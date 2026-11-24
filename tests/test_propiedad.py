"""Propiedad de las piezas (decisión 14): cada componente emite y modifica solo piezas de su tipo,
y solo a través de la Onda. Excepciones transitorias hasta el bloque C: proponer ``Accion`` y que
un ``Impulso`` module arousal y confianza de ``Accion``."""

import pathlib
import re

import pytest

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.azar import Azar
from ida.nucleo.linaje import Arquetipo
from ida.nucleo.memoria import Memoria
from ida.nucleo.mundo import Perfil
from ida.nucleo.onda import EXCEPCIONES_TRANSITORIAS, Onda, PiezaAjena
from ida.nucleo.soma import Soma
from ida.nucleo.vocabulario import Verbo

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


class _Accion(Componente):
    tipo = "Accion"


def test_sin_excepciones_solo_accion_propone_y_nadie_modula_acciones_ajenas():
    """C3.5: se quitaron las dos excepciones transitorias del bloque B."""
    assert EXCEPCIONES_TRANSITORIAS == {}
    ctx = _ctx(Onda(1, 100, 1e9))
    v, imp, acc = _montar(_Valor()), _montar(_Impulso()), _montar(_Accion())
    with pytest.raises(PiezaAjena):                    # otro tipo ya no propone acciones
        v.proponer(ctx, Verbo.MOVER, "celda", 0.5, 0.6, "prueba")
    c = acc.proponer(ctx, Verbo.MOVER, "celda", 0.5, 0.6, "prueba")
    assert c is not None and "excepcion" not in c.registro[-1]
    with pytest.raises(PiezaAjena):                    # un Impulso ya no modula acciones
        imp.modificar(ctx, c, arousal=0.2)
    with pytest.raises(PiezaAjena):
        v.modificar(ctx, c, arousal=0.9)
    assert c.arousal == pytest.approx(0.5) and ctx.onda.excepciones == {}


def test_el_core_queda_exento():
    onda = Onda(1, 100, 1e9)
    v = _montar(_Valor(), "CORE")
    ctx = _ctx(onda)
    onda.exento = True
    v.percibir(ctx, v.pieza(ctx, "x", 0.5, tipo="Exterocepcion"))
    onda.exento = False
    assert "x" in onda.ev("Exterocepcion")


def test_metadatos_origen_registro_acotado_y_audit():
    from ida.nucleo.pieza import MAX_REGISTRO, Pieza

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
