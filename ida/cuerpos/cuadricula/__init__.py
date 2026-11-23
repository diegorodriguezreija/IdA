"""Cuerpo cuadrícula (D10): mundos de rejilla 2D con orientación (posición ``<nombre>_x_y``, ``cuerpo["casillas"]`` y
``cuerpo["orientacion"]``).

Componentes, en orden de montaje (y de ``aprender``):
- ``ModeloDirecto`` (CORE.Actuar): qué hace cada acción con el propio cuerpo;
- ``MapaLocal`` (S1.Interpretar): mapa métrico de las casillas vistas, transformaciones y cierres.

La geometría y el buscador de posturas se mueven en A6, con ``Recinto``.
"""

from typing import Dict, List

from ida.core.arquitectura import Componente
from ida.core.mundo import Cuerpo
from ida.cuerpos.cuadricula.mapa_local import MapaLocal
from ida.cuerpos.cuadricula.modelo_directo import ModeloDirecto

__all__ = ["Cuadricula", "MapaLocal", "ModeloDirecto"]


class Cuadricula(Cuerpo):
    nombre = "cuadricula"

    def componentes(self) -> Dict[str, List[Componente]]:
        return {"CORE.Actuar": [ModeloDirecto()], "S1.Interpretar": [MapaLocal()]}
