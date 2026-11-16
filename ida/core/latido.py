"""El latido: ensambla Core, Sistemas y mundo y ejecuta un ciclo de vida con su guillotina.

Orden de un latido:
1. Soma: metabolismo. Observación del mundo. Presupuesto del latido (frecuencia y amplitud).
2. Onda nueva: ``ei`` = ``ef`` anterior (solo lectura).
3. Core · Sentir (exento de peaje).
4. Core: aprende del efecto de la acción anterior (el cuarteto ``ei → ef``).
5. S1 → S2 → S3, con guillotina cooperativa. Si salta, se pasa directamente al paso 6.
   (Dormido: parálisis; solo sueño y vigilancia de alarmas.)
6. Core · Actuar (exento): Tribunal → actuador del mundo → ``ef["Ejecucion"]``.
7. Indicadores, memoria rápida (K piezas de mayor arousal) y episodio.
"""

import time
from typing import Any, Callable, Dict, List, Optional, cast

from ida.core.arquitectura import Componente, Contexto, Modulo, Sistema
from ida.core.azar import Azar
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.mundo import Efecto, Mundo
from ida.core.onda import Canales, LatidoAgotado, Onda
from ida.core.pieza import Episodio, Pieza
from ida.core.sentidos import Actuador, Escena, Interocepcion, Propiocepcion, Tribunal, aplicar_efecto
from ida.core.soma import Soma, VITALES
from ida.core.vocabulario import Afecto, Verbo

CANALES_SENSORES = {"Interocepcion", "Propiocepcion", "Escena"}


class Organismo:
    def __init__(
        self,
        mundo: Mundo,
        sistemas: List[Sistema],
        arquetipo: Arquetipo,
        memoria: Memoria,
        azar: Azar,
        con_experiencia: bool = True,
        biblioteca: Optional[Any] = None,
    ):
        self.mundo = mundo
        self.perfil = mundo.perfil
        self.sistemas = sistemas
        self.arquetipo = arquetipo
        self.memoria = memoria
        self.azar = azar
        self.con_experiencia = con_experiencia
        self.biblioteca = biblioteca
        self.soma = Soma(vitales_propios=tuple(VITALES) if self.perfil.vitales_propios else ())
        verbos_mundo = sorted(set(mundo.verbos()), key=lambda v: v.value)
        self.verbos = set(verbos_mundo)
        if Verbo.ESPERAR in self.verbos:
            self.verbos.add(Verbo.LEER)

        self.tribunal = Tribunal()
        self.sentir = Modulo("Sentir", [Interocepcion(), Propiocepcion(), Escena()], exento=True)
        actuadores: List[Componente] = [Actuador(v, mundo.ejecutar) for v in verbos_mundo]
        self.actuar = Modulo("Actuar", [self.tribunal, *actuadores], exento=True)
        for c in self.sentir.componentes + self.actuar.componentes:
            c.sistema = "CORE"

        # Componentes propios del mundo: se añaden a la etapa indicada ("S3.Reaccionar", "CORE.Sentir"...)
        for destino, componentes in mundo.componentes_propios().items():
            sistema, etapa = destino.split(".")
            for comp in componentes:
                comp.propio_del_mundo = True
                if sistema == "CORE" and etapa == "Sentir":
                    comp.sistema = "MUNDO"
                    self.sentir.componentes.append(comp)
                else:
                    self._sistema(sistema).añadir(etapa, comp)

        self.ciclo = 0
        self.ef_anterior: Optional[Canales] = None
        self.ultimo_efecto: Optional[Efecto] = None
        self.episodio: Optional[Episodio] = None
        self._vit_ep = self.soma.vitalidad
        self._ali_ep = self.soma.alimentacion
        self.contadores: Dict[str, int] = {"miedo": 0, "calma": 0, "hambre": 0, "guillotinas": 0, "dormido": 0}
        self._ubicacion_previa: Optional[str] = None
        self.al_dormir: Optional[Callable[["Organismo"], Any]] = None   # callback opcional (persistencia)

    def _sistema(self, nombre: str) -> Sistema:
        for s in self.sistemas:
            if s.nombre == nombre:
                return s
        raise KeyError(f"Sistema desconocido: {nombre}")

    # -----------------------------------------------------------------------
    def latir(self) -> Onda:
        self.ciclo += 1
        soma = self.soma
        soma.metabolismo()
        t_percibir = time.time_ns()
        obs = self.mundo.observar()
        t_percibido = time.time_ns()
        if obs.vitales:
            soma.sincronizar(obs.vitales)
        if obs.dormido is not None:
            soma.dormido = obs.dormido
        frecuencia, amplitud = soma.presupuesto(self.perfil.frecuencia_ms, self.perfil.amplitud)
        onda = Onda(self.ciclo, amplitud, frecuencia, self.ef_anterior)
        ctx = Contexto(
            onda,
            soma,
            self.memoria,
            self.arquetipo,
            self.azar,
            self.perfil,
            self.verbos,
            obs,
            self.con_experiencia,
            biblioteca=self.biblioteca,
        )
        onda.fases.append(("percibir", t_percibir, t_percibido))

        # 3. Sentir
        with onda.fase("sentir"):
            self.sentir.ejecutar(ctx)
        # 4. Aprender del efecto de la acción anterior (el cuarteto)
        with onda.fase("aprender"):
            self._aprender(ctx)

        # 5. Cognición (o sueño)
        if soma.dormido:
            with onda.fase("dormir"):
                self._dormir(ctx)
        else:
            try:
                for s in self.sistemas:
                    onda.control_vital(0, donde=f"antes de {s.nombre}")
                    with onda.fase(s.nombre):
                        s.latir(ctx)
            except LatidoAgotado as exc:
                onda.guillotina = True
                onda.motivo_guillotina = str(exc)
                self.contadores["guillotinas"] += 1
            if Verbo.DORMIR in self.verbos and self.perfil.duerme and min(soma.energia, soma.descanso) <= 5.0:
                self._candidato_core(ctx, Verbo.DORMIR, "agotamiento: sueño ineludible")
        onda.notas["ms_cognicion"] = round(onda.ms_transcurridos(), 2)

        # 6. Actuar
        ctx.extra.pop("efecto", None)
        with onda.fase("actuar"):
            self.actuar.ejecutar(ctx)
        if "efecto" not in ctx.extra:     # ACECHAR o ESPERAR en un mundo sin ese verbo: no se toca el mundo
            d = ctx.extra.get("decision")
            if d is not None:
                aplicar_efecto(ctx, d.carga["verbo"], d, Efecto(exito=True, mensaje="sin acción en el mundo"))
        self.ultimo_efecto = ctx.extra.get("efecto")
        ej = onda.reactiva.ef.get("Ejecucion", {}).get("Ejecucion")
        if ej is not None and not soma.dormido and ej.carga["verbo"] not in (Verbo.ACECHAR, Verbo.ESPERAR, Verbo.LEER):
            exp = self.memoria.proyectar(ej.carga["verbo"], ej.carga.get("clase", ""), self.ciclo) if self.con_experiencia else None
            if exp is not None:
                onda.notas["expectativa"] = f"espera {exp.esperado:+.1f} al {exp.verbo.value} {exp.clase}"

        # 7. Indicadores, memoria rápida y episodio
        with onda.fase("cierre"):
            self._indicadores(ctx)
            self._memoria_rapida(ctx)
            self._episodio(ctx)
        soma.agotado_previo = onda.guillotina and "amplitud" in onda.motivo_guillotina
        onda.notas["ms_total"] = round(onda.ms_transcurridos(), 2)
        self.ef_anterior = onda.reactiva.ef
        return onda

    # -----------------------------------------------------------------------
    def _candidato_core(self, ctx: Contexto, verbo: Verbo, motivo: str) -> None:
        p = Pieza(id=f"CORE:{verbo.value}:", tipo="Ejecucion", arousal=1.0, confianza=1.0,
                  carga={"verbo": verbo, "objetivo": "", "clase": "", "motivo": motivo, "datos": {}},
                  sistema="CORE", creada=ctx.latido, actualizada=ctx.latido)
        ctx.onda.reactiva.acc.setdefault("Ejecucion", {})[p.id] = p
        ctx.onda.registrar("Ejecucion", p)

    def _aprender(self, ctx: Contexto) -> None:
        ubicacion = ctx.observacion.ubicacion if ctx.observacion else ""
        if self.con_experiencia and ubicacion:
            if self._ubicacion_previa and self._ubicacion_previa != ubicacion:
                self.memoria.registrar_transicion(self._ubicacion_previa, ubicacion, ctx.latido)
            self._ubicacion_previa = ubicacion
            if ctx.observacion:
                for e in ctx.observacion.entidades:
                    if e.rasgos.get("lugar", 0.0) < 0.5 and e.rasgos.get("proximidad", 0.0) >= 0.9:
                        self.memoria.registrar_donde(e.clase, ubicacion, ctx.latido)
        previa = ctx.onda.ei("Ejecucion").get("Ejecucion")
        if previa is None or not self.con_experiencia:
            return
        c = previa.carga
        if bool(c.get("exito")) and ubicacion and c["verbo"] in (Verbo.COGER, Verbo.COMER, Verbo.USAR):
            clase_obj = c.get("obtenido") or c.get("clase") or ""
            if clase_obj:
                self.memoria.registrar_donde(clase_obj, ubicacion, ctx.latido)
        verbo = c["verbo"] if c["verbo"] not in (Verbo.ACECHAR, Verbo.LEER) else None
        ap = self.memoria.aprender(verbo, c.get("clase", ""), c.get("delta", {}), c.get("causa"), c.get("obtenido"), bool(c.get("exito")), ctx.latido)
        if ap.rpe:
            ctx.soma.error_prediccion(max(-20.0, min(20.0, ap.rpe * 2.0)))
        if ap.sorpresa:
            s = Pieza(id=f"sorpresa_{ctx.latido}", tipo="Sorpresa", arousal=0.85, carga={"rpe": round(ap.rpe, 2)}, sistema="CORE", creada=ctx.latido)
            ctx.onda.registrar("Sorpresa", s)
            ctx.onda.reactiva.ev.setdefault("Sorpresa", {})[s.id] = s   # el Core la pone en el foco sin peaje
        if ap.textos:
            ctx.onda.notas["aprendizaje"] = ap.textos

    def _aprender_de_la_muerte(self, onda: Onda) -> None:
        """El último latido no tiene sucesor: se aprende ya de la acción que acabó con la vida."""
        ej = onda.reactiva.ef.get("Ejecucion", {}).get("Ejecucion")
        if ej is None or not self.con_experiencia:
            return
        c = ej.carga
        ap = self.memoria.aprender(c["verbo"], c.get("clase", ""), c.get("delta", {}), c.get("causa"), c.get("obtenido"),
                                   bool(c.get("exito")), self.ciclo, mortal=True)
        cast(List[str], onda.notas.setdefault("aprendizaje", [])).extend(ap.textos)

    def _dormir(self, ctx: Contexto) -> None:
        """Parálisis motora. Despierta por alarma (peligro cercano, hambre crítica) o al descansar."""
        soma = self.soma
        peligro = max((p.rasgo("peligro") * p.rasgo("proximidad") for p in ctx.onda.ev("Escena").values()), default=0.0)
        if peligro >= 0.6 or soma.alimentacion <= soma.HAMBRE_CRITICA or (soma.descanso >= 95.0 and soma.energia >= 85.0):
            soma.dormido = False
            ctx.onda.notas["despierta"] = "alarma" if peligro >= 0.6 or soma.alimentacion <= soma.HAMBRE_CRITICA else "descansado"
            return
        self.contadores["dormido"] += 1
        self._candidato_core(ctx, Verbo.DORMIR if Verbo.DORMIR in self.verbos else Verbo.ESPERAR, "sigue dormido")

    def _indicadores(self, ctx: Contexto) -> None:
        onda = ctx.onda
        escena = onda.ev("Escena").values()
        peligro = max((p.rasgo("peligro") * max(p.rasgo("proximidad"), 0.3) for p in escena), default=0.0)
        sup = [p.arousal for p in onda.ev("Supervivencia").values()]
        if sup:
            peligro = max(peligro, max(sup) if ctx.soma.alimentacion > ctx.soma.HAMBRE_CRITICA else 0.0)
        cognitivas = [p.arousal for canal, piezas in onda.reactiva.ev.items() if canal not in CANALES_SENSORES for p in piezas.values()]
        tension = sum(cognitivas) / len(cognitivas) if cognitivas else 0.0
        novedad = max((p.rasgo("novedad") for p in escena), default=0.0)
        ctx.soma.actualizar_indicadores(peligro, tension, novedad)
        if ctx.soma.afecto in (Afecto.MIEDO, Afecto.PANICO):
            self.contadores["miedo"] += 1
        elif ctx.soma.afecto == Afecto.CALMA:
            self.contadores["calma"] += 1
        if ctx.soma.alimentacion <= 30:
            self.contadores["hambre"] += 1

    def _memoria_rapida(self, ctx: Contexto) -> None:
        if not self.memoria.k:
            return
        piezas = [
            {"latido": ctx.latido, "tipo": p.tipo, "id": p.id, "arousal": round(p.arousal, 3), "clase": p.clase, "sistema": p.sistema}
            for canal, d in ctx.onda.reactiva.ev.items() if canal not in ("Interocepcion", "Propiocepcion")
            for p in d.values()
        ]
        self.memoria.guardar_rapido(piezas)

    def _episodio(self, ctx: Contexto) -> None:
        """Apertura y cierre de episodios (reglas de partida de la versión limpia, §5)."""
        soma, onda = self.soma, ctx.onda
        maximo = max((p.arousal for canal, d in onda.reactiva.ev.items() if canal not in CANALES_SENSORES for p in d.values()), default=0.0)
        sorpresa = bool(onda.ev("Sorpresa"))
        ej = onda.reactiva.ef.get("Ejecucion", {}).get("Ejecucion")
        if self.episodio is None:
            d_vit = abs(soma.vitalidad - self._vit_ep)
            if maximo >= self.perfil.umbral_apertura_episodio or sorpresa or d_vit >= 2.0:
                self.episodio = Episodio(id=f"ep_{self.arquetipo.id}_{ctx.latido}", inicio=ctx.latido)
                if ctx.observacion is not None and ctx.observacion.ubicacion:
                    self.episodio.trayectoria.append(ctx.observacion.ubicacion)
                self._vit_ep, self._ali_ep = soma.vitalidad, soma.alimentacion
            else:
                self._vit_ep, self._ali_ep = soma.vitalidad, soma.alimentacion
                return
        ep = self.episodio
        ep.arousal_max = max(ep.arousal_max, maximo)
        if ctx.observacion is not None and ctx.observacion.ubicacion:
            if not ep.trayectoria or ep.trayectoria[-1] != ctx.observacion.ubicacion:
                ep.trayectoria.append(ctx.observacion.ubicacion)
        if ej is not None:
            ep.acciones.append({"latido": ctx.latido, "verbo": ej.carga["verbo"].value, "objetivo": ej.carga["objetivo"]})
        calma = maximo < 0.55 and not sorpresa and abs(soma.vitalidad - self._vit_ep) < 0.5
        longitud = ctx.latido - ep.inicio + 1
        if longitud >= self.perfil.latidos_por_episodio or calma or soma.dormido or not soma.esta_vivo:
            d_vit = soma.vitalidad - self._vit_ep
            ep.fin = ctx.latido
            ep.balance = round(d_vit + 0.5 * (soma.alimentacion - self._ali_ep), 3)
            ep.resuelto = soma.esta_vivo and d_vit >= -1.0 and ep.balance >= -2.5
            self.memoria.episodios.append(ep)
            if self.con_experiencia and self.perfil.hogar and ctx.observacion is not None:
                self.memoria.recordar_lugar(ctx.observacion.ubicacion, 1.0 if ep.resuelto and calma else -0.5)
            onda.notas["episodio"] = f"{ep.id} cerrado: balance {ep.balance:+.1f} ({'resuelto' if ep.resuelto else 'sin resolver'})"
            self.episodio = None
            self._vit_ep, self._ali_ep = soma.vitalidad, soma.alimentacion

    # -----------------------------------------------------------------------
    def vivir(self, max_latidos: int, al_latir=None) -> int:
        """Ejecuta latidos hasta la muerte, el fin del mundo o ``max_latidos``. Devuelve los latidos vividos."""
        for _ in range(max_latidos):
            t0 = time.perf_counter()
            estaba_dormido = self.soma.dormido
            onda = self.latir()
            if self.soma.dormido and not estaba_dormido:
                if self.con_experiencia:
                    self.memoria.consolidar(self.ciclo)
                if self.al_dormir:
                    self.al_dormir(self)
            if al_latir:
                al_latir(self, onda)
            if not self.soma.esta_vivo:
                self._aprender_de_la_muerte(onda)
                break
            if self.mundo.terminado():
                break
            # Cautela 1: si hay una lectura completando y espera respuesta en modo no-tiempo-real,
            # la espera bloqueante ocurre aquí, entre un latido y otro, fuera de la guillotina.
            if self.memoria.lectura_activa and not self.perfil.tiempo_real:
                reg = self.memoria.lectura_activa
                if reg.ticket and reg.latidos_dedicados >= reg.duracion_requerida:
                    while not reg.ticket.lista():
                        time.sleep(0.001)
            if self.perfil.tiempo_real:          # marcapasos: el mundo no espera
                restante = self.perfil.frecuencia_ms / 1000.0 - (time.perf_counter() - t0)
                if restante > 0:
                    time.sleep(restante)
        return self.ciclo
