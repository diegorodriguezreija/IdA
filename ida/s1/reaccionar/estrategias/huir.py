"""Estrategia Huir."""

from typing import Optional

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.estrategia import Definicion, Propuesta
from ida.nucleo.pieza import Pieza, acotar
from ida.nucleo.vocabulario import Verbo
from ida.s1.comun import SEGURIDAD, _peligro, _salida
from ida.s1.reaccionar.estrategias.proteger import recinto
from ida.sistemas.piezas import alarma


class Huir(Definicion):
    """Seguridad: alejarse al lugar más seguro mientras el peligro supere el umbral de miedo. Dentro de un recinto (sin
    accesos por los que llegue un peligro, ``Recinto``) no se huye: el refugio ya protege, y moverse dentro no aleja de
    nada. Si salir o quedarse lo deciden el cobijo, el riesgo de fuera y las necesidades (``Proteger``, ``SalirDelRecinto``)."""

    nombre = "huir"
    impulsos = (SEGURIDAD,)
    prioridad = 10

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        r = recinto(ctx)
        if r is not None and r.carga["dentro"]:
            return False
        return intensidad >= ctx.arquetipo.umbral_miedo and _salida(ctx, intensidad) is not None

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        peligro = _peligro(ctx)
        salida = _salida(ctx, peligro)
        if salida is None:
            return None
        a = alarma(ctx)
        de = a.carga["clase_amenaza"] if a is not None else ""
        return Propuesta(Verbo.MOVER, salida.id, acotar(0.75 + 0.25 * peligro), 0.85, f"huir de {de}", clase=salida.clase)
