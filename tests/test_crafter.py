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
    mundo.jugador.inventory["drink"] = 2
    agua = [e for e in mundo.observar().entidades if e.clase == "agua"]
    if agua:
        assert agua[0].rasgos["nutritivo"] > 0.5


def test_dormido_lo_decide_el_juego(mundo):
    mundo.jugador.inventory["energy"] = 3
    mundo.ejecutar(Verbo.DORMIR, "", {})
    assert mundo.observar().dormido is True


def test_coger_sin_obtener_nada_no_es_exito(mundo):
    pos = tuple(mundo.jugador.pos)
    ef = mundo.ejecutar(Verbo.COGER, f"suelo_{pos[0] + 1}_{pos[1]}", {})
    assert ef.exito is False


def test_vida_corta_en_crafter(tmp_path):
    r = ejecutar("crafter", latidos=80, semilla=3, consola=False, datos=str(tmp_path))[0]
    assert r["latidos"] > 0 and "logros" in r["puntuacion"]


def test_dotacion_innata_y_alarma_hostiles(mundo):
    from ida.core.memoria import Memoria
    from ida.core.vocabulario import Relacion
    from ida.mundos.crafter import asegurar_dotacion_innata, DOTACION_INNATA, HOSTILES

    mem = Memoria("completa")
    asegurar_dotacion_innata(mem)
    for sujeto, relacion, confianza in DOTACION_INNATA:
        assert (sujeto, relacion) in mem.saber
        p = mem.saber[(sujeto, relacion)]
        assert p.confianza == pytest.approx(0.95)

    assert HOSTILES["zombi"] == 1.0
    assert HOSTILES["esqueleto"] == 1.0
    assert HOSTILES["flecha"] == 1.0
    assert HOSTILES["lava"] == 1.0


def test_impulso_nido_y_recursos(mundo):
    nec = {n.nombre: n for n in mundo.perfil.necesidades}
    assert "preparar_nido" in nec
    assert nec["preparar_nido"].constantes == ("nido",)

    comps = mundo.componentes_propios()
    assert "S1.Interpretar" in comps
    assert any(c.tipo == "EvaluacionNido" for c in comps["S1.Interpretar"])

    # Sin madera ni pico, el recurso arbol tiene valor alto
    mundo.jugador.inventory["wood"] = 0
    mundo.jugador.inventory["wood_pickaxe"] = 0
    assert mundo._valor_recurso("arbol") > 0.8
    obs = mundo.observar()
    assert "nido" in obs.vitales
    assert obs.vitales["nido"] <= 50.0


def test_estrategia_anidar_fases(mundo, capsys):
    from ida.core.azar import Azar
    from ida.core.latido import Organismo
    from ida.core.linaje import Arquetipo
    from ida.core.memoria import Memoria
    from ida.mundos.crafter import Anidar
    from ida.sistemas import crear_sistemas

    ests = mundo.estrategias_propias()
    assert "S1" in ests
    anidar = next((e for e in ests["S1"] if isinstance(e, Anidar)), None)
    assert anidar is not None
    assert "preparar_nido" in anidar.impulsos

    azar = Azar(1)
    arq = Arquetipo.nuevo(azar)
    org = Organismo(mundo, crear_sistemas(), arq, Memoria("completa"), azar)
    for _ in range(5):
        org.latir()
    captured = capsys.readouterr()
    assert "[anidar] paso:" in captured.out
