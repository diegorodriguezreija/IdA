"""Estrategia ComerLoNutritivo para S3."""

from typing import Optional

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.estrategia import Definicion, Propuesta
from ida.nucleo.pieza import Pieza
from ida.nucleo.vocabulario import Verbo
from ida.s3.comun import _conclusion
from ida.sistemas.piezas import al_alcance, lugares, mejor


class ComerLoNutritivo(Definicion):
    """Necesidades que satisface lo nutritivo, por conocimiento (antes ``Comportamiento``, COMER)."""

    nombre = "comer_lo_nutritivo"
    rasgo = "nutritivo"
    prioridad = 10

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return _conclusion(ctx, "COMER") is not None

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        cc = _conclusion(ctx, "COMER")
        if cc is None:
            return None
        c, objetivo = cc
        motivo = f"S3: {c.carga['texto']}"
        if al_alcance(objetivo):
            return Propuesta(Verbo.COMER, objetivo.id, 0.65, c.confianza, motivo, clase=objetivo.clase)
        destino = mejor(lugares(ctx), lambda lugar: lugar.rasgo("nutritivo") - 1.5 * lugar.rasgo("peligro"))
        if destino is not None and destino.rasgo("nutritivo") > 0:
            return Propuesta(Verbo.MOVER, destino.id, 0.55, c.confianza, motivo + " (acercarse)", clase=destino.clase)
        return None
