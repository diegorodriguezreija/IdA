"""Lecturas comunes de la Onda para los Componentes de los sistemas: lo percibido, lo que está al alcance y la alarma.
Solo usan el vocabulario común (rasgos)."""

from typing import Iterable, List, Optional

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.pieza import Pieza

ALCANCE = 0.9          # proximidad a partir de la cual algo está al alcance
MAX_OBJETOS = 7        # atención limitada: 7 ± 2 objetos por latido


def exterocepcion(ctx: Contexto) -> List[Pieza]:
    return list(ctx.onda.ev("Exterocepcion").values())


def lugares(ctx: Contexto) -> List[Pieza]:
    return [p for p in exterocepcion(ctx) if p.rasgo("lugar") >= 0.5]


def objetos(ctx: Contexto) -> List[Pieza]:
    return list(ctx.onda.ev("Objeto").values())


def al_alcance(p: Pieza) -> bool:
    return p.rasgo("proximidad") >= ALCANCE



def mejor(piezas: Iterable[Pieza], clave) -> Optional[Pieza]:
    piezas = list(piezas)
    return max(piezas, key=clave) if piezas else None


def alarma(ctx: Contexto) -> Optional[Pieza]:
    return ctx.onda.ev("Supervivencia").get("alarma")
