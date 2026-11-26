"""Crafter en T2a (O6, O8): la escena valida y es repetible, y las opciones declaradas son las de la medición oficial."""

import inspect
import os
import sys
from typing import Any, Dict, List

import pytest

pytest.importorskip("crafter")

from ida.ejecutor import ejecutar  # noqa: E402
from ida.mundos.crafter import MundoCrafter  # noqa: E402
from ida.mundos.opciones import OpcionInvalida, convertir, defectos  # noqa: E402
from ida.telemetria.esquema import validar, validar_escena  # noqa: E402
from ida.telemetria.grabacion import escenas  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "herramientas"))


def _vida(tmp_path, nombre: str, latidos: int = 60, semilla: int = 31, **opciones: Any) -> List[Dict[str, Any]]:
    regs: List[Dict[str, Any]] = []
    ejecutar("crafter", latidos=latidos, semilla=semilla, consola=False, datos=str(tmp_path / nombre), nivel="vital",
             plazo_logico=40, tabula_rasa=True, opciones_mundo=opciones, al_latir=lambda o, onda, r: regs.append(r))
    return regs


# --- escena --------------------------------------------------------------------------------------------------------

def test_escena_valida_y_coherente():
    m = MundoCrafter(vista="oficial")
    m.reiniciar(31)
    e = m.escena()
    assert validar_escena(e) == []
    assert (e["ancho"], e["alto"]) == (9, 7)                    # vista oficial de día
    assert e["yo"] == {"x": 4, "y": 3, "orientacion": "sur"}    # en el centro, mirando hacia abajo al nacer
    assert e["origen"] == [m.jugador.pos[0] - 4, m.jugador.pos[1] - 3]
    assert e["celdas"][3][4] in ("hierba", "arena", "camino")  # donde está el individuo
    assert e["inventario"]["salud"] == 9 and "madera" in e["inventario"]
    assert e["extra"]["logros"] == [] and 0.0 <= e["extra"]["luz"] <= 1.0


def test_escena_solo_lee():
    """Dos llamadas seguidas dan lo mismo y no cambian lo que se observa después (O3)."""
    m = MundoCrafter(vista="oficial")
    m.reiniciar(31)
    for _ in range(30):
        m.ejecutar_primitivas(["move_left"])
    a = m.escena()
    assert m.escena() == a
    ids = sorted(e.id for e in m.observar().entidades)
    m2 = MundoCrafter(vista="oficial")
    m2.reiniciar(31)
    for _ in range(30):
        m2.ejecutar_primitivas(["move_left"])
    assert sorted(e.id for e in m2.observar().entidades) == ids


def test_escena_en_el_registro_repetible(tmp_path):
    """La escena va en el registro solo cuando cambia, valida, y es la misma en dos ejecuciones con plazo lógico."""
    a = _vida(tmp_path, "a", vista="oficial")
    b = _vida(tmp_path, "b", vista="oficial")
    assert all(validar(r) == [] for r in a)
    assert "escena" in a[0]
    assert [r.get("escena") for r in a] == [r.get("escena") for r in b]
    reconstruidas = list(escenas(a))
    for anterior, r, actual in zip(reconstruidas, a[1:], reconstruidas[1:], strict=False):
        assert ("escena" in r) == (actual != anterior)          # solo cuando cambia
    assert all(e is not None for e in reconstruidas)


# --- opciones ------------------------------------------------------------------------------------------------------

def test_defectos_declarados_son_los_de_la_medicion_oficial():
    """O8: vista, longitud y manual, los de ``evaluar_crafter.evaluar`` (D17); radio y ventana, los del constructor, que
    la evaluación no toca; las opciones nuevas reproducen lo de hoy."""
    import evaluar_crafter

    oficial = inspect.signature(evaluar_crafter.evaluar).parameters
    constructor = inspect.signature(MundoCrafter.__init__).parameters
    d = defectos(MundoCrafter.opciones())
    assert d["vista"] == oficial["vista"].default == "oficial"
    assert d["longitud"] == oficial["longitud_episodio"].default == 10000
    assert d["manual"] == oficial["manual"].default == "estricto"
    assert d["radio"] == constructor["radio"].default == 4
    assert d["ventana"] is False and constructor["ventana"].default == 0
    assert d["mapa"] == constructor["mapa"].default == 64
    assert d["semilla_mapa"] is None and constructor["semilla_mapa"].default is None
    assert set(d) == {"vista", "radio", "manual", "longitud", "mapa", "semilla_mapa", "ventana"}


def test_defectos_del_constructor_sin_cambiar():
    """La invariancia usa los del constructor: siguen siendo los de antes de T2a."""
    c = inspect.signature(MundoCrafter.__init__).parameters
    assert (c["vista"].default, c["longitud"].default, c["manual"].default, c["radio"].default) == ("cuadrada", 100000, "estricto", 4)


def test_opciones_de_crafter_fuera_de_rango(tmp_path):
    decl = MundoCrafter.opciones()
    with pytest.raises(OpcionInvalida, match=r"crafter: opción 'mapa': 200 fuera del rango \[32, 128\]"):
        convertir(decl, {"mapa": "200"}, "crafter")
    with pytest.raises(OpcionInvalida, match="no es uno de oficial, cuadrada"):
        convertir(decl, {"vista": "panoramica"}, "crafter")
    with pytest.raises(OpcionInvalida, match="opción desconocida de crafter"):
        ejecutar("crafter", latidos=1, consola=False, datos=str(tmp_path), opciones_mundo={"radiio": 4})


def test_ventana_booleana_del_constructor():
    assert MundoCrafter(ventana=True).ventana and MundoCrafter(ventana="1").ventana
    assert not MundoCrafter(ventana=False).ventana and not MundoCrafter().ventana


def test_opciones_nuevas_por_defecto_dan_lo_de_hoy(tmp_path):
    hoy = _vida(tmp_path, "hoy", latidos=40)
    explicitas = _vida(tmp_path, "explicitas", latidos=40, mapa=64, semilla_mapa="")
    assert [r["accion"] for r in hoy] == [r["accion"] for r in explicitas]


def test_semilla_y_tamano_del_mapa():
    a, b = MundoCrafter(semilla_mapa=7), MundoCrafter(semilla_mapa=7)
    a.reiniciar(1)
    b.reiniciar(2)                              # otra semilla del organismo, el mismo mapa
    assert a.escena()["celdas"] == b.escena()["celdas"]
    c = MundoCrafter(mapa=32)
    c.reiniciar(1)
    assert c.env._world.area == (32, 32) and tuple(c.jugador.pos) == (16, 16)
