"""Estrategia Refugiarse para S2."""

from typing import Optional, Tuple

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.estrategia import Definicion, Propuesta
from ida.nucleo.pieza import Pieza, acotar
from ida.nucleo.vocabulario import Verbo
from ida.s2.comun import CANSANCIO, SEGURIDAD, _peligro
from ida.sistemas_comun import lugares


class Refugiarse(Definicion):
    """Cansancio y Seguridad (antes ``Hogar``): el refugio que se valora, el hogar recordado. Volver a
    él con cansancio o peligro (≥ 0,4), por la vista o por la ruta del hipocampo, y descansar allí;
    con mucho cansancio y en calma también se descansa sin hogar (decisión 10)."""

    nombre = "refugiarse"
    impulsos = (CANSANCIO, SEGURIDAD)
    prioridad = 10

    @staticmethod
    def _estado(ctx: Contexto) -> Tuple[float, float, Optional[str], str]:
        hogar = ctx.memoria.hogar() if ctx.perfil.hogar else None
        aqui = ctx.ubicacion()
        return _peligro(ctx), ctx.soma.cansancio(), hogar, aqui

    def _puerta(self, ctx: Contexto) -> Optional[Pieza]:
        peligro, cansancio, hogar, aqui = self._estado(ctx)
        if not (hogar and hogar != aqui and (cansancio >= 0.4 or peligro >= 0.4)):
            return None
        puerta = next((lugar for lugar in lugares(ctx) if lugar.id == hogar), None)
        if puerta is None and ctx.con_experiencia:
            salto = ctx.memoria.ruta(aqui, hogar)
            if salto:
                # El retorno por memoria espacial no debe pisar la huida si el lugar implica peligro
                umbral_p = 0.2 if peligro >= 0.4 else 0.8
                puerta = next((lugar for lugar in lugares(ctx) if lugar.id == salto and lugar.rasgo("peligro") < umbral_p), None)
        return puerta

    def _descansar(self, ctx: Contexto, impulso: str) -> bool:
        peligro, cansancio, hogar, aqui = self._estado(ctx)
        return impulso == CANSANCIO and cansancio >= 0.6 and peligro < 0.3 and (hogar is None or hogar == aqui or cansancio >= 0.85)

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return ctx.perfil.duerme and (self._descansar(ctx, impulso) or self._puerta(ctx) is not None)

    def paso(self, ctx: Contexto, estrategia: Pieza) -> str:
        return "descansar" if self._descansar(ctx, estrategia.carga["impulso"]) else "volver"

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        peligro, cansancio, hogar, aqui = self._estado(ctx)
        if estrategia.carga.get("paso") == "descansar":
            return Propuesta(Verbo.DORMIR, aqui, acotar(0.4 + 0.5 * cansancio), 0.8,
                             "cansancio: dormir" + (" en el hogar" if hogar == aqui else ""))
        puerta = self._puerta(ctx)
        if puerta is None:
            return None
        return Propuesta(Verbo.MOVER, puerta.id, acotar(0.3 + 0.5 * max(cansancio, peligro * 0.7)), 0.7, "volver al hogar", clase=puerta.clase)
