"""Paso 2.3: el adaptador de Crafter lee el manual (estricto o ampliado)."""

import pytest

pytest.importorskip("crafter")

from ida.core.memoria import Memoria  # noqa: E402
from ida.core.vocabulario import Verbo  # noqa: E402


def test_crafter_lee_el_manual():
    from ida.mundos.crafter import MundoCrafter

    estricto = MundoCrafter(vista="oficial")
    assert estricto.peligrosos == {"zombi", "esqueleto", "flecha", "lava"}
    assert estricto.utiles == {"arbol", "piedra", "carbon", "hierro", "diamante", "mesa", "horno"}
    req = {(h["verbo"], h["objetivo"]): h for h in estricto.manual()["hechos"] if h["tipo"] == "requisito"}
    assert req[("USAR", "place_table")]["requiere_inventario"] == {"wood": None}   # claves del inventario percibido

    ampliado = MundoCrafter(vista="oficial", manual="ampliado")
    m = Memoria()
    m.aplicar_manual(ampliado.manual())
    assert m.requisitos[(Verbo.USAR, "place_table")].requiere_inventario == {"wood": 2}
    assert m.requisitos[(Verbo.COGER, "hierro")].requiere_inventario == {"stone_pickaxe": 1}
    assert "health" not in (m.claves_inventario or set())

    estricto.reiniciar(1)
    assert not any("peligro" in e.rasgos for e in estricto.observar().entidades)   # paso 6: lo calcula la base
    m = Memoria()
    m.aplicar_manual(estricto.manual())
    assert all(m.peligrosa(c) for c in estricto.peligrosos)                       # el manual da el previo
    with pytest.raises(ValueError):
        MundoCrafter(manual="otro")
