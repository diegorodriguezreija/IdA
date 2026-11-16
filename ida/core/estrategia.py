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
(estado interno de la máquina de la propia estrategia, decisión 17) y ``reflejo``.

Progreso y agotamiento (decisión 16): el progreso se mide sobre la **intensidad cruda** del impulso,
no sobre su arousal modulado. Tras unos latidos de gracia, el agotamiento crece si el progreso por
latido es menor que el esperado y baja si es mejor (teorema del valor marginal).
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ida.core.pieza import Pieza, acotar
from ida.core.vocabulario import Verbo

ACTIVA = "activa"
COMPLETADA = "completada"        # la necesidad bajó del objetivo
SIN_OBJETO = "sin_objeto"        # dejó de ser elegible (no hay a qué aplicarla)
AGOTADA = "agotada"              # se abandona por esfuerzo sin progreso
TERMINADA = "terminada"          # un reflejo cumplió su duración fija

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
    """

    nombre: str = "estrategia"
    impulsos: Tuple[str, ...] = ()
    prioridad: int = 0
    reflejo: bool = False
    ultimo_recurso: bool = False

    def elegible(self, ctx: Any, impulso: str, intensidad: float) -> bool:
        return True

    def actuar(self, ctx: Any, estrategia: Pieza) -> Optional[Propuesta]:
        return None


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


def nueva(sistema: str, definicion: Definicion, impulso: str, intensidad: float, objetivo: float, latido: int) -> Pieza:
    """Pieza ``Estrategia`` recién activada para ``impulso``."""
    return Pieza(
        id=f"{sistema}:{definicion.nombre}:{impulso}",
        tipo="Estrategia",
        arousal=acotar(intensidad),
        carga={"nombre": definicion.nombre, "impulso": impulso, "valor_inicial": acotar(intensidad), "objetivo": objetivo,
               "progreso": 0.0, "agotamiento": 0.0, "esfuerzo": 0, "inicio": latido, "estado": ACTIVA, "paso": 0,
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
