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
    assert refugio.visitadas == {}

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


def test_dano_sed_con_esqueleto_a_4_es_none(mundo):
    import numpy as np
    from crafter import objects as crafter_objects

    mundo.reiniciar(1)
    mundo.jugador.health = 5
    mundo.jugador.inventory["food"] = 5
    mundo.jugador.inventory["drink"] = 0
    mundo.jugador._recover = -15
    pos_p = mundo.jugador.pos
    esq = crafter_objects.Skeleton(mundo.env._world, pos_p + np.array([4, 0]), mundo.jugador)
    mundo.env._world.add(esq)
    ef = mundo.ejecutar(Verbo.ESPERAR, "", {})
    assert ef.delta.get("vitalidad", 0) < 0
    assert ef.causa is None
    assert ef.muerte is False


def test_flecha_no_mortal_desde_5_es_esqueleto(mundo):
    import numpy as np
    from crafter import objects as crafter_objects

    mundo.reiniciar(1)
    mundo.jugador.health = 7
    mundo.jugador.inventory["food"] = 5
    mundo.jugador.inventory["drink"] = 5
    pos_p = mundo.jugador.pos
    flecha = crafter_objects.Arrow(mundo.env._world, pos_p - np.array([1, 0]), np.array([1, 0]))
    mundo.env._world.add(flecha)
    ef = mundo.ejecutar(Verbo.ESPERAR, "", {})
    assert ef.delta.get("vitalidad", 0) < 0
    assert ef.causa == "esqueleto"
    assert ef.muerte is False
    assert mundo.jugador.health == 5


def test_zombi_en_cruz_con_dano_2_es_zombi(mundo):
    import numpy as np
    from crafter import objects as crafter_objects

    mundo.reiniciar(1)
    mundo.jugador.health = 7
    mundo.jugador.inventory["food"] = 5
    mundo.jugador.inventory["drink"] = 5
    pos_p = mundo.jugador.pos
    zombi = crafter_objects.Zombie(mundo.env._world, pos_p + np.array([1, 0]), mundo.jugador)
    mundo.env._world.add(zombi)
    ef = mundo.ejecutar(Verbo.ESPERAR, "", {})
    assert ef.delta.get("vitalidad", 0) < 0
    assert ef.causa == "zombi"
    assert ef.muerte is False
    assert mundo.jugador.health == 5


def test_agua_inalcanzable_detras_roca_elige_accesible():
    from ida.core.azar import Azar
    from ida.core.memoria import Memoria
    from ida.core.mundo import Perfil
    from ida.core.onda import Onda, Pieza
    from ida.core.soma import Soma
    from ida.core.linaje import Arquetipo
    from ida.core.arquitectura import Contexto
    from ida.mundos.crafter import RefugioNocturno

    ref = RefugioNocturno()
    ref.bajando = False
    ref.mapa = {
        (10, 10): "grass",
        (10, 11): "stone",
        (9, 12): "stone",
        (11, 12): "stone",
        (10, 13): "stone",
        (10, 12): "water",  # agua inalcanzable: rodeada de roca por las 4 casillas en cruz
        (11, 10): "grass",
        (12, 10): "grass",
        (13, 10): "grass",
        (14, 10): "water",  # agua accesible por camino libre
    }
    onda = Onda(10, 100.0, 1e9)
    onda.percibir("Propiocepcion", Pieza("yo", "Propiocepcion", carga={
        "inventario": {"drink": 0, "food": 8, "health": 9, "stone": 1, "wood_pickaxe": 1, "wood_sword": 1},
        "cuerpo": {"pos": (10, 10), "orientacion": (1, 0)},
    }))
    onda.percibir("Ambiente", Pieza("ambiente", "Ambiente", carga={"luz": 0.8}))
    onda.percibir("Exterocepcion", Pieza("celda_11_10", "Exterocepcion", carga={
        "datos": {"pos": (11, 10)},
        "terreno": "grass",
        "clase": "suelo",
        "rasgos": {"lugar": 1.0, "peligro": 0.0},
    }))

    ctx = Contexto(onda, Soma(), Memoria(), Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER, Verbo.COMER})
    prop = ref._abastecer(ctx, (10, 10), {"drink": 0, "food": 8}, 0.9, 0.9)

    assert (10, 12) in ref.inalcanzables
    assert prop is not None
    assert prop.verbo == Verbo.MOVER
    assert prop.objetivo == "celda_11_10"


def test_c1_1_roca_tres_casillas_en_linea():
    ref = RefugioNocturno()
    ref.mapa = {
        (10, 10): "grass",
        (10, 11): "stone",
        (10, 12): "stone",
        (10, 13): "stone",
        (9, 12): "stone",
        (11, 12): "stone",
        (9, 13): "stone",
        (11, 13): "stone",
        (10, 14): "stone",
    }
    res = ref._evaluar_recinto((10, 10), (0, 1), (10, 10), None, 0)
    assert res is not None
    puntuacion, colocar = res
    assert colocar == 0
    assert puntuacion > 0


def test_c1_2_lateral_e2_transitable_coloca_una_piedra():
    from ida.core.arquitectura import Contexto
    from ida.core.azar import Azar
    from ida.core.linaje import Arquetipo
    from ida.core.memoria import Memoria
    from ida.core.mundo import Perfil
    from ida.core.onda import Onda, Pieza
    from ida.core.soma import Soma

    ref = RefugioNocturno()
    ref.bajando = True
    ref.luz_previa = 0.4
    ref.mapa = {
        (10, 10): "grass",
        (10, 11): "path",
        (10, 12): "path",
        (10, 13): "path",
        (9, 12): "stone",
        (11, 12): "grass",  # lateral de e2 transitable (falta 1 pared)
        (9, 13): "stone",
        (11, 13): "stone",
        (10, 14): "stone",
        (11, 11): "grass",  # A vecina de (11, 12)
        (11, 10): "grass",  # P = 2A - C
    }
    res = ref._evaluar_recinto((10, 10), (0, 1), (10, 10), None, 2)
    assert res is not None
    assert res[1] == 1

    # En A=(11, 11) mirando a C=(11, 12) (orientación (0, 1)), la fase tapar coloca la piedra
    onda = Onda(20, 100.0, 1e9)
    onda.percibir("Propiocepcion", Pieza("yo", "Propiocepcion", carga={
        "ubicacion": "celda_11_11",
        "inventario": {"drink": 8, "food": 8, "health": 9, "stone": 2, "wood_pickaxe": 1, "wood_sword": 1},
        "cuerpo": {"pos": (11, 11), "orientacion": (0, 1), "vista": dict(ref.mapa)},
    }))
    onda.percibir("Ambiente", Pieza("ambiente", "Ambiente", carga={"luz": 0.4}))
    ctx = Contexto(onda, Soma(), Memoria(), Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER, Verbo.USAR})
    est = Pieza("S2:refugio_nocturno:cobijo", "Estrategia", carga={"paso": {"fase": "tapar", "mina": ((10, 10), (0, 1))}})
    prop = ref.actuar(ctx, est)
    assert prop is not None
    assert prop.verbo == Verbo.USAR
    assert prop.objetivo == "place_stone"


def test_c1_3_recinto_en_hierba_junto_al_agua_orden_plan_mirar():
    ref = RefugioNocturno()
    # Recinto en hierba junto al agua al fondo (10, 14), con roca en (9, 12), (9, 13) y 1 roca en e1 (10, 11)
    # Faltan 2 paredes laterales: (11, 13) y (11, 12); con 3 piedras en inventario (o 0 rocks + 2 paredes con 3 piedras)
    ref.mapa = {
        (10, 10): "grass",
        (10, 11): "grass",
        (10, 12): "grass",
        (10, 13): "grass",
        (9, 12): "stone",
        (9, 13): "stone",
        (10, 14): "water",
        (11, 12): "grass",
        (11, 13): "grass",
        (11, 11): "grass",
        (11, 10): "grass",
        (12, 12): "grass",
        (13, 12): "grass",
        (12, 13): "grass",
        (13, 13): "grass",
    }
    mina = ((10, 10), (0, 1))
    res = ref._evaluar_recinto((10, 10), (0, 1), (10, 10), None, 3)
    assert res is not None
    assert res[1] == 2

    orden = ref._orden_paredes_factible((10, 10), mina)
    assert len(orden) == 2
    pos_sim = (10, 10)
    for pared in orden:
        plan = ref._plan_mirar(pos_sim, pared, mina)
        assert plan is not None
        p_pos, a_pos = plan
        assert ref.mapa.get(a_pos) == "grass"
        assert ref.mapa.get(p_pos) == "grass"
        assert (2 * a_pos[0] - pared[0], 2 * a_pos[1] - pared[1]) == p_pos
        ref.mapa[pared] = "stone"
        pos_sim = a_pos


def test_c1_4_no_factible_sin_piedra_suficiente():
    ref = RefugioNocturno()
    ref.mapa = {
        (10, 10): "grass",
        (10, 11): "grass",
        (10, 12): "grass",
        (10, 13): "grass",
        (9, 12): "stone",
        (11, 12): "grass",  # 1 pared a colocar + 1 sello = 2 piedras necesarias
        (9, 13): "stone",
        (11, 13): "stone",
        (10, 14): "stone",
    }
    assert ref._evaluar_recinto((10, 10), (0, 1), (10, 10), None, 1) is None
    assert ref._evaluar_recinto((10, 10), (0, 1), (10, 10), None, 2) is not None


def test_c1_5_lava_a_distancia_2_se_rechaza():
    ref = RefugioNocturno()
    ref.mapa = {
        (10, 10): "grass",
        (10, 11): "stone",
        (10, 12): "stone",
        (10, 13): "stone",
        (9, 12): "stone",
        (11, 12): "stone",
        (9, 13): "stone",
        (11, 13): "stone",
        (10, 14): "stone",
        (12, 12): "lava",  # a distancia 2 de e2=(10, 12)
    }
    assert ref._evaluar_recinto((10, 10), (0, 1), (10, 10), None, 0) is None


def test_c3b_caducidad_visitadas():
    ref = RefugioNocturno()
    ref.visitadas[(5, 5)] = 10
    assert ref._es_visitada((5, 5), latido=100) is True   # diferencia 90 <= 150
    assert ref._es_visitada((5, 5), latido=160) is True   # diferencia 150 <= 150
    assert ref._es_visitada((5, 5), latido=161) is False  # diferencia 151 > 150
    assert ref._es_visitada((6, 6), latido=161) is False  # nunca visitada





