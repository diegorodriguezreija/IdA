"""Ajedrez en T2b (O6, O8): escena valida y es repetible, y las opciones nuevas en su defecto dan lo de hoy."""

import inspect
from typing import Any, Dict, List

import pytest

chess = pytest.importorskip("chess")

from ida.ejecutor import ejecutar  # noqa: E402
from ida.mundos.ajedrez import MundoAjedrez  # noqa: E402
from ida.mundos.opciones import OpcionInvalida, convertir, defectos  # noqa: E402
from ida.telemetria.esquema import validar, validar_escena  # noqa: E402
from ida.telemetria.grabacion import escenas  # noqa: E402


def _vida(tmp_path, nombre: str, latidos: int = 40, semilla: int = 1, **opciones: Any) -> List[Dict[str, Any]]:
    regs: List[Dict[str, Any]] = []
    ejecutar("ajedrez", latidos=latidos, semilla=semilla, consola=False, datos=str(tmp_path / nombre), nivel="vital",
             plazo_logico=40, tabula_rasa=True, opciones_mundo=opciones, al_latir=lambda o, onda, r: regs.append(r))
    return regs


# --- escena --------------------------------------------------------------------------------------------------------

def test_escena_valida_y_coherente():
    m = MundoAjedrez()
    m.reiniciar(1)
    e = m.escena()
    assert validar_escena(e) == []
    assert (e["ancho"], e["alto"]) == (8, 8)
    assert e["yo"] == {"color": "blanco"}
    assert e["turno"] == "blanco"
    assert len(e["piezas"]) == 32
    assert e["marcas"] == []
    assert e["extra"]["fen"] == chess.STARTING_FEN
    # Rey blanco en e1: columna 4, fila 7 desde arriba
    rey_b = next(p for p in e["piezas"] if p["clase"] == "rey" and p["color"] == "blanco")
    assert (rey_b["x"], rey_b["y"]) == (4, 7)
    # Rey negro en e8: columna 4, fila 0 desde arriba
    rey_n = next(p for p in e["piezas"] if p["clase"] == "rey" and p["color"] == "negro")
    assert (rey_n["x"], rey_n["y"]) == (4, 0)


def test_escena_con_jugada_y_marcas():
    m = MundoAjedrez()
    m.reiniciar(1)
    m.tablero.push(chess.Move.from_uci("e2e4"))
    e = m.escena()
    assert validar_escena(e) == []
    assert len(e["marcas"]) == 2
    assert any(mc["x"] == 4 and mc["y"] == 6 for mc in e["marcas"])  # e2
    assert any(mc["x"] == 4 and mc["y"] == 4 for mc in e["marcas"])  # e4


def test_escena_solo_lee():
    m = MundoAjedrez()
    m.reiniciar(1)
    a = m.escena()
    b = m.escena()
    assert a == b
    assert m.tablero.fen() == chess.STARTING_FEN


def test_escena_en_el_registro_repetible(tmp_path):
    a = _vida(tmp_path, "a", latidos=30)
    b = _vida(tmp_path, "b", latidos=30)
    assert all(validar(r) == [] for r in a)
    assert "escena" in a[0]
    assert [r.get("escena") for r in a] == [r.get("escena") for r in b]
    reconstruidas = list(escenas(a))
    for anterior, r, actual in zip(reconstruidas, a[1:], reconstruidas[1:], strict=False):
        assert ("escena" in r) == (actual != anterior)
    assert all(e is not None for e in reconstruidas)


# --- opciones ------------------------------------------------------------------------------------------------------

def test_defectos_declarados_y_constructor():
    d = defectos(MundoAjedrez.opciones())
    c = inspect.signature(MundoAjedrez.__init__).parameters
    assert d["color"] == c["color"].default == "blancas"
    assert d["dificultad"] == c["dificultad"].default == 2
    assert d["elo"] == c["elo"].default == 1350
    assert d["apertura"] == c["apertura"].default == 0
    assert set(d) == {"color", "dificultad", "elo", "apertura"}


def test_opciones_de_ajedrez_fuera_de_rango():
    decl = MundoAjedrez.opciones()
    with pytest.raises(OpcionInvalida, match=r"ajedrez: opción 'dificultad': 5 fuera del rango \[0, 3\]"):
        convertir(decl, {"dificultad": "5"}, "ajedrez")
    with pytest.raises(OpcionInvalida, match=r"ajedrez: opción 'color': 'rojas' no es uno de blancas, negras"):
        convertir(decl, {"color": "rojas"}, "ajedrez")
    with pytest.raises(OpcionInvalida, match=r"ajedrez: opción 'apertura': 25 fuera del rango \[0, 20\]"):
        convertir(decl, {"apertura": "25"}, "ajedrez")


def test_opciones_nuevas_por_defecto_dan_lo_de_hoy(tmp_path):
    hoy = _vida(tmp_path, "hoy", latidos=40)
    explicitas = _vida(tmp_path, "explicitas", latidos=40, apertura=0)
    assert [r["accion"] for r in hoy] == [r["accion"] for r in explicitas]


def test_apertura_aleatoria():
    m = MundoAjedrez(apertura=4)
    m.reiniciar(1)
    assert len(m.tablero.move_stack) >= 4
