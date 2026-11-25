"""El latido: ensambla Core, Sistemas y mundo y ejecuta un ciclo de vida con su guillotina.

Orden de un latido:
1. Soma: metabolismo. Observación del mundo. Regulación (D12): frecuencia, amplitud y potencia.
2. Onda nueva: ``ei`` = ``ef`` anterior (solo lectura).
3. Core · Sentir (exento de peaje). Después, la preatención de S1 (D5): exenta, también dormido (``Amenaza``
   aprende y estima el peligro en las piezas; ``Saliencia`` pone el arousal).
4. Plasticidad (D6), un solo gancho ``aprender`` por fases (``Componente.fase_plasticidad``): dentro de
   ``_aprender``, los del cuerpo y los dueños de lo que se aprende del efecto; el Core aprende del efecto de la acción
   anterior (el cuarteto ``ei → ef``); después, la fase general.
5. S1 → S2 → S3, con un único fondo de amplitud y potencia gastado en ese orden. La guillotina
   solo salta por plazo; si salta, se pasa directamente al paso 6.
   (Dormido: parálisis; solo sueño y vigilancia de alarmas.)
6. Traza de elegibilidad (``marcar_elegibilidad`` de todo lo montado). Core · Actuar (exento): Tribunal → actuador
   del mundo → ``ef["Accion"]``.
7. Indicadores, memoria rápida (K piezas de mayor arousal) y episodio.
"""

import time
from collections import deque
from types import MappingProxyType
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, cast

from ida.nucleo.arquitectura import Componente, Contexto, Modulo, Preatencion, Sistema, expectativa_ejecutada, variables_proactivas
from ida.nucleo.azar import Azar
from ida.nucleo.linaje import Arquetipo
from ida.nucleo.memoria import Memoria
from ida.nucleo.mundo import Cuerpo, Efecto, Mundo
from ida.nucleo.onda import CANALES_SENSORES, AutorCore, Canales, LatidoAgotado, Onda
from ida.nucleo.pieza import Episodio, Pieza
from ida.core.actuar.actuador import aplicar_efecto
from ida.core.actuar.tribunal import Tribunal
from ida.core.montaje import montar, sistema_por_nombre
from ida.core.regulacion import Regulacion
from ida.nucleo.soma import Soma, VITALES
from ida.nucleo.vocabulario import Afecto, Verbo


class Organismo:
    # Lo que deja el montaje al nacer (``ida/core/montaje.py``, C3)
    verbos: Set[Verbo]
    regulacion: Regulacion          # CORE.Regulacion (D12): fija frecuencia, amplitud y potencia de cada latido
    tribunal: Tribunal
    sentir: Modulo
    actuar: Modulo
    cuerpo: Optional[Cuerpo]
    componentes_cuerpo: List[Componente]   # en orden de montaje; aprenden en la fase «cuerpo» (D6)
    preatencion: Preatencion
    registrados: Set[str]           # nombres de clase de todo lo montado (Componentes y definiciones de los catálogos)

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
        self.ops_por_ms: Optional[float] = None   # plazo lógico de la guillotina (``Onda``); None = reloj

        montar(self)   # al nacer: registro del mundo, opcionales, cuerpo, comprobaciones y secciones de memoria (D3, D7)

        self.ciclo = 0
        self.ef_anterior: Optional[Canales] = None
        self.estrategias: Dict[str, Pieza] = {}   # estrategias activas de S1, S2 y S3, conservadas entre latidos
        self.ultimo_efecto: Optional[Efecto] = None
        self.causa_muerte: Optional[str] = None
        self.episodio: Optional[Episodio] = None
        self._vit_ep = self.soma.vitalidad
        self._ali_ep = self.soma.alimentacion
        self.contadores: Dict[str, int] = {"miedo": 0, "calma": 0, "hambre": 0, "guillotinas": 0, "dormido": 0, "plus_decide": 0}
        self._ubicacion_previa: Optional[str] = None
        self.al_dormir: Optional[Callable[["Organismo"], Any]] = None   # callback opcional (persistencia)
        self._corto_plazo: deque[Any] = deque(maxlen=max(0, self.perfil.corto_plazo))

    @property
    def corto_plazo(self) -> Tuple[Any, ...]:
        return tuple(self._corto_plazo)

    def _sistema(self, nombre: str) -> Sistema:
        return sistema_por_nombre(self.sistemas, nombre)

    # -----------------------------------------------------------------------
    def latir(self) -> Onda:
        self.ciclo += 1
        soma = self.soma
        soma.metabolismo()
        t_percibir = time.time_ns()
        obs = self.mundo.observar()
        t_percibido = time.time_ns()
        # Excepción admitida a D4 (solo los sensores leen la Observación): sincronizar el soma con las constantes vitales y
        # el sueño que da el mundo es transducción del propio cuerpo, y va antes de la regulación (que usa el soma).
        if obs.vitales:
            soma.sincronizar(obs.vitales)
        if obs.dormido is not None:
            soma.dormido = obs.dormido
        frecuencia, amplitud, potencia = self.regulacion.ritmo(soma, self.perfil.frecuencia_ms, self.perfil.amplitud)
        onda = Onda(self.ciclo, amplitud, frecuencia, self.ef_anterior, potencia_max=potencia, estrategias=self.estrategias,
                    ops_por_ms=self.ops_por_ms)
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
            registrados=self.registrados,
            cuerpo=self.cuerpo,
            corto_plazo=tuple(self._corto_plazo),
        )
        onda.fases.append(("percibir", t_percibir, t_percibido))

        # 3. Sentir
        with onda.fase("sentir"):
            self.sentir.ejecutar(ctx)
        ctx.observacion = None   # D4: después de los sensores nadie lee la Observación; todo lo demás lee piezas
        # 3b. Preatención (D5): exenta, también dormido; solo modifica piezas de los sensores
        with onda.fase("preatencion"):
            self.preatencion.ejecutar(ctx)
        # 4. Aprender del efecto de la acción anterior (el cuarteto)
        with onda.fase("aprender"):
            self._ver_clases(ctx)
            self._aprender(ctx)
            if self.con_experiencia and self.perfil.mecanismos.expectativa:
                self._contrastar(ctx)
            self._plasticidad(ctx)

        # 5. Cognición (o sueño)
        if soma.dormido:
            with onda.fase("dormir"):
                self._dormir(ctx)
        else:
            try:
                for s in self.sistemas:
                    onda.control_vital(0, donde=f"antes de {s.nombre}")
                    cast(Dict[str, Any], onda.notas.setdefault("restante", {}))[s.nombre] = (onda.amplitud_restante(), round(onda.potencia_restante(), 3))
                    with onda.fase(s.nombre):
                        s.latir(ctx)
            except LatidoAgotado as exc:
                onda.guillotina = True
                onda.motivo_guillotina = str(exc)
                self.contadores["guillotinas"] += 1
            if Verbo.DORMIR in self.verbos and self.perfil.duerme and min(soma.energia, soma.descanso) <= 5.0:
                self._candidato_core(ctx, Verbo.DORMIR, "agotamiento: sueño ineludible")
        onda.notas["ms_cognicion"] = round(onda.ms_transcurridos(), 2)

        # 6. Actuar. Antes, la traza de elegibilidad (D6): lo presente al actuar queda marcado para el efecto
        for comp in self.montados():
            comp.marcar_elegibilidad(ctx)
        ctx.extra.pop("efecto", None)
        with onda.fase("actuar"):
            self.actuar.ejecutar(ctx)
        if "efecto" not in ctx.extra:     # ACECHAR o ESPERAR en un mundo sin ese verbo: no se toca el mundo
            d = ctx.extra.get("decision")
            if d is not None:
                aplicar_efecto(ctx, d.carga["verbo"], d, Efecto(exito=True, mensaje="sin acción en el mundo"))
        self.ultimo_efecto = ctx.extra.get("efecto")
        if onda.notas.get("plus_decide"):
            self.contadores["plus_decide"] += 1
        ej = onda.reactiva.ef.get("Accion", {}).get("Accion")
        if ej is not None and not soma.dormido and ej.carga["verbo"] not in (Verbo.ACECHAR, Verbo.ESPERAR, Verbo.LEER):
            exp = self.memoria.proyectar(ej.carga["verbo"], ej.carga.get("clase", ""), self.ciclo) if self.con_experiencia else None
            if exp is not None:
                onda.notas["expectativa"] = f"espera {exp.esperado:+.1f} al {exp.verbo.value} {exp.clase}"

        # 7. Indicadores, memoria rápida y episodio
        with onda.fase("cierre"):
            self._indicadores(ctx)
            self._memoria_rapida(ctx)
            if self.perfil.mecanismos.buffer:
                self._marcar_dia(ctx)
            self._episodio(ctx)
        soma.agotado_previo = onda.amplitud_agotada
        onda.notas["ms_total"] = round(onda.ms_transcurridos(), 2)
        self.ef_anterior = onda.reactiva.ef
        self._guardar_corto_plazo(onda)
        return onda

    def _guardar_corto_plazo(self, onda: Onda) -> None:
        if self._corto_plazo.maxlen and self._corto_plazo.maxlen > 0:
            ef_inmutable = MappingProxyType({
                c: MappingProxyType(dict(p)) for c, p in onda.reactiva.ef.items()
            })
            self._corto_plazo.append(ef_inmutable)

    # -----------------------------------------------------------------------
    def _candidato_core(self, ctx: Contexto, verbo: Verbo, motivo: str) -> None:
        p = Pieza(id=f"CORE:{verbo.value}:", tipo="Accion", arousal=1.0, confianza=1.0,
                  carga={"verbo": verbo, "objetivo": "", "clase": "", "motivo": motivo, "datos": {}},
                  sistema="CORE", creada=ctx.latido, actualizada=ctx.latido)
        ctx.onda.proponer("Accion", p, autor=AutorCore("Accion"))

    def montados(self) -> List[Componente]:
        """Todos los Componentes montados, en orden determinista: Core (Sentir, Regulación, Actuar), preatención y S1,
        S2 y S3 por módulos."""
        return [*self.sentir.componentes, self.regulacion, *self.actuar.componentes, *self.preatencion.componentes,
                *(c for s in self.sistemas for m in s.modulos for c in m.componentes)]

    def _aprenden(self, fase: str) -> List[Componente]:
        """Lo montado que aprende en ``fase`` (``Componente.fase_plasticidad``, D6), en el orden de ``montados``."""
        return [c for c in self.montados() if c.fase_plasticidad == fase]

    def _plasticidad(self, ctx: Contexto) -> None:
        """Plasticidad (D6), fase «general»: el gancho ``aprender`` de cada Componente montado que la declara, en el orden
        de ``montados``. Las fases «cuerpo» y «efecto» corren antes, dentro de ``_aprender``."""
        for c in self._aprenden("general"):
            c.aprender(ctx)

    def _ver_clases(self, ctx: Contexto) -> None:
        """Plasticidad del Core (D7): familiaridad por clase de cada entidad percibida (una pieza ``Exterocepcion`` por
        entidad, del sensor del Core). Antes la escribía el propio sensor; nadie la lee entre el Sentir y este punto."""
        if self.memoria.activa:
            for e in ctx.onda.ev("Exterocepcion").values():
                self.memoria.ver_clase(e.clase)

    def _aprender(self, ctx: Contexto) -> None:
        ubicacion = ctx.ubicacion()
        if self.con_experiencia and ubicacion:
            if self._ubicacion_previa and self._ubicacion_previa != ubicacion:
                self.memoria.registrar_transicion(self._ubicacion_previa, ubicacion, ctx.latido)
            self._ubicacion_previa = ubicacion
            for e in ctx.onda.ev("Exterocepcion").values():
                if e.rasgo("lugar") < 0.5 and e.rasgo("proximidad") >= 0.9:
                    self.memoria.registrar_donde(e.clase, ubicacion, ctx.latido)
        previa = ctx.onda.ei("Accion").get("Accion")
        if self.con_experiencia and self.memoria.activa:
            for comp in self._aprenden("cuerpo"):   # D6, fase «cuerpo» (D10; cuadrícula: ModeloDirecto, MapaLocal)
                comp.aprender(ctx)
        if previa is None or not self.con_experiencia:
            return
        c = previa.carga
        if bool(c.get("exito")) and ubicacion and c["verbo"] in (Verbo.COGER, Verbo.COMER, Verbo.USAR):
            clase_obj = c.get("obtenido") or c.get("clase") or ""
            if clase_obj:
                self.memoria.registrar_donde(clase_obj, ubicacion, ctx.latido)
        verbo = c["verbo"] if c["verbo"] not in (Verbo.ACECHAR, Verbo.LEER) else None
        for comp in self._aprenden("efecto"):   # D6, fase «efecto»: los dueños de lo que se aprende del efecto (D7; Apetencia:
            comp.aprender(ctx)                  # aliestesia; Requisito: requisitos, intentos y metas)
        ap = self.memoria.aprender(verbo, c.get("clase", ""), c.get("delta", {}), c.get("causa"), c.get("obtenido"), bool(c.get("exito")), ctx.latido)
        if ap.rpe:
            ctx.soma.error_prediccion(max(-20.0, min(20.0, ap.rpe * 2.0)))
        if ap.sorpresa:
            s = Pieza(id=f"sorpresa_{ctx.latido}", tipo="Sorpresa", arousal=0.85, carga={"rpe": round(ap.rpe, 2)}, sistema="CORE", creada=ctx.latido)
            ctx.onda.percibir("Sorpresa", s, autor=AutorCore("Sorpresa"))   # el Core la pone en el foco sin peaje
        if ap.textos:
            ctx.onda.notas["aprendizaje"] = ap.textos

    def _causa_de_muerte(self, onda: Onda) -> str:
        """Siempre una causa: la que dio el mundo (``Efecto.causa``); si no hay, la necesidad declarada
        más agotada (déficit 1), sin contar la propia salud (p. ej. «hambre»); si no, «desgaste»."""
        if self.ultimo_efecto is not None and self.ultimo_efecto.causa:
            return str(self.ultimo_efecto.causa)
        valores = {n: float(p.carga["valor"]) for n, p in onda.ev("Interocepcion").items()}
        valores.update({n: float(getattr(self.soma, n)) for n in VITALES})
        agotadas = [(d, n.nombre) for n in self.perfil.necesidades if "vitalidad" not in n.constantes
                    for d in [n.deficit(valores)] if d is not None and d >= 0.99]
        return max(agotadas)[1] if agotadas else "desgaste"

    def _contrastar(self, ctx: Contexto) -> None:
        """Bloque F, F1 (decisión 24): contrasta las expectativas que S1 y S2 dejaron en el latido anterior
        con lo que ha llegado. Aprende la transición; con error alto, la ``Sorpresa`` de siempre (por
        sistema) entra en el foco y lo percibido de esa clase gana arousal (atrae atención)."""
        onda = ctx.onda
        ahora = variables_proactivas(onda, ctx.soma, self.perfil)
        for sistema in ("S1", "S2"):
            e = expectativa_ejecutada(onda, sistema)
            if e is None:
                continue
            c = e.carga
            observado = {k: round(ahora[k] - float(b), 4) for k, b in c["base"].items() if k in ahora}
            error = self.memoria.contrastar(sistema, c["verbo"].value, c["clase"], observado, ctx.latido)
            if error is None or error < Memoria.UMBRAL_SORPRESA:
                continue
            s = Pieza(id=f"sorpresa_{sistema}_{ctx.latido}", tipo="Sorpresa", arousal=min(1.0, 0.5 + error),
                      carga={"sistema": sistema, "clase": c["clase"], "error": error}, sistema="CORE", creada=ctx.latido)
            onda.percibir("Sorpresa", s, autor=AutorCore("Sorpresa"))
            for p in list(onda.ev("Exterocepcion").values()):
                if p.clase == c["clase"]:
                    onda.modificar(p, None, arousal=min(1.0, p.arousal + 0.2 * min(1.0, error)))   # el Core, sin autor

    def _aprender_de_la_muerte(self, onda: Onda) -> None:
        """El último latido no tiene sucesor: se aprende ya de la acción que acabó con la vida."""
        ej = onda.reactiva.ef.get("Accion", {}).get("Accion")
        if ej is None or not self.con_experiencia:
            return
        c = ej.carga
        ap = self.memoria.aprender(c["verbo"], c.get("clase", ""), c.get("delta", {}), c.get("causa"), c.get("obtenido"),
                                   bool(c.get("exito")), self.ciclo, mortal=True)
        cast(List[str], onda.notas.setdefault("aprendizaje", [])).extend(ap.textos)

    def _dormir(self, ctx: Contexto) -> None:
        """Parálisis motora. Despierta por alarma (peligro cercano, hambre crítica) o al descansar."""
        soma = self.soma
        peligro = max((p.rasgo("peligro") * p.rasgo("proximidad") for p in ctx.onda.ev("Exterocepcion").values()), default=0.0)
        if peligro >= 0.6 or soma.alimentacion <= soma.HAMBRE_CRITICA or (soma.descanso >= 95.0 and soma.energia >= 85.0):
            soma.dormido = False
            ctx.onda.notas["despierta"] = "alarma" if peligro >= 0.6 or soma.alimentacion <= soma.HAMBRE_CRITICA else "descansado"
            return
        self.contadores["dormido"] += 1
        self._candidato_core(ctx, Verbo.DORMIR if Verbo.DORMIR in self.verbos else Verbo.ESPERAR, "sigue dormido")

    def _indicadores(self, ctx: Contexto) -> None:
        onda = ctx.onda
        exterocepcion = onda.ev("Exterocepcion").values()
        peligro = max((p.rasgo("peligro") * max(p.rasgo("proximidad"), 0.3) for p in exterocepcion), default=0.0)
        sup = [p.arousal for p in onda.ev("Supervivencia").values()]
        if sup:
            peligro = max(peligro, max(sup) if ctx.soma.alimentacion > ctx.soma.HAMBRE_CRITICA else 0.0)
        cognitivas = [p.arousal for canal, piezas in onda.reactiva.ev.items() if canal not in CANALES_SENSORES for p in piezas.values()]
        tension = sum(cognitivas) / len(cognitivas) if cognitivas else 0.0
        novedad = max((p.rasgo("novedad") for p in exterocepcion), default=0.0)
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

    def _marcar_dia(self, ctx: Contexto) -> None:
        """Búfer diurno (bloque E, E1): las piezas de la experiencia reactiva, puntuadas por su arousal y el
        feedback del latido (suma de los de S1, S2 y S3), y la onda resumida en el episodio del día."""
        if not self.con_experiencia or not self.memoria.activa or self.soma.dormido:
            return
        onda = ctx.onda
        feedback = sum(float(p.carga.get("valor", 0.0)) for p in onda.ef("Feedback").values())
        piezas = [
            {"latido": ctx.latido, "tipo": p.tipo, "id": p.id, "arousal": round(p.arousal, 3), "clase": p.clase, "sistema": p.sistema}
            for canal, d in onda.reactiva.ev.items() if canal not in CANALES_SENSORES
            for p in d.values()
        ]
        ej = onda.reactiva.ef.get("Accion", {}).get("Accion")
        resumen = {"verbo": ej.carga["verbo"].value, "clase": ej.carga.get("clase", ""), "exito": ej.carga.get("exito")} if ej else {}
        self.memoria.marcar(ctx.latido, piezas, feedback, resumen)

    def _episodio(self, ctx: Contexto) -> None:
        """Apertura y cierre de episodios (reglas de partida de la versión limpia, §5)."""
        soma, onda = self.soma, ctx.onda
        ubicacion = ctx.ubicacion()
        maximo = max((p.arousal for canal, d in onda.reactiva.ev.items() if canal not in CANALES_SENSORES for p in d.values()), default=0.0)
        sorpresa = bool(onda.ev("Sorpresa"))
        ej = onda.reactiva.ef.get("Accion", {}).get("Accion")
        if self.episodio is None:
            d_vit = abs(soma.vitalidad - self._vit_ep)
            if maximo >= self.perfil.umbral_apertura_episodio or sorpresa or d_vit >= 2.0:
                self.episodio = Episodio(id=f"ep_{self.arquetipo.id}_{ctx.latido}", inicio=ctx.latido)
                if ubicacion:
                    self.episodio.trayectoria.append(ubicacion)
                self._vit_ep, self._ali_ep = soma.vitalidad, soma.alimentacion
            else:
                self._vit_ep, self._ali_ep = soma.vitalidad, soma.alimentacion
                return
        ep = self.episodio
        ep.arousal_max = max(ep.arousal_max, maximo)
        if ubicacion:
            if not ep.trayectoria or ep.trayectoria[-1] != ubicacion:
                ep.trayectoria.append(ubicacion)
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
            if self.con_experiencia and self.perfil.hogar and ctx.onda.ev("Propiocepcion").get("yo") is not None:
                self.memoria.recordar_lugar(ubicacion, 1.0 if ep.resuelto and calma else -0.5)
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
                    self.memoria.consolidar(self.ciclo, reduccion=self.perfil.mecanismos.reduccion)
                    if self.perfil.mecanismos.consolidacion:
                        self.memoria.consolidar_dia(self.ciclo)
                if self.al_dormir:
                    self.al_dormir(self)
            if al_latir:
                al_latir(self, onda)
            if not self.soma.esta_vivo:
                self.causa_muerte = self._causa_de_muerte(onda)
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
        if self.con_experiencia and self.perfil.mecanismos.consolidacion and not self.perfil.duerme:
            self.memoria.consolidar_dia(self.ciclo)   # mundos sin sueño: al final de la vida o de la partida
        return self.ciclo
