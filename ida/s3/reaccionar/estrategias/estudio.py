"""Estrategia Estudio para S3."""

from typing import Optional

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.biblioteca import Consulta, ElementoConsulta, EstadoLectura, RegistroLectura
from ida.nucleo.estrategia import ConPropuestas
from ida.nucleo.pieza import Pieza, acotar
from ida.nucleo.vocabulario import Afecto, EstadoSaber, Verbo
from ida.sistemas_comun import alarma


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
                mem.fijar_lectura(None, type(self).__name__, fin=ctx.latido)
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
                    mem.fijar_lectura(None, type(self).__name__, fin=ctx.latido)
                    ctx.onda.notas["aprendizaje"] = "«deja la lectura: interrumpida»"
                    return

            # Detectar interrupción por alarma o peligro súbito
            al = alarma(ctx)
            if al is not None and al.carga.get("peligro", 0.0) >= 0.3:
                reg.estado = EstadoLectura.INTERRUMPIDO
                mem.fijar_lectura(None, type(self).__name__, fin=ctx.latido)
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
                    mem.fijar_lectura(None, type(self).__name__, fin=ctx.latido)
                    return
                elif ctx.perfil.tiempo_real:
                    if reg.latidos_dedicados >= reg.duracion_requerida + self.MAX_LATIDOS_ESPERA_TR:
                        reg.estado = EstadoLectura.SIN_RESPUESTA
                        mem.fijar_lectura(None, type(self).__name__, fin=ctx.latido)
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
                mem.fijar_lectura(reg_prev, type(self).__name__)
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
        mem.fijar_lectura(reg_nuevo, type(self).__name__)
        ctx.onda.notas["aprendizaje"] = f"«empieza a leer sobre {len(elementos_cons)} hipótesis»"
        self.proponer(
            ctx,
            Verbo.LEER,
            "biblioteca",
            arousal=0.28,
            confianza=0.60,
            motivo=f"estudio: lectura (0/{duracion})",
        )
