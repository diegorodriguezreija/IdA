"""P0: la medición de Crafter cuenta pasos del entorno (``env.step``) y no pasa del presupuesto.

Un latido ejecuta hasta ``max_sinergia`` primitivas del cuerpo y cada una es un ``env.step``. Con ``contar="entorno"``
la suma de ``pasos`` del JSON es el número de ``env.step`` ejecutados y el total queda en [N, N + max_sinergia - 1]
(el entorno solo se comprueba entre latidos: la segunda primitiva de una sinergia puede dar un paso de más). Con
``contar="latidos"`` (la contabilidad anterior) la decisión de IdA es la misma: las mismas acciones, latido a latido.
"""

import os
import sys
from typing import Any, List, Tuple

import pytest

pytest.importorskip("crafter")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))

import crafter  # noqa: E402

import equivalencia as eq  # noqa: E402
import evaluar_crafter as ev  # noqa: E402
import resumen_evaluacion as re_  # noqa: E402

CONFIG = {"vista": "oficial", "sin_herencia": True, "manual": "estricto", "quiet": True, "plazo_logico": 40.0}


def _max_sinergia() -> int:
    from ida.mundos import cargar
    return int(cargar("crafter")(vista="oficial").registro().cuerpo._motor.max_sinergia)


def _contar_env_step(monkeypatch: pytest.MonkeyPatch) -> List[int]:
    """Envuelve ``crafter.Env.step`` y devuelve una lista cuyo único elemento cuenta las llamadas."""
    cuenta = [0]
    original = crafter.Env.step

    def step(self: Any, accion: Any) -> Any:
        cuenta[0] += 1
        return original(self, accion)

    monkeypatch.setattr(crafter.Env, "step", step)
    return cuenta


@pytest.mark.parametrize("presupuesto, longitud", [(150, 60), (97, 10000)])
def test_pasos_del_json_son_los_env_step(monkeypatch, presupuesto, longitud):
    cuenta = _contar_env_step(monkeypatch)
    res = ev.evaluar(presupuesto, 31, longitud_episodio=longitud, **CONFIG)
    assert res["contabilidad"] == "entorno"
    assert sum(ep["pasos"] for ep in res["por_episodio"]) == cuenta[0] == res["pasos"] == res["pasos_entorno"]
    assert sum(ep["latidos"] for ep in res["por_episodio"]) == res["latidos"]
    assert res["latidos"] <= res["pasos"]
    assert res["primitivas_por_latido"] == round(res["pasos"] / res["latidos"], 4)
    # el presupuesto se agota y no se pasa salvo por la segunda primitiva de una sinergia (documentado)
    assert presupuesto <= res["pasos"] <= presupuesto + _max_sinergia() - 1
    # ningún episodio pasa de su longitud más ese mismo paso de más
    assert all(ep["pasos"] <= longitud + _max_sinergia() - 1 for ep in res["por_episodio"])


def test_contabilidad_antigua_cuenta_latidos(monkeypatch):
    cuenta = _contar_env_step(monkeypatch)
    res = ev.evaluar(120, 31, contar="latidos", **CONFIG)
    assert res["contabilidad"] == "latidos"
    assert res["pasos"] == res["latidos"] == 120 == sum(ep["pasos"] for ep in res["por_episodio"])
    assert res["pasos_entorno"] == cuenta[0] == sum(ep["pasos_entorno"] for ep in res["por_episodio"])


def test_contabilidad_desconocida():
    with pytest.raises(ValueError):
        ev.evaluar(10, 31, contar="primitivas", **CONFIG)


def test_misma_decision_con_las_dos_contabilidades():
    """Las mismas acciones (episodio, latido, verbo, objetivo) en los primeros 150 latidos con las dos contabilidades.
    Con la nueva se da presupuesto de sobra (300 pasos del entorno) para que el corte del último episodio no caiga
    dentro de los latidos comparados."""
    antigua: List[Tuple[int, int, str, str]] = []
    nueva: List[Tuple[int, int, str, str]] = []
    ev.evaluar(150, 31, contar="latidos", traza=antigua, **CONFIG)
    ev.evaluar(300, 31, contar="entorno", traza=nueva, **CONFIG)
    assert len(antigua) == 150 and len(nueva) >= 150
    assert nueva[:150] == antigua


def test_resumen_avisa_si_se_mezclan_contabilidades():
    ep = {"logros": ["collect_wood"]}
    viejo = {"semilla_base": 31, "tasas_logros": {"collect_wood": 100.0}, "por_episodio": [ep]}   # sin el campo: latidos
    nuevo = {**viejo, "contabilidad": "entorno"}
    assert re_.contabilidad(viejo) == "latidos"
    assert re_.comparar_pareado(nuevo, nuevo)["avisos"] == []
    assert re_.comparar_pareado(viejo, {**viejo, "contabilidad": "latidos"})["avisos"] == []
    avisos = re_.comparar_pareado(nuevo, viejo)["avisos"]
    assert len(avisos) == 1 and "entorno" in avisos[0] and "latidos" in avisos[0]


def test_equivalencia_ignora_las_claves_nuevas_solo_si_la_base_no_las_tiene():
    base = {"pasos": 10, "por_episodio": [{"pasos": 10}]}
    actual = {"pasos": 10, "contabilidad": "latidos", "latidos": 10, "pasos_entorno": 11, "primitivas_por_latido": 1.1,
              "ms_por_latido": 3.0, "por_episodio": [{"pasos": 10, "latidos": 10, "pasos_entorno": 11}]}
    assert eq.comparar_estructuras(base, actual) == []
    assert eq.comparar_estructuras({**base, "pasos_entorno": 12}, actual) != []     # si la base la tiene, se compara
    assert eq.comparar_estructuras({**base, "pasos": 9}, actual) != []
    assert eq.argumentos_contabilidad(RAIZ) == ["--contar", "latidos"]
