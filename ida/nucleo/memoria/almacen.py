"""Memoria del individuo: recuerdos (dimensión activa), expectativas (dimensión proactiva),
conocimiento formal legible, episodios, sueño y herencia.

Escribe el Core, no los componentes: los componentes señalan lo relevante con su arousal y el
Core guarda lo más saliente de cada latido. La escritura va en dos velocidades: lo mínimo en
cada latido (en RAM) y lo costoso (persistir, olvidar, consolidar) al dormir o al morir.

Fachada (C3): ``Memoria`` es un solo almacén (D7) que compone sus partes, cada una en su módulo:
``proposiciones`` (proposiciones, registros, expectativas), ``lugares`` (hogar, mapa y «dónde»), ``secciones`` (las de
los dueños) y ``mecanismos`` (bloques E y F). Aquí queda lo que las junta: el estado, la escritura rápida, el sueño, el
manual, el legado y la herencia.
"""

import math
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from ida.nucleo.biblioteca import RegistroLectura
from ida.nucleo.memoria.lugares import Arista, Lugares, RecuerdoLugar
from ida.nucleo.memoria.mecanismos import Mecanismos
from ida.nucleo.memoria.proposiciones import Expectativa, Proposicion, Proposiciones, Registro
from ida.nucleo.memoria.secciones import Seccion, Secciones, admitir
from ida.nucleo.pieza import Episodio
from ida.nucleo.vocabulario import EstadoSaber, Relacion, Verbo

PERFILES_MEMORIA = {"apagada": 0, "ligera": 2, "completa": 5}   # K piezas guardadas por latido


class Memoria(Proposiciones, Lugares, Mecanismos, Secciones):
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
        self.lecturas: List[RegistroLectura] = []
        self._lectura_activa: Optional[RegistroLectura] = None
        self._ultimo_fin_lectura: int = -100
        self.aciertos = 0
        self.fallos = 0
        # Bloque E (decisión 19): búfer diurno de tamaño fijo y episodio del día (secuencia de ondas).
        self.diurno: List[Tuple[float, int, Dict[str, Any]]] = []   # montículo (puntuación, orden, pieza)
        self._orden_diurno = 0
        self.dia: List[Dict[str, Any]] = []
        # E2: grafo semántico (nodos con fuerza y valencia; relaciones por coincidencia) y almacén de días.
        self.grafo: Dict[str, Dict[str, Any]] = {}
        self.relaciones: Dict[Tuple[str, str], float] = {}
        self.dias: List[Dict[str, Any]] = []
        # E3: conceptos (prototipo por clase, id estable sin significado) e instancias.
        self.conceptos: Dict[str, Dict[str, Any]] = {}       # id -> {"etiqueta", "prototipo", "n"}
        self._concepto_de: Dict[str, str] = {}               # etiqueta legible -> id
        self.instancias: Dict[str, Dict[str, Any]] = {}      # id de la instancia -> {"concepto", "visto"}
        # F1: modelo de transiciones (sistema, verbo, clase) -> cambio medio de cada variable, aprendido de lo vivido.
        self.modelo: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        self._modelo_por: Dict[Tuple[str, str], Set[str]] = {}
        # D7: secciones con dueño. No existen hasta que su dueño se monta (``Organismo``), pero el manual y el legado
        # llegan antes: la Memoria guarda ambos, en orden, y se los entrega a cada sección al registrarse.
        self._secciones: Dict[str, Tuple[str, Seccion]] = {}
        self._diferido: List[Tuple[str, Dict[str, Any], float]] = []   # ("manual" | "legado", datos, tasa)
        self.heredados = 0                                             # hechos heredados, con los de las secciones

    @property
    def activa(self) -> bool:
        return self.k > 0

    # --- escritura rápida y episodios ------------------------------------------
    def guardar_rapido(self, piezas: List[Dict[str, Any]]) -> None:
        """Cada latido: las K piezas de mayor arousal, a un búfer en RAM."""
        if self.k:
            piezas = sorted(piezas, key=lambda p: -p["arousal"])[: self.k]
            self.buffer.extend(piezas)

    # --- escrituras delegadas (D7): el autor de cada una debe estar entre los que admite su dueño -----------------
    AUTORES_LECTURA = frozenset({"Estudio"})                 # lectura activa y fin de la última (S3)

    @property
    def lectura_activa(self) -> Optional[RegistroLectura]:
        return self._lectura_activa

    @property
    def ultimo_fin_lectura(self) -> int:
        return self._ultimo_fin_lectura

    def fijar_lectura(self, registro: Optional[RegistroLectura], autor: str, fin: Optional[int] = None) -> None:
        """La lectura activa (None: ninguna) y, con ``fin``, el latido en que terminó la última. Autor: ``Estudio``."""
        admitir(autor, self.AUTORES_LECTURA, "la lectura activa")
        self._lectura_activa = registro
        if fin is not None:
            self._ultimo_fin_lectura = fin

    def ver_clase(self, clase: str) -> int:
        self.clases_vistas[clase] = self.clases_vistas.get(clase, 0) + 1
        return self.clases_vistas[clase]

    # --- sueño: lo costoso, fuera del camino crítico --------------------------
    def consolidar(self, ahora: int, reduccion: bool = False) -> Dict[str, int]:
        """Olvido, consolidación y replay inverso de trayectorias. Lo demostrado y lo de arousal extremo no se olvida.
        Con ``reduccion`` (bloque E, E4), la reducción nocturna sustituye al olvido de hipótesis por antigüedad."""
        olvidadas = self.reducir(ahora) if reduccion else self._olvidar_hipotesis(ahora)
        recuerdos_olvidados = self._olvidar_registros(ahora)
        aristas_olvidadas = self._olvidar_lugares(ahora)
        # Del búfer solo sobrevive lo de arousal alto (lo demás ya está agregado en registros)
        self.buffer = [p for p in self.buffer if p["arousal"] >= 0.85]

        # Replay inverso de trayectorias recientes al dormir (Fase 2)
        episodios_replay = self._replay()

        return {
            "hipotesis_olvidadas": olvidadas,
            "recuerdos_olvidados": recuerdos_olvidados,
            "aristas_olvidadas": aristas_olvidadas,
            "episodios_replay": episodios_replay,
        }

    # --- manual del mundo y requisitos de las acciones (paso 2) ----------------
    CONFIANZA_MANUAL = 0.8      # c_aut de lo que declara el manual (y confianza inicial de sus requisitos)
    PESO_MANUAL = 1.0           # w_aut del manual: pesa como una experiencia propia

    def aplicar_manual(self, manual: Dict[str, Any]) -> int:
        """Al nacer, antes de heredar: las proposiciones del manual entran como autoridad (``c_aut``), refutables
        por la experiencia; los requisitos, con fuente «manual»; las metas, sin conseguir. Un requisito repetido
        (mismo verbo y objetivo) completa al anterior: fija cantidades desconocidas y suma lo que falte. Los
        hechos de tipo «nota» no se cargan. Con ``inventario``, el manual declara qué claves del inventario
        percibido son objetos. Devuelve cuántos hechos se cargaron."""
        if not self.activa or not manual:
            return 0
        n = 0
        for h in manual.get("hechos", []):
            tipo = h.get("tipo")
            if tipo == "proposicion":
                p = cast(Proposicion, self.proposicion(str(h["sujeto"]), Relacion[h["relacion"]], crear=True))
                p.aplicar_autoridad(str(h.get("veredicto", "afirma")), self.CONFIANZA_MANUAL, self.PESO_MANUAL, ahora=0)
                n += 1   # qué necesidad satisface (paso 0b): lo toma la sección «satisface» (Apetencia)
            elif tipo in ("meta", "requisito"):
                n += 1   # D7: los toma la sección «requisitos» (Requisito), como el inventario que declara el manual
        self._diferir("manual", manual)   # D7: lo de las secciones, al registrarse cada una (o ya, si lo está)
        return n

    # --- herencia dentro del linaje (barrera de Weismann) ----------------------
    def legado(self, ahora: int) -> Dict[str, Any]:
        """Lo que pasa al linaje: lo demostrado, la memoria colectiva de S1 (recuerdos agregados) y los
        requisitos que la experiencia ha visto cumplirse al menos una vez."""
        legado: Dict[str, Any] = {
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
        for _, seccion in sorted(self._secciones.values(), key=lambda d: d[1].orden_legado):   # D7: cada sección, su parte
            legado.update(seccion.legado(ahora))
        return legado

    def heredar(self, legado: Dict[str, Any], tasa: float = 1.0) -> int:
        """Lo heredado entra como hipótesis fuerte: hace falta experiencia propia para demostrarlo.
        Con ``tasa`` < 1 (bloque E, E7) solo pasa esa fracción de cada parte del legado: las
        proposiciones de más confianza y los registros con más experiencias (redondeo hacia arriba)."""
        if not self.activa:
            return 0
        proposiciones = list(legado.get("proposiciones", []))
        registros = list(legado.get("registros", []))
        if tasa < 1.0:
            def parte(xs: List[Dict[str, Any]], clave: str) -> List[Dict[str, Any]]:
                k = math.ceil(max(0.0, tasa) * len(xs))
                return sorted(xs, key=lambda d: -float(d[clave]))[:k]
            proposiciones = parte(proposiciones, "confianza")
            registros = parte(registros, "n")
        n = 0
        for d in proposiciones:
            clave = (d["sujeto"], Relacion[d["relacion"]])
            existente = self.saber.get(clave)
            p = Proposicion(d["sujeto"], Relacion[d["relacion"]], confianza=float(d["confianza"]) * 0.8)
            p.confirmaciones = Proposicion.CONFIRMACIONES_MINIMAS - 1
            p.heredada = True
            if existente is not None and existente.c_aut is not None:   # lo del manual se conserva como autoridad
                p.c_aut, p.w_aut = existente.c_aut, existente.w_aut
            self.saber[clave] = p
            n += 1
        for d in registros:
            r = Registro(n=max(1, int(d["n"]) // 2))
            r.suma = float(d["media"]) * r.n
            self.registros[(Verbo[d["verbo"]], d["clase"])] = r
            n += 1
        n += self._diferir("legado", legado, tasa)   # D7: las secciones toman lo suyo al registrarse (o ya, si lo están)
        self.heredados += n
        return n
