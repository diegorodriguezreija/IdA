"""Componente Emocion para S2."""

from ida.nucleo.arquitectura import Componente, Contexto


class Emocion(Componente):
    """Estado afectivo interno sentido por el individuo, tal como lo calcula ``Soma``.

    Se registra en ``ef`` a coste cero: no entra en ``ev``, así que no cambia la tensión ni la
    apertura de episodios, que leen todos los canales de ``ev``.
    """

    tipo = "Emocion"
    entradas = ("Interocepcion", "Patron")

    def reactiva(self, ctx: Contexto) -> None:
        self.registrar(ctx, self.pieza(ctx, "emocion", arousal=ctx.soma.estres,
                                       carga={"valencia": round(ctx.soma.valencia, 3), "afecto": ctx.soma.afecto.value,
                                              "placer": round(ctx.soma.placer, 1)},
                                       entradas=["Interocepcion", "Patron"]))
