"""Reflejo: detección de cambios bruscos de peligro."""

from ida.nucleo.arquitectura import Componente, Contexto
from ida.sistemas.piezas import alarma


class Reflejo(Componente):
    """Detecta un cambio brusco del Sentir (decisión 6): si el peligro sube de golpe respecto al latido
    anterior al menos el umbral del reflejo, registra un sobresalto. La respuesta es la estrategia
    refleja de S1, de duración fija y prioridad máxima.

    El umbral escala con el carácter: ``Perfil.umbral_reflejo`` vale para un ``umbral_miedo`` de
    referencia (0,6, el del arquetipo por defecto) y se multiplica por ``umbral_miedo / 0,6``. Un
    individuo valiente necesita un salto mayor para sobresaltarse; uno reactivo, menor.
    """

    tipo = "Reflejo"
    entradas = ("Supervivencia",)
    UMBRAL_MIEDO_REFERENCIA = 0.6

    def umbral(self, ctx: Contexto) -> float:
        return min(1.0, ctx.perfil.umbral_reflejo * ctx.arquetipo.umbral_miedo / self.UMBRAL_MIEDO_REFERENCIA)

    def reactiva(self, ctx: Contexto) -> None:
        a = alarma(ctx)
        if a is None:
            return
        previa = ctx.onda.ei("Supervivencia").get("alarma")
        antes = float(previa.carga["peligro"]) if previa is not None else 0.0
        salto = float(a.carga["peligro"]) - antes
        if salto >= self.umbral(ctx):
            self.registrar(ctx, self.pieza(ctx, "sobresalto", arousal=1.0,
                                           carga={"salto": round(salto, 3), "peligro": a.carga["peligro"], "de": a.carga["clase_amenaza"]}))
