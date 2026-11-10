"""Memoria del individuo: recuerdos (dimensión activa), expectativas (dimensión proactiva),
conocimiento formal legible, episodios, sueño y herencia.

Escribe el Core, no los componentes: los componentes señalan lo relevante con su arousal y el
Core guarda lo más saliente de cada latido. La escritura va en dos velocidades: lo mínimo en
cada latido (en RAM) y lo costoso (persistir, olvidar, consolidar) al dormir o al morir.
"""

import math
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


def _signo(x: float, margen: float = 0.25) -> int:
    return 0 if abs(x) < margen else (1 if x > 0 else -1)


class Memoria:
    def __init__(self, perfil: str = "completa"):
        if perfil not in PERFILES_MEMORIA:
            raise ValueError(f"Perfil de memoria desconocido: {perfil}")
        self.perfil = perfil
        self.k = PERFILES_MEMORIA[perfil]
        self.saber: Dict[Tuple[str, Relacion], Proposicion] = {}
        self.registros: Dict[Tuple[Verbo, str], Registro] = {}
        self.lugares: Dict[str, float] = {}            # bienestar recordado por lugar (hogar)
        self.clases_vistas: Dict[str, int] = {}        # familiaridad por clase
        self.expectativa: Optional[Expectativa] = None
        self.buffer: List[Dict[str, Any]] = []         # piezas salientes pendientes de persistir
        self.episodios: List[Episodio] = []
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

    # --- sueño: lo costoso, fuera del camino crítico --------------------------
    def consolidar(self, ahora: int) -> Dict[str, int]:
        """Olvido y consolidación. Lo demostrado y lo de arousal extremo no se olvida."""
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
        # Del búfer solo sobrevive lo de arousal alto (lo demás ya está agregado en registros)
        self.buffer = [p for p in self.buffer if p["arousal"] >= 0.85]
        return {"hipotesis_olvidadas": olvidadas, "recuerdos_olvidados": recuerdos_olvidados}

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
