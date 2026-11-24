"""Secciones de la Memoria con dueño (D7, A7b): registro, manual y legado diferidos, legado por secciones y autor."""

from typing import Any, Dict, List

import pytest

from ida.nucleo.memoria import Memoria, Seccion


class Anotadora(Seccion):
    """Sección de prueba: apunta lo que recibe, en orden, y da su parte del legado."""

    def __init__(self, clave: str, orden: int = 0) -> None:
        self.clave = clave
        self.orden_legado = orden
        self.recibido: List[Any] = []

    def aplicar_manual(self, manual: Dict[str, Any]) -> None:
        self.recibido.append(("manual", manual.get(self.clave)))

    def heredar(self, legado: Dict[str, Any], tasa: float = 1.0) -> int:
        self.recibido.append(("legado", legado.get(self.clave), tasa))
        return 1 if self.clave in legado else 0

    def legado(self, ahora: int) -> Dict[str, Any]:
        return {self.clave: ahora}


def test_nombre_repetido_es_error() -> None:
    mem = Memoria()
    mem.registrar_seccion("a", "Uno", Anotadora("a"))
    with pytest.raises(ValueError):
        mem.registrar_seccion("a", "Otro", Anotadora("a"))


def test_manual_y_legado_diferidos_en_orden() -> None:
    mem = Memoria()
    mem.aplicar_manual({"hechos": [], "a": 1})
    mem.heredar({"a": 2}, tasa=0.5)
    assert not mem.tiene_seccion("a")
    s = Anotadora("a")
    mem.registrar_seccion("a", "Uno", s)
    assert s.recibido == [("manual", 1), ("legado", 2, 0.5)]
    assert mem.heredados == 1
    mem.heredar({"a": 3})          # ya registrada: le llega en el momento
    assert s.recibido[-1] == ("legado", 3, 1.0)
    assert mem.heredados == 2


def test_memoria_apagada_no_difiere() -> None:
    mem = Memoria("apagada")
    mem.aplicar_manual({"hechos": [], "a": 1})
    mem.heredar({"a": 2})
    s = Anotadora("a")
    mem.registrar_seccion("a", "Uno", s)
    assert s.recibido == [] and s.activa is False


def test_legado_por_secciones_en_su_orden() -> None:
    mem = Memoria()
    mem.registrar_seccion("z", "Uno", Anotadora("z", orden=2))
    mem.registrar_seccion("y", "Otro", Anotadora("y", orden=1))
    legado = mem.legado(7)
    assert list(legado) == ["proposiciones", "registros", "y", "z"]
    assert legado["y"] == 7 and legado["z"] == 7


def test_lectura_libre_y_escritura_solo_del_dueño() -> None:
    mem = Memoria()
    s = Anotadora("a")
    mem.registrar_seccion("a", "Uno", s)
    assert mem.seccion("a") is s and mem.dueño("a") == "Uno"
    assert mem.seccion_propia("a", "Uno") is s
    with pytest.raises(PermissionError):
        mem.seccion_propia("a", "Otro")
    with pytest.raises(KeyError):
        mem.seccion("b")


def test_las_secciones_son_independientes() -> None:
    """Cada sección recibe el manual y el legado enteros y toma lo suyo: lo que recibe una no depende de otra."""
    mem = Memoria()
    mem.aplicar_manual({"hechos": [], "a": 1, "b": 10})
    a, b = Anotadora("a"), Anotadora("b")
    mem.registrar_seccion("b", "Dos", b)
    mem.registrar_seccion("a", "Uno", a)
    assert a.recibido == [("manual", 1)] and b.recibido == [("manual", 10)]
