"""Componente Proposicion para S3."""

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.vocabulario import Relacion
from ida.sistemas_comun import objetos


class Proposicion(Componente):
    """Proposiciones de lo que se sabe de cada clase presente (pasada activa)."""

    tipo = "Proposicion"
    entradas = ("Agente",)

    def activa(self, ctx: Contexto) -> None:
        """Dimensión activa: trae a la atención lo que se sabe de las clases presentes."""
        if not ctx.con_experiencia:
            return
        vistas = set()
        for o in objetos(ctx):
            if o.clase in vistas:
                continue
            vistas.add(o.clase)
            for rel in Relacion:
                p = ctx.memoria.proposicion(o.clase, rel)
                if p is None:
                    continue
                estado = p.estado(ctx.latido)
                self.percibir(ctx, self.pieza(ctx, f"{o.clase}|{rel.name}", arousal=0.3 + 0.4 * p.confianza, confianza=p.confianza,
                                              carga={"clase": o.clase, "relacion": rel, "estado": estado, "texto": p.texto(ctx.latido)}))
