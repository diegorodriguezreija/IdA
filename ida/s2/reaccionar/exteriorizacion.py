"""Componente Exteriorizacion para S2."""

from ida.nucleo.arquitectura import Componente, Contexto


class Exteriorizacion(Componente):
    tipo = "Exteriorizacion"

    def reactiva(self, ctx: Contexto) -> None:
        self.registrar(ctx, self.pieza(ctx, "exteriorizacion", arousal=ctx.soma.estres,
                                       carga={"afecto": ctx.soma.afecto.value, "placer": round(ctx.soma.placer, 1)}))
