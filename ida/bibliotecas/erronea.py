"""Biblioteca con tasa de error determinista con semilla."""

from typing import Dict, Optional, Tuple, Union

from ida.bibliotecas.fija import BibliotecaFija, TicketFijo
from ida.core.azar import Azar
from ida.core.biblioteca import (
    Biblioteca,
    Consulta,
    ElementoRespuesta,
    Respuesta,
    Ticket,
    Veredicto,
)


class BibliotecaErronea(Biblioteca):
    """Como BibliotecaFija, pero invierte una fracción configurable de veredictos según semilla."""

    def __init__(
        self,
        conocimiento: Optional[Union[Dict[Tuple[str, str], Tuple[str, float]], str]] = None,
        tasa_error: float = 0.5,
        semilla: int = 42,
    ):
        self.base = BibliotecaFija(conocimiento)
        self.tasa_error = tasa_error
        self.azar = Azar(semilla)

    def solicitar(self, consulta: Consulta) -> Ticket:
        ticket_base = self.base.solicitar(consulta)
        resp_base = ticket_base.respuesta()
        if resp_base is None:
            return ticket_base
        elementos_mod = []
        for el in resp_base.elementos:
            if el.veredicto in (Veredicto.AFIRMA, Veredicto.NIEGA):
                if self.azar.probabilidad(self.tasa_error):
                    nuevo_ver = Veredicto.NIEGA if el.veredicto == Veredicto.AFIRMA else Veredicto.AFIRMA
                    elementos_mod.append(ElementoRespuesta(el.sujeto, el.relacion, nuevo_ver, el.confianza))
                else:
                    elementos_mod.append(el)
            else:
                elementos_mod.append(el)
        return TicketFijo(Respuesta(elementos=elementos_mod))
