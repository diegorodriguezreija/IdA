"""Estrategia Alimentarse."""

from typing import Optional

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.estrategia import Definicion, Propuesta
from ida.nucleo.pieza import Pieza, acotar
from ida.nucleo.vocabulario import Verbo
from ida.s1.comun import (
    SATISFACE_MIN,
    Comestible,
    _aceptables_a_la_vista,
    _al_alcance,
    _destino_comida,
    _hacia,
    _lugares_permitidos,
    _rechazado,
)
from ida.sistemas.motivacion import apetito
from ida.sistemas.piezas import mejor

BUSCAR, ACERCARSE, COMER = "buscar", "acercarse", "comer"


class Alimentarse(Definicion):
    """Necesidades que satisface lo nutritivo (decisión 2 del autor sobre C1): una sola estrategia con
    tres fases, buscar → acercarse → comer.

    - **comer**: hay algo aceptable al alcance (y el mundo deja comer): el mejor por nutritivo − peligro.
    - **acercarse**: hay comida aceptable a la vista o se huele comida en un lugar a la vista: ir
    hacia el lugar más nutritivo y menos peligroso. Si lo que hay al alcance se rechaza pero hay
    comida aceptable a la vista, ir hacia esa comida (por posición percibida, si el mundo la da):
    el olor del lugar también lleva a lo rechazado.
    - **buscar**: lo único al alcance se rechaza (se valora mal o se sabe dañino) y no hay nada
    aceptable a la vista: no se come y se va a otro sitio, el lugar más nuevo y menos peligroso.
    Elegible mientras haya algo de eso; si no hay nada a la vista, se cierra y exploran otros sistemas.

    **Por necesidad** (paso 0b, si ``Apetencia`` está registrada, D15): cada impulso al que sirve solo
    considera comestible lo que satisface **su** necesidad (``Apetencia``: satisface ≥ ``SATISFACE_MIN``),
    elige entre ello por el deseo (aliestesia) y su arousal sale de la intensidad del impulso de origen,
    no del hambre global del cuerpo. El olor de los lugares solo guía si su rasgo no es ambiguo (una sola
    necesidad declarada se satisface con él); si no, se acerca por posición percibida.
    """

    nombre = "alimentarse"
    rasgo = "nutritivo"
    prioridad = 10

    def rechaza(self, ctx: Contexto, o: Pieza) -> bool:
        """Criterio de elección del objeto. Un mundo puede ampliarlo con una estrategia propia."""
        return _rechazado(ctx, o)

    # --- paso 0b: por necesidad ---------------------------------------------------------------
    @staticmethod
    def _apetencia(ctx: Contexto, o: Pieza) -> Optional[Pieza]:
        return ctx.onda.ev("Apetencia").get(o.id)

    def _comestible(self, ctx: Contexto, impulso: str) -> Comestible:
        def comestible(o: Pieza) -> bool:
            a = self._apetencia(ctx, o)
            return a is not None and float(a.carga["satisface"].get(impulso, 0.0)) >= SATISFACE_MIN
        return comestible

    def _deseo(self, ctx: Contexto, o: Pieza) -> float:
        a = self._apetencia(ctx, o)
        return float(a.carga["deseo"]) if a is not None else 0.0

    @staticmethod
    def _olor_sin_ambiguedad(ctx: Contexto, impulso: str) -> bool:
        """El rasgo de los lugares (su olor) lleva a lo que satisface ``impulso`` solo si ninguna otra necesidad
        declarada se satisface con ese mismo rasgo."""
        rasgos = {n.nombre: n.rasgo for n in ctx.perfil.necesidades}
        rasgo = rasgos.get(impulso)
        return rasgo is not None and sum(1 for r in rasgos.values() if r == rasgo) == 1

    def _destino_olor(self, ctx: Contexto, impulso: str) -> Optional[Pieza]:
        return _destino_comida(ctx) if self._olor_sin_ambiguedad(ctx, impulso) else None

    @staticmethod
    def _intensidad(ctx: Contexto, impulso: str) -> float:
        imp = ctx.onda.ef("Impulso").get(impulso)
        return float(imp.carga["intensidad"]) if imp is not None else 0.0

    def _elegible_por_necesidad(self, ctx: Contexto, impulso: str) -> bool:
        comestible = self._comestible(ctx, impulso)
        aceptables, rechazados = _al_alcance(ctx, self.rechaza, comestible)
        return bool(aceptables or rechazados or _aceptables_a_la_vista(ctx, self.rechaza, comestible)) or \
            self._destino_olor(ctx, impulso) is not None

    def _paso_por_necesidad(self, ctx: Contexto, impulso: str) -> str:
        comestible = self._comestible(ctx, impulso)
        aceptables, rechazados = _al_alcance(ctx, self.rechaza, comestible)
        if aceptables and Verbo.COMER in ctx.verbos and self._intensidad(ctx, impulso) > 0.0:
            return COMER
        if _aceptables_a_la_vista(ctx, self.rechaza, comestible):
            return ACERCARSE
        if rechazados and not aceptables:
            return BUSCAR
        return ACERCARSE if self._destino_olor(ctx, impulso) is not None else BUSCAR

    def _actuar_por_necesidad(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        impulso = str(estrategia.carga["impulso"])
        ganas = 0.25 + 0.75 * self._intensidad(ctx, impulso)     # como ``apetito``, con la intensidad del impulso de origen
        comestible = self._comestible(ctx, impulso)
        paso = estrategia.carga.get("paso")
        if paso == COMER:
            aceptables, _ = _al_alcance(ctx, self.rechaza, comestible)
            cerca = mejor(aceptables, lambda o: self._deseo(ctx, o) - o.rasgo("peligro"))
            if cerca is not None:
                return Propuesta(Verbo.COMER, cerca.id, acotar(0.35 + 0.6 * ganas), 0.7, f"comer {cerca.clase}", clase=cerca.clase)
        if paso == ACERCARSE:
            vista = mejor(_aceptables_a_la_vista(ctx, self.rechaza, comestible),
                          lambda o: self._deseo(ctx, o) * o.rasgo("proximidad") - o.rasgo("peligro"))
            if vista is not None:
                lugar = _hacia(ctx, vista)
                if lugar is not None:
                    a = self._apetencia(ctx, vista)
                    s = float(a.carga["satisface"].get(impulso, 0.0)) if a is not None else 0.0
                    return Propuesta(Verbo.MOVER, lugar.id, acotar(0.25 + 0.6 * ganas * s), 0.6, f"acercarse a {vista.clase}", clase=lugar.clase)
            destino = self._destino_olor(ctx, impulso)
            if destino is not None:
                ar = acotar(0.25 + 0.6 * ganas * destino.rasgo("nutritivo"))
                return Propuesta(Verbo.MOVER, destino.id, ar, 0.6, "acercarse a la comida", clase=destino.clase)
        if paso in (BUSCAR, ACERCARSE):
            otro = mejor([lugar for lugar in _lugares_permitidos(ctx) if lugar.rasgo("peligro") < 0.5],
                         lambda lugar: lugar.rasgo("novedad") - lugar.rasgo("peligro"))
            if otro is not None:
                return Propuesta(Verbo.MOVER, otro.id, acotar(0.2 + 0.3 * ganas), 0.5, "buscar comida en otro sitio", clase=otro.clase)
        return None

    # --- conducta -----------------------------------------------------------------------------
    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        if ctx.registrado("Apetencia"):
            return self._elegible_por_necesidad(ctx, impulso)
        aceptables, rechazados = _al_alcance(ctx, self.rechaza)
        return bool(aceptables or rechazados) or _destino_comida(ctx) is not None

    def paso(self, ctx: Contexto, estrategia: Pieza) -> str:
        if ctx.registrado("Apetencia"):
            return self._paso_por_necesidad(ctx, str(estrategia.carga["impulso"]))
        aceptables, rechazados = _al_alcance(ctx, self.rechaza)
        if aceptables and Verbo.COMER in ctx.verbos and ctx.soma.alimentacion < 95.0:
            return COMER
        if rechazados and not aceptables:
            return ACERCARSE if _aceptables_a_la_vista(ctx, self.rechaza) else BUSCAR
        return ACERCARSE if _destino_comida(ctx) is not None else BUSCAR

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        if ctx.registrado("Apetencia"):
            return self._actuar_por_necesidad(ctx, estrategia)
        paso = estrategia.carga.get("paso")
        if paso == COMER:
            aceptables, _ = _al_alcance(ctx, self.rechaza)
            cerca = mejor(aceptables, lambda o: o.rasgo("nutritivo") - o.rasgo("peligro"))
            if cerca is not None:
                return Propuesta(Verbo.COMER, cerca.id, acotar(0.35 + 0.6 * apetito(ctx)), 0.7, f"comer {cerca.clase}", clase=cerca.clase)
        if paso == ACERCARSE:
            _, rechazados = _al_alcance(ctx, self.rechaza)
            vista = mejor(_aceptables_a_la_vista(ctx, self.rechaza), lambda o: o.rasgo("nutritivo") * o.rasgo("proximidad") - o.rasgo("peligro"))
            if rechazados and vista is not None:
                lugar = _hacia(ctx, vista)
                if lugar is not None:
                    ar = acotar(0.25 + 0.6 * apetito(ctx) * vista.rasgo("nutritivo"))
                    return Propuesta(Verbo.MOVER, lugar.id, ar, 0.6, f"acercarse a {vista.clase}", clase=lugar.clase)
            destino = _destino_comida(ctx)
            if destino is not None:
                ar = acotar(0.25 + 0.6 * apetito(ctx) * destino.rasgo("nutritivo"))
                return Propuesta(Verbo.MOVER, destino.id, ar, 0.6, "acercarse a la comida", clase=destino.clase)
        if paso == BUSCAR:
            otro = mejor([lugar for lugar in _lugares_permitidos(ctx) if lugar.rasgo("peligro") < 0.5],
                         lambda lugar: lugar.rasgo("novedad") - lugar.rasgo("peligro"))
            if otro is not None:
                return Propuesta(Verbo.MOVER, otro.id, acotar(0.2 + 0.3 * apetito(ctx)), 0.5, "buscar comida en otro sitio", clase=otro.clase)
        return None
