"""La Pieza: unidad individual de información que circula por la Onda."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


def acotar(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return float(max(lo, min(hi, x)))


@dataclass
class Pieza:
    """Unidad producida por un Componente.

    - ``id``: identidad estable (un mismo objeto del mundo conserva su id).
    - ``tipo``: clase de Pieza (Escena, Imagen, Objeto, Supervivencia, Valor, Ejecucion...).
    - ``arousal``: saliencia o urgencia, en [0, 1].
    - ``confianza``: certeza, en [0, 1].
    - ``carga``: datos propios (para entidades: ``clase`` y ``rasgos``).
    - ``entradas``: ids o tipos de las piezas que la causaron (trazabilidad).
    - ``sistema``: quién la produjo (CORE, S1, S2, S3 o MUNDO).
    - ``creada`` y ``actualizada``: latido de creación y de última actualización.
    """

    id: str
    tipo: str
    arousal: float = 0.0
    confianza: float = 1.0
    carga: Dict[str, Any] = field(default_factory=dict)
    entradas: List[str] = field(default_factory=list)
    sistema: str = "CORE"
    creada: int = 0
    actualizada: int = 0

    def __post_init__(self) -> None:
        self.arousal = acotar(self.arousal)
        self.confianza = acotar(self.confianza)

    # Atajos para piezas que representan entidades del mundo
    @property
    def clase(self) -> str:
        return str(self.carga.get("clase", ""))

    def rasgo(self, nombre: str) -> float:
        return float(self.carga.get("rasgos", {}).get(nombre, 0.0))

    def resumen(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "arousal": round(self.arousal, 3),
            "confianza": round(self.confianza, 3),
            "sistema": self.sistema,
        }


@dataclass
class Episodio:
    """Secuencia de latidos delimitada por cambios significativos, con su balance vital."""

    id: str
    inicio: int
    fin: int = 0
    balance: float = 0.0
    resuelto: bool = False
    arousal_max: float = 0.0
    acciones: List[Dict[str, Any]] = field(default_factory=list)
