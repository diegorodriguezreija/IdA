"""Toda la aleatoriedad del organismo sale de aquí, con semilla, para poder repetir una ejecución."""

import random
from typing import Optional, Sequence, TypeVar

T = TypeVar("T")


class Azar:
    def __init__(self, semilla: Optional[int] = None):
        self.semilla = semilla
        self._rng = random.Random(semilla)

    def uniforme(self, a: float = 0.0, b: float = 1.0) -> float:
        return self._rng.uniform(a, b)

    def ruido(self, amplitud: float) -> float:
        """Ruido bipolar en [-amplitud, +amplitud]."""
        return self._rng.uniform(-amplitud, amplitud)

    def eleccion(self, opciones: Sequence[T]) -> T:
        return self._rng.choice(list(opciones))

    def probabilidad(self, p: float) -> bool:
        return self._rng.random() < p

    def derivar(self, etiqueta: int) -> "Azar":
        """Generador hijo independiente y reproducible (para un mundo, una generación...)."""
        base = self.semilla if self.semilla is not None else 0
        return Azar(base * 1_000_003 + etiqueta)
