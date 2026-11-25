"""Componente Patron para S2."""

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.vocabulario import Verbo
from ida.sistemas.piezas import objetos


class Patron(Componente):
    tipo = "Patron"
    entradas = ("Objeto",)

    def reactiva(self, ctx: Contexto) -> None:
        for o in objetos(ctx):
            vistos = ctx.memoria.clases_vistas.get(o.clase, 0)
            self.percibir(ctx, self.pieza(ctx, o.id, arousal=o.arousal * 0.8,
                                          carga={"clase": o.clase, "familiaridad": round(min(1.0, vistos / 20.0), 3)},
                                          entradas=[o.id]))

    def activa(self, ctx: Contexto) -> None:
        """Dimensión activa: recupera lo que la experiencia dice de cada clase."""
        if not ctx.con_experiencia:
            return
        for _pid, p in ctx.onda.ev("Patron").items():
            recuerdos = {v.value: round(ctx.memoria.recordar(v, p.clase)[0], 2)
                         for v in (Verbo.COMER, Verbo.MOVER, Verbo.ATACAR, Verbo.COGER) if ctx.memoria.recordar(v, p.clase)[1]}
            if recuerdos:
                self.modificar(ctx, p, carga={"recuerdos": recuerdos})
