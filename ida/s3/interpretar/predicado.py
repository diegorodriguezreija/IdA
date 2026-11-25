"""Componente Predicado para S3."""

from ida.nucleo.arquitectura import Componente, Contexto
from ida.sistemas.piezas import al_alcance, objetos


class Predicado(Componente):
    """Predicados de lo observado ahora (pasada reactiva)."""

    tipo = "Predicado"
    entradas = ("Agente",)

    def reactiva(self, ctx: Contexto) -> None:
        for o in objetos(ctx):
            predicados = []
            if al_alcance(o):
                predicados.append("está al alcance")
            elif o.rasgo("proximidad") >= 0.5:
                predicados.append("está cerca")
            if o.rasgo("novedad") >= 0.6:
                predicados.append("es nuevo")
            if predicados:
                self.percibir(ctx, self.pieza(ctx, o.id, arousal=0.2, carga={"clase": o.clase, "predicados": predicados}))
