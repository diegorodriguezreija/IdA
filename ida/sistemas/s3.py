"""S3 · Verdad: comunicación, razonamiento y lenguaje formal interno. Trabaja con lo que le sobra a S2.

El conocimiento lo escribe el Core (``Memoria.aprender``) a partir de la experiencia. S3 lo lee,
lo expresa en frases legibles y saca conclusiones. Un Comportamiento de S3 solo se apoya en
proposiciones **demostradas**.

| Etapa       | Componente           | Produce |
|-------------|----------------------|---------|
| Sentir      | Comunicacion         | Comunicación: mensajes que el mundo pone en la escena |
| Interpretar | Agente               | Agente (mismo id que Objeto y Sujeto) |
| Interpretar | Predicado            | Predicado: lo que se observa ahora (pasada reactiva) |
| Interpretar | Proposicion          | Proposición: lo que se sabe de su clase (pasada activa) |
| Interpretar | Sentencia            | Sentencia: proposiciones encadenadas con una condición |
| Interpretar | Creencia             | Creencia: lo que se sostiene como cierto, con trust y fuentes |
| Interpretar | Logica               | Lógica: la conclusión que se sigue de las sentencias |
| Reaccionar  | Intencion            | Intención: saber y las que declare el mundo (el qué deliberado) |
| Reaccionar  | Feedback             | Feedback de S3: baja del error de predicción (aciertos menos sorpresas) |
| Reaccionar  | Estrategia           | Estrategias de conocimiento: evitar, comer y coger lo sabido; estudiar |
| Actuar      | Accion               | Acción de cada estrategia activa de S3, con su origen |
| Reaccionar  | Impulso              | Control gradual según la certeza, sobre piezas Impulso (sube o baja impulsos) |
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ida.core.arquitectura import Componente, Contexto, Modulo, Sistema
from ida.core.estrategia import Catalogo, ConPropuestas, Definicion, Propuesta
from ida.core.memoria import desplazamiento
from ida.core.biblioteca import Consulta, ElementoConsulta, EstadoLectura, RegistroLectura
from ida.core.pieza import Pieza, acotar
from ida.core.vocabulario import Afecto, EstadoSaber, Relacion, Verbo
from ida.sistemas.comun import Accion, Estrategia, al_alcance, alarma, apetito, exterocepcion, lugares, mejor, objetos


class Comunicacion(Componente):
    tipo = "Comunicacion"
    entradas = ("Exterocepcion",)

    def reactiva(self, ctx: Contexto) -> None:
        for p in exterocepcion(ctx):
            mensaje = p.carga.get("datos", {}).get("mensaje")
            if mensaje:
                self.percibir(ctx, self.pieza(ctx, p.id, arousal=0.5, carga={"clase": p.clase, "mensaje": str(mensaje)[:200]}, entradas=[p.id]))


class Agente(Componente):
    tipo = "Agente"
    entradas = ("Objeto",)

    def reactiva(self, ctx: Contexto) -> None:
        for o in objetos(ctx):
            self.percibir(ctx, self.pieza(ctx, o.id, arousal=o.arousal * 0.5, carga={"clase": o.clase, "actua": o.rasgo("agente") >= 0.5},
                                          entradas=[o.id]))


class Predicado(Componente):
    """Predicados de lo observado ahora (pasada reactiva)."""

    tipo = "Predicado"
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
                self.percibir(ctx, self.pieza(ctx, o.id, arousal=0.2, carga={"clase": o.clase, "predicados": predicados}))


class Proposicion(Componente):
    """Proposiciones de lo que se sabe de cada clase presente (pasada activa)."""

    tipo = "Proposicion"
    entradas = ("Agente",)

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


def _conclusion(ctx: Contexto, tipo: str) -> Optional[Tuple[Pieza, Pieza]]:
    """La conclusión de ``Logica`` de ese tipo (EVITAR, COMER, COGER) y su objeto, si están a la vista."""
    c = ctx.onda.ev("Logica").get("conclusion")
    if c is None or c.carga["conclusion"] != tipo:
        return None
    objetivo = ctx.onda.ev("Objeto").get(c.carga["objetivo"])
    return (c, objetivo) if objetivo is not None else None


class EvitarLoPeligroso(Definicion):
    """Seguridad, por conocimiento (antes ``Comportamiento``, EVITAR): alejarse de lo que se sabe peligroso."""

    nombre = "evitar_lo_peligroso"
    impulsos = ("seguridad",)
    prioridad = 10

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return _conclusion(ctx, "EVITAR") is not None and bool(lugares(ctx))

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        cc = _conclusion(ctx, "EVITAR")
        salida = mejor(lugares(ctx), lambda lugar: -lugar.rasgo("peligro"))
        if cc is None or salida is None:
            return None
        return Propuesta(Verbo.MOVER, salida.id, 0.7, cc[0].confianza, f"S3: {cc[0].carga['texto']}", clase=salida.clase)


class ComerLoNutritivo(Definicion):
    """Necesidades que satisface lo nutritivo, por conocimiento (antes ``Comportamiento``, COMER)."""

    nombre = "comer_lo_nutritivo"
    rasgo = "nutritivo"
    prioridad = 10

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return _conclusion(ctx, "COMER") is not None

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        cc = _conclusion(ctx, "COMER")
        if cc is None:
            return None
        c, objetivo = cc
        motivo = f"S3: {c.carga['texto']}"
        if al_alcance(objetivo):
            return Propuesta(Verbo.COMER, objetivo.id, 0.65, c.confianza, motivo, clase=objetivo.clase)
        destino = mejor(lugares(ctx), lambda lugar: lugar.rasgo("nutritivo") - 1.5 * lugar.rasgo("peligro"))
        if destino is not None and destino.rasgo("nutritivo") > 0:
            return Propuesta(Verbo.MOVER, destino.id, 0.55, c.confianza, motivo + " (acercarse)", clase=destino.clase)
        return None


class CogerLoUtil(Definicion):
    """Exploración, por conocimiento (antes ``Comportamiento``, COGER): coger lo que se sabe útil."""

    nombre = "coger_lo_util"
    impulsos = ("exploracion",)
    prioridad = 10

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return _conclusion(ctx, "COGER") is not None

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        cc = _conclusion(ctx, "COGER")
        if cc is None:
            return None
        c, objetivo = cc
        return Propuesta(Verbo.COGER, objetivo.id, 0.5, c.confianza, f"S3: {c.carga['texto']}", clase=objetivo.clase)


class Impulso(Componente):
    """Control de S3 de arriba abajo (decisión 13): con certeza, sube los impulsos que encajan con lo
    que sabe y baja los que no. Gradual, no un interruptor: el cambio es proporcional a la confianza
    de lo demostrado (hasta ``FUERZA``). Sin nada demostrado, no toca nada. Solo modifica piezas
    ``Impulso`` (de cualquier sistema, decisión 14); el Tribunal suma ese cambio al arousal de las
    acciones de ese impulso.
    - Peligro demostrado cerca (proximidad ≥ 0,5): sube Seguridad.
    - Todo lo comestible a la vista se sabe que no nutre: baja las necesidades que satisface lo nutritivo.
    """

    tipo = "Impulso"
    FUERZA = 0.2

    def reactiva(self, ctx: Contexto) -> None:
        if not ctx.con_experiencia:
            return
        creencias = ctx.onda.ef("Creencia")
        impulsos = ctx.onda.ef("Impulso")
        seguridad = impulsos.get("seguridad")
        if seguridad is not None:
            certeza = max((c.carga["trust"] for o in objetos(ctx) if o.rasgo("proximidad") >= 0.5
                           for c in [creencia(creencias, o.clase, Relacion.PELIGROSO)] if c is not None and c.carga["sostiene"]),
                          default=0.0)
            if certeza > 0.0:
                self.modificar(ctx, seguridad, arousal=seguridad.arousal + self.FUERZA * certeza, entrada="S3: peligro demostrado cerca")
        comestibles = [o for o in objetos(ctx) if o.rasgo("nutritivo") >= 0.3]
        refutadas = [creencia(creencias, o.clase, Relacion.NUTRITIVO) for o in comestibles]
        if comestibles and all(c is not None and c.carga["estado"] == EstadoSaber.REFUTADA for c in refutadas):
            confianza_nutre = max(c.carga["trust"] for c in refutadas if c is not None)
            certeza = 1.0 - confianza_nutre        # certeza de que no nutre
            for imp in impulsos.values():
                if imp.carga.get("rasgo") == "nutritivo":
                    self.modificar(ctx, imp, arousal=imp.arousal - self.FUERZA * certeza, entrada="S3: lo que hay no nutre")


class Estudio(ConPropuestas):
    """Estrategia de S3 para la intención saber (antes componente): lectura con atención sostenida en
    consulta a una biblioteca externa sobre hipótesis pendientes. Lleva su propio control (cooldown,
    interrupción por alarma o por no leer), así que no se agota por falta de progreso."""

    nombre = "estudiar"
    impulsos = ("saber",)
    prioridad = 10
    agotable = False

    COOLDOWN_LECTURA = 15
    MAX_HIPOTESIS_POR_LECTURA = 2
    L0 = 4
    L1 = 2
    MAX_LATIDOS_ESPERA_TR = 10

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return ctx.con_experiencia and Verbo.ESPERAR in ctx.verbos and ctx.memoria.activa

    def decidir(self, ctx: Contexto, estrategia: Optional[Pieza] = None) -> None:
        if not ctx.con_experiencia or Verbo.ESPERAR not in ctx.verbos:
            return
        mem = ctx.memoria
        if not mem.activa:
            return

        # 1. Si está dormido, interrumpir si había lectura activa
        if ctx.soma.dormido:
            if mem.lectura_activa is not None:
                mem.lectura_activa.estado = EstadoLectura.INTERRUMPIDO
                mem.lectura_activa = None
                mem.ultimo_fin_lectura = ctx.latido
                ctx.onda.notas["aprendizaje"] = "«deja la lectura: sueño»"
            return

        # 2. Gestionar lectura activa en curso
        if mem.lectura_activa is not None:
            reg = mem.lectura_activa

            # Detectar interrupción: si tras haber empezado no se ejecutó LEER en el latido anterior
            if ctx.latido > reg.inicio:
                ej_ant = ctx.onda.ei("Accion").get("Accion")
                if ej_ant is None or ej_ant.carga.get("verbo") != Verbo.LEER:
                    reg.estado = EstadoLectura.INTERRUMPIDO
                    mem.lectura_activa = None
                    mem.ultimo_fin_lectura = ctx.latido
                    ctx.onda.notas["aprendizaje"] = "«deja la lectura: interrumpida»"
                    return

            # Detectar interrupción por alarma o peligro súbito
            al = alarma(ctx)
            if al is not None and al.carga.get("peligro", 0.0) >= 0.3:
                reg.estado = EstadoLectura.INTERRUMPIDO
                mem.lectura_activa = None
                mem.ultimo_fin_lectura = ctx.latido
                ctx.onda.notas["aprendizaje"] = "«deja la lectura: alarma»"
                return

            reg.latidos_dedicados += 1

            # ¿Completó la duración requerida de atención sostenida?
            if reg.latidos_dedicados >= reg.duracion_requerida:
                if reg.ticket and reg.ticket.lista():
                    resp = reg.ticket.respuesta()
                    if resp is not None and resp.elementos:
                        reg.respuesta = {}
                        for el in resp.elementos:
                            reg.respuesta[f"{el.sujeto}:{el.relacion.name}"] = {
                                "veredicto": el.veredicto.value,
                                "confianza": el.confianza,
                            }
                            prop = mem.proposicion(el.sujeto, el.relacion)
                            if prop is not None:
                                c_ant = prop.confianza
                                prop.aplicar_autoridad(
                                    el.veredicto.value,
                                    el.confianza,
                                    ctx.arquetipo.deferencia * 2.0,
                                    ctx.latido,
                                )
                                c_post = prop.confianza
                                ctx.onda.notas["aprendizaje"] = (
                                    f"«lee: la biblioteca {el.veredicto.value} "
                                    f"'{el.sujeto} {el.relacion.value}' ({el.confianza:.2f}); "
                                    f"confianza {c_ant:.2f} -> {c_post:.2f}»"
                                )
                        reg.estado = EstadoLectura.LEIDO
                    else:
                        reg.estado = EstadoLectura.INVALIDO
                    mem.lectura_activa = None
                    mem.ultimo_fin_lectura = ctx.latido
                    return
                elif ctx.perfil.tiempo_real:
                    if reg.latidos_dedicados >= reg.duracion_requerida + self.MAX_LATIDOS_ESPERA_TR:
                        reg.estado = EstadoLectura.SIN_RESPUESTA
                        mem.lectura_activa = None
                        mem.ultimo_fin_lectura = ctx.latido
                        return

            # Inercia atencional: mientras sostiene la lectura, gana arousal y confianza
            # para proteger la tarea frente a distracciones leves (Curiosidad), pero cede ante
            # alarmas o reflejos de S1 (arousal >= 0.7).
            progreso = reg.latidos_dedicados / max(1, reg.duracion_requerida)
            self.proponer(
                ctx,
                Verbo.LEER,
                "biblioteca",
                arousal=acotar(0.32 + 0.25 * progreso),
                confianza=acotar(0.65 + 0.20 * progreso),
                motivo=f"estudio: leyendo ({reg.latidos_dedicados}/{reg.duracion_requerida})",
            )
            return

        # 3. Considerar iniciar nueva lectura o relectura
        al = alarma(ctx)
        peligro = al.carga.get("peligro", 0.0) if al else 0.0
        if peligro >= 0.2:
            return
        if ctx.soma.hambre() >= 0.45 or ctx.soma.cansancio() >= 0.45:
            return
        if ctx.soma.afecto not in (Afecto.CALMA, Afecto.CURIOSIDAD):
            return
        if ctx.latido - mem.ultimo_fin_lectura < self.COOLDOWN_LECTURA:
            return

        # 3a. Relectura de registro disponible previo interrumpido
        for reg_prev in reversed(mem.lecturas):
            if reg_prev.estado == EstadoLectura.INTERRUMPIDO and reg_prev.ticket and reg_prev.ticket.lista():
                reg_prev.estado = EstadoLectura.PENDIENTE
                reg_prev.latidos_dedicados = 0
                mem.lectura_activa = reg_prev
                ctx.onda.notas["aprendizaje"] = f"«relee registro sobre {len(reg_prev.elementos)} hipótesis»"
                self.proponer(
                    ctx,
                    Verbo.LEER,
                    "biblioteca",
                    arousal=0.28,
                    confianza=0.60,
                    motivo=f"estudio: relectura (0/{reg_prev.duracion_requerida})",
                )
                return

        # 3b. Nueva lectura: requiere biblioteca externa y proposiciones en hipótesis
        if ctx.biblioteca is None:
            return

        consultadas_recientes = {
            par for r in mem.lecturas[-5:] for par in r.elementos
        }
        hipotesis = sorted(
            (
                p for p in mem.saber.values()
                if p.estado(ctx.latido) == EstadoSaber.HIPOTESIS
                and (p.sujeto, p.relacion.name) not in consultadas_recientes
            ),
            key=lambda p: (p.confirmaciones + p.refutaciones, abs(p.confianza - 0.5)),
        )
        if not hipotesis:
            return

        seleccionadas = hipotesis[: self.MAX_HIPOTESIS_POR_LECTURA]
        elementos_cons = [ElementoConsulta(p.sujeto, p.relacion) for p in seleccionadas]
        ticket = ctx.biblioteca.solicitar(Consulta(elementos=elementos_cons))
        duracion = self.L0 + self.L1 * len(elementos_cons)
        reg_nuevo = RegistroLectura(
            id=f"lec_{ctx.latido}",
            inicio=ctx.latido,
            elementos=[(e.sujeto, e.relacion.name) for e in elementos_cons],
            duracion_requerida=duracion,
            ticket=ticket,
            estado=EstadoLectura.PENDIENTE,
        )
        mem.lecturas.append(reg_nuevo)
        mem.lectura_activa = reg_nuevo
        ctx.onda.notas["aprendizaje"] = f"«empieza a leer sobre {len(elementos_cons)} hipótesis»"
        self.proponer(
            ctx,
            Verbo.LEER,
            "biblioteca",
            arousal=0.28,
            confianza=0.60,
            motivo=f"estudio: lectura (0/{duracion})",
        )


# ---------------------------------------------------------------------------
# Paso 5 de la fase de generalización: planificador general sobre requisitos
# ---------------------------------------------------------------------------
def _yo(ctx: Contexto) -> Dict[str, Any]:
    yo = ctx.onda.ev("Propiocepcion").get("yo")
    return dict(yo.carga) if yo is not None else {}


def inventario(ctx: Contexto) -> Dict[str, float]:
    """Inventario percibido (propiocepción)."""
    return {str(k): float(v) for k, v in (_yo(ctx).get("inventario") or {}).items()}


def delante(ctx: Contexto) -> Optional[Dict[str, Any]]:
    """Lo que hay delante (``cuerpo["delante"]`` = {"id", "clase"}), si el mundo lo percibe."""
    d = (_yo(ctx).get("cuerpo") or {}).get("delante")
    return dict(d) if isinstance(d, dict) and d.get("clase") else None


def _cosas(ctx: Contexto) -> List[Pieza]:
    return [p for p in exterocepcion(ctx) if p.rasgo("lugar") < 0.5]


def _pos(p: Pieza) -> Optional[Tuple[int, int]]:
    pos = p.carga.get("datos", {}).get("pos")
    return (int(pos[0]), int(pos[1])) if isinstance(pos, (list, tuple)) and len(pos) == 2 else None


def _dist(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def al_alcance_clase(ctx: Contexto, clase: str) -> bool:
    return any(p.clase == clase and al_alcance(p) for p in _cosas(ctx))


def desplazamientos_a_clase(ctx: Contexto, clase: str) -> List[Tuple[int, int]]:
    """Desplazamientos ``(|dx|, |dy|)`` ordenados a cada instancia visible de ``clase``. Con posiciones se
    calculan; sin ellas, lo que está al alcance cuenta como (0, 1) y lo demás no se sabe (se omite)."""
    aqui = _pos_propia(ctx)
    salida: List[Tuple[int, int]] = []
    for p in _cosas(ctx):
        if p.clase != clase:
            continue
        pos = _pos(p)
        if aqui is not None and pos is not None:
            salida.append(desplazamiento(pos[0] - aqui[0], pos[1] - aqui[1]))
        elif al_alcance(p):
            salida.append((0, 1))
    return salida


@dataclass
class Paso:
    """La primera acción ejecutable de una cadena de requisitos, con su coste estimado."""

    verbo: Verbo
    objetivo: str
    clase: str
    coste: float
    confianza: float
    motivo: List[str]
    datos: Dict[str, Any] = field(default_factory=dict)
    destino: str = ""                  # adónde lleva un MOVER (instancia o lugar recordado)
    distancia: Optional[int] = None    # distancia a ese destino al proponerlo, si se sabe


COSTE_RECORDADO = 15.0     # ir adonde se recuerda algo que no se ve
COSTE_POR_PROXIMIDAD = 10.0
MAX_RUTA_MAPA = 40         # pasos máximos de una ruta por el mapa local hasta algo recordado
COSTE_SIN_PRODUCTOR = 2 * COSTE_RECORDADO   # reponer una unidad de algo que ninguna acción conocida da
VECINAS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def ir_por_el_mapa(ctx: Contexto, clase: str, confianza: float = 0.5, excluir: frozenset = frozenset()) -> Optional[Paso]:
    """Un paso hacia la casilla recordada de ``clase`` más cercana por el mapa local de la memoria (paso 3), con el coste en
    pasos de la ruta hasta quedar al lado. La ruta solo pasa por casillas de clases que se sabe transitables. Destino
    ``<clase>@x_y`` (``excluir`` lo aparca). None sin posiciones, sin mapa, sin ninguna recordada a menos de
    ``MAX_RUTA_MAPA`` pasos, si ya está al lado o si el primer paso no es un lugar percibido sin peligro."""
    mem = ctx.memoria
    aqui = _pos_propia(ctx)
    if aqui is None or not ctx.con_experiencia or not mem.casillas:
        return None
    objetivos = {p for p, c in mem.casillas.items() if c == clase and f"{clase}@{p[0]}_{p[1]}" not in excluir}
    if not objetivos:
        return None
    junto = {(x + dx, y + dy): (x, y) for x, y in sorted(objetivos) for dx, dy in VECINAS}
    if aqui in junto:
        return None
    previo: Dict[Tuple[int, int], Tuple[int, int]] = {}
    frontera, d, llegada = [aqui], 0, None
    while frontera and llegada is None and d < MAX_RUTA_MAPA:
        d += 1
        siguiente = []
        for x, y in frontera:
            for dx, dy in VECINAS:
                v = (x + dx, y + dy)
                if v in previo or v == aqui or mem.transitable(mem.casillas.get(v)) is not True:
                    continue
                previo[v] = (x, y)
                if v in junto:
                    llegada = v
                    break
                siguiente.append(v)
            if llegada is not None:
                break
        frontera = siguiente
    if llegada is None:
        return None
    primero = llegada
    while previo[primero] != aqui:
        primero = previo[primero]
    puerta = next((lugar for lugar in lugares(ctx) if _pos(lugar) == primero and lugar.rasgo("peligro") < 0.5), None)
    if puerta is None:
        return None
    x, y = junto[llegada]
    return Paso(Verbo.MOVER, puerta.id, puerta.clase, float(d), confianza, [f"volver a {clase} (mapa, {d} pasos)"],
                destino=f"{clase}@{x}_{y}", distancia=d)


def acercarse_a_clase(ctx: Contexto, clase: str, confianza: float = 0.5, excluir: frozenset = frozenset()) -> Optional[Paso]:
    """Un paso hacia la instancia visible más cercana de ``clase`` o, si no se ve, hacia donde se recuerda
    (``memoria.donde_esta`` y ``memoria.ruta``). General: con posiciones (``datos["pos"]``) elige el lugar
    vecino que más acorta la distancia; sin ellas, solo la ruta topológica de la memoria. ``excluir``: destinos
    aparcados (instancias o lugares) que no se eligen."""
    visibles = [p for p in _cosas(ctx) if p.clase == clase and p.id not in excluir]
    sitios = [lugar for lugar in lugares(ctx) if lugar.rasgo("peligro") < 0.5]
    if visibles:
        objetivo = max(visibles, key=lambda p: p.rasgo("proximidad"))
        destino = _pos(objetivo)
        aqui = _pos_propia(ctx)
        if destino is not None and aqui is not None:
            con_pos = [(lugar, _pos(lugar)) for lugar in sitios]
            candidatos = [(lp, lugar) for lugar, lp in con_pos if lp is not None]
            if candidatos:
                lp, lugar = min(candidatos, key=lambda c: _dist(c[0], destino))
                if _dist(lp, destino) < _dist(aqui, destino):
                    coste = COSTE_POR_PROXIMIDAD * (1.0 - objetivo.rasgo("proximidad"))
                    return Paso(Verbo.MOVER, lugar.id, lugar.clase, coste, confianza, [f"ir a {clase}"],
                                destino=objetivo.id, distancia=_dist(aqui, destino))
    ubicacion = ctx.observacion.ubicacion if ctx.observacion else ""
    destino_nodo = ctx.memoria.donde_esta(clase) if ctx.con_experiencia else None
    if ubicacion and destino_nodo and destino_nodo != ubicacion and destino_nodo not in excluir:
        salto = ctx.memoria.ruta(ubicacion, destino_nodo)
        puerta = next((lugar for lugar in sitios if lugar.id == salto), None)
        if puerta is not None:
            camino = ctx.memoria.camino(ubicacion, destino_nodo)
            return Paso(Verbo.MOVER, puerta.id, puerta.clase, COSTE_RECORDADO, confianza, [f"volver a {clase} (recordado)"],
                        destino=destino_nodo, distancia=len(camino) - 1 if camino else None)
    return None


def _pos_propia(ctx: Contexto) -> Optional[Tuple[int, int]]:
    """Posición propia si la ubicación lleva coordenadas al final (``<nombre>_x_y``); si no, None."""
    partes = str(ctx.observacion.ubicacion if ctx.observacion else "").rsplit("_", 2)
    if len(partes) == 3 and partes[1].lstrip("-").isdigit() and partes[2].lstrip("-").isdigit():
        return int(partes[1]), int(partes[2])
    return None


class PerseguirMetas(ConPropuestas):
    """Estrategia general de S3 para la intención «progresar» (paso 5): encadena requisitos hacia atrás desde
    las metas que declara el manual del mundo. No sabe qué es nada: trabaja con (verbo, objetivo) →
    requisitos → efecto. Con ``memoria.metas`` vacía (un mundo sin manual) no es elegible.

    - Para cada meta pendiente busca la primera acción ejecutable que la acerca (``_resolver``) y propone la
      de menor coste: submetas pendientes más distancia a la instancia objetivo, más los fallos esperados de
      la acción, 1 / tasa − 1 (``Memoria.tasa_estimada``). Una acción cuyo efecto puede salir (manual o
      experiencia) no se bloquea por fallos seguidos: su coste crece con ellos.
    - No persigue metas de ATACAR (lo arbitra Seguridad) ni de DORMIR (no decide cuándo dormir): son metas
      del manual, pero se cumplen por otras vías.
    - Sin plan, con calma y con poca frecuencia, prueba COGER sobre lo que tiene delante si aún no lo ha
      probado en esta vida (exploración de efectos, 5.2 c).
    """

    nombre = "perseguir_metas"
    impulsos = ("progresar",)
    prioridad = 10
    agotable = False
    PROFUNDIDAD = 5
    AROUSAL = 0.5
    CADA_EXPLORACION = 5          # latidos entre pruebas de efectos
    VERBOS_PLAN = (Verbo.USAR, Verbo.COGER, Verbo.COMER)
    SIN_ACERCARSE = 8             # propuestas seguidas de MOVER al mismo destino sin que baje la distancia...
    APARCAR = 30                  # ...que lo dejan aparcado durante estos latidos

    def __init__(self) -> None:
        super().__init__()
        self._aparcados: Dict[str, int] = {}          # destino -> latido hasta el que no se elige
        self._seguimiento: Tuple[str, Optional[int], int] = ("", None, 0)   # destino, mejor distancia, propuestas sin bajar
        self._costes_unidad: Dict[Tuple[int, str], float] = {}           # (latido, objeto) -> pasos para una unidad
        self._rutas_mapa: Dict[Tuple[int, str, frozenset], Optional[Paso]] = {}   # (latido, clase, aparcados) -> paso por el mapa

    def _excluir(self, ctx: Contexto) -> frozenset:
        return frozenset(d for d, hasta in self._aparcados.items() if ctx.latido < hasta)

    def _vigilar(self, ctx: Contexto, paso: Paso) -> None:
        """Antibloqueo general: si las últimas ``SIN_ACERCARSE`` propuestas fueron MOVER hacia el mismo destino y la
        distancia no ha bajado, ese destino queda aparcado ``APARCAR`` latidos."""
        if paso.verbo != Verbo.MOVER or not paso.destino:
            self._seguimiento = ("", None, 0)
            return
        destino, mejor_d, n = self._seguimiento
        if destino != paso.destino:
            self._seguimiento = (paso.destino, paso.distancia, 0)
            return
        if paso.distancia is not None and (mejor_d is None or paso.distancia < mejor_d):
            self._seguimiento = (destino, paso.distancia, 0)
            return
        n += 1
        if n >= self.SIN_ACERCARSE:
            self._aparcados[destino] = ctx.latido + self.APARCAR
            self._seguimiento = ("", None, 0)
        else:
            self._seguimiento = (destino, mejor_d, n)

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return bool(ctx.con_experiencia) and (any(not m.conseguida and m.verbo in self.VERBOS_PLAN for m in ctx.memoria.metas.values())
                                              or bool(self._peticiones(ctx, inventario(ctx))))

    @staticmethod
    def _peticiones(ctx: Contexto, inv: Dict[str, float]) -> List[Pieza]:
        """Metas instrumentales pendientes (piezas ``Peticion`` de este latido): lo pedido que aún no se tiene."""
        return [p for _, p in sorted(ctx.onda.ef("Peticion").items()) if inv.get(str(p.carga["objeto"]), 0.0) < float(p.carga["cantidad"])]

    def conseguir(self, ctx: Contexto, objeto: str, inv: Dict[str, float]) -> Optional[Paso]:
        """Primer paso del plan más barato para tener una unidad más de ``objeto``: la mejor de las acciones cuyo efecto
        lo da (requisitos), resuelta hacia atrás como cualquier carencia de inventario. None si nada lo da."""
        productoras = sorted((k for k, q in ctx.memoria.requisitos.items() if q.efecto.get(objeto, 0) > 0),
                             key=lambda k: (k[0].value, k[1]))
        pasos = [p for p in (self._resolver(ctx, k, inv, frozenset(), 0) for k in productoras) if p is not None]
        return min(pasos, key=lambda q: q.coste) if pasos else None

    def decidir(self, ctx: Contexto, estrategia: Optional[Pieza] = None) -> None:
        inv = inventario(ctx)
        mejor_paso: Optional[Paso] = None
        meta_mejor = ""
        for meta in ctx.memoria.metas.values():
            if meta.conseguida or meta.verbo not in self.VERBOS_PLAN:
                continue
            paso = self._resolver(ctx, (meta.verbo, meta.objetivo), inv, frozenset(), 0)
            if paso is not None and (mejor_paso is None or paso.coste < mejor_paso.coste):
                mejor_paso, meta_mejor = paso, meta.objetivo
        if mejor_paso is not None:
            self._vigilar(ctx, mejor_paso)
            motivo = "metas: " + meta_mejor + "".join(f" ← {m}" for m in mejor_paso.motivo)
            self.proponer(ctx, mejor_paso.verbo, mejor_paso.objetivo, self.AROUSAL, mejor_paso.confianza, motivo,
                          clase=mejor_paso.clase, **mejor_paso.datos)
        else:
            self._explorar_efectos(ctx)
        self._atender_peticiones(ctx, inv)

    def _atender_peticiones(self, ctx: Contexto, inv: Dict[str, float]) -> None:
        """Metas instrumentales (``Peticion``): para cada objeto pedido que falta, el primer paso para conseguirlo, con el
        arousal de quien lo pide (la urgencia de su impulso). Compite en el Tribunal con lo demás."""
        for p in self._peticiones(ctx, inv):
            objeto = str(p.carga["objeto"])
            sin = {**inv, objeto: 0.0}        # una unidad más, aunque ya se tenga alguna
            paso = self.conseguir(ctx, objeto, sin)
            if paso is None:
                continue
            motivo = f"{p.carga['origen']}: pide {objeto}" + "".join(f" ← {m}" for m in paso.motivo)
            if p.carga.get("motivo"):
                motivo += f" · {p.carga['motivo']}"
            self.proponer(ctx, paso.verbo, paso.objetivo, float(p.carga["urgencia"]), paso.confianza, motivo,
                          clase=paso.clase, **paso.datos)

    def _resolver(self, ctx: Contexto, accion: Tuple[Verbo, str], inv: Dict[str, float], visitado: frozenset,
                  prof: int) -> Optional[Paso]:
        if prof > self.PROFUNDIDAD or accion in visitado or ctx.memoria.bloqueada(*accion):
            return None
        visitado = visitado | {accion}
        mem = ctx.memoria
        r = mem.requisitos.get(accion)
        faltan_inv = {k: (n or 1) - inv.get(k, 0.0) for k, n in (r.requiere_inventario if r else {}).items()
                      if inv.get(k, 0.0) < (n or 1)}
        faltan_cerca = []
        for c in sorted(r.requiere_cerca if r else ()):
            if r is None or not any(r.cerca_basta(c, d) for d in desplazamientos_a_clase(ctx, c)):
                faltan_cerca.append(c)
        if not faltan_inv and not faltan_cerca:
            return self._ejecutar(ctx, accion, r)
        # Cada carencia necesita su propio plan; si alguna no lo tiene, la acción no es alcanzable. Se ejecuta
        # primero la carencia más barata y el coste es la suma de todas.
        planes: List[Paso] = []

        def mejor_de(opciones: List[Optional[Paso]], texto: str) -> Optional[Paso]:
            validas = [p for p in opciones if p is not None]
            if not validas:
                return None
            p = min(validas, key=lambda q: q.coste)
            p.coste += 1.0
            p.motivo.insert(0, texto)
            return p

        for item in sorted(faltan_inv):
            productoras = sorted((k for k, q in mem.requisitos.items() if q.efecto.get(item, 0) > 0), key=lambda k: (k[0].value, k[1]))
            p = mejor_de([self._resolver(ctx, k, inv, visitado, prof + 1) for k in productoras], f"falta {item}")
            if p is None:
                return None
            planes.append(p)
        for clase in faltan_cerca:
            # Ir a una que se ve o se recuerda (mapa local, con el coste de la ruta) frente a producir otra, con el coste de
            # reponer lo que consume. Así no se coloca una nueva mientras ir a la conocida cueste menos.
            colocadoras = sorted((k for k, q in mem.requisitos.items() if clase in q.aparece), key=lambda k: (k[0].value, k[1]))
            confianza = r.confianza if r else 0.5
            por_mapa = self._por_el_mapa(ctx, clase, confianza) if ctx.perfil.mecanismos.material_mapa else \
                ir_por_el_mapa(ctx, clase, confianza, self._excluir(ctx))
            opciones = [acercarse_a_clase(ctx, clase, confianza, self._excluir(ctx)), por_mapa]
            opciones += [self._con_consumo(ctx, k, self._resolver(ctx, k, inv, visitado, prof + 1), inv, visitado, prof)
                         for k in colocadoras]
            p = mejor_de(opciones, f"falta cerca {clase}")
            if p is None:
                return None
            planes.append(p)
        # Primero lo que se lleva (inventario) y después el sitio: ir junto a algo antes de tener lo que se usa allí obliga a
        # volver. El coste cuenta todas las carencias.
        primero = min(planes[:len(faltan_inv)] or planes, key=lambda q: q.coste)
        primero.coste = sum(q.coste for q in planes)
        return primero

    def _con_consumo(self, ctx: Contexto, accion: Tuple[Verbo, str], paso: Optional[Paso], inv: Dict[str, float],
                     visitado: frozenset, prof: int) -> Optional[Paso]:
        """Producir algo cuesta también reponer lo que consume: lo que su efecto aprendido resta del inventario
        (``Requisito.efecto`` negativo), por el coste de conseguir cada unidad. Sin experiencia de su efecto, nada."""
        r = ctx.memoria.requisitos.get(accion)
        if paso is None or r is None:
            return paso
        for k, d in sorted(r.efecto.items()):
            if d < 0:
                paso.coste += -d * self._coste_unidad(ctx, k, inv, visitado | {accion}, prof + 1)
        return paso

    def _coste_unidad(self, ctx: Contexto, objeto: str, inv: Dict[str, float], visitado: frozenset, prof: int) -> float:
        """Pasos estimados para conseguir una unidad de ``objeto`` desde cero (el plan más barato de sus productoras)."""
        clave = (ctx.latido, objeto)
        if clave not in self._costes_unidad:
            if len(self._costes_unidad) > 200:
                self._costes_unidad.clear()
            sin = {**inv, objeto: 0.0}
            productoras = sorted((k for k, q in ctx.memoria.requisitos.items() if q.efecto.get(objeto, 0) > 0),
                                 key=lambda k: (k[0].value, k[1]))
            pasos = [q for q in (self._resolver(ctx, k, sin, visitado, prof) for k in productoras) if q is not None]
            self._costes_unidad[clave] = min(q.coste for q in pasos) + 1.0 if pasos else COSTE_SIN_PRODUCTOR
        return self._costes_unidad[clave]

    def _por_el_mapa(self, ctx: Contexto, clase: str, confianza: float) -> Optional[Paso]:
        """``ir_por_el_mapa`` con caché por latido (el planificador la pide muchas veces por latido). Devuelve una copia.
        Solo con el interruptor ``material_mapa`` (deuda 11c)."""
        clave = (ctx.latido, clase, self._excluir(ctx))
        if clave not in self._rutas_mapa:
            if len(self._rutas_mapa) > 200:
                self._rutas_mapa.clear()
            self._rutas_mapa[clave] = ir_por_el_mapa(ctx, clase, 0.5, clave[2])
        q = self._rutas_mapa[clave]
        return None if q is None else Paso(q.verbo, q.objetivo, q.clase, q.coste, confianza, list(q.motivo), dict(q.datos), q.destino, q.distancia)

    def _ejecutar(self, ctx: Contexto, accion: Tuple[Verbo, str], r: Any) -> Optional[Paso]:
        verbo, objetivo = accion
        confianza = float(r.confianza) if r is not None else 0.5
        # Coste en intentos: 1 / tasa estimada. El primer intento ya cuenta como el paso (coste 0, como cualquier
        # acción que siempre funciona); se suman los fallos esperados antes del éxito, 1 / tasa − 1.
        penal = 1.0 / max(ctx.memoria.tasa_estimada(verbo, objetivo), 1e-6) - 1.0
        texto = f"{verbo.value} {objetivo}"
        if verbo == Verbo.USAR:
            d = delante(ctx)
            if r is not None and d is not None and d["clase"] in r.delante_fallido and r.requiere_delante:
                sitio = mejor([lugar for lugar in lugares(ctx) if lugar.rasgo("peligro") < 0.5], lambda lugar: lugar.rasgo("novedad"))
                if sitio is None:
                    return None
                return Paso(Verbo.MOVER, sitio.id, sitio.clase, 2.0 + penal, confianza, [texto, f"no sirve delante {d['clase']}"])
            return Paso(Verbo.USAR, objetivo, objetivo, penal, confianza, [texto], {"receta": objetivo})
        d = delante(ctx)
        if d is not None and d["clase"] == objetivo:
            return Paso(verbo, str(d["id"]), objetivo, penal, confianza, [texto])
        instancias = [p for p in _cosas(ctx) if p.clase == objetivo]
        cerca = [p for p in instancias if al_alcance(p)]
        if cerca:
            p = max(cerca, key=lambda q: q.rasgo("proximidad"))
            return Paso(verbo, p.id, objetivo, penal, confianza, [texto])
        if ctx.perfil.mecanismos.material_mapa:
            # Deuda 11c: ir a por ello a lo visible, a lo que recuerda la memoria topológica o a una casilla recordada del
            # mapa local de la que sale (p. ej. el material de un cierre), la de menor coste.
            opciones = [q for q in (acercarse_a_clase(ctx, objetivo, confianza, self._excluir(ctx)),
                                    self._por_el_mapa(ctx, objetivo, confianza)) if q is not None]
            ir = min(opciones, key=lambda q: q.coste) if opciones else None
        else:
            ir = acercarse_a_clase(ctx, objetivo, confianza, self._excluir(ctx))
        if ir is not None:
            ir.coste += penal
            ir.motivo.insert(0, texto)
        return ir

    def _explorar_efectos(self, ctx: Contexto) -> None:
        """5.2 c: balbuceo motor. Con calma (nada peligroso a la vista) y cada ``CADA_EXPLORACION`` latidos,
        COGER sobre lo que hay delante si en esta vida aún no se ha probado."""
        if ctx.latido % self.CADA_EXPLORACION or any(p.rasgo("peligro") > 0.0 for p in _cosas(ctx)):
            return
        d = delante(ctx)
        if d is None:
            return
        clave = (Verbo.COGER, str(d["clase"]))
        if clave in ctx.memoria.requisitos or clave in ctx.memoria.intentos:
            return
        self.proponer(ctx, Verbo.COGER, str(d["id"]), 0.3, 0.5, f"metas: probar a coger {d['clase']} (sin plan)", clase=str(d["clase"]))


SABER = "saber"
INTENSIDAD_INTENCION_DEL_MUNDO = 0.5


class Intencion(Componente):
    """El «qué» deliberado de S3 (decisión 11), frente al impulso, que surge:
    - **saber**: reducir la incertidumbre; intensidad = fracción de lo que se sabe de las clases a la
      vista que aún es hipótesis (0 si no se sabe nada de ellas);
    - las que declara el mundo (``Perfil.intenciones``), con intensidad fija: son metas sostenidas, no
      necesidades que se sacian.
    """

    tipo = "Intencion"

    def reactiva(self, ctx: Contexto) -> None:
        clases = {o.clase for o in objetos(ctx)}
        props = [p for (clase, _), p in ctx.memoria.saber.items() if clase in clases] if ctx.con_experiencia else []
        saber = sum(1 for p in props if p.estado(ctx.latido) == EstadoSaber.HIPOTESIS) / len(props) if props else 0.0
        intenciones = {SABER: saber, **dict.fromkeys(ctx.perfil.intenciones, INTENSIDAD_INTENCION_DEL_MUNDO)}
        for nombre, intensidad in intenciones.items():
            self.registrar(ctx, self.pieza(ctx, nombre, arousal=intensidad,
                                           carga={"intensidad": round(intensidad, 4), "objetivo": 0.0, "rasgo": None}))


class Feedback(Componente):
    """Feedback de S3 (decisión 5): baja del error de predicción respecto al latido anterior,
    Δ aciertos − Δ sorpresas de las expectativas de la memoria. Positivo = predice mejor. Es el
    mérito de las estrategias de S3, sea cual sea el impulso o la intención a los que sirven."""

    tipo = "Feedback"

    def reactiva(self, ctx: Contexto) -> None:
        aciertos, fallos = int(ctx.memoria.aciertos), int(ctx.memoria.fallos)
        previo = ctx.onda.ei("Feedback").get(f"feedback:{self.sistema}")
        antes = previo.carga["estado"] if previo is not None else {"aciertos": aciertos, "fallos": fallos}
        valor = float((aciertos - antes["aciertos"]) - (fallos - antes["fallos"]))
        impulsos = {**ctx.onda.ef("Impulso"), **ctx.onda.ef("Intencion")}
        self.registrar(ctx, self.pieza(ctx, f"feedback:{self.sistema}", arousal=0.0,
                                       carga={"valor": valor, "por_impulso": dict.fromkeys(impulsos, valor),
                                              "estado": {"aciertos": aciertos, "fallos": fallos}}))


def estrategias_s3() -> List[Definicion]:
    return [EvitarLoPeligroso(), ComerLoNutritivo(), CogerLoUtil(), Estudio(), PerseguirMetas()]


def crear_s3() -> Sistema:
    catalogo = Catalogo(estrategias_s3())
    return Sistema("S3", "Verdad", [
        Modulo("Sentir", [Comunicacion()]),
        Modulo("Interpretar", [Agente(), Predicado(), Proposicion(), Sentencia(), Logica(), Creencia()]),
        Modulo("Reaccionar", [Intencion(), Impulso(), Feedback(), Estrategia(catalogo)]),
        Modulo("Actuar", [Accion(catalogo)]),
    ])
