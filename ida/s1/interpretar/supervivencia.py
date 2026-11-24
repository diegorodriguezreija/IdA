"""Supervivencia: relación de cada Objeto con la supervivencia y alarma general."""

from typing import Dict, Tuple

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.pieza import Pieza, acotar
from ida.nucleo.vocabulario import EstadoSaber, Relacion
from ida.sistemas_comun import apetito, objetos

RECURSO, PELIGRO, NEUTRO = "recurso", "peligro", "neutro"
ENCUENTROS_HABITUACION = 20      # avistamientos sin daño para la familiaridad completa (como en Patron)
HABITUACION_MAX = 0.4            # la amenaza aparente baja hasta un 40 % con la familiaridad
SENSIBILIZACION_MAX = 0.5        # tras un daño, la amenaza sube hasta un 50 % con su confianza


def relacion_supervivencia(ctx: Contexto, o: Pieza, amenaza: float, atractivo: float) -> Tuple[str, float, float]:
    """Clase de relación de un objeto con la supervivencia, su trust y el factor sobre su amenaza
    (decisión 8): habituación y sensibilización.
    - peligro: ya hizo daño (hay hipótesis de daño): trust = su confianza; sensibilización, la amenaza
      sube hasta ``1 + SENSIBILIZACION_MAX``;
    - recurso: se sabe que nutre (confianza ≥ 0,5 y no refutado) o lo parece (atractivo > 0,05);
    - neutro: el resto. Trust = familiaridad (encuentros sin daño): bajo = desconocido, alto =
      habituado; si además parece peligroso, la amenaza baja hasta ``1 − HABITUACION_MAX``.
    Sin experiencia, solo la apariencia: peligro si amenaza > 0,05, recurso si atractivo > 0,05."""
    if not ctx.con_experiencia or not ctx.memoria.activa:
        return (PELIGRO if amenaza > 0.05 else RECURSO if atractivo > 0.05 else NEUTRO), 0.0, 1.0
    mem = ctx.memoria
    dano = mem.proposicion(o.clase, Relacion.PELIGROSO)
    if dano is not None and dano.estado(ctx.latido) != EstadoSaber.REFUTADA:
        return PELIGRO, dano.confianza, 1.0 + SENSIBILIZACION_MAX * dano.confianza
    nutre = mem.proposicion(o.clase, Relacion.NUTRITIVO)
    if (nutre is not None and nutre.confianza >= 0.5 and nutre.estado(ctx.latido) != EstadoSaber.REFUTADA) or atractivo > 0.05:
        return RECURSO, nutre.confianza if nutre is not None else 0.5, 1.0
    familiaridad = min(1.0, mem.clases_vistas.get(o.clase, 0) / ENCUENTROS_HABITUACION)
    return NEUTRO, familiaridad, 1.0 - HABITUACION_MAX * familiaridad


class Supervivencia(Componente):
    """Relación de cada Objeto con la supervivencia. El peligro es graduado por cercanía y por número,
    no un sí o no, y la sensibilidad depende del carácter (neuroticismo)."""

    tipo = "Supervivencia"
    entradas = ("Objeto", "Interocepcion")

    def reactiva(self, ctx: Contexto) -> None:
        sensibilidad = 0.8 + 0.4 * ctx.arquetipo.neuroticismo
        seguro = 1.0
        principal, max_amenaza = None, 0.0
        comida, max_comida = None, 0.0
        clases: Dict[str, Tuple[str, float]] = {}
        for o in objetos(ctx):
            amenaza = acotar(o.rasgo("peligro") * (0.3 + 0.7 * o.rasgo("proximidad")) * sensibilidad)
            atractivo = o.rasgo("nutritivo") * (0.4 + 0.6 * o.rasgo("proximidad"))
            categoria, trust, factor = relacion_supervivencia(ctx, o, amenaza, atractivo)
            amenaza = acotar(amenaza * factor)
            clases[o.clase] = (categoria, round(trust, 3))
            seguro *= (1.0 - amenaza)
            if amenaza > max_amenaza:
                principal, max_amenaza = o, amenaza
            if atractivo > max_comida:
                comida, max_comida = o, atractivo
            if amenaza > 0.05 or atractivo > 0.05:
                self.percibir(ctx, self.pieza(ctx, o.id, arousal=max(amenaza, atractivo * apetito(ctx)),
                                              carga={"clase": o.clase, "amenaza": round(amenaza, 3), "atractivo": round(atractivo, 3),
                                                     "categoria": categoria, "trust": round(trust, 3)},
                                              entradas=[o.id]))
        peligro = 1.0 - seguro
        self.percibir(ctx, self.pieza(
            ctx, "alarma", arousal=max(peligro, 0.9 if ctx.soma.alimentacion <= ctx.soma.HAMBRE_CRITICA else 0.0),
            carga={"peligro": round(peligro, 3), "hambre": round(ctx.soma.hambre(), 3), "cansancio": round(ctx.soma.cansancio(), 3),
                   "amenaza": principal.id if principal else None, "clase_amenaza": principal.clase if principal else None,
                   "comida": comida.id if comida else None, "clases": clases},
            entradas=["Objeto", "Interocepcion"],
        ))
