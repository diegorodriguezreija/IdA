"""Crafter: observación con rasgos, sueño sincronizado con el juego y reglas de éxito de COMER y COGER."""

import pytest

pytest.importorskip("crafter")

from ida.core.vocabulario import RASGOS, Verbo  # noqa: E402
from ida.ejecutor import ejecutar  # noqa: E402
from ida.mundos.crafter import MundoCrafter, PlanAsentarse, RefugioNocturno  # noqa: E402


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


def test_c3d_forrajeo_oportunista():
    from types import SimpleNamespace
    from ida.core.pieza import Pieza

    ref = RefugioNocturno()
    vaca = Pieza("vaca_1", "Exterocepcion", carga={"clase": "vaca", "datos": {"pos": (10, 12)}, "rasgos": {"nutritivo": 0.5}})
    suelo = Pieza("celda_10_11", "Exterocepcion", carga={"clase": "suelo", "datos": {"pos": (10, 11)}, "rasgos": {"lugar": 1.0}})
    ref.mapa[(10, 11)] = "grass"
    ref.mapa[(10, 12)] = "grass"

    onda = SimpleNamespace(
        ev=lambda canal: {"Exterocepcion": {"vaca_1": vaca, "celda_10_11": suelo}}.get(canal, {})
    )
    ctx = SimpleNamespace(latido=10, onda=onda)
    pos = (10, 10)

    # Caso 1: vaca a 2, comida 4, luz 1 -> propone ir a por ella (MOVER)
    prop1 = ref._forrajeo_oportunista(ctx, pos, {"food": 4.0}, luz=1.0)
    assert prop1 is not None
    assert prop1.verbo == Verbo.MOVER
    h = 5.0 / 9.0
    assert abs(prop1.arousal - (0.55 + 0.35 * h)) < 1e-4
    assert abs(prop1.confianza - (0.70 + 0.25 * h)) < 1e-4

    # Caso 2: comida 8 -> no la propone
    prop2 = ref._forrajeo_oportunista(ctx, pos, {"food": 8.0}, luz=1.0)
    assert prop2 is None

    # Caso 3: vaca adyacente a distancia 1 -> propone COMER
    vaca_adj = Pieza("vaca_2", "Exterocepcion", carga={"clase": "vaca", "datos": {"pos": (10, 11)}, "rasgos": {"nutritivo": 0.5}})
    onda_adj = SimpleNamespace(
        ev=lambda canal: {"Exterocepcion": {"vaca_2": vaca_adj}}.get(canal, {})
    )
    ctx_adj = SimpleNamespace(latido=11, onda=onda_adj)
    prop3 = ref._forrajeo_oportunista(ctx_adj, pos, {"food": 4.0}, luz=1.0)
    assert prop3 is not None
    assert prop3.verbo == Verbo.COMER
    assert prop3.objetivo == "vaca_2"


def test_c4_1_bolsillo_tres_paredes_ciclo_completo():
    """8.5 Test 1: Bolsillo con 3 paredes naturales: el ciclo completo (plantar, cerrar,
    cosechar y volver a cerrar) es factible con _plan_mirar."""
    from types import SimpleNamespace
    from ida.core.pieza import Pieza

    ref = RefugioNocturno()
    mina = ((10, 10), (0, 1))
    # Recinto en (10, 10..13)
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
        # Bolsillo natural B = (8, 10) a dist 2 de e0=(10, 10), con 3 paredes naturales y acceso A = (8, 11)
        (8, 10): "grass",
        (7, 10): "stone",
        (8, 9): "water",
        (9, 10): "stone",
        (8, 11): "grass",
        (8, 12): "grass",
        (7, 11): "grass",
        (6, 11): "grass",
        (9, 11): "grass",
        (10, 9): "grass",
    }
    bol = ref._buscar_bolsillo((10, 10), mina, solo_natural=True)
    assert bol is not None
    assert bol["pos"] == (8, 10)
    assert bol["acceso"] == (8, 11)
    assert bol["paredes"] == []
    ref.bolsillos.append(bol)

    def _ctx_en(lat: int, extra_ext: dict | None = None):
        ext = {
            f"celda_{c[0]}_{c[1]}": Pieza(
                f"celda_{c[0]}_{c[1]}", "Exterocepcion",
                carga={"clase": "suelo", "datos": {"pos": c, "terreno": m}, "rasgos": {"lugar": 1.0, "peligro": 0.0}},
            )
            for c, m in ref.mapa.items() if m in ("grass", "path", "sand") and c not in ref.plantas_propias
        }
        if extra_ext:
            ext.update(extra_ext)
        onda = SimpleNamespace(
            ev=lambda canal: {"Exterocepcion": ext}.get(canal, {}),
            ei=lambda canal: {},
        )
        return SimpleNamespace(latido=lat, onda=onda)

    inv = {"food": 5.0, "drink": 8.0, "stone": 2.0, "sapling": 1.0, "wood_pickaxe": 1.0, "wood_sword": 1.0}
    # 1. Plantar: desde P=(8, 12) entra a A=(8, 11) mirando a B=(8, 10) y hace place_plant
    prop_mov = ref._avanzar_bolsillo(_ctx_en(50), (8, 12), (0, 1), inv, bol, mina, 0.7, 0.85, "refugio")
    assert prop_mov is not None and prop_mov.verbo == Verbo.MOVER and prop_mov.objetivo == "celda_8_11"
    prop_pl = ref._avanzar_bolsillo(_ctx_en(51), (8, 11), (0, -1), inv, bol, mina, 0.7, 0.85, "refugio")
    assert prop_pl is not None and prop_pl.verbo == Verbo.USAR and prop_pl.objetivo == "place_plant"
    bol["plantada"] = True
    bol["latido_plantacion"] = 51
    ref.plantas_propias.add((8, 10))

    # 2. Cerrar A=(8, 11) con _plan_mirar sin pisar B=(8, 10)
    plan_c = ref._plan_mirar((8, 11), (8, 11), mina)
    assert plan_c is not None
    P_c, A_c = plan_c
    assert P_c != (8, 10) and A_c != (8, 10)
    cara_c = (8 - A_c[0], 11 - A_c[1])
    prop_st = ref._avanzar_bolsillo(_ctx_en(53), A_c, cara_c, inv, bol, mina, 0.7, 0.85, "refugio")
    assert prop_st is not None and prop_st.verbo == Verbo.USAR and prop_st.objetivo == "place_stone"
    ref.mapa[(8, 11)] = "stone"
    bol["cerrado"] = True

    # 3. Cosechar: planta madura en B=(8, 10) -> picar piedra de A=(8, 11), entrar a A y COMER
    planta_madura = Pieza(
        "planta_1", "Exterocepcion",
        carga={"clase": "planta", "datos": {"pos": (8, 10)}, "rasgos": {"nutritivo": 0.8, "proximidad": 0.8}},
    )
    ctx_cos1 = _ctx_en(360, {"planta_1": planta_madura})
    prop_abrir = ref._actuar_cosecha_o_recierre(ctx_cos1, (8, 12), (0, -1), inv, mina, "refugio")
    assert prop_abrir is not None and prop_abrir.verbo == Verbo.COGER and prop_abrir.objetivo == "piedra_8_11"
    ref.mapa[(8, 11)] = "path"
    bol["cerrado"] = False

    ctx_cos2 = _ctx_en(361, {"planta_1": planta_madura})
    prop_entrar = ref._actuar_cosecha_o_recierre(ctx_cos2, (8, 12), (0, -1), inv, mina, "refugio")
    assert prop_entrar is not None and prop_entrar.verbo == Verbo.MOVER and prop_entrar.objetivo == "celda_8_11"

    ctx_cos3 = _ctx_en(362, {"planta_1": planta_madura})
    prop_comer = ref._actuar_cosecha_o_recierre(ctx_cos3, (8, 11), (0, -1), inv, mina, "refugio")
    assert prop_comer is not None and prop_comer.verbo == Verbo.COMER and prop_comer.objetivo == "planta_1"

    # 4. Volver a cerrar A=(8, 11) tras comer la planta (nutritivo vuelve a 0.0)
    planta_inmadura = Pieza(
        "planta_1", "Exterocepcion",
        carga={"clase": "planta", "datos": {"pos": (8, 10)}, "rasgos": {"nutritivo": 0.0, "proximidad": 1.0}},
    )
    ctx_rec = _ctx_en(364, {"planta_1": planta_inmadura})
    prop_rec = ref._actuar_cosecha_o_recierre(ctx_rec, A_c, cara_c, inv, mina, "refugio")
    assert prop_rec is not None and prop_rec.verbo == Verbo.USAR and prop_rec.objetivo == "place_stone"


def test_c4_2_fila_tres_plantas_junto_al_agua():
    """8.5 Test 2: Fila de 3 plantas junto al agua: orden factible con _plan_mirar."""
    ref = RefugioNocturno()
    mina = ((10, 14), (0, 1))
    ref.mapa = {
        (10, 14): "grass",
        (10, 15): "stone",
        (10, 16): "stone",
        (10, 17): "stone",
        (9, 16): "stone",
        (11, 16): "stone",
        (9, 17): "stone",
        (11, 17): "stone",
        (10, 18): "stone",
    }
    # Agua en y=9, fila de hierba en y=10 (x=10..12), extremos en (9,10) y (13,10), accesos en y=11, P en y=12..13
    for x in range(8, 15):
        ref.mapa[(x, 9)] = "water"
        for y in range(10, 14):
            ref.mapa[(x, y)] = "grass"

    fila = ref._planificar_fila_bolsillos((10, 13), mina, n_plantas=3)
    assert fila is not None and len(fila) == 3
    pos_sim = (10, 13)
    for item in fila:
        for w in item["paredes"]:
            plan_w = ref._plan_mirar(pos_sim, w, mina)
            assert plan_w is not None
            pos_sim = plan_w[1]
            ref.mapa[w] = "stone"
        b_i, a_i = item["pos"], item["acceso"]
        p_i = (2 * a_i[0] - b_i[0], 2 * a_i[1] - b_i[1])
        assert ref._es_transitable_huerto(p_i) and ref._es_transitable_huerto(a_i)
        ref.plantas_propias.add(b_i)
        plan_a = ref._plan_mirar(a_i, a_i, mina)
        assert plan_a is not None
        pos_sim = plan_a[1]
        ref.mapa[a_i] = "stone"

    # Al terminar, las 3 plantas tienen sus 4 vecinos en cruz bloqueados (agua, piedra u otra planta de la fila)
    for item in fila:
        bx, by = item["pos"]
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            assert ref._es_bloqueada_huerto((bx + dx, by + dy))


def test_c4_3_sin_piedra_pica_roca_antes_de_bolsillo():
    """8.5 Test 3: Sin piedra: el plan pica roca antes de preparar el bolsillo."""
    from types import SimpleNamespace
    from ida.core.pieza import Pieza

    ref = RefugioNocturno()
    mina = ((10, 10), (0, 1))
    ref.mina_recordada = mina
    ref.paso_oscuro = True
    ref.mapa = {
        (10, 10): "grass",
        (10, 11): "path",
        (10, 12): "path",
        (10, 13): "path",
        (9, 12): "stone",
        (11, 12): "stone",
        (9, 13): "stone",
        (11, 13): "stone",
        (10, 14): "stone",
        # Bolsillo natural en (8, 10)
        (8, 10): "grass",
        (7, 10): "stone",
        (8, 9): "water",
        (9, 10): "stone",
        (8, 11): "grass",
        (8, 12): "grass",
        (9, 11): "grass",
        # Roca suelta para picar en (11, 10) adyacente a (10, 10)
        (11, 10): "stone",
    }
    plan_s3 = PlanAsentarse(ref)
    yo = Pieza(
        "yo", "Propiocepcion",
        carga={
            "ubicacion": "celda_10_10",
            "inventario": {"food": 7.0, "drink": 7.0, "stone": 0.0, "sapling": 1.0, "wood_pickaxe": 1.0, "wood_sword": 1.0},
            "cuerpo": {"orientacion": (1, 0), "vista": dict(ref.mapa)},
        },
    )
    amb = Pieza("ambiente", "Ambiente", carga={"luz": 0.92})
    piedra_pz = Pieza("piedra_11_10", "Exterocepcion", carga={"clase": "piedra", "datos": {"pos": (11, 10)}, "rasgos": {"proximidad": 1.0}})
    suelo_pz = Pieza("celda_9_11", "Exterocepcion", carga={"clase": "suelo", "datos": {"pos": (9, 11), "terreno": "grass"}, "rasgos": {"lugar": 1.0}})
    onda = SimpleNamespace(
        ev=lambda canal: {
            "Propiocepcion": {"yo": yo},
            "Ambiente": {"ambiente": amb},
            "Exterocepcion": {"piedra_11_10": piedra_pz, "celda_9_11": suelo_pz},
        }.get(canal, {}),
        ei=lambda canal: {},
    )
    propuestas = []
    plan_s3.proponer = lambda _ctx, verbo, obj, ar, conf, motivo, **kw: propuestas.append((verbo, obj, motivo))  # type: ignore[method-assign]
    ctx = SimpleNamespace(
        latido=340,
        onda=onda,
        perfil=SimpleNamespace(hogar=True, mecanismos=SimpleNamespace(plan=False)),
        memoria=SimpleNamespace(hogar=lambda: None),
        con_experiencia=True,
    )
    assert plan_s3.elegible(ctx, "asentarse", 0.8) is True
    plan_s3.decidir(ctx)
    assert len(propuestas) == 1
    verbo, obj, _motivo = propuestas[0]
    assert verbo == Verbo.COGER
    assert obj == "piedra_11_10"


def test_c4_4_presupuesto_luz_dia1():
    """Test de presupuesto (8.0): el bolsillo del día 1 suma sus pasos a _coste_restante_pasos,
    y sin margen de luz no se planta el día 1 (el refugio manda)."""
    from types import SimpleNamespace
    from ida.core.pieza import Pieza

    ref = RefugioNocturno()
    mina = ((10, 10), (0, 1))
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
        # Bolsillo natural en (8, 10)
        (8, 10): "grass",
        (7, 10): "stone",
        (8, 9): "water",
        (9, 10): "stone",
        (8, 11): "grass",
        (8, 12): "grass",
        (7, 11): "grass",
        (6, 11): "grass",
        (9, 11): "grass",
        (10, 9): "grass",
    }
    inv = {"food": 7.0, "drink": 7.0, "stone": 2.0, "sapling": 1.0, "wood_pickaxe": 1.0, "wood_sword": 1.0}
    coste_sin = ref._coste_restante_pasos((10, 10), inv, mina, incluir_huerto=False)
    coste_con = ref._coste_restante_pasos((10, 10), inv, mina, incluir_huerto=True)
    assert coste_con > coste_sin

    def _paso_con_luz(lat: int, luz_val: float, bajando_val: bool):
        ref.bajando = bajando_val
        ref.luz_previa = luz_val + (0.01 if bajando_val else -0.01)
        yo = Pieza(
            "yo", "Propiocepcion",
            carga={"ubicacion": "celda_10_10", "inventario": dict(inv), "cuerpo": {"orientacion": (0, 1), "vista": dict(ref.mapa)}},
        )
        amb = Pieza("ambiente", "Ambiente", carga={"luz": luz_val})
        onda = SimpleNamespace(
            ev=lambda canal: {"Propiocepcion": {"yo": yo}, "Ambiente": {"ambiente": amb}, "Exterocepcion": {}}.get(canal, {}),
            ei=lambda canal: {},
        )
        ctx = SimpleNamespace(
            latido=lat, onda=onda,
            perfil=SimpleNamespace(hogar=True),
            memoria=SimpleNamespace(hogar=lambda: None),
            con_experiencia=True,
        )
        est_pz = Pieza("est", "Estrategia", carga={"paso": {"fase": "elegir_mina", "mina": mina, "mejor_dist": 0, "sin_avance": 0, "saliendo": False}})
        return ref.paso(ctx, est_pz)

    # Con margen de luz (luz=0.85, mañana) -> entra en fase 'huerto'
    estado_con_margen = _paso_con_luz(60, 0.85, False)
    assert estado_con_margen["fase"] == "huerto"

    # Sin margen de luz (luz=0.52, bajando al ocaso) -> no planta el día 1, va a 'cavar' el refugio
    estado_sin_margen = _paso_con_luz(165, 0.52, True)
    assert estado_sin_margen["fase"] != "huerto"
    assert estado_sin_margen["fase"] == "cavar"







