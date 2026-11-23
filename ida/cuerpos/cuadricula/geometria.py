"""Geometría de cuadrícula 2D (D10): vecinos, distancia, entorno y búsqueda en anchura."""

from collections import deque
from typing import Any, Callable, Deque, Dict, Hashable, Iterable, List, Optional, Set, Tuple

from ida.core.memoria import Pos

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
