"""Marcapasos: fija el ritmo de cada latido a partir de los indicadores del cuerpo.

El Core crea la Onda con lo que devuelve. Es sustituible (``Organismo.marcapasos``): otro algoritmo
puede cambiar el ritmo sin tocar el resto. Devuelve frecuencia (plazo), amplitud (piezas nuevas que
caben en el latido) y potencia (arousal que se puede otorgar o cambiar en total).

Valores por defecto (bloque B, sin algoritmo adaptativo):
- Frecuencia y amplitud: dependen de la energía, el sueño, la taquicardia y el peligro (ver ``ritmo``).
- Potencia = amplitud, así que la fuerza máxima por pieza (potencia / amplitud) es 1: ningún
  componente ve recortado un arousal de 0 a 1 ni un cambio completo. Con menos, un reflejo de
  arousal 1 quedaría recortado en cualquier latido.
- La medición previa (paso B0, ``herramientas/consumo.py``) da un arousal otorgado por latido muy por
  debajo de la amplitud, así que con estos valores la potencia solo se agota en latidos atípicos.
  Cifras en ``docs/MEDICIONES_BLOQUE_B.md``.
"""

from typing import Tuple

from ida.core.soma import Soma


class Marcapasos:
    FUERZA_POR_PIEZA = 1.0   # potencia / amplitud

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
            amplitud = int(amplitud_base * (0.5 + 0.5 * soma.energia / 100.0))
            if soma.agotado_previo:
                amplitud = int(amplitud * 1.5)
        frecuencia = frecuencia_base_ms * (1.0 - 0.3 * soma.indicadores.get("peligro", 0.0))
        amplitud = max(5, amplitud)
        return frecuencia, amplitud, amplitud * self.FUERZA_POR_PIEZA
