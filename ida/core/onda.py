"""La Onda: el paquete de un latido, con su presupuesto y la guillotina.

Dimensión reactiva (el cuarteto de la experiencia):
- ``ei``: estado inicial. Es el ``ef`` del latido anterior, de solo lectura.
- ``ev``: lo que se percibe e interpreta ahora. Cobra amplitud.
- ``acc``: candidatos de Ejecución propuestos por los sistemas. Cobra amplitud.
- ``ef``: estado final. Registro de todo a coste cero; contiene la ``Ejecucion``.

La guillotina es cooperativa: cada emisión pasa por ``control_vital``, que cobra amplitud y
mira el reloj. Si se agota cualquiera de los dos, salta ``LatidoAgotado``; el latido corta los
componentes que faltan y el Tribunal decide con lo que ya haya en ``acc``.

``fases`` apunta cuándo empieza y termina cada fase del latido (reloj de pared, en ns). Es un
registro pasivo: el núcleo no llama a nadie; la observabilidad externa lo lee después.
"""

import time
from contextlib import contextmanager
from types import MappingProxyType
from typing import Callable, Dict, Iterator, List, Optional, Tuple

from ida.core.pieza import Pieza

Canales = Dict[str, Dict[str, Pieza]]


class LatidoAgotado(Exception):
    """La guillotina: se agotó el plazo o la amplitud del latido."""


class DimensionReactiva:
    def __init__(self, ef_anterior: Optional[Canales] = None):
        previo = ef_anterior or {}
        self.ei = MappingProxyType({c: MappingProxyType(dict(p)) for c, p in previo.items()})
        self.ev: Canales = {}
        self.acc: Canales = {}
        self.ef: Canales = {}

    def fase(self, nombre: str):
        return {"ei": self.ei, "ev": self.ev, "acc": self.acc, "ef": self.ef}[nombre]

    def hay(self, canal: str) -> bool:
        """¿Hay alguna pieza de ese canal en cualquier fase? (activa a los componentes)."""
        return any(canal in f and len(f[canal]) > 0 for f in (self.ei, self.ev, self.acc))


class Onda:
    def __init__(
        self,
        ciclo: int,
        amplitud_max: int,
        frecuencia_ms: float,
        ef_anterior: Optional[Canales] = None,
        reloj: Callable[[], float] = time.perf_counter,
    ):
        self.ciclo = ciclo
        self.amplitud_max = int(amplitud_max)
        self.frecuencia_ms = float(frecuencia_ms)
        self.amplitud_consumida = 0
        self.reactiva = DimensionReactiva(ef_anterior)
        self._reloj = reloj
        self._t0 = reloj()
        self.exento = False            # True mientras corren los módulos del Core (sin peaje)
        self.guillotina = False
        self.motivo_guillotina = ""
        self.tiempos_ms: Dict[str, float] = {}   # tiempo de cada componente en este latido
        self.notas: Dict[str, object] = {}       # resúmenes para consola y telemetría
        self.fases: List[Tuple[str, int, int]] = []   # (fase, inicio_ns, fin_ns) para la observabilidad

    @contextmanager
    def fase(self, nombre: str) -> Iterator[None]:
        """Apunta la duración de una fase del latido, también si la corta la guillotina."""
        inicio = time.time_ns()
        try:
            yield
        finally:
            self.fases.append((nombre, inicio, time.time_ns()))

    # --- presupuesto -------------------------------------------------------
    def ms_transcurridos(self) -> float:
        return (self._reloj() - self._t0) * 1000.0

    def ms_restantes(self) -> float:
        return max(0.0, self.frecuencia_ms - self.ms_transcurridos())

    def amplitud_restante(self) -> int:
        return max(0, self.amplitud_max - self.amplitud_consumida)

    def control_vital(self, coste: int = 0, donde: str = "") -> None:
        """Cobra amplitud y comprueba el plazo. Lanza ``LatidoAgotado`` si se supera algo."""
        if self.exento:
            return
        if self.ms_transcurridos() > self.frecuencia_ms:
            raise LatidoAgotado(f"plazo de {self.frecuencia_ms:.0f} ms superado en {donde or '?'}")
        if coste > 0:
            if self.amplitud_consumida + coste > self.amplitud_max:
                self.amplitud_consumida = self.amplitud_max
                raise LatidoAgotado(f"amplitud {self.amplitud_max} agotada en {donde or '?'}")
            self.amplitud_consumida += coste

    # --- emisiones ---------------------------------------------------------
    def registrar(self, canal: str, pieza: Pieza) -> None:
        """Escribe en ``ef`` a coste cero."""
        self.reactiva.ef.setdefault(canal, {})[pieza.id] = pieza

    def percibir(self, canal: str, pieza: Pieza, coste: int = 1) -> None:
        """Proyecta la pieza a ``ev`` (atención consciente) cobrando amplitud."""
        self.control_vital(coste, donde=canal)
        pieza.actualizada = self.ciclo
        self.registrar(canal, pieza)
        self.reactiva.ev.setdefault(canal, {})[pieza.id] = pieza

    def proponer(self, canal: str, pieza: Pieza, coste: int = 1) -> Pieza:
        """Deposita un candidato en ``acc``. Si ya existe uno con el mismo id, conserva el más urgente."""
        existente = self.reactiva.acc.get(canal, {}).get(pieza.id)
        if existente is not None and existente.arousal >= pieza.arousal:
            return existente
        self.control_vital(coste, donde=canal)
        self.registrar(canal, pieza)
        self.reactiva.acc.setdefault(canal, {})[pieza.id] = pieza
        return pieza

    # --- lectura -----------------------------------------------------------
    def ev(self, canal: str) -> Dict[str, Pieza]:
        return self.reactiva.ev.get(canal, {})

    def acc(self, canal: str) -> Dict[str, Pieza]:
        return self.reactiva.acc.get(canal, {})

    def ei(self, canal: str):
        return self.reactiva.ei.get(canal, {})
