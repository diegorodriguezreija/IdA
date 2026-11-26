"""Mínimo en T2b (O6, O8): escena valida y es repetible, y las opciones nuevas en su defecto dan lo de hoy."""

import inspect
from typing import Any, Dict, List

import pytest

from ida.ejecutor import ejecutar
from ida.mundos.minimo import MundoMinimo
from ida.mundos.opciones import OpcionInvalida, convertir, defectos
from ida.telemetria.esquema import validar, validar_escena
from ida.telemetria.grabacion import escenas


def _vida(tmp_path, nombre: str, latidos: int = 100, semilla: int = 1, **opciones: Any) -> List[Dict[str, Any]]:
    regs: List[Dict[str, Any]] = []
    ejecutar("minimo", latidos=latidos, semilla=semilla, consola=False, datos=str(tmp_path / nombre), nivel="vital",
             plazo_logico=40, tabula_rasa=True, opciones_mundo=opciones, al_latir=lambda o, onda, r: regs.append(r))
    return regs


# --- escena --------------------------------------------------------------------------------------------------------

def test_escena_valida_y_coherente():
    m = MundoMinimo()
    m.reiniciar(1)
    e = m.escena()
    assert validar_escena(e) == []
    assert (e["ancho"], e["alto"]) == (9, 9)
    assert e["yo"] == {"x": 4, "y": 4}
    assert len(e["celdas"]) == 9 and all(len(fila) == 9 for fila in e["celdas"])
    assert e["celdas"][4][4] == "pradera"
    assert e["inventario"] == {}
    assert set(e["extra"]) == {"bayas", "setas"}
    assert any(ent["clase"] == "baya" for ent in e["entidades"])
    assert any(ent["clase"] == "lobo" for ent in e["entidades"])


def test_escena_solo_lee():
    m = MundoMinimo()
    m.reiniciar(1)
    for _ in range(10):
        m.ejecutar(m.verbos().pop(), "", {})
    a = m.escena()
    assert m.escena() == a
    obs1 = [e.id for e in m.observar().entidades]
    obs2 = [e.id for e in m.observar().entidades]
    assert obs1 == obs2


def test_escena_en_el_registro_repetible(tmp_path):
    a = _vida(tmp_path, "a", latidos=60)
    b = _vida(tmp_path, "b", latidos=60)
    assert all(validar(r) == [] for r in a)
    assert "escena" in a[0]
    assert [r.get("escena") for r in a] == [r.get("escena") for r in b]
    reconstruidas = list(escenas(a))
    for anterior, r, actual in zip(reconstruidas, a[1:], reconstruidas[1:], strict=False):
        assert ("escena" in r) == (actual != anterior)
    assert all(e is not None for e in reconstruidas)


# --- opciones ------------------------------------------------------------------------------------------------------

def test_defectos_declarados_y_constructor():
    d = defectos(MundoMinimo.opciones())
    c = inspect.signature(MundoMinimo.__init__).parameters
    assert d["tamano"] == c["tamano"].default == 9
    assert d["depredadores"] == c["depredadores"].default == 1
    assert d["comida"] == c["comida"].default == 4
    assert set(d) == {"tamano", "depredadores", "comida"}


def test_opciones_de_minimo_fuera_de_rango():
    decl = MundoMinimo.opciones()
    with pytest.raises(OpcionInvalida, match=r"minimo: opción 'tamano': 3 fuera del rango \[5, 25\]"):
        convertir(decl, {"tamano": "3"}, "minimo")
    with pytest.raises(OpcionInvalida, match=r"minimo: opción 'depredadores': 10 fuera del rango \[0, 5\]"):
        convertir(decl, {"depredadores": "10"}, "minimo")
    with pytest.raises(OpcionInvalida, match=r"minimo: opción 'comida': 0 fuera del rango \[1, 20\]"):
        convertir(decl, {"comida": "0"}, "minimo")


def test_opciones_nuevas_por_defecto_dan_lo_de_hoy(tmp_path):
    hoy = _vida(tmp_path, "hoy", latidos=100)
    explicitas = _vida(tmp_path, "explicitas", latidos=100, tamano=9, depredadores=1, comida=4)
    assert [r["accion"] for r in hoy] == [r["accion"] for r in explicitas]


def test_cambio_de_opciones():
    m = MundoMinimo(tamano=11, depredadores=2, comida=6)
    m.reiniciar(1)
    e = m.escena()
    assert (e["ancho"], e["alto"]) == (11, 11)
    assert e["yo"] == {"x": 5, "y": 5}
    assert sum(1 for ent in e["entidades"] if ent["clase"] == "baya") == 6
    assert sum(1 for ent in e["entidades"] if ent["clase"] == "lobo") == 2
