"""Defensa (S1.Reaccionar): estrategia de S1 propia del mundo de archivos."""

from typing import Optional

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.estrategia import Definicion, Propuesta
from ida.nucleo.pieza import Pieza
from ida.nucleo.vocabulario import Verbo


class Defensa(Definicion):
    """Estrategia de S1 propia del mundo de archivos para el impulso Seguridad.

    Un depredador de la carpeta muerde mientras se esté en ella y a veces cambia de carpeta: huir
    solo aplaza el problema. Si hay uno al alcance y queda vitalidad (≥ 30, por interocepción),
    plantarle cara (atacarlo lo elimina con un 60 % de probabilidad). Con poca vitalidad quedan las
    estrategias genéricas.
    """

    nombre = "plantar_cara"
    impulsos = ("seguridad",)
    prioridad = 50

    @staticmethod
    def _depredador(ctx: Contexto) -> Optional[Pieza]:
        vit = ctx.onda.ev("Interocepcion").get("vitalidad")
        if vit is None or float(vit.carga["valor"]) < 30.0:
            return None
        return next((p for p in ctx.onda.ev("Exterocepcion").values()
                     if p.rasgo("agente") >= 0.5 and p.rasgo("peligro") >= 0.5 and p.rasgo("proximidad") >= 0.9), None)

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return self._depredador(ctx) is not None

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        p = self._depredador(ctx)
        if p is None:
            return None
        return Propuesta(Verbo.ATACAR, p.id, 1.0, 0.97, f"defensa: plantar cara al {p.clase}", clase=p.clase)
