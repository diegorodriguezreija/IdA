"""Componente Creencia para S3."""

from typing import Dict, Optional

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.pieza import Pieza
from ida.nucleo.vocabulario import EstadoSaber, Relacion
from ida.sistemas_comun import objetos

PESO_AFECTIVO = 0.1    # peso de la fuente afectiva frente a la confianza por experiencia y autoridad


class Creencia(Componente):
    """Lo que el individuo sostiene como cierto (decisión 12), con su trust y sus fuentes. Cierra el
    círculo de S3·Interpretar: representar, generar, consolidar. Una creencia por cada proposición de
    la memoria (en ``ef``, sin coste: es estado, no atención).
    - **sostiene**: la proposición está demostrada; **estado**: hipótesis, demostrada o refutada.
    - **fuentes**: experiencia (``c_exp``), autoridad (``c_aut``, si la hay), herencia (si viene del
      linaje) y afectiva: la valencia que S2 da ahora a la clase (negativa para «hace daño», positiva
      para «nutre»), con poco peso (``PESO_AFECTIVO``) y refutable: solo ajusta el trust.
    - **trust**: (confianza por fuentes + PESO_AFECTIVO × afectiva) / (1 + PESO_AFECTIVO).
    """

    tipo = "Creencia"
    MAX_CREENCIAS = 64   # bloque E: la emisión queda acotada aunque la memoria crezca

    def reactiva(self, ctx: Contexto) -> None:
        if not ctx.con_experiencia:
            return
        valencias: Dict[str, float] = {}
        for pv in ctx.onda.ev("Valor").values():
            valencias.setdefault(str(pv.carga.get("clase", "")), float(pv.carga.get("valencia", 0.0)))
        saber = list(ctx.memoria.saber.items())
        if len(saber) > self.MAX_CREENCIAS:
            # Por encima del tope: primero lo que está a la vista o recordado, luego lo de más confianza;
            # se conserva el orden original entre lo elegido.
            presentes = {o.clase for o in objetos(ctx)} | {str(r.carga.get("clase", "")) for r in ctx.onda.ev("Recuerdo").values()}
            orden = sorted(range(len(saber)), key=lambda i: (saber[i][0][0] not in presentes, -saber[i][1].confianza, i))
            elegidos = set(orden[: self.MAX_CREENCIAS])
            saber = [x for i, x in enumerate(saber) if i in elegidos]
        for (clase, rel), p in saber:
            v = valencias.get(clase, 0.0)
            afectiva = max(0.0, -v) if rel == Relacion.PELIGROSO else max(0.0, v) if rel == Relacion.NUTRITIVO else 0.0
            estado = p.estado(ctx.latido)
            trust = (p.confianza + PESO_AFECTIVO * afectiva) / (1.0 + PESO_AFECTIVO)
            self.registrar(ctx, self.pieza(ctx, f"{clase}|{rel.name}", arousal=trust, confianza=trust, carga={
                "clase": clase, "relacion": rel, "estado": estado, "sostiene": estado == EstadoSaber.DEMOSTRADA, "trust": round(trust, 3),
                "fuentes": {"experiencia": round(p.c_exp, 3), "autoridad": p.c_aut, "herencia": p.heredada, "afectiva": round(afectiva, 3)}}))


def creencia(fuente: Dict[str, Pieza], clase: str, rel: Relacion) -> Optional[Pieza]:
    return fuente.get(f"{clase}|{rel.name}")
