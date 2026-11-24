"""Estrategias de S1."""

from ida.s1.reaccionar.estrategias.afrontar import Afrontar
from ida.s1.reaccionar.estrategias.alimentarse import Alimentarse
from ida.s1.reaccionar.estrategias.defenderse import Defenderse
from ida.s1.reaccionar.estrategias.huir import Huir
from ida.s1.reaccionar.estrategias.proteger import Proteger
from ida.s1.reaccionar.estrategias.quieto_o_huir import QuietoOHuir
from ida.s1.reaccionar.estrategias.seguir_en_movimiento import SeguirEnMovimiento
from ida.s1.reaccionar.estrategias.sobresalto import Sobresalto

__all__ = [
    "Afrontar",
    "Alimentarse",
    "Defenderse",
    "Huir",
    "Proteger",
    "QuietoOHuir",
    "SeguirEnMovimiento",
    "Sobresalto",
]
