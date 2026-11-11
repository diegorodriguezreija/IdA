"""Memoria del individuo: recuerdos (dimensión activa), expectativas (dimensión proactiva),
conocimiento formal legible, episodios, sueño y herencia.

Escribe el Core, no los componentes: los componentes señalan lo relevante con su arousal y el
Core guarda lo más saliente de cada latido. La escritura va en dos velocidades: lo mínimo en
cada latido (en RAM) y lo costoso (persistir, olvidar, consolidar) al dormir o al morir.
"""

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, cast

from ida.core.pieza import Episodio, acotar
from ida.core.vocabulario import EstadoSaber, Relacion, Verbo

PERFILES_MEMORIA = {"apagada": 0, "ligera": 2, "completa": 5}   # K piezas guardadas por latido


# ---------------------------------------------------------------------------
# Conocimiento formal (lenguaje interno de S3)
# ---------------------------------------------------------------------------
@dataclass
class Proposicion:
    """«<clase> <relación>», con confianza. Solo cuenta como sabido lo que la experiencia confirma."""

    sujeto: str
    relacion: Relacion
    confianza: float = 0.3
    confirmaciones: int = 0
    refutaciones: int = 0
    ultima_refutacion: int = -10**9
    heredada: bool = False
    actualizada: int = 0

    CONFIRMACIONES_MINIMAS = 3
    CONFIANZA_DEMOSTRADA = 0.7
    LATIDOS_SIN_REFUTAR = 30

    def estado(self, ahora: int) -> EstadoSaber:
        if self.refutaciones > 0 and self.confianza < 0.15:
            return EstadoSaber.REFUTADA
        if (
            self.confirmaciones >= self.CONFIRMACIONES_MINIMAS
            and self.confianza >= self.CONFIANZA_DEMOSTRADA
            and ahora - self.ultima_refutacion > self.LATIDOS_SIN_REFUTAR
        ):
            return EstadoSaber.DEMOSTRADA
        return EstadoSaber.HIPOTESIS

    def confirmar(self, ahora: int) -> None:
        """La confianza sube despacio."""
        self.confirmaciones += 1
        self.confianza = acotar(self.confianza + 0.15 * (1.0 - self.confianza))
        self.actualizada = ahora

    def refutar(self, ahora: int) -> None:
        """...y baja más rápido."""
        self.refutaciones += 1
        self.confianza = acotar(self.confianza * 0.7 - 0.05)
        self.ultima_refutacion = ahora
        self.actualizada = ahora

    def texto(self, ahora: int) -> str:
        origen = ", heredada" if self.heredada else ""
        return f"«{self.sujeto} {self.relacion.value}» ({self.estado(ahora).value}{origen}, {self.confianza:.2f})"


@dataclass
class Registro:
    """Recuerdo agregado de hacer ``verbo`` sobre una ``clase``: cuántas veces y con qué balance medio."""

    n: int = 0
    suma: float = 0.0
    ultimo: int = 0

    @property
    def media(self) -> float:
        return self.suma / self.n if self.n else 0.0


@dataclass
class Expectativa:
    """Predicción proactiva: «si hago <verbo> sobre <clase>, el balance será <signo>»."""

    latido: int
    verbo: Verbo
    clase: str
    esperado: float


@dataclass
class Aprendizaje:
    """Lo que el Core aprendió al contrastar la acción anterior con el presente (para la consola)."""

    textos: List[str] = field(default_factory=list)
    sorpresa: bool = False
    rpe: float = 0.0


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


def _signo(x: float, margen: float = 0.25) -> int:
    return 0 if abs(x) < margen else (1 if x > 0 else -1)


class Memoria:
    MAX_NODOS_MAPA = 200
    EDAD_OLVIDO_MAPA = 300

    def __init__(self, perfil: str = "completa", con_replay: bool = True):
        if perfil not in PERFILES_MEMORIA:
            raise ValueError(f"Perfil de memoria desconocido: {perfil}")
        self.perfil = perfil
        self.k = PERFILES_MEMORIA[perfil]
        self.con_replay = con_replay
        self.saber: Dict[Tuple[str, Relacion], Proposicion] = {}
        self.registros: Dict[Tuple[Verbo, str], Registro] = {}
        self.lugares: Dict[str, float] = {}            # bienestar recordado por lugar (hogar)
        self.clases_vistas: Dict[str, int] = {}        # familiaridad por clase
        self.mapa: Dict[str, Dict[str, Arista]] = {}   # grafo de transiciones (hipocampo)
        self.mapa_valores: Dict[str, float] = {}       # valor atribuido a lugares por replay
        self.donde: Dict[str, RecuerdoLugar] = {}      # clase -> última ubicación al alcance
        self.expectativa: Optional[Expectativa] = None
        self.buffer: List[Dict[str, Any]] = []         # piezas salientes pendientes de persistir
        self.episodios: List[Episodio] = []
        self._ultimo_consolidar_ep: int = 0
        self.aciertos = 0
        self.fallos = 0

    @property
    def activa(self) -> bool:
        return self.k > 0

    # --- conocimiento ----------------------------------------------------------
    def proposicion(self, clase: str, relacion: Relacion, crear: bool = False) -> Optional[Proposicion]:
        clave = (clase, relacion)
        if clave not in self.saber and crear:
            self.saber[clave] = Proposicion(clase, relacion)
        return self.saber.get(clave)

    def demostrada(self, clase: str, relacion: Relacion, ahora: int) -> bool:
        p = self.saber.get((clase, relacion))
        return p is not None and p.estado(ahora) == EstadoSaber.DEMOSTRADA

    def conocimiento(self, ahora: int) -> List[str]:
        orden = sorted(self.saber.values(), key=lambda p: (-p.confianza, p.sujeto))
        return [p.texto(ahora) for p in orden]

    # --- dimensión activa: recuerdos -------------------------------------------
    def recordar(self, verbo: Verbo, clase: str) -> Tuple[float, int]:
        r = self.registros.get((verbo, clase))
        return (r.media, r.n) if r else (0.0, 0)

    def sesgo(self, verbo: Verbo, clase: str, ahora: int) -> Tuple[float, float]:
        """Sesgo de la experiencia sobre un candidato: (activa, proactiva), cada uno en [-1, 1].

        - Activa: el balance medio que dejó hacer esto mismo antes.
        - Proactiva: lo que se sabe (proposiciones) sobre la clase del objetivo.
        """
        if not self.activa or not clase:
            return 0.0, 0.0
        media, n = self.recordar(verbo, clase)
        activa = math.tanh(media / 5.0) * min(1.0, n / 3.0) if n else 0.0
        proactiva = 0.0
        nutr = self.saber.get((clase, Relacion.NUTRITIVO))
        pelig = self.saber.get((clase, Relacion.PELIGROSO))
        if verbo == Verbo.COMER and nutr is not None:
            estado = nutr.estado(ahora)
            proactiva += nutr.confianza if estado == EstadoSaber.DEMOSTRADA else (-0.5 if estado == EstadoSaber.REFUTADA else 0.0)
        if verbo in (Verbo.MOVER, Verbo.COMER, Verbo.COGER) and pelig is not None:
            if pelig.estado(ahora) == EstadoSaber.DEMOSTRADA:
                proactiva -= pelig.confianza
        return activa, acotar(proactiva, -1.0, 1.0)

    # --- el cuarteto: aprender del efecto de la acción anterior --------------
    def aprender(
        self,
        verbo: Optional[Verbo],
        clase: str,
        delta: Dict[str, float],
        causa: Optional[str],
        obtenido: Optional[str],
        exito: bool,
        ahora: int,
        mortal: bool = False,
    ) -> Aprendizaje:
        """Contrasta lo que hizo (``ei``) con lo que le pasó al cuerpo (``ev``)."""
        ap = Aprendizaje()
        if not self.activa:
            return ap
        d_vit = delta.get("vitalidad", 0.0)
        if causa and causa != clase:
            d_vit = max(0.0, d_vit)       # el daño lo causó otra cosa: no se atribuye a esta acción
        balance = d_vit + 0.5 * delta.get("alimentacion", 0.0) + 0.25 * delta.get("energia", 0.0)

        # Dimensión activa: recuerdo agregado de (verbo, clase)
        if verbo is not None and clase:
            r = self.registros.setdefault((verbo, clase), Registro())
            r.n += 1
            r.suma += balance
            r.ultimo = ahora

        # Conocimiento formal a partir de la agencia
        def confirmar(c: str, rel: Relacion) -> None:
            p = cast(Proposicion, self.proposicion(c, rel, crear=True))
            antes = p.estado(ahora)
            p.confirmar(ahora)
            if p.estado(ahora) != antes:
                ap.textos.append(f"ahora sabe {p.texto(ahora)}")

        def refutar(c: str, rel: Relacion) -> None:
            p = cast(Proposicion, self.proposicion(c, rel, crear=True))
            antes = p.estado(ahora)
            p.refutar(ahora)
            if p.estado(ahora) != antes:
                ap.textos.append(f"duda de {p.texto(ahora)}")

        if verbo == Verbo.COMER and clase and exito:
            if delta.get("alimentacion", 0.0) > 0.0 or delta.get("energia", 0.0) > 0.0:
                confirmar(clase, Relacion.NUTRITIVO)
            else:
                refutar(clase, Relacion.NUTRITIVO)
            if d_vit <= -1.0:
                confirmar(clase, Relacion.PELIGROSO)
                if d_vit <= -5.0:   # aversión gustativa: un envenenamiento grave se aprende casi de una vez
                    confirmar(clase, Relacion.PELIGROSO)
        if causa:
            confirmar(causa, Relacion.PELIGROSO)
            if mortal:   # trauma: lo que mató queda demostrado de una vez (y puede pasar al linaje)
                p = cast(Proposicion, self.proposicion(causa, Relacion.PELIGROSO, crear=True))
                p.confirmaciones = max(p.confirmaciones, Proposicion.CONFIRMACIONES_MINIMAS)
                p.confianza = max(p.confianza, Proposicion.CONFIANZA_DEMOSTRADA)
        if verbo in (Verbo.COGER, Verbo.USAR) and exito and (obtenido or clase):
            confirmar(obtenido or clase, Relacion.UTIL)

        # Dimensión proactiva: validar la expectativa del latido anterior
        exp = self.expectativa
        if exp is not None and verbo == exp.verbo and clase == exp.clase:
            ap.rpe = balance - exp.esperado
            if _signo(balance) == _signo(exp.esperado):
                self.aciertos += 1
                ap.textos.append(f"esperaba {exp.esperado:+.1f} y obtuvo {balance:+.1f}: acierto")
            else:
                self.fallos += 1
                ap.sorpresa = True
                ap.textos.append(f"esperaba {exp.esperado:+.1f} y obtuvo {balance:+.1f}: sorpresa")
        self.expectativa = None
        return ap

    def proyectar(self, verbo: Verbo, clase: str, ahora: int) -> Optional[Expectativa]:
        """Anota la expectativa de la acción que se va a ejecutar, si hay recuerdo en que basarla."""
        if not self.activa or not clase or verbo == Verbo.MOVER:
            self.expectativa = None           # moverse depende de todo lo demás: no se predice
            return None
        media, n = self.recordar(verbo, clase)
        if n == 0 or _signo(media) == 0:      # solo se anota lo que predice algo
            self.expectativa = None
            return None
        self.expectativa = Expectativa(ahora, verbo, clase, media)
        return self.expectativa

    # --- escritura rápida y episodios ------------------------------------------
    def guardar_rapido(self, piezas: List[Dict[str, Any]]) -> None:
        """Cada latido: las K piezas de mayor arousal, a un búfer en RAM."""
        if self.k:
            piezas = sorted(piezas, key=lambda p: -p["arousal"])[: self.k]
            self.buffer.extend(piezas)

    def ver_clase(self, clase: str) -> int:
        self.clases_vistas[clase] = self.clases_vistas.get(clase, 0) + 1
        return self.clases_vistas[clase]

    def recordar_lugar(self, lugar: str, bienestar: float) -> None:
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

    # --- sueño: lo costoso, fuera del camino crítico --------------------------
    def consolidar(self, ahora: int) -> Dict[str, int]:
        """Olvido, consolidación y replay inverso de trayectorias. Lo demostrado y lo de arousal extremo no se olvida."""
        olvidadas = 0
        for clave, p in list(self.saber.items()):
            estado = p.estado(ahora)
            if estado == EstadoSaber.DEMOSTRADA:
                continue
            if estado == EstadoSaber.HIPOTESIS and ahora - p.actualizada > 150 and p.confianza < 0.4:
                del self.saber[clave]
                olvidadas += 1
        recuerdos_olvidados = 0
        for clave_r, r in list(self.registros.items()):
            if r.n == 1 and abs(r.media) < 0.5 and ahora - r.ultimo > 200:
                del self.registros[clave_r]
                recuerdos_olvidados += 1
        aristas_olvidadas = 0
        for vecs in list(self.mapa.values()):
            for dest, ar in list(vecs.items()):
                if ar.usos <= 1 and ahora - ar.ultimo_latido > self.EDAD_OLVIDO_MAPA:
                    del vecs[dest]
                    aristas_olvidadas += 1
        for clase_d, rec in list(self.donde.items()):
            if ahora - rec.ultimo_latido > self.EDAD_OLVIDO_MAPA:
                del self.donde[clase_d]
        # Del búfer solo sobrevive lo de arousal alto (lo demás ya está agregado en registros)
        self.buffer = [p for p in self.buffer if p["arousal"] >= 0.85]

        # Replay inverso de trayectorias recientes al dormir (Fase 2)
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

        return {
            "hipotesis_olvidadas": olvidadas,
            "recuerdos_olvidados": recuerdos_olvidados,
            "aristas_olvidadas": aristas_olvidadas,
            "episodios_replay": episodios_replay,
        }

    # --- herencia dentro del linaje (barrera de Weismann) ----------------------
    def legado(self, ahora: int) -> Dict[str, Any]:
        """Lo que pasa al linaje: lo demostrado y la memoria colectiva de S1 (recuerdos agregados)."""
        return {
            "proposiciones": [
                {"sujeto": p.sujeto, "relacion": p.relacion.name, "confianza": round(p.confianza, 3)}
                for p in self.saber.values()
                if p.estado(ahora) == EstadoSaber.DEMOSTRADA
            ],
            "registros": [
                {"verbo": v.name, "clase": c, "n": r.n, "media": round(r.media, 3)}
                for (v, c), r in self.registros.items()
                if r.n >= 2
            ],
        }

    def heredar(self, legado: Dict[str, Any]) -> int:
        """Lo heredado entra como hipótesis fuerte: hace falta experiencia propia para demostrarlo."""
        if not self.activa:
            return 0
        n = 0
        for d in legado.get("proposiciones", []):
            p = Proposicion(d["sujeto"], Relacion[d["relacion"]], confianza=float(d["confianza"]) * 0.8)
            p.confirmaciones = Proposicion.CONFIRMACIONES_MINIMAS - 1
            p.heredada = True
            self.saber[(p.sujeto, p.relacion)] = p
            n += 1
        for d in legado.get("registros", []):
            r = Registro(n=max(1, int(d["n"]) // 2))
            r.suma = float(d["media"]) * r.n
            self.registros[(Verbo[d["verbo"]], d["clase"])] = r
            n += 1
        return n
