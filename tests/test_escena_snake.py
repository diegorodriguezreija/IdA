"""Snake en T2b (O6, O8): escena valida con estado construido a mano (sin navegador) y opciones declaradas."""

import inspect

import pytest

from ida.mundos.opciones import OpcionInvalida, convertir, defectos
from ida.mundos.snake import MundoSnake
from ida.telemetria.esquema import validar_escena


def test_escena_valida_sin_navegador():
    m = MundoSnake(ventana=False)
    # Estado inicial por defecto de _reset_estado(): cabeza en (10, 2), cuerpo de 3 casillas, direccion "S"
    e = m.escena()
    assert validar_escena(e) == []
    assert (e["ancho"], e["alto"]) == (21, 15)
    assert e["yo"] == {"x": 10, "y": 2, "orientacion": "sur"}
    assert len(e["entidades"]) == 3
    assert e["entidades"][0] == {"clase": "cuerpo", "x": 10, "y": 2, "estado": "cabeza", "id": "cuerpo_0"}
    assert e["entidades"][1] == {"clase": "cuerpo", "x": 10, "y": 1, "estado": "cabeza" if (10, 1) == m.cabeza else "cuerpo", "id": "cuerpo_1"}
    assert e["inventario"] == {}
    assert e["extra"]["puntos"] == 0


def test_escena_con_comida_y_orientacion():
    m = MundoSnake(ventana=False)
    m.comida = (5, 7)
    m.direccion = "E"
    m.puntos = 10
    e = m.escena()
    assert validar_escena(e) == []
    assert e["yo"]["orientacion"] == "este"
    assert any(ent["clase"] == "comida" and (ent["x"], ent["y"]) == (5, 7) for ent in e["entidades"])
    assert e["extra"]["puntos"] == 10


def test_escena_solo_lee():
    m = MundoSnake(ventana=False)
    a = m.escena()
    b = m.escena()
    assert a == b


def test_defectos_declarados_y_constructor():
    d = defectos(MundoSnake.opciones())
    c = inspect.signature(MundoSnake.__init__).parameters
    assert d["dificultad"] == c["dificultad"].default == 0
    assert d["ventana"] == c["ventana"].default is False
    assert d["ritmo"] == c["ritmo"].default == 60
    assert set(d) == {"dificultad", "ventana", "ritmo"}


def test_opciones_snake_fuera_de_rango():
    decl = MundoSnake.opciones()
    with pytest.raises(OpcionInvalida, match=r"snake: opción 'dificultad': 5 fuera del rango \[0, 2\]"):
        convertir(decl, {"dificultad": "5"}, "snake")
    with pytest.raises(OpcionInvalida, match=r"snake: opción 'ritmo': 10 fuera del rango \[20, 200\]"):
        convertir(decl, {"ritmo": "10"}, "snake")


def test_opciones_convertidas():
    decl = MundoSnake.opciones()
    assert convertir(decl, {"dificultad": "2", "ventana": "1", "ritmo": "120"}, "snake") == {
        "dificultad": 2, "ventana": True, "ritmo": 120,
    }
