"""Componente Sentencia para S3."""

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.vocabulario import EstadoSaber, Relacion
from ida.sistemas_comun import al_alcance, apetito, objetos


class Sentencia(Componente):
    """Encadena proposiciones demostradas con la situación: «si <clase> está cerca y <condición>, <conclusión>»."""

    tipo = "Sentencia"
    entradas = ("Proposicion",)

    def reactiva(self, ctx: Contexto) -> None:
        props = {(p.carga["clase"], p.carga["relacion"]): p for p in ctx.onda.ev("Proposicion").values()
                 if p.carga["estado"] == EstadoSaber.DEMOSTRADA}
        for o in objetos(ctx):
            cerca = o.rasgo("proximidad") >= 0.5
            if (o.clase, Relacion.PELIGROSO) in props and cerca:
                self._sentencia(ctx, o, "EVITAR", f"si {o.clase} está cerca, hace daño → evitarlo", props[(o.clase, Relacion.PELIGROSO)])
            if (o.clase, Relacion.NUTRITIVO) in props and apetito(ctx) >= 0.4:
                self._sentencia(ctx, o, "COMER", f"si tengo hambre y hay {o.clase}, me alimenta → comerlo", props[(o.clase, Relacion.NUTRITIVO)])
            if (o.clase, Relacion.UTIL) in props and ctx.soma.cargando is None and al_alcance(o):
                self._sentencia(ctx, o, "COGER", f"{o.clase} sirve para algo → cogerlo", props[(o.clase, Relacion.UTIL)])

    def _sentencia(self, ctx, o, conclusion, texto, base) -> None:
        self.percibir(ctx, self.pieza(ctx, f"{conclusion}:{o.id}", arousal=0.6, confianza=base.confianza,
                                      carga={"objetivo": o.id, "clase": o.clase, "conclusion": conclusion, "texto": texto},
                                      entradas=[base.id]))
