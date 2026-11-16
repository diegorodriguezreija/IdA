"""Utilidades compartidas por los componentes base. Solo usan el vocabulario común (rasgos)."""

from typing import Iterable, List, Optional

from ida.core.arquitectura import Componente, Contexto
from ida.core.estrategia import Catalogo
from ida.core.pieza import Pieza

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


def apetito(ctx: Contexto) -> float:
    """Ganas de comer: un apetito basal más el hambre del cuerpo."""
    return 0.25 + 0.75 * ctx.soma.hambre()


def mejor(piezas: Iterable[Pieza], clave) -> Optional[Pieza]:
    piezas = list(piezas)
    return max(piezas, key=clave) if piezas else None


def alarma(ctx: Contexto) -> Optional[Pieza]:
    return ctx.onda.ev("Supervivencia").get("alarma")


class Accion(Componente):
    """Etapa Actuar de un sistema (decisiones 3 y 17): traduce cada estrategia activa del sistema
    en una acción, con su origen (impulso y estrategia). Es la dueña de las piezas ``Accion``."""

    tipo = "Accion"

    def __init__(self, catalogo: Catalogo):
        super().__init__("Accion")
        self.catalogo = catalogo

    def reactiva(self, ctx: Contexto) -> None:
        for p in list(ctx.onda.estrategias.values()):
            if p.sistema != self.sistema:
                continue
            definicion = self.catalogo.get(p.carga["nombre"])
            propuesta = definicion.actuar(ctx, p) if definicion is not None else None
            if propuesta is None:
                continue
            self.proponer(ctx, propuesta.verbo, propuesta.objetivo, propuesta.arousal, propuesta.confianza, propuesta.motivo,
                          clase=propuesta.clase, origen={"impulso": p.carga["impulso"], "estrategia": p.id}, **(propuesta.datos or {}))
