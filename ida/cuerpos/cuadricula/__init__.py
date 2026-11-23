"""Cuerpo cuadrícula (D10): mundos de rejilla 2D con orientación (posición ``<nombre>_x_y``, ``cuerpo["casillas"]`` y
``cuerpo["orientacion"]``).

Componentes, en orden de montaje (y de ``aprender``):
- ``ModeloDirecto`` (CORE.Actuar): qué hace cada acción con el propio cuerpo;
- ``MapaLocal`` (S1.Interpretar): mapa métrico de las casillas vistas, transformaciones y cierres.

Y su capa motora (D9), ``MotorCuadricula`` (una biblioteca, no un Componente): traduce la intención a primitivas del
mundo, con como mucho ``max_sinergia`` primitivas por Actuación, y juzga su éxito.

La geometría y el buscador de posturas se mueven en A6, con ``Recinto``.
"""

from typing import Dict, List, Optional

from ida.core.arquitectura import Componente
from ida.core.mundo import Cuerpo, Motor
from ida.cuerpos.cuadricula.mapa_local import MapaLocal
from ida.cuerpos.cuadricula.modelo_directo import ModeloDirecto
from ida.cuerpos.cuadricula.motor import MotorCuadricula

__all__ = ["Cuadricula", "MapaLocal", "ModeloDirecto", "MotorCuadricula"]


class Cuadricula(Cuerpo):
    nombre = "cuadricula"

    def __init__(self, max_sinergia: int = 2) -> None:
        self._motor = MotorCuadricula(max_sinergia)

    def motor(self) -> Optional[Motor]:
        return self._motor

    def componentes(self) -> Dict[str, List[Componente]]:
        return {"CORE.Actuar": [ModeloDirecto()], "S1.Interpretar": [MapaLocal()]}
