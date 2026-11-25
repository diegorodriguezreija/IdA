"""Constantes y funciones comunes para S2."""

from typing import Optional

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.pieza import Pieza
from ida.nucleo.vocabulario import Relacion
from ida.sistemas.piezas import alarma

EXPLORACION = "exploracion"
SEGURIDAD = "seguridad"
CANSANCIO = "cansancio"


def _peligro(ctx: Contexto) -> float:
    a = alarma(ctx)
    return float(a.carga["peligro"]) if a else 0.0


def _recordado(ctx: Contexto, clase: str, rel: Relacion) -> Optional[Pieza]:
    return ctx.onda.ev("Recuerdo").get(f"{clase}|{rel.name}")
