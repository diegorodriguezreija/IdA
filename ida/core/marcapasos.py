"""Marcapasos: fija el ritmo de cada latido a partir de los indicadores del cuerpo.

El Core crea la Onda con lo que devuelve. Es sustituible (``Organismo.marcapasos``): otro algoritmo
puede cambiar el ritmo sin tocar el resto. Por ahora devuelve frecuencia y amplitud con la fórmula
que antes estaba en ``Soma.presupuesto``; la potencia se añade más adelante.
"""

from typing import Tuple

from ida.core.soma import Soma


class Marcapasos:
    def ritmo(self, soma: Soma, frecuencia_base_ms: float, amplitud_base: int) -> Tuple[float, int]:
        """Frecuencia (plazo en ms) y amplitud del próximo latido según el estado del cuerpo.

        - La energía escala la amplitud (cansado se atiende a menos cosas).
        - Dormido, la amplitud baja a 20.
        - Si el latido anterior agotó la amplitud, este tiene un 50 % más («taquicardia»).
        - Con peligro, el plazo se acorta hasta un 30 %: se decide antes y S1 gana peso.
        """
        if soma.dormido:
            amplitud = 20
        else:
            amplitud = int(amplitud_base * (0.5 + 0.5 * soma.energia / 100.0))
            if soma.agotado_previo:
                amplitud = int(amplitud * 1.5)
        frecuencia = frecuencia_base_ms * (1.0 - 0.3 * soma.indicadores.get("peligro", 0.0))
        return frecuencia, max(5, amplitud)
