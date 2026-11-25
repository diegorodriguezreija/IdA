"""Cuerpo cuadrícula (D10): mundos de rejilla 2D con orientación (posición ``<nombre>_x_y``, ``cuerpo["casillas"]`` y
``cuerpo["orientacion"]``).

Componentes, en orden de montaje (y de ``aprender``):
- ``ModeloDirecto`` (CORE.Actuar): qué hace cada acción con el propio cuerpo;
- ``MapaLocal`` (S1.Interpretar): mapa métrico de las casillas vistas, transformaciones y cierres.

Y su capa motora (D9), ``MotorCuadricula`` (una biblioteca, no un Componente): traduce la intención a primitivas del
mundo, con como mucho ``max_sinergia`` primitivas por Actuación, y juzga su éxito.

El espacio (D10, C1): ``Cuadricula`` implementa la interfaz espacial de ``Cuerpo`` con la geometría de ``geometria.py``
(posición ``<nombre>_x_y``, distancia Manhattan, desplazamiento ``(|dx|, |dy|)`` ordenado, cuatro vecinos y casillas a la
vista). ``radio_prueba``: hasta qué desplazamiento se prueba una acción con requisito de cercanía antes de caminar.
"""

from typing import Any, Dict, Hashable, List, Optional, Set, Tuple

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.mundo import Cuerpo, Motor, Perfil
from ida.cuerpos.cuadricula.buscador import buscar_postura, mover
from ida.cuerpos.cuadricula.geometria import (
    RADIO_PRUEBA,
    Desplazamiento,
    _bfs,
    _manhattan,
    _suma,
    _vecinas,
    desplazamiento,
    entorno,
    pos_de,
)
from ida.cuerpos.cuadricula.mapa import ir_por_el_mapa
from ida.cuerpos.cuadricula.core.actuar.modelo_directo import ModeloDirecto
from ida.cuerpos.cuadricula.memoria import MapaCuadricula
from ida.cuerpos.cuadricula.s1.interpretar.mapa_local import MapaLocal
from ida.cuerpos.cuadricula.motor import MotorCuadricula

__all__ = [
    "Cuadricula",
    "MapaCuadricula",
    "MapaLocal",
    "ModeloDirecto",
    "MotorCuadricula",
    "RADIO_PRUEBA",
    "_bfs",
    "_manhattan",
    "_suma",
    "_vecinas",
    "buscar_postura",
    "desplazamiento",
    "entorno",
    "ir_por_el_mapa",
    "mover",
    "pos_de",
]


class Cuadricula(Cuerpo):
    nombre = "cuadricula"
    junto: Hashable = (0, 1)

    def __init__(self, max_sinergia: int = 2, radio_prueba: int = RADIO_PRUEBA) -> None:
        self._motor = MotorCuadricula(max_sinergia)
        self.radio_prueba = int(radio_prueba)

    # --- espacio (D10, C1) ----------------------------------------------------------
    posicion = staticmethod(pos_de)
    distancia = staticmethod(_manhattan)    # sin envoltorio: Amenaza la llama en bucles

    @staticmethod
    def relacion(a: Any, b: Any) -> Desplazamiento:
        return desplazamiento(b[0] - a[0], b[1] - a[1])

    @staticmethod
    def magnitud(relacion: Any) -> int:
        return int(relacion[0] + relacion[1])

    @staticmethod
    def orden(relacion: Any) -> Tuple[Any, ...]:
        """A igual distancia, el desplazamiento más diagonal."""
        return (relacion[0] + relacion[1], -relacion[0])

    contiguos = staticmethod(_vecinas)

    @staticmethod
    def percibidas(postura: Optional[Dict[str, Any]]) -> Optional[Set[Any]]:
        """Las casillas a la vista (``cuerpo["casillas"]``), o None si el mundo no las da."""
        crudas = (postura or {}).get("casillas")
        if isinstance(crudas, dict) and crudas:
            return {(int(k[0]), int(k[1])) for k in crudas}
        return None

    def motor(self) -> Optional[Motor]:
        return self._motor

    def seccion_memoria(self, perfil: Perfil) -> Optional[Tuple[str, Any]]:
        """D7: el cuerpo es dueño de la sección «cuadricula» (mapa local, transformaciones y modelo del cuerpo)."""
        return "cuadricula", MapaCuadricula()

    def componentes(self) -> Dict[str, List[Componente]]:
        return {"CORE.Actuar": [ModeloDirecto()], "S1.Interpretar": [MapaLocal()]}

    def ir_por_el_mapa(
        self, ctx: Contexto, clase: str, confianza: float = 0.5, excluir: frozenset = frozenset()
    ) -> Optional[Tuple[Tuple[int, int], int, Tuple[int, int]]]:
        return ir_por_el_mapa(ctx, clase, confianza, excluir)
