"""Contratos de ``Mundo`` de T2a (O6, O8, O18): ``escena()`` y ``opciones()``, su validación y la escena en el registro."""

import importlib

import pytest

from ida.ejecutor import ejecutar
from ida.mundos import MUNDOS, cargar
from ida.mundos.opciones import OpcionInvalida, con_defectos, convertir, opcion, validar_declaracion
from ida.nucleo.mundo import Mundo
from ida.telemetria.esquema import validar, validar_escena
from ida.telemetria.grabacion import escenas


def _clase(nombre: str):
    """La clase del mundo, o se salta si su módulo no se puede importar (dependencias de mundo)."""
    modulo, _, clase = MUNDOS[nombre].partition(":")
    try:
        return getattr(importlib.import_module(modulo), clase)
    except ImportError as e:   # pragma: no cover - depende de los extras instalados
        pytest.skip(f"{nombre}: {e}")


# --- escena: contrato por defecto ----------------------------------------------------------------------------------

def test_escena_por_defecto_es_none():
    class Vacio(Mundo):
        def reiniciar(self, semilla):
            pass

        def observar(self):
            raise NotImplementedError

        def verbos(self):
            return set()

    assert Vacio().escena() is None
    assert Vacio.opciones() == []


@pytest.mark.parametrize("nombre", sorted(MUNDOS))
def test_cada_mundo_sin_escena_hereda_none(nombre):
    """Los mundos que aún no implementan ``escena()`` (T2b) heredan la de ``Mundo``, que devuelve None."""
    clase = _clase(nombre)
    if clase.escena is Mundo.escena:
        assert Mundo.escena(object.__new__(clase)) is None


# --- escena: validador ---------------------------------------------------------------------------------------------

REJILLA = {
    "tipo": "rejilla", "ancho": 3, "alto": 2,
    "celdas": [["hierba", "agua", None], ["arena", "hierba", "piedra"]],
    "entidades": [{"clase": "vaca", "x": 2, "y": 1, "id": "vaca_1"}],
    "yo": {"x": 1, "y": 0, "orientacion": "sur"},
    "origen": [10, 20], "inventario": {"madera": 2}, "extra": {"luz": 0.5},
}
ARBOL = {
    "tipo": "arbol",
    "nodos": [{"ruta": "", "clase": "raiz", "padre": None}, {"ruta": "a", "clase": "nodo", "padre": ""},
              {"ruta": "a/b", "clase": "nodo", "padre": "a"}],
    "entidades": [{"clase": "comida", "ruta": "a/b", "nombre": "x"}],
    "yo": {"ruta": "a"}, "inventario": {}, "extra": {},
}
TABLERO = {
    "tipo": "tablero", "ancho": 8, "alto": 8,
    "piezas": [{"clase": "rey", "color": "blanco", "x": 4, "y": 7}],
    "yo": {"color": "blanco"}, "turno": "negro", "marcas": [{"clase": "ultima", "x": 4, "y": 7}],
    "inventario": {}, "extra": {"fen": "8/8/8/8/8/8/8/4K3 b - - 0 1"},
}


@pytest.mark.parametrize("escena", [REJILLA, ARBOL, TABLERO], ids=["rejilla", "arbol", "tablero"])
def test_escenas_validas(escena):
    assert validar_escena(escena) == []


@pytest.mark.parametrize("cambio, error", [
    ({"tipo": "mapa"}, "tipo"),
    ({"celdas": [["hierba"]]}, "celdas"),
    ({"entidades": [{"clase": "vaca", "x": 3, "y": 0}]}, "fuera"),
    ({"yo": {"x": 0, "y": 5}}, "yo"),
    ({"yo": {"x": 0, "y": 0, "orientacion": "arriba"}}, "orientacion"),
    ({"inventario": {"madera": "dos"}}, "inventario"),
    ({"extra": None}, "extra"),
])
def test_rejilla_invalida(cambio, error):
    errores = validar_escena({**REJILLA, **cambio})
    assert errores and error in errores[0]


def test_arbol_y_tablero_invalidos():
    assert validar_escena({**ARBOL, "yo": {"ruta": "z"}})
    assert validar_escena({**ARBOL, "nodos": [{"ruta": "a/b", "clase": "nodo", "padre": "a"}]})
    assert validar_escena({**TABLERO, "piezas": [{"clase": "rey", "color": "blanco", "x": 8, "y": 0}]})


def test_registro_valida_la_escena(tmp_path):
    regs: list = []
    ejecutar("minimo", latidos=2, semilla=1, consola=False, datos=str(tmp_path), nivel="vital", plazo_logico=40,
             al_latir=lambda o, onda, reg: regs.append(reg))
    r = {k: v for k, v in regs[-1].items() if k != "escena"}
    assert validar(r) == []
    assert validar({**r, "escena": REJILLA}) == []
    assert any("escena" in e for e in validar({**r, "escena": {**REJILLA, "alto": 5}}))


def test_escenas_se_reconstruyen():
    rs = [{"vida": 1, "escena": {"n": 1}}, {"vida": 1}, {"vida": 1, "escena": {"n": 2}}, {"vida": 2}, {"vida": 2, "escena": {"n": 3}}]
    assert list(escenas(rs)) == [{"n": 1}, {"n": 1}, {"n": 2}, None, {"n": 3}]


# --- opciones ------------------------------------------------------------------------------------------------------

TEXTO = {"es": "texto", "en": "text"}


def test_declaracion_valida_y_mal_formada():
    d = opcion("radio", "entero", 4, TEXTO, TEXTO, min=2, max=8)
    assert validar_declaracion(d) == []
    with pytest.raises(OpcionInvalida, match="defecto"):
        opcion("radio", "entero", 12, TEXTO, TEXTO, min=2, max=8)
    with pytest.raises(OpcionInvalida, match="tipo"):
        opcion("radio", "texto", "a", TEXTO, TEXTO)
    with pytest.raises(OpcionInvalida, match="etiqueta"):
        opcion("radio", "booleano", False, {"es": "solo es"}, TEXTO)
    with pytest.raises(OpcionInvalida, match="valores"):
        opcion("vista", "opcion", "a", TEXTO, TEXTO, valores=[])
    with pytest.raises(OpcionInvalida, match="valor"):
        opcion("semilla", "entero", None, TEXTO, TEXTO, min=0, max=9)
    assert opcion("semilla", "entero", None, TEXTO, TEXTO, min=0, max=9, vacia=True)["defecto"] is None


DECL = [
    opcion("radio", "entero", 4, TEXTO, TEXTO, min=2, max=8),
    opcion("tasa", "real", 0.5, TEXTO, TEXTO, min=0.0, max=1.0),
    opcion("vista", "opcion", "oficial", TEXTO, TEXTO, valores=["oficial", "cuadrada"]),
    opcion("ventana", "booleano", False, TEXTO, TEXTO),
    opcion("semilla", "entero", None, TEXTO, TEXTO, min=0, max=100, vacia=True),
]


def test_convertir_desde_texto_y_json():
    assert convertir(DECL, {"radio": "5", "tasa": "0.25", "vista": "cuadrada", "ventana": "1", "semilla": ""}) == {
        "radio": 5, "tasa": 0.25, "vista": "cuadrada", "ventana": True, "semilla": None}
    assert convertir(DECL, {"radio": 5, "tasa": 1, "ventana": 0, "semilla": 7}) == {"radio": 5, "tasa": 1.0, "ventana": False, "semilla": 7}
    assert convertir([], {"lo_que_sea": "x"}) == {"lo_que_sea": "x"}   # mundo sin declaraciones: tal cual


@pytest.mark.parametrize("valores, mensaje", [
    ({"radio": "12"}, r"'radio': 12 fuera del rango \[2, 8\]"),
    ({"radio": "4.5"}, "no es un entero"),
    ({"radio": True}, "booleano"),
    ({"tasa": "mucho"}, "no es un número real"),
    ({"vista": "panoramica"}, "no es uno de oficial, cuadrada"),
    ({"ventana": "quizá"}, "no es un booleano"),
    ({"radio": ""}, "necesita un valor"),
    ({"radiio": 4}, "opción desconocida de prueba: 'radiio'"),
])
def test_valores_invalidos_dan_error_claro(valores, mensaje):
    with pytest.raises(OpcionInvalida, match=mensaje):
        convertir(DECL, valores, "prueba")


def test_con_defectos():
    assert con_defectos(DECL, {"radio": "6"}) == {"radio": 6, "tasa": 0.5, "vista": "oficial", "ventana": False, "semilla": None}


@pytest.mark.parametrize("nombre", sorted(MUNDOS))
def test_cada_mundo_declara_opciones_validas(nombre):
    """O18: cada declaración es válida, su defecto pasa su propia validación y los nombres no se repiten."""
    declaraciones = cargar(nombre).opciones() if nombre != "ajedrez" else _clase(nombre).opciones()
    assert isinstance(declaraciones, list)
    nombres = [d["nombre"] for d in declaraciones]
    assert len(nombres) == len(set(nombres))
    for d in declaraciones:
        assert validar_declaracion(d) == [], d["nombre"]
        assert convertir(declaraciones, {d["nombre"]: d["defecto"]}) == {d["nombre"]: d["defecto"]}
