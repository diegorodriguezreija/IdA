"""Ritmo visible de una vida (O3): pausa, ×1, ×4 y máximo, aplicado *entre* latidos y fuera del organismo.

El ejecutor llama a ``Regulador.esperar`` después de publicar cada latido (en el ``al_latir`` del organismo, cuando el
latido ya terminó y antes de que empiece el siguiente). El organismo no lo ve: con plazo lógico (O11) la guillotina
cuenta operaciones, no tiempo, así que el ritmo no cambia la conducta. En los mundos de tiempo real (Snake) el ritmo lo
marca el mundo: el ejecutor no llama al regulador y la API no deja cambiarlo.

- ``x1``: el latido dura al menos ``frecuencia_ms`` del ``Perfil`` (lo de siempre: ``time.sleep(frecuencia_ms/1000)``).
- ``x4``: la cuarta parte.
- ``max``: sin espera.
- ``pausa``: espera hasta que el ritmo cambie o se pida parar.

Un cambio de ritmo durante una espera se aplica en el acto (la espera se recalcula desde su inicio).
"""

import threading
import time
from typing import Any, Optional

RITMOS = ("pausa", "x1", "x4", "max")
FACTOR = {"x1": 1.0, "x4": 0.25, "max": 0.0}


class Regulador:
    """El ritmo pedido para la vida en curso. Seguro entre hilos: la API lo cambia, el hilo de la vida lo lee."""

    def __init__(self, ritmo: str = "x1") -> None:
        if ritmo not in RITMOS:
            raise ValueError(f"ritmo desconocido {ritmo!r} (conocidos: {', '.join(RITMOS)})")
        self._ritmo = ritmo
        self._cond = threading.Condition()
        self._soltar = False

    @property
    def ritmo(self) -> str:
        return self._ritmo

    def fijar(self, ritmo: str) -> None:
        if ritmo not in RITMOS:
            raise ValueError(f"ritmo desconocido {ritmo!r} (conocidos: {', '.join(RITMOS)})")
        with self._cond:
            self._ritmo = ritmo
            self._cond.notify_all()

    def soltar(self) -> None:
        """Despierta cualquier espera (para parar la vida aunque esté en pausa)."""
        with self._cond:
            self._soltar = True
            self._cond.notify_all()

    def esperar(self, frecuencia_ms: float, parada: Optional[Any] = None) -> None:
        """Espera lo que pide el ritmo entre dos latidos. ``parada``: un ``threading.Event``; si se activa, no espera más."""
        inicio = time.monotonic()
        with self._cond:
            while True:
                if self._soltar or (parada is not None and parada.is_set()):
                    return
                if self._ritmo == "pausa":
                    self._cond.wait(timeout=0.25)   # vuelve a mirar la parada aunque nadie avise
                    continue
                restante = inicio + FACTOR[self._ritmo] * frecuencia_ms / 1000.0 - time.monotonic()
                if restante <= 0:
                    return
                self._cond.wait(timeout=min(restante, 0.25))
