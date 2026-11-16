"""Utilidades compartidas por los componentes base. Solo usan el vocabulario común (rasgos)."""

from typing import Any, Dict, Iterable, List, Optional, Tuple

from ida.core.arquitectura import Componente, Contexto
from ida.core import estrategia as est
from ida.core.estrategia import Catalogo, Definicion
from ida.core.pieza import Pieza

ALCANCE = 0.9          # proximidad a partir de la cual algo está al alcance
MAX_OBJETOS = 7        # atención limitada: 7 ± 2 objetos por latido


def exterocepcion(ctx: Contexto) -> List[Pieza]:
    return list(ctx.onda.ev("Exterocepcion").values())


def lugares(ctx: Contexto) -> List[Pieza]:
    return [p for p in exterocepcion(ctx) if p.rasgo("lugar") >= 0.5]


def objetos(ctx: Contexto) -> List[Pieza]:
    return list(ctx.onda.ev("Objeto").values())


def al_alcance(p: Pieza) -> bool:
    return p.rasgo("proximidad") >= ALCANCE


def apetito(ctx: Contexto) -> float:
    """Ganas de comer: un apetito basal más el hambre del cuerpo."""
    return 0.25 + 0.75 * ctx.soma.hambre()


def mejor(piezas: Iterable[Pieza], clave) -> Optional[Pieza]:
    piezas = list(piezas)
    return max(piezas, key=clave) if piezas else None


def alarma(ctx: Contexto) -> Optional[Pieza]:
    return ctx.onda.ev("Supervivencia").get("alarma")


class Accion(Componente):
    """Etapa Actuar de un sistema (decisiones 3 y 17): traduce cada estrategia activa del sistema
    en una acción, con su origen (impulso y estrategia). Es la dueña de las piezas ``Accion``."""

    tipo = "Accion"

    def __init__(self, catalogo: Catalogo):
        super().__init__("Accion")
        self.catalogo = catalogo

    def reactiva(self, ctx: Contexto) -> None:
        for p in list(ctx.onda.estrategias.values()):
            if p.sistema != self.sistema:
                continue
            definicion = self.catalogo.get(p.carga["nombre"])
            propuesta = definicion.actuar(ctx, p) if definicion is not None else None
            if propuesta is None:
                continue
            self.proponer(ctx, propuesta.verbo, propuesta.objetivo, propuesta.arousal, propuesta.confianza, propuesta.motivo,
                          clase=propuesta.clase, origen={"impulso": p.carga["impulso"], "estrategia": p.id}, **(propuesta.datos or {}))


class Estrategia(Componente):
    """Elige, mantiene y abandona las estrategias de un sistema (decisiones 4, 16 y 17).

    Considera todos los impulsos (de cualquier sistema) y las intenciones de S3; el catálogo del
    sistema decide a cuáles sirve. ``impulso_critico`` (en S1, Seguridad) tiene reflejo y último
    recurso innato cuando todas sus estrategias se agotan.

    - Una estrategia activa como mucho por impulso, más el reflejo. Continúa mientras sea elegible.
      Solo cede ante otra elegible si la supera con un margen claro (histéresis,
      ``MARGEN_SUSTITUCION``) en puntuación = valor aprendido + prioridad innata / 100 (p. ej., de
      huir a plantar cara). Las fases de una misma estrategia (buscar, acercarse, comer) no son
      sustituciones: las fija ``Definicion.paso`` en cada latido.
    - Se cierra al bajar la necesidad al objetivo (completada), al dejar de ser elegible (sin objeto)
      o al agotarse (agotada; no se vuelve a elegir durante ``Perfil.enfriamiento_estrategia``).
    - Agotar una estrategia de Seguridad cambia de estrategia, no abandona el impulso; si todas
      las elegibles están agotadas, último recurso innato (quedarse quieto o huir).
    - Si nada es elegible para un impulso en un mundo que no deja esperar, último recurso genérico
      (seguir en movimiento). Un último recurso cede en cuanto otra estrategia es elegible.
    - Elección: la de mayor puntuación; la apertura regula cuánto se prueba otra al azar. Valor
      aprendido por impulso y estrategia durante la vida, al cerrarse: el mérito es el feedback de su sistema
      de su impulso acumulado mientras se ejecutó, normalizado por la intensidad inicial (en [−1, 1]);
      la fuerza del aprendizaje es esa intensidad inicial (su arousal). Sin experiencia no se aprende
      ni se explora.
    """

    tipo = "Estrategia"
    VALOR_INICIAL = 0.5
    TASA = 0.5
    EXPLORACION = 0.2
    MARGEN_SUSTITUCION = 0.2

    def __init__(self, catalogo: Catalogo, impulso_critico: Optional[str] = None):
        super().__init__("Estrategia")
        self.catalogo = catalogo
        self.impulso_critico = impulso_critico
        self.valor: Dict[Tuple[str, str], float] = {}
        self.enfriando: Dict[Tuple[str, str], int] = {}

    def reactiva(self, ctx: Contexto) -> None:
        onda, perfil = ctx.onda, ctx.perfil
        impulsos = {**onda.ef("Impulso"), **onda.ef("Intencion")}
        previa = onda.ei("Accion").get("Accion")
        ejecutada = previa.carga.get("origen", {}).get("estrategia") if previa is not None else None
        fb = onda.ef("Feedback").get(f"feedback:{self.sistema}")
        feedback = fb.carga.get("por_impulso", {}) if fb is not None else {}
        notas: Dict[str, Any] = {"activas": [], "ejecutada": None, "abandonos": [], "reflejo": False, "interrumpe": False, "sustituciones": 0}

        for p in [p for p in onda.estrategias.values() if p.sistema == self.sistema]:
            c = p.carga
            if p.id == ejecutada:
                notas["ejecutada"] = c["nombre"]
            if c["reflejo"]:
                if ctx.latido - c["inicio"] >= perfil.duracion_reflejo:
                    self._cerrar(ctx, p, est.TERMINADA)
                continue
            imp = impulsos.get(c["impulso"])
            intensidad = float(imp.carga["intensidad"]) if imp is not None else 0.0
            cambios = est.avanzar(c, intensidad, p.id == ejecutada, ctx.latido, perfil.gracia_estrategia, perfil.ritmo_esperado_estrategia)
            if p.id == ejecutada:          # el mérito se lo lleva la estrategia que se ejecutó (decisión 23)
                cambios["merito"] = float(c.get("merito", 0.0)) + float(feedback.get(c["impulso"], 0.0))
            self.modificar(ctx, p, carga=cambios)
            definicion = self.catalogo.get(c["nombre"])
            if intensidad <= c["objetivo"] + 1e-9:
                self._cerrar(ctx, p, est.COMPLETADA)
            elif c["agotamiento"] >= 1.0 and (definicion is None or definicion.agotable):
                self._cerrar(ctx, p, est.AGOTADA)
                self.enfriando[(c["impulso"], c["nombre"])] = ctx.latido + perfil.enfriamiento_estrategia
                notas["abandonos"].append(c["nombre"])
            elif definicion is None or not definicion.elegible(ctx, c["impulso"], intensidad):
                self._cerrar(ctx, p, est.SIN_OBJETO)
            elif definicion.ultimo_recurso and self._mejor(ctx, c["impulso"], imp.carga.get("rasgo") if imp is not None else None, intensidad):
                self._cerrar(ctx, p, est.SUSTITUIDA)     # un último recurso cede en cuanto hay otra opción
                notas["sustituciones"] += 1
            else:
                paso = definicion.paso(ctx, p)
                if paso != c.get("paso"):
                    self.modificar(ctx, p, carga={"paso": paso})

        sobresalto = onda.ef("Reflejo").get("sobresalto")
        reflejo_activo = any(p.sistema == self.sistema and p.carga["reflejo"] for p in onda.estrategias.values())
        if sobresalto is not None and not reflejo_activo and self.impulso_critico is not None:
            critico = self.impulso_critico
            imp = impulsos.get(critico)
            reflejo = next((d for d in self.catalogo.todas() if d.reflejo and d.sirve(critico, None)), None)
            if imp is not None and reflejo is not None:
                p = self._activar(ctx, reflejo, critico, float(imp.carga["intensidad"]), float(imp.carga["objetivo"]))
                notas["reflejo"] = True
                notas["interrumpe"] = ejecutada is not None and ejecutada != p.id and not ejecutada.startswith("innato:")

        activa_por_impulso = {p.carga["impulso"]: p for p in onda.estrategias.values() if p.sistema == self.sistema and not p.carga["reflejo"]}
        for nombre, imp in impulsos.items():
            intensidad, objetivo = float(imp.carga["intensidad"]), float(imp.carga["objetivo"])
            if intensidad <= objetivo:
                continue
            actual = activa_por_impulso.get(nombre)
            if actual is not None:
                # Continuidad, salvo que otra elegible la supere con margen claro (histéresis).
                mejor_def = self._mejor(ctx, nombre, imp.carga.get("rasgo"), intensidad)
                if mejor_def is None or mejor_def.nombre == actual.carga["nombre"] or \
                        self._puntuacion(nombre, mejor_def) < self._puntuacion(nombre, self.catalogo.get(actual.carga["nombre"])) + self.MARGEN_SUSTITUCION:
                    continue
                self._cerrar(ctx, actual, est.SUSTITUIDA)
                notas["sustituciones"] += 1
                self._activar(ctx, mejor_def, nombre, intensidad, objetivo, ctx_paso=True)
                continue
            definicion = self._elegir(ctx, nombre, imp.carga.get("rasgo"), intensidad)
            if definicion is not None:
                self._activar(ctx, definicion, nombre, intensidad, objetivo, ctx_paso=True)

        notas["activas"] = [p.carga["nombre"] for p in onda.estrategias.values() if p.sistema == self.sistema]
        onda.notas[f"estrategias_{self.sistema}"] = notas

    def _puntuacion(self, impulso: str, d: Optional[Definicion]) -> float:
        """Valor aprendido + prioridad innata / 100."""
        if d is None:
            return -1.0
        return self.valor.get((impulso, d.nombre), self.VALOR_INICIAL) + d.prioridad / 100.0

    def _disponibles(self, ctx: Contexto, impulso: str, rasgo: Optional[str], intensidad: float) -> Tuple[List[Definicion], List[Definicion]]:
        elegibles = [d for d in self.catalogo.todas()
                     if not d.reflejo and not d.ultimo_recurso and d.sirve(impulso, rasgo) and d.elegible(ctx, impulso, intensidad)]
        return elegibles, [d for d in elegibles if self.enfriando.get((impulso, d.nombre), -1) <= ctx.latido]

    def _mejor(self, ctx: Contexto, impulso: str, rasgo: Optional[str], intensidad: float) -> Optional[Definicion]:
        _, disponibles = self._disponibles(ctx, impulso, rasgo, intensidad)
        return max(disponibles, key=lambda d: self._puntuacion(impulso, d)) if disponibles else None

    def _elegir(self, ctx: Contexto, impulso: str, rasgo: Optional[str], intensidad: float) -> Optional[Definicion]:
        elegibles, disponibles = self._disponibles(ctx, impulso, rasgo, intensidad)
        if not disponibles:
            ultimos = [d for d in self.catalogo.todas() if d.ultimo_recurso and d.sirve(impulso, rasgo)]
            if elegibles and impulso == self.impulso_critico:     # todas agotadas: respuesta innata de último recurso
                return next((d for d in ultimos if not d.cualquier_impulso), None)
            # Nada elegible: en un mundo que no deja esperar, seguir en movimiento.
            return next((d for d in ultimos if d.cualquier_impulso and d.elegible(ctx, impulso, intensidad)), None)
        if ctx.con_experiencia and len(disponibles) > 1 and ctx.azar.probabilidad(self.EXPLORACION * ctx.arquetipo.apertura):
            return ctx.azar.eleccion(disponibles)
        return max(disponibles, key=lambda d: self._puntuacion(impulso, d))

    def _activar(self, ctx: Contexto, definicion: Definicion, impulso: str, intensidad: float, objetivo: float,
                 ctx_paso: bool = False) -> Pieza:
        p = est.nueva(self.sistema, definicion, impulso, intensidad, objetivo, ctx.latido)
        if ctx_paso:      # fase inicial de su máquina de estados
            p = est.nueva(self.sistema, definicion, impulso, intensidad, objetivo, ctx.latido, paso=definicion.paso(ctx, p))
        return ctx.onda.activar(p, self)

    def _cerrar(self, ctx: Contexto, p: Pieza, estado: str) -> None:
        c = p.carga
        if ctx.con_experiencia and not c["reflejo"]:
            clave = (c["impulso"], c["nombre"])
            v = self.valor.get(clave, self.VALOR_INICIAL)
            tramo = max(float(c["valor_inicial"]) - float(c["objetivo"]), 0.05)
            merito = max(-1.0, min(1.0, float(c.get("merito", 0.0)) / tramo))
            self.valor[clave] = v + self.TASA * float(c["valor_inicial"]) * (merito - v)
        ctx.onda.cerrar(p, estado, self)
