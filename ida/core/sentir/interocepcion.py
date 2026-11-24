"""Interocepcion: una pieza por constante vital, con su variación respecto al latido anterior."""

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.soma import VITALES


class Interocepcion(Componente):
    tipo = "Interocepcion"

    def reactiva(self, ctx: Contexto) -> None:
        previo = ctx.onda.ei("Interocepcion")
        valores = {nombre: float(getattr(ctx.soma, nombre)) for nombre in VITALES}
        if ctx.observacion is not None and ctx.observacion.vitales:
            valores.update({k: float(v) for k, v in ctx.observacion.vitales.items() if k not in valores})
        for nombre, valor in valores.items():
            antes = float(previo[nombre].carga["valor"]) if nombre in previo else valor
            p = self.pieza(ctx, nombre, arousal=(100.0 - valor) / 100.0, carga={"valor": round(valor, 2), "delta": round(valor - antes, 2)})
            self.percibir(ctx, p)
