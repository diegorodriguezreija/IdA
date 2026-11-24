"""Cuerpo cuadrícula (D10): mundos de rejilla 2D con orientación (posición ``<nombre>_x_y``, ``cuerpo["casillas"]`` y
``cuerpo["orientacion"]``).

Componentes, en orden de montaje (y de ``aprender``):
- ``ModeloDirecto`` (CORE.Actuar): qué hace cada acción con el propio cuerpo;
- ``MapaLocal`` (S1.Interpretar): mapa métrico de las casillas vistas, transformaciones y cierres.

Y su capa motora (D9), ``MotorCuadricula`` (una biblioteca, no un Componente): traduce la intención a primitivas del
mundo, con como mucho ``max_sinergia`` primitivas por Actuación, y juzga su éxito.

La geometría y el buscador de posturas se mueven en A6, con ``Recinto``.
"""

from typing import Any, Dict, List, Optional, Tuple

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.mundo import Cuerpo, Motor, Perfil
from ida.cuerpos.cuadricula.buscador import buscar_postura, mover
from ida.cuerpos.cuadricula.geometria import _bfs, _manhattan, _suma, _vecinas, entorno
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
    "_bfs",
    "_manhattan",
    "_suma",
    "_vecinas",
    "buscar_postura",
    "entorno",
    "ir_por_el_mapa",
    "mover",
]


class Cuadricula(Cuerpo):
    nombre = "cuadricula"

    def __init__(self, max_sinergia: int = 2) -> None:
        self._motor = MotorCuadricula(max_sinergia)

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
