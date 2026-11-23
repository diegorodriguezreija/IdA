"""Motor del cuerpo cuadrícula (D9, A5b): traduce la intención a primitivas leyendo piezas y juzga su éxito como lo
hacía ``MundoCrafter.ejecutar`` antes de A5b.

La referencia de los tests de equivalencia es una copia literal de ``ejecutar``, ``_interactuar`` y ``_posicion`` antes de
A5b (solo cambia que ``_efecto`` ya no recibe ``exito``: se pone después).
"""

from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple

import pytest

from ida.core.azar import Azar
from ida.core.latido import Organismo
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.mundo import Efecto
from ida.core.pieza import Pieza
from ida.core.vocabulario import Verbo
from ida.cuerpos.cuadricula import Cuadricula, MotorCuadricula
from ida.sistemas import crear_sistemas

Pos = Tuple[int, int]
DISPONIBLES = ["noop", "move_left", "move_right", "move_up", "move_down", "do", "sleep", "place_table", "make_wood_pickaxe"]


def _ctx(aqui: Pos, cara: Pos, ext: Optional[Dict[str, Pos]] = None, vista: Optional[Dict[str, List[int]]] = None) -> Any:
    yo = Pieza(id="yo", tipo="Propiocepcion", carga={"ubicacion": f"celda_{aqui[0]}_{aqui[1]}",
                                                      "cuerpo": {"orientacion": cara,
                                                                 "vista": {k: {"clase": k.rsplit("_", 1)[0], "pos": v} for k, v in (vista or {}).items()}}})
    piezas = {"Propiocepcion": {"yo": yo},
              "Exterocepcion": {i: Pieza(id=i, tipo="Exterocepcion", carga={"clase": i.split("_")[0], "rasgos": {}, "datos": {"pos": p}})
                                for i, p in (ext or {}).items()}}
    return SimpleNamespace(onda=SimpleNamespace(ev=lambda canal: piezas.get(canal, {})))


def _intencion(verbo: Verbo, objetivo: str = "", datos: Optional[Dict[str, Any]] = None) -> Pieza:
    return Pieza(id="decision", tipo="Decision", carga={"verbo": verbo, "objetivo": objetivo, "datos": dict(datos or {})})


def _efecto(antes: Dict[str, int], despues: Dict[str, int], delta: Optional[Dict[str, float]] = None) -> Efecto:
    return Efecto(True, dict(delta or {}), medidas={"inventario_antes": antes, "inventario_despues": despues, "objetos": ["sapling", "wood"]})


# --- traducción ---------------------------------------------------------------

def test_mover_a_una_vecina_y_no_a_otra():
    m = MotorCuadricula()
    assert m.primitivas(_intencion(Verbo.MOVER, "celda_6_5"), _ctx((5, 5), (0, 1)), DISPONIBLES) == ["move_right"]
    assert m.primitivas(_intencion(Verbo.MOVER, "celda_5_4"), _ctx((5, 5), (0, 1)), DISPONIBLES) == ["move_up"]
    assert m.primitivas(_intencion(Verbo.MOVER, "celda_7_5"), _ctx((5, 5), (0, 1)), DISPONIBLES) == []
    assert m.primitivas(_intencion(Verbo.MOVER, "vaca_1"), _ctx((5, 5), (0, 1)), DISPONIBLES) == []   # no se sabe dónde está


@pytest.mark.parametrize("verbo", [Verbo.COMER, Verbo.ATACAR, Verbo.COGER])
def test_golpe_con_y_sin_giro(verbo):
    m = MotorCuadricula()
    assert m.primitivas(_intencion(verbo, "arbol_4_5"), _ctx((5, 5), (-1, 0)), DISPONIBLES) == ["do"]
    assert m.primitivas(_intencion(verbo, "arbol_4_5"), _ctx((5, 5), (0, 1)), DISPONIBLES) == ["move_left", "do"]
    assert m.primitivas(_intencion(verbo, "arbol_3_5"), _ctx((5, 5), (-1, 0)), DISPONIBLES) == []


def test_objetivo_sin_coordenadas_por_pieza_y_por_vista():
    m = MotorCuadricula()
    ctx = _ctx((5, 5), (0, 1), ext={"vaca_1": (5, 6)}, vista={"vaca_2": [6, 5], "vaca_1": [0, 0]})
    assert m.primitivas(_intencion(Verbo.ATACAR, "vaca_1"), ctx, DISPONIBLES) == ["do"]               # la pieza manda
    assert m.primitivas(_intencion(Verbo.ATACAR, "vaca_2"), ctx, DISPONIBLES) == ["move_right", "do"]  # solo en la vista
    assert m.primitivas(_intencion(Verbo.ATACAR, "vaca_3"), ctx, DISPONIBLES) == []


def test_usar_dormir_y_el_resto():
    m, ctx = MotorCuadricula(), _ctx((5, 5), (0, 1))
    assert m.primitivas(_intencion(Verbo.USAR, "mesa", {"receta": "place_table"}), ctx, DISPONIBLES) == ["place_table"]
    assert m.primitivas(_intencion(Verbo.USAR, "place_table"), ctx, DISPONIBLES) == ["place_table"]
    assert m.primitivas(_intencion(Verbo.USAR, "mesa", {"receta": "make_diamond_sword"}), ctx, DISPONIBLES) == []
    assert m.primitivas(_intencion(Verbo.DORMIR), ctx, DISPONIBLES) == ["sleep"]
    assert m.primitivas(_intencion(Verbo.ESPERAR), ctx, DISPONIBLES) == ["noop"]
    assert m.primitivas(_intencion(Verbo.ACECHAR, "zombi_1"), ctx, DISPONIBLES) == ["noop"]


def test_sinergia_de_dos():
    motor = Cuadricula().motor()
    assert isinstance(motor, MotorCuadricula) and motor.max_sinergia == 2
    uno = MotorCuadricula(max_sinergia=1)
    assert uno.primitivas(_intencion(Verbo.COGER, "arbol_4_5"), _ctx((5, 5), (0, 1)), DISPONIBLES) == ["move_left"]


# --- juicio -------------------------------------------------------------------

def test_juicio_como_antes():
    m = MotorCuadricula()
    inv = {"food": 3, "drink": 3, "health": 9, "wood": 0, "sapling": 0}
    assert m.juzgar(_intencion(Verbo.MOVER, "celda_6_5"), [], _efecto(inv, inv)) is False
    # COMER que no alimenta (un golpe a la vaca que aún no la abate) y que alimenta
    assert m.juzgar(_intencion(Verbo.COMER, "vaca_1"), ["do"], _efecto(inv, inv)) is False
    assert m.juzgar(_intencion(Verbo.COMER, "vaca_1"), ["do"], _efecto(inv, {**inv, "food": 9}, {"alimentacion": 66.67})) is True
    # COGER sin ganancia (la salud no cuenta) y con ganancia
    assert m.juzgar(_intencion(Verbo.COGER, "arbol_4_5"), ["do"], _efecto(inv, {**inv, "health": 9, "food": 4})) is False
    assert m.juzgar(_intencion(Verbo.COGER, "arbol_4_5"), ["do"], _efecto(inv, {**inv, "wood": 1})) is True
    assert m.juzgar(_intencion(Verbo.ATACAR, "zombi_1"), ["do"], _efecto(inv, inv)) is True
    assert m.juzgar(_intencion(Verbo.USAR, "place_table"), ["place_table"], _efecto(inv, inv)) is True


def test_cuenta_de_primitivas():
    m = MotorCuadricula()
    m.contar(["move_left", "do"])
    m.contar(["do"])
    assert m.ejecutadas == {"move_left": 1, "do": 2}


# --- mundos sin cuerpo --------------------------------------------------------

def test_un_mundo_sin_cuerpo_no_cambia():
    from ida.mundos.minimo import MundoMinimo
    mundo = MundoMinimo()
    assert mundo.primitivas() is None and mundo.registro().cuerpo is None
    azar = Azar(1)
    org = Organismo(mundo, crear_sistemas(), Arquetipo.nuevo(azar), Memoria(mundo.perfil.memoria), azar)
    actuadores = [c for c in org.actuar.componentes if type(c).__name__ == "Actuador"]
    assert actuadores and all(a._motor is None and a._ejecutar_primitivas is None for a in actuadores)


# --- Crafter: el efecto por primitivas es el de antes ---------------------------

def _posicion_antes(m: Any, objetivo: str) -> Optional[Pos]:
    partes = objetivo.rsplit("_", 2)
    if len(partes) == 3 and partes[1].lstrip("-").isdigit() and partes[2].lstrip("-").isdigit():
        return int(partes[1]), int(partes[2])
    for cid, _, cpos, _ in m._cosas():
        if cid == objetivo:
            return cpos
    return None


def _ejecutar_antes(m: Any, verbo: Verbo, objetivo: str, datos: Dict[str, Any]) -> Efecto:
    """``MundoCrafter.ejecutar`` antes de A5b, literal salvo el ``exito`` de ``_efecto``."""
    from ida.mundos.crafter import INVENTARIO, MOVIMIENTOS, _dist
    p = m.jugador
    antes = {"salud": p.health, **dict(p.inventory)}
    logros_antes = {k for k, v in p.achievements.items() if v} if isinstance(p.achievements, dict) else set(p.achievements)
    exito = True
    m._causa_contacto = None

    def interactuar() -> bool:
        pos, destino = tuple(p.pos), _posicion_antes(m, objetivo)
        if destino is None or _dist(pos, destino) != 1:
            return False
        direccion = (destino[0] - pos[0], destino[1] - pos[1])
        if tuple(p.facing) != direccion:
            m._paso(MOVIMIENTOS[direccion])
        m._paso("do")
        return True

    if verbo == Verbo.MOVER:
        destino = _posicion_antes(m, objetivo)
        pos = tuple(p.pos)
        if destino is not None and _dist(pos, destino) == 1:
            m._paso(MOVIMIENTOS[(destino[0] - pos[0], destino[1] - pos[1])])
        else:
            exito = False
    elif verbo in (Verbo.COMER, Verbo.ATACAR, Verbo.COGER):
        exito = interactuar()
        if exito and verbo == Verbo.COMER and p.inventory["food"] <= antes["food"] and p.inventory["drink"] <= antes["drink"]:
            exito = False
        if exito and verbo == Verbo.COGER and not any(p.inventory[k] > antes[k] for k in INVENTARIO):
            exito = False
    elif verbo == Verbo.USAR:
        receta = datos.get("receta") or objetivo
        exito = receta in m.acciones
        if exito:
            m._paso(receta)
    elif verbo == Verbo.DORMIR:
        m._paso("sleep")
    else:
        m._paso("noop")
    ef = m._efecto(antes, logros_antes)
    ef.exito = exito
    return ef


def _ctx_de(obs: Any) -> Any:
    """Las piezas que darían los sensores del Core con esta Observación (Propiocepcion «yo» y Exterocepcion)."""
    yo = Pieza(id="yo", tipo="Propiocepcion", carga={"ubicacion": obs.ubicacion, "cuerpo": dict(obs.cuerpo or {})})
    ext = {e.id: Pieza(id=e.id, tipo="Exterocepcion", carga={"clase": e.clase, "rasgos": dict(e.rasgos), "datos": dict(e.datos)})
           for e in obs.entidades}
    piezas = {"Propiocepcion": {"yo": yo}, "Exterocepcion": ext}
    return SimpleNamespace(onda=SimpleNamespace(ev=lambda canal: piezas.get(canal, {})))


def _ejecutar_ahora(m: Any, motor: MotorCuadricula, verbo: Verbo, objetivo: str, datos: Dict[str, Any]) -> Tuple[Efecto, List[str]]:
    """Lo que hace el Actuador del Core desde A5b."""
    obs = m.observar()
    intencion = _intencion(verbo, objetivo, datos)
    prims = motor.primitivas(intencion, _ctx_de(obs), m.primitivas())
    ef = m.ejecutar_primitivas(prims, verbo) if prims else Efecto(exito=False)
    ef.exito = motor.juzgar(intencion, prims, ef)
    return ef, prims


def _guion(obs: Any, i: int) -> Tuple[Verbo, str, Dict[str, Any]]:
    """Una conducta fija y variada: golpea lo que tiene al lado, a veces fabrica o duerme, y si no, se mueve."""
    cerca = [e for e in obs.entidades if e.rasgos.get("lugar", 0.0) < 0.5 and e.rasgos.get("proximidad", 0.0) >= 1.0]
    lugares = [e for e in obs.entidades if e.rasgos.get("lugar", 0.0) >= 0.5]
    if i % 23 == 7:
        return Verbo.USAR, "mesa", {"receta": ("place_table", "make_wood_pickaxe", "inventar")[i % 3]}
    if i % 41 == 5:
        return Verbo.DORMIR, "", {}
    if cerca and i % 3:
        e = cerca[i % len(cerca)]
        return (Verbo.COGER, Verbo.COMER, Verbo.ATACAR)[i % 3], e.id, {}
    if lugares:
        return Verbo.MOVER, lugares[(i // 4) % len(lugares)].id, {}
    return Verbo.ESPERAR, "", {}


def _campos(ef: Efecto) -> Tuple[Any, ...]:
    return ef.exito, ef.delta, ef.causa, ef.obtenido, ef.muerte, ef.mensaje


@pytest.mark.parametrize("semilla", [1, 7])
def test_el_efecto_por_primitivas_es_el_de_antes(semilla):
    pytest.importorskip("crafter")
    from ida.mundos.crafter import MundoCrafter
    a, b = MundoCrafter(), MundoCrafter()
    a.reiniciar(semilla)
    b.reiniciar(semilla)
    motor = MotorCuadricula()
    dos = 0
    for i in range(400):
        if a.terminado():
            break
        obs = a.observar()
        assert [e.id for e in obs.entidades] == [e.id for e in b.observar().entidades]
        verbo, objetivo, datos = _guion(obs, i)
        antes = _ejecutar_antes(a, verbo, objetivo, datos)
        ahora, prims = _ejecutar_ahora(b, motor, verbo, objetivo, datos)
        assert _campos(ahora) == _campos(antes), (i, verbo, objetivo, prims)
        assert a.t == b.t     # las visitas ya no son del adaptador (A4): las compara tests/test_valoracion_crafter.py
        dos += len(prims) == 2
    assert dos > 0      # hubo golpes con giro: secuencias de dos primitivas


def test_vecina_fuera_de_las_14_entidades():
    """Con más de 14 entidades a la vista (lava alrededor, que va primero), una vaca vecina no está entre las piezas
    Exterocepcion, pero el Motor la encuentra en ``vista``."""
    pytest.importorskip("crafter")
    from crafter import objects

    from ida.mundos.crafter import MundoCrafter
    m = MundoCrafter()
    m.reiniciar(1)
    w, (px, py) = m.env._world, (int(m.jugador.pos[0]), int(m.jugador.pos[1]))
    vaca = (px + 1, py)
    for x in range(px - 3, px + 4):
        for y in range(py - 3, py + 4):
            if (x, y) not in ((px, py), vaca) and abs(x - px) + abs(y - py) >= 2:
                if w[(x, y)][1] is not None:
                    w.remove(w[(x, y)][1])
                w[(x, y)] = "lava"
    if w[vaca][1] is not None:
        w.remove(w[vaca][1])
    w[vaca] = "grass"
    w.add(objects.Cow(w, vaca))
    obs = m.observar()
    vid = (obs.cuerpo or {})["vista"]
    ids = [i for i, v in vid.items() if tuple(v["pos"]) == vaca and v["clase"] == "vaca"]
    assert len(m._cosas()) > 14 and ids
    assert ids[0] not in {e.id for e in obs.entidades}
    motor = MotorCuadricula()
    cara = tuple(m.jugador.facing)
    esperado = ["do"] if cara == (1, 0) else ["move_right", "do"]
    assert motor.primitivas(_intencion(Verbo.ATACAR, ids[0]), _ctx_de(obs), m.primitivas()) == esperado
