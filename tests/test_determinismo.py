"""Herramienta de evaluación de Crafter: la verificación de determinismo detecta dos ejecuciones distintas."""

import argparse
import os
import sys
from typing import Any, List

import pytest

pytest.importorskip("crafter")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "herramientas"))

import evaluar_crafter as ev  # noqa: E402


def _args() -> argparse.Namespace:
    return argparse.Namespace(verificar_determinismo=10, semilla=31, perfil="Equilibrado", vista="oficial", longitud=10000,
                              sin_estrategias_propias=True, sin_herencia=True, manual="estricto", mecanismos=[],
                              plazo_logico=None, contar="entorno")


def _falso(trazas: List[List[Any]]) -> Any:
    llamadas = iter(trazas)

    def evaluar(*a: Any, traza: List[Any], **k: Any) -> dict:
        traza.extend(next(llamadas))
        return {"latidos_cortados": 0}
    return evaluar


def test_iguales_da_cero(monkeypatch):
    t = [(1, 1, "MOVER", "celda_1_1"), (1, 2, "COGER", "arbol_2_2")]
    monkeypatch.setattr(ev, "evaluar", _falso([t, list(t)]))
    assert ev.verificar_determinismo(_args()) == 0


def test_distintas_da_uno(monkeypatch):
    a = [(1, 1, "MOVER", "celda_1_1"), (1, 2, "COGER", "arbol_2_2")]
    b = [(1, 1, "MOVER", "celda_1_1"), (1, 2, "MOVER", "celda_1_2")]
    monkeypatch.setattr(ev, "evaluar", _falso([a, b]))
    assert ev.verificar_determinismo(_args()) == 1


def test_una_vida_corta_real_es_determinista():
    assert ev.verificar_determinismo(argparse.Namespace(**{**vars(_args()), "verificar_determinismo": 60})) == 0
