"""Ajedrez: el rival corregido juega bien y el sensor traduce las jugadas a rasgos con significado."""

import pytest

chess = pytest.importorskip("chess")

from ida.ejecutor import ejecutar  # noqa: E402
from ida.mundos.ajedrez import MundoAjedrez  # noqa: E402
from ida.mundos.ajedrez.rival import RivalLocal  # noqa: E402

DAMA_COLGADA = "rnbqkbnr/pp1ppppp/8/2p5/3Q4/8/PPP1PPPP/RNB1KBNR b KQkq - 0 1"
MATE_EN_1 = "rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2"


@pytest.mark.parametrize("dificultad", [1, 2, 3])
def test_rival_come_la_dama_y_da_mate(dificultad):
    assert RivalLocal(dificultad, semilla=1).jugar(chess.Board(DAMA_COLGADA)).uci() == "c5d4"
    assert RivalLocal(dificultad, semilla=1).jugar(chess.Board(MATE_EN_1)).uci() == "d8h4"


def test_sensor_ve_el_mate_y_el_peligro():
    m = MundoAjedrez(color="negras")
    m.tablero = chess.Board(MATE_EN_1)
    jugadas = {e.id: e for e in m.observar().entidades if e.rasgos.get("lugar")}
    assert jugadas["d8h4"].rasgos["nutritivo"] == 1.0
    # Tras 1.e4 d5, Dg4 regala la dama al alfil de c8; De2 es segura.
    m.tablero = chess.Board("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2")
    jugadas = {e.id: e for e in m.observar().entidades if e.rasgos.get("lugar")}
    assert jugadas["d1g4"].rasgos["peligro"] > 0.9
    assert jugadas["d1e2"].rasgos["peligro"] < jugadas["d1g4"].rasgos["peligro"]


def test_partida_corta(tmp_path):
    r = ejecutar("ajedrez", latidos=30, semilla=1, consola=False, datos=str(tmp_path), opciones_mundo={"dificultad": 1})[0]
    assert r["puntuacion"]["jugadas"] > 0
