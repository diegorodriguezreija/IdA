"""Componente Impulso para S2."""

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.pieza import acotar
from ida.s2.comun import EXPLORACION
from ida.sistemas.piezas import lugares, objetos


class Impulso(Componente):
    """Impulsos propios de S2 (decisión 10): Exploración, con intensidad cruda = apertura × la novedad
    máxima a la vista (lugares y objetos). Ya no modula acciones: el «no comas esto» lo resuelve la
    elección del objeto de las estrategias (C1)."""

    tipo = "Impulso"

    def reactiva(self, ctx: Contexto) -> None:
        novedad = max([lugar.rasgo("novedad") for lugar in lugares(ctx)] + [o.rasgo("novedad") for o in objetos(ctx)] + [0.0])
        intensidad = acotar(ctx.arquetipo.apertura * novedad)
        self.registrar(ctx, self.pieza(ctx, EXPLORACION, arousal=intensidad,
                                       carga={"intensidad": round(intensidad, 4), "objetivo": 0.0, "rasgo": None}))
