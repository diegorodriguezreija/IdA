"""Proposiciones, registros y expectativas: lo que el Core aprende del efecto de la acción anterior (D7, sección del
Core: proposiciones, registros verbo × clase y expectativa del latido siguiente)."""

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, cast

from ida.nucleo.pieza import acotar
from ida.nucleo.vocabulario import EstadoSaber, Relacion, Verbo


# ---------------------------------------------------------------------------
# Conocimiento formal (lenguaje interno de S3)
# ---------------------------------------------------------------------------
class Proposicion:
    """«<clase> <relación>», con confianza ponderada por fuente de evidencia."""

    CONFIRMACIONES_MINIMAS = 3
    CONFIANZA_DEMOSTRADA = 0.7
    LATIDOS_SIN_REFUTAR = 30
    DECAY = 0.05             # bloque E, E4: caducidad por noche de c_exp (reducción nocturna ×0,95)
    DANO_SATURA = 10.0       # pérdida de vitalidad con la que el arousal de daño llega a 1 (el doble de un envenenamiento grave)

    def __init__(
        self,
        sujeto: str,
        relacion: Relacion,
        confianza: float = 0.3,
        confirmaciones: int = 0,
        refutaciones: int = 0,
        ultima_refutacion: int = -10**9,
        heredada: bool = False,
        actualizada: int = 0,
        c_aut: Optional[float] = None,
        w_aut: float = 0.0,
        c_exp: Optional[float] = None,
    ):
        self.sujeto = sujeto
        self.relacion = relacion
        self.c_exp = c_exp if c_exp is not None else confianza
        self.confirmaciones = confirmaciones
        self.refutaciones = refutaciones
        self.ultima_refutacion = ultima_refutacion
        self.heredada = heredada
        self.actualizada = actualizada
        self.c_aut = c_aut
        self.w_aut = w_aut
        self.decay = self.DECAY   # metadato decay (decisión 7): lo usa la reducción nocturna (E4)

    @property
    def confianza(self) -> float:
        if self.c_aut is None or self.w_aut <= 0.0:
            return self.c_exp
        w_exp = float(1 + self.confirmaciones + self.refutaciones)
        return (w_exp * self.c_exp + self.w_aut * self.c_aut) / (w_exp + self.w_aut)

    @confianza.setter
    def confianza(self, valor: float) -> None:
        self.c_exp = valor

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
        self.c_exp = acotar(self.c_exp + 0.15 * (1.0 - self.c_exp))
        self.actualizada = ahora

    def marcar_dano(self, perdida_vitalidad: float) -> None:
        """Un recuerdo de daño caduca menos cuanto mayor fue el daño: decay = DECAY × (1 − arousal de daño),
        con arousal de daño = pérdida / DANO_SATURA acotado a [0, 1]. Se queda el menor decay visto."""
        arousal = acotar(perdida_vitalidad / self.DANO_SATURA)
        self.decay = min(self.decay, round(self.DECAY * (1.0 - arousal), 6))

    def refutar(self, ahora: int) -> None:
        """...y baja más rápido."""
        self.refutaciones += 1
        self.c_exp = acotar(self.c_exp * 0.7 - 0.05)
        self.ultima_refutacion = ahora
        self.actualizada = ahora

    def aplicar_autoridad(self, veredicto: str, confianza_fuente: float, peso_fuente: float, ahora: int) -> None:
        """Aplica testimonio externo de autoridad. Modula c_aut y w_aut."""
        if veredicto == "afirma":
            c_val = acotar(confianza_fuente)
        elif veredicto == "niega":
            c_val = acotar(1.0 - confianza_fuente)
        else:
            return
        if self.c_aut is None:
            self.c_aut = c_val
            self.w_aut = max(0.0, peso_fuente)
        else:
            w_total = self.w_aut + peso_fuente
            if w_total > 0:
                self.c_aut = (self.w_aut * self.c_aut + peso_fuente * c_val) / w_total
                self.w_aut = w_total
        self.actualizada = ahora

    def texto(self, ahora: int) -> str:
        partes_origen = []
        if self.heredada:
            partes_origen.append("heredada")
        if self.c_aut is not None and self.w_aut > 0.0:
            partes_origen.append("autoridad")
        origen = f", {', '.join(partes_origen)}" if partes_origen else ""
        return f"«{self.sujeto} {self.relacion.value}» ({self.estado(ahora).value}{origen}, {self.confianza:.2f})"

    def __repr__(self) -> str:
        return f"Proposicion({self.sujeto!r}, {self.relacion!r}, confianza={self.confianza:.3f})"

    def __eq__(self, otro: object) -> bool:
        if not isinstance(otro, Proposicion):
            return False
        return (
            self.sujeto == otro.sujeto
            and self.relacion == otro.relacion
            and self.confirmaciones == otro.confirmaciones
            and self.refutaciones == otro.refutaciones
            and self.heredada == otro.heredada
            and round(self.confianza, 4) == round(otro.confianza, 4)
        )


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


class Proposiciones:
    """Parte de la ``Memoria`` (fachada en ``almacen.py``): conocimiento formal, recuerdos agregados por (verbo, clase) y
    la expectativa de la acción que se va a ejecutar, con su aprendizaje (el cuarteto ``ei → ef``)."""

    saber: Dict[Tuple[str, Relacion], Proposicion]
    registros: Dict[Tuple[Verbo, str], Registro]
    expectativa: Optional[Expectativa]
    aciertos: int
    fallos: int

    if TYPE_CHECKING:
        @property
        def activa(self) -> bool: ...

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
        perdida = max(0.0, -delta.get("vitalidad", 0.0))

        def confirmar(c: str, rel: Relacion) -> None:
            p = cast(Proposicion, self.proposicion(c, rel, crear=True))
            antes = p.estado(ahora)
            p.confirmar(ahora)
            if rel == Relacion.PELIGROSO and perdida > 0.0:
                p.marcar_dano(perdida)
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

    def peligrosa(self, clase: str) -> bool:
        """Paso 6: si la memoria tiene la clase por peligrosa (``Relacion.PELIGROSO`` del manual o de la experiencia, no
        refutada). Es lo que da el previo de su daño."""
        p = self.saber.get((clase, Relacion.PELIGROSO))
        return p is not None and p.estado(0) != EstadoSaber.REFUTADA and p.confianza >= 0.5

    def _olvidar_hipotesis(self, ahora: int) -> int:
        """Olvido de hipótesis por antigüedad (sin reducción nocturna): lo demostrado no se olvida."""
        olvidadas = 0
        for clave, p in list(self.saber.items()):
            estado = p.estado(ahora)
            if estado == EstadoSaber.DEMOSTRADA:
                continue
            if estado == EstadoSaber.HIPOTESIS and ahora - p.actualizada > 150 and p.confianza < 0.4:
                del self.saber[clave]
                olvidadas += 1
        return olvidadas

    def _olvidar_registros(self, ahora: int) -> int:
        recuerdos_olvidados = 0
        for clave_r, r in list(self.registros.items()):
            if r.n == 1 and abs(r.media) < 0.5 and ahora - r.ultimo > 200:
                del self.registros[clave_r]
                recuerdos_olvidados += 1
        return recuerdos_olvidados
