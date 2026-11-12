"""S2 · Valor: motivación, sentimiento y relación social. Trabaja con lo que le sobra a S1.

| Etapa       | Componente       | Produce |
|-------------|------------------|---------|
| Sentir      | Patron           | Patrón: qué clase de cosa es y qué recuerda de ella |
| Interpretar | Sujeto           | Sujeto (mismo id que el Objeto) |
| Interpretar | Valor            | Valor: motivación, sentimiento y social de cada sujeto |
| Reaccionar  | Exteriorizacion  | Exteriorización del estado afectivo (en ``ef``, sin coste) |
| Reaccionar  | ImpulsoS2        | Modula los candidatos existentes según el valor de su objetivo |
| Reaccionar  | Curiosidad       | Candidato de explorar lo nuevo, que solo gana si nada urge |
| Reaccionar  | Hogar            | Recordar dónde se estuvo bien, volver y descansar allí |
| Reaccionar  | Orientacion      | Usar el mapa espacial para navegar hacia recursos nutritivos recordados |
"""

import math

from ida.core.arquitectura import Componente, Contexto, Modulo, Sistema
from ida.core.pieza import Pieza, acotar
from ida.core.vocabulario import Relacion, Verbo
from ida.sistemas.comun import al_alcance, alarma, apetito, lugares, mejor, objetos


class Patron(Componente):
    tipo = "Patron"
    entradas = ("Objeto",)

    def reactiva(self, ctx: Contexto) -> None:
        for o in objetos(ctx):
            vistos = ctx.memoria.clases_vistas.get(o.clase, 0)
            self.percibir(ctx, self.pieza(ctx, o.id, arousal=o.arousal * 0.8,
                                          carga={"clase": o.clase, "familiaridad": round(min(1.0, vistos / 20.0), 3)},
                                          entradas=[o.id]))

    def activa(self, ctx: Contexto) -> None:
        """Dimensión activa: recupera lo que la experiencia dice de cada clase."""
        if not ctx.con_experiencia:
            return
        for pid, p in ctx.onda.ev("Patron").items():
            recuerdos = {v.value: round(ctx.memoria.recordar(v, p.clase)[0], 2)
                         for v in (Verbo.COMER, Verbo.MOVER, Verbo.ATACAR, Verbo.COGER) if ctx.memoria.recordar(v, p.clase)[1]}
            if recuerdos:
                p.carga["recuerdos"] = recuerdos


class Sujeto(Componente):
    tipo = "Sujeto"
    entradas = ("Patron",)

    def reactiva(self, ctx: Contexto) -> None:
        for o in objetos(ctx):
            self.percibir(ctx, self.pieza(ctx, o.id, arousal=o.arousal * 0.5, carga={"clase": o.clase}, entradas=[o.id]), coste=0)


class Valor(Componente):
    """Valencia de cada sujeto: lo que motiva, lo que se siente por él (memoria) y lo social."""

    tipo = "Valor"
    entradas = ("Sujeto",)

    def reactiva(self, ctx: Contexto) -> None:
        arq, mem = ctx.arquetipo, ctx.memoria
        for o in objetos(ctx):
            motivacion = o.rasgo("nutritivo") * apetito(ctx) + 0.5 * o.rasgo("recurso") * arq.apertura
            patron = ctx.onda.ev("Patron").get(o.id)
            recuerdos = patron.carga.get("recuerdos", {}) if patron else {}
            sentimiento = math.tanh(sum(recuerdos.values()) / 5.0) if recuerdos else 0.0
            if mem.demostrada(o.clase, Relacion.PELIGROSO, ctx.latido):
                sentimiento -= 0.5
            social = o.rasgo("agente") * (arq.extraversion - 0.5)
            valencia = acotar(0.5 * motivacion + 0.5 * sentimiento + social - o.rasgo("peligro") * arq.neuroticismo, -1.0, 1.0)
            self.percibir(ctx, self.pieza(ctx, o.id, arousal=abs(valencia),
                                          carga={"clase": o.clase, "valencia": round(valencia, 3), "motivacion": round(motivacion, 3),
                                                 "sentimiento": round(sentimiento, 3), "social": round(social, 3)},
                                          entradas=[o.id, "Patron"]))


class Exteriorizacion(Componente):
    tipo = "Exteriorizacion"

    def reactiva(self, ctx: Contexto) -> None:
        self.registrar(ctx, self.pieza(ctx, "exteriorizacion", arousal=ctx.soma.estres,
                                       carga={"afecto": ctx.soma.afecto.value, "placer": round(ctx.soma.placer, 1)}))


class ImpulsoS2(Componente):
    """Convergencia sobre el canal común: sube o baja los candidatos según el valor de su objetivo."""

    tipo = "Impulso"
    entradas = ("Valor",)

    def reactiva(self, ctx: Contexto) -> None:
        valores = ctx.onda.ev("Valor")
        for c in ctx.onda.acc("Ejecucion").values():
            v = valores.get(c.carga["objetivo"])
            if v is None:
                continue
            c.arousal = acotar(c.arousal + 0.15 * v.carga["valencia"])
            c.entradas.append(f"S2:valor {v.carga['valencia']:+.2f}")


class Curiosidad(Componente):
    """Sube cuando no hay peligro ni necesidad; lo nuevo atrae. Puntuación baja: solo gana si nada urge."""

    tipo = "Curiosidad"

    def reactiva(self, ctx: Contexto) -> None:
        a = alarma(ctx)
        peligro = a.carga["peligro"] if a else 0.0
        if peligro >= 0.3 or ctx.soma.hambre() >= 0.6:
            return
        apertura = ctx.arquetipo.apertura

        def _score_lugar(l: Pieza) -> float:
            s = l.rasgo("novedad") - l.rasgo("peligro")
            if ctx.con_experiencia and ctx.memoria.activa:
                val = ctx.memoria.valor_lugar(l.id)
                s += max(-0.4, min(0.3, val * 0.15))
            return s

        nuevo = mejor(lugares(ctx), _score_lugar)
        if nuevo is not None and nuevo.rasgo("novedad") > 0.0 and nuevo.rasgo("peligro") < 0.5:
            ar = acotar(0.15 + 0.25 * apertura * nuevo.rasgo("novedad"))
            self.registrar(ctx, self.pieza(ctx, "curiosidad", arousal=ar, carga={"hacia": nuevo.id}))
            self.proponer(ctx, Verbo.MOVER, nuevo.id, ar, 0.5, "curiosidad: explorar", clase=nuevo.clase)
        util = mejor([o for o in objetos(ctx) if al_alcance(o) and o.rasgo("recurso") >= 0.4 and o.rasgo("peligro") < 0.3],
                     lambda o: o.rasgo("recurso") + o.rasgo("novedad"))
        if util is not None and ctx.soma.cargando is None:
            ar = acotar(0.2 + 0.3 * apertura * util.rasgo("recurso"))
            self.proponer(ctx, Verbo.COGER, util.id, ar, 0.5, f"curiosidad: coger {util.clase}", clase=util.clase)


class Hogar(Componente):
    """Hogar seguro en tres fases: recordar dónde se estuvo bien (lo hace el Core al cerrar episodios),
    volver cuando hay cansancio o peligro, y descansar allí. Descansar se propone también sin hogar
    si el cansancio es alto y hay calma."""

    tipo = "Hogar"

    def reactiva(self, ctx: Contexto) -> None:
        soma, perfil = ctx.soma, ctx.perfil
        if not perfil.duerme:
            return
        a = alarma(ctx)
        peligro = a.carga["peligro"] if a else 0.0
        cansancio = soma.cansancio()
        hogar = ctx.memoria.hogar() if perfil.hogar else None
        aqui = ctx.observacion.ubicacion if ctx.observacion else ""
        if hogar and hogar != aqui and (cansancio >= 0.4 or peligro >= 0.4):
            puerta = next((l for l in lugares(ctx) if l.id == hogar), None)
            if puerta is None and ctx.con_experiencia:
                salto = ctx.memoria.ruta(aqui, hogar)
                if salto:
                    # El retorno al hogar por memoria espacial no debe pisar la huida si la casilla implica peligro
                    umbral_p = 0.2 if peligro >= 0.4 else 0.8
                    puerta = next((l for l in lugares(ctx) if l.id == salto and l.rasgo("peligro") < umbral_p), None)
            if puerta is not None:
                # Urgencia mayor cuando es refugio directo sin peligro inmediato o cansancio manda
                ar = acotar(0.3 + 0.5 * max(cansancio, peligro * 0.7))
                self.proponer(ctx, Verbo.MOVER, puerta.id, ar, 0.7, "volver al hogar", clase=puerta.clase)
        if cansancio >= 0.6 and peligro < 0.3 and (hogar is None or hogar == aqui or cansancio >= 0.85):
            ar = acotar(0.4 + 0.5 * cansancio)
            self.registrar(ctx, self.pieza(ctx, "descansar", arousal=ar, carga={"en_hogar": hogar == aqui}))
            self.proponer(ctx, Verbo.DORMIR, aqui, ar, 0.8, "cansancio: dormir" + (" en el hogar" if hogar == aqui else ""))


class Orientacion(Componente):
    """Orientación espacial (hipocampo): ante necesidad nutritiva sin fuente visible,
    navega hacia ubicaciones recordadas de clases demostradas o prometedoras como nutritivas.
    """

    tipo = "Orientacion"

    def reactiva(self, ctx: Contexto) -> None:
        if not ctx.con_experiencia or not ctx.memoria.activa:
            return
        a = alarma(ctx)
        peligro = a.carga["peligro"] if a else 0.0
        hambre = ctx.soma.hambre()
        if peligro >= 0.4 or hambre < 0.35:
            return
        # Solo actua si no hay un recurso comestible visible ya cercano en la escena
        if any(o.rasgo("nutritivo") >= 0.3 for o in objetos(ctx)):
            return
        aqui = ctx.observacion.ubicacion if ctx.observacion else ""
        if not aqui:
            return
        for (clase, rel), prop in ctx.memoria.saber.items():
            if rel != Relacion.NUTRITIVO or prop.confianza < 0.55:
                continue
            if ctx.memoria.demostrada(clase, Relacion.PELIGROSO, ctx.latido):
                continue
            destino = ctx.memoria.donde_esta(clase)
            if destino and destino != aqui:
                salto = ctx.memoria.ruta(aqui, destino)
                if salto:
                    puerta = next((l for l in lugares(ctx) if l.id == salto and l.rasgo("peligro") < 0.6), None)
                    if puerta is not None:
                        ar = acotar(0.25 + 0.45 * hambre * prop.confianza)
                        self.registrar(ctx, self.pieza(ctx, "orientacion", arousal=ar, carga={"hacia": destino, "clase": clase}))
                        self.proponer(ctx, Verbo.MOVER, puerta.id, ar, 0.65, f"orientación: recordar {clase}", clase=puerta.clase)
                        return


def crear_s2() -> Sistema:
    return Sistema("S2", "Valor", [
        Modulo("Sentir", [Patron()]),
        Modulo("Interpretar", [Sujeto(), Valor()]),
        Modulo("Reaccionar", [Exteriorizacion(), ImpulsoS2(), Curiosidad(), Hogar(), Orientacion()]),
    ])
