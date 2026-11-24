"""Feedback: retroalimentación de supervivencia sobre déficits y peligro."""

from ida.nucleo.arquitectura import Componente, Contexto, expectativa_ejecutada
from ida.s1.comun import deficits
from ida.sistemas_comun import PESO_PREDICCION


class Feedback(Componente):
    """Feedback de S1 (decisión 5): cuánto bajan los déficits del cuerpo y el peligro respecto al latido
    anterior. Positivo = mejora. Es la señal de mérito de las estrategias de S1."""

    tipo = "Feedback"

    def reactiva(self, ctx: Contexto) -> None:
        ahora = deficits(ctx)
        previo = ctx.onda.ei("Feedback").get(f"feedback:{self.sistema}")
        antes = previo.carga["deficits"] if previo is not None else ahora
        cambios = {k: round(antes.get(k, v) - v, 4) for k, v in ahora.items()}
        e = expectativa_ejecutada(ctx.onda, self.sistema) if ctx.perfil.mecanismos.expectativa else None
        if e is not None and e.carga["esperado"]:
            # Bloque F, F1: error de predicción con signo (mejor de lo esperado = positivo) por necesidad.
            for k, base in e.carga["base"].items():
                if k in ahora and k in e.carga["esperado"]:
                    rpe = float(e.carga["esperado"][k]) - (ahora[k] - float(base))
                    cambios[k] = round(cambios.get(k, 0.0) + PESO_PREDICCION * rpe, 4)
        self.registrar(ctx, self.pieza(ctx, f"feedback:{self.sistema}", arousal=0.0,
                                       carga={"valor": round(sum(cambios.values()), 4), "por_impulso": cambios, "deficits": ahora}))
