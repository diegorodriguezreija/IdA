"""Ayuda de pruebas (A7b, D7): una Memoria con las secciones que registrarían sus dueños al montar un Organismo.

Las pruebas unitarias que no montan un Organismo y escriben en el mapa local o en los requisitos usan esta memoria. El
manual y el legado aplicados antes o después llegan igual a las secciones (diferidos o al momento)."""

from ida.nucleo.memoria import Memoria
from ida.cuerpos.cuadricula import Cuadricula
from ida.nucleo.mundo import Perfil
from ida.sistemas.requisito import Requisitos


def memoria_con_secciones(perfil_memoria: str = "completa", cuerpo: bool = True) -> Memoria:
    mem = Memoria(perfil_memoria)
    mem.registrar_seccion("requisitos", "Requisito", Requisitos())   # general (S3 · Interpretar): está en todos los mundos
    if cuerpo:
        c = Cuadricula()
        declarada = c.seccion_memoria(Perfil())
        assert declarada is not None
        mem.registrar_seccion(declarada[0], c.nombre, declarada[1])
    return mem


def requisitos(mem: Memoria) -> Requisitos:
    """La sección «requisitos» para escribir en ella como su dueño (``Requisito``)."""
    seccion = mem.seccion_propia("requisitos", "Requisito")
    assert isinstance(seccion, Requisitos)
    return seccion
