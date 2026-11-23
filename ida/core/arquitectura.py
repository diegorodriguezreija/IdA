"""Componente, Módulo y Sistema: la estructura de la mente.

- Un **Componente** produce un tipo de Pieza. Tiene tres barridos: ``reactiva`` (lo que entra
  ahora), ``activa`` (recuperar experiencia) y ``proactiva`` (anotar expectativas). Solo se
  ejecuta si hay piezas de alguno de sus ``entradas`` (o si no declara ninguna).
- Un **Módulo** agrupa los componentes de una etapa (Sentir, Interpretar, Reaccionar, Actuar)
  y los ejecuta por barridos: primero todos los reactivos; después, los
  activos; después, los proactivos. Sin amplitud o potencia, la Onda rechaza o recorta cada
  operación y el resto sigue. Los módulos del Core están exentos de peaje.
- La **Preatención** (D5) es el módulo exento de los Componentes preatentivos de S1: corre una vez por latido, tras
  Core · Sentir, y solo puede modificar piezas de los sensores del Core.
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


SIN_EXPECTATIVA = (Verbo.ACECHAR, Verbo.ESPERAR, Verbo.LEER)   # acciones sin efecto propio que predecir


def expectativa_ejecutada(onda: Onda, sistema: str) -> Optional[Pieza]:
    """Bloque F, F1: la expectativa que ``sistema`` dejó en el latido anterior (``ei``), si la acción
    ejecutada fue aquella sobre la que esperaba. Si no se ejecutó, no hay nada que contrastar."""
    e = onda.ei("Expectativa").get(f"expectativa:{sistema}")
    previa = onda.ei("Accion").get("Accion")
    if e is None or previa is None:
        return None
    if previa.carga.get("verbo") != e.carga.get("verbo") or previa.carga.get("objetivo") != e.carga.get("objetivo"):
        return None
    return e


def variables_proactivas(onda: Onda, soma: Soma, perfil: Perfil) -> Dict[str, float]:
    """Variables sobre las que S1 y S2 dejan expectativas: el déficit de cada necesidad que declara el
    mundo (desde la interocepción) y el placer (/100) y el estrés del cuerpo."""
    valores = {n: float(p.carga["valor"]) for n, p in onda.ev("Interocepcion").items()}
    v: Dict[str, float] = {}
    for necesidad in perfil.necesidades:
        d = necesidad.deficit(valores)
        if d is not None:
            v[necesidad.nombre] = round(d, 4)
    v["placer"] = round(float(soma.placer) / 100.0, 4)
    v["estres"] = round(float(soma.estres), 4)
    return v


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
    observacion: Optional[Observacion] = None   # solo para Core · Sentir: el Organismo la pone a None después (D4)
    con_experiencia: bool = True
    biblioteca: Optional[Any] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    registrados: Set[str] = field(default_factory=set)

    @property
    def latido(self) -> int:
        return self.onda.ciclo

    def registrado(self, nombre: str) -> bool:
        return nombre in self.registrados

    def ubicacion(self) -> str:
        """Dónde está el individuo, de la pieza ``Propiocepcion`` «yo» (D4: fuera de los sensores nadie lee la
        Observación)."""
        yo = self.onda.ev("Propiocepcion").get("yo")
        return str(yo.carga.get("ubicacion") or "") if yo is not None else ""


class Componente:
    tipo: str = "Pieza"
    entradas: tuple = ()
    # Preatención (D5): un Componente preatentivo corre en la preatención de S1 (S1 · Sentir), justo después de
    # Core · Sentir, despierto o dormido, exento de atención; solo modifica piezas de los sensores del Core.
    preatentivo: bool = False
    # Preatentivo integrador (D5): corre el último de la preatención, tras los que ponen rasgos (``Saliencia``).
    integrador: bool = False
    # Componente de un cuerpo (D10): el nombre de su familia. El Core llama a su ``aprender`` en el punto del latido que
    # le corresponde (``Organismo._aprender``), no en el gancho general de plasticidad.
    de_cuerpo: str = ""
    # Opcional (D3, D15): general, pero solo se monta si el mundo lo nombra en ``Registro.opcionales``; si no, se quita al
    # montar y lo demás conserva su orden. Sustituye a las activaciones condicionales.
    opcional: bool = False
    propio_del_mundo: bool = False   # lo pone el Core al montar lo que declara el registro del mundo (D3), cuerpo incluido

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

    # Plasticidad (D6): el Core lo llama en la fase «aprender» de cada latido (también dormido), después de
    # ``Organismo._aprender`` y ``_contrastar``. Por defecto no aprende nada.
    def aprender(self, ctx: Contexto) -> None:
        pass

    # --- utilidades para producir piezas -------------------------------------
    def pieza(self, ctx: Contexto, id: str, arousal: float, confianza: float = 1.0, carga=None, entradas=None, tipo=None,
              decay: float = 0.0, fitness: Optional[float] = None, cost: Optional[float] = None) -> Pieza:
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
            decay=decay,
            fitness=fitness,
            cost=cost,
        )

    def percibir(self, ctx: Contexto, pieza: Pieza) -> Optional[Pieza]:
        """Proyecta la pieza a ``ev``. Fuera del Core cuesta 1 de amplitud y su arousal en potencia.
        Devuelve ``None`` si no queda amplitud y la pieza no entra."""
        return pieza if ctx.onda.percibir(pieza.tipo, pieza, autor=self) else None

    def registrar(self, ctx: Contexto, pieza: Pieza) -> Pieza:
        ctx.onda.registrar(pieza.tipo, pieza, autor=self)
        return pieza

    def modificar(self, ctx: Contexto, pieza: Pieza, *, arousal: Optional[float] = None, confianza: Optional[float] = None,
                  carga: Optional[Dict[str, Any]] = None, entrada: Optional[str] = None) -> Pieza:
        """Cambia una pieza ya emitida a través de la Onda, que comprueba la propiedad y lo anota."""
        return ctx.onda.modificar(pieza, self, arousal=arousal, confianza=confianza, carga=carga, entrada=entrada)

    def proponer(
        self,
        ctx: Contexto,
        verbo: Verbo,
        objetivo: str,
        arousal: float,
        confianza: float,
        motivo: str,
        clase: str = "",
        origen: Optional[Dict[str, str]] = None,
        **datos: Any,
    ) -> Optional[Pieza]:
        """Entrega un candidato de Acción al canal ``acc["Accion"]``. Solo el Tribunal ejecuta.
        ``origen`` (impulso y estrategia) viaja con la acción hasta ``ef["Accion"]``."""
        if verbo not in ctx.verbos:
            return None
        carga: Dict[str, Any] = {"verbo": verbo, "objetivo": objetivo, "clase": clase, "motivo": motivo, "datos": datos}
        if origen:
            carga["origen"] = dict(origen)
        p = self.pieza(
            ctx,
            id=f"{self.sistema}:{verbo.value}:{objetivo}",
            arousal=arousal,
            confianza=confianza,
            carga=carga,
            entradas=[self.nombre],
            tipo="Accion",
        )
        return ctx.onda.proponer("Accion", p, autor=self)


class Modulo:
    prefijo_tiempos = ""   # prefijo de la clave de ``Onda.tiempos_ms`` (la preatención usa el suyo)

    def __init__(self, nombre: str, componentes: List[Componente], exento: bool = False):
        self.nombre = nombre
        self.componentes = list(componentes)
        self.exento = exento

    def ejecutar(self, ctx: Contexto) -> None:
        onda = ctx.onda
        onda.exento = self.exento
        try:
            for barrido in BARRIDOS:
                # Sin amplitud o sin potencia, la Onda rechaza o recorta cada operación; el resto sigue.
                for comp in self.componentes:
                    if not comp.activo(onda):
                        continue
                    onda.control_vital(0, donde=f"{comp.sistema}.{comp.nombre}")
                    t0 = time.perf_counter()
                    getattr(comp, barrido)(ctx)
                    clave = f"{self.prefijo_tiempos}{comp.sistema}.{comp.nombre}"
                    onda.tiempos_ms[clave] = onda.tiempos_ms.get(clave, 0.0) + (time.perf_counter() - t0) * 1000.0
        finally:
            onda.exento = False


class Preatencion(Modulo):
    """La preatención (D5, paso 3 del latido): los Componentes preatentivos de S1 · Sentir.

    Corre una vez por latido, justo después de Core · Sentir y también dormido, exenta de amplitud, potencia y plazo
    como el Sentir del Core. Mientras corre, la Onda está en modo preatención (``Onda.preatencion``): solo admite
    modificar el arousal o los rasgos de piezas de los sensores del Core; emitir o tocar otra cosa lanza ``PiezaAjena``.
    """

    prefijo_tiempos = "preatencion:"

    def __init__(self, componentes: List[Componente]):
        for c in componentes:
            if not c.preatentivo:
                raise ValueError(f"{c.nombre} no es preatentivo y no puede ir en la preatención")
        super().__init__("Preatencion", componentes, exento=True)

    def ejecutar(self, ctx: Contexto) -> None:
        ctx.onda.preatencion = True
        try:
            super().ejecutar(ctx)
        finally:
            ctx.onda.preatencion = False


class Sistema:
    """Un sistema con su meta y sus módulos.

    ``preatencion``: sus Componentes preatentivos (D5). Su sitio en el diseño es ``<sistema>.Sentir``, pero no están en
    el módulo Sentir: los ejecuta el Organismo una sola vez por latido en su ``Preatencion`` (exenta), así que no
    vuelven a correr cuando el sistema late en la cognición. Solo S1 tiene preatención.
    """

    def __init__(self, nombre: str, meta: str, modulos: List[Modulo], preatencion: Optional[List[Componente]] = None):
        self.nombre = nombre
        self.meta = meta
        self.modulos = modulos
        self.preatencion: List[Componente] = []
        for m in modulos:
            for c in m.componentes:
                if c.preatentivo:
                    raise ValueError(f"{c.nombre} es preatentivo: va en la preatención de {nombre}, no en {m.nombre}")
                c.sistema = nombre
        for c in preatencion or []:
            self.añadir_preatentivo(c)

    def añadir_preatentivo(self, componente: Componente) -> None:
        if not componente.preatentivo:
            raise ValueError(f"{componente.nombre} no es preatentivo")
        if self.nombre != "S1":
            raise ValueError(f"Solo S1 tiene preatención ({componente.nombre} en {self.nombre})")
        componente.sistema = self.nombre
        self.preatencion.append(componente)

    def modulo(self, etapa: str) -> Modulo:
        for m in self.modulos:
            if m.nombre == etapa:
                return m
        nuevo = Modulo(etapa, [])
        self.modulos.append(nuevo)
        self.modulos.sort(key=lambda m: ETAPAS.index(m.nombre) if m.nombre in ETAPAS else len(ETAPAS))
        return nuevo

    def añadir(self, etapa: str, componente: Componente) -> None:
        if componente.preatentivo:
            if etapa != "Sentir":
                raise ValueError(f"{componente.nombre} es preatentivo: solo puede ir en {self.nombre}.Sentir")
            self.añadir_preatentivo(componente)
            return
        componente.sistema = self.nombre
        self.modulo(etapa).componentes.append(componente)

    def latir(self, ctx: Contexto) -> None:
        for m in self.modulos:
            m.ejecutar(ctx)

    def componentes(self) -> List[Componente]:
        return [c for m in self.modulos for c in m.componentes]
