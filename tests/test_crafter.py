"""Crafter: observación con rasgos, sueño sincronizado con el juego y reglas de éxito de COMER y COGER."""

import pytest

pytest.importorskip("crafter")

from ida.core.vocabulario import RASGOS, Verbo  # noqa: E402
from ida.ejecutor import ejecutar  # noqa: E402
from ida.mundos.crafter import MundoCrafter  # noqa: E402


@pytest.fixture
def mundo():
    m = MundoCrafter()
    m.reiniciar(1)
    return m


def test_observacion_y_aliestesia(mundo):
    obs = mundo.observar()
    assert obs.vitales and obs.dormido is False
    assert all(set(e.rasgos) <= set(RASGOS) for e in obs.entidades)
    assert any(e.rasgos.get("lugar") for e in obs.entidades)
    assert all(set(e.rasgos) <= {"proximidad", "agente", "lugar"} for e in obs.entidades)   # en bruto (A4)
    assert MundoCrafter.perfil.rasgos_declarados == ()


def test_dormido_lo_decide_el_juego(mundo):
    mundo.jugador.inventory["energy"] = 3
    mundo.ejecutar_primitivas(["sleep"], Verbo.DORMIR)
    assert mundo.observar().dormido is True


def test_coger_sin_obtener_nada_no_es_exito(mundo):
    from ida.core.pieza import Pieza
    from ida.cuerpos.cuadricula import MotorCuadricula
    intencion = Pieza(id="decision", tipo="Decision", carga={"verbo": Verbo.COGER, "objetivo": "suelo_0_0"})
    ef = mundo.ejecutar_primitivas(["do"], Verbo.COGER)
    assert ef.exito is True                                  # el adaptador ya no juzga
    assert set(ef.medidas) == {"inventario_antes", "inventario_despues", "objetos"}
    assert MotorCuadricula().juzgar(intencion, ["do"], ef) is False


def test_vida_corta_en_crafter(tmp_path):
    r = ejecutar("crafter", latidos=80, semilla=3, consola=False, datos=str(tmp_path))[0]
    assert r["latidos"] > 0 and "logros" in r["puntuacion"]
