"""AlimentarseConPrudencia (S1.Reaccionar): estrategia de S1 propia del mundo de archivos."""

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.pieza import Pieza
from ida.s1.reaccionar.estrategias.alimentarse import Alimentarse
from ida.s3.interpretar.proposicion import Relacion
from ida.mundos.archivos.s3.reaccionar.prudencia import _indicios_de_dano


class AlimentarseConPrudencia(Alimentarse):
    """Estrategia de S1 propia del mundo de archivos: alimentarse con prudencia alimentaria. Aquí
    comestibles y tóxicos tienen la misma apariencia y cada mordisco tóxico cuesta 10 de vitalidad,
    así que esperar a que el daño esté demostrado sale caro. Además del criterio genérico (valor y
    lo demostrado), rechaza:
    - las especies con indicios de daño, aunque sean una hipótesis (confianza ≥ 0,35);
    - las especies desconocidas si a la vista hay otra que se sabe que nutre (neofobia).
    Lleva el mismo nombre que la genérica, así que la sustituye en el catálogo de S1 de este mundo.
    """

    nombre = "alimentarse"

    def rechaza(self, ctx: Contexto, o: Pieza) -> bool:
        if super().rechaza(ctx, o) or _indicios_de_dano(ctx, o.clase):
            return True
        conocidas = {p.clase for p in ctx.onda.ev("Exterocepcion").values()
                     if ctx.memoria.demostrada(p.clase, Relacion.NUTRITIVO, ctx.latido)}
        return ctx.memoria.proposicion(o.clase, Relacion.NUTRITIVO) is None and bool(conocidas - {o.clase})
