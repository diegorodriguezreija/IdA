"""Exterocepcion: una pieza por entidad percibida, en bruto (arousal 0)."""

from ida.nucleo.arquitectura import Componente, Contexto


class Exterocepcion(Componente):
    """Una pieza por entidad, en bruto: arousal 0 (sin valorar). La saliencia la pone la preatención (``Saliencia``, D5)."""

    tipo = "Exterocepcion"

    def reactiva(self, ctx: Contexto) -> None:
        if ctx.observacion is None:
            return
        for e in ctx.observacion.entidades:
            p = self.pieza(ctx, e.id, arousal=0.0, carga={"clase": e.clase, "rasgos": dict(e.rasgos), "datos": dict(e.datos)})
            self.percibir(ctx, p)   # D7: las clases vistas (novedad) las cuenta la plasticidad del Core, no el sensor
