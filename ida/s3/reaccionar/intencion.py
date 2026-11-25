"""Componente Intencion para S3."""

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.vocabulario import EstadoSaber
from ida.s3.comun import INTENSIDAD_INTENCION_DEL_MUNDO, SABER
from ida.sistemas.piezas import objetos


class Intencion(Componente):
    """El «qué» deliberado de S3 (decisión 11), frente al impulso, que surge:
    - **saber**: reducir la incertidumbre; intensidad = fracción de lo que se sabe de las clases a la
      vista que aún es hipótesis (0 si no se sabe nada de ellas);
    - las que declara el mundo (``Perfil.intenciones``), con intensidad fija: son metas sostenidas, no
      necesidades que se sacian.
    """

    tipo = "Intencion"

    def reactiva(self, ctx: Contexto) -> None:
        clases = {o.clase for o in objetos(ctx)}
        props = [p for (clase, _), p in ctx.memoria.saber.items() if clase in clases] if ctx.con_experiencia else []
        saber = sum(1 for p in props if p.estado(ctx.latido) == EstadoSaber.HIPOTESIS) / len(props) if props else 0.0
        intenciones = {SABER: saber, **dict.fromkeys(ctx.perfil.intenciones, INTENSIDAD_INTENCION_DEL_MUNDO)}
        for nombre, intensidad in intenciones.items():
            self.registrar(ctx, self.pieza(ctx, nombre, arousal=intensidad,
                                           carga={"intensidad": round(intensidad, 4), "objetivo": 0.0, "rasgo": None}))
