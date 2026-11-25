"""Lugares: hogar, mapa topológico de transiciones (hipocampo), células de lugar («dónde» está cada clase) y su replay
al dormir (D7, sección del Core; sin herencia)."""

from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from ida.nucleo.memoria.secciones import admitir
from ida.nucleo.pieza import Episodio


@dataclass
class Arista:
    """Transición espacial observada entre dos ubicaciones en el mapa cognitivo."""

    usos: int = 1
    ultimo_latido: int = 0
    valor_replay: float = 0.0


@dataclass
class RecuerdoLugar:
    """Asociación espacial (célula de lugar): última ubicación donde estuvo al alcance una clase."""

    ubicacion: str
    ultimo_latido: int = 0
    confianza: float = 1.0



class Lugares:
    """Parte de la ``Memoria`` (fachada en ``almacen.py``): lugares y rutas."""

    MAX_NODOS_MAPA = 200
    EDAD_OLVIDO_MAPA = 300
    AUTORES_LUGARES = frozenset({"CORE", "Recinto"})         # hogar: el Core (episodios) y Recinto (dentro del recinto)
    AUTORES_DONDE = frozenset({"RecordarComida"})            # olvidar dónde estaba una clase

    con_replay: bool
    lugares: Dict[str, float]
    mapa: Dict[str, Dict[str, Arista]]
    mapa_valores: Dict[str, float]
    donde: Dict[str, RecuerdoLugar]
    episodios: List[Episodio]
    _ultimo_consolidar_ep: int

    if TYPE_CHECKING:
        @property
        def activa(self) -> bool: ...

    def recordar_lugar(self, lugar: str, bienestar: float, autor: str = "CORE") -> None:
        admitir(autor, self.AUTORES_LUGARES, "lugares")
        previo = self.lugares.get(lugar, 0.0)
        self.lugares[lugar] = 0.7 * previo + 0.3 * bienestar

    def hogar(self) -> Optional[str]:
        if not self.lugares:
            return None
        lugar, valor = max(self.lugares.items(), key=lambda kv: kv[1])
        return lugar if valor > 0.2 else None

    # --- hipocampo: mapa topológico y células de lugar (sin herencia) -------
    def registrar_transicion(self, origen: str, destino: str, ahora: int) -> None:
        if not self.activa or not origen or not destino or origen == destino:
            return
        vecinos = self.mapa.setdefault(origen, {})
        if destino in vecinos:
            a = vecinos[destino]
            a.usos += 1
            a.ultimo_latido = ahora
        else:
            vecinos[destino] = Arista(usos=1, ultimo_latido=ahora)
        self.mapa.setdefault(destino, {})
        while len(self.mapa) > self.MAX_NODOS_MAPA:
            self._podar_mapa()

    def _podar_mapa(self) -> None:
        """Elimina el nodo más antiguo (menor actividad entre aristas salientes/entrantes) si excede MAX_NODOS_MAPA."""
        if len(self.mapa) <= self.MAX_NODOS_MAPA:
            return
        def frescura(nodo: str) -> int:
            if nodo in self.mapa and self.mapa[nodo]:
                return max(a.ultimo_latido for a in self.mapa[nodo].values())
            # Si no tiene aristas salientes, mirar entrantes o 0
            entrantes = [vecs[nodo].ultimo_latido for vecs in self.mapa.values() if nodo in vecs]
            return max(entrantes, default=0)
        # No podar los recién añadidos si tienen 0 todavía excepto si es viejo
        peor = min(self.mapa.keys(), key=frescura)
        del self.mapa[peor]
        for vecinos in self.mapa.values():
            vecinos.pop(peor, None)

    def registrar_donde(self, clase: str, ubicacion: str, ahora: int, confianza: float = 1.0) -> None:
        if not self.activa or not clase or not ubicacion:
            return
        self.donde[clase] = RecuerdoLugar(ubicacion=ubicacion, ultimo_latido=ahora, confianza=confianza)

    def donde_esta(self, clase: str) -> Optional[str]:
        if not self.activa:
            return None
        rec = self.donde.get(clase)
        return rec.ubicacion if rec is not None else None

    def olvidar_donde(self, clase: str, autor: str) -> None:
        admitir(autor, self.AUTORES_DONDE, "dónde está una clase")
        self.donde.pop(clase, None)

    def valor_lugar(self, lugar: str) -> float:
        return self.mapa_valores.get(lugar, 0.0)

    @staticmethod
    def _eliminar_bucles_trayectoria(trayectoria: List[str]) -> List[str]:
        """Elimina ciclos reteniendo una ruta simple donde cada paso consecutivo fue una transición real."""
        if not trayectoria:
            return []
        pila: List[str] = []
        posiciones: Dict[str, int] = {}
        for nodo in trayectoria:
            if not nodo:
                continue
            if nodo in posiciones:
                idx = posiciones[nodo]
                for n in pila[idx + 1:]:
                    posiciones.pop(n, None)
                pila = pila[:idx + 1]
            else:
                posiciones[nodo] = len(pila)
                pila.append(nodo)
        return pila

    def camino(self, origen: str, destino: str, max_profundidad: int = 30) -> Optional[List[str]]:
        """Bloque F, F2: la ruta completa de ``origen`` a ``destino`` (ambos incluidos) por el mapa, con el
        mismo BFS y el mismo orden de vecinos que ``ruta``. Se usa al construir un plan, no en cada latido."""
        if not self.activa or not origen or not destino or origen == destino:
            return None
        if origen not in self.mapa or destino not in self.mapa:
            return None
        padre: Dict[str, str] = {}
        cola: deque[Tuple[str, int]] = deque([(origen, 0)])
        visitados = {origen}
        while cola:
            actual, prof = cola.popleft()
            if prof >= max_profundidad:
                continue
            vecinos = sorted(
                self.mapa.get(actual, {}).items(),
                key=lambda kv: (-kv[1].valor_replay if kv[1].valor_replay != 0.0 else 0.0, -kv[1].usos)
                if self.con_replay else -kv[1].usos,
            )
            for sig, _ in vecinos:
                if sig in visitados:
                    continue
                visitados.add(sig)
                padre[sig] = actual
                if sig == destino:
                    camino = [destino]
                    while camino[-1] != origen:
                        camino.append(padre[camino[-1]])
                    return camino[::-1]
                cola.append((sig, prof + 1))
        return None

    def ruta(self, origen: str, destino: str, max_profundidad: int = 30) -> Optional[str]:
        """Devuelve el siguiente salto desde ``origen`` hacia ``destino`` mediante BFS acotado."""
        if not self.activa or not origen or not destino or origen == destino:
            return None
        if origen not in self.mapa or destino not in self.mapa:
            return None
        cola: deque[Tuple[str, Optional[str], int]] = deque([(origen, None, 0)])
        visitados = {origen}
        while cola:
            actual, primer_salto, prof = cola.popleft()
            if prof >= max_profundidad:
                continue
            # Orden determinista respetando inserción y preferencia por mayor valor_replay y luego usos
            vecinos = sorted(
                self.mapa.get(actual, {}).items(),
                key=lambda kv: (-kv[1].valor_replay if kv[1].valor_replay != 0.0 else 0.0, -kv[1].usos)
                if self.con_replay else -kv[1].usos,
            )
            for sig, _ in vecinos:
                salto = primer_salto if primer_salto is not None else sig
                if sig == destino:
                    return salto
                if sig not in visitados:
                    visitados.add(sig)
                    cola.append((sig, salto, prof + 1))
        return None

    def _olvidar_lugares(self, ahora: int) -> int:
        """Al dormir: se olvidan las aristas de un solo uso y los «dónde» de hace más de ``EDAD_OLVIDO_MAPA`` latidos.
        Devuelve las aristas olvidadas."""
        aristas_olvidadas = 0
        for vecs in list(self.mapa.values()):
            for dest, ar in list(vecs.items()):
                if ar.usos <= 1 and ahora - ar.ultimo_latido > self.EDAD_OLVIDO_MAPA:
                    del vecs[dest]
                    aristas_olvidadas += 1
        for clase_d, rec in list(self.donde.items()):
            if ahora - rec.ultimo_latido > self.EDAD_OLVIDO_MAPA:
                del self.donde[clase_d]
        return aristas_olvidadas

    def _replay(self) -> int:
        """Replay inverso de las trayectorias de los episodios nuevos al dormir (Fase 2). Devuelve los episodios
        repasados."""
        episodios_replay = 0
        if self.con_replay and self.activa:
            gamma = 0.8
            nodos_actualizados: set[str] = set()
            aristas_actualizadas: set[Tuple[str, str]] = set()
            for ep in self.episodios[self._ultimo_consolidar_ep:]:
                episodios_replay += 1
                if not ep.trayectoria or ep.balance == 0.0:
                    continue
                ruta_simple = self._eliminar_bucles_trayectoria(ep.trayectoria)
                if not ruta_simple:
                    continue
                recompensa = ep.balance
                for i, nodo in enumerate(reversed(ruta_simple)):
                    descuento = gamma ** i
                    delta = round(recompensa * descuento, 4)
                    if nodo not in self.mapa_valores:
                        self.mapa_valores[nodo] = delta
                    else:
                        self.mapa_valores[nodo] = round(0.7 * self.mapa_valores[nodo] + 0.3 * delta, 4)
                    nodos_actualizados.add(nodo)
                for orig, dest in zip(ruta_simple[:-1], ruta_simple[1:], strict=False):
                    if orig in self.mapa and dest in self.mapa[orig]:
                        ar = self.mapa[orig][dest]
                        v_dest = self.mapa_valores.get(dest, 0.0)
                        if ar.valor_replay == 0.0:
                            ar.valor_replay = v_dest
                        else:
                            ar.valor_replay = round(0.7 * ar.valor_replay + 0.3 * v_dest, 4)
                        aristas_actualizadas.add((orig, dest))
            self._ultimo_consolidar_ep = len(self.episodios)
            # Decaimiento pasivo de valores espaciales antiguos no reforzados en este sueño
            for n in list(self.mapa_valores.keys()):
                if n not in nodos_actualizados:
                    self.mapa_valores[n] = round(self.mapa_valores[n] * 0.9, 4)
                    if abs(self.mapa_valores[n]) < 0.01:
                        del self.mapa_valores[n]
            for orig, vecs in self.mapa.items():
                for dest, ar in vecs.items():
                    if (orig, dest) not in aristas_actualizadas and ar.valor_replay != 0.0:
                        ar.valor_replay = round(ar.valor_replay * 0.9, 4)
                        if abs(ar.valor_replay) < 0.01:
                            ar.valor_replay = 0.0
        return episodios_replay
