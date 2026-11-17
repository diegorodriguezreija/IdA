"""Memoria del individuo: recuerdos (dimensión activa), expectativas (dimensión proactiva),
conocimiento formal legible, episodios, sueño y herencia.

Escribe el Core, no los componentes: los componentes señalan lo relevante con su arousal y el
Core guarda lo más saliente de cada latido. La escritura va en dos velocidades: lo mínimo en
cada latido (en RAM) y lo costoso (persistir, olvidar, consolidar) al dormir o al morir.
"""

import heapq
import math
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from ida.core.biblioteca import RegistroLectura
from ida.core.pieza import Episodio, acotar
from ida.core.vocabulario import EstadoSaber, Relacion, Verbo

PERFILES_MEMORIA = {"apagada": 0, "ligera": 2, "completa": 5}   # K piezas guardadas por latido


# ---------------------------------------------------------------------------
# Conocimiento formal (lenguaje interno de S3)
# ---------------------------------------------------------------------------
class Proposicion:
    """«<clase> <relación>», con confianza ponderada por fuente de evidencia."""

    CONFIRMACIONES_MINIMAS = 3
    CONFIANZA_DEMOSTRADA = 0.7
    LATIDOS_SIN_REFUTAR = 30
    DECAY = 0.05             # bloque E, E4: caducidad por noche de c_exp (reducción nocturna ×0,95)
    DANO_SATURA = 10.0       # pérdida de vitalidad con la que el arousal de daño llega a 1 (el doble de un envenenamiento grave)

    def __init__(
        self,
        sujeto: str,
        relacion: Relacion,
        confianza: float = 0.3,
        confirmaciones: int = 0,
        refutaciones: int = 0,
        ultima_refutacion: int = -10**9,
        heredada: bool = False,
        actualizada: int = 0,
        c_aut: Optional[float] = None,
        w_aut: float = 0.0,
        c_exp: Optional[float] = None,
    ):
        self.sujeto = sujeto
        self.relacion = relacion
        self.c_exp = c_exp if c_exp is not None else confianza
        self.confirmaciones = confirmaciones
        self.refutaciones = refutaciones
        self.ultima_refutacion = ultima_refutacion
        self.heredada = heredada
        self.actualizada = actualizada
        self.c_aut = c_aut
        self.w_aut = w_aut
        self.decay = self.DECAY   # metadato decay (decisión 7): lo usa la reducción nocturna (E4)

    @property
    def confianza(self) -> float:
        if self.c_aut is None or self.w_aut <= 0.0:
            return self.c_exp
        w_exp = float(1 + self.confirmaciones + self.refutaciones)
        return (w_exp * self.c_exp + self.w_aut * self.c_aut) / (w_exp + self.w_aut)

    @confianza.setter
    def confianza(self, valor: float) -> None:
        self.c_exp = valor

    def estado(self, ahora: int) -> EstadoSaber:
        if self.refutaciones > 0 and self.confianza < 0.15:
            return EstadoSaber.REFUTADA
        if (
            self.confirmaciones >= self.CONFIRMACIONES_MINIMAS
            and self.confianza >= self.CONFIANZA_DEMOSTRADA
            and ahora - self.ultima_refutacion > self.LATIDOS_SIN_REFUTAR
        ):
            return EstadoSaber.DEMOSTRADA
        return EstadoSaber.HIPOTESIS

    def confirmar(self, ahora: int) -> None:
        """La confianza sube despacio."""
        self.confirmaciones += 1
        self.c_exp = acotar(self.c_exp + 0.15 * (1.0 - self.c_exp))
        self.actualizada = ahora

    def marcar_dano(self, perdida_vitalidad: float) -> None:
        """Un recuerdo de daño caduca menos cuanto mayor fue el daño: decay = DECAY × (1 − arousal de daño),
        con arousal de daño = pérdida / DANO_SATURA acotado a [0, 1]. Se queda el menor decay visto."""
        arousal = acotar(perdida_vitalidad / self.DANO_SATURA)
        self.decay = min(self.decay, round(self.DECAY * (1.0 - arousal), 6))

    def refutar(self, ahora: int) -> None:
        """...y baja más rápido."""
        self.refutaciones += 1
        self.c_exp = acotar(self.c_exp * 0.7 - 0.05)
        self.ultima_refutacion = ahora
        self.actualizada = ahora

    def aplicar_autoridad(self, veredicto: str, confianza_fuente: float, peso_fuente: float, ahora: int) -> None:
        """Aplica testimonio externo de autoridad. Modula c_aut y w_aut."""
        if veredicto == "afirma":
            c_val = acotar(confianza_fuente)
        elif veredicto == "niega":
            c_val = acotar(1.0 - confianza_fuente)
        else:
            return
        if self.c_aut is None:
            self.c_aut = c_val
            self.w_aut = max(0.0, peso_fuente)
        else:
            w_total = self.w_aut + peso_fuente
            if w_total > 0:
                self.c_aut = (self.w_aut * self.c_aut + peso_fuente * c_val) / w_total
                self.w_aut = w_total
        self.actualizada = ahora

    def texto(self, ahora: int) -> str:
        partes_origen = []
        if self.heredada:
            partes_origen.append("heredada")
        if self.c_aut is not None and self.w_aut > 0.0:
            partes_origen.append("autoridad")
        origen = f", {', '.join(partes_origen)}" if partes_origen else ""
        return f"«{self.sujeto} {self.relacion.value}» ({self.estado(ahora).value}{origen}, {self.confianza:.2f})"

    def __repr__(self) -> str:
        return f"Proposicion({self.sujeto!r}, {self.relacion!r}, confianza={self.confianza:.3f})"

    def __eq__(self, otro: object) -> bool:
        if not isinstance(otro, Proposicion):
            return False
        return (
            self.sujeto == otro.sujeto
            and self.relacion == otro.relacion
            and self.confirmaciones == otro.confirmaciones
            and self.refutaciones == otro.refutaciones
            and self.heredada == otro.heredada
            and round(self.confianza, 4) == round(otro.confianza, 4)
        )


@dataclass
class Registro:
    """Recuerdo agregado de hacer ``verbo`` sobre una ``clase``: cuántas veces y con qué balance medio."""

    n: int = 0
    suma: float = 0.0
    ultimo: int = 0

    @property
    def media(self) -> float:
        return self.suma / self.n if self.n else 0.0


@dataclass
class Expectativa:
    """Predicción proactiva: «si hago <verbo> sobre <clase>, el balance será <signo>»."""

    latido: int
    verbo: Verbo
    clase: str
    esperado: float


@dataclass
class Aprendizaje:
    """Lo que el Core aprendió al contrastar la acción anterior con el presente (para la consola)."""

    textos: List[str] = field(default_factory=list)
    sorpresa: bool = False
    rpe: float = 0.0


@dataclass
class Arista:
    """Transición espacial observada entre dos ubicaciones en el mapa cognitivo."""

    usos: int = 1
    ultimo_latido: int = 0
    valor_replay: float = 0.0


@dataclass
class RecuerdoLugar:
    """Asociación espacial (célula de lugar): última ubicación donde estuvo al alcance una clase."""

    ubicacion: str
    ultimo_latido: int = 0
    confianza: float = 1.0


def _signo(x: float, margen: float = 0.25) -> int:
    return 0 if abs(x) < margen else (1 if x > 0 else -1)


class Memoria:
    MAX_NODOS_MAPA = 200
    EDAD_OLVIDO_MAPA = 300

    def __init__(self, perfil: str = "completa", con_replay: bool = True):
        if perfil not in PERFILES_MEMORIA:
            raise ValueError(f"Perfil de memoria desconocido: {perfil}")
        self.perfil = perfil
        self.k = PERFILES_MEMORIA[perfil]
        self.con_replay = con_replay
        self.saber: Dict[Tuple[str, Relacion], Proposicion] = {}
        self.registros: Dict[Tuple[Verbo, str], Registro] = {}
        self.lugares: Dict[str, float] = {}            # bienestar recordado por lugar (hogar)
        self.clases_vistas: Dict[str, int] = {}        # familiaridad por clase
        self.mapa: Dict[str, Dict[str, Arista]] = {}   # grafo de transiciones (hipocampo)
        self.mapa_valores: Dict[str, float] = {}       # valor atribuido a lugares por replay
        self.donde: Dict[str, RecuerdoLugar] = {}      # clase -> última ubicación al alcance
        self.expectativa: Optional[Expectativa] = None
        self.buffer: List[Dict[str, Any]] = []         # piezas salientes pendientes de persistir
        self.episodios: List[Episodio] = []
        self._ultimo_consolidar_ep: int = 0
        self.lecturas: List[RegistroLectura] = []
        self.lectura_activa: Optional[RegistroLectura] = None
        self.ultimo_fin_lectura: int = -100
        self.aciertos = 0
        self.fallos = 0
        # Bloque E (decisión 19): búfer diurno de tamaño fijo y episodio del día (secuencia de ondas).
        self.diurno: List[Tuple[float, int, Dict[str, Any]]] = []   # montículo (puntuación, orden, pieza)
        self._orden_diurno = 0
        self.dia: List[Dict[str, Any]] = []
        # E2: grafo semántico (nodos con fuerza y valencia; relaciones por coincidencia) y almacén de días.
        self.grafo: Dict[str, Dict[str, Any]] = {}
        self.relaciones: Dict[Tuple[str, str], float] = {}
        self.dias: List[Dict[str, Any]] = []
        # E3: conceptos (prototipo por clase, id estable sin significado) e instancias.
        self.conceptos: Dict[str, Dict[str, Any]] = {}       # id -> {"etiqueta", "prototipo", "n"}
        self._concepto_de: Dict[str, str] = {}               # etiqueta legible -> id
        self.instancias: Dict[str, Dict[str, Any]] = {}      # id de la instancia -> {"concepto", "visto"}
        # F1: modelo de transiciones (sistema, verbo, clase) -> cambio medio de cada variable, aprendido de lo vivido.
        self.modelo: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        self._modelo_por: Dict[Tuple[str, str], Set[str]] = {}

    @property
    def activa(self) -> bool:
        return self.k > 0

    # --- conocimiento ----------------------------------------------------------
    def proposicion(self, clase: str, relacion: Relacion, crear: bool = False) -> Optional[Proposicion]:
        clave = (clase, relacion)
        if clave not in self.saber and crear:
            self.saber[clave] = Proposicion(clase, relacion)
        return self.saber.get(clave)

    def demostrada(self, clase: str, relacion: Relacion, ahora: int) -> bool:
        p = self.saber.get((clase, relacion))
        return p is not None and p.estado(ahora) == EstadoSaber.DEMOSTRADA

    def conocimiento(self, ahora: int) -> List[str]:
        orden = sorted(self.saber.values(), key=lambda p: (-p.confianza, p.sujeto))
        return [p.texto(ahora) for p in orden]

    # --- dimensión activa: recuerdos -------------------------------------------
    def recordar(self, verbo: Verbo, clase: str) -> Tuple[float, int]:
        r = self.registros.get((verbo, clase))
        return (r.media, r.n) if r else (0.0, 0)

    def sesgo(self, verbo: Verbo, clase: str, ahora: int) -> Tuple[float, float]:
        """Sesgo de la experiencia sobre un candidato: (activa, proactiva), cada uno en [-1, 1].

        - Activa: el balance medio que dejó hacer esto mismo antes.
        - Proactiva: lo que se sabe (proposiciones) sobre la clase del objetivo.
        """
        if not self.activa or not clase:
            return 0.0, 0.0
        media, n = self.recordar(verbo, clase)
        activa = math.tanh(media / 5.0) * min(1.0, n / 3.0) if n else 0.0
        proactiva = 0.0
        nutr = self.saber.get((clase, Relacion.NUTRITIVO))
        pelig = self.saber.get((clase, Relacion.PELIGROSO))
        if verbo == Verbo.COMER and nutr is not None:
            estado = nutr.estado(ahora)
            proactiva += nutr.confianza if estado == EstadoSaber.DEMOSTRADA else (-0.5 if estado == EstadoSaber.REFUTADA else 0.0)
        if verbo in (Verbo.MOVER, Verbo.COMER, Verbo.COGER) and pelig is not None:
            if pelig.estado(ahora) == EstadoSaber.DEMOSTRADA:
                proactiva -= pelig.confianza
        return activa, acotar(proactiva, -1.0, 1.0)

    # --- el cuarteto: aprender del efecto de la acción anterior --------------
    def aprender(
        self,
        verbo: Optional[Verbo],
        clase: str,
        delta: Dict[str, float],
        causa: Optional[str],
        obtenido: Optional[str],
        exito: bool,
        ahora: int,
        mortal: bool = False,
    ) -> Aprendizaje:
        """Contrasta lo que hizo (``ei``) con lo que le pasó al cuerpo (``ev``)."""
        ap = Aprendizaje()
        if not self.activa:
            return ap
        d_vit = delta.get("vitalidad", 0.0)
        if causa and causa != clase:
            d_vit = max(0.0, d_vit)       # el daño lo causó otra cosa: no se atribuye a esta acción
        balance = d_vit + 0.5 * delta.get("alimentacion", 0.0) + 0.25 * delta.get("energia", 0.0)

        # Dimensión activa: recuerdo agregado de (verbo, clase)
        if verbo is not None and clase:
            r = self.registros.setdefault((verbo, clase), Registro())
            r.n += 1
            r.suma += balance
            r.ultimo = ahora

        # Conocimiento formal a partir de la agencia
        perdida = max(0.0, -delta.get("vitalidad", 0.0))

        def confirmar(c: str, rel: Relacion) -> None:
            p = cast(Proposicion, self.proposicion(c, rel, crear=True))
            antes = p.estado(ahora)
            p.confirmar(ahora)
            if rel == Relacion.PELIGROSO and perdida > 0.0:
                p.marcar_dano(perdida)
            if p.estado(ahora) != antes:
                ap.textos.append(f"ahora sabe {p.texto(ahora)}")

        def refutar(c: str, rel: Relacion) -> None:
            p = cast(Proposicion, self.proposicion(c, rel, crear=True))
            antes = p.estado(ahora)
            p.refutar(ahora)
            if p.estado(ahora) != antes:
                ap.textos.append(f"duda de {p.texto(ahora)}")

        if verbo == Verbo.COMER and clase and exito:
            if delta.get("alimentacion", 0.0) > 0.0 or delta.get("energia", 0.0) > 0.0:
                confirmar(clase, Relacion.NUTRITIVO)
            else:
                refutar(clase, Relacion.NUTRITIVO)
            if d_vit <= -1.0:
                confirmar(clase, Relacion.PELIGROSO)
                if d_vit <= -5.0:   # aversión gustativa: un envenenamiento grave se aprende casi de una vez
                    confirmar(clase, Relacion.PELIGROSO)
        if causa:
            confirmar(causa, Relacion.PELIGROSO)
            if mortal:   # trauma: lo que mató queda demostrado de una vez (y puede pasar al linaje)
                p = cast(Proposicion, self.proposicion(causa, Relacion.PELIGROSO, crear=True))
                p.confirmaciones = max(p.confirmaciones, Proposicion.CONFIRMACIONES_MINIMAS)
                p.confianza = max(p.confianza, Proposicion.CONFIANZA_DEMOSTRADA)
        if verbo in (Verbo.COGER, Verbo.USAR) and exito and (obtenido or clase):
            confirmar(obtenido or clase, Relacion.UTIL)

        # Dimensión proactiva: validar la expectativa del latido anterior
        exp = self.expectativa
        if exp is not None and verbo == exp.verbo and clase == exp.clase:
            ap.rpe = balance - exp.esperado
            if _signo(balance) == _signo(exp.esperado):
                self.aciertos += 1
                ap.textos.append(f"esperaba {exp.esperado:+.1f} y obtuvo {balance:+.1f}: acierto")
            else:
                self.fallos += 1
                ap.sorpresa = True
                ap.textos.append(f"esperaba {exp.esperado:+.1f} y obtuvo {balance:+.1f}: sorpresa")
        self.expectativa = None
        return ap

    def proyectar(self, verbo: Verbo, clase: str, ahora: int) -> Optional[Expectativa]:
        """Anota la expectativa de la acción que se va a ejecutar, si hay recuerdo en que basarla."""
        if not self.activa or not clase or verbo == Verbo.MOVER:
            self.expectativa = None           # moverse depende de todo lo demás: no se predice
            return None
        media, n = self.recordar(verbo, clase)
        if n == 0 or _signo(media) == 0:      # solo se anota lo que predice algo
            self.expectativa = None
            return None
        self.expectativa = Expectativa(ahora, verbo, clase, media)
        return self.expectativa

    # --- escritura rápida y episodios ------------------------------------------
    def guardar_rapido(self, piezas: List[Dict[str, Any]]) -> None:
        """Cada latido: las K piezas de mayor arousal, a un búfer en RAM."""
        if self.k:
            piezas = sorted(piezas, key=lambda p: -p["arousal"])[: self.k]
            self.buffer.extend(piezas)

    CAPACIDAD_DIURNO = 256      # piezas que caben en el búfer diurno
    CAPACIDAD_DIA = 1000        # latidos que caben en el episodio del día

    def marcar(self, latido: int, piezas: List[Dict[str, Any]], feedback: float, resumen: Dict[str, Any]) -> None:
        """De día (decisión 19): puntúa cada pieza (arousal + feedback del latido) y guarda las mejores en
        un búfer de tamaño fijo; si está lleno, una pieza nueva solo entra si supera a la peor. Barato:
        montículo en memoria. Añade el latido al episodio del día."""
        for p in piezas:
            puntuacion = float(p["arousal"]) + feedback
            self._orden_diurno += 1
            entrada = (puntuacion, self._orden_diurno, {**p, "puntuacion": round(puntuacion, 4)})
            if len(self.diurno) < self.CAPACIDAD_DIURNO:
                heapq.heappush(self.diurno, entrada)
            elif puntuacion > self.diurno[0][0]:
                heapq.heapreplace(self.diurno, entrada)
        if len(self.dia) < self.CAPACIDAD_DIA:
            self.dia.append({"latido": latido, "feedback": round(feedback, 4), **resumen})

    DIAS_GUARDADOS = 30         # días que conserva el almacén de episodios del día
    NODOS_POR_LATIDO = 5        # piezas de un mismo latido que se relacionan entre sí al consolidar

    @staticmethod
    def nodo(pieza: Dict[str, Any]) -> str:
        """Nodo semántico de una pieza: su tipo y su clase (o su id, si no tiene clase)."""
        return f"{pieza.get('tipo', '')}:{pieza.get('clase') or pieza.get('id', '')}"

    def consolidar_dia(self, ahora: int) -> Dict[str, int]:
        """De noche (decisión 19): lo mejor puntuado del búfer diurno pasa al grafo semántico (fuerza =
        puntuación positiva; valencia = feedback acumulado) y se relaciona con lo que coincidió en el mismo
        latido; el episodio del día pasa al almacén de días. El búfer y el día se vacían."""
        por_latido: Dict[int, List[Dict[str, Any]]] = {}
        for _, _, p in sorted(self.diurno, reverse=True):
            por_latido.setdefault(int(p.get("latido", 0)), []).append(p)
            nodo = self.nodo(p)
            n = self.grafo.setdefault(nodo, {"fuerza": 0.0, "valencia": 0.0, "usos": 0, "ultimo": 0,
                                              "tipo": p.get("tipo", ""), "clase": p.get("clase", "")})
            n["fuerza"] = round(n["fuerza"] + max(0.0, float(p["puntuacion"])), 4)
            n["valencia"] = round(n["valencia"] + float(p["puntuacion"]) - float(p["arousal"]), 4)
            n["usos"] += 1
            n["ultimo"] = max(n["ultimo"], int(p.get("latido", 0)))
        relaciones = 0
        for piezas in por_latido.values():
            nodos = sorted({self.nodo(p): float(p["puntuacion"]) for p in piezas[: self.NODOS_POR_LATIDO]}.items())
            for i, (a, pa) in enumerate(nodos):
                for b, pb in nodos[i + 1:]:
                    self.relaciones[(a, b)] = round(self.relaciones.get((a, b), 0.0) + max(0.0, min(pa, pb)), 4)
                    relaciones += 1
        consolidadas = len(self.diurno)
        if self.dia:
            self.dias.append({"fin": ahora, "latidos": len(self.dia), "feedback": round(sum(d["feedback"] for d in self.dia), 4),
                              "ondas": list(self.dia)})
            del self.dias[: max(0, len(self.dias) - self.DIAS_GUARDADOS)]
        self.diurno.clear()
        self.dia.clear()
        return {"piezas_consolidadas": consolidadas, "relaciones": relaciones}

    MAX_INSTANCIAS = 500        # instancias recordadas (se olvidan las vistas hace más tiempo)

    def instancia(self, instancia: str, clase: str, rasgos: Dict[str, float], ahora: int) -> str:
        """Decisión 20: actualiza el concepto de la clase (prototipo = media de los rasgos de sus
        instancias) y recuerda la instancia. Devuelve el id estable del concepto."""
        cid = self._concepto_de.get(clase)
        if cid is None:
            cid = f"c{len(self.conceptos) + 1}"
            self._concepto_de[clase] = cid
            self.conceptos[cid] = {"etiqueta": clase, "prototipo": {}, "n": 0}
        c = self.conceptos[cid]
        c["n"] += 1
        proto = c["prototipo"]
        for k in set(proto) | set(rasgos):
            proto[k] = round(proto.get(k, 0.0) + (float(rasgos.get(k, 0.0)) - proto.get(k, 0.0)) / c["n"], 4)
        self.instancias[instancia] = {"concepto": cid, "visto": ahora}
        if len(self.instancias) > self.MAX_INSTANCIAS:
            del self.instancias[min(self.instancias, key=lambda i: self.instancias[i]["visto"])]
        return cid

    def concepto(self, clase: str) -> Optional[Dict[str, Any]]:
        cid = self._concepto_de.get(clase)
        return self.conceptos.get(cid) if cid else None

    # --- F1: expectativas (dimensión proactiva, decisión 24) ----------------------
    MAX_MODELO = 1000            # entradas (sistema, verbo, clase); se olvida la usada hace más tiempo
    N_MAX_MODELO = 10            # la media del modelo pesa como mucho 10 experiencias (sigue los cambios)
    UMBRAL_SORPRESA = 0.1        # error de predicción a partir del cual hay sorpresa
    PARECIDO_CONCEPTO = 0.2      # distancia máxima entre prototipos para generalizar de un concepto a otro

    @staticmethod
    def _distancia(a: Dict[str, float], b: Dict[str, float]) -> float:
        claves = set(a) | set(b)
        return sum(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in claves) / len(claves) if claves else 1.0

    def esperar(self, sistema: str, verbo: str, clase: str) -> Optional[Tuple[Dict[str, float], str]]:
        """Lo que se espera que cambie cada variable si ``sistema`` hace ``verbo`` sobre ``clase``, y de dónde
        sale: lo vivido con esa clase («episodios»); si no, lo vivido con la clase de concepto más parecido
        («concepto»); para S2, la valencia del nodo del grafo semántico («grafo»). None si no hay base."""
        entrada = self.modelo.get((sistema, verbo, clase))
        if entrada is not None:
            return {k: m for k, (_, m) in entrada["vars"].items()}, "episodios"
        propio = self.concepto(clase)
        if propio is not None:
            mejor: Optional[Tuple[float, str]] = None
            for otra in sorted(self._modelo_por.get((sistema, verbo), ())):
                otro = self.concepto(otra)
                if otro is None:
                    continue
                d = self._distancia(propio["prototipo"], otro["prototipo"])
                if d <= self.PARECIDO_CONCEPTO and (mejor is None or d < mejor[0]):
                    mejor = (d, otra)
            if mejor is not None:
                return {k: m for k, (_, m) in self.modelo[(sistema, verbo, mejor[1])]["vars"].items()}, "concepto"
        nodo = self.grafo.get(f"Objeto:{clase}")
        if sistema == "S2" and nodo is not None and nodo.get("usos", 0) > 0:
            return {"valencia": round(float(nodo["valencia"]) / float(nodo["usos"]), 4)}, "grafo"
        return None

    def contrastar(self, sistema: str, verbo: str, clase: str, observado: Dict[str, float], ahora: int) -> Optional[float]:
        """Compara lo observado con lo esperado (si había expectativa), cuenta acierto o fallo (los contadores
        del error de predicción que ya usa el feedback de S3) y aprende la transición. Devuelve el error."""
        esperado = self.esperar(sistema, verbo, clase)
        error: Optional[float] = None
        if esperado is not None:
            exp = esperado[0]
            if "valencia" in exp:
                obs_val = observado.get("placer", 0.0) - observado.get("estres", 0.0)
                error = abs(obs_val - exp["valencia"])
            else:
                error = sum(abs(observado.get(k, 0.0) - e) for k, e in exp.items())
            error = round(error, 4)
            if error >= self.UMBRAL_SORPRESA:
                self.fallos += 1
            else:
                self.aciertos += 1
        clave = (sistema, verbo, clase)
        entrada = self.modelo.setdefault(clave, {"vars": {}, "ultimo": ahora})
        entrada["ultimo"] = ahora
        variables = dict(observado)
        if sistema == "S2":
            variables["valencia"] = observado.get("placer", 0.0) - observado.get("estres", 0.0)
            variables = {"valencia": variables["valencia"]}
        for k, v in variables.items():
            n, m = entrada["vars"].get(k, (0, 0.0))
            n = min(n + 1, self.N_MAX_MODELO)
            entrada["vars"][k] = (n, round(m + (v - m) / n, 4))
        self._modelo_por.setdefault((sistema, verbo), set()).add(clase)
        if len(self.modelo) > self.MAX_MODELO:
            viejo = min(self.modelo, key=lambda c: self.modelo[c]["ultimo"])
            del self.modelo[viejo]
            self._modelo_por.get((viejo[0], viejo[1]), set()).discard(viejo[2])
        return error

    REPASO_FUERZA = 1.1            # E6: refuerzo de un nodo repasado
    REPASO_CONFIANZA = 0.02        # E6: refuerzo de las hipótesis de la clase repasada
    REPASO_VENTANA = 100           # E6: latidos hacia atrás que cuentan como «reciente»

    def recientes_para_repaso(self, ahora: int, n: int = 2) -> List[Tuple[str, str]]:
        """Lo reciente de más fuerza (decisión 21): nodos del grafo de los últimos ``REPASO_VENTANA``
        latidos o, si aún no hay grafo, lo mejor del búfer del día. Devuelve (nodo, clase)."""
        nodos = [(d["fuerza"], k, d.get("clase", "")) for k, d in self.grafo.items() if ahora - d.get("ultimo", 0) <= self.REPASO_VENTANA]
        if not nodos:
            nodos = [(punt, self.nodo(p), p.get("clase", "")) for punt, _, p in self.diurno]
        return [(k, c) for _, k, c in sorted(nodos, reverse=True)[:n]]

    def repasar(self, nodo: str, clase: str, ahora: int) -> None:
        """Repaso en calma: refuerza el nodo y las hipótesis de su clase, y las refresca."""
        if nodo in self.grafo:
            self.grafo[nodo]["fuerza"] = round(self.grafo[nodo]["fuerza"] * self.REPASO_FUERZA, 4)
            self.grafo[nodo]["ultimo"] = ahora
        for (c, _), p in self.saber.items():
            if c == clase and p.estado(ahora) == EstadoSaber.HIPOTESIS:
                p.c_exp = acotar(p.c_exp + self.REPASO_CONFIANZA)
                p.actualizada = max(p.actualizada, ahora)

    def reconsolidar(self, clave: Tuple[str, Relacion], ahora: int, arousal: float) -> None:
        """Decisión 22: un recuerdo recuperado vuelve a ser modificable; se refresca (no envejece) y, si
        hay búfer diurno, entra en él para persistirse de noche."""
        p = self.saber.get(clave)
        if p is not None:
            p.actualizada = max(p.actualizada, ahora)
        if self.diurno is not None:
            self._orden_diurno += 1
            pieza = {"latido": ahora, "tipo": "Recuerdo", "id": f"{clave[0]}|{clave[1].name}", "arousal": arousal, "clase": clave[0],
                     "sistema": "S2", "puntuacion": arousal}
            if len(self.diurno) < self.CAPACIDAD_DIURNO:
                heapq.heappush(self.diurno, (arousal, self._orden_diurno, pieza))
            elif arousal > self.diurno[0][0]:
                heapq.heapreplace(self.diurno, (arousal, self._orden_diurno, pieza))

    def ver_clase(self, clase: str) -> int:
        self.clases_vistas[clase] = self.clases_vistas.get(clase, 0) + 1
        return self.clases_vistas[clase]

    def recordar_lugar(self, lugar: str, bienestar: float) -> None:
        previo = self.lugares.get(lugar, 0.0)
        self.lugares[lugar] = 0.7 * previo + 0.3 * bienestar

    def hogar(self) -> Optional[str]:
        if not self.lugares:
            return None
        lugar, valor = max(self.lugares.items(), key=lambda kv: kv[1])
        return lugar if valor > 0.2 else None

    # --- hipocampo: mapa topológico y células de lugar (sin herencia) -------
    def registrar_transicion(self, origen: str, destino: str, ahora: int) -> None:
        if not self.activa or not origen or not destino or origen == destino:
            return
        vecinos = self.mapa.setdefault(origen, {})
        if destino in vecinos:
            a = vecinos[destino]
            a.usos += 1
            a.ultimo_latido = ahora
        else:
            vecinos[destino] = Arista(usos=1, ultimo_latido=ahora)
        self.mapa.setdefault(destino, {})
        while len(self.mapa) > self.MAX_NODOS_MAPA:
            self._podar_mapa()

    def _podar_mapa(self) -> None:
        """Elimina el nodo más antiguo (menor actividad entre aristas salientes/entrantes) si excede MAX_NODOS_MAPA."""
        if len(self.mapa) <= self.MAX_NODOS_MAPA:
            return
        def frescura(nodo: str) -> int:
            if nodo in self.mapa and self.mapa[nodo]:
                return max(a.ultimo_latido for a in self.mapa[nodo].values())
            # Si no tiene aristas salientes, mirar entrantes o 0
            entrantes = [vecs[nodo].ultimo_latido for vecs in self.mapa.values() if nodo in vecs]
            return max(entrantes, default=0)
        # No podar los recién añadidos si tienen 0 todavía excepto si es viejo
        peor = min(self.mapa.keys(), key=frescura)
        del self.mapa[peor]
        for vecinos in self.mapa.values():
            vecinos.pop(peor, None)

    def registrar_donde(self, clase: str, ubicacion: str, ahora: int, confianza: float = 1.0) -> None:
        if not self.activa or not clase or not ubicacion:
            return
        self.donde[clase] = RecuerdoLugar(ubicacion=ubicacion, ultimo_latido=ahora, confianza=confianza)

    def donde_esta(self, clase: str) -> Optional[str]:
        if not self.activa:
            return None
        rec = self.donde.get(clase)
        return rec.ubicacion if rec is not None else None

    def olvidar_donde(self, clase: str) -> None:
        self.donde.pop(clase, None)

    def valor_lugar(self, lugar: str) -> float:
        return self.mapa_valores.get(lugar, 0.0)

    @staticmethod
    def _eliminar_bucles_trayectoria(trayectoria: List[str]) -> List[str]:
        """Elimina ciclos reteniendo una ruta simple donde cada paso consecutivo fue una transición real."""
        if not trayectoria:
            return []
        pila: List[str] = []
        posiciones: Dict[str, int] = {}
        for nodo in trayectoria:
            if not nodo:
                continue
            if nodo in posiciones:
                idx = posiciones[nodo]
                for n in pila[idx + 1:]:
                    posiciones.pop(n, None)
                pila = pila[:idx + 1]
            else:
                posiciones[nodo] = len(pila)
                pila.append(nodo)
        return pila

    def camino(self, origen: str, destino: str, max_profundidad: int = 30) -> Optional[List[str]]:
        """Bloque F, F2: la ruta completa de ``origen`` a ``destino`` (ambos incluidos) por el mapa, con el
        mismo BFS y el mismo orden de vecinos que ``ruta``. Se usa al construir un plan, no en cada latido."""
        if not self.activa or not origen or not destino or origen == destino:
            return None
        if origen not in self.mapa or destino not in self.mapa:
            return None
        padre: Dict[str, str] = {}
        cola: deque[Tuple[str, int]] = deque([(origen, 0)])
        visitados = {origen}
        while cola:
            actual, prof = cola.popleft()
            if prof >= max_profundidad:
                continue
            vecinos = sorted(
                self.mapa.get(actual, {}).items(),
                key=lambda kv: (-kv[1].valor_replay if kv[1].valor_replay != 0.0 else 0.0, -kv[1].usos)
                if self.con_replay else -kv[1].usos,
            )
            for sig, _ in vecinos:
                if sig in visitados:
                    continue
                visitados.add(sig)
                padre[sig] = actual
                if sig == destino:
                    camino = [destino]
                    while camino[-1] != origen:
                        camino.append(padre[camino[-1]])
                    return camino[::-1]
                cola.append((sig, prof + 1))
        return None

    def ruta(self, origen: str, destino: str, max_profundidad: int = 30) -> Optional[str]:
        """Devuelve el siguiente salto desde ``origen`` hacia ``destino`` mediante BFS acotado."""
        if not self.activa or not origen or not destino or origen == destino:
            return None
        if origen not in self.mapa or destino not in self.mapa:
            return None
        cola: deque[Tuple[str, Optional[str], int]] = deque([(origen, None, 0)])
        visitados = {origen}
        while cola:
            actual, primer_salto, prof = cola.popleft()
            if prof >= max_profundidad:
                continue
            # Orden determinista respetando inserción y preferencia por mayor valor_replay y luego usos
            vecinos = sorted(
                self.mapa.get(actual, {}).items(),
                key=lambda kv: (-kv[1].valor_replay if kv[1].valor_replay != 0.0 else 0.0, -kv[1].usos)
                if self.con_replay else -kv[1].usos,
            )
            for sig, _ in vecinos:
                salto = primer_salto if primer_salto is not None else sig
                if sig == destino:
                    return salto
                if sig not in visitados:
                    visitados.add(sig)
                    cola.append((sig, salto, prof + 1))
        return None

    # --- sueño: lo costoso, fuera del camino crítico --------------------------
    REDUCCION_GRAFO = 0.9          # E4: factor nocturno sobre las fuerzas del grafo semántico
    PODA_GRAFO = 0.05              # E4: fuerza por debajo de la cual se poda un nodo o relación
    REDUCCION_HIPOTESIS = 0.95     # E4: factor nocturno de referencia (= 1 − Proposicion.DECAY); cada hipótesis usa su decay
    PODA_HIPOTESIS = 0.15          # E4: confianza por debajo de la cual se poda una hipótesis

    def reducir(self, ahora: int) -> int:
        """Reducción nocturna (decisión 21, homeostasis sináptica): todas las fuerzas del grafo y la
        confianza de las hipótesis no demostradas se reducen en proporción (se mantienen las diferencias
        relativas) y se poda lo que cae por debajo del umbral. Devuelve lo podado."""
        podado = 0
        for nodo in list(self.grafo):
            self.grafo[nodo]["fuerza"] = round(self.grafo[nodo]["fuerza"] * self.REDUCCION_GRAFO, 4)
            if self.grafo[nodo]["fuerza"] < self.PODA_GRAFO:
                del self.grafo[nodo]
                podado += 1
        for clave in list(self.relaciones):
            self.relaciones[clave] = round(self.relaciones[clave] * self.REDUCCION_GRAFO, 4)
            if self.relaciones[clave] < self.PODA_GRAFO or clave[0] not in self.grafo or clave[1] not in self.grafo:
                del self.relaciones[clave]
                podado += 1
        for clave, p in list(self.saber.items()):
            if p.estado(ahora) == EstadoSaber.DEMOSTRADA:
                continue
            p.c_exp = acotar(p.c_exp * (1.0 - p.decay))   # metadato decay (por defecto, ×REDUCCION_HIPOTESIS)
            if p.confianza < self.PODA_HIPOTESIS:
                del self.saber[clave]
                podado += 1
        return podado

    def consolidar(self, ahora: int, reduccion: bool = False) -> Dict[str, int]:
        """Olvido, consolidación y replay inverso de trayectorias. Lo demostrado y lo de arousal extremo no se olvida.
        Con ``reduccion`` (bloque E, E4), la reducción nocturna sustituye al olvido de hipótesis por antigüedad."""
        olvidadas = 0
        if reduccion:
            olvidadas = self.reducir(ahora)
        for clave, p in list(self.saber.items()) if not reduccion else []:
            estado = p.estado(ahora)
            if estado == EstadoSaber.DEMOSTRADA:
                continue
            if estado == EstadoSaber.HIPOTESIS and ahora - p.actualizada > 150 and p.confianza < 0.4:
                del self.saber[clave]
                olvidadas += 1
        recuerdos_olvidados = 0
        for clave_r, r in list(self.registros.items()):
            if r.n == 1 and abs(r.media) < 0.5 and ahora - r.ultimo > 200:
                del self.registros[clave_r]
                recuerdos_olvidados += 1
        aristas_olvidadas = 0
        for vecs in list(self.mapa.values()):
            for dest, ar in list(vecs.items()):
                if ar.usos <= 1 and ahora - ar.ultimo_latido > self.EDAD_OLVIDO_MAPA:
                    del vecs[dest]
                    aristas_olvidadas += 1
        for clase_d, rec in list(self.donde.items()):
            if ahora - rec.ultimo_latido > self.EDAD_OLVIDO_MAPA:
                del self.donde[clase_d]
        # Del búfer solo sobrevive lo de arousal alto (lo demás ya está agregado en registros)
        self.buffer = [p for p in self.buffer if p["arousal"] >= 0.85]

        # Replay inverso de trayectorias recientes al dormir (Fase 2)
        episodios_replay = 0
        if self.con_replay and self.activa:
            gamma = 0.8
            nodos_actualizados: set[str] = set()
            aristas_actualizadas: set[Tuple[str, str]] = set()
            for ep in self.episodios[self._ultimo_consolidar_ep:]:
                episodios_replay += 1
                if not ep.trayectoria or ep.balance == 0.0:
                    continue
                ruta_simple = self._eliminar_bucles_trayectoria(ep.trayectoria)
                if not ruta_simple:
                    continue
                recompensa = ep.balance
                for i, nodo in enumerate(reversed(ruta_simple)):
                    descuento = gamma ** i
                    delta = round(recompensa * descuento, 4)
                    if nodo not in self.mapa_valores:
                        self.mapa_valores[nodo] = delta
                    else:
                        self.mapa_valores[nodo] = round(0.7 * self.mapa_valores[nodo] + 0.3 * delta, 4)
                    nodos_actualizados.add(nodo)
                for orig, dest in zip(ruta_simple[:-1], ruta_simple[1:], strict=False):
                    if orig in self.mapa and dest in self.mapa[orig]:
                        ar = self.mapa[orig][dest]
                        v_dest = self.mapa_valores.get(dest, 0.0)
                        if ar.valor_replay == 0.0:
                            ar.valor_replay = v_dest
                        else:
                            ar.valor_replay = round(0.7 * ar.valor_replay + 0.3 * v_dest, 4)
                        aristas_actualizadas.add((orig, dest))
            self._ultimo_consolidar_ep = len(self.episodios)
            # Decaimiento pasivo de valores espaciales antiguos no reforzados en este sueño
            for n in list(self.mapa_valores.keys()):
                if n not in nodos_actualizados:
                    self.mapa_valores[n] = round(self.mapa_valores[n] * 0.9, 4)
                    if abs(self.mapa_valores[n]) < 0.01:
                        del self.mapa_valores[n]
            for orig, vecs in self.mapa.items():
                for dest, ar in vecs.items():
                    if (orig, dest) not in aristas_actualizadas and ar.valor_replay != 0.0:
                        ar.valor_replay = round(ar.valor_replay * 0.9, 4)
                        if abs(ar.valor_replay) < 0.01:
                            ar.valor_replay = 0.0

        return {
            "hipotesis_olvidadas": olvidadas,
            "recuerdos_olvidados": recuerdos_olvidados,
            "aristas_olvidadas": aristas_olvidadas,
            "episodios_replay": episodios_replay,
        }

    # --- herencia dentro del linaje (barrera de Weismann) ----------------------
    def legado(self, ahora: int) -> Dict[str, Any]:
        """Lo que pasa al linaje: lo demostrado y la memoria colectiva de S1 (recuerdos agregados)."""
        return {
            "proposiciones": [
                {"sujeto": p.sujeto, "relacion": p.relacion.name, "confianza": round(p.confianza, 3)}
                for p in self.saber.values()
                if p.estado(ahora) == EstadoSaber.DEMOSTRADA
            ],
            "registros": [
                {"verbo": v.name, "clase": c, "n": r.n, "media": round(r.media, 3)}
                for (v, c), r in self.registros.items()
                if r.n >= 2
            ],
        }

    def heredar(self, legado: Dict[str, Any], tasa: float = 1.0) -> int:
        """Lo heredado entra como hipótesis fuerte: hace falta experiencia propia para demostrarlo.
        Con ``tasa`` < 1 (bloque E, E7) solo pasa esa fracción de cada parte del legado: las
        proposiciones de más confianza y los registros con más experiencias (redondeo hacia arriba)."""
        if not self.activa:
            return 0
        proposiciones = list(legado.get("proposiciones", []))
        registros = list(legado.get("registros", []))
        if tasa < 1.0:
            def parte(xs: List[Dict[str, Any]], clave: str) -> List[Dict[str, Any]]:
                k = math.ceil(max(0.0, tasa) * len(xs))
                return sorted(xs, key=lambda d: -float(d[clave]))[:k]
            proposiciones = parte(proposiciones, "confianza")
            registros = parte(registros, "n")
        n = 0
        for d in proposiciones:
            p = Proposicion(d["sujeto"], Relacion[d["relacion"]], confianza=float(d["confianza"]) * 0.8)
            p.confirmaciones = Proposicion.CONFIRMACIONES_MINIMAS - 1
            p.heredada = True
            self.saber[(p.sujeto, p.relacion)] = p
            n += 1
        for d in registros:
            r = Registro(n=max(1, int(d["n"]) // 2))
            r.suma = float(d["media"]) * r.n
            self.registros[(Verbo[d["verbo"]], d["clase"])] = r
            n += 1
        return n
