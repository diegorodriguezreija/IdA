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
from ida.core.actuar.actuador import Actuador, aplicar_efecto
from ida.core.actuar.tribunal import Tribunal
from ida.core.regulacion import Regulacion
from ida.core.sentir.ambiente import Ambiente
from ida.core.sentir.exterocepcion import Exterocepcion
from ida.core.sentir.interocepcion import Interocepcion
from ida.core.sentir.propiocepcion import Propiocepcion
from ida.nucleo.soma import Soma, VITALES
from ida.nucleo.vocabulario import Afecto, Verbo

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
        # Montaje declarado por el registro del mundo (D3)
        reg = mundo.registro()
        # Capa motora (D9): con primitivas del mundo y Motor del cuerpo, el Actuador ejecuta primitivas
        motor = reg.cuerpo.motor() if reg.cuerpo is not None else None
        disponibles = mundo.primitivas() if motor is not None else None
        if disponibles is None:
            motor = None
        actuadores: List[Componente] = [Actuador(v, mundo.ejecutar, motor, mundo.ejecutar_primitivas if motor else None, disponibles)
                                        for v in verbos_mundo]
        self.actuar = Modulo("Actuar", [self.tribunal, *actuadores], exento=True)
        for c in self.sentir.componentes + self.actuar.componentes:
            c.sistema = "CORE"

        self.cuerpo: Optional[Cuerpo] = reg.cuerpo

        # Opcionales (D3, D15): los generales con ``opcional`` que el mundo no nombra se quitan en su sitio, antes que nada
        self._montar_opcionales(reg.opcionales)

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

        # Preatención (D5): los preatentivos de S1 · Sentir, en un módulo exento que corre tras Core · Sentir. Los
        # integradores (``Saliencia``) corren siempre los últimos, sea cual sea el orden de registro (orden estable)
        self.preatencion = Preatencion(sorted((c for s in self.sistemas for c in s.preatencion), key=lambda c: c.integrador))

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

        # Plasticidad con el efecto (D6, D7): los que aprenden en ``_aprender``, en el orden de ``montados``
        self.componentes_efecto: List[Componente] = [c for c in self.montados() if c.aprende_con_efecto and not c.de_cuerpo]

        # Memoria (D7): las secciones de sus dueños (el cuerpo y después los Componentes montados, en orden), que reciben
        # al registrarse el manual y el legado que la Memoria guardó para ellas
        fuentes: List[Tuple[str, Any]] = [(reg.cuerpo.nombre, reg.cuerpo)] if reg.cuerpo is not None else []
        fuentes += [(c.__class__.__name__, c) for c in self.montados() if not c.de_cuerpo]
        for dueño, fuente in fuentes:
            declarada = fuente.seccion_memoria(self.perfil)
            if declarada is not None and self.memoria.dueño(declarada[0]) != dueño:   # una memoria ya montada por el
                self.memoria.registrar_seccion(declarada[0], dueño, declarada[1])     # mismo dueño conserva su sección

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

    def _montar_opcionales(self, nombres: List[str]) -> None:
        """Quita los generales opcionales (Componentes de los módulos, preatentivos y definiciones de los catálogos) cuya
        clase no está en ``nombres``, conservando el orden relativo de lo demás. Un nombre que no corresponde a ningún
        opcional del montaje general es un error (D3)."""
        pedidos = set(nombres)
        vistos: Set[str] = set()
        for s in self.sistemas:
            listas = [m.componentes for m in s.modulos] + [s.preatencion]
            for lista in listas:
                vistos |= {c.__class__.__name__ for c in lista if c.opcional}
                lista[:] = [c for c in lista if not c.opcional or c.__class__.__name__ in pedidos]
            catalogos = {id(c.catalogo): c.catalogo for c in s.componentes() if c.tipo == "Estrategia" and hasattr(c, "catalogo")}
            for catalogo in catalogos.values():
                for d in catalogo.todas():
                    if d.opcional:
                        vistos.add(d.__class__.__name__)
                        if d.__class__.__name__ not in pedidos:
                            catalogo.quitar(d.nombre)
        desconocidos = sorted(pedidos - vistos)
        if desconocidos:
            raise ValueError(f"Opcionales desconocidos en el registro de {self.mundo.nombre}: {desconocidos}. "
                             f"Opcionales del montaje general: {sorted(vistos)}")

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

        # 6. Actuar
        for comp in self.componentes_efecto:   # paso 2: lo que había antes de actuar (Requisito)
            comp.antes_de_actuar(ctx)
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

    def _plasticidad(self, ctx: Contexto) -> None:
        """Plasticidad (D6): el gancho ``aprender`` de cada Componente montado, en el orden de ``montados``. Los del cuerpo
        no: su ``aprender`` lo llama ``_aprender`` en su punto del latido."""
        for c in self.montados():
            if not c.de_cuerpo and not c.aprende_con_efecto:
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
            for comp in self.componentes_cuerpo:   # cuerpo (D10), en orden de montaje (cuadrícula: ModeloDirecto, MapaLocal)
                comp.aprender(ctx)
        if previa is None or not self.con_experiencia:
            return
        c = previa.carga
        if bool(c.get("exito")) and ubicacion and c["verbo"] in (Verbo.COGER, Verbo.COMER, Verbo.USAR):
            clase_obj = c.get("obtenido") or c.get("clase") or ""
            if clase_obj:
                self.memoria.registrar_donde(clase_obj, ubicacion, ctx.latido)
        verbo = c["verbo"] if c["verbo"] not in (Verbo.ACECHAR, Verbo.LEER) else None
        for comp in self.componentes_efecto:   # D6, D7: los dueños de lo que se aprende del efecto (Apetencia: aliestesia;
            comp.aprender(ctx)                 # Requisito: requisitos, intentos y metas), en el orden de ``montados``
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
