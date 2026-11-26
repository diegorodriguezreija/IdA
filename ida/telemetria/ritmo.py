"""Ritmo visible de una vida (O3, O20): aplicado *entre* latidos y fuera del organismo.

El plazo del latido (``Perfil.frecuencia_ms``) es biología: cuánto tiene IdA para pensar. La velocidad para mirar es de
la telemetría (O20): cada mundo tiene un *ritmo cómodo* para seguirlo a ojo (ms por latido, en
``ida/telemetria/catalogo.py``, ``RITMO_COMODO_MS``). El ejecutor llama a ``Regulador.esperar`` después de publicar cada
latido (en el ``al_latir`` del organismo, cuando el latido ya terminó y antes de que empiece el siguiente). El organismo
no lo ve: con plazo lógico (O11) la guillotina cuenta operaciones, no tiempo, así que el ritmo no cambia la conducta. En
los mundos de tiempo real (Snake) el ritmo lo marca el mundo: el ejecutor no llama al regulador y la API no deja
cambiarlo.

- ``lento``: el doble del cómodo.
- ``comodo``: el de entrada.
- ``x4``: la cuarta parte del cómodo.
- ``max``: sin espera.
- ``pausa``: espera hasta que el ritmo cambie, se pida un paso (``paso``: deja pasar un latido) o se pida parar.

El cómodo es el ``comodo_ms`` del regulador; si no se da (la CLI con ``--ver``, el panel clásico), el ``frecuencia_ms``
que pasa el ejecutor, como antes de T4a. ``x1`` se admite como sinónimo de ``comodo`` (la API de T3).

El periodo se mide entre dos salidas de la espera, no desde el final del latido: un latido que tarda 80 ms a ritmo
cómodo de 250 ms espera 170 ms, así que lo que se ve avanza con un periodo regular. Un cambio de ritmo durante una espera
se aplica en el acto (la espera se recalcula).
"""

import threading
import time
from typing import Any, Optional

RITMOS = ("pausa", "lento", "comodo", "x4", "max")
SINONIMOS = {"x1": "comodo"}
FACTOR = {"lento": 2.0, "comodo": 1.0, "x4": 0.25, "max": 0.0}


def normalizar(ritmo: Any) -> str:
    """El nombre canónico de un ritmo (``x1`` -> ``comodo``) o ``ValueError`` si no se conoce."""
    r = SINONIMOS.get(ritmo, ritmo) if isinstance(ritmo, str) else ritmo
    if r not in RITMOS:
        raise ValueError(f"ritmo desconocido {ritmo!r} (conocidos: {', '.join(RITMOS)})")
    return r


class Regulador:
    """El ritmo pedido para la vida en curso. Seguro entre hilos: la API lo cambia, el hilo de la vida lo lee."""

    def __init__(self, ritmo: str = "comodo", comodo_ms: Optional[float] = None) -> None:
        self._ritmo = normalizar(ritmo)
        self.comodo_ms = None if comodo_ms is None else float(comodo_ms)
        self._cond = threading.Condition()
        self._soltar = False
        self._pasos = 0                       # latidos pedidos con «paso a paso» que aún no han pasado
        self._ultima: Optional[float] = None  # cuándo terminó la última espera (para un periodo regular)

    @property
    def ritmo(self) -> str:
        return self._ritmo

    def fijar(self, ritmo: str) -> str:
        r = normalizar(ritmo)
        with self._cond:
            self._ritmo = r
            if r != "pausa":
                self._pasos = 0
            self._cond.notify_all()
        return r

    def paso(self) -> int:
        """Deja pasar un latido (solo en pausa: ``ValueError`` si no). Devuelve los pasos pendientes."""
        with self._cond:
            if self._ritmo != "pausa":
                raise ValueError("«paso a paso» solo en pausa")
            self._pasos += 1
            self._cond.notify_all()
            return self._pasos

    def soltar(self) -> None:
        """Despierta cualquier espera (para parar la vida aunque esté en pausa)."""
        with self._cond:
            self._soltar = True
            self._cond.notify_all()

    def ms_por_latido(self, frecuencia_ms: float) -> Optional[float]:
        """Los ms por latido del ritmo actual (``None`` en pausa)."""
        if self._ritmo == "pausa":
            return None
        base = self.comodo_ms if self.comodo_ms is not None else float(frecuencia_ms)
        return FACTOR[self._ritmo] * base

    def esperar(self, frecuencia_ms: float, parada: Optional[Any] = None) -> None:
        """Espera lo que pide el ritmo entre dos latidos. ``parada``: un ``threading.Event``; si se activa, no espera más."""
        inicio = time.monotonic()
        with self._cond:
            try:
                while True:
                    if self._soltar or (parada is not None and parada.is_set()):
                        return
                    if self._ritmo == "pausa":
                        if self._pasos > 0:
                            self._pasos -= 1
                            return
                        self._cond.wait(timeout=0.25)   # vuelve a mirar la parada aunque nadie avise
                        continue
                    periodo = (self.ms_por_latido(frecuencia_ms) or 0.0) / 1000.0
                    desde = inicio if self._ultima is None else max(self._ultima, inicio - periodo)
                    restante = desde + periodo - time.monotonic()
                    if restante <= 0:
                        return
                    self._cond.wait(timeout=min(restante, 0.25))
            finally:
                self._ultima = time.monotonic()
