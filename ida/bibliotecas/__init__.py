"""Adaptadores de bibliotecas externas de autoridad."""

from ida.bibliotecas.erronea import BibliotecaErronea
from ida.bibliotecas.fija import BibliotecaFija
from ida.bibliotecas.nula import BibliotecaNula

__all__ = ["BibliotecaNula", "BibliotecaFija", "BibliotecaErronea"]
