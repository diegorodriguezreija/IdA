"""Estrategia Explorar para S2."""

from typing import List, Optional

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.estrategia import Definicion, Propuesta
from ida.nucleo.pieza import Pieza, acotar
from ida.nucleo.vocabulario import Verbo
from ida.s2.comun import EXPLORACION, _peligro
from ida.sistemas_comun import al_alcance, cautela, lugares, mejor, objetos


class Explorar(Definicion):
    """Exploración (antes ``Curiosidad``): sin peligro (< 0,3) ni mucha hambre (< 0,6), recorrer el
    lugar más nuevo (ponderado por lo que se recuerda de él) y coger lo útil al alcance. Son dos
    acciones de la misma fase: las propone las dos y decide el Tribunal, como antes."""

    nombre = "explorar"
    impulsos = (EXPLORACION,)
    prioridad = 10

    @staticmethod
    def _calma(ctx: Contexto) -> bool:
        return _peligro(ctx) < 0.3 and ctx.soma.hambre() < 0.6

    @staticmethod
    def _nuevo(ctx: Contexto) -> Optional[Pieza]:
        def puntuar(lugar: Pieza) -> float:
            s = lugar.rasgo("novedad") - lugar.rasgo("peligro")
            if ctx.con_experiencia and ctx.memoria.activa:
                s += max(-0.4, min(0.3, ctx.memoria.valor_lugar(lugar.id) * 0.15))
            return s

        evitar = cautela(ctx)[1]
        nuevo = mejor([lugar for lugar in lugares(ctx) if lugar.id not in evitar], puntuar)
        return nuevo if nuevo is not None and nuevo.rasgo("novedad") > 0.0 and nuevo.rasgo("peligro") < 0.5 else None

    @staticmethod
    def _util(ctx: Contexto) -> Optional[Pieza]:
        if ctx.soma.cargando is not None:
            return None
        return mejor([o for o in objetos(ctx) if al_alcance(o) and o.rasgo("recurso") >= 0.4 and o.rasgo("peligro") < 0.3],
                     lambda o: o.rasgo("recurso") + o.rasgo("novedad"))

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return self._calma(ctx) and (self._util(ctx) is not None or self._nuevo(ctx) is not None)

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> List[Propuesta]:
        apertura = ctx.arquetipo.apertura
        propuestas = []
        nuevo = self._nuevo(ctx)
        if nuevo is not None:
            propuestas.append(Propuesta(Verbo.MOVER, nuevo.id, acotar(0.15 + 0.25 * apertura * nuevo.rasgo("novedad")), 0.5,
                                        "curiosidad: explorar", clase=nuevo.clase))
        util = self._util(ctx)
        if util is not None:
            propuestas.append(Propuesta(Verbo.COGER, util.id, acotar(0.2 + 0.3 * apertura * util.rasgo("recurso")), 0.5,
                                        f"curiosidad: coger {util.clase}", clase=util.clase))
        return propuestas
