"""Componente Feedback para S3."""

from ida.nucleo.arquitectura import Componente, Contexto


class Feedback(Componente):
    """Feedback de S3 (decisión 5): baja del error de predicción respecto al latido anterior,
    Δ aciertos − Δ sorpresas de las expectativas de la memoria. Positivo = predice mejor. Es el
    mérito de las estrategias de S3, sea cual sea el impulso o la intención a los que sirven."""

    tipo = "Feedback"

    def reactiva(self, ctx: Contexto) -> None:
        aciertos, fallos = int(ctx.memoria.aciertos), int(ctx.memoria.fallos)
        previo = ctx.onda.ei("Feedback").get(f"feedback:{self.sistema}")
        antes = previo.carga["estado"] if previo is not None else {"aciertos": aciertos, "fallos": fallos}
        valor = float((aciertos - antes["aciertos"]) - (fallos - antes["fallos"]))
        impulsos = {**ctx.onda.ef("Impulso"), **ctx.onda.ef("Intencion")}
        self.registrar(ctx, self.pieza(ctx, f"feedback:{self.sistema}", arousal=0.0,
                                       carga={"valor": valor, "por_impulso": dict.fromkeys(impulsos, valor),
                                              "estado": {"aciertos": aciertos, "fallos": fallos}}))
