"""Hechos de la vida (O5): se deducen comparando el estado al final de cada latido con el del latido anterior.

No se toca el motor: el deductor solo lee el organismo (como el observador) y guarda una instantánea pequeña de lo que
compara. Los hechos no llevan frases: tipo y parámetros (catálogo v1 en ``ida/telemetria/esquema.py``, ``HECHOS``); la
interfaz forma la frase en el idioma elegido.

Lo que se compara:

- ``nace``: el primer latido de un organismo nuevo. Lo que el individuo ya trae al nacer (manual, herencia) es la
  línea de partida: no se cuenta como aprendido.
- ``primera_vez``: la primera acción con éxito de cada (verbo, clase) en la vida.
- ``aprende``: una proposición nueva, que pasa a demostrada o que vuelve a hipótesis desde refutada
  (``saber: proposicion``); o un requisito de acción nuevo, que cambia lo que pide o produce, o que se ve cumplirse por
  primera vez (``saber: requisito``, sección «requisitos» de la memoria, si el mundo la monta).
- ``duda`` / ``refuta``: una proposición demostrada que vuelve a hipótesis / una que pasa a refutada.
- ``peligro``: cada ``aprende`` de una proposición «hace daño», con el daño esperado de un encuentro si la sección
  «peligros» lo estima.
- ``sorpresa``: cada pieza ``Sorpresa`` del latido: la de la expectativa (con lo esperado, que es la expectativa que
  quedó anotada al final del latido anterior, y lo obtenido) o la del modelo de transiciones (F1, con su error).
- ``logro``: cada logro nuevo de la puntuación del mundo (si la puntuación tiene una lista ``logros``).
- ``estrategia``: una estrategia que entra en las activas (``inicio``) o sale (``fin``, con su estado final).
- ``duerme`` / ``despierta``: cambios del sueño del cuerpo (``despierta`` lleva el motivo que anota el Core).
- ``muere``: el latido en que la vitalidad llega a cero, con la causa que da el Core.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from ida.nucleo.onda import Onda
from ida.nucleo.vocabulario import Relacion

Firma = Tuple[Any, ...]


@dataclass
class _Instantanea:
    saber: Dict[Tuple[str, str], str] = field(default_factory=dict)        # (sujeto, relación) -> estado
    requisitos: Dict[Tuple[str, str], Firma] = field(default_factory=dict)  # (verbo, objetivo) -> firma
    logros: Set[str] = field(default_factory=set)
    estrategias: Dict[str, Any] = field(default_factory=dict)              # id -> pieza (para leer su estado al salir)
    dormido: bool = False
    expectativa: Optional[Tuple[str, str, float]] = None                   # (verbo, clase, esperado)


def _fuente(p: Any) -> str:
    if p.heredada:
        return "herencia"
    if p.c_aut is not None and p.w_aut > 0.0:
        return "manual"
    return "experiencia"


def _requisitos(org: Any) -> Dict[Tuple[str, str], Any]:
    mem = org.memoria
    if not mem.tiene_seccion("requisitos"):
        return {}
    reqs = getattr(mem.seccion("requisitos"), "requisitos", None)
    if not isinstance(reqs, dict):
        return {}
    return {(str(getattr(v, "value", v)), str(o)): r for (v, o), r in reqs.items()}


def requisito(clave: Tuple[str, str], r: Any) -> Dict[str, Any]:
    """Un requisito de acción en la forma del hecho ``aprende`` de requisito (sin ``tipo`` ni ``saber``)."""
    return {"verbo": clave[0], "clase": clave[1], "requiere": dict(r.requiere_inventario), "cerca": sorted(r.requiere_cerca),
            "efecto": dict(r.efecto), "confirmado": r.exitos >= 1, "fuente": str(r.fuente), "confianza": round(float(r.confianza), 3)}


def requisitos(org: Any) -> List[Dict[str, Any]]:
    """Todos los requisitos de acción de la memoria (del manual y de la experiencia), en un orden estable."""
    return [requisito(k, r) for k, r in sorted(_requisitos(org).items())]


def fuente(p: Any) -> str:
    """La fuente de una proposición: ``herencia``, ``manual`` (autoridad) o ``experiencia``."""
    return _fuente(p)


def _firma(r: Any) -> Firma:
    return (tuple(sorted(r.requiere_inventario.items())), tuple(sorted(r.requiere_cerca)), tuple(sorted(r.efecto.items())),
            r.exitos >= 1)


def _dano(org: Any, clase: str) -> Optional[float]:
    """Daño esperado de un encuentro con ``clase``, si la sección «peligros» lo estima (consulta sin efectos)."""
    mem = org.memoria
    if not mem.tiene_seccion("peligros"):
        return None
    estimar = getattr(mem.seccion("peligros"), "dano_propio", None)
    if estimar is None:
        return None
    return round(float(estimar(clase, True)), 3)


class Deductor:
    """Deduce los hechos de una vida, latido a latido. Uno por organismo."""

    def __init__(self) -> None:
        self._previo: Optional[_Instantanea] = None
        self._acciones: Set[Tuple[str, str]] = set()

    def _instantanea(self, org: Any, onda: Onda, logros: List[str]) -> _Instantanea:
        mem = org.memoria
        exp = mem.expectativa
        return _Instantanea(
            saber={(p.sujeto, p.relacion.name): p.estado(onda.ciclo).name.lower() for p in mem.saber.values()},
            requisitos={k: _firma(r) for k, r in _requisitos(org).items()},
            logros=set(logros),
            estrategias=dict(onda.estrategias),
            dormido=bool(org.soma.dormido),
            expectativa=(str(exp.verbo.value), str(exp.clase), float(exp.esperado)) if exp is not None else None,
        )

    def deducir(self, org: Any, onda: Onda, registro: Dict[str, Any]) -> List[Dict[str, Any]]:
        logros: List[str] = registro["score"]["logros"]
        ahora = self._instantanea(org, onda, logros)
        previo, self._previo = self._previo, ahora
        hechos: List[Dict[str, Any]] = []
        if previo is None:
            hechos.append({"tipo": "nace", "individuo": registro["individuo"], "generacion": registro["generacion"],
                           "heredados": int(org.memoria.heredados)})
            previo = ahora   # lo que trae al nacer es la línea de partida
        self._accion(registro.get("accion"), hechos)
        self._saber(org, onda, previo, ahora, hechos)
        self._requisitos(org, previo, ahora, hechos)
        self._sorpresas(onda, previo, hechos)
        hechos.extend({"tipo": "logro", "nombre": n} for n in logros if n not in previo.logros)
        self._estrategias(previo, ahora, hechos)
        if ahora.dormido and not previo.dormido:
            hechos.append({"tipo": "duerme"})
        elif previo.dormido and not ahora.dormido:
            hechos.append({"tipo": "despierta", "motivo": str(onda.notas.get("despierta", "") or "")})
        if not org.soma.esta_vivo:
            hechos.append({"tipo": "muere", "causa": str(org._causa_de_muerte(onda)), "latidos": int(onda.ciclo),
                           "puntuacion": registro["score"]["puntuacion"]})
        return hechos

    def _accion(self, accion: Optional[Dict[str, Any]], hechos: List[Dict[str, Any]]) -> None:
        if not accion or accion.get("exito") is not True or not accion.get("clase"):
            return
        clave = (accion["verbo"], accion["clase"])
        if clave not in self._acciones:
            self._acciones.add(clave)
            hechos.append({"tipo": "primera_vez", "verbo": clave[0], "clase": clave[1]})

    @staticmethod
    def _saber(org: Any, onda: Onda, previo: _Instantanea, ahora: _Instantanea, hechos: List[Dict[str, Any]]) -> None:
        for (sujeto, rel), estado in ahora.saber.items():
            antes = previo.saber.get((sujeto, rel))
            if antes == estado:
                continue
            p = org.memoria.saber.get((sujeto, Relacion[rel]))
            if p is None:
                continue
            confianza = round(float(p.confianza), 3)
            if antes is None or estado == "demostrada" or (antes == "refutada" and estado == "hipotesis"):
                hechos.append({"tipo": "aprende", "saber": "proposicion", "clase": sujeto, "relacion": rel, "estado": estado,
                               "fuente": _fuente(p), "confianza": confianza})
                if rel == Relacion.PELIGROSO.name:
                    hechos.append({"tipo": "peligro", "clase": sujeto, "estado": estado, "dano": _dano(org, sujeto),
                                   "confianza": confianza})
            elif estado == "refutada":
                hechos.append({"tipo": "refuta", "clase": sujeto, "relacion": rel, "confianza": confianza})
            else:   # de demostrada a hipótesis
                hechos.append({"tipo": "duda", "clase": sujeto, "relacion": rel, "confianza": confianza})

    @staticmethod
    def _requisitos(org: Any, previo: _Instantanea, ahora: _Instantanea, hechos: List[Dict[str, Any]]) -> None:
        cambiados = [k for k, f in ahora.requisitos.items() if previo.requisitos.get(k) != f]
        if not cambiados:
            return
        reqs = _requisitos(org)
        for clave in cambiados:
            hechos.append({"tipo": "aprende", "saber": "requisito", **requisito(clave, reqs[clave])})

    def cierre(self, org: Any, onda: Onda, registro: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Los hechos de lo aprendido al morir (``Organismo._aprender_de_la_muerte``, después del último latido): solo lo
        que cambió en la memoria (``aprende``, ``peligro``, ``duda``, ``refuta``). Nada de ``muere``, sorpresas, logros ni
        estrategias: eso ya salió en el último latido."""
        ahora = self._instantanea(org, onda, registro["score"]["logros"])
        previo, self._previo = self._previo, ahora
        if previo is None:
            return []
        hechos: List[Dict[str, Any]] = []
        self._saber(org, onda, previo, ahora, hechos)
        self._requisitos(org, previo, ahora, hechos)
        return hechos

    @staticmethod
    def _sorpresas(onda: Onda, previo: _Instantanea, hechos: List[Dict[str, Any]]) -> None:
        for p in onda.ev("Sorpresa").values():
            c = p.carga
            if "rpe" in c:
                h: Dict[str, Any] = {"tipo": "sorpresa", "origen": "expectativa", "clase": "", "rpe": float(c["rpe"])}
                if previo.expectativa is not None:
                    verbo, clase, esperado = previo.expectativa
                    h.update({"verbo": verbo, "clase": clase, "esperado": round(esperado, 3),
                              "obtenido": round(esperado + float(c["rpe"]), 3)})
                hechos.append(h)
            elif "error" in c:
                hechos.append({"tipo": "sorpresa", "origen": "modelo", "sistema": str(c.get("sistema", "")),
                               "clase": str(c.get("clase", "")), "error": round(float(c["error"]), 4)})

    @staticmethod
    def _estrategias(previo: _Instantanea, ahora: _Instantanea, hechos: List[Dict[str, Any]]) -> None:
        for pid, p in ahora.estrategias.items():
            if pid not in previo.estrategias:
                hechos.append({"tipo": "estrategia", "sistema": p.sistema, "nombre": str(p.carga.get("nombre", "")), "cambio": "inicio"})
        for pid, p in previo.estrategias.items():
            if pid not in ahora.estrategias:
                hechos.append({"tipo": "estrategia", "sistema": p.sistema, "nombre": str(p.carga.get("nombre", "")), "cambio": "fin",
                               "estado": str(p.carga.get("estado", "") or "")})
