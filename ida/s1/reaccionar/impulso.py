"""Impulso: impulsos por necesidad declarada y Seguridad."""

from ida.nucleo.arquitectura import Componente, Contexto
from ida.s1.comun import alostasis, deficits


class Impulso(Componente):
    """Un impulso por necesidad que declara el mundo (su déficit es la intensidad cruda) y Seguridad
    (el peligro). No proponen acciones: lo hacen las estrategias (decisiones 2 y 3).

    **Alostasis** (paso 3, ``docs/ENCARGO_PASO3_PROTEGER.md``, 3.2): regulación por anticipación. Solo para el cobijo,
    la intensidad es la del déficit previsto: ``max(déficit, déficit + tendencia · T)``, con la tendencia
    como media móvil del cambio del déficit por latido. Sin tendencia que suba, o sin déficit (saciedad: lo lleno no se llena
    más), la intensidad es el déficit. El horizonte T sale del recinto (``alostasis``). Las demás necesidades no se anticipan."""

    tipo = "Impulso"
    entradas = ("Supervivencia",)

    def reactiva(self, ctx: Contexto) -> None:
        rasgos = {n.nombre: n.rasgo for n in ctx.perfil.necesidades}
        defs = deficits(ctx)
        for nombre, (intensidad, tendencia, horizonte) in alostasis(ctx, defs).items():
            self.registrar(ctx, self.pieza(ctx, nombre, arousal=intensidad, carga={
                "intensidad": round(intensidad, 4), "objetivo": 0.0, "rasgo": rasgos.get(nombre), "deficit": round(defs[nombre], 4),
                "tendencia": round(tendencia, 6), "horizonte": round(horizonte, 2)}))
