"""Biblioteca determinista fija basada en un diccionario o archivo JSON."""

import json
from typing import Dict, Optional, Tuple, Union

from ida.core.biblioteca import (
    Biblioteca,
    Consulta,
    ElementoRespuesta,
    Respuesta,
    Ticket,
    Veredicto,
)


class TicketFijo(Ticket):
    def __init__(self, respuesta: Respuesta):
        self._respuesta = respuesta

    def lista(self) -> bool:
        return True

    def respuesta(self) -> Optional[Respuesta]:
        return self._respuesta


class BibliotecaFija(Biblioteca):
    """Devuelve respuestas deterministas predefinidas."""

    def __init__(self, conocimiento: Optional[Union[Dict[Tuple[str, str], Tuple[str, float]], str]] = None):
        self.datos: Dict[Tuple[str, str], Tuple[str, float]] = {}
        if isinstance(conocimiento, str):
            with open(conocimiento, "r", encoding="utf-8") as f:
                cargado = json.load(f)
                for k, v in cargado.items():
                    sujeto, rel = k.split(":")
                    self.datos[(sujeto, rel)] = (v[0], float(v[1]))
        elif isinstance(conocimiento, dict):
            for k, v in conocimiento.items():
                if isinstance(k, tuple):
                    self.datos[k] = (v[0], float(v[1]))
                elif isinstance(k, str) and ":" in k:
                    sujeto, rel = k.split(":")
                    self.datos[(sujeto, rel)] = (v[0], float(v[1]))

    def solicitar(self, consulta: Consulta) -> Ticket:
        elementos = []
        for e in consulta.elementos:
            clave = (e.sujeto, e.relacion.name)
            if clave in self.datos:
                veredicto_str, conf = self.datos[clave]
                try:
                    ver = Veredicto(veredicto_str)
                except ValueError:
                    ver = Veredicto.INVALIDO
                elementos.append(ElementoRespuesta(e.sujeto, e.relacion, ver, conf))
            else:
                elementos.append(ElementoRespuesta(e.sujeto, e.relacion, Veredicto.NO_SABE, 0.0))
        return TicketFijo(Respuesta(elementos=elementos))
