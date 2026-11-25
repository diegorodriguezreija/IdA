"""Actuador: materializa en el mundo la decisión del Tribunal para un verbo concreto."""

from typing import Any, Callable, Dict, List, Optional

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.mundo import Efecto, Motor
from ida.nucleo.pieza import Pieza
from ida.nucleo.vocabulario import Verbo


class Actuador(Componente):
    """Materializa en el mundo la decisión del Tribunal para un verbo concreto.

    Si el mundo tiene primitivas y el cuerpo tiene Motor (D9), el Motor traduce la decisión a primitivas al ejecutarla;
    sin primitivas (precondición no cumplida) no se toca el mundo. El éxito lo juzga el Motor con lo medido en bruto.
    Si no, el mundo ejecuta el verbo."""

    tipo = "Accion"

    def __init__(self, verbo: Verbo, ejecutar: Callable[[Verbo, str, Dict[str, Any]], Efecto], motor: Optional[Motor] = None,
                 ejecutar_primitivas: Optional[Callable[[List[str]], Efecto]] = None,
                 disponibles: Optional[List[str]] = None):
        super().__init__(f"Actuador_{verbo.value}")
        self.verbo = verbo
        self._ejecutar = ejecutar
        self._motor = motor
        self._ejecutar_primitivas = ejecutar_primitivas
        self._disponibles = list(disponibles or [])

    def reactiva(self, ctx: Contexto) -> None:
        d = ctx.extra.get("decision")
        if d is None:
            return
        verbo = d.carga["verbo"]
        # ACECHAR y LEER no se ejecutan en el mundo: si el mundo admite ESPERAR, lo hace su actuador.
        if verbo in (Verbo.ACECHAR, Verbo.LEER) and self.verbo == Verbo.ESPERAR:
            verbo = Verbo.ESPERAR
        if verbo != self.verbo:
            return
        if self._motor is None or self._ejecutar_primitivas is None:
            efecto = self._ejecutar(verbo, d.carga["objetivo"], d.carga.get("datos", {}))
            aplicar_efecto(ctx, verbo, d, efecto)
            return
        primitivas = self._motor.primitivas(d, ctx, self._disponibles)
        efecto = self._ejecutar_primitivas(primitivas) if primitivas else Efecto(exito=False)
        self._motor.contar(primitivas)    # copia eferente
        efecto.exito = self._motor.juzgar(d, primitivas, efecto)
        aplicar_efecto(ctx, verbo, d, efecto, primitivas)


def aplicar_efecto(ctx: Contexto, verbo: Verbo, decision: Pieza, efecto: Efecto, primitivas: Optional[List[str]] = None) -> None:
    """Aplica el efecto al soma y registra la pieza ``Accion`` ejecutada (con sus primitivas, si las hubo: D9)."""
    soma = ctx.soma
    soma.aplicar(efecto.delta)
    if efecto.exito:
        if verbo == Verbo.DORMIR:
            soma.dormido = True
        elif verbo == Verbo.COGER:
            soma.cargando = efecto.obtenido or decision.carga.get("clase") or decision.carga["objetivo"]
        elif verbo == Verbo.SOLTAR:
            soma.cargando = None
    if efecto.muerte:
        soma.vitalidad = 0.0
    ctx.extra["efecto"] = efecto
    ej = Pieza(
        id="Accion",
        tipo="Accion",
        arousal=decision.arousal,
        confianza=decision.confianza,
        carga={
            "verbo": decision.carga["verbo"],
            "objetivo": decision.carga["objetivo"],
            "clase": decision.carga.get("clase", ""),
            "sistema": decision.carga.get("sistema", ""),
            "motivo": decision.carga.get("motivo", ""),
            "origen": dict(decision.carga.get("origen", {})),
            "exito": efecto.exito,
            "delta": dict(efecto.delta),
            "causa": efecto.causa,
            "obtenido": efecto.obtenido,
            "mensaje": efecto.mensaje,
            **({"primitivas": list(primitivas)} if primitivas is not None else {}),
        },
        entradas=["decision"],
        sistema="CORE",
        creada=ctx.latido,
        actualizada=ctx.latido,
    )
    ctx.onda.registrar("Accion", ej)
