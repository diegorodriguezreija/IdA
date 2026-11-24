"""Regulación de la Onda (D12): fija el ritmo de cada latido a partir de los indicadores del cuerpo.

Es un Componente del Core (``CORE.Regulacion``): reglas instantáneas (condición → ajuste), sin búsquedas
ni bucles sobre la memoria. Sustituye al antiguo ``Marcapasos`` con las mismas reglas y los mismos datos.
El Core crea la Onda con lo que devuelve ``ritmo``: frecuencia (plazo), amplitud (piezas nuevas que
caben en el latido) y potencia (arousal que se puede otorgar o cambiar en total).

Fase A: se calcula al crear la Onda (la Onda necesita frecuencia, amplitud y potencia al nacer), con el
soma y los indicadores del latido anterior, como el Marcapasos. Leer lo sentido en el propio latido es B2.

Valores por defecto (bloque B, sin algoritmo adaptativo):
- Frecuencia y amplitud: dependen de la energía, el sueño, la taquicardia y el peligro (ver ``ritmo``).
- Potencia = amplitud, así que la fuerza máxima por pieza (potencia / amplitud) es 1: ningún
  componente ve recortado un arousal de 0 a 1 ni un cambio completo. Con menos, un reflejo de
  arousal 1 quedaría recortado en cualquier latido.
- Escasez de atención (calibrada antes de la mejora de los mundos, decisiones 15 y 18): la amplitud es
  ``FACTOR_AMPLITUD`` × la amplitud base del perfil del mundo. 0,45 es el nivel más escaso del barrido
  que no pierde de forma significativa y en el que S3 se queda sin recursos más a menudo con peligro
  que en calma (foco estrecho con peligro). Cifras en ``docs/CALIBRACION_ATENCION.md``.
"""

from typing import Tuple

from ida.nucleo.arquitectura import Componente
from ida.nucleo.soma import Soma


class Regulacion(Componente):
    tipo = "Regulacion"

    FUERZA_POR_PIEZA = 1.0   # potencia / amplitud
    FACTOR_AMPLITUD = 0.45   # amplitud = factor × amplitud base del perfil (escasez de atención)

    def ritmo(self, soma: Soma, frecuencia_base_ms: float, amplitud_base: int) -> Tuple[float, int, float]:
        """Frecuencia (plazo en ms), amplitud y potencia del próximo latido según el estado del cuerpo.

        - La energía escala la amplitud (cansado se atiende a menos cosas).
        - Dormido, la amplitud baja a 20.
        - Si el latido anterior agotó la amplitud, este tiene un 50 % más («taquicardia»).
        - Con peligro, el plazo se acorta hasta un 30 %: se decide antes y S1 gana peso.
        - Potencia = amplitud × ``FUERZA_POR_PIEZA``.
        """
        if soma.dormido:
            amplitud = 20
        else:
            amplitud = int(amplitud_base * self.FACTOR_AMPLITUD * (0.5 + 0.5 * soma.energia / 100.0))
            if soma.agotado_previo:
                amplitud = int(amplitud * 1.5)
        frecuencia = frecuencia_base_ms * (1.0 - 0.3 * soma.indicadores.get("peligro", 0.0))
        amplitud = max(5, amplitud)
        return frecuencia, amplitud, amplitud * self.FUERZA_POR_PIEZA
