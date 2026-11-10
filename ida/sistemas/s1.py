"""S1 · Supervivencia: cuerpo, peligro, reflejos e impulsos básicos. Rápido, simple y siempre primero.

| Etapa       | Componente     | Produce |
|-------------|----------------|---------|
| Sentir      | Imagen         | Imagen (gestalt del instante) y Objeto (lo que entra en la atención) |
| Interpretar | Supervivencia  | Supervivencia por objeto (peligro graduado) y una alarma global |
| Reaccionar  | Reflejo        | Reflejo (huir o defenderse) y su candidato de Ejecución |
| Reaccionar  | ImpulsoS1      | Impulso (comer, acercarse a la comida) y su candidato de Ejecución |
"""

from ida.core.arquitectura import Componente, Contexto, Modulo, Sistema
from ida.core.pieza import acotar
from ida.core.vocabulario import Verbo
from ida.sistemas.comun import MAX_OBJETOS, al_alcance, alarma, apetito, escena, lugares, mejor, objetos


class Imagen(Componente):
    """Integra Escena, Interocepción y el resultado de la acción anterior en una representación del instante.

    Solo los objetos más salientes (7 ± 2) pasan a la atención como piezas ``Objeto``.
    """

    tipo = "Imagen"
    entradas = ("Escena", "Interocepcion")

    def reactiva(self, ctx: Contexto) -> None:
        cosas = [p for p in escena(ctx) if p.rasgo("lugar") < 0.5]
        cosas.sort(key=lambda p: -p.arousal)
        foco = cosas[0] if cosas else None
        previa = ctx.onda.ei("Ejecucion").get("Ejecucion")
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
            entradas=["Escena", "Interocepcion", "Ejecucion"],
        ))
        for p in cosas[:MAX_OBJETOS]:
            self.percibir(ctx, self.pieza(ctx, p.id, arousal=p.arousal, confianza=p.confianza,
                                          carga={"clase": p.clase, "rasgos": dict(p.carga["rasgos"])},
                                          entradas=[p.id], tipo="Objeto"))


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
        for o in objetos(ctx):
            amenaza = acotar(o.rasgo("peligro") * (0.3 + 0.7 * o.rasgo("proximidad")) * sensibilidad)
            atractivo = o.rasgo("nutritivo") * (0.4 + 0.6 * o.rasgo("proximidad"))
            seguro *= (1.0 - amenaza)
            if amenaza > max_amenaza:
                principal, max_amenaza = o, amenaza
            if atractivo > max_comida:
                comida, max_comida = o, atractivo
            if amenaza > 0.05 or atractivo > 0.05:
                self.percibir(ctx, self.pieza(ctx, o.id, arousal=max(amenaza, atractivo * apetito(ctx)),
                                              carga={"clase": o.clase, "amenaza": round(amenaza, 3), "atractivo": round(atractivo, 3)},
                                              entradas=[o.id]))
        peligro = 1.0 - seguro
        self.percibir(ctx, self.pieza(
            ctx, "alarma", arousal=max(peligro, 0.9 if ctx.soma.alimentacion <= ctx.soma.HAMBRE_CRITICA else 0.0),
            carga={"peligro": round(peligro, 3), "hambre": round(ctx.soma.hambre(), 3), "cansancio": round(ctx.soma.cansancio(), 3),
                   "amenaza": principal.id if principal else None, "clase_amenaza": principal.clase if principal else None,
                   "comida": comida.id if comida else None},
            entradas=["Objeto", "Interocepcion"],
        ))


class Reflejo(Componente):
    """Ante peligro por encima del umbral de miedo: huir al lugar más seguro, o defenderse si no hay salida."""

    tipo = "Reflejo"
    entradas = ("Supervivencia",)

    def reactiva(self, ctx: Contexto) -> None:
        a = alarma(ctx)
        if a is None or a.carga["peligro"] < ctx.arquetipo.umbral_miedo:
            return
        amenaza = ctx.onda.ev("Objeto").get(a.carga["amenaza"])
        salida = mejor(lugares(ctx), lambda l: -l.rasgo("peligro"))
        urgencia = acotar(0.75 + 0.25 * a.carga["peligro"])
        if salida is not None and salida.rasgo("peligro") < a.carga["peligro"]:
            self.registrar(ctx, self.pieza(ctx, "huir", arousal=urgencia, carga={"de": a.carga["clase_amenaza"], "a": salida.id}))
            self.proponer(ctx, Verbo.MOVER, salida.id, urgencia, 0.85, f"reflejo: huir de {a.carga['clase_amenaza']}", clase=salida.clase)
        elif amenaza is not None and al_alcance(amenaza):
            self.registrar(ctx, self.pieza(ctx, "defenderse", arousal=urgencia, carga={"de": amenaza.clase}))
            self.proponer(ctx, Verbo.ATACAR, amenaza.id, urgencia, 0.7, f"reflejo: defenderse de {amenaza.clase}", clase=amenaza.clase)


class ImpulsoS1(Componente):
    """Impulsos básicos: comer lo que está al alcance y acercarse a la comida."""

    tipo = "Impulso"
    entradas = ("Supervivencia",)

    def reactiva(self, ctx: Contexto) -> None:
        ganas = apetito(ctx)
        comestibles = [o for o in objetos(ctx) if o.rasgo("nutritivo") >= 0.3]
        cerca = mejor([o for o in comestibles if al_alcance(o)], lambda o: o.rasgo("nutritivo") - o.rasgo("peligro"))
        if cerca is not None and ctx.soma.alimentacion < 95.0:
            ar = acotar(0.35 + 0.6 * ganas)
            self.registrar(ctx, self.pieza(ctx, "comer", arousal=ar, carga={"clase": cerca.clase}))
            self.proponer(ctx, Verbo.COMER, cerca.id, ar, 0.7, f"impulso: comer {cerca.clase}", clase=cerca.clase)
        destino = mejor(lugares(ctx), lambda l: l.rasgo("nutritivo") - 1.5 * l.rasgo("peligro"))
        if destino is not None and destino.rasgo("nutritivo") > 0.0 and destino.rasgo("peligro") < 0.8:
            ar = acotar(0.25 + 0.6 * ganas * destino.rasgo("nutritivo"))
            self.proponer(ctx, Verbo.MOVER, destino.id, ar, 0.6, "impulso: acercarse a la comida", clase=destino.clase)
        if not ctx.onda.acc("Ejecucion") and Verbo.ESPERAR not in ctx.verbos and destino is not None:
            # El mundo no deja esperar y nadie propone nada: el mal menor.
            self.proponer(ctx, Verbo.MOVER, destino.id, 0.3, 0.5, "sin opción mejor: el mal menor", clase=destino.clase)


def crear_s1() -> Sistema:
    return Sistema("S1", "Supervivencia", [
        Modulo("Sentir", [Imagen()]),
        Modulo("Interpretar", [Supervivencia()]),
        Modulo("Reaccionar", [Reflejo(), ImpulsoS1()]),
    ])
