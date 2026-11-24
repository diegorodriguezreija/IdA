"""Navegación y búsqueda de materiales por el mapa local de cuadrícula (D16)."""

from typing import Dict, Optional, Tuple, cast

from ida.core.arquitectura import Contexto
from ida.cuerpos.cuadricula.memoria import MapaCuadricula

MAX_RUTA_MAPA = 40         # pasos máximos de una ruta por el mapa local hasta algo recordado
VECINAS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _pos_propia(ctx: Contexto) -> Optional[Tuple[int, int]]:
    """Posición propia si la ubicación lleva coordenadas al final (``<nombre>_x_y``); si no, None."""
    partes = ctx.ubicacion().rsplit("_", 2)
    if len(partes) == 3 and partes[1].lstrip("-").isdigit() and partes[2].lstrip("-").isdigit():
        return int(partes[1]), int(partes[2])
    return None


def ir_por_el_mapa(
    ctx: Contexto, clase: str, confianza: float = 0.5, excluir: frozenset = frozenset()
) -> Optional[Tuple[Tuple[int, int], int, Tuple[int, int]]]:
    """La casilla siguiente hacia la recordada de ``clase`` más cercana por el mapa local de la memoria (paso 3),
    con el coste en pasos de la ruta hasta quedar al lado y la casilla objetivo ``(x, y)``. La ruta solo pasa por
    casillas de clases que se sabe transitables. None sin posiciones, sin mapa, sin ninguna recordada a menos de
    ``MAX_RUTA_MAPA`` pasos o si ya está al lado."""
    if not ctx.memoria.tiene_seccion("cuadricula"):
        return None
    mem = cast(MapaCuadricula, ctx.memoria.seccion("cuadricula"))
    aqui = _pos_propia(ctx)
    if aqui is None or not ctx.con_experiencia or not mem.casillas:
        return None
    objetivos = {p for p, c in mem.casillas.items() if c == clase and f"{clase}@{p[0]}_{p[1]}" not in excluir}
    if not objetivos:
        return None
    junto = {(x + dx, y + dy): (x, y) for x, y in sorted(objetivos) for dx, dy in VECINAS}
    if aqui in junto:
        return None
    previo: Dict[Tuple[int, int], Tuple[int, int]] = {}
    frontera, d, llegada = [aqui], 0, None
    while frontera and llegada is None and d < MAX_RUTA_MAPA:
        d += 1
        siguiente = []
        for x, y in frontera:
            for dx, dy in VECINAS:
                v = (x + dx, y + dy)
                if v in previo or v == aqui or mem.transitable(mem.casillas.get(v)) is not True:
                    continue
                previo[v] = (x, y)
                if v in junto:
                    llegada = v
                    break
                siguiente.append(v)
            if llegada is not None:
                break
        frontera = siguiente
    if llegada is None:
        return None
    primero = llegada
    while previo[primero] != aqui:
        primero = previo[primero]
    x, y = junto[llegada]
    return (primero, d, (x, y))
