"""Memoria del individuo (D7): un solo almacén, ``Memoria`` (``almacen.py``), con sus partes por responsabilidades:

- ``proposiciones``: ``Proposicion``, ``Registro``, ``Expectativa`` y ``Aprendizaje`` (lo que el Core aprende del efecto);
- ``lugares``: ``Arista`` y ``RecuerdoLugar`` (hogar, mapa de transiciones y «dónde»);
- ``secciones``: ``Seccion`` y el registro de las secciones con dueño;
- ``mecanismos``: los bloques E y F (búfer diurno, grafo semántico, conceptos, reducción, repaso, modelo de transiciones).
"""

from ida.nucleo.memoria.almacen import PERFILES_MEMORIA, Memoria
from ida.nucleo.memoria.lugares import Arista, RecuerdoLugar
from ida.nucleo.memoria.proposiciones import Aprendizaje, Expectativa, Proposicion, Registro
from ida.nucleo.memoria.secciones import Seccion

__all__ = ["PERFILES_MEMORIA", "Aprendizaje", "Arista", "Expectativa", "Memoria", "Proposicion", "RecuerdoLugar", "Registro",
           "Seccion"]
