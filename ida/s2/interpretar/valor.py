"""Componente Valor para S2."""

import math

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.pieza import acotar
from ida.nucleo.vocabulario import Relacion
from ida.s2.comun import _recordado
from ida.sistemas_comun import apetito, objetos


class Valor(Componente):
    """Lo que vale cada sujeto para mí (decisión 9), en cuatro dimensiones:
    - **motivacional**: lo que satisface una necesidad actual (nutritivo × apetito, y lo útil según la
      apertura);
    - **potencia**: la fuerza percibida del sujeto (su rasgo de peligro; el cansancio del sujeto no se
      percibe todavía);
    - **sentimental**: la valencia que la memoria asocia a la clase (recuerdos de sus efectos; −0,5 si
      se sabe peligrosa);
    - **social**: 0 mientras no haya varios individuos.
    La valencia se mantiene como combinación de las dimensiones (0,5 · motivacional + 0,5 · sentimental
    + social − potencia · neuroticismo), para las estrategias que ya la leen."""

    tipo = "Valor"
    entradas = ("Sujeto",)

    def reactiva(self, ctx: Contexto) -> None:
        arq, mem = ctx.arquetipo, ctx.memoria
        for o in objetos(ctx):
            motivacional = o.rasgo("nutritivo") * apetito(ctx) + 0.5 * o.rasgo("recurso") * arq.apertura
            potencia = o.rasgo("peligro")
            patron = ctx.onda.ev("Patron").get(o.id)
            recuerdos = patron.carga.get("recuerdos", {}) if patron else {}
            sentimental = math.tanh(sum(recuerdos.values()) / 5.0) if recuerdos else 0.0
            if ctx.perfil.mecanismos.evocacion:   # bloque E, E5: lo recuperado, no la memoria
                peligrosa = (r := _recordado(ctx, o.clase, Relacion.PELIGROSO)) is not None and bool(r.carga.get("demostrada"))
            else:
                peligrosa = mem.demostrada(o.clase, Relacion.PELIGROSO, ctx.latido)
            if peligrosa:
                sentimental -= 0.5
            social = 0.0
            valencia = acotar(0.5 * motivacional + 0.5 * sentimental + social - potencia * arq.neuroticismo, -1.0, 1.0)
            self.percibir(ctx, self.pieza(ctx, o.id, arousal=abs(valencia),
                                          carga={"clase": o.clase, "valencia": round(valencia, 3), "motivacional": round(motivacional, 3),
                                                 "potencia": round(potencia, 3), "sentimental": round(sentimental, 3), "social": social},
                                          entradas=[o.id, "Patron"]))
