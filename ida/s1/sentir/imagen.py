"""Imagen: integra Exterocepcion, Interocepción y el resultado de la acción anterior en una representación del instante."""

from ida.nucleo.arquitectura import Componente, Contexto
from ida.sistemas.piezas import exterocepcion, lugares


def _cosas(ctx: Contexto) -> list:
    """Lo percibido que no es un lugar, de más a menos saliente (orden estable)."""
    cosas = [p for p in exterocepcion(ctx) if p.rasgo("lugar") < 0.5]
    cosas.sort(key=lambda p: -p.arousal)
    return cosas


class Imagen(Componente):
    """Integra Exterocepcion, Interocepción y el resultado de la acción anterior en una representación del instante."""

    tipo = "Imagen"
    entradas = ("Exterocepcion", "Interocepcion")

    def reactiva(self, ctx: Contexto) -> None:
        cosas = _cosas(ctx)
        foco = cosas[0] if cosas else None
        previa = ctx.onda.ei("Accion").get("Accion")
        agencia = ""
        if previa is not None:
            d = previa.carga.get("delta", {})
            agencia = f"{previa.carga['verbo'].value} {previa.carga.get('clase') or previa.carga['objetivo']} → " + (
                ", ".join(f"{k} {v:+.1f}" for k, v in d.items() if v) or "sin cambios"
            )
        self.percibir(ctx, self.pieza(
            ctx, f"imagen_{ctx.latido}", arousal=foco.arousal if foco else 0.1,
            carga={"foco": foco.id if foco else None, "clase_foco": foco.clase if foco else None,
                   "n_cosas": len(cosas), "n_lugares": len(lugares(ctx)), "agencia": agencia},
            entradas=["Exterocepcion", "Interocepcion", "Accion"],
        ))
