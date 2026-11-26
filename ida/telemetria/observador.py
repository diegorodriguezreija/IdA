"""El observador (O2, O3, O4): lee el organismo al final de cada latido y produce el registro del latido v1.

Solo lee. No llama a nada que cambie el estado del organismo, de la memoria, del mundo ni del azar: lee atributos,
propiedades y métodos de consulta (``Soma.valores``, ``Proposicion.estado``, ``Necesidad.deficit``,
``Mundo.puntuacion``, ``Mundo.vista``, ``Mundo.escena``). El esquema está en ``ida/telemetria/esquema.py``.

La escena (O6) viaja en el registro solo cuando cambia respecto a la del latido anterior de la misma vida: la primera
completa y después completa cada vez que cambia. Para reconstruirla al reproducir, la de un latido es la última que
llegó en esa vida (``ida.telemetria.grabacion.escenas``).

Una excepción documentada (revisada con el autor en T1): en Crafter, ``vista()`` llama a ``_cosas()``, que asigna un id
a cada criatura vista por primera vez. Entre el final del latido y el ``observar()`` siguiente (que también llama
primero a ``_cosas()``) el entorno no avanza, así que asigna los mismos ids en el mismo orden: es una caché que no
cambia la conducta. Lo mismo vale para ``escena()`` en Crafter, que lee las criaturas por la misma vía (``_cosas()``)
justo después de ``vista()``. Lo comprueba ``herramientas/invariancia.py --observador completo``.

El núcleo no sabe nada de esto: la base no importa ``ida.telemetria`` (``tests/test_pureza.py``).
"""

import json
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ida.nucleo.onda import Onda
from ida.nucleo.soma import VITALES
from ida.nucleo.vocabulario import EstadoSaber
from ida.telemetria.esquema import NIVELES, VERSION
from ida.telemetria.hechos import Deductor

RASGOS_ARQUETIPO = ("apertura", "responsabilidad", "neuroticismo", "extraversion", "umbral_miedo")
SABER_COGNITIVO = 20      # proposiciones de más confianza en el nivel cognitivo (como el panel de hoy)
PROFUNDIDAD_JSON = 6      # profundidad máxima al copiar cargas y registros de piezas


def a_json(x: Any, profundidad: int = PROFUNDIDAD_JSON) -> Any:
    """Copia ``x`` en tipos de JSON sin tocar el original: enumerados por su valor, conjuntos ordenados, tuplas como
    listas, claves como texto y lo demás como texto."""
    if x is None or isinstance(x, (bool, int, str)):
        return x
    if isinstance(x, float):
        return x if x == x and x not in (float("inf"), float("-inf")) else None
    if isinstance(x, Enum):
        return a_json(x.value, profundidad)
    if profundidad <= 0:
        return str(x)
    if isinstance(x, dict):
        return {str(a_json(k, 1)): a_json(v, profundidad - 1) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [a_json(v, profundidad - 1) for v in x]
    if isinstance(x, (set, frozenset)):
        return sorted((a_json(v, profundidad - 1) for v in x), key=lambda v: json.dumps(v, sort_keys=True, default=str))
    return str(x)


def _estado(p: Any, ahora: int) -> str:
    """Estado de una proposición con un nombre estable: ``hipotesis``, ``demostrada`` o ``refutada``."""
    e: EstadoSaber = p.estado(ahora)
    return e.name.lower()


class Observador:
    """Produce el registro del latido v1 de cada latido (``registrar``), al nivel pedido."""

    def __init__(self, nivel: str = "cognitivo"):
        if nivel not in NIVELES:
            raise ValueError(f"Nivel de observación desconocido {nivel!r}: {', '.join(NIVELES)}")
        self.nivel = nivel
        self._n = NIVELES.index(nivel)
        self.vida = 0
        self._org: Any = None
        self._hechos = Deductor()
        self._escena: Optional[Dict[str, Any]] = None   # la última escena enviada en esta vida

    # --- vida ------------------------------------------------------------------------------------------------------
    def _nueva_vida(self, org: Any) -> None:
        self._org = org
        self.vida += 1
        self._hechos = Deductor()
        self._escena = None

    # --- registro --------------------------------------------------------------------------------------------------
    def registrar(self, org: Any, onda: Onda) -> Dict[str, Any]:
        """El registro del latido que acaba de terminar. Solo lee."""
        if org is not self._org:
            self._nueva_vida(org)
        arq = org.arquetipo
        r: Dict[str, Any] = {
            "v": VERSION, "nivel": self.nivel, "latido": onda.ciclo, "vida": self.vida, "generacion": int(arq.generacion),
            "individuo": str(arq.id), "mundo": str(org.mundo.nombre), "con_experiencia": bool(org.con_experiencia),
        }
        self._vital(org, onda, r)
        r["hechos"] = self._hechos.deducir(org, onda, r)
        if self._n >= 1:
            self._cognitivo(org, onda, r)
        if self._n >= 2:
            self._completo(onda, r)
        return r

    # --- nivel vital -----------------------------------------------------------------------------------------------
    def _vital(self, org: Any, onda: Onda, r: Dict[str, Any]) -> None:
        soma, notas, mem = org.soma, onda.notas, org.memoria
        valores = soma.valores()
        r["ritmo"] = {
            "ms": notas.get("ms_cognicion", 0.0), "ms_total": notas.get("ms_total", 0.0), "plazo_ms": round(onda.frecuencia_ms, 1),
            "amplitud": [onda.amplitud_consumida, onda.amplitud_max],
            "potencia": [round(onda.potencia_consumida, 3), round(onda.potencia_max, 3)],
            "guillotina": onda.motivo_guillotina if onda.guillotina else "", "logico": bool(onda.ops_por_ms),
        }
        r["cuerpo"] = {k: valores[k] for k in VITALES} | {
            "dormido": bool(soma.dormido), "cargando": None if soma.cargando is None else str(soma.cargando), "vivo": soma.esta_vivo}
        r["quimica"] = {k: valores[k] for k in ("dopamina", "placer", "estres")}
        r["afecto"] = {"estado": soma.afecto.value, "valencia": round(soma.valencia, 3), "indicadores": dict(soma.indicadores)}
        r["necesidades"] = self._necesidades(org, onda)
        r["accion"] = self._accion(onda)
        punt = a_json(org.mundo.puntuacion())
        logros = punt.get("logros") if isinstance(punt, dict) else None
        r["score"] = {"puntuacion": punt if isinstance(punt, dict) else {"valor": punt},
                      "logros": [str(x) for x in logros] if isinstance(logros, list) else []}
        r["hechos"] = []
        r["experiencia"] = {
            # list(): si una nota llega como texto, la consola de siempre la recorre carácter a carácter; se conserva
            "aprendizaje": [str(t) for t in list(notas.get("aprendizaje", []) or [])],   # type: ignore[call-overload]
            "expectativa": str(notas.get("expectativa", "") or ""),
            "cambio_decision": bool(notas.get("experiencia_cambio")),
            "episodio": str(notas.get("episodio", "") or ""),
        }
        estados = [_estado(p, onda.ciclo) for p in mem.saber.values()]
        r["memoria"] = {
            "aciertos": int(mem.aciertos), "sorpresas": int(mem.fallos), "episodios": len(mem.episodios),
            "demostradas": estados.count("demostrada"), "hipotesis": estados.count("hipotesis"),
            "refutadas": estados.count("refutada"), "recuerdos": len(mem.registros), "heredados": int(mem.heredados),
        }
        r["contadores"] = {str(k): int(v) for k, v in org.contadores.items()}
        r["arquetipo"] = {k: float(getattr(org.arquetipo, k)) for k in RASGOS_ARQUETIPO}
        r["vista"] = str(org.mundo.vista())
        escena = org.mundo.escena()
        if escena is not None:
            escena = a_json(escena)
            if escena != self._escena:      # solo cuando cambia (O6)
                r["escena"] = escena
                self._escena = escena

    @staticmethod
    def _necesidades(org: Any, onda: Onda) -> List[Dict[str, Any]]:
        """Déficit de cada necesidad declarada, con las constantes interoceptivas y las del cuerpo (como la causa de
        muerte del Core)."""
        valores: Dict[str, float] = {}
        for n, p in onda.ev("Interocepcion").items():
            v = p.carga.get("valor")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                valores[n] = float(v)
        valores.update({n: float(getattr(org.soma, n)) for n in VITALES})
        salida = []
        for nec in org.perfil.necesidades:
            d = nec.deficit(valores)
            if d is not None:
                salida.append({"nombre": nec.nombre, "deficit": round(d, 3)})
        return salida

    @staticmethod
    def _accion(onda: Onda) -> Optional[Dict[str, Any]]:
        ej = onda.reactiva.ef.get("Accion", {}).get("Accion")
        if ej is None:
            return None
        c = ej.carga
        exito = c.get("exito")
        motivo = c.get("motivo", "")
        accion = {
            "verbo": str(a_json(c["verbo"])), "objetivo": str(c.get("objetivo", "")), "clase": str(c.get("clase", "") or ""),
            "sistema": str(c.get("sistema", "")), "exito": exito if isinstance(exito, bool) else None,
            "mensaje": str(c.get("mensaje", "") or ""), "motivo": str(motivo) if motivo else "",
        }
        origen = c.get("origen")
        if isinstance(origen, dict) and origen.get("estrategia") is not None:
            accion["estrategia"] = str(origen["estrategia"])
        return accion

    # --- nivel cognitivo -------------------------------------------------------------------------------------------
    def _cognitivo(self, org: Any, onda: Onda, r: Dict[str, Any]) -> None:
        reactiva, notas = onda.reactiva, onda.notas
        canales: Dict[str, Dict[str, int]] = {}
        for fase, piezas in (("ev", reactiva.ev), ("acc", reactiva.acc), ("ef", reactiva.ef)):
            for canal, d in piezas.items():
                canales.setdefault(canal, {"ev": 0, "acc": 0, "ef": 0})[fase] = len(d)
        lista: List[Dict[str, Any]] = []
        for fase, piezas in (("ev", reactiva.ev), ("acc", reactiva.acc)):
            for canal, d in piezas.items():
                for p in d.values():
                    lista.append({"id": str(p.id), "canal": canal, "fase": fase, "tipo": p.tipo, "arousal": round(p.arousal, 4),
                                  "confianza": round(p.confianza, 4), "origen": p.origen, "sistema": p.sistema})
        r["onda"] = {
            "canales": canales,
            "piezas": lista,
            "flujo": self._flujo(onda),
            "consumo": {s: {k: round(v, 4) for k, v in c.items()} for s, c in onda.consumo.items()},
            "restante": {s: [a_json(x) for x in v] for s, v in dict(notas.get("restante", {}) or {}).items()},   # type: ignore[call-overload]
            "operaciones": int(onda.operaciones),
            "guillotina": bool(onda.guillotina),
            "excepciones": {k: int(v) for k, v in onda.excepciones.items()},
        }
        candidatos = [a_json(e) for e in list(notas.get("evaluados", []) or [])]   # type: ignore[call-overload]
        decision = reactiva.ef.get("Decision", {}).get("decision")   # la del Tribunal: su entrada es el candidato ganador
        ganador = None
        if decision is not None:
            ganador = {"id": str(decision.entradas[0]) if decision.entradas else "",
                       "sistema": str(decision.carga.get("sistema", "") or "")}
        r["tribunal"] = {"ganador": ganador, "candidatos": candidatos,
                         "cambio_experiencia": bool(notas.get("experiencia_cambio")), "plus_decide": bool(notas.get("plus_decide"))}
        r["estrategias"] = {
            "activas": [{"id": str(pid), "sistema": p.sistema, "nombre": str(p.carga.get("nombre", ""))}
                        for pid, p in onda.estrategias.items()],
            "por_sistema": {s: a_json(notas[f"estrategias_{s}"]) for s in ("S1", "S2", "S3") if f"estrategias_{s}" in notas},
        }
        mem = org.memoria
        orden = sorted(mem.saber.values(), key=lambda p: (-p.confianza, p.sujeto))
        r["saber"] = [{"sujeto": p.sujeto, "relacion": p.relacion.name, "estado": _estado(p, onda.ciclo),
                       "confianza": float(p.confianza), "heredada": bool(p.heredada),
                       "autoridad": p.c_aut is not None and p.w_aut > 0.0}
                      for p in (orden if self._n >= 2 else orden[:SABER_COGNITIVO])]

    @staticmethod
    def _flujo(onda: Onda) -> List[Dict[str, str]]:
        """Por dónde pasó la información en este latido: cada pieza que otro Componente modificó (de su autor original a
        quien la tocó) y cada pieza que se formó a partir de otra (``entradas``: del autor de la entrada al de la pieza)."""
        indice: Dict[str, Any] = {}
        for d in onda.reactiva.ef.values():
            for p in d.values():
                indice[str(p.id)] = p
        flujo: List[Dict[str, str]] = []
        vistos: set = set()
        for pid, p in indice.items():
            for e in p.registro:
                if e.get("latido") == onda.ciclo and e.get("autor") != p.origen:
                    clave = (pid, p.origen, e.get("autor"), e.get("op"))
                    if clave not in vistos:
                        vistos.add(clave)
                        flujo.append({"pieza": pid, "de": p.origen, "a": str(e.get("autor")), "op": str(e.get("op"))})
            if p.actualizada == onda.ciclo or p.creada == onda.ciclo:
                for ent in p.entradas:
                    previa = indice.get(str(ent))
                    if previa is not None and previa is not p and previa.origen != p.origen:
                        clave = (str(ent), previa.origen, p.origen, "entrada")
                        if clave not in vistos:
                            vistos.add(clave)
                            flujo.append({"pieza": str(ent), "de": previa.origen, "a": p.origen, "op": "entrada"})
        return flujo

    # --- nivel completo --------------------------------------------------------------------------------------------
    @staticmethod
    def _completo(onda: Onda, r: Dict[str, Any]) -> None:
        r["tiempos_ms"] = {k: round(v, 4) for k, v in onda.tiempos_ms.items()}
        fases: List[Tuple[str, int, int]] = list(onda.fases)
        t0 = min((f[1] for f in fases), default=0)
        r["fases"] = [[nombre, round((ini - t0) / 1e6, 4), round((fin - t0) / 1e6, 4)] for nombre, ini, fin in fases]
        piezas = []
        for canal, d in onda.reactiva.ef.items():
            for p in d.values():
                piezas.append({"id": str(p.id), "canal": canal, "fase": "ef", "tipo": p.tipo, "arousal": round(p.arousal, 4),
                               "confianza": round(p.confianza, 4), "origen": p.origen, "sistema": p.sistema,
                               "creada": int(p.creada), "actualizada": int(p.actualizada), "entradas": a_json(list(p.entradas)),
                               "carga": a_json(p.carga), "registro": a_json(list(p.registro))})
        r["piezas"] = piezas
