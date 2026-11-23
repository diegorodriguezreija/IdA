"""Saliencia (D5): preatención general de S1 · Sentir.

``Exterocepcion`` (Core · Sentir) emite cada entidad en bruto, con arousal 0. La saliencia ascendente se calcula
aquí, antes del cuello de botella de la atención y sin pagarla (como el colículo superior): a cada pieza
``Exterocepcion`` le pone de arousal lo más saliente de sus rasgos, con la fórmula que antes estaba en el sensor:

    saliencia = max(peligro · max(proximidad, 0,3), nutritivo · proximidad, 0,4 · novedad)

Corre después de ``Amenaza``, que es quien escribe el ``peligro`` aprendido. Coste lineal en lo percibido.
"""

from ida.core.arquitectura import Componente, Contexto


class Saliencia(Componente):
    tipo = "Exterocepcion"
    preatentivo = True

    def reactiva(self, ctx: Contexto) -> None:
        for p in ctx.onda.ev("Exterocepcion").values():
            r = p.carga.get("rasgos", {})
            cerca = r.get("proximidad", 0.0)
            saliencia = max(r.get("peligro", 0.0) * max(cerca, 0.3), r.get("nutritivo", 0.0) * cerca, 0.4 * r.get("novedad", 0.0))
            self.modificar(ctx, p, arousal=saliencia)
