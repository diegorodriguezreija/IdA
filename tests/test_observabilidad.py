"""OpenTelemetry: cada latido es una traza con sus fases, y la guillotina se ve como un evento."""

import pytest

pytest.importorskip("opentelemetry.sdk")

from opentelemetry.sdk.metrics.export import InMemoryMetricReader  # noqa: E402
from opentelemetry.sdk.trace.export import SimpleSpanProcessor  # noqa: E402
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter  # noqa: E402

from ida.ejecutor import ejecutar  # noqa: E402
from ida.telemetria import otel  # noqa: E402


@pytest.fixture
def capturar(monkeypatch):
    spans, lector = InMemorySpanExporter(), InMemoryMetricReader()
    original = otel.Observabilidad.__init__

    def init(self, mundo, **kw):
        original(self, mundo, procesador=SimpleSpanProcessor(spans), lector=lector)

    monkeypatch.setattr(otel.Observabilidad, "__init__", init)
    return spans, lector


def _metricas(lector):
    datos = lector.get_metrics_data()
    return {m.name: m for rm in datos.resource_metrics for sm in rm.scope_metrics for m in sm.metrics}


def test_cada_latido_es_una_traza_con_sus_fases(capturar, tmp_path):
    spans, lector = capturar
    ejecutar("minimo", latidos=5, semilla=3, consola=False, datos=str(tmp_path), otel=True)
    tramos = spans.get_finished_spans()
    raices = [t for t in tramos if t.name == "latido"]
    assert len(raices) == 5
    hijos = [t.name for t in tramos if t.parent is not None and t.parent.span_id == raices[0].context.span_id]
    assert hijos == ["percibir", "sentir", "aprender", "S1", "S2", "S3", "actuar", "cierre"]
    assert raices[0].attributes["ida.decision.verbo"]
    nombres = set(_metricas(lector))
    assert {"ida.latido.duracion", "ida.fase.duracion", "ida.latidos", "ida.decisiones", "ida.soma", "ida.vidas"} <= nombres


def test_la_guillotina_se_ve_en_la_traza(capturar, tmp_path):
    from dataclasses import replace

    from ida.mundos import minimo

    spans, _ = capturar
    perfil = minimo.MundoMinimo.perfil
    try:
        minimo.MundoMinimo.perfil = replace(perfil, frecuencia_ms=0.0)
        ejecutar("minimo", latidos=3, semilla=3, consola=False, datos=str(tmp_path), otel=True)
    finally:
        minimo.MundoMinimo.perfil = perfil
    raices = [t for t in spans.get_finished_spans() if t.name == "latido"]
    assert all(t.attributes["ida.guillotina"] for t in raices)
    eventos = [e.name for t in spans.get_finished_spans() for e in t.events]
    assert "guillotina" in eventos
