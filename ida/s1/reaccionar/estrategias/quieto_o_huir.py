"""Estrategia QuietoOHuir."""

from typing import Optional

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.estrategia import Definicion, Propuesta
from ida.nucleo.pieza import Pieza, acotar
from ida.nucleo.vocabulario import Verbo
from ida.s1.comun import SEGURIDAD, _peligro, _salida


class QuietoOHuir(Definicion):
    """Último recurso de Seguridad cuando todas sus estrategias están agotadas: huir si hay un lugar
    menos peligroso; si no, quedarse quieto."""

    nombre = "quieto_o_huir"
    impulsos = (SEGURIDAD,)
    ultimo_recurso = True

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        peligro = _peligro(ctx)
        salida = _salida(ctx, peligro)
        urgencia = acotar(0.75 + 0.25 * peligro)
        if salida is not None:
            return Propuesta(Verbo.MOVER, salida.id, urgencia, 0.85, "último recurso: huir", clase=salida.clase)
        return Propuesta(Verbo.ESPERAR, "", urgencia, 0.6, "último recurso: quedarse quieto")
