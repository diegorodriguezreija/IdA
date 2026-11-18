"""Crafter: observación con rasgos, sueño sincronizado con el juego y reglas de éxito de COMER y COGER."""

import pytest

pytest.importorskip("crafter")

from ida.core.vocabulario import RASGOS, Verbo  # noqa: E402
from ida.ejecutor import ejecutar  # noqa: E402
from ida.mundos.crafter import MundoCrafter, RefugioNocturno  # noqa: E402


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


def test_mapa_refugio_empieza_vacio_en_cada_vida(mundo):
    from types import SimpleNamespace

    refugio = RefugioNocturno()
    assert refugio.mapa == {}
    assert refugio.visitadas == set()

    # Vida 1: simular latidos 1 y 2 poblando el mapa y el estado recordado
    obs1 = mundo.observar()
    yo1 = SimpleNamespace(carga={"ubicacion": obs1.ubicacion, "inventario": obs1.inventario, "cuerpo": obs1.cuerpo})
    amb1 = SimpleNamespace(carga=obs1.ambiente)
    onda1 = SimpleNamespace(
        ev=lambda canal: {"Propiocepcion": {"yo": yo1}, "Ambiente": {"ambiente": amb1}}.get(canal, {})
    )
    ctx1 = SimpleNamespace(latido=1, onda=onda1)
    refugio._actualizar_memoria(ctx1)
    assert len(refugio.mapa) > 0
    refugio.mapa[(999, 999)] = "stone"
    refugio.mina_recordada = ((10, 10), (1, 0))
    refugio.paso_oscuro = True

    ctx2 = SimpleNamespace(latido=2, onda=onda1)
    refugio._actualizar_memoria(ctx2)
    assert (999, 999) in refugio.mapa

    # Vida 2 (comienza en latido 1): el mapa y los recuerdos de la vida anterior se vacían antes de incorporar la vista actual
    mundo.reiniciar(2)
    obs_nueva = mundo.observar()
    yo_nuevo = SimpleNamespace(carga={"ubicacion": obs_nueva.ubicacion, "inventario": obs_nueva.inventario, "cuerpo": {"orientacion": (0, 1), "vista": {}}})
    onda_nueva = SimpleNamespace(
        ev=lambda canal: {"Propiocepcion": {"yo": yo_nuevo}, "Ambiente": {"ambiente": amb1}}.get(canal, {})
    )
    ctx_nueva_vida = SimpleNamespace(latido=1, onda=onda_nueva)
    refugio._actualizar_memoria(ctx_nueva_vida)
    assert refugio.mapa == {}
    assert refugio.mina_recordada is None
    assert refugio.paso_oscuro is False


def test_atribucion_causas_muerte(mundo):
    # 1. Hambre cuando food == 0 en el paso de la muerte
    mundo.jugador.health = 1
    mundo.jugador.inventory["food"] = 0
    mundo.jugador.inventory["drink"] = 5
    mundo.jugador._recover = -15
    ef = mundo.ejecutar(Verbo.ESPERAR, "", {})
    assert ef.causa == "hambre"
    assert ef.muerte is True

    # 2. Sed cuando drink == 0 en el paso de la muerte
    mundo.reiniciar(1)
    mundo.jugador.health = 1
    mundo.jugador.inventory["food"] = 5
    mundo.jugador.inventory["drink"] = 0
    mundo.jugador._recover = -15
    ef = mundo.ejecutar(Verbo.ESPERAR, "", {})
    assert ef.causa == "sed"
    assert ef.muerte is True

    # 3. Flecha de esqueleto impacta al jugador mortalmente
    import numpy as np
    from crafter import objects as crafter_objects

    mundo.reiniciar(1)
    mundo.jugador.health = 2
    mundo.jugador.inventory["food"] = 5
    mundo.jugador.inventory["drink"] = 5
    pos_p = mundo.jugador.pos
    flecha = crafter_objects.Arrow(mundo.env._world, pos_p - np.array([1, 0]), np.array([1, 0]))
    mundo.env._world.add(flecha)
    ef = mundo.ejecutar(Verbo.ESPERAR, "", {})
    assert ef.causa == "esqueleto"
    assert ef.muerte is True

