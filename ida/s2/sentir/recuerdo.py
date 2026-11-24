"""Componente Recuerdo para S2."""

from typing import Optional

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.pieza import acotar
from ida.nucleo.vocabulario import Afecto, EstadoSaber, Relacion
from ida.sistemas_comun import objetos


class Recuerdo(Componente):
    """Recuperación evocada (bloque E, E5; decisión 22): con la potencia que sobra tras la pasada reactiva,
    las piezas evocadoras traen a la atención lo que la memoria les asocia, como piezas ``Recuerdo``:
    - cada objeto a la vista: si se sabe que su clase hace daño (demostrado);
    - cada impulso que satisface lo nutritivo, con hambre (≥ 0,35): las clases que se creen nutritivas
      (confianza ≥ 0,55) y no se saben peligrosas, con dónde se vieron por última vez.
    Lo recuperado se reconsolida: se refresca y, con búfer diurno, se persiste de noche. ``Valor`` y la
    estrategia ``recordar_comida`` leen estas piezas en lugar de la memoria."""

    tipo = "Recuerdo"
    POTENCIA_MINIMA = 0.25     # fracción de potencia que debe sobrar para recordar
    POTENCIA_REPASO = 0.5      # E6: fracción de potencia que debe sobrar para repasar

    def activa(self, ctx: Contexto) -> None:
        if not (ctx.con_experiencia and ctx.memoria.activa):
            return
        if ctx.perfil.mecanismos.evocacion:
            self._evocar(ctx)
        if ctx.perfil.mecanismos.repaso:
            self._repasar(ctx)

    def _repasar(self, ctx: Contexto) -> None:
        """Repaso en calma (bloque E, E6; decisión 21): en calma, con potencia de sobra y sin recuerdos
        evocados en este latido, trae lo reciente de más fuerza y lo refuerza. Solo en calma, para que
        repasar lo negativo no se convierta en rumiación."""
        onda = ctx.onda
        if ctx.soma.afecto != Afecto.CALMA or onda.ev("Recuerdo"):
            return
        if onda.potencia_max <= 0 or onda.potencia_restante() < self.POTENCIA_REPASO * onda.potencia_max:
            return
        for nodo, clase in ctx.memoria.recientes_para_repaso(ctx.latido):
            if self.percibir(ctx, self.pieza(ctx, f"repaso:{nodo}", arousal=0.2, carga={"clase": clase, "relacion": None,
                                                                                    "demostrada": False, "donde": None, "repaso": True})) is not None:
                ctx.memoria.repasar(nodo, clase, ctx.latido)

    def _evocar(self, ctx: Contexto) -> None:
        onda, mem, ahora = ctx.onda, ctx.memoria, ctx.latido
        if onda.potencia_max <= 0 or onda.potencia_restante() < self.POTENCIA_MINIMA * onda.potencia_max:
            return
        for clase in sorted({o.clase for o in objetos(ctx)}):
            if mem.demostrada(clase, Relacion.PELIGROSO, ahora):
                self._traer(ctx, clase, Relacion.PELIGROSO, None)
        hambre = any(i.carga.get("rasgo") == "nutritivo" and float(i.carga.get("intensidad", 0.0)) > 0.0 for i in onda.ef("Impulso").values())
        if hambre and ctx.soma.hambre() >= 0.35:
            for (clase, rel), prop in list(mem.saber.items()):
                if rel == Relacion.NUTRITIVO and prop.confianza >= 0.55 and not mem.demostrada(clase, Relacion.PELIGROSO, ahora):
                    self._traer(ctx, clase, rel, mem.donde_esta(clase))

    def _traer(self, ctx: Contexto, clase: str, rel: Relacion, donde: Optional[str]) -> None:
        prop = ctx.memoria.proposicion(clase, rel)
        if prop is None:
            return
        arousal = acotar(0.5 * prop.confianza)
        if self.percibir(ctx, self.pieza(ctx, f"{clase}|{rel.name}", arousal=arousal, confianza=prop.confianza,
                                         carga={"clase": clase, "relacion": rel, "demostrada": prop.estado(ctx.latido) == EstadoSaber.DEMOSTRADA,
                                                "donde": donde})) is not None:
            ctx.memoria.reconsolidar((clase, rel), ctx.latido, arousal)
