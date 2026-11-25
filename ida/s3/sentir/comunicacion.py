"""Componente Comunicacion para S3."""

from ida.nucleo.arquitectura import Componente, Contexto
from ida.sistemas.piezas import exterocepcion


class Comunicacion(Componente):
    tipo = "Comunicacion"
    entradas = ("Exterocepcion",)

    def reactiva(self, ctx: Contexto) -> None:
        for p in exterocepcion(ctx):
            mensaje = p.carga.get("datos", {}).get("mensaje")
            if mensaje:
                self.percibir(ctx, self.pieza(ctx, p.id, arousal=0.5, carga={"clase": p.clase, "mensaje": str(mensaje)[:200]}, entradas=[p.id]))
