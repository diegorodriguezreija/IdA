"""Estrategias (bloque C): tipo de pieza, progreso, agotamiento y conservación entre latidos."""

import pytest

from ida.core import estrategia as est
from ida.core.arquitectura import Componente, Contexto
from ida.core.azar import Azar
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.mundo import Perfil
from ida.core.onda import Onda, PiezaAjena
from ida.core.soma import Soma
from ida.core.vocabulario import Verbo


class _Estrategia(Componente):
    tipo = "Estrategia"


class _Otro(Componente):
    tipo = "Valor"


class _Huir(est.Definicion):
    nombre = "huir"
    impulsos = ("seguridad",)


def _ctx(onda: Onda) -> Contexto:
    return Contexto(onda, Soma(), Memoria(), Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER})


def _comp(cls):
    c = cls()
    c.sistema = "S1"
    return c


def test_pieza_estrategia_y_progreso_sobre_la_intensidad_cruda():
    p = est.nueva("S1", _Huir(), "seguridad", 0.8, 0.0, latido=5)
    assert p.id == "S1:huir:seguridad" and p.tipo == "Estrategia" and p.carga["estado"] == est.ACTIVA
    assert p.carga["valor_inicial"] == pytest.approx(0.8) and p.carga["inicio"] == 5
    assert est.progreso(p.carga, 0.4) == pytest.approx(0.5)
    assert est.progreso(p.carga, 0.9) == 0.0 and est.progreso(p.carga, 0.0) == 1.0


def test_agotamiento_tras_la_gracia_sube_sin_progreso_y_baja_con_el():
    p = est.nueva("S1", _Huir(), "seguridad", 0.8, 0.0, latido=0)
    c = dict(p.carga)
    c.update(est.avanzar(c, 0.8, True, latido=2, gracia=3, ritmo_esperado=0.02))    # en la gracia: no sube
    assert c["agotamiento"] == 0.0 and c["esfuerzo"] == 1
    for t in range(3, 8):
        c.update(est.avanzar(c, 0.8, False, latido=t, gracia=3, ritmo_esperado=0.02))
    assert c["agotamiento"] == pytest.approx(5 * est.SUBIDA_AGOTAMIENTO) and c["esfuerzo"] == 1
    c.update(est.avanzar(c, 0.4, True, latido=8, gracia=3, ritmo_esperado=0.02))      # progresa: baja
    assert c["agotamiento"] == pytest.approx(5 * est.SUBIDA_AGOTAMIENTO - est.BAJADA_AGOTAMIENTO)


def test_la_onda_conserva_las_estrategias_entre_latidos_y_comprueba_la_propiedad():
    activas: dict = {}
    onda1 = Onda(1, 10, 1e9, estrategias=activas)
    ctx1, e = _ctx(onda1), _comp(_Estrategia)
    p = onda1.activar(est.nueva("S1", _Huir(), "seguridad", 0.8, 0.0, 1), e)
    assert onda1.ef("Estrategia")[p.id] is p and onda1.amplitud_consumida == 0      # estado, no atención
    with pytest.raises(PiezaAjena):
        onda1.activar(est.nueva("S1", _Huir(), "otra", 0.5, 0.0, 1), _comp(_Otro))
    onda2 = Onda(2, 10, 1e9, estrategias=activas)
    assert onda2.estrategias[p.id] is p                                              # sigue activa
    onda2.cerrar(p, est.AGOTADA, e)
    assert p.id not in activas and p.carga["estado"] == est.AGOTADA
    assert ctx1.onda is onda1
