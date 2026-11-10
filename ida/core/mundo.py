"""Contrato entre el framework y un mundo.

Un mundo traduce su realidad al vocabulario común (``ida.core.vocabulario``):
- en cada latido entrega una ``Observacion`` con entidades que llevan ``rasgos`` con significado;
- ejecuta los verbos que declara y devuelve un ``Efecto``.

El framework no sabe nada más del mundo. Si un mundo necesita razonamiento propio, lo aporta
como componentes adicionales (``componentes_propios``), declarados como tales.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

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

    def puntuacion(self) -> Dict[str, Any]:
        """Resultado del mundo para el resumen de la vida (puntos, logros, resultado...)."""
        return {}

    def vista(self) -> str:
        """Representación de texto del mundo para la consola y la telemetría."""
        return ""

    def cerrar(self) -> None:
        """Libera recursos (navegador, conexiones...)."""
