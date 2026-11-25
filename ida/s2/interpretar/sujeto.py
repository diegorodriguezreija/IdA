"""Componente Sujeto para S2."""

from ida.nucleo.arquitectura import Componente, Contexto
from ida.sistemas.piezas import objetos


class Sujeto(Componente):
    tipo = "Sujeto"
    entradas = ("Patron",)

    def reactiva(self, ctx: Contexto) -> None:
        for o in objetos(ctx):
            self.percibir(ctx, self.pieza(ctx, o.id, arousal=o.arousal * 0.5, carga={"clase": o.clase}, entradas=[o.id]))
