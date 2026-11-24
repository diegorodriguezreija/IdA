"""Contrato entre el framework y un mundo.

Un mundo traduce su realidad al vocabulario común (``ida.nucleo.vocabulario``):
- en cada latido entrega una ``Observacion`` con entidades que llevan ``rasgos`` con significado;
- ejecuta los verbos que declara y devuelve un ``Efecto``; o, si declara primitivas (``primitivas()``), ejecuta las que
  le pide el Core (traducidas por el Motor de su cuerpo) y devuelve el ``Efecto`` en bruto.

El framework no sabe nada más del mundo. Si un mundo necesita razonamiento propio, lo aporta
a través de su registro (``registro()``), declarado como tal.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

from ida.nucleo.vocabulario import RASGOS, Verbo

if TYPE_CHECKING:
    from ida.nucleo.arquitectura import Componente, Contexto
    from ida.nucleo.pieza import Pieza


@dataclass
class Alta:
    añade: List[Any] = field(default_factory=list)        # en el orden declarado
    sustituye: Dict[str, Any] = field(default_factory=dict) # nombre de CLASE del general -> sustituto


class Cuerpo:
    """Familia de cuerpos (D10): lo que comparten los mundos con el mismo tipo de cuerpo (p. ej. una cuadrícula 2D con
    orientación). La implementa ``ida/cuerpos/<familia>`` y la registra el mundo (``Registro.cuerpo``): el Core recibe
    el objeto y nunca importa ``ida/cuerpos`` (D2).

    ``componentes()``: destino -> Componentes, en orden. Destinos válidos: los del registro y ``CORE.Actuar``. El Core
    los monta antes que los del mundo, con las reglas de ``añade``, y les pone ``de_cuerpo = nombre``."""

    nombre: str = ""

    def componentes(self) -> Dict[str, List["Componente"]]:
        return {}

    def seccion_memoria(self, perfil: "Perfil") -> Optional[Tuple[str, Any]]:
        """Memoria (D7): la sección de la que el cuerpo es dueño, como (nombre, sección), o None."""
        return None

    def motor(self) -> Optional["Motor"]:
        """Capa motora del cuerpo (D9), o None: sin ella, el Core ejecuta verbos. Expone la cuenta de primitivas
        ejecutadas (``Motor.ejecutadas``, copia eferente)."""
        return None

    def ir_por_el_mapa(
        self, ctx: "Contexto", clase: str, confianza: float = 0.5, excluir: frozenset = frozenset()
    ) -> Optional[Any]:
        """Búsqueda de material en el mapa de la memoria si el cuerpo ofrece esa navegación (D16)."""
        return None


class Motor:
    """Capa motora de un cuerpo (D9): una biblioteca, no un Componente. Traduce la intención decidida (la pieza
    ``decision`` del Tribunal) a las primitivas del mundo leyendo piezas, y juzga su éxito comparando lo pretendido con
    lo medido en bruto (``Efecto.medidas``). Lleva la cuenta de las primitivas ejecutadas (copia eferente)."""

    def __init__(self) -> None:
        self.ejecutadas: Dict[str, int] = {}

    def primitivas(self, intencion: "Pieza", ctx: "Contexto", disponibles: List[str]) -> List[str]:
        """Las primitivas para la intención, o [] si no se cumple su precondición (no se toca el mundo)."""
        return []

    def juzgar(self, intencion: "Pieza", primitivas: List[str], efecto: "Efecto") -> bool:
        """Si la intención tuvo éxito, con lo medido en bruto."""
        return bool(primitivas)

    def contar(self, primitivas: List[str]) -> None:
        for p in primitivas:
            self.ejecutadas[p] = self.ejecutadas.get(p, 0) + 1


@dataclass
class Registro:
    componentes: Dict[str, Alta] = field(default_factory=dict)  # destino -> Alta
    estrategias: Dict[str, Alta] = field(default_factory=dict)  # "S1" | "S2" | "S3" -> Alta
    cuerpo: Optional[Cuerpo] = None                              # familia de cuerpos (D10), o ninguna
    opcionales: List[str] = field(default_factory=list)         # nombres de CLASE de los generales opcionales que monta (D3)


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
    medidas: Dict[str, Any] = field(default_factory=dict)  # lo medido en bruto para juzgar el éxito (p. ej. inventario antes y después)


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


# Mecanismos de los bloques E y F (docs/MEDICIONES_E.md, docs/MEDICIONES_F.md, docs/VEREDICTO_E_F.md).
# Ningún mundo los declara: no mejoraron ninguno. Se activarán por mundo solo donde se demuestre su valor.
MEMORIA_E = MecanismosMemoria(buffer=True, consolidacion=True, conceptos=True, reduccion=True, evocacion=True, repaso=True)
# E + Expectativa (F1) y Plan (F2).
MEMORIA_EF = MecanismosMemoria(buffer=True, consolidacion=True, conceptos=True, reduccion=True, evocacion=True, repaso=True,
                               expectativa=True, plan=True)


@dataclass(frozen=True)
class Escala:
    """Constantes de escala del mundo que usan los Componentes y estrategias generales (D15). Por defecto, los valores
    de antes de A6a; el mundo que los usa los fija en su ``Perfil``. Lo que no depende de la escala (proporciones
    internas, pesos de previos, ventanas) se queda en su Componente."""

    dano_previo: float = 100.0 * 2.0 / 9.0   # Amenaza: daño de un golpe de lo peligroso sin datos, en vitalidad (0-100)
    golpes_previo: float = 10.0              # Amenaza: golpes para derribar algo sin datos (pesimista)
    margen_lugar: int = 3                    # Amenaza: casillas más allá del alcance a las que se anula el peligro de un lugar
    reserva: float = 100.0 * 3.0 / 9.0       # Afrontar: vitalidad que una lucha debe dejar intacta
    coste_sin_sitio: float = 45.0            # Impulso (alostasis): horizonte del cobijo sin ningún sitio, en pasos
    coste_recordado: float = 15.0            # S3: coste estimado de ir a una casilla recordada (en pasos)
    coste_por_proximidad: float = 10.0       # S3: escala del coste por proximidad (en pasos)
    coste_sin_productor: float = 30.0        # S3: coste de reponer algo sin acción conocida (2 * coste_recordado)


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
    corto_plazo: int = 8              # N ondas en la memoria a corto plazo (D13)
    necesidades: Tuple[Necesidad, ...] = NECESIDADES_BASE   # de cada una sale un impulso de S1
    intenciones: Tuple[str, ...] = ()         # intenciones deliberadas propias del mundo (S3), además de «saber»
    mecanismos: MecanismosMemoria = MecanismosMemoria()   # memoria del bloque E (interruptores)
    # Estrategias y reflejo (bloque C, decisiones 4, 6 y 16)
    umbral_reflejo: float = 0.4               # salto del peligro entre latidos que dispara el reflejo
    duracion_reflejo: int = 3                 # latidos fijos que dura el reflejo
    gracia_estrategia: int = 10               # latidos antes de que una estrategia pueda agotarse
    ritmo_esperado_estrategia: float = 0.02   # progreso por latido esperado (por defecto, sin aprender)
    enfriamiento_estrategia: int = 10         # latidos sin volver a elegir una estrategia agotada
    # Rasgos valorados ("peligro", "nutritivo", "recurso", "novedad") entregados hechos por el mundo (D4)
    rasgos_declarados: Tuple[str, ...] = ()
    escala: Escala = Escala()   # constantes de escala de los generales (D15)
    # La aliestesia (paso 0b) ya no es una perilla: la tiene el mundo que registra ``Apetencia`` (D3, D15).


class Mundo(ABC):
    nombre: str = "mundo"
    perfil: Perfil = Perfil()

    @abstractmethod
    def reiniciar(self, semilla: Optional[int]) -> None:
        """Prepara un episodio nuevo (una vida)."""

    @abstractmethod
    def observar(self) -> Observacion:
        """Lo que se percibe ahora."""

    def ejecutar(self, verbo: Verbo, objetivo: str, datos: Dict[str, Any]) -> Efecto:
        """Materializa una Ejecución en el mundo (mundos sin primitivas: sus verbos son sus primitivas)."""
        raise NotImplementedError(f"El mundo {self.nombre!r} no ejecuta verbos: ejecuta primitivas")

    def primitivas(self) -> Optional[List[str]]:
        """Acciones elementales del mundo (D9), o None si el mundo ejecuta verbos. Con primitivas, el Motor del cuerpo
        traduce cada intención y el Core llama a ``ejecutar_primitivas``."""
        return None

    def ejecutar_primitivas(self, primitivas: List[str], intencion: Optional[Verbo] = None) -> Efecto:
        """Ejecuta la secuencia y devuelve el efecto en bruto (``exito`` True: el éxito lo juzga el Motor del cuerpo, con
        ``Efecto.medidas``). ``intencion`` no cambia lo que se ejecuta."""
        raise NotImplementedError(f"El mundo {self.nombre!r} no ejecuta primitivas")

    @abstractmethod
    def verbos(self) -> Set[Verbo]:
        """Verbos que este mundo sabe ejecutar."""

    def terminado(self) -> bool:
        """El mundo ha terminado la vida (fin de partida, límite propio...)."""
        return False

    def registro(self) -> Registro:
        """Registro declarado de Componentes, estrategias y cuerpo del mundo (decisión D3)."""
        return Registro()

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
