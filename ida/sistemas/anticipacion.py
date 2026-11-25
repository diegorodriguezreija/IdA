"""Anticipacion (D11): la expectativa de cada sistema, como copia eferente de su propuesta."""

from typing import Tuple

from ida.nucleo.arquitectura import SIN_EXPECTATIVA, Componente, Contexto, variables_proactivas

PESO_PREDICCION = 0.5   # bloque F, F1: peso del error de predicción con signo en el feedback de S1 y S2


class Anticipacion(Componente):
    """Expectativa (bloque F, F1; decisión 24). En el barrido proactivo, con la potencia que sobra, deja
    en ``ef`` lo que el sistema espera del latido siguiente si se ejecuta su propuesta de mayor arousal:
    el cambio de sus ``variables`` según la memoria (lo vivido, el concepto parecido o el grafo). Lleva
    la base para que el Core y el feedback midan el cambio real. Sin expectativa previa queda vacía
    (``esperado`` = {}) y sirve para aprender la transición."""

    tipo = "Expectativa"
    POTENCIA_MINIMA = 0.25

    def __init__(self, variables: Tuple[str, ...] = ()):
        super().__init__("Anticipacion")
        self.variables = variables      # vacío = las necesidades del mundo

    def proactiva(self, ctx: Contexto) -> None:
        if not (ctx.perfil.mecanismos.expectativa and ctx.con_experiencia and ctx.memoria.activa):
            return
        onda = ctx.onda
        if onda.potencia_max <= 0 or onda.potencia_restante() < self.POTENCIA_MINIMA * onda.potencia_max:
            return
        propias = [p for p in onda.acc("Accion").values() if p.sistema == self.sistema and p.carga["verbo"] not in SIN_EXPECTATIVA
                   and p.carga.get("clase")]
        if not propias:
            return
        p = max(propias, key=lambda q: (q.arousal, q.id))
        verbo, clase = p.carga["verbo"], str(p.carga["clase"])
        todas = variables_proactivas(onda, ctx.soma, ctx.perfil)
        nombres = self.variables or tuple(n.nombre for n in ctx.perfil.necesidades)
        esperado = ctx.memoria.esperar(self.sistema, verbo.value, clase)
        self.registrar(ctx, self.pieza(ctx, f"expectativa:{self.sistema}", arousal=0.0, carga={
            "verbo": verbo, "objetivo": p.carga["objetivo"], "clase": clase, "base": {k: todas[k] for k in nombres if k in todas},
            "esperado": dict(esperado[0]) if esperado else {}, "fuente": esperado[1] if esperado else None}))
