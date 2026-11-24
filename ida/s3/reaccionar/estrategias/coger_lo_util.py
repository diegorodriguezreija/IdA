"""Estrategia CogerLoUtil para S3."""

from typing import Optional

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.estrategia import Definicion, Propuesta
from ida.nucleo.pieza import Pieza
from ida.nucleo.vocabulario import Verbo
from ida.s3.comun import _conclusion


class CogerLoUtil(Definicion):
    """Exploración, por conocimiento (antes ``Comportamiento``, COGER): coger lo que se sabe útil."""

    nombre = "coger_lo_util"
    impulsos = ("exploracion",)
    prioridad = 10

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return _conclusion(ctx, "COGER") is not None

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        cc = _conclusion(ctx, "COGER")
        if cc is None:
            return None
        c, objetivo = cc
        return Propuesta(Verbo.COGER, objetivo.id, 0.5, c.confianza, f"S3: {c.carga['texto']}", clase=objetivo.clase)
