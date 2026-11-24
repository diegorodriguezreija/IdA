"""Ambiente: condiciones del entorno (una sola pieza ambiente, si el mundo las da)."""

from ida.nucleo.arquitectura import Componente, Contexto


class Ambiente(Componente):
    """Condiciones del entorno (``Observacion.ambiente``): una sola pieza ``ambiente``, si el mundo las da."""

    tipo = "Ambiente"

    def reactiva(self, ctx: Contexto) -> None:
        if ctx.observacion is not None and ctx.observacion.ambiente:
            self.percibir(ctx, self.pieza(ctx, "ambiente", arousal=0.0, carga=dict(ctx.observacion.ambiente)))
