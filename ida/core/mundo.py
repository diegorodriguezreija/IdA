"""Contrato entre el framework y un mundo.

Un mundo traduce su realidad al vocabulario común (``ida.core.vocabulario``):
- en cada latido entrega una ``Observacion`` con entidades que llevan ``rasgos`` con significado;
- ejecuta los verbos que declara y devuelve un ``Efecto``.

El framework no sabe nada más del mundo. Si un mundo necesita razonamiento propio, lo aporta
como componentes adicionales (``componentes_propios``), declarados como tales.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from ida.core.vocabulario import RASGOS, Verbo


@dataclass
class Entidad:
    """Algo que el individuo percibe. ``id`` estable entre latidos; ``clase`` es la etiqueta del mundo."""

    id: str
    clase: str
    rasgos: Dict[str, float]
    datos: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        desconocidos = set(self.rasgos) - set(RASGOS)
        if desconocidos:
            raise ValueError(f"Rasgos desconocidos en {self.id}: {sorted(desconocidos)}")
        self.rasgos = {k: float(max(0.0, min(1.0, v))) for k, v in self.rasgos.items()}


@dataclass
class Observacion:
    """Lo que el mundo entrega en un latido."""

    ubicacion: str                                   # dónde está el individuo
    entidades: List[Entidad]                         # incluye los lugares (rasgo ``lugar``)
    vitales: Optional[Dict[str, float]] = None       # constantes propias del mundo (0-100), si las tiene
    inventario: Optional[Dict[str, float]] = None    # lo que lleva encima, si el mundo lo tiene (propiocepción)
    cuerpo: Optional[Dict[str, Any]] = None           # postura u orientación, si el mundo la tiene (propiocepción)
    ambiente: Optional[Dict[str, float]] = None       # condiciones del entorno, p. ej. la luz (sensor Ambiente)
    dormido: Optional[bool] = None                   # si el mundo decide cuándo se duerme y se despierta
    mensaje: str = ""                                # texto libre para la consola


@dataclass
class Efecto:
    """Consecuencia de ejecutar un verbo."""

    exito: bool = True
    delta: Dict[str, float] = field(default_factory=dict)  # cambios en el soma: alimentacion, vitalidad, energia...
    causa: Optional[str] = None      # clase de la entidad que causó un daño, si el mundo lo sabe
    obtenido: Optional[str] = None   # clase de lo obtenido (comido, recogido, fabricado)
    muerte: bool = False
    mensaje: str = ""


@dataclass(frozen=True)
class Necesidad:
    """Una necesidad del cuerpo que el mundo declara a partir de sus constantes vitales (0-100).

    De cada necesidad sale un impulso de S1 (decisión 1 del autor sobre C0). Su déficit, en [0, 1],
    es la intensidad cruda del impulso: 0 desde el nivel de ``confort``, 1 con la constante a 0.
    Con varias constantes, cuenta la más baja. ``rasgo`` es el rasgo del vocabulario común que la
    satisface (p. ej. ``nutritivo``), si lo hay: así las estrategias genéricas saben a qué sirven.
    """

    nombre: str
    constantes: Tuple[str, ...]
    confort: float = 100.0
    rasgo: Optional[str] = None

    def deficit(self, valores: Dict[str, float]) -> Optional[float]:
        presentes = [valores[c] for c in self.constantes if c in valores]
        if not presentes or self.confort <= 0:
            return None
        return float(max(0.0, min(1.0, (self.confort - min(presentes)) / self.confort)))


# Las del metabolismo interno de ``Soma`` (mundos que no marcan sus constantes).
NECESIDADES_BASE: Tuple[Necesidad, ...] = (
    Necesidad("hambre", ("alimentacion",), 95.0, "nutritivo"),
    Necesidad("cansancio", ("energia", "descanso"), 60.0),
    Necesidad("salud", ("vitalidad",), 100.0),
)


@dataclass(frozen=True)
class MecanismosMemoria:
    """Interruptores de los mecanismos de memoria del bloque E (decisiones 19 a 22) y de los del bloque F. Todos apagados:
    IdA se comporta como ``base-v2.0``. Cada uno se activa por separado. (El paso 3, «proteger X», está siempre activo.)"""

    buffer: bool = False          # E1: búfer diurno de tamaño fijo y episodio del día
    consolidacion: bool = False   # E2: al dormir (o al final de la vida), del búfer al grafo semántico
    conceptos: bool = False       # E3: prototipo de cada clase a partir de sus instancias
    reduccion: bool = False       # E4: reducción nocturna proporcional y poda (sustituye al olvido de hipótesis)
    evocacion: bool = False       # E5: recuperación evocada y reconsolidación
    repaso: bool = False          # E6: repaso en calma de lo reciente
    tasa_herencia: float = 1.0    # E7: fracción de lo aprendido que se hereda (1 = como base-v2.0)
    expectativa: bool = False     # F1: expectativas de S1 y S2 sobre el latido siguiente, contrastadas por el Core
    plan: bool = False            # F2: estrategias como cadena de pasos (Plan)
    material_mapa: bool = False   # deuda 11c: el planificador busca el material también en el mapa local (S3)


# Mecanismos de los bloques E y F (docs/MEDICIONES_E.md, docs/MEDICIONES_F.md, docs/VEREDICTO_E_F.md).
# Ningún mundo los declara: no mejoraron ninguno. Se activarán por mundo solo donde se demuestre su valor.
MEMORIA_E = MecanismosMemoria(buffer=True, consolidacion=True, conceptos=True, reduccion=True, evocacion=True, repaso=True)
# E + Expectativa (F1) y Plan (F2).
MEMORIA_EF = MecanismosMemoria(buffer=True, consolidacion=True, conceptos=True, reduccion=True, evocacion=True, repaso=True,
                               expectativa=True, plan=True)


@dataclass
class Perfil:
    """Las pocas perillas de un mundo. Cada una tiene un efecto visible al ejecutar."""

    tiempo_real: bool = False         # True: el mundo avanza aunque IdA no haya terminado (marcapasos)
    frecuencia_ms: float = 100.0      # plazo base del latido (guillotina)
    amplitud: int = 100               # presupuesto base de atención por latido
    memoria: str = "completa"         # "apagada" | "ligera" | "completa"
    duerme: bool = True               # hay sueño (y consolidación) dentro de la vida
    hogar: bool = False               # usa el componente de hogar seguro
    peso_experiencia: float = 0.15    # cuánto sesga la experiencia las puntuaciones del Tribunal
    vitales_propios: bool = False     # el mundo marca las constantes del cuerpo (no el metabolismo interno)
    umbral_apertura_episodio: float = 0.65
    latidos_por_episodio: int = 6
    necesidades: Tuple[Necesidad, ...] = NECESIDADES_BASE   # de cada una sale un impulso de S1
    intenciones: Tuple[str, ...] = ()         # intenciones deliberadas propias del mundo (S3), además de «saber»
    mecanismos: MecanismosMemoria = MecanismosMemoria()   # memoria del bloque E (interruptores)
    # Estrategias y reflejo (bloque C, decisiones 4, 6 y 16)
    umbral_reflejo: float = 0.4               # salto del peligro entre latidos que dispara el reflejo
    duracion_reflejo: int = 3                 # latidos fijos que dura el reflejo
    gracia_estrategia: int = 10               # latidos antes de que una estrategia pueda agotarse
    ritmo_esperado_estrategia: float = 0.02   # progreso por latido esperado (por defecto, sin aprender)
    enfriamiento_estrategia: int = 10         # latidos sin volver a elegir una estrategia agotada

    @property
    def aliestesia(self) -> bool:
        """Paso 0b (``docs/PROPUESTA_PASO0.md``): hay que aprender qué necesidad satisface cada clase cuando dos o
        más necesidades se satisfacen con el mismo rasgo (el rasgo no dice a cuál sirve un objeto). Con una sola
        necesidad por rasgo, el rasgo ya lo dice: satisface = rasgo y la base hace lo de siempre."""
        rasgos = [n.rasgo for n in self.necesidades if n.rasgo]
        return len(rasgos) != len(set(rasgos))


class Mundo(ABC):
    nombre: str = "mundo"
    perfil: Perfil = Perfil()

    @abstractmethod
    def reiniciar(self, semilla: Optional[int]) -> None:
        """Prepara un episodio nuevo (una vida)."""

    @abstractmethod
    def observar(self) -> Observacion:
        """Lo que se percibe ahora."""

    @abstractmethod
    def ejecutar(self, verbo: Verbo, objetivo: str, datos: Dict[str, Any]) -> Efecto:
        """Materializa una Ejecución en el mundo."""

    @abstractmethod
    def verbos(self) -> Set[Verbo]:
        """Verbos que este mundo sabe ejecutar."""

    def terminado(self) -> bool:
        """El mundo ha terminado la vida (fin de partida, límite propio...)."""
        return False

    def componentes_propios(self) -> Dict[str, list]:
        """Componentes adicionales por destino, p. ej. ``{"S3.Reaccionar": [MiComponente()]}``."""
        return {}

    def estrategias_propias(self) -> Dict[str, list]:
        """Estrategias propias del mundo por sistema (``Definicion`` de ``ida.core.estrategia``),
        p. ej. ``{"S1": [MiDefensa()]}``. Se añaden al catálogo del componente ``Estrategia``."""
        return {}

    def manual(self) -> Dict[str, Any]:
        """Hechos declarados del mundo (instrucciones), con su fuente. Por defecto, ninguno.

        Formato: ``{"hechos": [...], "inventario": [...]}``. Cada hecho es una ``proposicion`` (sujeto,
        relación, veredicto), un ``requisito`` (verbo, objetivo, requiere_inventario, requiere_cerca y,
        si se sabe, efecto) o una ``nota`` (no se carga). ``inventario``, opcional, son las claves del
        inventario percibido que cuentan como objetos. Entra en la memoria al nacer, antes de heredar."""
        return {}

    def puntuacion(self) -> Dict[str, Any]:
        """Resultado del mundo para el resumen de la vida (puntos, logros, resultado...)."""
        return {}

    def vista(self) -> str:
        """Representación de texto del mundo para la consola y la telemetría."""
        return ""

    def cerrar(self) -> None:
        """Libera recursos (navegador, conexiones...)."""
