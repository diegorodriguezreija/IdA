"""Observabilidad con OpenTelemetry (opcional: ``pip install -e ".[observabilidad]"``).

Traduce lo que el latido ya apunta a trazas y métricas estándar, y las envía por OTLP/HTTP a un
OpenTelemetry Collector (por defecto ``http://localhost:4318``, o lo que diga
``OTEL_EXPORTER_OTLP_ENDPOINT``). Con ``docker compose up`` se ven en Jaeger (trazas),
Prometheus (métricas) y Grafana (panel ya montado).

- **Trazas.** Cada latido es una traza: un tramo ``latido`` con un hijo por fase (percibir,
  sentir, aprender, S1, S2, S3 o dormir, actuar, cierre), con sus tiempos reales. Si salta la
  guillotina, el tramo de la fase cortada lleva el evento ``guillotina`` y las fases cognitivas
  siguientes no existen: se ve el corte en la cascada.
- **Métricas.** Duración del latido y de cada fase, guillotinas, decisiones por sistema y por
  verbo, decisiones cambiadas por la experiencia, aprendizajes, constantes vitales, estrés,
  amplitud, proposiciones por estado, puntuación numérica del mundo y vidas terminadas.

El núcleo no sabe nada de esto: solo apunta sus fases en la Onda (``Onda.fases``).
"""

from typing import Any, Dict, Iterable, List, Tuple

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


class Observabilidad:
    def __init__(self, mundo: str, intervalo_metricas_ms: int = 5000, procesador: Any = None, lector: Any = None):
        """``procesador`` y ``lector`` sustituyen a los exportadores OTLP (los tests usan los de memoria)."""
        self.mundo = mundo
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

    # --- por latido -------------------------------------------------------------------------
    def latido(self, onda: Any, r: Dict[str, Any]) -> None:
        """Registra un latido. ``r`` es el resumen de ``consola.resumen_latido`` (con memoria y puntuación)."""
        fases: List[Tuple[str, int, int]] = list(onda.fases)
        if not fases:
            return
        attrs = dict(self._base)   # sin el individuo: los indicadores son del que vive ahora
        decision = r.get("decision", {})
        inicio, fin = fases[0][1], fases[-1][2]
        raiz = self.tracer.start_span("latido", start_time=inicio, attributes={
            "ida.mundo": self.mundo,
            "ida.individuo": r.get("individuo", ""),
            "ida.latido": onda.ciclo,
            "ida.afecto": r.get("afecto", ""),
            "ida.decision.verbo": decision.get("verbo", ""),
            "ida.decision.objetivo": str(decision.get("objetivo", "")),
            "ida.decision.sistema": decision.get("sistema", ""),
            "ida.decision.motivo": r.get("motivo", ""),
            "ida.experiencia_cambio": bool(r.get("experiencia", {}).get("cambio_decision")),
            "ida.amplitud.consumida": onda.amplitud_consumida,
            "ida.amplitud.maxima": onda.amplitud_max,
            "ida.plazo_ms": onda.frecuencia_ms,
            "ida.guillotina": onda.guillotina,
        })
        contexto = trace.set_span_in_context(raiz)
        ultima_cognitiva = max((i for i, f in enumerate(fases) if f[0] in FASES_COGNITIVAS), default=-1)
        for i, (nombre, ini, fin_f) in enumerate(fases):
            tramo = self.tracer.start_span(nombre, context=contexto, start_time=ini)
            for clave, ms in _tiempos_de(onda.tiempos_ms, nombre):
                tramo.set_attribute(f"ida.componente_ms.{clave}", round(ms, 3))
            if onda.guillotina and i == ultima_cognitiva:
                tramo.add_event("guillotina", {"motivo": onda.motivo_guillotina}, timestamp=fin_f)
            tramo.end(end_time=fin_f)
            self.h_fase.record((fin_f - ini) / 1e6, {**self._base, "fase": nombre})
        if onda.guillotina:
            raiz.add_event("guillotina", {"motivo": onda.motivo_guillotina})
        for texto in r.get("experiencia", {}).get("aprendizaje", []):
            raiz.add_event("aprendizaje", {"texto": texto})
        raiz.end(end_time=fin)

        self.h_latido.record((fin - inicio) / 1e6, self._base)
        self.c_latidos.add(1, self._base)
        if onda.guillotina:
            self.c_guillotinas.add(1, self._base)
        if decision.get("verbo"):
            self.c_decisiones.add(1, {**self._base, "sistema": decision.get("sistema", "") or "?", "verbo": decision["verbo"]})
        if r.get("experiencia", {}).get("cambio_decision"):
            self.c_cambiadas.add(1, self._base)
        n_apr = len(r.get("experiencia", {}).get("aprendizaje", []))
        if n_apr:
            self.c_aprendizajes.add(n_apr, self._base)
        self._ultimo = {"r": r, "attrs": attrs, "onda": (onda.amplitud_consumida, onda.amplitud_max)}

    def vida(self, latidos: int, vivo: bool) -> None:
        self.c_vidas.add(1, {**self._base, "final": "vive" if vivo else "muere"})
        self.h_vida.record(latidos, self._base)

    def cerrar(self) -> None:
        self._trazas.shutdown()
        self._metricas.shutdown()

    # --- indicadores observables (último latido) ---------------------------------------------
    def _obs_soma(self, _: CallbackOptions) -> Iterable[Observation]:
        r, attrs = self._ultimo.get("r"), self._ultimo.get("attrs", {})
        if not r:
            return []
        valores = {**r.get("soma", {}), **{f"indicador_{k}": v for k, v in r.get("indicadores", {}).items()}}
        return [Observation(float(v), {**attrs, "medida": k}) for k, v in valores.items() if isinstance(v, (int, float))]

    def _obs_amplitud(self, _: CallbackOptions) -> Iterable[Observation]:
        if "onda" not in self._ultimo:
            return []
        consumida, maxima = self._ultimo["onda"]
        attrs = self._ultimo["attrs"]
        return [Observation(consumida, {**attrs, "tipo": "consumida"}), Observation(maxima, {**attrs, "tipo": "maxima"})]

    def _obs_conocimiento(self, _: CallbackOptions) -> Iterable[Observation]:
        r, attrs = self._ultimo.get("r"), self._ultimo.get("attrs", {})
        mem = (r or {}).get("memoria", {})
        return [Observation(mem[k], {**attrs, "estado": k}) for k in ("demostradas", "hipotesis", "refutadas") if k in mem]

    def _obs_puntuacion(self, _: CallbackOptions) -> Iterable[Observation]:
        r, attrs = self._ultimo.get("r"), self._ultimo.get("attrs", {})
        punt = (r or {}).get("puntuacion", {})
        return [Observation(float(v), {**attrs, "clave": k}) for k, v in punt.items()
                if isinstance(v, (int, float)) and not isinstance(v, bool)]


def _tiempos_de(tiempos_ms: Dict[str, float], fase: str) -> List[Tuple[str, float]]:
    """Tiempos de los componentes que corren en una fase (``S1.Reflejo`` va en la fase ``S1``)."""
    def es_de(clave: str) -> bool:
        sistema, _, nombre = clave.partition(".")
        if fase == "actuar":
            return sistema == "CORE" and (nombre == "Tribunal" or nombre.startswith("Actuador"))
        if fase == "sentir":
            return sistema == "MUNDO" or (sistema == "CORE" and nombre != "Tribunal" and not nombre.startswith("Actuador"))
        return sistema == fase
    return [(k, v) for k, v in tiempos_ms.items() if es_de(k)]
