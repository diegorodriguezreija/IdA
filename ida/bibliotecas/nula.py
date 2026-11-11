"""Biblioteca nula (por defecto). No existe biblioteca externa; garantiza invariancia absoluta."""

from typing import Optional

from ida.core.biblioteca import (
    Biblioteca,
    Consulta,
    ElementoRespuesta,
    Respuesta,
    Ticket,
    Veredicto,
)


class TicketNulo(Ticket):
    def __init__(self, consulta: Consulta):
        self._respuesta = Respuesta(
            elementos=[
                ElementoRespuesta(sujeto=e.sujeto, relacion=e.relacion, veredicto=Veredicto.NO_SABE, confianza=0.0)
                for e in consulta.elementos
            ]
        )

    def lista(self) -> bool:
        return True

    def respuesta(self) -> Optional[Respuesta]:
        return self._respuesta


class BibliotecaNula(Biblioteca):
    """Biblioteca inexistente que siempre responde 'no_sabe'."""

    def solicitar(self, consulta: Consulta) -> Ticket:
        return TicketNulo(consulta)
