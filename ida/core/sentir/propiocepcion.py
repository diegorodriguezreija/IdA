"""Propiocepcion: la pieza «yo»: ubicación, si carga algo, inventario y cuerpo."""

from typing import Any, Dict

from ida.nucleo.arquitectura import Componente, Contexto


class Propiocepcion(Componente):
    """La pieza «yo»: ubicación, si carga algo, inventario (solo si el mundo lo tiene: sin la clave, el mundo no tiene
    inventario) y cuerpo."""

    tipo = "Propiocepcion"

    def reactiva(self, ctx: Contexto) -> None:
        obs = ctx.observacion
        carga: Dict[str, Any] = {"ubicacion": obs.ubicacion if obs else "", "cargando": ctx.soma.cargando}
        if obs is not None and obs.inventario is not None:
            carga["inventario"] = dict(obs.inventario)
        carga["cuerpo"] = dict(obs.cuerpo or {}) if obs else {}
        self.percibir(ctx, self.pieza(ctx, "yo", arousal=0.1, carga=carga))
