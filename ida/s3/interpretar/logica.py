"""Componente Logica para S3."""

from ida.nucleo.arquitectura import Componente, Contexto


class Logica(Componente):
    """Combina las sentencias y resuelve conflictos: evitar el daño prevalece sobre comer o coger."""

    tipo = "Logica"
    entradas = ("Sentencia",)
    PRIORIDAD = {"EVITAR": 0, "COMER": 1, "COGER": 2}

    def reactiva(self, ctx: Contexto) -> None:
        sentencias = sorted(ctx.onda.ev("Sentencia").values(), key=lambda s: (self.PRIORIDAD[s.carga["conclusion"]], -s.confianza))
        if sentencias:
            s = sentencias[0]
            self.percibir(ctx, self.pieza(ctx, "conclusion", arousal=0.6, confianza=s.confianza, carga=dict(s.carga), entradas=[s.id]))
