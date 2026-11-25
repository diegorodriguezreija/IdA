"""Peticion (D11): las metas instrumentales que las estrategias activas piden al planificador."""

from typing import Any, Dict

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.estrategia import Catalogo
from ida.nucleo.pieza import acotar


class Peticion(Componente):
    """Metas instrumentales (paso 3 de la fase de generalización): lo que piden al planificador las estrategias activas del
    sistema (``Definicion.pedir``), una pieza ``Peticion`` por objeto pedido, con la urgencia del impulso que la origina. El
    planificador de S3 (``PerseguirMetas``), que corre después, las atiende en el mismo latido. Si dos estrategias piden lo
    mismo, queda la cantidad y la urgencia mayores."""

    tipo = "Peticion"

    def __init__(self, catalogo: Catalogo):
        super().__init__("Peticion")
        self.catalogo = catalogo

    def reactiva(self, ctx: Contexto) -> None:
        pedidas: Dict[str, Dict[str, Any]] = {}
        for p in list(ctx.onda.estrategias.values()):
            if p.sistema != self.sistema:
                continue
            definicion = self.catalogo.get(p.carga["nombre"])
            for pet in (definicion.pedir(ctx, p) if definicion is not None else []):
                objeto = str(pet["objeto"])
                previa = pedidas.get(objeto)
                if previa is None or (float(pet["cantidad"]), float(pet["urgencia"])) > (previa["cantidad"], previa["urgencia"]):
                    pedidas[objeto] = {"objeto": objeto, "cantidad": float(pet["cantidad"]), "urgencia": acotar(float(pet["urgencia"])),
                                       "motivo": str(pet.get("motivo", "")), "origen": p.carga["nombre"]}
        for objeto, carga in sorted(pedidas.items()):
            self.registrar(ctx, self.pieza(ctx, f"peticion:{objeto}", arousal=carga["urgencia"], carga=carga))
