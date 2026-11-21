"""Comparación pareada de ``resumen_evaluacion.py``: episodio a episodio sobre la misma semilla base."""

import os
import sys
from typing import Any, Dict, List

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "herramientas"))

import resumen_evaluacion as rv  # noqa: E402


def _json(logros_por_ep: List[List[str]], semilla: int = 31) -> Dict[str, Any]:
    return {"semilla_base": semilla, "tasas_logros": {"a": 0.0, "b": 0.0},
            "por_episodio": [{"logros": lg} for lg in logros_por_ep]}


def test_iguales_dan_cero_sin_excluirlo():
    x = _json([["a"], [], ["a", "b"], ["b"]])
    r = rv.comparar_pareado(x, x, n_boot=200)
    assert r["score"]["diferencia"] == 0.0 and r["score"]["ic"] == (0.0, 0.0) and not r["score"]["excluye_cero"]


def test_empareja_los_primeros_min_episodios():
    a = _json([["a"]] * 6)
    b = _json([[]] * 4)
    r = rv.comparar_pareado(a, b, n_boot=200)
    assert r["episodios_pareados"] == 4
    assert r["logros"]["a"]["diferencia"] == 100.0 and r["logros"]["a"]["excluye_cero"]
    assert r["score"]["excluye_cero"]


def test_rechaza_semillas_distintas_o_sin_por_episodio():
    with pytest.raises(ValueError):
        rv.comparar_pareado(_json([["a"]]), _json([["a"]], semilla=32))
    viejo = {"semilla_base": 31, "tasas_logros": {"a": 0.0}}
    with pytest.raises(ValueError, match="por_episodio"):
        rv.comparar_pareado(viejo, _json([["a"]]))
