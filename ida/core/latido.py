"""El latido: ensambla Core, Sistemas y mundo y ejecuta un ciclo de vida con su guillotina.

Orden de un latido:
1. Soma: metabolismo. Observación del mundo. Regulación (D12): frecuencia, amplitud y potencia.
2. Onda nueva: ``ei`` = ``ef`` anterior (solo lectura).
3. Core · Sentir (exento de peaje). Después, la preatención de S1 (D5): exenta, también dormido (``Amenaza``
   aprende y estima el peligro en las piezas; ``Saliencia`` pone el arousal).
4. Core: aprende del efecto de la acción anterior (el cuarteto ``ei → ef``); después, el gancho ``aprender`` de cada
   Componente montado (plasticidad, D6).
5. S1 → S2 → S3, con un único fondo de amplitud y potencia gastado en ese orden. La guillotina
   solo salta por plazo; si salta, se pasa directamente al paso 6.
   (Dormido: parálisis; solo sueño y vigilancia de alarmas.)
6. Core · Actuar (exento): Tribunal → actuador del mundo → ``ef["Accion"]``.
7. Indicadores, memoria rápida (K piezas de mayor arousal) y episodio.
"""

import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, cast

from ida.core.arquitectura import Componente, Contexto, Modulo, Preatencion, Sistema, expectativa_ejecutada, variables_proactivas
from ida.core.azar import Azar
from ida.core.linaje import Arquetipo
from ida.core.memoria import RADIO_PRUEBA, Desplazamiento, Memoria, desplazamiento, pos_de
from ida.core.mundo import Efecto, Mundo
from ida.core.onda import CANALES_SENSORES, AutorCore, Canales, LatidoAgotado, Onda
from ida.core.pieza import Episodio, Pieza
from ida.core.regulacion import Regulacion
from ida.core.sentidos import Actuador, Ambiente, Exterocepcion, Interocepcion, Propiocepcion, Tribunal, aplicar_efecto
from ida.core.soma import Soma, VITALES
from ida.core.vocabulario import Afecto, Verbo

DESTINOS_VALIDOS_COMPONENTES = {"CORE.Sentir"} | {
    f"{sis}.{etapa}"
    for sis in ("S1", "S2", "S3")
    for etapa in ("Sentir", "Interpretar", "Reaccionar", "Actuar")
}
DESTINOS_VALIDOS_CUERPO = DESTINOS_VALIDOS_COMPONENTES | {"CORE.Actuar"}
SISTEMAS_VALIDOS_ESTRATEGIAS = {"S1", "S2", "S3"}


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

        self.regulacion = Regulacion()       # CORE.Regulacion (D12): fija frecuencia, amplitud y potencia de cada latido
        self.regulacion.sistema = "CORE"
        self.ops_por_ms: Optional[float] = None   # plazo lógico de la guillotina (``Onda``); None = reloj
        self.tribunal = Tribunal()
        self.sentir = Modulo("Sentir", [Interocepcion(), Propiocepcion(), Exterocepcion(), Ambiente()], exento=True)
        actuadores: List[Componente] = [Actuador(v, mundo.ejecutar) for v in verbos_mundo]
        self.actuar = Modulo("Actuar", [self.tribunal, *actuadores], exento=True)
        for c in self.sentir.componentes + self.actuar.componentes:
            c.sistema = "CORE"

        # Montaje declarado por el registro del mundo (D3)
        reg = mundo.registro()

        # Cuerpo (D10): sus Componentes, antes que los del mundo, con las reglas de ``añade``
        self.componentes_cuerpo: List[Componente] = []   # en orden de montaje; su ``aprender`` lo llama ``_aprender``
        if reg.cuerpo is not None:
            for destino, comps in reg.cuerpo.componentes().items():
                if destino not in DESTINOS_VALIDOS_CUERPO:
                    raise ValueError(
                        f"Destino no válido para un Componente del cuerpo '{reg.cuerpo.nombre}': '{destino}'. "
                        f"Válidos: {sorted(DESTINOS_VALIDOS_CUERPO)}"
                    )
                modulo, preatencion, sistema_asignar = self._destino(destino)
                for comp in comps:
                    comp.de_cuerpo = reg.cuerpo.nombre
                    self._añadir(modulo, preatencion, destino, comp, sistema_asignar)
                    self.componentes_cuerpo.append(comp)

        # Componentes del registro (por destino, en el orden declarado)
        for destino, alta in reg.componentes.items():
            if destino not in DESTINOS_VALIDOS_COMPONENTES:
                raise ValueError(
                    f"Destino de componente no válido: '{destino}'. Válidos: {sorted(DESTINOS_VALIDOS_COMPONENTES)}"
                )
            modulo, preatencion, sistema_asignar = self._destino(destino)

            # sustituye: busca en el módulo de destino (o en su preatención) el Componente general cuya clase se llame como la clave
            for nombre_clase, sustituto in alta.sustituye.items():
                lista = modulo.componentes
                idx = next((i for i, c in enumerate(lista) if c.__class__.__name__ == nombre_clase), None)
                if idx is None and preatencion is not None:
                    lista = preatencion
                    idx = next((i for i, c in enumerate(lista) if c.__class__.__name__ == nombre_clase), None)
                if idx is None:
                    raise ValueError(f"No existe componente general '{nombre_clase}' en {destino} para sustituir")
                original = lista[idx]
                if sustituto.tipo != original.tipo:
                    raise ValueError(
                        f"El sustituto '{sustituto.__class__.__name__}' tiene tipo '{sustituto.tipo}', "
                        f"pero '{nombre_clase}' tiene tipo '{original.tipo}'"
                    )
                if sustituto.preatentivo != original.preatentivo:
                    raise ValueError(f"El sustituto '{sustituto.__class__.__name__}' debe ser preatentivo como '{nombre_clase}' o no serlo")
                sustituto.propio_del_mundo = True
                sustituto.sistema = sistema_asignar
                lista[idx] = sustituto

            # añade: se añade al final del módulo (los preatentivos, al final de la preatención), en el orden declarado
            for comp in alta.añade:
                self._añadir(modulo, preatencion, destino, comp, sistema_asignar)

        # Estrategias del registro (por sistema)
        for sis, alta in reg.estrategias.items():
            if sis not in SISTEMAS_VALIDOS_ESTRATEGIAS:
                raise ValueError(
                    f"Sistema no válido para estrategias: '{sis}'. Válidos: {sorted(SISTEMAS_VALIDOS_ESTRATEGIAS)}"
                )
            elige: Any = next((c for c in self._sistema(sis).componentes() if c.tipo == "Estrategia"), None)
            if elige is None:
                raise ValueError(f"{sis} no tiene componente Estrategia para las estrategias de {mundo.nombre}")
            catalogo = elige.catalogo

            # sustituye: clave es nombre de CLASE de la definición general; mismo atributo nombre; catalogo.añadir
            for nombre_clase, sustituto in alta.sustituye.items():
                original_def = next((d for d in catalogo.todas() if d.__class__.__name__ == nombre_clase), None)
                if original_def is None:
                    raise ValueError(f"No existe estrategia general de clase '{nombre_clase}' en {sis} para sustituir")
                if sustituto.nombre != original_def.nombre:
                    raise ValueError(
                        f"El sustituto '{sustituto.__class__.__name__}' tiene nombre '{sustituto.nombre}', "
                        f"pero la original '{nombre_clase}' tiene nombre '{original_def.nombre}'"
                    )
                catalogo.añadir(sustituto)

            # añade: nombre o nombre de clase repetido -> ValueError; se añade con catalogo.añadir
            for d in alta.añade:
                if catalogo.get(d.nombre) is not None:
                    raise ValueError(f"Ya existe una estrategia con nombre '{d.nombre}' en el catálogo de {sis}")
                if any(existente.__class__.__name__ == d.__class__.__name__ for existente in catalogo.todas()):
                    raise ValueError(f"Ya existe una estrategia de clase '{d.__class__.__name__}' en el catálogo de {sis}")
                catalogo.añadir(d)

        # Preatención (D5): los preatentivos de S1 · Sentir, en un módulo exento que corre tras Core · Sentir
        self.preatencion = Preatencion([c for s in self.sistemas for c in s.preatencion])

        # Conjunto de nombres de clase de todo lo montado (Componentes Core, preatención y S1-S3, y definiciones de catálogos)
        self.registrados: Set[str] = {
            c.__class__.__name__ for c in self.sentir.componentes + self.actuar.componentes + self.preatencion.componentes
        } | {
            c.__class__.__name__ for s in self.sistemas for m in s.modulos for c in m.componentes
        } | {
            d.__class__.__name__
            for s in self.sistemas
            for c in s.componentes()
            if c.tipo == "Estrategia" and hasattr(c, "catalogo")
            for d in c.catalogo.todas()
        }

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
        self._antes_accion: Optional[Tuple[Dict[str, float], Set[str], Optional[str], Dict[str, Desplazamiento]]] = None   # inv., cerca, delante, desplaz.
        self.al_dormir: Optional[Callable[["Organismo"], Any]] = None   # callback opcional (persistencia)

    def _destino(self, destino: str) -> Tuple[Modulo, Optional[List[Componente]], str]:
        """Módulo de un destino ya validado, su preatención (solo ``S1.Sentir``, D5) y el ``sistema`` que se asigna."""
        if destino == "CORE.Sentir":
            return self.sentir, None, "MUNDO"
        if destino == "CORE.Actuar":
            return self.actuar, None, "CORE"
        sis, etapa = destino.split(".")
        preatencion = self._sistema("S1").preatencion if destino == "S1.Sentir" else None
        return self._sistema(sis).modulo(etapa), preatencion, sis

    @staticmethod
    def _añadir(modulo: Modulo, preatencion: Optional[List[Componente]], destino: str, comp: Componente, sistema: str) -> None:
        """``añade`` (D3): al final del módulo (un preatentivo, al final de la preatención), con nombre de clase único."""
        if comp.preatentivo and preatencion is None:
            raise ValueError(f"'{comp.__class__.__name__}' es preatentivo: solo puede registrarse en S1.Sentir (D5)")
        lista = preatencion if comp.preatentivo and preatencion is not None else modulo.componentes
        if any(c.__class__.__name__ == comp.__class__.__name__ for c in modulo.componentes + (preatencion or [])):
            raise ValueError(f"Ya existe un componente '{comp.__class__.__name__}' en {destino}; declara sustituye")
        comp.propio_del_mundo = True
        comp.sistema = sistema
        lista.append(comp)

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
        )
        onda.fases.append(("percibir", t_percibir, t_percibido))

        # 3. Sentir
        with onda.fase("sentir"):
            self.sentir.ejecutar(ctx)
        # 3b. Preatención (D5): exenta, también dormido; solo modifica piezas de los sensores
        with onda.fase("preatencion"):
            self.preatencion.ejecutar(ctx)
        # 4. Aprender del efecto de la acción anterior (el cuarteto)
        with onda.fase("aprender"):
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

        # 6. Actuar
        self._antes_accion = self._situacion_inventario(ctx)   # paso 2: lo que había antes de actuar (requisitos)
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
        return onda

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

    def _plasticidad(self, ctx: Contexto) -> None:
        """Plasticidad (D6): el gancho ``aprender`` de cada Componente montado, en el orden de ``montados``. Los del cuerpo
        no: su ``aprender`` lo llama ``_aprender`` en su punto del latido."""
        for c in self.montados():
            if not c.de_cuerpo:
                c.aprender(ctx)

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
        previa = ctx.onda.ei("Accion").get("Accion")
        if self.con_experiencia and self.memoria.activa:
            self._aprender_mapa(ctx, previa.carga if previa is not None else None)
            for comp in self.componentes_cuerpo:   # cuerpo (D10): mapa local y modelo directo, en orden de montaje
                comp.aprender(ctx)
        if previa is None or not self.con_experiencia:
            return
        c = previa.carga
        if bool(c.get("exito")) and ubicacion and c["verbo"] in (Verbo.COGER, Verbo.COMER, Verbo.USAR):
            clase_obj = c.get("obtenido") or c.get("clase") or ""
            if clase_obj:
                self.memoria.registrar_donde(clase_obj, ubicacion, ctx.latido)
        verbo = c["verbo"] if c["verbo"] not in (Verbo.ACECHAR, Verbo.LEER) else None
        ahora_inv = self._situacion_inventario(ctx)
        objetivo = str(c.get("clase") or c.get("objetivo") or "")
        if c["verbo"] in (Verbo.USAR, Verbo.COGER) and self._antes_accion is not None and ahora_inv is not None:
            self.memoria.aprender_requisito(c["verbo"], objetivo, self._antes_accion[0], ahora_inv[0], self._antes_accion[1],
                                            bool(c.get("exito")), cerca_despues=ahora_inv[1], delante=self._antes_accion[2],
                                            distancias=self._antes_accion[3])
        if self.perfil.aliestesia:
            self._aprender_satisface(ctx, c)
        if self.memoria.metas:   # paso 5: metas del manual (solo si el mundo las declara)
            self.memoria.registrar_meta(c["verbo"], objetivo, bool(c.get("exito")),
                                        self._antes_accion[0] if self._antes_accion is not None else None,
                                        ahora_inv[0] if ahora_inv is not None else None, dict(c.get("delta", {})))
        ap = self.memoria.aprender(verbo, c.get("clase", ""), c.get("delta", {}), c.get("causa"), c.get("obtenido"), bool(c.get("exito")), ctx.latido)
        if ap.rpe:
            ctx.soma.error_prediccion(max(-20.0, min(20.0, ap.rpe * 2.0)))
        if ap.sorpresa:
            s = Pieza(id=f"sorpresa_{ctx.latido}", tipo="Sorpresa", arousal=0.85, carga={"rpe": round(ap.rpe, 2)}, sistema="CORE", creada=ctx.latido)
            ctx.onda.percibir("Sorpresa", s, autor=AutorCore("Sorpresa"))   # el Core la pone en el foco sin peaje
        if ap.textos:
            ctx.onda.notas["aprendizaje"] = ap.textos

    def _aprender_satisface(self, ctx: Contexto, c: Dict[str, Any]) -> None:
        """Paso 0b (aliestesia), aprendizaje por contingencia: qué necesidades subieron respecto al latido anterior
        (``delta`` de la interocepción; cada ``Necesidad`` declara sus constantes). Tras comer algo con éxito, cuenta
        para esa clase; en cualquier otro latido, para la línea base de cada necesidad (lo que sube sin comer)."""
        delta = {k: float(p.carga.get("delta", 0.0)) for k, p in ctx.onda.ev("Interocepcion").items()}
        subidas = {n.nombre: any(delta.get(k, 0.0) > 0.0 for k in n.constantes) for n in self.perfil.necesidades}
        if c["verbo"] == Verbo.COMER and bool(c.get("exito")) and c.get("clase"):
            self.memoria.aprender_satisface(str(c["clase"]), subidas)
        else:
            self.memoria.actualizar_linea_base(subidas)

    def _aprender_mapa(self, ctx: Contexto, c: Optional[Dict[str, Any]]) -> None:
        """Paso 3 (proteger X): mapa local, modelo del cuerpo y transformaciones, desde lo percibido.

        Necesita posiciones (ubicación ``<nombre>_x_y``) y la clase de cada casilla a la vista (``cuerpo["casillas"]``);
        sin ellas no hace nada. Antes de actualizar el mapa contrasta la acción anterior con lo que hay ahora:
        - MOVER hacia una casilla vecina de clase conocida: si la posición cambió y si quedó mirando hacia ella, según la
          casilla fuera transitable o no (modelo del cuerpo, propiocepción);
        - COGER, COMER o ATACAR sobre una vecina: si quedó mirando hacia ella;
        - COGER o USAR: si la casilla sobre la que actuó cambió de clase (la de delante, para USAR), la transformación; si la
          acción salió y la casilla no cambió, también («no la cambia»): así un primer intento real corrige lo inferido.
        """
        obs = ctx.observacion
        if obs is None:
            return
        aqui = pos_de(obs.ubicacion)
        cuerpo = obs.cuerpo or {}
        crudas = cuerpo.get("casillas")
        if aqui is None or not isinstance(crudas, dict) or not crudas:
            return
        casillas = {(int(k[0]), int(k[1])): str(v) for k, v in crudas.items()}
        o = cuerpo.get("orientacion")
        cara = (int(o[0]), int(o[1])) if isinstance(o, (list, tuple)) and len(o) == 2 else None
        mem = self.memoria
        if c is not None and mem.yo_previo is not None:
            p0, f0 = mem.yo_previo
            verbo = c["verbo"]
            if verbo == Verbo.USAR:
                destino = (p0[0] + f0[0], p0[1] + f0[1]) if f0 is not None else None
            else:
                destino = pos_de(c.get("objetivo"))
            if destino is not None and abs(destino[0] - p0[0]) + abs(destino[1] - p0[1]) == 1:
                direccion = (destino[0] - p0[0], destino[1] - p0[1])
                antes = mem.casillas.get(destino)
                if verbo == Verbo.MOVER:
                    libre = mem.transitable(antes)
                    if libre is not None:
                        mem.aprender_cuerpo("mover", libre, aqui == destino, cara == direccion)
                elif verbo in (Verbo.COGER, Verbo.COMER, Verbo.ATACAR):
                    mem.aprender_cuerpo("interactuar", True, aqui != p0, cara == direccion)
                despues = casillas.get(destino)
                cambio = antes is not None and despues is not None and antes != despues
                if verbo in (Verbo.COGER, Verbo.USAR) and antes is not None and despues is not None and (cambio or bool(c.get("exito"))):
                    objetivo = str(c.get("clase") or c.get("objetivo") or "")
                    mem.aprender_transformacion(verbo, objetivo, antes, despues)   # también «no cambió», si la acción salió
                    if cambio and verbo == Verbo.USAR and not mem.transitable_peligro(despues):
                        mem.cierres.add(destino)
                    elif cambio:
                        mem.cierres.discard(destino)
        libres, ocupadas, peligros = set(), set(), set()
        exterocepcion = ctx.onda.ev("Exterocepcion")   # el peligro (de Amenaza o del mundo) está en la pieza de cada entidad
        for e in obs.entidades:
            pos = e.datos.get("pos")
            if not isinstance(pos, (list, tuple)) or len(pos) != 2:
                continue
            p = (int(pos[0]), int(pos[1]))
            if e.rasgos.get("lugar", 0.0) >= 0.5:
                libres.add(p)
            elif e.clase != casillas.get(p):
                ocupadas.add(p)          # algo encima de la casilla (no es la propia casilla)
                pieza = exterocepcion.get(e.id)
                if pieza is not None and pieza.rasgo("peligro") >= 0.5 and e.rasgos.get("agente", 0.0) >= 0.5:
                    peligros.add(p)
        mem.ver_casillas(aqui, casillas, libres, ocupadas, peligros)
        mem.yo_previo = (aqui, cara)

    @staticmethod
    def _situacion_inventario(ctx: Contexto) -> Optional[Tuple[Dict[str, float], Set[str], Optional[str], Dict[str, Desplazamiento]]]:
        """Inventario percibido, clases al alcance (no lugares) y clase de lo que hay delante (``cuerpo["delante"]``,
        si el mundo lo da), si el mundo da inventario. Para los requisitos y las metas."""
        obs = ctx.observacion
        if obs is None or obs.inventario is None:
            return None
        cerca = {e.clase for e in obs.entidades if e.rasgos.get("lugar", 0.0) < 0.5 and e.rasgos.get("proximidad", 0.0) >= 0.9}
        delante = (obs.cuerpo or {}).get("delante")
        return (dict(obs.inventario), cerca, (str(delante.get("clase")) if isinstance(delante, dict) and delante.get("clase") else None),
                Organismo._distancias(obs))

    @staticmethod
    def _distancias(obs: Any) -> Dict[str, Desplazamiento]:
        """Desplazamiento ``(|dx|, |dy|)`` ordenado a la instancia más cercana de cada clase, hasta ``RADIO_PRUEBA``
        casillas (a igual distancia, el más diagonal). Con posiciones (ubicación ``<nombre>_x_y`` y ``datos["pos"]``)
        se calcula; sin ellas, lo que está al alcance (proximidad ≥ 0,9) cuenta como (0, 1)."""
        partes = str(obs.ubicacion).rsplit("_", 2)
        aqui = (int(partes[1]), int(partes[2])) if len(partes) == 3 and all(x.lstrip("-").isdigit() for x in partes[1:]) else None
        dist: Dict[str, Desplazamiento] = {}
        for e in obs.entidades:
            if e.rasgos.get("lugar", 0.0) >= 0.5:
                continue
            pos = e.datos.get("pos")
            if aqui is not None and isinstance(pos, (list, tuple)) and len(pos) == 2:
                d = desplazamiento(int(pos[0]) - aqui[0], int(pos[1]) - aqui[1])
            elif e.rasgos.get("proximidad", 0.0) >= 0.9:
                d = (0, 1)
            else:
                continue
            previo = dist.get(e.clase)
            if sum(d) <= RADIO_PRUEBA and (previo is None or (sum(d), -d[0]) < (sum(previo), -previo[0])):
                dist[e.clase] = d
        return dist

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
        maximo = max((p.arousal for canal, d in onda.reactiva.ev.items() if canal not in CANALES_SENSORES for p in d.values()), default=0.0)
        sorpresa = bool(onda.ev("Sorpresa"))
        ej = onda.reactiva.ef.get("Accion", {}).get("Accion")
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
