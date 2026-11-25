"""Cuerpo cuadrícula (D10, A5a): ``ModeloDirecto`` y ``MapaLocal`` reproducen lo que hacía ``Organismo._aprender_mapa``.

La referencia es una copia literal de ``_aprender_mapa`` antes de A5a (leía la Observación). Los Componentes reciben solo
piezas sintéticas (``Propiocepcion`` «yo» y ``Exterocepcion``) y la acción anterior en ``ei["Accion"]``; su contexto no
tiene Observación. Tras cada latido, la memoria de los dos lados debe ser idéntica.
"""

import copy
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple

import pytest

from ida.nucleo.memoria import Memoria
from ida.nucleo.mundo import Perfil
from ida.nucleo.onda import Onda
from ida.nucleo.pieza import Pieza
from ida.nucleo.vocabulario import Verbo
from ida.cuerpos.cuadricula import Cuadricula, MapaLocal, ModeloDirecto, pos_de

Pos = Tuple[int, int]
Ent = Tuple[str, str, Dict[str, float], Pos]   # id, clase, rasgos, posición


def _referencia(mem: Any, obs: Any, exterocepcion: Dict[str, Pieza], c: Optional[Dict[str, Any]]) -> None:
    """``Organismo._aprender_mapa`` tal como estaba antes de A5a (``self.memoria`` → ``mem``). A7b: ``mem`` es la sección
    «cuadricula» (D7), que tiene los mismos datos y métodos que tenía la Memoria."""
    if obs is None:
        return
    aqui = pos_de(obs.ubicacion)
    cuerpo = obs.cuerpo or {}
    crudas = cuerpo.get("casillas")
    if aqui is None or not isinstance(crudas, dict) or not crudas:
        return
    casillas = {(int(k[0]), int(k[1])): str(v) for k, v in crudas.items()}
    o = cuerpo.get("orientacion")
    cara = (int(o[0]), int(o[1])) if isinstance(o, (list, tuple)) and len(o) == 2 else None
    if c is not None and mem.yo_previo is not None:
        p0, f0 = mem.yo_previo
        verbo = c["verbo"]
        if verbo == Verbo.USAR:
            destino = (p0[0] + f0[0], p0[1] + f0[1]) if f0 is not None else None
        else:
            destino = pos_de(c.get("objetivo"))
        if destino is not None and abs(destino[0] - p0[0]) + abs(destino[1] - p0[1]) == 1:
            direccion = (destino[0] - p0[0], destino[1] - p0[1])
            antes = mem.casillas.get(destino)
            if verbo == Verbo.MOVER:
                libre = mem.transitable(antes)
                if libre is not None:
                    mem.aprender_cuerpo("mover", libre, aqui == destino, cara == direccion)
            elif verbo in (Verbo.COGER, Verbo.COMER, Verbo.ATACAR):
                mem.aprender_cuerpo("interactuar", True, aqui != p0, cara == direccion)
            despues = casillas.get(destino)
            cambio = antes is not None and despues is not None and antes != despues
            if verbo in (Verbo.COGER, Verbo.USAR) and antes is not None and despues is not None and (cambio or bool(c.get("exito"))):
                objetivo = str(c.get("clase") or c.get("objetivo") or "")
                mem.aprender_transformacion(verbo, objetivo, antes, despues)
                if cambio and verbo == Verbo.USAR and not mem.transitable_peligro(despues):
                    mem.cierres.add(destino)
                elif cambio:
                    mem.cierres.discard(destino)
    libres, ocupadas, peligros = set(), set(), set()
    for e in obs.entidades:
        pos = e.datos.get("pos")
        if not isinstance(pos, (list, tuple)) or len(pos) != 2:
            continue
        p = (int(pos[0]), int(pos[1]))
        if e.rasgos.get("lugar", 0.0) >= 0.5:
            libres.add(p)
        elif e.clase != casillas.get(p):
            ocupadas.add(p)
            pieza = exterocepcion.get(e.id)
            if pieza is not None and pieza.rasgo("peligro") >= 0.5 and e.rasgos.get("agente", 0.0) >= 0.5:
                peligros.add(p)
    mem.ver_casillas(aqui, casillas, libres, ocupadas, peligros)
    mem.yo_previo = (aqui, cara)


def _percepcion(pos: Pos, cara: Pos, mapa: Dict[Pos, str], cosas: List[Ent]) -> Tuple[Any, Dict[str, Any]]:
    """Observación (para la referencia) y piezas (para los Componentes) de un latido: casillas a 2 o menos, un lugar por
    vecina libre y las ``cosas`` dadas."""
    vista = {p: c for p, c in mapa.items() if abs(p[0] - pos[0]) <= 2 and abs(p[1] - pos[1]) <= 2}
    entidades: List[Ent] = list(cosas)
    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        v = (pos[0] + d[0], pos[1] + d[1])
        if mapa.get(v) == "suelo":
            entidades.append((f"celda_{v[0]}_{v[1]}", "suelo", {"lugar": 1.0, "proximidad": 1.0}, v))
    cuerpo = {"orientacion": cara, "casillas": vista}
    obs = SimpleNamespace(ubicacion=f"celda_{pos[0]}_{pos[1]}", cuerpo=cuerpo,
                          entidades=[SimpleNamespace(id=i, clase=c, rasgos=dict(r), datos={"pos": p}) for i, c, r, p in entidades])
    piezas = {
        "Propiocepcion": {"yo": Pieza(id="yo", tipo="Propiocepcion", carga={"ubicacion": obs.ubicacion, "inventario": {},
                                                                            "cuerpo": dict(cuerpo)})},
        "Exterocepcion": {i: Pieza(id=i, tipo="Exterocepcion", carga={"clase": c, "rasgos": dict(r), "datos": {"pos": p}})
                          for i, c, r, p in entidades},
    }
    return obs, piezas


def _estado(mem: Memoria) -> Dict[str, Any]:
    sec = mem.seccion("cuadricula") if mem.tiene_seccion("cuadricula") else None
    return {k: copy.deepcopy(getattr(sec, k)) if sec else None for k in ("casillas", "cuerpo", "cierres", "yo_previo", "transformaciones",
                                                         "peligro_sobre", "paso_libre", "paso_bloqueado", "version_mapa")}


LOBO: Ent = ("lobo_1", "lobo", {"agente": 1.0, "peligro": 0.8, "proximidad": 0.5}, (0, 0))
BASE = {(x, 0): "suelo" for x in range(4)} | {(x, y): "roca" for x in range(-1, 5) for y in (-1, 1)} | {(-1, 0): "roca", (4, 0): "tronco"}

# (posición, orientación, mapa, cosas, acción del latido anterior)
SECUENCIA: List[Tuple[Pos, Pos, Dict[Pos, str], List[Ent], Optional[Dict[str, Any]]]] = [
    ((1, 0), (0, 1), BASE, [LOBO], None),
    ((2, 0), (1, 0), BASE, [LOBO], {"verbo": Verbo.MOVER, "objetivo": "celda_2_0", "exito": True}),
    ((2, 0), (0, 1), BASE, [], {"verbo": Verbo.MOVER, "objetivo": "roca_2_1", "exito": False}),       # bloqueada: solo gira
    ((3, 0), (1, 0), BASE, [], {"verbo": Verbo.MOVER, "objetivo": "celda_3_0", "exito": True}),
    ((3, 0), (1, 0), BASE | {(4, 0): "suelo"}, [],
     {"verbo": Verbo.COGER, "objetivo": "tronco_4_0", "clase": "tronco", "exito": True}),               # lo transforma
    ((3, 0), (1, 0), BASE | {(4, 0): "roca"}, [], {"verbo": Verbo.USAR, "objetivo": "", "exito": True}),  # cierra
    ((3, 0), (1, 0), BASE | {(4, 0): "roca"}, [],
     {"verbo": Verbo.COGER, "objetivo": "roca_4_0", "clase": "roca", "exito": True}),                    # salió y no cambió
]


def test_cuerpo_cuadricula_igual_que_aprender_mapa() -> None:
    ref, nuevo = Memoria("completa"), Memoria("completa")
    cuerpo = Cuadricula()
    for mem in (ref, nuevo):   # D7: la sección «cuadricula» es del cuerpo; aquí se registra como al montarlo
        nombre, seccion = cuerpo.seccion_memoria(Perfil())   # type: ignore[misc]
        mem.registrar_seccion(nombre, cuerpo.nombre, seccion)
        seccion.paso_bloqueado["roca"] = 1   # la roca ya se sabe no transitable: el USAR que la pone cierra
    componentes = [c for comps in cuerpo.componentes().values() for c in comps]
    for c in componentes:
        c.de_cuerpo = cuerpo.nombre      # lo pone el Organismo al montarlos
    assert [type(c) for c in componentes] == [ModeloDirecto, MapaLocal]
    for pos, cara, mapa, cosas, accion in SECUENCIA:
        obs, piezas = _percepcion(pos, cara, mapa, cosas)
        _referencia(ref.seccion("cuadricula"), obs, piezas["Exterocepcion"], accion)
        ei = {"Accion": {"Accion": SimpleNamespace(carga=accion)}} if accion is not None else {}
        onda = SimpleNamespace(ev=lambda canal, p=piezas: p.get(canal, {}), ei=lambda canal, a=ei: a.get(canal, {}))
        ctx = SimpleNamespace(memoria=nuevo, observacion=None, onda=onda)   # sin Observación: solo piezas
        for c in componentes:
            c.aprender(ctx)  # type: ignore[arg-type]
        assert _estado(nuevo) == _estado(ref)
    # La secuencia ejerce lo que se partió: modelo del cuerpo, transformación, cierre y peligros sobre casillas
    sec = nuevo.seccion("cuadricula")
    assert sec.cuerpo and sec.transformaciones and sec.peligro_sobre
    assert (4, 0) in sec.cierres
    assert sec.modelo_cuerpo("mover", True) == (True, True) and sec.modelo_cuerpo("mover", False) == (False, True)


@pytest.mark.parametrize("comp", [ModeloDirecto(), MapaLocal()], ids=lambda c: type(c).__name__)
def test_sin_situacion_no_hacen_nada_y_no_tienen_barridos(comp: Any) -> None:
    mem = Memoria("completa")
    antes = _estado(mem)
    ctx = SimpleNamespace(memoria=mem, observacion=None, onda=SimpleNamespace(ev=lambda canal: {}, ei=lambda canal: {}))
    comp.aprender(ctx)
    assert _estado(mem) == antes
    assert comp.activo(Onda(1, 10, 100.0)) is False


def test_espacio_del_cuerpo():
    """C1 (D10): el cuerpo dice cómo es el espacio. Sin cuerpo, sin espacio métrico; la cuadrícula, con su geometría."""
    from ida.nucleo.mundo import SIN_ESPACIO

    assert SIN_ESPACIO.posicion("celda_3_4") is None and SIN_ESPACIO.distancia((0, 0), (1, 1)) is None
    assert SIN_ESPACIO.relacion((0, 0), (1, 1)) is None and SIN_ESPACIO.contiguos((0, 0)) == []
    assert SIN_ESPACIO.percibidas({"casillas": {(0, 0): "x"}}) is None
    assert SIN_ESPACIO.magnitud(SIN_ESPACIO.junto) <= SIN_ESPACIO.radio_prueba
    c = Cuadricula()
    assert c.posicion("celda_3_-4") == (3, -4) and c.posicion("fin") is None and c.posicion("3_4") is None
    assert c.distancia((0, 0), (2, -3)) == 5
    assert c.relacion((5, 5), (4, 7)) == (1, 2) and c.relacion((0, 0), (0, -1)) == c.junto == (0, 1)
    assert c.magnitud((1, 2)) == 3 and c.radio_prueba == 2
    assert c.orden((1, 1)) < c.orden((0, 2))            # a igual distancia, la diagonal
    assert sorted(c.contiguos((0, 0))) == [(-1, 0), (0, -1), (0, 1), (1, 0)]
    assert c.percibidas({"casillas": {(1, 2): "hierba"}}) == {(1, 2)} and c.percibidas({}) is None
