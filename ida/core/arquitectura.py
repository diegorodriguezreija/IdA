"""Componente, Módulo y Sistema: la estructura de la mente.

- Un **Componente** produce un tipo de Pieza. Tiene tres barridos: ``reactiva`` (lo que entra
  ahora), ``activa`` (recuperar experiencia) y ``proactiva`` (anotar expectativas). Solo se
  ejecuta si hay piezas de alguno de sus ``entradas`` (o si no declara ninguna).
- Un **Módulo** agrupa los componentes de una etapa (Sentir, Interpretar, Reaccionar, Actuar)
  y los ejecuta por barridos: primero todos los reactivos; después, si queda amplitud, los
  activos; después, los proactivos. Los módulos del Core están exentos de peaje.
- Un **Sistema** (S1, S2, S3) tiene una meta y sus módulos.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from ida.core.azar import Azar
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.mundo import Observacion, Perfil
from ida.core.onda import Onda
from ida.core.pieza import Pieza
from ida.core.soma import Soma
from ida.core.vocabulario import Verbo

ETAPAS = ("Sentir", "Interpretar", "Reaccionar", "Actuar")
BARRIDOS = ("reactiva", "activa", "proactiva")


@dataclass
class Contexto:
    """Todo lo que un componente puede consultar durante un latido."""

    onda: Onda
    soma: Soma
    memoria: Memoria
    arquetipo: Arquetipo
    azar: Azar
    perfil: Perfil
    verbos: Set[Verbo]
    observacion: Optional[Observacion] = None
    con_experiencia: bool = True
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def latido(self) -> int:
        return self.onda.ciclo


class Componente:
    tipo: str = "Pieza"
    entradas: tuple = ()

    def __init__(self, nombre: Optional[str] = None):
        self.nombre = nombre or self.__class__.__name__
        self.sistema = ""   # lo fija el Sistema (o "CORE"/"MUNDO") al montarlo

    def activo(self, onda: Onda) -> bool:
        return not self.entradas or any(onda.reactiva.hay(c) for c in self.entradas)

    # Los tres barridos (todos opcionales)
    def reactiva(self, ctx: Contexto) -> None:
        pass

    def activa(self, ctx: Contexto) -> None:
        pass

    def proactiva(self, ctx: Contexto) -> None:
        pass

    # --- utilidades para producir piezas -------------------------------------
    def pieza(self, ctx: Contexto, id: str, arousal: float, confianza: float = 1.0, carga=None, entradas=None, tipo=None) -> Pieza:
        return Pieza(
            id=id,
            tipo=tipo or self.tipo,
            arousal=arousal,
            confianza=confianza,
            carga=dict(carga or {}),
            entradas=list(entradas or []),
            sistema=self.sistema,
            creada=ctx.latido,
            actualizada=ctx.latido,
        )

    def percibir(self, ctx: Contexto, pieza: Pieza, coste: int = 1) -> Pieza:
        ctx.onda.percibir(pieza.tipo, pieza, coste)
        return pieza

    def registrar(self, ctx: Contexto, pieza: Pieza) -> Pieza:
        ctx.onda.registrar(pieza.tipo, pieza)
        return pieza

    def proponer(
        self,
        ctx: Contexto,
        verbo: Verbo,
        objetivo: str,
        arousal: float,
        confianza: float,
        motivo: str,
        clase: str = "",
        **datos: Any,
    ) -> Optional[Pieza]:
        """Entrega un candidato de Ejecución al canal ``acc["Ejecucion"]``. Solo el Tribunal ejecuta."""
        if verbo not in ctx.verbos:
            return None
        p = self.pieza(
            ctx,
            id=f"{self.sistema}:{verbo.value}:{objetivo}",
            arousal=arousal,
            confianza=confianza,
            carga={"verbo": verbo, "objetivo": objetivo, "clase": clase, "motivo": motivo, "datos": datos},
            entradas=[self.nombre],
            tipo="Ejecucion",
        )
        return ctx.onda.proponer("Ejecucion", p)


class Modulo:
    def __init__(self, nombre: str, componentes: List[Componente], exento: bool = False):
        self.nombre = nombre
        self.componentes = list(componentes)
        self.exento = exento

    def ejecutar(self, ctx: Contexto) -> None:
        onda = ctx.onda
        onda.exento = self.exento
        try:
            for barrido in BARRIDOS:
                if barrido != "reactiva" and not self.exento and onda.amplitud_restante() <= 0:
                    break
                for comp in self.componentes:
                    if not comp.activo(onda):
                        continue
                    onda.control_vital(0, donde=f"{comp.sistema}.{comp.nombre}")
                    t0 = time.perf_counter()
                    getattr(comp, barrido)(ctx)
                    clave = f"{comp.sistema}.{comp.nombre}"
                    onda.tiempos_ms[clave] = onda.tiempos_ms.get(clave, 0.0) + (time.perf_counter() - t0) * 1000.0
        finally:
            onda.exento = False


class Sistema:
    def __init__(self, nombre: str, meta: str, modulos: List[Modulo]):
        self.nombre = nombre
        self.meta = meta
        self.modulos = modulos
        for m in modulos:
            for c in m.componentes:
                c.sistema = nombre

    def modulo(self, etapa: str) -> Modulo:
        for m in self.modulos:
            if m.nombre == etapa:
                return m
        nuevo = Modulo(etapa, [])
        self.modulos.append(nuevo)
        self.modulos.sort(key=lambda m: ETAPAS.index(m.nombre) if m.nombre in ETAPAS else len(ETAPAS))
        return nuevo

    def añadir(self, etapa: str, componente: Componente) -> None:
        componente.sistema = self.nombre
        self.modulo(etapa).componentes.append(componente)

    def latir(self, ctx: Contexto) -> None:
        for m in self.modulos:
            m.ejecutar(ctx)

    def componentes(self) -> List[Componente]:
        return [c for m in self.modulos for c in m.componentes]
