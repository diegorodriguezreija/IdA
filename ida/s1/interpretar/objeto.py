"""Objeto: distingue los cuerpos dentro de la Imagen."""

from ida.nucleo.arquitectura import Componente, Contexto
from ida.s1.sentir.imagen import _cosas
from ida.sistemas.piezas import MAX_OBJETOS


class Objeto(Componente):
    """Distingue los cuerpos dentro de la Imagen: solo los más salientes (7 ± 2) pasan a la atención
    como piezas ``Objeto``, cada una con coste 1."""

    tipo = "Objeto"
    entradas = ("Imagen",)

    def reactiva(self, ctx: Contexto) -> None:
        conceptos = ctx.perfil.mecanismos.conceptos and ctx.con_experiencia and ctx.memoria.activa
        for p in _cosas(ctx)[:MAX_OBJETOS]:
            self.percibir(ctx, self.pieza(ctx, p.id, arousal=p.arousal, confianza=p.confianza,
                                          carga={"clase": p.clase, "rasgos": dict(p.carga["rasgos"])},
                                          entradas=[p.id]))
            if conceptos:   # bloque E, E3: la instancia actualiza el concepto de su clase (decisión 20)
                ctx.memoria.instancia(p.id, p.clase, p.carga["rasgos"], ctx.latido)
