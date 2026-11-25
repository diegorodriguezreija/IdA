"""Accion: la etapa Actuar común de los sistemas."""

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.estrategia import Catalogo


class Accion(Componente):
    """Etapa Actuar de un sistema (decisiones 3 y 17): traduce cada estrategia activa del sistema
    en una acción, con su origen (impulso y estrategia). Es la dueña de las piezas ``Accion``."""

    tipo = "Accion"

    def __init__(self, catalogo: Catalogo):
        super().__init__("Accion")
        self.catalogo = catalogo

    def reactiva(self, ctx: Contexto) -> None:
        for p in list(ctx.onda.estrategias.values()):
            if p.sistema != self.sistema:
                continue
            definicion = self.catalogo.get(p.carga["nombre"])
            resultado = definicion.actuar(ctx, p) if definicion is not None else None
            propuestas = resultado if isinstance(resultado, list) else ([resultado] if resultado is not None else [])
            for propuesta in propuestas:
                self.proponer(ctx, propuesta.verbo, propuesta.objetivo, propuesta.arousal, propuesta.confianza, propuesta.motivo,
                              clase=propuesta.clase, origen={"impulso": p.carga["impulso"], "estrategia": p.id}, **(propuesta.datos or {}))
