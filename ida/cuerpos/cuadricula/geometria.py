"""Geometría de cuadrícula 2D (D10): posiciones, vecinos, distancia, desplazamientos, entorno y búsqueda en anchura.

Es la geometría del cuerpo cuadrícula: el código general no la conoce y la pide al cuerpo (``Cuerpo`` en
``ida/nucleo/mundo.py``, que ``Cuadricula`` implementa con estas funciones).
"""

from collections import deque
from typing import Any, Callable, Deque, Dict, Hashable, Iterable, List, Optional, Set, Tuple

Pos = Tuple[int, int]
DIRECCIONES: Tuple[Pos, ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))
Desplazamiento = Tuple[int, int]   # (|dx|, |dy|) ordenados de menor a mayor: (0, 1) al lado, (1, 1) diagonal, (0, 2) a dos en línea
RADIO_PRUEBA = 2   # paso 5: hasta esta distancia se prueba una acción con requisito de cercanía antes de caminar

MAX_ESTADOS = 6000        # coste de cálculo: estados máximos por búsqueda
Accion = Tuple[str, Pos]  # ("mover", destino) | ("coger", casilla) | ("usar", casilla)


def _suma(a: Pos, b: Pos) -> Pos:
    """Suma componente a componente de dos posiciones 2D."""
    return a[0] + b[0], a[1] + b[1]


def _vecinas(p: Pos) -> List[Pos]:
    """Las cuatro casillas vecinas ortogonales."""
    x, y = p
    return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]


def _manhattan(a: Pos, b: Pos) -> int:
    """Distancia Manhattan (|dx| + |dy|) entre dos posiciones."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def pos_de(ubicacion: Any) -> Optional[Pos]:
    """Posición al final de un identificador ``<nombre>_x_y`` (convención de los mundos de cuadrícula), o None."""
    partes = str(ubicacion or "").rsplit("_", 2)
    if len(partes) == 3 and partes[1].lstrip("-").isdigit() and partes[2].lstrip("-").isdigit():
        return int(partes[1]), int(partes[2])
    return None


def desplazamiento(dx: int, dy: int) -> Desplazamiento:
    """``(|dx|, |dy|)`` ordenados de menor a mayor."""
    a, b = sorted((abs(int(dx)), abs(int(dy))))
    return (a, b)


def entorno(interior: Tuple[Pos, ...]) -> Set[Pos]:
    """Casillas a 2 o menos (en cada eje) de un conjunto de posiciones."""
    return {(x, y) for (cx, cy) in interior for x in range(cx - 2, cx + 3) for y in range(cy - 2, cy + 3)}


def _bfs(inicio: Hashable, sucesores: Callable[[Any], Iterable[Tuple[Any, Any]]], meta: Callable[[Any], bool],
         profundidad: int, max_estados: int = MAX_ESTADOS) -> Optional[List[Any]]:
    """Búsqueda en anchura: la secuencia más corta de acciones hasta un estado meta (None si no la hay en el límite)."""
    if meta(inicio):
        return []
    padres: Dict[Any, Tuple[Any, Any]] = {}
    vistos = {inicio}
    cola: Deque[Tuple[Any, int]] = deque([(inicio, 0)])
    while cola:
        estado, prof = cola.popleft()
        if prof >= profundidad:
            continue
        for accion, nuevo in sucesores(estado):
            if nuevo in vistos:
                continue
            vistos.add(nuevo)
            padres[nuevo] = (estado, accion)
            if meta(nuevo):
                plan: List[Any] = []
                while nuevo != inicio:
                    nuevo, a = padres[nuevo]
                    plan.append(a)
                return plan[::-1]
            if len(vistos) >= max_estados:
                return None
            cola.append((nuevo, prof + 1))
    return None
