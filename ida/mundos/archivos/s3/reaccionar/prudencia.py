"""Prudencia (S3.Reaccionar): componente propio del mundo de archivos."""

from typing import Dict, Set

from ida.nucleo.arquitectura import Componente, Contexto
from ida.s3.interpretar.proposicion import Relacion


def _indicios_de_dano(ctx: Contexto, clase: str) -> bool:
    dano = ctx.memoria.proposicion(clase, Relacion.PELIGROSO)
    return dano is not None and dano.confianza >= 0.35


class Prudencia(Componente):
    """Componente propio del mundo de archivos (S3): recuerda las carpetas donde solo había comida
    dañina y las desaconseja (piezas ``Cautela`` de lugar) durante ``RECUERDO`` latidos; el «olor» de
    una carpeta no distingue lo comestible de lo tóxico y podría atraparlo yendo y viniendo. La
    estrategia ``BuscarEnOtraCarpeta`` usa esa memoria. La prudencia al elegir qué comer está en la
    estrategia ``AlimentarseConPrudencia`` (antes, este componente frenaba las acciones).
    """

    tipo = "Cautela"
    RECUERDO = 80   # latidos que se evita una carpeta con solo comida dañina

    def __init__(self) -> None:
        super().__init__("Prudencia")
        self.malas: Dict[str, int] = {}

    def recientes(self, ahora: int) -> Set[str]:
        return {c for c, t in self.malas.items() if ahora - t < self.RECUERDO}

    def reactiva(self, ctx: Contexto) -> None:
        ahora = ctx.latido
        aqui = ctx.ubicacion()
        al_alcance = [o for o in ctx.onda.ev("Objeto").values() if o.rasgo("nutritivo") >= 0.3 and o.rasgo("proximidad") >= 0.9]
        if aqui and al_alcance and all(_indicios_de_dano(ctx, o.clase) for o in al_alcance):
            self.malas[aqui] = ahora
        for carpeta in self.recientes(ahora):
            self.registrar(ctx, self.pieza(ctx, f"cautela:{carpeta}", arousal=0.5,
                                           carga={"clase": None, "lugar": carpeta, "motivo": "carpeta con solo comida dañina"}))
