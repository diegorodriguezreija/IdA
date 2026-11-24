"""Componente Agente para S3."""

from ida.nucleo.arquitectura import Componente, Contexto
from ida.sistemas_comun import objetos


class Agente(Componente):
    tipo = "Agente"
    entradas = ("Objeto",)

    def reactiva(self, ctx: Contexto) -> None:
        for o in objetos(ctx):
            self.percibir(ctx, self.pieza(ctx, o.id, arousal=o.arousal * 0.5, carga={"clase": o.clase, "actua": o.rasgo("agente") >= 0.5},
                                          entradas=[o.id]))
