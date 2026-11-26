"""Registro del latido v1 (T1): esquema, observador y hechos deducidos."""

import copy
from typing import Any, Dict, List, Optional

import pytest

from ida.consola import linea
from ida.ejecutor import ejecutar
from ida.telemetria.esquema import HECHOS, NIVELES, es_valido, validar
from ida.telemetria.observador import Observador


def _vida(tmp_path, nivel: Optional[str], semilla: int = 1, latidos: int = 40, mundo: str = "minimo") -> List[Dict[str, Any]]:
    """Una vida con plazo lógico: los registros (o, sin observador, lo que decide en cada latido)."""
    salida: List[Dict[str, Any]] = []

    def al_latir(o: Any, onda: Any, registro: Optional[Dict[str, Any]]) -> None:
        ej = onda.reactiva.ef.get("Accion", {}).get("Accion")
        salida.append(registro if registro is not None else
                      {"latido": onda.ciclo, "verbo": ej.carga["verbo"].value if ej else "", "soma": o.soma.valores()})

    ejecutar(mundo, latidos=latidos, semilla=semilla, consola=False, datos=str(tmp_path / f"d_{nivel}_{semilla}"),
             al_latir=al_latir, nivel=nivel, plazo_logico=40, tabula_rasa=True)
    return salida


@pytest.fixture(scope="module")
def registros(tmp_path_factory) -> Dict[str, List[Dict[str, Any]]]:
    base = tmp_path_factory.mktemp("obs")
    return {n: _vida(base, n) for n in NIVELES}


# --- esquema ----------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("nivel", NIVELES)
def test_los_registros_reales_cumplen_el_esquema(registros, nivel):
    regs = registros[nivel]
    assert len(regs) == 40
    for r in regs:
        assert validar(r) == [], (r["latido"], validar(r)[:3])
        assert r["v"] == 1 and r["nivel"] == nivel


def test_cada_nivel_incluye_al_anterior(registros):
    vital, cognitivo, completo = (set(registros[n][5]) for n in NIVELES)
    assert vital < cognitivo < completo
    assert {"onda", "tribunal", "estrategias", "saber"} <= cognitivo - vital
    assert {"tiempos_ms", "fases", "piezas"} <= completo - cognitivo


def test_las_piezas_llevan_su_autoria(registros):
    r = registros["completo"][10]
    assert r["onda"]["piezas"] and all(p["origen"] for p in r["onda"]["piezas"])
    assert all(isinstance(p["registro"], list) and p["registro"] for p in r["piezas"])
    assert r["tribunal"]["candidatos"] and r["tribunal"]["ganador"]["id"] in {c["id"] for c in r["tribunal"]["candidatos"]}


def _registro_valido(registros) -> Dict[str, Any]:
    return copy.deepcopy(registros["cognitivo"][3])


@pytest.mark.parametrize("estropear, mensaje", [
    (lambda r: r.update(v=2), "v:"),
    (lambda r: r.update(nivel="todo"), "nivel:"),
    (lambda r: r.pop("cuerpo"), "cuerpo: falta"),
    (lambda r: r["cuerpo"].update(vitalidad="mucha"), "cuerpo.vitalidad"),
    (lambda r: r["ritmo"].update(amplitud=[1, "dos"]), "ritmo.amplitud[1]"),
    (lambda r: r.pop("onda"), "onda: falta"),                       # nivel cognitivo sin la Onda
    (lambda r: r["tribunal"].update(candidatos={}), "tribunal.candidatos"),
    (lambda r: r.update(latido=True), "latido"),                    # un booleano no es un entero
    (lambda r: r.update(hechos=[{"tipo": "vuela"}]), "tipo de hecho desconocido"),
    (lambda r: r.update(hechos=[{"tipo": "muere", "causa": "hambre"}]), "hechos[0].latidos: falta"),
    (lambda r: r.update(hechos=[{"tipo": "aprende", "saber": "proposicion", "clase": "baya", "fuente": "experiencia",
                                 "confianza": 0.4}]), "hechos[0].relacion: falta"),
])
def test_registros_invalidos(registros, estropear, mensaje):
    r = _registro_valido(registros)
    estropear(r)
    errores = validar(r)
    assert errores and any(mensaje in e for e in errores), errores


def test_el_esquema_admite_campos_nuevos(registros):
    """Las versiones futuras solo añaden campos: un campo desconocido no invalida un registro v1."""
    r = _registro_valido(registros)
    r["escena"] = {"tipo": "rejilla"}
    r["cuerpo"]["temperatura"] = 36.5
    assert es_valido(r)
    assert validar("no es un registro")


def test_nivel_desconocido():
    with pytest.raises(ValueError):
        Observador("todo")


# --- el observador no cambia la conducta (O3) -----------------------------------------------------------------------
def test_el_observador_no_cambia_la_vida(tmp_path, registros):
    sin = _vida(tmp_path, None)
    con = registros["completo"]
    assert [(s["latido"], s["verbo"], s["soma"]["vitalidad"], s["soma"]["alimentacion"]) for s in sin] == \
        [(c["latido"], c["accion"]["verbo"] if c["accion"] else "", c["cuerpo"]["vitalidad"], c["cuerpo"]["alimentacion"]) for c in con]


# --- consola desde el registro ----------------------------------------------------------------------------------------
def test_linea_de_consola_desde_el_registro(registros):
    r = _registro_valido(registros)
    r.update(latido=7)
    r["ritmo"].update(ms=1.25, plazo_ms=95.0, amplitud=[33, 42], guillotina="")
    r["cuerpo"].update(vitalidad=100.0, alimentacion=98.5, energia=90.9)
    r["afecto"]["estado"] = "CURIOSIDAD"
    r["accion"] = {"verbo": "COMER", "objetivo": "baya_4", "clase": "baya", "sistema": "S1", "exito": False, "mensaje": "",
                   "motivo": "comer baya"}
    r["experiencia"] = {"aprendizaje": ["ahora sabe algo"], "expectativa": "", "cambio_decision": True, "episodio": ""}
    assert linea(r) == ("L0007 [  1.2/95ms A 33/42 ] vit 100.0 ali  98.5 ene  90.9 | CURIOSIDAD | ⇒ COMER baya_4 (S1) «comer baya» ✗\n"
                        "      · experiencia: ahora sabe algo\n"
                        "      · la experiencia cambió la decisión")


# --- hechos (O5) ------------------------------------------------------------------------------------------------------
def _hechos(regs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [dict(h, latido=r["latido"]) for r in regs for h in r["hechos"]]


@pytest.fixture(scope="module")
def vida_que_muere(tmp_path_factory) -> List[Dict[str, Any]]:
    """Mínimo, semilla 6: muere antes de los 300 latidos (plazo lógico 40)."""
    return _vida(tmp_path_factory.mktemp("muere"), "vital", semilla=6, latidos=300)


def test_hechos_de_una_vida_corta(vida_que_muere):
    hechos = _hechos(vida_que_muere)
    tipos = {h["tipo"] for h in hechos}
    assert {"nace", "aprende", "primera_vez", "muere"} <= tipos, tipos
    assert tipos <= set(HECHOS)
    assert vida_que_muere[0]["hechos"][0] == {"tipo": "nace", "individuo": vida_que_muere[0]["individuo"],
                                              "generacion": 1, "heredados": 0}
    final = vida_que_muere[-1]
    muere = [h for h in final["hechos"] if h["tipo"] == "muere"]
    assert len(muere) == 1 and muere[0]["latidos"] == final["latido"] < 300 and muere[0]["causa"]
    assert not final["cuerpo"]["vivo"] and all(r["cuerpo"]["vivo"] for r in vida_que_muere[:-1])


def test_primera_vez_una_sola_vez_por_verbo_y_clase(vida_que_muere):
    primeras = [(h["verbo"], h["clase"]) for h in _hechos(vida_que_muere) if h["tipo"] == "primera_vez"]
    assert primeras and len(primeras) == len(set(primeras))


def test_aprende_coincide_con_la_memoria(vida_que_muere):
    """Cada proposición que aparece en la memoria tiene su «aprende»; y el recuento de demostradas sube con ellos."""
    aprende = [h for h in _hechos(vida_que_muere) if h["tipo"] == "aprende" and h["saber"] == "proposicion"]
    assert aprende and all(h["estado"] in ("hipotesis", "demostrada") for h in aprende)
    nuevas = {(h["clase"], h["relacion"]) for h in aprende}
    total_final = sum(vida_que_muere[-1]["memoria"][k] for k in ("demostradas", "hipotesis", "refutadas"))
    assert len(nuevas) >= total_final > 0


def test_los_hechos_no_dependen_del_nivel(registros):
    vital = _hechos(registros["vital"])
    assert vital == _hechos(registros["cognitivo"]) == _hechos(registros["completo"])
    assert vital[0]["tipo"] == "nace"


def test_cada_vida_tiene_su_nace(tmp_path):
    regs: List[Dict[str, Any]] = []
    ejecutar("minimo", latidos=15, semilla=2, generaciones=2, consola=False, datos=str(tmp_path), nivel="vital",
             plazo_logico=40, tabula_rasa=True, al_latir=lambda _o, _onda, r: regs.append(r))
    nacimientos = [(r["vida"], h["generacion"]) for r in regs for h in r["hechos"] if h["tipo"] == "nace"]
    assert nacimientos == [(1, 1), (2, 2)]
