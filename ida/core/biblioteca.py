"""Puerto hexagonal para bibliotecas externas de autoridad."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ida.core.vocabulario import Relacion


class Veredicto(str, Enum):
    AFIRMA = "afirma"
    NIEGA = "niega"
    NO_SABE = "no_sabe"
    INVALIDO = "invalido"


class EstadoLectura(str, Enum):
    PENDIENTE = "pendiente"
    DISPONIBLE = "disponible"
    LEIDO = "leido"
    INTERRUMPIDO = "interrumpido"
    SIN_RESPUESTA = "sin_respuesta"
    INVALIDO = "invalido"


@dataclass(frozen=True)
class ElementoConsulta:
    sujeto: str
    relacion: Relacion


@dataclass
class Consulta:
    elementos: List[ElementoConsulta]


@dataclass
class ElementoRespuesta:
    sujeto: str
    relacion: Relacion
    veredicto: Veredicto
    confianza: float = 0.5


@dataclass
class Respuesta:
    elementos: List[ElementoRespuesta] = field(default_factory=list)


class Ticket(ABC):
    """Promesa asíncrona no bloqueante de una respuesta de biblioteca."""

    @abstractmethod
    def lista(self) -> bool:
        """Devuelve True si la respuesta ya está disponible sin bloquear."""
        ...

    @abstractmethod
    def respuesta(self) -> Optional[Respuesta]:
        """Devuelve la Respuesta si está lista, o None si sigue pendiente."""
        ...


class Biblioteca(ABC):
    """Interfaz abstracta de una biblioteca consultable."""

    @abstractmethod
    def solicitar(self, consulta: Consulta) -> Ticket:
        """Emite una consulta asíncrona y devuelve un Ticket inmediatamente."""
        ...


@dataclass
class RegistroLectura:
    """Registro de una consulta de biblioteca efectuada o en curso por el individuo."""

    id: str
    inicio: int
    elementos: List[Tuple[str, str]]
    estado: EstadoLectura = EstadoLectura.PENDIENTE
    duracion_requerida: int = 0
    latidos_dedicados: int = 0
    respuesta: Optional[Dict[str, Any]] = None
    ticket: Optional[Ticket] = None
