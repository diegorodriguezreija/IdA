"""Buscador de posturas en cuadrícula (D10): secuencias de MOVER para alcanzar una posición y orientación."""

from typing import Any, Iterable, List, Optional, Protocol, Tuple

from ida.core.memoria import DIRECCIONES, Pos
from ida.cuerpos.cuadricula.geometria import Accion, _bfs, _manhattan, _suma

MAX_PASOS_POSTURA = 12    # buscador: «qué secuencia de MOVER me deja en A mirando a C»


class ModeloMovimiento(Protocol):
    """Protocolo genérico para modelos que proporcionan previsiones de movimiento y transitabilidad."""

    mover_libre: Optional[Tuple[bool, bool]]
    mover_bloqueado: Optional[Tuple[bool, bool]]

    def libre(self, p: Pos) -> bool: ...


def mover(modelo: ModeloMovimiento, pos: Pos, cara: Optional[Pos], d: Pos, pasable: bool) -> Optional[Tuple[Pos, Optional[Pos]]]:
    """Efecto previsto de MOVER en la dirección ``d`` según el modelo del cuerpo aprendido (None si no se sabe)."""
    m = modelo.mover_libre if pasable else modelo.mover_bloqueado
    if m is None:
        return None
    avanza, mira = m
    return (_suma(pos, d) if avanza else pos), (d if mira else cara)


def buscar_postura(modelo: ModeloMovimiento, pos: Pos, cara: Optional[Pos], destino: Pos, mirando: Pos,
                   max_pasos: int = MAX_PASOS_POSTURA) -> Optional[List[Accion]]:
    """Secuencia de MOVER que deja en ``destino`` mirando a la casilla ``mirando`` (vecina), o None."""
    cara_meta = (mirando[0] - destino[0], mirando[1] - destino[1])

    def sucesores(e: Tuple[Pos, Optional[Pos]]) -> Iterable[Tuple[Accion, Any]]:
        p, c = e
        for d in DIRECCIONES:
            t = _suma(p, d)
            if _manhattan(t, pos) > max_pasos:
                continue
            r = mover(modelo, p, c, d, modelo.libre(t))
            if r is not None and r != (p, c):
                yield ("mover", t), r

    res = _bfs((pos, cara), sucesores, lambda e: e == (destino, cara_meta), max_pasos)
    return res
