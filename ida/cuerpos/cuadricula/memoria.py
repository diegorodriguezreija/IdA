"""Sección «cuadricula» de la Memoria (D7), cuyo dueño es el cuerpo cuadrícula: el mapa local de esta vida (no se
hereda). Es la versión mínima del mapa cognitivo compartido: clase de cada casilla vista, qué clases son transitables,
qué hace cada acción con la casilla sobre la que actúa (las transformaciones son geometría del cuerpo) y cómo se mueve el
propio cuerpo. Escriben en ella ``ModeloDirecto`` y ``MapaLocal``; leerla es libre (``memoria.seccion("cuadricula")``).
"""

from typing import Dict, List, Optional, Set, Tuple

from ida.nucleo.memoria import Seccion
from ida.cuerpos.cuadricula.geometria import DIRECCIONES, Pos
from ida.nucleo.vocabulario import Verbo


class MapaCuadricula(Seccion):
    def __init__(self) -> None:
        self.casillas: Dict[Pos, str] = {}
        self.version_mapa = 0                       # sube cada vez que cambia una casilla recordada
        self.paso_libre: Dict[str, int] = {}        # clase -> veces que una vecina de esa clase era un lugar (transitable)
        self.paso_bloqueado: Dict[str, int] = {}    # clase -> veces que una vecina vacía de esa clase no lo era
        self.peligro_sobre: Set[str] = set()        # clases de casilla sobre las que se ha visto un peligro que se mueve
        self.transformaciones: Dict[Tuple[Verbo, str], Dict[Tuple[str, str], int]] = {}   # (verbo, objetivo) -> {(antes, después): n}
        self.cuerpo: Dict[Tuple[str, bool], List[int]] = {}   # (acción, destino libre) -> [n, avanza, queda mirando hacia allí]
        self.cierres: Set[Pos] = set()              # casillas cerradas por el propio individuo
        self.yo_previo: Optional[Tuple[Pos, Optional[Pos]]] = None   # posición y orientación del latido anterior

    def transitable(self, clase: Optional[str]) -> Optional[bool]:
        """Si se puede pasar por una casilla de ``clase``: sí si alguna vez fue un lugar (casilla a la que ir); no si,
        vacía, nunca lo fue; None si no hay pruebas."""
        if not clase:
            return None
        if self.paso_libre.get(clase, 0) > 0:
            return True
        if self.paso_bloqueado.get(clase, 0) > 0:
            return False
        return None

    def transitable_peligro(self, clase: Optional[str]) -> bool:
        """Si un peligro puede llegar por una casilla de ``clase``. Previo: por donde pasa uno mismo pasa un peligro que se
        mueve, y lo desconocido se supone abierto; la experiencia añade las clases sobre las que se ha visto uno."""
        return self.transitable(clase) is not False or clase in self.peligro_sobre

    def ver_casillas(self, aqui: Pos, casillas: Dict[Pos, str], libres: Set[Pos], ocupadas: Set[Pos], peligros: Set[Pos]) -> None:
        """Actualiza el mapa local con lo visto. ``libres``: casillas que son lugares; ``ocupadas``: con algo encima (no
        dicen nada de su clase); ``peligros``: casillas con un peligro que se mueve encima."""
        for p, c in casillas.items():
            if self.casillas.get(p) != c:
                self.casillas[p] = c
                self.version_mapa += 1
        for dx, dy in DIRECCIONES:
            v = (aqui[0] + dx, aqui[1] + dy)
            vecina = casillas.get(v)
            if vecina is None:
                continue
            if v in libres:
                self.paso_libre[vecina] = self.paso_libre.get(vecina, 0) + 1
            elif v not in ocupadas:
                self.paso_bloqueado[vecina] = self.paso_bloqueado.get(vecina, 0) + 1
        for p in peligros:
            if p in casillas:
                self.peligro_sobre.add(casillas[p])

    def aprender_transformacion(self, verbo: Verbo, objetivo: str, antes: str, despues: str) -> None:
        """La acción cambió la clase de la casilla sobre la que actuó."""
        t = self.transformaciones.setdefault((verbo, objetivo), {})
        t[(antes, despues)] = t.get((antes, despues), 0) + 1

    def resultado(self, verbo: Verbo, objetivo: str, antes: Optional[str] = None) -> Optional[str]:
        """Clase en la que la acción ha convertido más veces la casilla (de clase ``antes``, si se da)."""
        t = {k: n for k, n in self.transformaciones.get((verbo, objetivo), {}).items() if antes is None or k[0] == antes}
        return max(t, key=lambda k: (t[k], k))[1] if t else None

    def aprender_cuerpo(self, accion: str, libre: bool, avanza: bool, mira: bool) -> None:
        """Propiocepción: tras ``accion`` hacia una casilla libre o no, si cambió la posición y si quedó mirando hacia ella."""
        r = self.cuerpo.setdefault((accion, libre), [0, 0, 0])
        r[0] += 1
        r[1] += int(avanza)
        r[2] += int(mira)

    def modelo_cuerpo(self, accion: str, libre: bool) -> Optional[Tuple[bool, bool]]:
        """(avanza, queda mirando hacia allí) más frecuentes tras ``accion`` hacia una casilla libre o no; None sin experiencia."""
        r = self.cuerpo.get((accion, libre))
        if not r or r[0] == 0:
            return None
        return 2 * r[1] > r[0], 2 * r[2] > r[0]
