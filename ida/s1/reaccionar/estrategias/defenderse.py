"""Estrategia Defenderse."""

from typing import Optional

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.estrategia import Definicion, Propuesta
from ida.nucleo.pieza import Pieza, acotar
from ida.nucleo.vocabulario import Verbo
from ida.s1.comun import SEGURIDAD, _amenaza, _peligro, _salida
from ida.sistemas.piezas import al_alcance


class Defenderse(Definicion):
    """Seguridad: sin salida y con la amenaza al alcance, defenderse."""

    nombre = "defenderse"
    impulsos = (SEGURIDAD,)
    prioridad = 5

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        amenaza = _amenaza(ctx)
        return intensidad >= ctx.arquetipo.umbral_miedo and _salida(ctx, intensidad) is None and amenaza is not None and al_alcance(amenaza)

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        amenaza = _amenaza(ctx)
        if amenaza is None or not al_alcance(amenaza):
            return None
        return Propuesta(Verbo.ATACAR, amenaza.id, acotar(0.75 + 0.25 * _peligro(ctx)), 0.7, f"defenderse de {amenaza.clase}", clase=amenaza.clase)
