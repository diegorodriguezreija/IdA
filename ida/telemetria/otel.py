"""Observabilidad con OpenTelemetry (opcional: ``pip install -e ".[observabilidad]"``), alimentada por el registro del latido.

O15: lo único que lee es el registro del latido v1 (``ida/telemetria/esquema.py``), el mismo que la consola, el directo
y la grabación; no toca el organismo ni la Onda. Lo traduce a trazas y métricas estándar y las envía por OTLP/HTTP a un
OpenTelemetry Collector (por defecto ``http://localhost:4318``, o lo que diga ``OTEL_EXPORTER_OTLP_ENDPOINT``). Con
``docker compose up`` se ven en Jaeger (trazas), Prometheus (métricas) y Grafana (panel ya montado en ``infra/``).

- **Trazas.** Cada latido es una traza: un tramo ``latido`` con un hijo por fase (percibir, sentir, preatención,
  aprender, S1, S2, S3 o dormir, actuar, cierre), con sus tiempos, y en cada fase los tiempos de sus Componentes
  (``ida.componente_ms.<clave>``). Las fases y los tiempos son campos del nivel completo (``fases``, ``tiempos_ms``):
  con ``--otel`` y sin ``--nivel``, el ejecutor observa a ese nivel. Con un nivel menor la traza es solo el tramo
  ``latido``, con la duración de la cognición (``ritmo.ms``). Si salta la guillotina, la última fase cognitiva y el
  tramo ``latido`` llevan el evento ``guillotina`` con su motivo; cada aprendizaje es un evento ``aprendizaje``.
- **Métricas de siempre** (los mismos nombres, unidades y atributos que antes de T6a: los paneles de ``infra/grafana``
  no cambian): ``ida.latido.duracion``, ``ida.fase.duracion``, ``ida.latidos``, ``ida.guillotinas``,
  ``ida.decisiones`` (sistema, verbo), ``ida.decisiones.cambiadas``, ``ida.aprendizajes``, ``ida.vidas`` (final),
  ``ida.vida.latidos`` y los indicadores ``ida.soma`` (medida), ``ida.amplitud`` (tipo), ``ida.conocimiento`` (estado)
  y ``ida.puntuacion`` (clave).
- **Métricas nuevas** (T6a, porque el registro las trae): ``ida.consumo`` (sistema, recurso: lo que gasta, rechaza o
  recorta cada sistema de la amplitud y la potencia; nivel cognitivo), ``ida.guillotinas.motivo`` (motivo),
  ``ida.hechos`` (tipo: los del catálogo de hechos v1), ``ida.potencia`` (tipo: consumida y máxima) y
  ``ida.componente.duracion`` (componente; nivel completo).

El registro de cierre (``cierre: true``, lo aprendido al morir) no es un latido: no da traza ni cuenta latidos, pero
sus hechos y aprendizajes sí cuentan.
"""

import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.metrics import CallbackOptions, Observation
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

FASES_COGNITIVAS = ("S1", "S2", "S3")
VITALES = ("vitalidad", "alimentacion", "energia", "descanso")


class Observabilidad:
    def __init__(self, mundo: str, intervalo_metricas_ms: int = 5000, procesador: Any = None, lector: Any = None,
                 reloj_ns: Any = time.time_ns):
        """``procesador`` y ``lector`` sustituyen a los exportadores OTLP (los tests usan los de memoria). ``reloj_ns``
        da el instante en que llega el registro: el latido acaba de terminar y sus fases se colocan hacia atrás desde él."""
        self.mundo = mundo
        self._reloj_ns = reloj_ns
        recurso = Resource.create({"service.name": "ida", "service.namespace": "ida", "ida.mundo": mundo})
        self._trazas = TracerProvider(resource=recurso)
        self._trazas.add_span_processor(procesador or BatchSpanProcessor(OTLPSpanExporter()))
        self._metricas = MeterProvider(
            resource=recurso,
            metric_readers=[lector or PeriodicExportingMetricReader(OTLPMetricExporter(), export_interval_millis=intervalo_metricas_ms)],
        )
        self.tracer = self._trazas.get_tracer("ida.latido")
        m = self._metricas.get_meter("ida")
        self._base: Dict[str, str] = {"mundo": mundo}
        self._ultimo: Dict[str, Any] = {}

        cubetas = [0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 25, 50, 100, 250, 1000]   # ms: las fases duran microsegundos
        # --- las de siempre (mismos nombres que los paneles de infra/grafana) ---
        self.h_latido = m.create_histogram("ida.latido.duracion", unit="ms", description="Duración total del latido",
                                           explicit_bucket_boundaries_advisory=cubetas)
        self.h_fase = m.create_histogram("ida.fase.duracion", unit="ms", description="Duración de cada fase del latido",
                                         explicit_bucket_boundaries_advisory=cubetas)
        self.c_latidos = m.create_counter("ida.latidos", description="Latidos vividos")
        self.c_guillotinas = m.create_counter("ida.guillotinas", description="Latidos cortados por la guillotina")
        self.c_decisiones = m.create_counter("ida.decisiones", description="Decisiones del Tribunal por sistema y verbo")
        self.c_cambiadas = m.create_counter("ida.decisiones.cambiadas", description="Decisiones que la experiencia cambió")
        self.c_aprendizajes = m.create_counter("ida.aprendizajes", description="Cambios de conocimiento aprendidos")
        self.c_vidas = m.create_counter("ida.vidas", description="Vidas terminadas")
        self.h_vida = m.create_histogram("ida.vida.latidos", unit="{latido}", description="Latidos vividos por vida")
        m.create_observable_gauge("ida.soma", callbacks=[self._obs_soma], description="Constantes vitales y química del cuerpo")
        m.create_observable_gauge("ida.amplitud", callbacks=[self._obs_amplitud], description="Amplitud consumida y máxima del latido")
        m.create_observable_gauge("ida.conocimiento", callbacks=[self._obs_conocimiento], description="Proposiciones por estado")
        m.create_observable_gauge("ida.puntuacion", callbacks=[self._obs_puntuacion], description="Puntuación numérica del mundo")
        # --- nuevas en T6a: lo que el registro trae y antes no se enviaba ---
        self.c_consumo = m.create_counter("ida.consumo", description="Gasto, rechazos y recortes de amplitud y potencia por sistema")
        self.c_guillotina_motivo = m.create_counter("ida.guillotinas.motivo", description="Guillotinas por motivo")
        self.c_hechos = m.create_counter("ida.hechos", description="Hechos del latido por tipo (catálogo de hechos v1)")
        self.h_componente = m.create_histogram("ida.componente.duracion", unit="ms", description="Duración de cada Componente",
                                               explicit_bucket_boundaries_advisory=cubetas)
        m.create_observable_gauge("ida.potencia", callbacks=[self._obs_potencia], description="Potencia consumida y máxima del latido")

    # --- por latido -------------------------------------------------------------------------------------------------
    def latido(self, r: Dict[str, Any]) -> None:
        """Registra un registro del latido v1 (cualquier nivel; el de cierre solo cuenta sus hechos y aprendizajes)."""
        experiencia = r.get("experiencia") or {}
        aprendizajes: List[str] = [str(t) for t in experiencia.get("aprendizaje") or []]
        hechos = [h for h in r.get("hechos") or [] if isinstance(h, dict)]
        for h in hechos:
            self.c_hechos.add(1, {**self._base, "tipo": str(h.get("tipo", "?"))})
        if aprendizajes:
            self.c_aprendizajes.add(len(aprendizajes), self._base)
        if r.get("cierre"):
            return

        ritmo = r.get("ritmo") or {}
        accion = r.get("accion") or {}
        amplitud = _par(ritmo.get("amplitud"))
        motivo = str(ritmo.get("guillotina") or "")
        guillotina = bool((r.get("onda") or {}).get("guillotina", bool(motivo)))
        fases = _fases(r.get("fases"))
        tiempos: Dict[str, float] = {k: float(v) for k, v in (r.get("tiempos_ms") or {}).items()}

        # Instantes absolutos: el latido acaba de terminar (el observador corre al final del latido).
        fin_ns = int(self._reloj_ns())
        duracion_ms = (fases[-1][2] - fases[0][1]) if fases else float(ritmo.get("ms") or 0.0)
        inicio_ns = fin_ns - int(round((fases[-1][2] if fases else duracion_ms) * 1e6))
        raiz = self.tracer.start_span("latido", start_time=inicio_ns, attributes={
            "ida.mundo": self.mundo,
            "ida.individuo": str(r.get("individuo", "")),
            "ida.latido": int(r.get("latido", 0)),
            "ida.afecto": str((r.get("afecto") or {}).get("estado", "")),
            "ida.decision.verbo": str(accion.get("verbo", "")),
            "ida.decision.objetivo": str(accion.get("objetivo", "")),
            "ida.decision.sistema": str(accion.get("sistema", "")),
            "ida.decision.motivo": str(accion.get("motivo", "")),
            "ida.experiencia_cambio": bool(experiencia.get("cambio_decision")),
            "ida.amplitud.consumida": amplitud[0],
            "ida.amplitud.maxima": amplitud[1],
            "ida.plazo_ms": float(ritmo.get("plazo_ms") or 0.0),
            "ida.guillotina": guillotina,
        })
        contexto = trace.set_span_in_context(raiz)
        ultima_cognitiva = max((i for i, f in enumerate(fases) if f[0] in FASES_COGNITIVAS), default=-1)
        for i, (nombre, ini_ms, fin_ms) in enumerate(fases):
            ini, fin_f = inicio_ns + int(round(ini_ms * 1e6)), inicio_ns + int(round(fin_ms * 1e6))
            tramo = self.tracer.start_span(nombre, context=contexto, start_time=ini)
            for clave, ms in _tiempos_de(tiempos, nombre):
                tramo.set_attribute(f"ida.componente_ms.{clave}", round(ms, 3))
            if guillotina and i == ultima_cognitiva:
                tramo.add_event("guillotina", {"motivo": motivo}, timestamp=fin_f)
            tramo.end(end_time=fin_f)
            self.h_fase.record(fin_ms - ini_ms, {**self._base, "fase": nombre})
        if guillotina:
            raiz.add_event("guillotina", {"motivo": motivo})
        for texto in aprendizajes:
            raiz.add_event("aprendizaje", {"texto": texto})
        raiz.end(end_time=fin_ns)

        self.h_latido.record(duracion_ms, self._base)
        self.c_latidos.add(1, self._base)
        if guillotina:
            self.c_guillotinas.add(1, self._base)
            self.c_guillotina_motivo.add(1, {**self._base, "motivo": motivo or "?"})
        if accion.get("verbo"):
            self.c_decisiones.add(1, {**self._base, "sistema": accion.get("sistema", "") or "?", "verbo": accion["verbo"]})
        if experiencia.get("cambio_decision"):
            self.c_cambiadas.add(1, self._base)
        for sistema, gasto in ((r.get("onda") or {}).get("consumo") or {}).items():
            for recurso, valor in (gasto or {}).items():
                if isinstance(valor, (int, float)) and not isinstance(valor, bool) and valor > 0:
                    self.c_consumo.add(float(valor), {**self._base, "sistema": str(sistema), "recurso": str(recurso)})
        for clave, ms in tiempos.items():
            self.h_componente.record(ms, {**self._base, "componente": clave})
        self._ultimo = {"r": r, "attrs": dict(self._base), "amplitud": amplitud, "potencia": _par(ritmo.get("potencia"))}

    def vida(self, latidos: int, vivo: bool) -> None:
        self.c_vidas.add(1, {**self._base, "final": "vive" if vivo else "muere"})
        self.h_vida.record(latidos, self._base)

    def cerrar(self) -> None:
        self._trazas.shutdown()
        self._metricas.shutdown()

    # --- indicadores observables (último latido) --------------------------------------------------------------------
    def _obs_soma(self, _: CallbackOptions) -> Iterable[Observation]:
        r, attrs = self._ultimo.get("r"), self._ultimo.get("attrs", {})
        if not r:
            return []
        cuerpo, quimica = r.get("cuerpo") or {}, r.get("quimica") or {}
        indicadores = (r.get("afecto") or {}).get("indicadores") or {}
        valores = {**{k: cuerpo.get(k) for k in VITALES}, **quimica, **{f"indicador_{k}": v for k, v in indicadores.items()}}
        return [Observation(float(v), {**attrs, "medida": k}) for k, v in valores.items()
                if isinstance(v, (int, float)) and not isinstance(v, bool)]

    def _obs_amplitud(self, _: CallbackOptions) -> Iterable[Observation]:
        return self._par_observado("amplitud")

    def _obs_potencia(self, _: CallbackOptions) -> Iterable[Observation]:
        return self._par_observado("potencia")

    def _par_observado(self, clave: str) -> Iterable[Observation]:
        if clave not in self._ultimo:
            return []
        consumida, maxima = self._ultimo[clave]
        attrs = self._ultimo["attrs"]
        return [Observation(consumida, {**attrs, "tipo": "consumida"}), Observation(maxima, {**attrs, "tipo": "maxima"})]

    def _obs_conocimiento(self, _: CallbackOptions) -> Iterable[Observation]:
        r, attrs = self._ultimo.get("r"), self._ultimo.get("attrs", {})
        mem = (r or {}).get("memoria", {})
        return [Observation(mem[k], {**attrs, "estado": k}) for k in ("demostradas", "hipotesis", "refutadas") if k in mem]

    def _obs_puntuacion(self, _: CallbackOptions) -> Iterable[Observation]:
        r, attrs = self._ultimo.get("r"), self._ultimo.get("attrs", {})
        punt = ((r or {}).get("score") or {}).get("puntuacion") or {}
        return [Observation(float(v), {**attrs, "clave": k}) for k, v in punt.items()
                if isinstance(v, (int, float)) and not isinstance(v, bool)]


def _par(valor: Any) -> Tuple[float, float]:
    """``[consumida, máxima]`` del registro como dos números (0 si falta)."""
    lista = list(valor) if isinstance(valor, (list, tuple)) else []
    lista += [0, 0]
    return (float(lista[0] or 0), float(lista[1] or 0))


def _fases(valor: Any) -> List[Tuple[str, float, float]]:
    """Las fases del registro (``[nombre, inicio_ms, fin_ms]`` desde el inicio del latido), en orden."""
    fases: List[Tuple[str, float, float]] = []
    for f in valor or []:
        if isinstance(f, (list, tuple)) and len(f) >= 3:
            fases.append((str(f[0]), float(f[1]), float(f[2])))
    return fases


def _tiempos_de(tiempos_ms: Dict[str, float], fase: str) -> List[Tuple[str, float]]:
    """Tiempos de los componentes que corren en una fase (``S1.Reflejo`` va en la fase ``S1``)."""
    def es_de(clave: str) -> bool:
        if clave.startswith("preatencion:"):
            return fase == "preatencion"
        sistema, _, nombre = clave.partition(".")
        if fase == "actuar":
            return sistema == "CORE" and (nombre == "Tribunal" or nombre.startswith("Actuador"))
        if fase == "sentir":
            return sistema == "MUNDO" or (sistema == "CORE" and nombre != "Tribunal" and not nombre.startswith("Actuador"))
        return sistema == fase
    return [(k, v) for k, v in tiempos_ms.items() if es_de(k)]


def metricas_de(lector: Any) -> Dict[str, Any]:
    """Las métricas de un lector en memoria por nombre (para las pruebas y para comprobar a mano)."""
    datos: Optional[Any] = lector.get_metrics_data()
    if datos is None:
        return {}
    return {m.name: m for rm in datos.resource_metrics for sm in rm.scope_metrics for m in sm.metrics}
