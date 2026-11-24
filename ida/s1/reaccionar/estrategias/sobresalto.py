"""Estrategia Sobresalto."""

from typing import Optional

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.estrategia import Definicion, Propuesta
from ida.nucleo.pieza import Pieza
from ida.nucleo.vocabulario import Verbo
from ida.s1.comun import SEGURIDAD, _amenaza, _peligro, _salida
from ida.sistemas_comun import al_alcance


class Sobresalto(Definicion):
    """Reflejo (decisión 6): ante un salto brusco del peligro, empezar a huir (o defenderse si no hay
    salida y la amenaza está al alcance). Innato, corto, de duración fija y prioridad máxima."""

    nombre = "sobresalto"
    impulsos = (SEGURIDAD,)
    reflejo = True

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        peligro = _peligro(ctx)
        salida = _salida(ctx, peligro)
        if salida is not None:
            return Propuesta(Verbo.MOVER, salida.id, 1.0, 0.9, "reflejo: sobresalto, huir", clase=salida.clase)
        amenaza = _amenaza(ctx)
        if amenaza is not None and al_alcance(amenaza):
            return Propuesta(Verbo.ATACAR, amenaza.id, 1.0, 0.9, f"reflejo: sobresalto, defenderse de {amenaza.clase}", clase=amenaza.clase)
        return None
