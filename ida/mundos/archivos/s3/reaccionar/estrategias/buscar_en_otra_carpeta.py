"""BuscarEnOtraCarpeta (S3.Reaccionar): estrategia de S3 propia del mundo de archivos."""

from typing import Optional

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.estrategia import Definicion, Propuesta
from ida.nucleo.pieza import Pieza
from ida.nucleo.vocabulario import Verbo
from ida.mundos.archivos.s3.reaccionar.prudencia import Prudencia


class BuscarEnOtraCarpeta(Definicion):
    """Estrategia de S3 propia del mundo de archivos para las necesidades que satisface lo nutritivo:
    si aquí solo había comida dañina, ir a otra carpeta (la más prometedora y nueva, no peligrosa y no
    recordada como mala)."""

    nombre = "buscar_en_otra_carpeta"
    rasgo = "nutritivo"
    prioridad = 20

    def __init__(self, prudencia: Prudencia) -> None:
        self.prudencia = prudencia

    def _destino(self, ctx: Contexto) -> Optional[Pieza]:
        aqui = ctx.ubicacion()
        malas = self.prudencia.recientes(ctx.latido)
        if aqui not in malas:
            return None
        carpetas = [p for p in ctx.onda.ev("Exterocepcion").values()
                    if p.rasgo("lugar") >= 0.5 and p.rasgo("peligro") < 0.5 and p.id not in malas]
        return max(carpetas, key=lambda p: p.rasgo("nutritivo") + 0.5 * p.rasgo("novedad")) if carpetas else None

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return self._destino(ctx) is not None

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        destino = self._destino(ctx)
        if destino is None:
            return None
        return Propuesta(Verbo.MOVER, destino.id, 0.6, 0.7, "prudencia: buscar comida en otra parte", clase=destino.clase)
