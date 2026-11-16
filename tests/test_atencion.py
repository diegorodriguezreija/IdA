"""Atención de la Onda (decisiones 15 y 18): amplitud, potencia y fuerza máxima por pieza."""

import pytest

from ida.core.arquitectura import Componente, Contexto
from ida.core.azar import Azar
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.mundo import Perfil
from ida.core.onda import LatidoAgotado, Onda
from ida.core.soma import Soma
from ida.core.vocabulario import Verbo


class _Valor(Componente):
    tipo = "Valor"


class _Impulso(Componente):
    tipo = "Impulso"


def _ctx(onda: Onda) -> Contexto:
    return Contexto(onda, Soma(), Memoria(), Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER})


def _comp(cls, sistema="S2"):
    c = cls()
    c.sistema = sistema
    return c


def test_pieza_nueva_cuesta_amplitud_y_su_arousal_en_potencia():
    onda = Onda(1, 10, 1e9, potencia_max=10.0)
    ctx, v = _ctx(onda), _comp(_Valor)
    v.percibir(ctx, v.pieza(ctx, "a", 0.6))
    assert onda.amplitud_consumida == 1 and onda.potencia_consumida == pytest.approx(0.6)
    v.registrar(ctx, v.pieza(ctx, "b", 0.9))                  # solo ef: no es atención
    assert onda.amplitud_consumida == 1 and onda.potencia_consumida == pytest.approx(0.6)
    v.percibir(ctx, v.pieza(ctx, "a", 0.2))                   # mismo id: sustituye, no ocupa más
    assert onda.amplitud_consumida == 1 and onda.potencia_consumida == pytest.approx(1.0)
    assert onda.consumo["S2"] == {"amplitud": 1.0, "potencia": pytest.approx(1.0), "rechazos_amplitud": 0.0, "recortes_potencia": 0.0}


def test_cambiar_arousal_cuesta_al_subir_y_al_bajar():
    onda = Onda(1, 10, 1e9, potencia_max=10.0)
    ctx, v = _ctx(onda), _comp(_Valor)
    p = v.percibir(ctx, v.pieza(ctx, "a", 0.5))
    v.modificar(ctx, p, arousal=0.8)
    v.modificar(ctx, p, arousal=0.3)
    v.modificar(ctx, p, confianza=0.1, carga={"x": 1})       # sin cambio de arousal: sin coste
    assert onda.potencia_consumida == pytest.approx(0.5 + 0.3 + 0.5)


def test_fuerza_maxima_por_pieza_recorta_el_cambio():
    onda = Onda(1, 10, 1e9, potencia_max=4.0)                  # fuerza máx. 0,4
    ctx, v, imp = _ctx(onda), _comp(_Valor), _comp(_Impulso)
    p = v.percibir(ctx, v.pieza(ctx, "a", 0.9))
    assert p.arousal == pytest.approx(0.4) and p.registro[-1]["cambios"]["arousal_limitado"] == (0.9, pytest.approx(0.4))
    c = v.proponer(ctx, Verbo.MOVER, "x", 0.3, 0.5, "prueba")
    imp.modificar(ctx, c, arousal=1.0)
    assert c.arousal == pytest.approx(0.7)


def test_dentro_de_los_sistemas_nada_es_gratis_y_el_core_exento_si():
    onda = Onda(1, 10, 1e9)
    ctx, v = _ctx(onda), _comp(_Valor)
    v.percibir(ctx, v.pieza(ctx, "a", 0.0))
    assert onda.amplitud_consumida == 1
    onda.exento = True
    v.percibir(ctx, v.pieza(ctx, "b", 1.0, tipo="Valor"))
    onda.exento = False
    assert onda.amplitud_consumida == 1 and onda.potencia_consumida == 0.0


def test_potencia_agotada_recorta_sin_cortar_el_latido():
    onda = Onda(1, 10, 1e9, potencia_max=1.0)                  # fuerza máx. 0,1
    ctx, v = _ctx(onda), _comp(_Valor)
    p = v.percibir(ctx, v.pieza(ctx, "a", 0.1))
    for i in range(20):                                         # cada vaivén cuesta 0,1
        v.modificar(ctx, p, arousal=0.0 if i % 2 == 0 else 0.1, confianza=0.5)
    assert onda.potencia_consumida == pytest.approx(1.0) and not onda.guillotina
    assert p.confianza == 0.5                                   # sin potencia, lo demás sigue
    assert onda.consumo["S2"]["recortes_potencia"] >= 1
    q = v.percibir(ctx, v.pieza(ctx, "b", 0.1))                # pieza nueva sin potencia: entra con arousal 0
    assert "b" in onda.ev("Valor") and q.arousal == 0.0


def test_solo_el_plazo_corta_el_latido():
    tiempo = [0.0]
    onda = Onda(1, 10, 50.0, reloj=lambda: tiempo[0])
    ctx, v = _ctx(onda), _comp(_Valor)
    v.percibir(ctx, v.pieza(ctx, "a", 0.1))
    tiempo[0] = 0.051
    with pytest.raises(LatidoAgotado, match="plazo"):
        v.percibir(ctx, v.pieza(ctx, "b", 0.1))


def test_el_core_escribe_con_autor_sin_pagar_y_percibir_devuelve_none_si_se_rechaza():
    from ida.core.onda import AutorCore
    from ida.core.pieza import Pieza

    onda = Onda(1, 1, 1e9, potencia_max=0.1)
    ctx, v = _ctx(onda), _comp(_Valor)
    assert v.percibir(ctx, v.pieza(ctx, "a", 0.0)) is not None
    assert v.percibir(ctx, v.pieza(ctx, "b", 0.0)) is None                 # sin amplitud: rechazada
    s = Pieza("sorpresa_1", "Sorpresa", arousal=0.85)
    assert onda.percibir("Sorpresa", s, autor=AutorCore("Sorpresa"))         # el Core no paga ni se recorta
    assert s.arousal == 0.85 and s.registro[-1]["autor"] == "CORE.Organismo"
    assert onda.amplitud_consumida == 1 and onda.potencia_consumida == 0.0
