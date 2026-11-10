"""S3 · Verdad: comunicación, razonamiento y lenguaje formal interno. Trabaja con lo que le sobra a S2.

El conocimiento lo escribe el Core (``Memoria.aprender``) a partir de la experiencia. S3 lo lee,
lo expresa en frases legibles y saca conclusiones. Un Comportamiento de S3 solo se apoya en
proposiciones **demostradas**.

| Etapa       | Componente           | Produce |
|-------------|----------------------|---------|
| Sentir      | Comunicacion         | Comunicación: mensajes que el mundo pone en la escena |
| Interpretar | Agente               | Agente (mismo id que Objeto y Sujeto) |
| Interpretar | PredicadoProposicion | Predicado (lo que se observa ahora) y Proposición (lo que se sabe de su clase) |
| Interpretar | Sentencia            | Sentencia: proposiciones encadenadas con una condición |
| Interpretar | Logica               | Lógica: la conclusión que se sigue de las sentencias |
| Reaccionar  | Comportamiento       | Comportamiento basado en conocimiento demostrado + candidato de Ejecución |
| Reaccionar  | ImpulsoS3            | Freno prefrontal sobre los candidatos que contradicen lo que se sabe |
"""

from ida.core.arquitectura import Componente, Contexto, Modulo, Sistema
from ida.core.pieza import acotar
from ida.core.vocabulario import EstadoSaber, Relacion, Verbo
from ida.sistemas.comun import al_alcance, apetito, escena, lugares, mejor, objetos


class Comunicacion(Componente):
    tipo = "Comunicacion"
    entradas = ("Escena",)

    def reactiva(self, ctx: Contexto) -> None:
        for p in escena(ctx):
            mensaje = p.carga.get("datos", {}).get("mensaje")
            if mensaje:
                self.percibir(ctx, self.pieza(ctx, p.id, arousal=0.5, carga={"clase": p.clase, "mensaje": str(mensaje)[:200]}, entradas=[p.id]))


class Agente(Componente):
    tipo = "Agente"
    entradas = ("Objeto",)

    def reactiva(self, ctx: Contexto) -> None:
        for o in objetos(ctx):
            self.percibir(ctx, self.pieza(ctx, o.id, arousal=o.arousal * 0.5, carga={"clase": o.clase, "actua": o.rasgo("agente") >= 0.5},
                                          entradas=[o.id]), coste=0)


class PredicadoProposicion(Componente):
    """Predicados de lo observado ahora y proposiciones de lo que se sabe de cada clase."""

    tipo = "Proposicion"
    entradas = ("Agente",)

    def reactiva(self, ctx: Contexto) -> None:
        for o in objetos(ctx):
            predicados = []
            if al_alcance(o):
                predicados.append("está al alcance")
            elif o.rasgo("proximidad") >= 0.5:
                predicados.append("está cerca")
            if o.rasgo("novedad") >= 0.6:
                predicados.append("es nuevo")
            if predicados:
                self.percibir(ctx, self.pieza(ctx, o.id, arousal=0.2, carga={"clase": o.clase, "predicados": predicados}, tipo="Predicado"), coste=0)

    def activa(self, ctx: Contexto) -> None:
        """Dimensión activa: trae a la atención lo que se sabe de las clases presentes."""
        if not ctx.con_experiencia:
            return
        vistas = set()
        for o in objetos(ctx):
            if o.clase in vistas:
                continue
            vistas.add(o.clase)
            for rel in Relacion:
                p = ctx.memoria.proposicion(o.clase, rel)
                if p is None:
                    continue
                estado = p.estado(ctx.latido)
                self.percibir(ctx, self.pieza(ctx, f"{o.clase}|{rel.name}", arousal=0.3 + 0.4 * p.confianza, confianza=p.confianza,
                                              carga={"clase": o.clase, "relacion": rel, "estado": estado, "texto": p.texto(ctx.latido)}))


class Sentencia(Componente):
    """Encadena proposiciones demostradas con la situación: «si <clase> está cerca y <condición>, <conclusión>»."""

    tipo = "Sentencia"
    entradas = ("Proposicion",)

    def reactiva(self, ctx: Contexto) -> None:
        props = {(p.carga["clase"], p.carga["relacion"]): p for p in ctx.onda.ev("Proposicion").values()
                 if p.carga["estado"] == EstadoSaber.DEMOSTRADA}
        for o in objetos(ctx):
            cerca = o.rasgo("proximidad") >= 0.5
            if (o.clase, Relacion.PELIGROSO) in props and cerca:
                self._sentencia(ctx, o, "EVITAR", f"si {o.clase} está cerca, hace daño → evitarlo", props[(o.clase, Relacion.PELIGROSO)])
            if (o.clase, Relacion.NUTRITIVO) in props and apetito(ctx) >= 0.4:
                self._sentencia(ctx, o, "COMER", f"si tengo hambre y hay {o.clase}, me alimenta → comerlo", props[(o.clase, Relacion.NUTRITIVO)])
            if (o.clase, Relacion.UTIL) in props and ctx.soma.cargando is None and al_alcance(o):
                self._sentencia(ctx, o, "COGER", f"{o.clase} sirve para algo → cogerlo", props[(o.clase, Relacion.UTIL)])

    def _sentencia(self, ctx, o, conclusion, texto, base) -> None:
        self.percibir(ctx, self.pieza(ctx, f"{conclusion}:{o.id}", arousal=0.6, confianza=base.confianza,
                                      carga={"objetivo": o.id, "clase": o.clase, "conclusion": conclusion, "texto": texto},
                                      entradas=[base.id]))


class Logica(Componente):
    """Combina las sentencias y resuelve conflictos: evitar el daño prevalece sobre comer o coger."""

    tipo = "Logica"
    entradas = ("Sentencia",)
    PRIORIDAD = {"EVITAR": 0, "COMER": 1, "COGER": 2}

    def reactiva(self, ctx: Contexto) -> None:
        sentencias = sorted(ctx.onda.ev("Sentencia").values(), key=lambda s: (self.PRIORIDAD[s.carga["conclusion"]], -s.confianza))
        if sentencias:
            s = sentencias[0]
            self.percibir(ctx, self.pieza(ctx, "conclusion", arousal=0.6, confianza=s.confianza, carga=dict(s.carga), entradas=[s.id]))


class Comportamiento(Componente):
    """Convierte la conclusión lógica en un candidato de Ejecución. Solo existe si hay conocimiento demostrado."""

    tipo = "Comportamiento"
    entradas = ("Logica",)

    def reactiva(self, ctx: Contexto) -> None:
        c = ctx.onda.ev("Logica").get("conclusion")
        if c is None:
            return
        objetivo = ctx.onda.ev("Objeto").get(c.carga["objetivo"])
        if objetivo is None:
            return
        conclusion, motivo = c.carga["conclusion"], f"S3: {c.carga['texto']}"
        if conclusion == "EVITAR":
            salida = mejor(lugares(ctx), lambda l: -l.rasgo("peligro"))
            if salida is not None:
                self.proponer(ctx, Verbo.MOVER, salida.id, 0.7, c.confianza, motivo, clase=salida.clase)
        elif conclusion == "COMER":
            if al_alcance(objetivo):
                self.proponer(ctx, Verbo.COMER, objetivo.id, 0.65, c.confianza, motivo, clase=objetivo.clase)
            else:
                destino = mejor(lugares(ctx), lambda l: l.rasgo("nutritivo") - 1.5 * l.rasgo("peligro"))
                if destino is not None and destino.rasgo("nutritivo") > 0:
                    self.proponer(ctx, Verbo.MOVER, destino.id, 0.55, c.confianza, motivo + " (acercarse)", clase=destino.clase)
        elif conclusion == "COGER":
            self.proponer(ctx, Verbo.COGER, objetivo.id, 0.5, c.confianza, motivo, clase=objetivo.clase)


class ImpulsoS3(Componente):
    """Freno prefrontal: baja los candidatos que van contra lo demostrado (acercarse a lo peligroso,
    comer lo que se sabe que no alimenta)."""

    tipo = "Impulso"
    entradas = ("Proposicion",)

    def reactiva(self, ctx: Contexto) -> None:
        mem, ahora = ctx.memoria, ctx.latido
        for c in ctx.onda.acc("Ejecucion").values():
            verbo, clase = c.carga["verbo"], c.carga.get("clase", "")
            if not clase or c.sistema == "S3":
                continue
            frenar = None
            if verbo in (Verbo.MOVER, Verbo.COMER, Verbo.COGER) and mem.demostrada(clase, Relacion.PELIGROSO, ahora):
                frenar = f"{clase} es peligroso"
            nutr = mem.proposicion(clase, Relacion.NUTRITIVO)
            if verbo == Verbo.COMER and nutr is not None and nutr.estado(ahora) == EstadoSaber.REFUTADA:
                frenar = f"{clase} no alimenta"
            if frenar:
                c.arousal = acotar(c.arousal * 0.4)
                c.confianza = acotar(c.confianza * 0.5)
                c.entradas.append(f"S3:frenado ({frenar})")


def crear_s3() -> Sistema:
    return Sistema("S3", "Verdad", [
        Modulo("Sentir", [Comunicacion()]),
        Modulo("Interpretar", [Agente(), PredicadoProposicion(), Sentencia(), Logica()]),
        Modulo("Reaccionar", [Comportamiento(), ImpulsoS3()]),
    ])
