"""OpenTelemetry sobre el registro del latido (O15): cada latido es una traza con sus fases, la guillotina se ve como un
evento, las métricas de siempre conservan sus nombres (los paneles de infra/grafana) y hay las nuevas que el registro
permite (consumo por sistema, guillotina por motivo, hechos por tipo). Con el exportador en memoria del SDK."""

import json
import os

import pytest

pytest.importorskip("opentelemetry.sdk")

from opentelemetry.sdk.metrics.export import InMemoryMetricReader  # noqa: E402
from opentelemetry.sdk.trace.export import SimpleSpanProcessor  # noqa: E402
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter  # noqa: E402

from ida.ejecutor import ejecutar  # noqa: E402
from ida.telemetria import otel  # noqa: E402

# Las métricas que había antes de T6a (las que usan los paneles de infra/grafana/dashboards/ida.json).
METRICAS_DE_SIEMPRE = {"ida.latido.duracion", "ida.fase.duracion", "ida.latidos", "ida.guillotinas", "ida.decisiones",
                       "ida.decisiones.cambiadas", "ida.aprendizajes", "ida.vidas", "ida.vida.latidos", "ida.soma",
                       "ida.amplitud", "ida.conocimiento", "ida.puntuacion"}
METRICAS_NUEVAS = {"ida.consumo", "ida.guillotinas.motivo", "ida.hechos", "ida.componente.duracion", "ida.potencia"}


@pytest.fixture
def capturar(monkeypatch):
    spans, lector = InMemorySpanExporter(), InMemoryMetricReader()
    original = otel.Observabilidad.__init__

    def init(self, mundo, **kw):
        original(self, mundo, procesador=SimpleSpanProcessor(spans), lector=lector)

    monkeypatch.setattr(otel.Observabilidad, "__init__", init)
    return spans, lector


def _puntos(metrica):
    return list(metrica.data.data_points)


def test_cada_latido_es_una_traza_con_sus_fases(capturar, tmp_path):
    spans, lector = capturar
    ejecutar("minimo", latidos=5, semilla=3, consola=False, datos=str(tmp_path), otel=True)
    tramos = spans.get_finished_spans()
    raices = [t for t in tramos if t.name == "latido"]
    assert len(raices) == 5
    hijos = [t for t in tramos if t.parent is not None and t.parent.span_id == raices[0].context.span_id]
    assert [t.name for t in hijos] == ["percibir", "sentir", "preatencion", "aprender", "S1", "S2", "S3", "actuar", "cierre"]
    assert all(raices[0].start_time <= t.start_time <= t.end_time <= raices[0].end_time for t in hijos)
    assert raices[0].attributes["ida.decision.verbo"] and raices[0].attributes["ida.latido"] == 1
    assert any(k.startswith("ida.componente_ms.") for t in hijos for k in t.attributes)
    nombres = set(otel.metricas_de(lector))
    assert {"ida.latido.duracion", "ida.fase.duracion", "ida.latidos", "ida.decisiones", "ida.soma", "ida.vidas"} <= nombres


def test_la_guillotina_se_ve_en_la_traza(capturar, tmp_path):
    from dataclasses import replace

    from ida.mundos import minimo

    spans, lector = capturar
    perfil = minimo.MundoMinimo.perfil
    try:
        minimo.MundoMinimo.perfil = replace(perfil, frecuencia_ms=0.0)
        ejecutar("minimo", latidos=3, semilla=3, consola=False, datos=str(tmp_path), otel=True)
    finally:
        minimo.MundoMinimo.perfil = perfil
    raices = [t for t in spans.get_finished_spans() if t.name == "latido"]
    assert all(t.attributes["ida.guillotina"] for t in raices)
    eventos = [e for t in spans.get_finished_spans() for e in t.events if e.name == "guillotina"]
    assert eventos and all(e.attributes["motivo"] for e in eventos)
    motivos = _puntos(otel.metricas_de(lector)["ida.guillotinas.motivo"])
    assert sum(p.value for p in motivos) == 3 and all(p.attributes["motivo"] for p in motivos)


def test_metricas_de_siempre_y_nuevas_desde_el_registro(capturar, tmp_path):
    """Las de siempre con sus nombres y atributos, y las nuevas: consumo por sistema, hechos por tipo, potencia y tiempo
    por Componente. Los valores salen del registro (se comparan con el de una grabación de la misma vida)."""
    from ida.telemetria.grabacion import leer

    spans, lector = capturar
    ruta = str(tmp_path / "g.jsonl.gz")
    ejecutar("minimo", latidos=40, semilla=3, consola=False, datos=str(tmp_path / "m"), otel=True, plazo_logico=40, grabar=ruta)
    _, regs = leer(ruta)
    m = otel.metricas_de(lector)
    sin_guillotina = {"ida.guillotinas", "ida.guillotinas.motivo"}   # esta vida no tiene: se ven en el test de la guillotina
    assert not any(r["ritmo"]["guillotina"] for r in regs)
    assert (METRICAS_DE_SIEMPRE | METRICAS_NUEVAS) - sin_guillotina <= set(m)
    assert sum(p.value for p in _puntos(m["ida.latidos"])) == 40
    tipos = {p.attributes["tipo"]: p.value for p in _puntos(m["ida.hechos"])}
    esperados: dict = {}
    for r in regs:
        for h in r["hechos"]:
            esperados[h["tipo"]] = esperados.get(h["tipo"], 0) + 1
    assert tipos == esperados and "nace" in tipos
    consumo = {(p.attributes["sistema"], p.attributes["recurso"]) for p in _puntos(m["ida.consumo"])}
    assert consumo and {s for s, _ in consumo} <= {"S1", "S2", "S3"}
    soma = {p.attributes["medida"] for p in _puntos(m["ida.soma"])}
    assert {"vitalidad", "alimentacion", "energia", "descanso", "dopamina", "placer", "estres"} <= soma
    assert any(k.startswith("indicador_") for k in soma)
    assert {p.attributes["tipo"] for p in _puntos(m["ida.potencia"])} == {"consumida", "maxima"}
    assert {p.attributes["componente"] for p in _puntos(m["ida.componente.duracion"])} >= set(regs[0]["tiempos_ms"])
    assert {p.attributes["clave"] for p in _puntos(m["ida.puntuacion"])}
    decisiones = sum(p.value for p in _puntos(m["ida.decisiones"]))
    assert decisiones == sum(1 for r in regs if not r.get("cierre") and (r["accion"] or {}).get("verbo"))


def test_otel_solo_lee_el_registro():
    """Un registro sin Onda ni organismo basta (O15). Con un nivel sin fases, la traza es solo el tramo «latido» con la
    duración de la cognición; el de cierre no es un latido, pero sus hechos cuentan."""
    spans, lector = InMemorySpanExporter(), InMemoryMetricReader()
    o = otel.Observabilidad("minimo", procesador=SimpleSpanProcessor(spans), lector=lector, reloj_ns=lambda: 10_000_000_000)
    base = {"v": 1, "nivel": "vital", "latido": 4, "vida": 1, "generacion": 1, "individuo": "Minimo_G1", "mundo": "minimo",
            "con_experiencia": True, "ritmo": {"ms": 2.5, "ms_total": 3.0, "plazo_ms": 50.0, "amplitud": [3, 7],
                                                "potencia": [0.4, 1.0], "guillotina": "", "logico": True},
            "cuerpo": {"vitalidad": 90.0, "alimentacion": 50.0, "energia": 40.0, "descanso": 30.0}, "quimica": {"estres": 0.1},
            "afecto": {"estado": "CALMA", "indicadores": {"peligro": 0.0}}, "accion": {"verbo": "MOVER", "sistema": "S1"},
            "score": {"puntuacion": {"comida": 2, "vivo": True}}, "hechos": [{"tipo": "logro", "nombre": "x"}],
            "experiencia": {"aprendizaje": ["a"], "cambio_decision": False}, "memoria": {"demostradas": 1}}
    o.latido(base)
    o.latido(dict(base, cierre=True, hechos=[{"tipo": "aprende"}], experiencia={"aprendizaje": ["b", "c"]}))
    tramos = spans.get_finished_spans()
    assert [t.name for t in tramos] == ["latido"]
    assert tramos[0].end_time == 10_000_000_000 and tramos[0].end_time - tramos[0].start_time == 2_500_000
    m = otel.metricas_de(lector)
    assert sum(p.value for p in _puntos(m["ida.latidos"])) == 1
    assert {p.attributes["tipo"]: p.value for p in _puntos(m["ida.hechos"])} == {"logro": 1, "aprende": 1}
    assert sum(p.value for p in _puntos(m["ida.aprendizajes"])) == 3
    assert {p.attributes["clave"] for p in _puntos(m["ida.puntuacion"])} == {"comida"}   # sin booleanos
    o.cerrar()


def test_el_panel_de_grafana_solo_usa_metricas_que_siguen():
    """Los paneles de infra/grafana consultan métricas con los nombres de siempre (Prometheus cambia «.» por «_»)."""
    ruta = os.path.join(os.path.dirname(os.path.dirname(__file__)), "infra", "grafana", "dashboards", "ida.json")
    if not os.path.exists(ruta):
        pytest.skip("sin infra/ en esta copia")
    with open(ruta, encoding="utf-8") as f:
        texto = json.dumps(json.load(f))
    prometheus = {n.replace(".", "_") for n in METRICAS_DE_SIEMPRE}
    import re
    usadas = set(re.findall(r"\b(ida_[a-z_]+?)(?:_total|_milliseconds_bucket|_sum|_count|_bucket)?\{", texto))
    assert usadas and all(any(u == p or u.startswith(p) for p in prometheus) for u in usadas), usadas
