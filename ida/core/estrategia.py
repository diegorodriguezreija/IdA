"""Estrategias (decisiones 3, 4, 16 y 17 de ``docs/REDISENO_BASE.md``).

Un **impulso** es el porqué: nace del estado sentido y no se elige. Una **estrategia** es el cómo:
dura varios latidos, tiene progreso y se agota. Cada sistema produce sus estrategias desde su
componente ``Estrategia`` (dueño de las piezas ``Estrategia``) y su componente ``Accion`` traduce
la estrategia activa en una acción.

El Core solo define el tipo y lo conserva entre latidos (``Onda.estrategias``). Qué hace cada
estrategia lo concretan los sistemas y los mundos con una ``Definicion``: cuándo es elegible para
un impulso y qué acción propone en cada latido (una máquina de estados determinista).

Datos de la pieza ``Estrategia`` (en ``carga``): ``nombre``, ``impulso`` (referencia al impulso que
la originó), ``valor_inicial`` (intensidad cruda al empezar), ``objetivo`` (umbral por debajo del
cual la necesidad desaparece), ``progreso`` y ``agotamiento`` en [0, 1], ``esfuerzo`` (latidos en
que su acción se ejecutó), ``inicio`` (latido), ``estado`` (activa, completada, agotada...), ``paso``
(estado interno de la máquina de la propia estrategia, decisión 17), ``merito`` (feedback de su impulso
acumulado mientras se ejecutó, decisión 23) y ``reflejo``.

Progreso y agotamiento (decisión 16): el progreso se mide sobre la **intensidad cruda** del impulso,
no sobre su arousal modulado. Tras unos latidos de gracia, el agotamiento crece si el progreso por
latido es menor que el esperado y baja si es mejor (teorema del valor marginal).
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

from ida.core.pieza import Pieza, acotar
from ida.core.vocabulario import Verbo

ACTIVA = "activa"
COMPLETADA = "completada"        # la necesidad bajó del objetivo
SIN_OBJETO = "sin_objeto"        # dejó de ser elegible (no hay a qué aplicarla)
AGOTADA = "agotada"              # se abandona por esfuerzo sin progreso
TERMINADA = "terminada"          # un reflejo cumplió su duración fija
SUSTITUIDA = "sustituida"        # apareció una estrategia elegible más específica o mejor valorada

SUBIDA_AGOTAMIENTO = 0.05        # por latido con progreso menor que el esperado, pasada la gracia
BAJADA_AGOTAMIENTO = 0.10        # por latido con progreso igual o mayor que el esperado


@dataclass
class Propuesta:
    """La acción que una estrategia propone en un latido (verbo genérico y parámetros)."""

    verbo: Verbo
    objetivo: str
    arousal: float
    confianza: float
    motivo: str
    clase: str = ""
    datos: Optional[Dict[str, Any]] = None


class Definicion:
    """Una estrategia concreta: para qué impulsos sirve, cuándo es elegible y qué hace.

    - ``nombre``: identifica la estrategia dentro de su sistema.
    - ``impulsos``: nombres de los impulsos a los que sirve.
    - ``prioridad``: orden innato entre estrategias elegibles con el mismo valor aprendido.
    - ``reflejo``: estrategia innata corta, de duración fija y prioridad máxima (decisión 6).
    - ``ultimo_recurso``: respuesta innata cuando todas las demás del impulso están agotadas.
    - ``rasgo``: sirve también a cualquier impulso cuya necesidad se satisface con ese rasgo.
    - ``cualquier_impulso``: sirve a cualquier impulso (respuestas de último recurso genéricas).
    - ``agotable``: si se abandona por agotamiento. Los planes deliberados de S3 que llevan su propio
      control de fallos no se agotan por falta de progreso de la necesidad.
    """

    nombre: str = "estrategia"
    impulsos: Tuple[str, ...] = ()
    rasgo: Optional[str] = None
    cualquier_impulso: bool = False
    agotable: bool = True
    prioridad: int = 0
    reflejo: bool = False
    ultimo_recurso: bool = False

    def sirve(self, impulso: str, rasgo: Optional[str]) -> bool:
        return self.cualquier_impulso or impulso in self.impulsos or (self.rasgo is not None and self.rasgo == rasgo)

    def elegible(self, ctx: Any, impulso: str, intensidad: float) -> bool:
        return True

    def paso(self, ctx: Any, estrategia: Pieza) -> Any:
        """Fase siguiente de la máquina de estados (decisión 17). Por defecto, una sola fase."""
        return estrategia.carga.get("paso", 0)

    def actuar(self, ctx: Any, estrategia: Pieza) -> Union[None, Propuesta, List[Propuesta]]:
        """La acción del latido, o varias acciones de la misma fase entre las que decide el Tribunal."""
        return None

    def pedir(self, ctx: Any, estrategia: Pieza) -> List[Dict[str, Any]]:
        """Metas instrumentales que la estrategia pide al planificador en este latido: ``{"objeto", "cantidad", "urgencia",
        "motivo"}`` = «tener al menos ``cantidad`` de ``objeto``», con la urgencia de su impulso. Por defecto, ninguna."""
        return []


class Plan(Definicion):
    """Plan (bloque F, F2; decisión 24): una estrategia que es una cadena de pasos hacia su meta.

    Con ``Perfil.mecanismos.plan``, la cadena se construye al activarse (``construir``) y se guarda en
    el estado de la propia estrategia (``paso`` = {"pasos", "i", "rehecho", "fallido"}). Cada latido se
    consumen los pasos cumplidos (``cumplido``); el progreso es la parte completada. Si la expectativa
    del paso en curso falla (``fallido``: la sorpresa de no encontrar lo esperado), el plan se rehace
    hasta ``REHACER`` veces; después queda fallido y la estrategia se agota. Sin el interruptor, la
    definición se comporta como antes (``paso_sin_plan`` y sus propios métodos)."""

    REHACER = 1

    def construir(self, ctx: Any, estrategia: Pieza) -> Optional[List[Dict[str, Any]]]:
        return None

    def cumplido(self, ctx: Any, paso: Dict[str, Any], estado: Dict[str, Any]) -> bool:
        return False

    def fallido(self, ctx: Any, paso: Dict[str, Any], estado: Dict[str, Any]) -> bool:
        return False

    def paso_sin_plan(self, ctx: Any, estrategia: Pieza) -> Any:
        return estrategia.carga.get("paso", 0)

    def paso(self, ctx: Any, estrategia: Pieza) -> Any:
        if not ctx.perfil.mecanismos.plan:
            return self.paso_sin_plan(ctx, estrategia)
        previo = estrategia.carga.get("paso")
        if isinstance(previo, dict) and "pasos" in previo:
            estado = dict(previo)
        else:
            estado = {"pasos": self.construir(ctx, estrategia) or [], "i": 0, "rehecho": 0, "fallido": False}
        if estado["fallido"]:
            return estado
        pasos, i = estado["pasos"], int(estado["i"])
        while i < len(pasos) and self.cumplido(ctx, pasos[i], {**estado, "i": i}):
            i += 1
        estado["i"] = i
        if i < len(pasos) and self.fallido(ctx, pasos[i], estado):
            nuevos = self.construir(ctx, estrategia) if estado["rehecho"] < self.REHACER else None
            if nuevos:
                estado = {"pasos": nuevos, "i": 0, "rehecho": estado["rehecho"] + 1, "fallido": False}
            else:
                estado["fallido"] = True
        return estado


def estado_plan(estrategia: Pieza) -> Optional[Dict[str, Any]]:
    """El estado del plan de una estrategia, si lo tiene."""
    e = estrategia.carga.get("paso")
    return e if isinstance(e, dict) and "pasos" in e else None


def progreso_plan(estado: Optional[Dict[str, Any]]) -> Optional[float]:
    """Parte completada de la cadena, en [0, 1] (None sin plan o con la cadena vacía)."""
    if not estado or not estado["pasos"]:
        return None
    return acotar(int(estado["i"]) / len(estado["pasos"]))


def paso_actual(estrategia: Pieza) -> Optional[Dict[str, Any]]:
    e = estado_plan(estrategia)
    if e is None or e["fallido"] or int(e["i"]) >= len(e["pasos"]):
        return None
    return dict(e["pasos"][int(e["i"])])


class Catalogo:
    """Las definiciones de estrategia de un sistema, por nombre. La comparten su componente
    ``Estrategia`` (que elige) y su componente ``Accion`` (que traduce a acción)."""

    def __init__(self, definiciones: Optional[list] = None):
        self._por_nombre: Dict[str, Definicion] = {}
        for d in definiciones or []:
            self.añadir(d)

    def añadir(self, definicion: Definicion) -> None:
        self._por_nombre[definicion.nombre] = definicion

    def get(self, nombre: str) -> Optional[Definicion]:
        return self._por_nombre.get(nombre)

    def todas(self) -> List[Definicion]:
        return list(self._por_nombre.values())


class ConPropuestas(Definicion):
    """Definición que decide con ``decidir`` y declara sus acciones con ``proponer``, con la misma
    firma que tenían los componentes que proponían directamente (para trasladarlos sin reescribirlos).
    ``actuar`` devuelve lo propuesto en el latido."""

    def __init__(self) -> None:
        self._propuestas: List[Propuesta] = []

    def actuar(self, ctx: Any, estrategia: Optional[Pieza]) -> List[Propuesta]:
        self._propuestas = []
        self.decidir(ctx, estrategia)
        return list(self._propuestas)

    def decidir(self, ctx: Any, estrategia: Optional[Pieza]) -> None:
        pass

    def proponer(self, ctx: Any, verbo: Verbo, objetivo: str, arousal: float, confianza: float, motivo: str,
                 clase: str = "", **datos: Any) -> None:
        if verbo in ctx.verbos:
            self._propuestas.append(Propuesta(verbo, objetivo, arousal, confianza, motivo, clase, dict(datos) or None))


def nueva(sistema: str, definicion: Definicion, impulso: str, intensidad: float, objetivo: float, latido: int, paso: Any = 0) -> Pieza:
    """Pieza ``Estrategia`` recién activada para ``impulso``."""
    return Pieza(
        id=f"{sistema}:{definicion.nombre}:{impulso}",
        tipo="Estrategia",
        arousal=acotar(intensidad),
        carga={"nombre": definicion.nombre, "impulso": impulso, "valor_inicial": acotar(intensidad), "objetivo": objetivo,
               "progreso": 0.0, "agotamiento": 0.0, "esfuerzo": 0, "inicio": latido, "estado": ACTIVA, "paso": paso, "merito": 0.0,
               "reflejo": definicion.reflejo},
        sistema=sistema,
        creada=latido,
        actualizada=latido,
    )


def progreso(carga: Dict[str, Any], intensidad: float) -> float:
    """Fracción recorrida del valor inicial hacia el objetivo, en [0, 1]."""
    tramo = carga["valor_inicial"] - carga["objetivo"]
    if tramo <= 1e-9:
        return 1.0 if intensidad <= carga["objetivo"] else 0.0
    return acotar((carga["valor_inicial"] - intensidad) / tramo)


def avanzar(carga: Dict[str, Any], intensidad: float, ejecutada: bool, latido: int, gracia: int, ritmo_esperado: float) -> Dict[str, Any]:
    """Nuevos valores de progreso, agotamiento y esfuerzo tras un latido (no muta ``carga``)."""
    nuevo = progreso(carga, intensidad)
    ritmo = nuevo - carga["progreso"]
    agotamiento = carga["agotamiento"]
    if latido - carga["inicio"] >= gracia:
        if ritmo >= ritmo_esperado and ritmo > 0.0:
            agotamiento = acotar(agotamiento - BAJADA_AGOTAMIENTO)
        else:
            agotamiento = acotar(agotamiento + SUBIDA_AGOTAMIENTO)
    return {"progreso": nuevo, "agotamiento": agotamiento, "esfuerzo": carga["esfuerzo"] + (1 if ejecutada else 0)}
