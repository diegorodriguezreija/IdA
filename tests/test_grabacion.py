"""Grabación de vidas (O7): escribir, leer y comparar; y la misma vida con plazo lógico se graba igual (O11)."""

import gzip
import json

import pytest

from ida.__main__ import main
from ida.ejecutor import ejecutar
from ida.telemetria.esquema import validar
from ida.telemetria.grabacion import FORMATO, Grabacion, cabecera, comparar, iterar, leer, sin_tiempos


def _grabar(tmp_path, nombre: str, latidos: int = 60, nivel: str = "cognitivo") -> str:
    ruta = str(tmp_path / f"{nombre}.jsonl.gz")
    ejecutar("minimo", latidos=latidos, semilla=1, consola=False, datos=str(tmp_path / f"datos_{nombre}"), tabula_rasa=True,
             grabar=ruta, nivel=nivel, plazo_logico=40)
    return ruta


def test_escribir_y_leer(tmp_path):
    ruta = str(tmp_path / "a.jsonl.gz")
    cab = cabecera("minimo", "vital", semilla=3, latidos=2, opciones={"x": 1}, plazo_logico=40.0, commit="abc")
    regs = [{"v": 1, "latido": 1, "dato": [1, 2]}, {"v": 1, "latido": 2, "dato": "ñ"}]
    with Grabacion(ruta, cab) as g:
        for r in regs:
            g.escribir(r)
    assert g.registros == 2
    leida, secuencia = leer(ruta)
    assert leida == cab and secuencia == regs
    with gzip.open(ruta, "rt", encoding="utf-8") as f:
        assert len(f.read().splitlines()) == 3      # cabecera y un registro por línea


def test_leer_rechaza_lo_que_no_es_una_grabacion(tmp_path):
    ruta = str(tmp_path / "otra.jsonl.gz")
    with gzip.open(ruta, "wt", encoding="utf-8") as f:
        f.write(json.dumps({"latido": 1}) + "\n")
    with pytest.raises(ValueError):
        leer(ruta)


def test_grabar_una_vida(tmp_path):
    ruta = _grabar(tmp_path, "vida")
    cab, regs = leer(ruta)
    assert cab["formato"] == FORMATO and cab["esquema"] == 1 and cab["mundo"] == "minimo"
    assert (cab["semilla"], cab["latidos"], cab["plazo_logico"], cab["nivel"]) == (1, 60, 40, "cognitivo")
    assert "commit" in cab and "opciones" in cab and "arquetipo" in cab
    assert [r["latido"] for r in regs] == list(range(1, 61))
    assert all(validar(r) == [] for r in regs)


def test_dos_grabaciones_de_la_misma_vida_son_iguales_salvo_los_tiempos(tmp_path):
    a, b = _grabar(tmp_path, "a", nivel="completo"), _grabar(tmp_path, "b", nivel="completo")
    assert comparar(a, b) is None
    la, lb = list(iterar(a)), list(iterar(b))
    assert len(la) == len(lb) == 61
    assert [sin_tiempos(x) for x in la] == [sin_tiempos(y) for y in lb]


def test_comparar_detecta_una_diferencia(tmp_path):
    a = _grabar(tmp_path, "a", latidos=20)
    cab, regs = leer(a)
    regs[5]["accion"] = None
    b = str(tmp_path / "b.jsonl.gz")
    with Grabacion(b, cab) as g:
        for r in regs:
            g.escribir(r)
    assert comparar(a, b) == "línea 6: distinta (latido 6)"


def test_sin_tiempos_quita_solo_los_campos_de_tiempo():
    r = {"latido": 3, "ritmo": {"ms": 1.0, "ms_total": 2.0, "plazo_ms": 100.0}, "tiempos_ms": {"S1.X": 0.1}, "fases": [], "creada": "hoy"}
    assert sin_tiempos(r) == {"latido": 3, "ritmo": {"plazo_ms": 100.0}}
    assert r["ritmo"]["ms"] == 1.0          # no toca el original


def test_la_cli_graba(tmp_path, monkeypatch, capsys):
    import ida.ejecutor as ej

    monkeypatch.setattr(ej, "DATOS", str(tmp_path / "datos"))
    ruta = str(tmp_path / "cli.jsonl.gz")
    assert main(["--mundo", "minimo", "--latidos", "12", "--semilla", "2", "--cada", "5", "--nivel", "vital",
                 "--plazo-logico", "40", "--grabar", ruta]) == 0
    cab, regs = leer(ruta)
    assert cab["nivel"] == "vital" and cab["plazo_logico"] == 40 and len(regs) == 12
    assert "L0005" in capsys.readouterr().out
