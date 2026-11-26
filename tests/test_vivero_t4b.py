"""T4b (O9, O10; sección 13 del diseño): compañero, colección y fichas; registro de cierre; resumen del saber; etiquetas
del cuerpo por mundo. Todo con datos en directorios temporales: nada toca ``datos/`` del proyecto."""

import json
import os
import time
import http.client
from typing import Any, Dict, List

import pytest

from ida.ejecutor import ejecutar
from ida.mundos import MUNDOS
from ida.telemetria.esquema import validar
from ida.telemetria.grabacion import leer
from ida.telemetria.servidor import WEB, Telemetria
from ida.telemetria.vivero import ErrorVivero, Vivero, convertir


# --- ayudas -------------------------------------------------------------------------------------------------------------
@pytest.fixture
def servidor(tmp_path):
    tel = Telemetria(puerto=0, anfitrion="127.0.0.1", modo_antesala=True, datos=str(tmp_path / "datos"))
    try:
        yield tel
    finally:
        tel.detener()


def _pedir(tel, metodo, ruta, cuerpo=None, origen=True):
    con = http.client.HTTPConnection("127.0.0.1", tel.puerto, timeout=30)
    h = {"Content-Type": "application/json"}
    if origen:
        h["Origin"] = f"http://127.0.0.1:{tel.puerto}"
    con.request(metodo, "/api/v1/" + ruta, body=json.dumps(cuerpo).encode() if cuerpo is not None else None, headers=h)
    r = con.getresponse()
    datos = r.read()
    tipo = r.getheader("Content-Type", "")
    disp = r.getheader("Content-Disposition", "")
    con.close()
    return r.status, (json.loads(datos) if datos and tipo.startswith("application/json") else datos), disp


def _vida(tel, semilla: int, **extra) -> Dict[str, Any]:
    """Lanza una vida corta de mínimo a ritmo máximo y espera a que termine."""
    s, d, _ = _pedir(tel, "POST", "vidas", {"mundo": "minimo", "latidos": 40, "semilla": semilla, **extra})
    assert s == 201, d
    _pedir(tel, "POST", "vidas/actual/ritmo", {"ritmo": "max"})
    fin = time.monotonic() + 120
    while time.monotonic() < fin:
        v = tel.vida_actual()
        if v and not v["activa"]:
            assert not v.get("error"), v
            return v
        time.sleep(0.05)
    raise AssertionError("la vida no terminó")


def _ficheros(raiz: str) -> List[str]:
    return sorted(os.path.relpath(os.path.join(d, f), raiz) for d, _, fs in os.walk(raiz) for f in fs)


FICHA_PANEL = {   # lo que guardaba «Restaurar en antesala» del panel (panel.html) y descarga /linaje/descargar
    "tipo": "ida_individuo_v1", "mundo": "minimo", "individuo": "Minimo_G7", "generacion": 7,
    "arquetipo": {"nombre": "IdA", "linaje": "Minimo", "generacion": 7, "padre": "Minimo_G6", "apertura": 0.61,
                  "responsabilidad": 0.55, "neuroticismo": 0.4, "extraversion": 0.35, "umbral_miedo": 0.62},
    "fitness": 912.0, "puntuacion": {"bayas": 25, "setas": 0}, "latidos": 412, "vivo": True,
    "legado": {"proposiciones": [], "registros": []},
}


# --- ciclo completo ---------------------------------------------------------------------------------------------------------
def test_ciclo_completo_sin_perder_nada(servidor, tmp_path):
    raiz = str(tmp_path / "datos")
    mundo_dir = os.path.join(raiz, "minimo")
    # 1. Una vida: el compañero es Minimo_G1
    _vida(servidor, 1)
    s, d, _ = _pedir(servidor, "GET", "companeros/minimo")
    assert s == 200 and d["companero"]["existe"] and d["companero"]["individuo"] == "Minimo_G1"
    assert [v["generacion"] for v in d["companero"]["linaje"]] == [1]
    # 2. Guardar ficha
    s, d, _ = _pedir(servidor, "POST", "companeros/minimo/guardar", {})
    assert s == 201, d
    ficha = d["ficha"]
    assert ficha["tipo"] == "ida_ficha" and ficha["version"] == 1 and ficha["individuo"] == "Minimo_G1"
    assert ficha["vidas"] and ficha["mejor_score"] is not None and ficha["fecha"] and "legado" in ficha
    assert os.path.isfile(os.path.join(raiz, "vivero", "fichas", f"{ficha['id']}.json"))
    # 3. Otra vida: la estirpe sigue (G2)
    _vida(servidor, 2)
    s, d, _ = _pedir(servidor, "GET", "companeros/minimo")
    assert d["companero"]["individuo"] == "Minimo_G2" and d["companero"]["generaciones"] == 2
    linaje_g2 = open(os.path.join(mundo_dir, "linaje.json"), encoding="utf-8").read()
    # 4. Adoptar la ficha: la estirpe G2 queda archivada, entera
    s, d, _ = _pedir(servidor, "POST", f"coleccion/{ficha['id']}/adoptar")
    assert s == 200, d
    assert d["companero"]["individuo"] == "Minimo_G1" and d["companero"]["adoptada_de"] == ficha["id"]
    archivada = d["archivada"]
    assert archivada and archivada["generaciones"] == 2 and archivada["motivo"] == "adoptar" and not archivada["incompleta"]
    dir_arch = os.path.join(raiz, "vivero", "estirpes", archivada["id"])
    assert open(os.path.join(dir_arch, "linaje.json"), encoding="utf-8").read() == linaje_g2
    assert os.path.isfile(os.path.join(dir_arch, "memoria.db"))
    s, d, _ = _pedir(servidor, "GET", "coleccion?mundo=minimo")
    assert [e["id"] for e in d["estirpes"]] == [archivada["id"]] and [f["id"] for f in d["fichas"]] == [ficha["id"]]
    # La ficha adoptada sigue en la colección; una vida nueva continúa desde ella (G2 hija de la ficha)
    _vida(servidor, 3)
    assert _pedir(servidor, "GET", "companeros/minimo")[1]["companero"]["individuo"] == "Minimo_G2"
    # 5. La estirpe G2 archivada se puede volver a adoptar: vuelve entera y la de la ficha se archiva
    s, d, _ = _pedir(servidor, "POST", f"coleccion/{archivada['id']}/adoptar")
    assert s == 200, d
    assert open(os.path.join(mundo_dir, "linaje.json"), encoding="utf-8").read() == linaje_g2
    assert not os.path.exists(dir_arch)   # ha vuelto a su mundo: no está dos veces
    segunda = d["archivada"]
    assert segunda and segunda["id"] != archivada["id"]
    # 6. Empezar de cero desde la aplicación: archiva (no borra) y nace una G1 nueva
    antes = len(_pedir(servidor, "GET", "coleccion?mundo=minimo")[1]["estirpes"])
    v = _vida(servidor, 4, tabula_rasa=True)
    assert v["archivada"]
    d = _pedir(servidor, "GET", "coleccion?mundo=minimo")[1]
    assert len(d["estirpes"]) == antes + 1
    arch_cero = next(e for e in d["estirpes"] if e["id"] == v["archivada"])
    assert arch_cero["motivo"] == "empezar_de_cero" and arch_cero["vidas"] == 2
    assert open(os.path.join(raiz, "vivero", "estirpes", v["archivada"], "linaje.json"), encoding="utf-8").read() == linaje_g2
    assert _pedir(servidor, "GET", "companeros/minimo")[1]["companero"]["individuo"] == "Minimo_G1"
    # 7. Importar una ficha antigua del panel: se convierte y avisa de lo que falta
    s, d, _ = _pedir(servidor, "POST", "coleccion/importar", {"ficha": FICHA_PANEL})
    assert s == 201, d
    imp = d["ficha"]
    assert imp["origen"] == "panel" and imp["individuo"] == "Minimo_G7" and imp["generacion"] == 7
    assert imp["vidas"][0]["score"] == 912.0 and imp["mejor_score"] == 912.0
    assert any(a.startswith("legado") for a in d["avisos"]) and any(a.startswith("commit") for a in d["avisos"])
    # Exportar: la ficha tal cual, para descargar
    s, cuerpo, disp = _pedir(servidor, "GET", f"coleccion/{imp['id']}/exportar")
    assert s == 200 and "attachment" in disp and cuerpo["id"] == imp["id"]
    # Renombrar
    s, d, _ = _pedir(servidor, "POST", f"coleccion/{imp['id']}/renombrar", {"nombre": "La de la abuela"})
    assert s == 200 and d["elemento"]["nombre"] == "La de la abuela"
    assert _pedir(servidor, "POST", f"coleccion/{imp['id']}/renombrar", {"nombre": "x" * 61})[0] == 400
    # 8. Borrar sin confirmar no borra; con un testigo malo tampoco; confirmando, sí; el testigo no vale dos veces
    ruta_imp = os.path.join(raiz, "vivero", "fichas", f"{imp['id']}.json")
    s, d, _ = _pedir(servidor, "POST", f"coleccion/{imp['id']}/borrar")
    assert s == 200 and d["testigo"] and d["elemento"]["id"] == imp["id"]
    assert os.path.isfile(ruta_imp)
    testigo = d["testigo"]
    s, d, _ = _pedir(servidor, "POST", f"coleccion/{imp['id']}/borrar/confirmar", {"testigo": "otro"})
    assert s == 400 and d["error"]["codigo"] == "testigo_invalido" and os.path.isfile(ruta_imp)
    s, d, _ = _pedir(servidor, "POST", f"coleccion/{ficha['id']}/borrar/confirmar", {"testigo": testigo})   # de otro elemento
    assert s == 400 and os.path.isfile(os.path.join(raiz, "vivero", "fichas", f"{ficha['id']}.json"))
    s, d, _ = _pedir(servidor, "POST", f"coleccion/{imp['id']}/borrar/confirmar", {"testigo": testigo})
    assert s == 200 and d["borrado"] == imp["id"] and not os.path.exists(ruta_imp)
    s, d, _ = _pedir(servidor, "POST", f"coleccion/{imp['id']}/borrar/confirmar", {"testigo": testigo})
    assert s == 400
    # Sin Origin propio, nada (403); un id con una ruta, 400
    assert _pedir(servidor, "POST", f"coleccion/{ficha['id']}/borrar", origen=False)[0] == 403
    assert _pedir(servidor, "GET", "coleccion/..%2F..%2Fminimo")[1]["error"]["codigo"] == "id_invalido"
    assert _pedir(servidor, "POST", "coleccion/minimo-20260101-000000-zzzzzz/adoptar")[0] == 400
    # Al final: la ficha guardada y las tres estirpes archivadas siguen ahí, con su linaje y su memoria
    final = _pedir(servidor, "GET", "coleccion?mundo=minimo")[1]
    assert [f["id"] for f in final["fichas"]] == [ficha["id"]] and len(final["estirpes"]) == 2
    for e in final["estirpes"]:
        assert {"linaje.json", "memoria.db", "estirpe.json"} <= set(os.listdir(os.path.join(raiz, "vivero", "estirpes", e["id"])))
    indice = json.load(open(os.path.join(raiz, "vivero", "indice.json"), encoding="utf-8"))
    assert {e["id"] for e in indice["elementos"]} == {ficha["id"]} | {e["id"] for e in final["estirpes"]}


def test_adoptar_y_archivar_con_la_vida_en_marcha_dan_409(servidor):
    _vida(servidor, 1)
    ficha = _pedir(servidor, "POST", "companeros/minimo/guardar", {})[1]["ficha"]
    s, d, _ = _pedir(servidor, "POST", "vidas", {"mundo": "minimo", "latidos": 100000, "semilla": 2})
    assert s == 201
    _pedir(servidor, "POST", "vidas/actual/ritmo", {"ritmo": "pausa"})
    assert _pedir(servidor, "POST", f"coleccion/{ficha['id']}/adoptar")[1]["error"]["codigo"] == "vida_en_curso"
    assert _pedir(servidor, "POST", "companeros/minimo/archivar")[1]["error"]["codigo"] == "vida_en_curso"
    _pedir(servidor, "POST", "vidas/actual/parar")
    s, d, _ = _pedir(servidor, "POST", "companeros/minimo/archivar")
    assert s == 200 and d["archivada"]
    assert _pedir(servidor, "POST", "companeros/minimo/archivar")[1] == {"archivada": None}   # ya no hay compañero
    assert _pedir(servidor, "POST", "companeros/minimo/guardar", {})[1]["error"]["codigo"] == "sin_companero"


def test_archivar_no_toca_lo_que_no_es_de_la_estirpe(tmp_path):
    """El bioma de archivos (y cualquier otra cosa en <datos>/<mundo>) se queda donde está."""
    raiz = tmp_path / "datos"
    d = raiz / "archivos"
    (d / "bioma" / "pradera").mkdir(parents=True)
    (d / "bioma" / "pradera" / "a.brote").write_text("x")
    (d / "linaje.json").write_text(json.dumps({"generaciones": [], "arquetipo": None, "legado": {}}))
    (d / "memoria.db").write_bytes(b"1234")
    meta = Vivero(str(raiz)).archivar("archivos")
    assert meta and meta["ficheros"] == ["linaje.json", "memoria.db"]
    assert (d / "bioma" / "pradera" / "a.brote").read_text() == "x"
    assert not (d / "linaje.json").exists() and not (d / "memoria.db").exists()
    assert (raiz / "vivero" / "estirpes" / meta["id"] / "memoria.db").read_bytes() == b"1234"


def test_la_cli_conserva_tabula_rasa(tmp_path):
    """La CLI (``--tabula-rasa``) sigue borrando su directorio de datos, como siempre; la aplicación archiva."""
    datos = tmp_path / "minimo"
    datos.mkdir()
    (datos / "otro.txt").write_text("x")
    ejecutar("minimo", latidos=3, semilla=1, consola=False, datos=str(datos), tabula_rasa=True, plazo_logico=40)
    assert not (datos / "otro.txt").exists()


# --- fichas antiguas y ranking -------------------------------------------------------------------------------------------
def test_convertir_fichas_antiguas():
    f = convertir(FICHA_PANEL)
    assert f["version"] == 1 and f["arquetipo"]["padre"] == "Minimo_G6" and f["vidas"][0]["latidos"] == 412
    assert f["commit"] is None and f["avisos"]
    linaje = {"tipo": "ida_linaje_completo_v1", "mundo": "crafter",
              "arquetipo_actual": {"apertura": 0.5, "responsabilidad": 0.5, "neuroticismo": 0.5, "extraversion": 0.5,
                                   "umbral_miedo": 0.6, "generacion": 3},
              "legado": {"proposiciones": [{"sujeto": "vaca", "relacion": "NUTRITIVO", "confianza": 0.9}]},
              "generaciones": [{"individuo": "Crafter_G3", "arquetipo": {"generacion": 3}, "puntuacion": {"n_logros": 2, "pasos": 300},
                                "latidos": 300, "vivo": False, "causa_muerte": "zombi"},
                               {"individuo": "Crafter_G1", "arquetipo": {"generacion": 1}, "puntuacion": {"n_logros": 1}, "latidos": 90}]}
    f = convertir(linaje)
    assert [v["individuo"] for v in f["vidas"]] == ["Crafter_G1", "Crafter_G3"]   # en orden de generación
    assert f["individuo"] == "Crafter_G3" and f["mejor_score"] == 2300.0 and f["vidas"][1]["causa_muerte"] == "zombi"
    assert not any(a.startswith("legado") for a in f["avisos"])
    # Lo que aceptaba la antesala de T3: solo carácter
    assert convertir({"mundo": "minimo", "arquetipo": {"apertura": 0.2}})["arquetipo"]["apertura"] == 0.2
    for malo in ({"mundo": "minimo"}, {"arquetipo": {"apertura": 0.2}}, {"mundo": "minimo", "arquetipo": {"apertura": 7}},
                 {"mundo": "luna", "arquetipo": {}}, [1, 2], {"tipo": "ida_ficha", "version": 9, "mundo": "minimo"}):
        with pytest.raises(ErrorVivero):
            convertir(malo)
    # Una ficha v1 exportada se vuelve a importar igual (con id nuevo)
    v1 = convertir(FICHA_PANEL)
    v1["id"] = "minimo-20260101-000000-abcdef"
    otra = convertir(json.loads(json.dumps(v1)))
    assert {k: otra[k] for k in ("individuo", "arquetipo", "vidas", "mejor_score", "legado")} == \
        {k: v1[k] for k in ("individuo", "arquetipo", "vidas", "mejor_score", "legado")}


def test_ranking_por_mundo(tmp_path):
    raiz = tmp_path / "datos"
    viv = Vivero(str(raiz))
    for score, ind in ((100.0, "Minimo_G1"), (900.0, "Minimo_G2"), (500.0, "Minimo_G3")):
        viv.importar(dict(FICHA_PANEL, individuo=ind, fitness=score))
    viv.importar(dict(FICHA_PANEL, mundo="archivos", individuo="Archivos_G1", fitness=50.0))
    (raiz / "minimo").mkdir()
    (raiz / "minimo" / "linaje.json").write_text(json.dumps({
        "generaciones": [{"individuo": "Minimo_G1", "arquetipo": {"generacion": 1}, "fitness": 700.0, "latidos": 10},
                         {"individuo": "Minimo_G2", "arquetipo": {"generacion": 2}, "fitness": 650.0, "latidos": 10}],
        "arquetipo": {"generacion": 2, "apertura": 0.5}, "legado": {}}))
    viv.archivar("minimo")
    (raiz / "minimo" / "linaje.json").write_text(json.dumps({
        "generaciones": [{"individuo": "Minimo_G1", "arquetipo": {"generacion": 1}, "fitness": 300.0, "latidos": 10}],
        "arquetipo": {"generacion": 1}, "legado": {}}))
    col = viv.coleccion()
    minimo = col["ranking"]["minimo"]
    assert [(x["tipo"], x["mejor_score"]) for x in minimo] == [("ficha", 900.0), ("estirpe", 700.0), ("ficha", 500.0),
                                                               ("companero", 300.0), ("ficha", 100.0)]
    assert [x["puesto"] for x in minimo] == [1, 2, 3, 4, 5]
    assert [x["mejor_score"] for x in col["ranking"]["archivos"]] == [50.0]
    assert [x["tipo"] for x in viv.coleccion("archivos")["ranking"]["archivos"]] == ["ficha"]


# --- registro de cierre ---------------------------------------------------------------------------------------------------------
def test_registro_de_cierre_con_lo_aprendido_al_morir(tmp_path):
    """Archivos, semilla 6 (plazo lógico 40): muere por el depredador y, al morir, aprende que es peligroso."""
    vistos: List[Dict[str, Any]] = []
    ruta = str(tmp_path / "g.jsonl.gz")
    ejecutar("archivos", latidos=600, semilla=6, consola=False, datos=str(tmp_path / "archivos"), plazo_logico=40,
             nivel="cognitivo", grabar=ruta, al_latir=lambda o, onda, r: vistos.append(r))
    _, regs = leer(ruta)
    cierre, ultimo = regs[-1], regs[-2]
    assert len(regs) == len(vistos) + 1 and not any(r.get("cierre") for r in vistos)   # al_latir no recibe el cierre
    assert cierre["cierre"] is True and "cierre" not in ultimo and cierre["latido"] == ultimo["latido"]
    assert validar(cierre) == []
    assert any(h["tipo"] == "muere" for h in ultimo["hechos"]) and not any(h["tipo"] == "muere" for h in cierre["hechos"])
    aprende = [h for h in cierre["hechos"] if h["tipo"] == "aprende"]
    assert aprende and aprende[0]["clase"] == "depredador" and aprende[0]["relacion"] == "PELIGROSO"
    assert any(h["tipo"] == "peligro" for h in cierre["hechos"])
    assert cierre["resumen_saber"]["proposiciones"] >= ultimo["resumen_saber"]["proposiciones"]
    assert any(p["sujeto"] == "depredador" and p["relacion"] == "PELIGROSO" for p in cierre["saber"])
    assert "escena" not in cierre


def test_sin_muerte_no_hay_cierre(tmp_path):
    ruta = str(tmp_path / "g.jsonl.gz")
    ejecutar("minimo", latidos=30, semilla=1, consola=False, datos=str(tmp_path / "m"), plazo_logico=40, nivel="vital", grabar=ruta)
    _, regs = leer(ruta)
    assert len(regs) == 30 and not any(r.get("cierre") for r in regs)


def test_el_servidor_marca_los_hechos_del_cierre_y_cuenta_el_reparto(servidor, monkeypatch):
    import ida.telemetria.servidor as srv
    monkeypatch.setattr(srv, "a_panel", lambda r: {})   # la forma del panel clásico no interesa aquí
    base = {"v": 1, "vida": 1, "latido": 5, "generacion": 1, "score": {"logros": []}}
    servidor.publicar(dict(base, accion={"sistema": "S1"}, hechos=[]))
    servidor.publicar(dict(base, latido=6, accion={"sistema": "S2"}, hechos=[]))
    servidor.publicar(dict(base, latido=6, cierre=True, accion={"sistema": "S2"},
                           hechos=[{"tipo": "aprende", "saber": "proposicion", "clase": "lobo"}]))
    d = servidor.diario()
    assert d["reparto"] == {"vida": 1, "cuenta": {"S1": 1, "S2": 1}}   # el cierre no cuenta otra acción
    assert d["hechos"][-1]["cierre"] is True and d["hechos"][-1]["latido"] == 6
    assert d["hasta"] == {"vida": 1, "latido": 6, "cierre": True}   # el Vivero no vuelve a sumar ese registro


# --- resumen del saber -----------------------------------------------------------------------------------------------------------
def test_resumen_del_saber_con_los_totales_de_toda_la_memoria(tmp_path):
    regs: List[Dict[str, Any]] = []
    ejecutar("crafter", latidos=25, semilla=31, consola=False, datos=str(tmp_path / "c"), plazo_logico=40, nivel="completo",
             al_latir=lambda o, onda, r: regs.append(r), opciones_mundo={"vista": "oficial"})
    r = regs[-1]
    rs = r["resumen_saber"]
    assert validar(r) == []
    assert rs["proposiciones"] == len(r["saber"]) == rs["demostradas"] + rs["hipotesis"] + rs["refutadas"]   # completo: saber entero
    assert rs["requisitos"] == len(r["requisitos"]) > 0                                                # los del manual también
    assert rs["requisitos_confirmados"] == sum(1 for q in r["requisitos"] if q["confirmado"])
    assert sum(rs["fuentes"].values()) == rs["proposiciones"] + rs["requisitos"]
    assert rs["fuentes"]["manual"] >= sum(1 for q in r["requisitos"] if q["fuente"] == "manual") > 0
    assert rs["heredadas"] == sum(1 for p in r["saber"] if p["heredada"])
    assert (rs["aciertos"], rs["sorpresas"]) == (r["memoria"]["aciertos"], r["memoria"]["sorpresas"])


def test_el_nivel_cognitivo_de_la_sse_lleva_resumen_y_requisitos():
    from ida.telemetria.api_v1 import CAMPOS_COGNITIVO, CAMPOS_VITAL
    assert {"resumen_saber", "escena", "cierre"} <= CAMPOS_VITAL and "requisitos" in CAMPOS_COGNITIVO - CAMPOS_VITAL


# --- etiquetas del cuerpo por mundo ----------------------------------------------------------------------------------------------
BARRAS = {"vitalidad", "alimentacion", "energia", "descanso"}


def _clases(mundo: str) -> Dict[str, Any]:
    with open(os.path.join(WEB, "i18n", "clases", f"{mundo}.json"), encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("mundo", MUNDOS)
def test_cada_mundo_declara_las_barras_de_su_cuerpo(mundo):
    cuerpo = _clases(mundo)["cuerpo"]
    assert cuerpo and set(cuerpo) <= BARRAS and "vitalidad" in cuerpo
    for barra, d in cuerpo.items():
        for campo in ("etiqueta", "ayuda"):
            assert set(d[campo]) == {"es", "en"} and all(v.strip() for v in d[campo].values()), (mundo, barra, campo)


def test_las_barras_tienen_sentido_en_cada_mundo():
    assert set(_clases("ajedrez")["cuerpo"]) == {"vitalidad", "alimentacion"}       # energía y descanso fijos en 100
    assert "Alimentación" not in json.dumps(_clases("ajedrez")["cuerpo"], ensure_ascii=False)
    assert "descanso" not in _clases("crafter")["cuerpo"]                           # el adaptador le da la energía
    assert "descanso" not in _clases("snake")["cuerpo"]                             # no duerme
    assert set(_clases("minimo")["cuerpo"]) == set(_clases("archivos")["cuerpo"]) == BARRAS


def test_ajedrez_marca_fijas_la_energia_y_el_descanso():
    """Lo que dice la tabla 13.6: en ajedrez la energía y el descanso son siempre 100 (por eso no se enseñan)."""
    pytest.importorskip("chess")
    from ida.mundos.ajedrez import MundoAjedrez
    m = MundoAjedrez()
    m.reiniciar(1)
    v = m.observar().vitales
    assert v["energia"] == 100.0 and v["descanso"] == 100.0
    m.cerrar()
