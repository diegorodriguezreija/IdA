"""Estrategia EvitarLoPeligroso para S3."""

from typing import Optional

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.estrategia import Definicion, Propuesta
from ida.nucleo.pieza import Pieza
from ida.nucleo.vocabulario import Verbo
from ida.s3.comun import _conclusion
from ida.sistemas.piezas import lugares, mejor


class EvitarLoPeligroso(Definicion):
    """Seguridad, por conocimiento (antes ``Comportamiento``, EVITAR): alejarse de lo que se sabe peligroso."""

    nombre = "evitar_lo_peligroso"
    impulsos = ("seguridad",)
    prioridad = 10

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return _conclusion(ctx, "EVITAR") is not None and bool(lugares(ctx))

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        cc = _conclusion(ctx, "EVITAR")
        salida = mejor(lugares(ctx), lambda lugar: -lugar.rasgo("peligro"))
        if cc is None or salida is None:
            return None
        return Propuesta(Verbo.MOVER, salida.id, 0.7, cc[0].confianza, f"S3: {cc[0].carga['texto']}", clase=salida.clase)
