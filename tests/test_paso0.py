"""Paso 0 de la fase de generalización (docs/PROPUESTA_PASO0.md): la intensidad del impulso llega al Tribunal.

- 0a: urgencia local en ``Tribunal.reactiva`` (interruptor ``Perfil.mecanismos.urgencia_local``).
"""

from dataclasses import replace
from typing import Dict, List, Tuple

import pytest

from ida.core.arquitectura import Contexto
from ida.core.azar import Azar
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.mundo import MecanismosMemoria, Perfil
from ida.core.onda import Onda
from ida.core.pieza import Pieza
from ida.core.sentidos import Tribunal
from ida.core.soma import Soma
from ida.core.vocabulario import Verbo

CON_0A = Perfil(mecanismos=MecanismosMemoria(urgencia_local=True))


def _candidato(id_: str, impulso: str, arousal: float, confianza: float) -> Pieza:
    return Pieza(id_, "Accion", arousal, confianza, {"verbo": Verbo.MOVER, "objetivo": id_, "clase": "", "motivo": "", "datos": {},
                                                    "origen": {"impulso": impulso, "estrategia": f"est:{id_}"}}, sistema="S1")


def _decidir(perfil: Perfil, estres: float, impulsos: Dict[str, Tuple[str, float]],
             candidatos: List[Tuple[str, str, float, float]]) -> Tuple[str, list]:
    """Un Tribunal con ``impulsos`` (nombre → (canal, intensidad)) y ``candidatos`` (id, impulso, arousal, confianza)."""
    onda = Onda(1, 100, 1e9)
    for nombre, (canal, intensidad) in impulsos.items():
        onda.registrar(canal, Pieza(nombre, canal, intensidad, carga={"intensidad": intensidad, "objetivo": 0.0, "rasgo": None}))
    for c in candidatos:
        onda.proponer("Accion", _candidato(*c))
    ctx = Contexto(onda, Soma(estres=estres), Memoria(), Arquetipo(), Azar(1), perfil, set(Verbo), None, True)
    t = Tribunal()
    t.sistema = "CORE"
    t.reactiva(ctx)
    return ctx.extra["decision"].carga["objetivo"], onda.notas["evaluados"]


def test_interruptor_apagado_por_defecto():
    assert Perfil().mecanismos.urgencia_local is False


def test_urgencia_por_debajo_del_umbral_es_nula():
    assert Tribunal.UMBRAL_URGENCIA == 0.5
    assert Tribunal.urgencia(0.0) == 0.0 and Tribunal.urgencia(0.5) == 0.0
    assert Tribunal.urgencia(0.75) == pytest.approx(0.5)
    assert Tribunal.urgencia(1.0) == pytest.approx(1.0)


@pytest.mark.parametrize("semilla", range(20))
def test_invariancia_por_construccion_con_todas_las_intensidades_bajo_u(semilla):
    """Con todas las intensidades < U, encender 0a no cambia ninguna puntuación ni la decisión."""
    azar = Azar(semilla)
    impulsos = {f"n{i}": ("Impulso", round(azar.uniforme(0.0, 0.4999), 4)) for i in range(4)}
    candidatos = [(f"c{j}", f"n{j % 4}", round(azar.uniforme(0.0, 1.0), 3), round(azar.uniforme(0.35, 1.0), 3)) for j in range(6)]
    estres = round(azar.uniforme(0.0, 1.0), 3)
    sin = _decidir(Perfil(), estres, impulsos, candidatos)
    con = _decidir(CON_0A, estres, impulsos, candidatos)
    assert sin == con


def test_necesidad_apurada_gana_a_otra_con_mas_confianza_y_menos_urgencia():
    """En calma (estrés 0,1), la propuesta de una necesidad a 0,95 pierde sin 0a frente a otra de confianza 0,9
    cuyo impulso está a 0,1, y gana con 0a: su estrés local es u(0,95) = 0,9."""
    impulsos = {"sed": ("Impulso", 0.95), "cobijo": ("Impulso", 0.1)}
    candidatos = [("beber", "sed", 0.95, 0.5), ("refugio", "cobijo", 0.3, 0.9)]
    sin, ev_sin = _decidir(Perfil(), 0.1, impulsos, candidatos)
    con, ev_con = _decidir(CON_0A, 0.1, impulsos, candidatos)
    assert sin == "refugio"
    assert con == "beber"
    base = {e["id"]: e["base"] for e in ev_con}
    assert base["beber"] == pytest.approx(0.95 * 0.9 + 0.5 * 0.1, abs=1e-3)
    assert base["refugio"] == pytest.approx(0.3 * 0.1 + 0.9 * 0.9, abs=1e-3)   # su impulso está bajo U: estrés global


def test_con_estres_global_mayor_manda_el_global():
    """El estrés local es el máximo: con el cuerpo más estresado que la urgencia del impulso, no cambia nada."""
    impulsos = {"sed": ("Impulso", 0.6), "cobijo": ("Impulso", 0.1)}       # u(0,6) = 0,2 < 0,7
    candidatos = [("beber", "sed", 0.7, 0.5), ("refugio", "cobijo", 0.3, 0.9)]
    assert _decidir(Perfil(), 0.7, impulsos, candidatos) == _decidir(CON_0A, 0.7, impulsos, candidatos)


def test_las_intenciones_de_intensidad_fija_no_cambian():
    """Las intenciones del mundo tienen intensidad fija 0,5 (= U): su urgencia es 0 y su puntuación no cambia."""
    impulsos = {"progresar": ("Intencion", 0.5), "hambre": ("Impulso", 0.3)}
    candidatos = [("fabricar", "progresar", 0.5, 0.6), ("comer", "hambre", 0.65, 0.7)]
    for estres in (0.0, 0.3, 0.9):
        _, ev_sin = _decidir(Perfil(), estres, impulsos, candidatos)
        _, ev_con = _decidir(CON_0A, estres, impulsos, candidatos)
        assert ev_sin == ev_con


def test_el_interruptor_se_combina_con_los_demas_mecanismos():
    m = replace(MecanismosMemoria(), urgencia_local=True)
    assert m.urgencia_local and not m.buffer and not m.plan
