"""Archivos en T2b (O6, O8): escena valida y es repetible, y las opciones nuevas en su defecto dan lo de hoy."""

import inspect
from typing import Any, Dict, List

import pytest

from ida.ejecutor import ejecutar
from ida.mundos.archivos import MundoArchivos
from ida.mundos.opciones import OpcionInvalida, convertir, defectos
from ida.telemetria.esquema import validar, validar_escena
from ida.telemetria.grabacion import escenas


def _vida(tmp_path, nombre: str, latidos: int = 100, semilla: int = 1, **opciones: Any) -> List[Dict[str, Any]]:
    regs: List[Dict[str, Any]] = []
    ejecutar("archivos", latidos=latidos, semilla=semilla, consola=False, datos=str(tmp_path / nombre), nivel="vital",
             plazo_logico=40, tabula_rasa=True, opciones_mundo=opciones, al_latir=lambda o, onda, r: regs.append(r))
    return regs


# --- escena --------------------------------------------------------------------------------------------------------

def test_escena_valida_y_coherente(tmp_path):
    m = MundoArchivos(datos=str(tmp_path / "bioma_test"))
    m.reiniciar(1)
    e = m.escena()
    assert validar_escena(e) == []
    assert e["tipo"] == "arbol"
    assert e["yo"] == {"ruta": ""}
    assert e["nodos"][0] == {"ruta": "", "clase": "raiz", "padre": None}
    rutas_nodos = {n["ruta"] for n in e["nodos"]}
    assert "Llanura" in rutas_nodos
    assert "Llanura/Valle" in rutas_nodos
    for ent in e["entidades"]:
        assert ent["ruta"] in rutas_nodos
        assert "nombre" in ent and "clase" in ent


def test_escena_solo_lee(tmp_path):
    m = MundoArchivos(datos=str(tmp_path / "bioma_test"))
    m.reiniciar(1)
    for _ in range(5):
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
    d = defectos(MundoArchivos.opciones())
    c = inspect.signature(MundoArchivos.__init__).parameters
    assert d["biomas"] == c["biomas"].default == 5
    assert d["frecuencia_brotes"] == c["frecuencia_brotes"].default == 25
    assert d["agresividad"] == c["agresividad"].default == 0.35
    assert set(d) == {"biomas", "frecuencia_brotes", "agresividad"}


def test_opciones_de_archivos_fuera_de_rango():
    decl = MundoArchivos.opciones()
    with pytest.raises(OpcionInvalida, match=r"archivos: opción 'biomas': 0 fuera del rango \[1, 5\]"):
        convertir(decl, {"biomas": "0"}, "archivos")
    with pytest.raises(OpcionInvalida, match=r"archivos: opción 'frecuencia_brotes': 2 fuera del rango \[5, 100\]"):
        convertir(decl, {"frecuencia_brotes": "2"}, "archivos")
    with pytest.raises(OpcionInvalida, match=r"archivos: opción 'agresividad': 1.5 fuera del rango \[0.0, 1.0\]"):
        convertir(decl, {"agresividad": "1.5"}, "archivos")


def test_opciones_nuevas_por_defecto_dan_lo_de_hoy(tmp_path):
    hoy = _vida(tmp_path, "hoy", latidos=100)
    explicitas = _vida(tmp_path, "explicitas", latidos=100, biomas=5, frecuencia_brotes=25, agresividad=0.35)
    assert [r["accion"] for r in hoy] == [r["accion"] for r in explicitas]


def test_cambio_de_biomas(tmp_path):
    m = MundoArchivos(datos=str(tmp_path / "bioma_test"), biomas=2)
    m.reiniciar(1)
    e = m.escena()
    rutas_nodos = [n["ruta"] for n in e["nodos"]]
    assert "Llanura" in rutas_nodos and "Bosque" in rutas_nodos
    assert "Montaña" not in rutas_nodos
