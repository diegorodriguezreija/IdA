"""T5a (O7, O13; DISENO_OBSERVABILIDAD, sección 14): grabar desde la API, el directo en memoria, las grabaciones y el
mapa de Componentes del Laboratorio. Todo con datos en directorios temporales: nada toca ``datos/`` del proyecto."""

import gzip
import http.client
import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Tuple

import pytest

from ida.telemetria import api_v1, componentes
from ida.telemetria.esquema import validar
from ida.telemetria.grabacion import escenas, leer
from ida.telemetria.laboratorio import Directo, ErrorLab, Grabaciones, ID_GRABACION, Laboratorio, entrada_indice
from ida.telemetria.servidor import WEB, Telemetria

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "herramientas"))
import mapa_componentes as mc  # noqa: E402


# --- ayudas -------------------------------------------------------------------------------------------------------------
@pytest.fixture
def servidor(tmp_path):
    tel = Telemetria(puerto=0, anfitrion="127.0.0.1", modo_antesala=True, datos=str(tmp_path / "datos"))
    try:
        yield tel
    finally:
        tel.detener()


def _pedir(tel, metodo, ruta, cuerpo=None) -> Tuple[int, Any, Dict[str, str]]:
    con = http.client.HTTPConnection("127.0.0.1", tel.puerto, timeout=60)
    h = {"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{tel.puerto}"}
    con.request(metodo, "/api/v1/" + ruta, body=json.dumps(cuerpo).encode() if cuerpo is not None else None, headers=h)
    r = con.getresponse()
    datos = r.read()
    cab = {k.lower(): v for k, v in r.getheaders()}
    con.close()
    tipo = cab.get("content-type", "")
    return r.status, (json.loads(datos) if datos and tipo.startswith("application/json") else datos), cab


def _esperar(condicion, limite=60.0):
    fin = time.monotonic() + limite
    while time.monotonic() < fin:
        if condicion():
            return
        time.sleep(0.05)
    raise AssertionError("no se cumplió a tiempo")


def _vida_entera(tel, **cuerpo) -> Dict[str, Any]:
    """Lanza una vida de mínimo a ritmo máximo y espera a que termine (y a que el Laboratorio lo haya escrito todo)."""
    s, d, _ = _pedir(tel, "POST", "vidas", {"mundo": "minimo", "latidos": 40, "semilla": 3, **cuerpo})
    assert s == 201, d
    _pedir(tel, "POST", "vidas/actual/ritmo", {"ritmo": "max"})
    _esperar(lambda: not tel.vida_actual()["activa"])
    tel.lab.esperar_cola()
    v = tel.vida_actual()
    assert not v.get("error"), v
    return v


def _estable(tel) -> int:
    """El último latido publicado, cuando lleva un rato sin cambiar (la vida está en pausa)."""
    previo = None
    while True:
        time.sleep(0.4)
        r = tel.ultimo_registro
        actual = None if r is None else (r["vida"], r["latido"])
        if actual is not None and actual == previo:
            tel.lab.esperar_cola()
            return int(actual[1])
        previo = actual


# --- grabar desde la API -------------------------------------------------------------------------------------------------
def test_grabar_al_lanzar_listar_descargar_y_borrar_en_dos_pasos(servidor, tmp_path):
    _vida_entera(servidor, grabar=True)
    s, d, _ = _pedir(servidor, "GET", "grabaciones")
    assert s == 200 and d["grabando"] is None and len(d["grabaciones"]) == 1
    g = d["grabaciones"][0]
    assert ID_GRABACION.match(g["id"]) and g["id"].startswith("minimo-")
    assert g["nivel"] == "completo" and g["empieza_tras"] is None and g["valida"] and not g["en_curso"]
    ruta = tmp_path / "datos" / "grabaciones" / f"{g['id']}.jsonl.gz"
    assert ruta.is_file()
    cab, regs = leer(str(ruta))
    assert cab["mundo"] == "minimo" and cab["nivel"] == "completo" and cab["origen"] == "vivero" and cab["semilla"] == 3
    assert g["registros"] == len(regs) and [r["latido"] for r in regs if not r.get("cierre")][:3] == [1, 2, 3]
    for r in regs:
        assert validar(r) == [], r["latido"]
    # descargar: los mismos bytes
    s, cuerpo, cab_http = _pedir(servidor, "GET", f"grabaciones/{g['id']}")
    assert s == 200 and cuerpo == ruta.read_bytes() and cab_http["content-type"] == "application/gzip"
    assert f'filename="{g["id"]}.jsonl.gz"' in cab_http["content-disposition"]
    # borrar: el primer paso no borra
    s, d, _ = _pedir(servidor, "POST", f"grabaciones/{g['id']}/borrar", {})
    assert s == 200 and d["caduca_s"] > 0 and d["grabacion"]["id"] == g["id"] and ruta.is_file()
    testigo = d["testigo"]
    s, d, _ = _pedir(servidor, "POST", f"grabaciones/{g['id']}/borrar/confirmar", {"testigo": "otro"})
    assert s == 400 and d["error"]["codigo"] == "testigo_invalido" and ruta.is_file()
    s, d, _ = _pedir(servidor, "POST", f"grabaciones/{g['id']}/borrar/confirmar", {"testigo": testigo})
    assert s == 200 and d == {"borrada": g["id"]} and not ruta.exists()
    s, d, _ = _pedir(servidor, "POST", f"grabaciones/{g['id']}/borrar/confirmar", {"testigo": testigo})
    assert s == 404 and d["error"]["codigo"] == "grabacion_desconocida"
    assert _pedir(servidor, "GET", "grabaciones")[1]["grabaciones"] == []


def test_grabar_a_media_vida_empieza_en_el_latido_siguiente(servidor, tmp_path):
    s, d, _ = _pedir(servidor, "POST", "vidas", {"mundo": "minimo", "latidos": 60, "semilla": 5})
    assert s == 201
    _pedir(servidor, "POST", "vidas/actual/ritmo", {"ritmo": "pausa"})
    ultimo = _estable(servidor)
    s, d, _ = _pedir(servidor, "POST", "vidas/actual/grabar", {})
    assert s == 201, d
    gid = d["grabacion"]["id"]
    assert d["grabacion"]["empieza_tras"]["latido"] == ultimo
    assert _pedir(servidor, "GET", "vidas/actual")[1]["vida"]["grabacion"]["id"] == gid
    s, d, _ = _pedir(servidor, "POST", "vidas/actual/grabar", {})
    assert s == 409 and d["error"]["codigo"] == "grabacion_en_curso"
    # mientras se graba no se abre, descarga ni borra
    assert _pedir(servidor, "GET", f"grabaciones/{gid}")[1]["error"]["codigo"] == "grabacion_en_curso"
    assert _pedir(servidor, "GET", f"grabaciones/{gid}/indice")[1]["error"]["codigo"] == "grabacion_en_curso"
    assert _pedir(servidor, "POST", f"grabaciones/{gid}/borrar", {})[1]["error"]["codigo"] == "grabacion_en_curso"
    for k in range(1, 4):
        assert _pedir(servidor, "POST", "vidas/actual/paso", {})[0] == 200
        _esperar(lambda k=k: servidor.ultimo_registro["latido"] == ultimo + k)
    servidor.lab.esperar_cola()
    s, d, _ = _pedir(servidor, "POST", "vidas/actual/grabar/terminar", {})
    assert s == 200 and d["grabacion"]["id"] == gid and d["grabacion"]["registros"] == 3 and not d["grabacion"]["en_curso"]
    s, d, _ = _pedir(servidor, "POST", "vidas/actual/grabar/terminar", {})
    assert s == 409 and d["error"]["codigo"] == "sin_grabacion"
    cab, regs = leer(str(tmp_path / "datos" / "grabaciones" / f"{gid}.jsonl.gz"))
    assert cab["empieza_tras"] == {"vida": 1, "latido": ultimo}
    assert [r["latido"] for r in regs] == [ultimo + 1, ultimo + 2, ultimo + 3]
    assert "escena" in regs[0]            # la primera lleva la escena vigente, aunque no haya cambiado
    _pedir(servidor, "POST", "vidas/actual/parar", {})


def test_grabar_sin_vida_y_rutas_con_identificador_invalido(servidor):
    s, d, _ = _pedir(servidor, "POST", "vidas/actual/grabar", {})
    assert s == 404 and d["error"]["codigo"] == "sin_vida"
    assert _pedir(servidor, "POST", "vidas", {"mundo": "minimo", "grabar": "si"})[1]["error"]["codigo"] == "campo_invalido"
    for ruta in ("grabaciones/..%2Fx/indice", "grabaciones/NO-VALIDO/latidos/0", "grabaciones/x"):
        s, d, _ = _pedir(servidor, "GET", ruta)
        assert s == 400 and d["error"]["codigo"] == "id_invalido", ruta
    s, d, _ = _pedir(servidor, "GET", "grabaciones/minimo-20260101-000000/indice")
    assert s == 404 and d["error"]["codigo"] == "grabacion_desconocida"


def test_el_reproductor_lee_la_grabacion_por_la_api(servidor, tmp_path):
    _vida_entera(servidor, grabar=True)
    gid = _pedir(servidor, "GET", "grabaciones")[1]["grabaciones"][0]["id"]
    s, d, _ = _pedir(servidor, "GET", f"grabaciones/{gid}/indice")
    assert s == 200 and not d["truncada"] and d["cabecera"]["mundo"] == "minimo"
    cab, regs = leer(str(tmp_path / "datos" / "grabaciones" / f"{gid}.jsonl.gz"))
    assert [e["latido"] for e in d["indice"]] == [r["latido"] for r in regs]
    assert d["indice"] == [entrada_indice(r, i) for i, r in enumerate(regs)]
    assert d["registros"] == len(regs) and set(d["tiempos_medios"]) == {k for r in regs for k in r.get("tiempos_ms", {})}
    esperadas = list(escenas(regs))
    for n in (0, len(regs) // 2, len(regs) - 1):
        s, dr, _ = _pedir(servidor, "GET", f"grabaciones/{gid}/latidos/{n}")
        r = dr["registro"]
        assert s == 200 and r["latido"] == regs[n]["latido"] and r["escena"] == esperadas[n]
        assert {k: v for k, v in r.items() if k != "escena"} == {k: v for k, v in regs[n].items() if k != "escena"}
    s, d, _ = _pedir(servidor, "GET", f"grabaciones/{gid}/latidos/{len(regs)}")
    assert s == 404 and d["error"]["codigo"] == "latido_fuera"


def test_el_directo_guarda_los_ultimos_latidos_sin_grabar(servidor):
    v = _vida_entera(servidor)
    s, d, _ = _pedir(servidor, "GET", "vidas/actual/latidos")
    assert s == 200 and d["lanzamiento"] == v["id"] and d["mundo"] == "minimo" and d["primero"] == 0
    assert d["siguiente"] == len(d["indice"]) and d["indice"][0]["latido"] == 1
    assert _pedir(servidor, "GET", "grabaciones")[1]["grabaciones"] == []      # sin grabar, nada en disco
    s, dr, _ = _pedir(servidor, "GET", "vidas/actual/latidos/0")
    assert s == 200 and dr["registro"]["latido"] == 1 and "escena" in dr["registro"] and dr["registro"]["nivel"] == "completo"
    s, dr, _ = _pedir(servidor, "GET", f"vidas/actual/latidos/{d['siguiente'] - 1}")
    assert "escena" in dr["registro"]          # la escena vigente, aunque ese latido no la trajera
    s, d2, _ = _pedir(servidor, "GET", f"vidas/actual/latidos?desde={d['siguiente'] - 2}")
    assert [e["n"] for e in d2["indice"]] == [d["siguiente"] - 2, d["siguiente"] - 1]
    assert _pedir(servidor, "GET", f"vidas/actual/latidos/{d['siguiente']}")[1]["error"]["codigo"] == "latido_fuera"
    assert _pedir(servidor, "GET", "vidas/actual/latidos/x")[1]["error"]["codigo"] == "campo_invalido"


def test_directo_limitado_pierde_los_mas_antiguos_y_sus_medias():
    d = Directo(maximo=3)
    d.reiniciar(7, "minimo")
    for i in range(1, 6):
        d.anadir({"v": 1, "vida": 1, "generacion": 1, "latido": i, "nivel": "completo", "hechos": [],
                  "ritmo": {"guillotina": "plazo" if i == 2 else ""}, "tiempos_ms": {"S1.Objeto": float(i)},
                  "fases": [["S1", 0.0, float(i)]], **({"escena": {"tipo": "rejilla", "i": 1}} if i == 1 else {})})
    ind = d.indice()
    assert ind["primero"] == 2 and ind["siguiente"] == 5 and [e["latido"] for e in ind["indice"]] == [3, 4, 5]
    assert ind["tiempos_medios"]["S1.Objeto"] == {"media": 4.0, "latidos": 3} and ind["guillotinas"] == 0
    assert d.registro(4)["escena"] == {"tipo": "rejilla", "i": 1}     # la escena del latido 1 sigue vigente
    with pytest.raises(ErrorLab):
        d.registro(1)


def test_grabaciones_cortadas_y_ficheros_que_no_son_grabaciones(tmp_path):
    carpeta = tmp_path / "grabaciones"
    carpeta.mkdir()
    (carpeta / "minimo-20260101-000000.jsonl.gz").write_bytes(gzip.compress(b'{"no": "cabecera"}\n'))
    gs = Grabaciones(str(carpeta))
    assert gs.listar()[0]["valida"] is False
    with pytest.raises(ErrorLab) as e:
        gs.indice("minimo-20260101-000000")
    assert e.value.codigo == "grabacion_invalida"
    cab = {"tipo": "cabecera", "formato": "ida-grabacion", "mundo": "minimo"}
    linea = json.dumps({"v": 1, "vida": 1, "latido": 1, "generacion": 1, "hechos": []})
    entero = gzip.compress((json.dumps(cab) + "\n" + linea + "\n" + linea).encode())
    (carpeta / "minimo-20260101-000001.jsonl.gz").write_bytes(entero[:-8])      # sin el CRC ni el tamaño del final del gzip
    d = gs.indice("minimo-20260101-000001")
    assert d["truncada"] and len(d["indice"]) >= 1


def test_ninguna_ruta_sale_de_la_carpeta(tmp_path):
    gs = Grabaciones(str(tmp_path / "g"))
    for malo in ("../x", "a/b", "minimo-2026-01", "", None, "MINIMO-20260101-000000"):
        with pytest.raises(ErrorLab) as e:
            gs.ruta(malo)
        assert e.value.codigo == "id_invalido"


# --- grabar no cambia la conducta (O3) -----------------------------------------------------------------------------------
def test_grabar_no_cambia_la_conducta(tmp_path):
    acciones = []
    for grabar in (False, True):
        tel = Telemetria(puerto=0, anfitrion="127.0.0.1", modo_antesala=True, datos=str(tmp_path / f"datos_{grabar}"))
        vistos: List[Any] = []
        original = tel.publicar
        tel.publicar = lambda r, o=original, v=vistos: (v.append((r.get("latido"), json.dumps(r.get("accion"), sort_keys=True))), o(r))[1]
        try:
            _vida_entera(tel, grabar=grabar)
        finally:
            tel.detener()
        acciones.append(vistos)
    assert acciones[0] and acciones[0] == acciones[1]


# --- mapa de Componentes (O13) -------------------------------------------------------------------------------------------
def test_los_74_elementos_tienen_descripcion_y_analogo_validos():
    espec = mc.cargar()
    assert len(espec) == 74
    for c in espec:
        assert set(c["descripcion"]) == {"es", "en"} and c["descripcion"]["es"].strip() and c["descripcion"]["en"].strip(), c["nombre"]
        assert set(c["analogo"]) == {"es", "en"} and bool(c["analogo"]["es"].strip()) == bool(c["analogo"]["en"].strip()), c["nombre"]
    assert mc.validar(espec, mc.decisiones_existentes()) == []


def test_el_validador_rechaza_textos_mal_formados():
    base = {"nombre": "X", "tipo": "componente", "clase": "general", "destino": "S1.Sentir", "hoy": "S1.Sentir", "decision": "previo"}
    malos = [
        {"descripcion": {"es": "algo"}},
        {"descripcion": {"es": "algo", "en": ""}},
        {"descripcion": "algo"},
        {"analogo": {"es": "ínsula", "en": ""}, "descripcion": {"es": "a", "en": "b"}},
        {"analogo": {"es": "x", "en": "y", "fr": "z"}, "descripcion": {"es": "a", "en": "b"}},
    ]
    for extra in malos:
        assert mc.validar_textos(dict(base, **extra)), extra
    assert mc.validar_textos(dict(base, analogo={"es": "", "en": ""}, descripcion={"es": "a", "en": "b"})) == []


def test_el_catalogo_de_la_api_sale_de_componentes_toml(servidor):
    s, d, _ = _pedir(servidor, "GET", "componentes")
    assert s == 200 and len(d["componentes"]) == 74
    espec = mc.cargar()
    for c, e in zip(d["componentes"], espec, strict=True):
        assert (c["nombre"], c["destino"], c["decision"]) == (e["nombre"], e["destino"], e["decision"])
        assert c["analogo"] == e["analogo"] and c["descripcion"] == e["descripcion"]
        assert c["mundos"] == [m for m in mc.MUNDOS if mc.montado_en(e, m, espec)]      # la misma regla que 06 y 07
        assert c["nucleo"] == mc.montado_en(e, "", espec)
    citadas = {c["decision"] for c in d["componentes"] if c["decision"] != "previo"}
    assert citadas <= set(d["decisiones"]) and all(v["titulo"] and v["texto"] for v in d["decisiones"].values())
    assert componentes.MUNDOS_MAPA == mc.MUNDOS


def test_las_claves_de_tiempo_del_registro_tienen_ficha(servidor):
    """Cada Componente que mide su tiempo en una vida real tiene su elemento en el mapa (el Actuador, por verbo)."""
    _vida_entera(servidor)
    cat = componentes.catalogo()
    claves = {c["clave_tiempo"] for c in cat["componentes"] if c["clave_tiempo"] and "minimo" in c["mundos"]}
    r = _pedir(servidor, "GET", "vidas/actual/latidos/5")[1]["registro"]
    vistas = {re.sub(r"^CORE\.Actuador_.*$", "CORE.Actuador", k) for k in r["tiempos_ms"]}
    assert vistas and vistas <= claves, sorted(vistas - claves)


# --- errores e idiomas ----------------------------------------------------------------------------------------------------
def test_los_codigos_del_laboratorio_estan_declarados():
    with open(os.path.join(os.path.dirname(api_v1.__file__), "laboratorio.py"), encoding="utf-8") as f:
        lanzados = set(re.findall(r"ErrorLab\(\d+, \"([a-z_]+)\"", f.read()))
    assert lanzados and lanzados <= set(api_v1.CODIGOS), sorted(lanzados - set(api_v1.CODIGOS))


def test_claves_del_laboratorio_que_se_forman_en_ejecucion():
    with open(os.path.join(WEB, "i18n", "es.json"), encoding="utf-8") as f:
        es = json.load(f)
    with open(os.path.join(WEB, "i18n", "en.json"), encoding="utf-8") as f:
        en = json.load(f)
    pasos = ("onda", "sentir", "preatencion", "plasticidad", "regulacion", "S1", "S2", "S3", "tribunal", "actuar", "cierre")
    familias = ([f"lab.paso.{p}{s}" for p in pasos for s in ("", ".que", ".bio")]
                + [f"lab.modulo.{m}" for m in ("Sentir", "Interpretar", "Reaccionar", "Actuar", "Regulacion")]
                + [f"lab.sistema.{s}" for s in ("CORE", "S1", "S2", "S3", "cuerpo")]
                + [f"lab.clase.{c}" for c in mc.CLASES] + [f"lab.tipo.{t}" for t in mc.TIPOS]
                + [f"lab.vista.{v}" for v in ("latido", "ingenieria", "grabaciones")]
                + [f"lab.nivel_valor.{n}" for n in ("vital", "cognitivo", "completo")]
                + [f"lab.hecho.{h}" for h in ("nace", "primera_vez", "aprende", "logro", "peligro", "sorpresa", "duda",
                                               "refuta", "muere", "duerme", "despierta")])
    assert not [k for k in familias if k not in es or k not in en]
    with open(os.path.join(WEB, "lab", "catalogo.js"), encoding="utf-8") as f:
        assert "'onda', 'sentir', 'preatencion', 'plasticidad', 'regulacion', 'S1', 'S2', 'S3', 'tribunal', 'actuar', 'cierre'" in f.read()


def test_laboratorio_cerrado_cierra_la_grabacion(tmp_path):
    lab = Laboratorio(str(tmp_path))
    lab.nueva_vida(1, "minimo")
    lab.empezar("minimo", {"tipo": "cabecera", "formato": "ida-grabacion", "mundo": "minimo", "nivel": "vital"})
    lab.poner({"v": 1, "vida": 1, "latido": 1, "generacion": 1, "hechos": [], "escena": {"tipo": "rejilla"}})
    lab.poner({"v": 1, "vida": 1, "latido": 2, "generacion": 1, "hechos": []})
    lab.cerrar()
    lista = lab.grabaciones.listar()
    assert len(lista) == 1 and lista[0]["registros"] == 2 and not lista[0]["en_curso"]
    cab, regs = leer(os.path.join(str(tmp_path), "grabaciones", lista[0]["id"] + ".jsonl.gz"))
    assert [r["latido"] for r in regs] == [1, 2] and regs[0]["escena"] == {"tipo": "rejilla"}
