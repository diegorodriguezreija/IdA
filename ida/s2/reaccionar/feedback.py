"""Componente Feedback para S2."""

from ida.nucleo.arquitectura import Componente, Contexto, expectativa_ejecutada
from ida.sistemas_comun import PESO_PREDICCION


class Feedback(Componente):
    """Feedback de S2 (decisión 5): mejora del placer y bajada del estrés respecto al latido anterior,
    (Δ placer) / 100 − Δ estrés. Positivo = mejora. Es el mérito de las estrategias de S2, sea cual
    sea el impulso al que sirven (S2 juzga con su criterio, el valor)."""

    tipo = "Feedback"

    def reactiva(self, ctx: Contexto) -> None:
        placer, estres = float(ctx.soma.placer), float(ctx.soma.estres)
        previo = ctx.onda.ei("Feedback").get(f"feedback:{self.sistema}")
        antes = previo.carga["estado"] if previo is not None else {"placer": placer, "estres": estres}
        valor = round((placer - antes["placer"]) / 100.0 - (estres - antes["estres"]), 4)
        e = expectativa_ejecutada(ctx.onda, self.sistema) if ctx.perfil.mecanismos.expectativa else None
        if e is not None and "valencia" in e.carga["esperado"]:
            # Bloque F, F1: error de predicción con signo sobre la valencia esperada.
            b = e.carga["base"]
            obtenida = (placer / 100.0 - float(b.get("placer", placer / 100.0))) - (estres - float(b.get("estres", estres)))
            valor = round(valor + PESO_PREDICCION * (obtenida - float(e.carga["esperado"]["valencia"])), 4)
        impulsos = {**ctx.onda.ef("Impulso"), **ctx.onda.ef("Intencion")}
        self.registrar(ctx, self.pieza(ctx, f"feedback:{self.sistema}", arousal=0.0,
                                       carga={"valor": valor, "por_impulso": dict.fromkeys(impulsos, valor),
                                              "estado": {"placer": placer, "estres": estres}}))
