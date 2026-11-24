"""Lo que comparten ``ModeloDirecto`` y ``MapaLocal``: dónde está y hacia dónde mira el cuerpo, qué casillas ve, y la
casilla vecina sobre la que actuó en el latido anterior.

Necesita posiciones (ubicación ``<nombre>_x_y``) y la clase de cada casilla a la vista (``cuerpo["casillas"]``); sin
ellas no hay situación y los dos Componentes no hacen nada. Lo lee de las piezas, no de la Observación: ubicación y
cuerpo, de la ``Propiocepcion`` «yo».
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.memoria import Pos, pos_de
from ida.nucleo.vocabulario import Verbo


@dataclass
class Situacion:
    aqui: Pos
    casillas: Dict[Pos, str]
    cara: Optional[Pos]


def situacion(ctx: Contexto) -> Optional[Situacion]:
    """Posición, casillas a la vista y orientación de este latido (pieza ``Propiocepcion`` «yo»), o None si no las hay."""
    yo = ctx.onda.ev("Propiocepcion").get("yo")
    if yo is None:
        return None
    aqui = pos_de(yo.carga.get("ubicacion"))
    cuerpo = yo.carga.get("cuerpo") or {}
    crudas = cuerpo.get("casillas")
    if aqui is None or not isinstance(crudas, dict) or not crudas:
        return None
    casillas = {(int(k[0]), int(k[1])): str(v) for k, v in crudas.items()}
    o = cuerpo.get("orientacion")
    cara = (int(o[0]), int(o[1])) if isinstance(o, (list, tuple)) and len(o) == 2 else None
    return Situacion(aqui, casillas, cara)


def accion_previa(ctx: Contexto) -> Optional[Dict[str, Any]]:
    """La acción ejecutada en el latido anterior (``ei["Accion"]``), si la hubo."""
    previa = ctx.onda.ei("Accion").get("Accion")
    return previa.carga if previa is not None else None


def vecina(mem: Any, c: Optional[Dict[str, Any]]) -> Optional[Tuple[Pos, Pos, Pos]]:
    """``(posición anterior, casilla destino, dirección)`` si la acción anterior iba sobre una casilla vecina de la posición
    anterior (para USAR, la de delante); si no, None."""
    if c is None or mem.yo_previo is None:
        return None
    p0, f0 = mem.yo_previo
    if c["verbo"] == Verbo.USAR:
        destino = (p0[0] + f0[0], p0[1] + f0[1]) if f0 is not None else None
    else:
        destino = pos_de(c.get("objetivo"))
    if destino is None or abs(destino[0] - p0[0]) + abs(destino[1] - p0[1]) != 1:
        return None
    return p0, destino, (destino[0] - p0[0], destino[1] - p0[1])
