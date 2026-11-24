"""Estrategia SeguirEnMovimiento."""

from typing import Optional

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.estrategia import Definicion, Propuesta
from ida.nucleo.pieza import Pieza
from ida.nucleo.vocabulario import Verbo
from ida.sistemas_comun import lugares, mejor


class SeguirEnMovimiento(Definicion):
    """Último recurso de cualquier impulso en un mundo que no deja esperar: si ninguna otra estrategia
    es elegible, moverse al lugar menos malo (el más nutritivo y menos peligroso). Cede en cuanto
    otra estrategia del impulso vuelve a ser elegible. Antes era «el mal menor» de ``Accion``."""

    nombre = "seguir_en_movimiento"
    cualquier_impulso = True
    ultimo_recurso = True

    @staticmethod
    def _destino(ctx: Contexto) -> Optional[Pieza]:
        return mejor(lugares(ctx), lambda lugar: lugar.rasgo("nutritivo") - 1.5 * lugar.rasgo("peligro"))

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return Verbo.ESPERAR not in ctx.verbos and self._destino(ctx) is not None

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        destino = self._destino(ctx)
        if destino is None:
            return None
        return Propuesta(Verbo.MOVER, destino.id, 0.3, 0.5, "sin opción mejor: seguir en movimiento", clase=destino.clase)
