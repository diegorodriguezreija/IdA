"""SalirDelRecinto: estrategia de las necesidades «de fuera» para abrir el recinto."""

from typing import Optional

from ida.core.arquitectura import Contexto
from ida.core.estrategia import ConPropuestas
from ida.core.pieza import Pieza
from ida.sistemas.proteger import COBIJO, Proteger, _proponer_abrir, recinto, riesgo_exterior


class SalirDelRecinto(ConPropuestas):
    """Estrategia general de las necesidades «de fuera» (las que declaran un ``rasgo``: se satisfacen con algo del mundo):
    dentro de un recinto, abrirlo cuando el déficit de la necesidad pesa más que quedarse.

    Quedarse pesa lo que el cobijo y lo que el riesgo de salir (``riesgo_exterior``: el peligro percibido, si llega al umbral
    de miedo). Es la misma regla con la que ``Proteger`` abre de noche, pero desde la necesidad. De día el cobijo no pide
    nada y ``Proteger`` se cierra, y dentro de un recinto las estrategias de la necesidad no ven lo que buscan. Sin esta
    estrategia, nadie abre: se sale tarde o por azar (``docs/DIAGNOSTICO_PASO3.md``, punto 3). Una necesidad apurada saca
    del recinto en cuanto el riesgo de fuera baja del umbral de miedo, o antes si pesa más que ese riesgo.
    """

    nombre = "salir_del_recinto"
    cualquier_impulso = True
    prioridad = 60

    @staticmethod
    def _deficit(ctx: Contexto, impulso: str) -> Optional[float]:
        fuera = {n.nombre for n in ctx.perfil.necesidades if n.rasgo} - {COBIJO}
        p = ctx.onda.ef("Impulso").get(impulso)
        if impulso not in fuera or p is None:
            return None
        return float(p.carga.get("deficit", p.carga["intensidad"]))

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        r = recinto(ctx)
        deficit = self._deficit(ctx, impulso)
        if r is None or not r.carga["dentro"] or not r.carga["abrir"] or deficit is None:
            return False
        cobijo, _, _ = Proteger._intensidades(ctx)
        return deficit > max(cobijo, riesgo_exterior(ctx))

    def decidir(self, ctx: Contexto, estrategia: Optional[Pieza] = None) -> None:
        r = recinto(ctx)
        impulso = str(estrategia.carga.get("impulso", "")) if estrategia is not None else ""
        deficit = self._deficit(ctx, impulso)
        if r is None or deficit is None or not r.carga["abrir"]:
            return
        cobijo, _, _ = Proteger._intensidades(ctx)
        _proponer_abrir(self, ctx, r.carga, "salir del recinto", impulso, deficit, cobijo)
