"""Propiedad de las piezas (decisión 14): cada componente emite y modifica solo piezas de su tipo,
y solo a través de la Onda. Excepciones transitorias hasta el bloque C: proponer ``Accion`` y que
un ``Impulso`` module arousal y confianza de ``Accion``."""

import pathlib
import re

import pytest

from ida.core.arquitectura import Componente, Contexto
from ida.core.azar import Azar
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.mundo import Perfil
from ida.core.onda import EXCEPCIONES_TRANSITORIAS, Onda, PiezaAjena
from ida.core.soma import Soma
from ida.core.vocabulario import Verbo

RAIZ = pathlib.Path(__file__).resolve().parent.parent / "ida"


def _ctx(onda: Onda) -> Contexto:
    return Contexto(onda, Soma(), Memoria(), Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER, Verbo.ESPERAR})


class _Valor(Componente):
    tipo = "Valor"


class _Impulso(Componente):
    tipo = "Impulso"


def _montar(comp: Componente, sistema: str = "S2") -> Componente:
    comp.sistema = sistema
    return comp


def test_emitir_un_tipo_ajeno_se_rechaza():
    ctx = _ctx(Onda(1, 100, 1e9))
    v = _montar(_Valor())
    with pytest.raises(PiezaAjena):
        v.percibir(ctx, v.pieza(ctx, "x", 0.5, tipo="Objeto"))
    with pytest.raises(PiezaAjena):
        v.registrar(ctx, v.pieza(ctx, "x", 0.5, tipo="Objeto"))
    assert not ctx.onda.ev("Objeto") and not ctx.onda.reactiva.ef.get("Objeto")


def test_modificar_solo_el_dueno_y_queda_en_el_registro():
    ctx = _ctx(Onda(3, 100, 1e9))
    v = _montar(_Valor())
    p = v.percibir(ctx, v.pieza(ctx, "seta", 0.4))
    v.modificar(ctx, p, arousal=0.7, carga={"valencia": -0.5})
    assert p.arousal == pytest.approx(0.7) and p.carga["valencia"] == -0.5 and p.actualizada == 3
    ultima = p.registro[-1]
    assert ultima["op"] == "modificar" and ultima["autor"] == "S2._Valor" and ultima["cambios"]["arousal"] == (0.4, 0.7)
    with pytest.raises(PiezaAjena):
        _montar(_Impulso()).modificar(ctx, p, arousal=0.1)
    assert p.arousal == pytest.approx(0.7)


def test_excepciones_transitorias_acotadas():
    ctx = _ctx(Onda(1, 100, 1e9))
    v, imp = _montar(_Valor()), _montar(_Impulso())
    c = v.proponer(ctx, Verbo.MOVER, "celda", 0.5, 0.6, "prueba")    # cualquiera propone Accion
    assert c is not None and c.registro[-1]["excepcion"] == "proponer_accion"
    imp.modificar(ctx, c, arousal=0.2, confianza=0.3, entrada="S2:prueba")
    assert c.arousal == pytest.approx(0.2) and c.entradas[-1] == "S2:prueba"
    assert c.registro[-1]["excepcion"] == "impulso_modula_accion"
    assert ctx.onda.excepciones == {"proponer_accion": 1, "impulso_modula_accion": 1}
    assert set(ctx.onda.excepciones) <= set(EXCEPCIONES_TRANSITORIAS)
    with pytest.raises(PiezaAjena):                    # Impulso no puede tocar la carga de una Accion
        imp.modificar(ctx, c, carga={"objetivo": "otra"})
    with pytest.raises(PiezaAjena):                    # ni otro tipo modularla
        v.modificar(ctx, c, arousal=0.9)


def test_el_core_queda_exento():
    onda = Onda(1, 100, 1e9)
    v = _montar(_Valor(), "CORE")
    ctx = _ctx(onda)
    onda.exento = True
    v.percibir(ctx, v.pieza(ctx, "x", 0.5, tipo="Exterocepcion"))
    onda.exento = False
    assert "x" in onda.ev("Exterocepcion")


def test_metadatos_origen_registro_acotado_y_audit():
    from ida.core.pieza import MAX_REGISTRO, Pieza

    ctx = _ctx(Onda(5, 100, 1e9))
    v = _montar(_Valor())
    p = v.percibir(ctx, v.pieza(ctx, "seta", 0.4, decay=0.1, cost=1.0))
    for i in range(MAX_REGISTRO + 5):
        v.modificar(ctx, p, arousal=i / 100)
    assert p.origen == "S2._Valor" and len(p.registro) == MAX_REGISTRO
    assert p.registro[-1]["cambios"]["arousal"][1] == pytest.approx((MAX_REGISTRO + 4) / 100)
    a = p.audit
    assert a["creada"] == 5 and a["actualizada"] == 5 and a["origen"] == "S2._Valor" and len(a["registro"]) == MAX_REGISTRO
    assert p.decay == pytest.approx(0.1) and p.cost == 1.0 and p.fitness is None
    assert Pieza("x", "T", 0.5, decay=0.9, origen="otro") == Pieza("x", "T", 0.5)   # los metadatos no cuentan en la igualdad


# Revisión estática: los sistemas y los mundos no mutan piezas ni escriben en la Onda directamente.
MUTACION = re.compile(r"\.(arousal|confianza)\s*(=|\+=|-=|\*=)(?!=)|\.carga\[[^\]]+\]\s*=(?!=)"
                      r"|\.carga\.(update|setdefault|pop)\(|\.entradas\.(append|extend)\(")
ESCRITURA_DIRECTA = re.compile(r"ctx\.onda\.(percibir|registrar|proponer|modificar)\(|\.reactiva\.(ev|acc|ef)\b")


@pytest.mark.parametrize("ruta", sorted([*(RAIZ / "sistemas").rglob("*.py"), *(RAIZ / "mundos").rglob("*.py")]), ids=lambda r: r.name)
def test_sin_mutaciones_directas(ruta):
    for n, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
        codigo = linea.split("#", 1)[0]
        assert not MUTACION.search(codigo), f"{ruta.name}:{n} muta una pieza sin pasar por la Onda: {linea.strip()}"
        assert not ESCRITURA_DIRECTA.search(codigo), f"{ruta.name}:{n} escribe en la Onda sin pasar por Componente: {linea.strip()}"
