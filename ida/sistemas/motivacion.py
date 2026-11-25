"""Señales motivacionales comunes a los sistemas: el apetito (del soma) y la cautela que deja S3."""

from typing import Tuple

from ida.nucleo.arquitectura import Contexto


def apetito(ctx: Contexto) -> float:
    """Ganas de comer: un apetito basal más el hambre del cuerpo."""
    return 0.25 + 0.75 * ctx.soma.hambre()


def cautela(ctx: Contexto) -> Tuple[set, set]:
    """Clases y lugares que S3 desaconseja (piezas ``Cautela`` del latido anterior: S3 corre después).
    Las emite el criterio de S3 de cada mundo (p. ej. una prudencia alimentaria)."""
    clases, sitios = set(), set()
    for c in ctx.onda.ei("Cautela").values():
        if c.carga.get("clase"):
            clases.add(c.carga["clase"])
        if c.carga.get("lugar"):
            sitios.add(c.carga["lugar"])
    return clases, sitios
