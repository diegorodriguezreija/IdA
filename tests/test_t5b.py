"""T5b (DISENO_OBSERVABILIDAD, sección 15): Epistemología, Biología, Análisis y comparación, Cierre, plurales.

- La historia de una proposición, reconstruida desde una grabación real de mínimo: nace como hipótesis, cambia de
  confianza y se demuestra (``ida/telemetria/analisis.py``).
- Dos grabaciones de la misma vida no divergen; dos vidas distintas divergen en el latido correcto
  (``grabacion.divergencia``, con ``grabacion.comparar`` como base), también por la API.
- Comparación de estirpes generación a generación (``Vivero.estirpe`` y ``analisis.comparar_estirpes``).
- Plurales: ninguna plantilla da «1 cosas» en ningún idioma.
- La tabla de análogos de Biología cita líneas de código que existen y dicen lo que la tabla les atribuye.
"""

import http.client
import json
import os
import re
import shutil

import pytest

from ida.ejecutor import ejecutar
from ida.telemetria.analisis import Series, clave_proposicion, comparar_estirpes, historia, redondear, series_de
from ida.telemetria.grabacion import Grabacion, comparar, divergencia, diferencias, leer
from ida.telemetria.laboratorio import Directo, Grabaciones
from ida.telemetria.servidor import WEB, Telemetria
from ida.telemetria.vivero import Vivero

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
I18N = os.path.join(WEB, "i18n")


def _pedir(tel, metodo, ruta):
    con = http.client.HTTPConnection("127.0.0.1", tel.puerto, timeout=60)
    con.request(metodo, "/api/v1/" + ruta, headers={"Origin": f"http://127.0.0.1:{tel.puerto}"})
    r = con.getresponse()
    datos = json.loads(r.read() or b"null")
    con.close()
    return r.status, datos, None


def _leer_web(*partes):
    with open(os.path.join(WEB, *partes), encoding="utf-8") as f:
        return f.read()


def _dic(idioma):
    with open(os.path.join(I18N, f"{idioma}.json"), encoding="utf-8") as f:
        return json.load(f)


ES, EN = _dic("es"), _dic("en")


@pytest.fixture(scope="module")
def grabaciones_minimo(tmp_path_factory):
    """Grabaciones reales de mínimo con plazo lógico: semilla 1 dos veces (la misma vida) y semilla 2, nivel completo,
    y semilla 1 con nivel cognitivo. Con los nombres de la carpeta de grabaciones del Laboratorio."""
    base = tmp_path_factory.mktemp("t5b")
    carpeta = base / "grabaciones"
    rutas = {}
    for nombre, semilla, nivel in (("a", 1, "completo"), ("b", 1, "completo"), ("c", 2, "completo"), ("cog", 1, "cognitivo")):
        id_ = {"a": "minimo-20261126-000001", "b": "minimo-20261126-000002", "c": "minimo-20261126-000003",
               "cog": "minimo-20261126-000004"}[nombre]
        ruta = str(carpeta / f"{id_}.jsonl.gz")
        ejecutar("minimo", latidos=120, semilla=semilla, consola=False, datos=str(base / f"datos_{nombre}"), tabula_rasa=True,
                 grabar=ruta, nivel=nivel, plazo_logico=40)
        rutas[nombre] = (id_, ruta)
    return str(carpeta), rutas


# --- la historia de una proposición ---------------------------------------------------------------------------------------
@pytest.mark.parametrize("cual", ["a", "cog"])
def test_historia_de_una_proposicion_desde_una_grabacion_real(grabaciones_minimo, cual):
    _, rutas = grabaciones_minimo
    _, regs = leer(rutas[cual][1])
    s = series_de(regs)
    p = historia(s, clave_proposicion("baya", "NUTRITIVO"))
    assert p is not None and p["tipo"] == "proposicion" and p["fuente"] == "experiencia"
    h = p["historia"]                                       # [n, latido, estado, confianza, fuente, vida]
    assert h[0][2] == "hipotesis"                           # nace como hipótesis...
    nace = h[0][1]
    assert regs[h[0][0]]["latido"] == nace
    confianzas = [x[3] for x in h if x[2] == "hipotesis"]
    assert len(set(confianzas)) >= 2                        # ...su confianza cambia...
    demostrada = next(x for x in h if x[2] == "demostrada")  # ...y se demuestra
    assert demostrada[1] > nace and demostrada[3] > confianzas[0]
    # Los hechos de la grabación cuentan lo mismo: «aprende» como hipótesis al nacer y como demostrada después.
    eventos = [(e["latido"], e["tipo"], e["estado"]) for e in p["eventos"]]
    assert (nace, "aprende", "hipotesis") in eventos and (demostrada[1], "aprende", "demostrada") in eventos
    hechos = [(r["latido"], h_["estado"]) for r in regs for h_ in r["hechos"]
              if h_["tipo"] == "aprende" and h_.get("clase") == "baya" and h_.get("relacion") == "NUTRITIVO"]
    assert hechos == [(nace, "hipotesis"), (demostrada[1], "demostrada")]
    # Cada paso de la historia es lo que dice el campo «saber» de su registro.
    for n, _latido, estado, confianza, _, _ in h:
        saber = {(x["sujeto"], x["relacion"]): x for x in regs[n]["saber"]}
        x = saber[("baya", "NUTRITIVO")]
        assert (x["estado"], redondear(x["confianza"])) == (estado, confianza)


def test_las_series_son_las_de_cada_registro(grabaciones_minimo):
    _, rutas = grabaciones_minimo
    _, regs = leer(rutas["a"][1])
    s = series_de(regs)
    col = s["columnas"]
    assert s["registros"] == len(regs) == len(col["n"]) and all(len(v) == len(regs) for v in col.values())
    for i in (0, 37, len(regs) - 1):
        r = regs[i]
        assert col["latido"][i] == r["latido"] and col["cuerpo/vitalidad"][i] == r["cuerpo"]["vitalidad"]
        assert col["quimica/dopamina"][i] == r["quimica"]["dopamina"] and col["afecto/estado"][i] == r["afecto"]["estado"]
        assert col["saber/demostradas"][i] == r["resumen_saber"]["demostradas"] and col["logros"][i] == len(r["score"]["logros"])
    # Daño: solo donde la vitalidad baja respecto al latido anterior
    danos = {h["n"] for h in s["hechos"] if h["tipo"] == "dano"}
    esperado = {i for i in range(1, len(regs)) if regs[i]["cuerpo"]["vitalidad"] < regs[i - 1]["cuerpo"]["vitalidad"]}
    assert danos == esperado
    assert s["vidas"][0]["nace"]["tipo"] == "nace" and s["vidas"][0]["hasta"] == len(regs) - 1


def test_directo_y_grabacion_dan_las_mismas_series(grabaciones_minimo):
    carpeta, rutas = grabaciones_minimo
    _, regs = leer(rutas["a"][1])
    d = Directo(maximo=10_000)
    for r in regs:
        d.anadir(r)
    directas = d.series()
    del directas["lanzamiento"], directas["primero"], directas["siguiente"]
    g = Grabaciones(carpeta).series(rutas["a"][0])
    del g["grabacion"], g["cabecera"], g["truncada"]
    assert json.loads(json.dumps(series_de(regs))) == directas == json.loads(json.dumps(g))


def test_el_directo_poda_las_series_con_lo_que_olvida(grabaciones_minimo):
    _, rutas = grabaciones_minimo
    _, regs = leer(rutas["a"][1])
    d = Directo(maximo=30)
    for r in regs:
        d.anadir(r)
    s = d.series()
    assert s["primero"] == len(regs) - 30 and s["columnas"]["n"] == list(range(len(regs) - 30, len(regs)))
    assert all(h["n"] >= s["primero"] for h in s["hechos"])
    p = historia(s, clave_proposicion("baya", "NUTRITIVO"))
    assert p["historia"][0][0] == s["primero"]                     # entra en lo que queda con su estado de antes
    assert s["vidas"][0]["recortada"] is True


def test_sin_el_campo_saber_la_historia_sale_de_los_hechos():
    regs = [{"v": 1, "nivel": "vital", "vida": 1, "latido": 1, "mundo": "minimo", "hechos": []},
            {"v": 1, "nivel": "vital", "vida": 1, "latido": 2, "mundo": "minimo",
             "hechos": [{"tipo": "aprende", "saber": "proposicion", "clase": "baya", "relacion": "NUTRITIVO", "estado": "hipotesis",
                         "fuente": "experiencia", "confianza": 0.4}]},
            {"v": 1, "nivel": "vital", "vida": 1, "latido": 3, "mundo": "minimo",
             "hechos": [{"tipo": "refuta", "clase": "baya", "relacion": "NUTRITIVO", "confianza": 0.1}]}]
    p = historia(series_de(regs), clave_proposicion("baya", "NUTRITIVO"))
    assert [(x[1], x[2], x[3]) for x in p["historia"]] == [(2, "hipotesis", 0.4), (3, "refutada", 0.1)]


# --- comparar dos grabaciones ------------------------------------------------------------------------------------------------
def test_la_misma_vida_no_diverge(grabaciones_minimo):
    carpeta, rutas = grabaciones_minimo
    (_, a), (_, b) = rutas["a"], rutas["b"]
    assert comparar(a, b) is None                          # la base: iguales línea a línea salvo los tiempos
    _, ra = leer(a)
    _, rb = leer(b)
    d = divergencia(ra, rb)
    assert d == {"comunes": len(ra), "iguales": len(ra), "primera": None}
    c = Grabaciones(carpeta).comparar(rutas["a"][0], rutas["b"][0])
    assert c["configuracion"]["misma"] is True and c["divergencia"]["primera"] is None


def test_vidas_distintas_divergen_en_el_latido_correcto(grabaciones_minimo):
    carpeta, rutas = grabaciones_minimo
    _, ra = leer(rutas["a"][1])
    _, rc = leer(rutas["c"][1])
    esperado = next(i for i, (x, y) in enumerate(zip(ra, rc, strict=False)) if diferencias(x, y))   # a mano, registro a registro
    d = divergencia(ra, rc)
    assert d["primera"]["latido"] == ra[esperado]["latido"] and d["iguales"] == esperado
    c = Grabaciones(carpeta).comparar(rutas["a"][0], rutas["c"][0])
    assert c["configuracion"] == {"misma": False, "distintas": ["semilla"], "otras": []}
    assert c["divergencia"]["primera"]["latido"] == ra[esperado]["latido"]


def test_una_diferencia_a_media_vida_se_marca_en_su_latido(grabaciones_minimo, tmp_path):
    _, rutas = grabaciones_minimo
    cab, regs = leer(rutas["a"][1])
    regs[30] = dict(regs[30], accion=None)
    ruta = str(tmp_path / "otra.jsonl.gz")
    with Grabacion(ruta, cab) as g:
        for r in regs:
            g.escribir(r)
    _, ra = leer(rutas["a"][1])
    d = divergencia(ra, regs)
    assert d["primera"]["latido"] == 31 and d["primera"]["campos"] == ["accion"] and d["iguales"] == 30
    # Grabar a media vida: la segunda empieza en el latido 50 y se alinea por latido, no por línea.
    d = divergencia(ra, ra[49:])
    assert d["primera"] is None and d["comunes"] == len(ra) - 49
    # Niveles distintos: se comparan los campos comunes (y las 20 primeras proposiciones del saber).
    _, rcog = leer(rutas["cog"][1])
    assert divergencia(ra, rcog)["primera"] is None


def test_la_api_compara_grabaciones_y_da_sus_series(tmp_path, grabaciones_minimo):
    carpeta, rutas = grabaciones_minimo
    datos = tmp_path / "datos"
    shutil.copytree(carpeta, datos / "grabaciones")
    tel = Telemetria(puerto=0, anfitrion="127.0.0.1", modo_antesala=True, datos=str(datos))
    try:
        s, d, _ = _pedir(tel, "GET", f"grabaciones/{rutas['a'][0]}/series")
        assert s == 200 and d["registros"] == 120 and d["mundo"] == "minimo" and d["cabecera"]["semilla"] == 1
        s, d, _ = _pedir(tel, "GET", f"grabaciones/{rutas['a'][0]}/comparar/{rutas['c'][0]}")
        assert s == 200 and d["divergencia"]["primera"] is not None and d["configuracion"]["distintas"] == ["semilla"]
        s, d, _ = _pedir(tel, "GET", "vidas/actual/series")
        assert s == 200 and d["registros"] == 0
        assert _pedir(tel, "GET", "grabaciones/nada/series")[1]["error"]["codigo"] == "id_invalido"
    finally:
        tel.detener()


# --- comparar estirpes ---------------------------------------------------------------------------------------------------------
def test_comparar_estirpes_generacion_a_generacion(tmp_path):
    raiz = tmp_path / "datos"
    ejecutar("minimo", latidos=40, semilla=1, generaciones=3, consola=False, datos=str(raiz / "minimo"), tabula_rasa=True, plazo_logico=40)
    viv = Vivero(str(raiz))
    archivada = viv.archivar("minimo", motivo="archivar")
    ejecutar("minimo", latidos=40, semilla=2, generaciones=2, consola=False, datos=str(raiz / "minimo"), plazo_logico=40)
    a = viv.estirpe("companero:minimo")
    b = viv.estirpe(archivada["id"])
    assert (a["tipo"], len(a["vidas"]), b["tipo"], len(b["vidas"])) == ("companero", 2, "estirpe", 3)
    c = comparar_estirpes(a, b)
    assert c["mismo_mundo"] and [f["generacion"] for f in c["filas"]] == [1, 2, 3]
    for f in c["filas"][:2]:
        assert f["diferencia"] == round(f["b"]["score"] - f["a"]["score"], 2)
        assert f["rasgos"]["apertura"] == [f["a"]["arquetipo"]["apertura"], f["b"]["arquetipo"]["apertura"]]
    assert c["filas"][2]["a"] is None and c["filas"][2]["diferencia"] is None   # A no tiene tercera generación
    assert c["a"]["generaciones"] == 2 and c["b"]["generaciones"] == 3
    assert c["b"]["mejor_score"] == max(v["score"] for v in b["vidas"])
    # Una ficha también es una estirpe (sus vidas).
    ficha = viv.guardar("minimo")
    assert len(viv.estirpe(ficha["id"])["vidas"]) == 2


def test_la_api_compara_estirpes(tmp_path):
    raiz = tmp_path / "datos"
    ejecutar("minimo", latidos=30, semilla=1, generaciones=2, consola=False, datos=str(raiz / "minimo"), tabula_rasa=True, plazo_logico=40)
    archivada = Vivero(str(raiz)).archivar("minimo")
    ejecutar("minimo", latidos=30, semilla=3, consola=False, datos=str(raiz / "minimo"), plazo_logico=40)
    tel = Telemetria(puerto=0, anfitrion="127.0.0.1", modo_antesala=True, datos=str(raiz))
    try:
        s, d, _ = _pedir(tel, "GET", f"estirpes/comparar?a=companero:minimo&b={archivada['id']}")
        assert s == 200 and len(d["filas"]) == 2 and d["a"]["generaciones"] == 1 and d["b"]["generaciones"] == 2
        s, d, _ = _pedir(tel, "GET", "estirpes/comparar?a=companero:minimo")
        assert s == 400 and d["error"]["codigo"] == "campo_invalido"
        s, d, _ = _pedir(tel, "GET", "estirpes/comparar?a=companero:archivos&b=companero:minimo")
        assert s == 404 and d["error"]["codigo"] == "sin_companero"
    finally:
        tel.detener()


# --- plurales e idiomas ------------------------------------------------------------------------------------------------------------
PLURAL = re.compile(r"\{(\w+)\|([^|{}]*)\|([^|{}]*)\}")


def _formar(plantilla, valor):
    """Lo que hace t() de web/i18n.js con todos los parámetros a ``valor``."""
    s = PLURAL.sub(lambda m: m.group(2) if valor == 1 else m.group(3), plantilla)
    return re.sub(r"\{(\w+)\}", str(valor), s)


def test_i18n_js_forma_los_plurales_como_este_test():
    js = _leer_web("i18n.js")
    assert r"/\{(\w+)\|([^|{}]*)\|([^|{}]*)\}/g" in js and "Number(params[n]) === 1 ? uno : varios" in js


# Sustantivos que, detrás de un número, son plurales: si salen tras «1», falta la forma singular.
PLURALES = {
    "es": {"cosas", "latidos", "registros", "piezas", "vidas", "generaciones", "candidatos", "rechazos", "avisos", "líneas",
           "acciones", "recuerdos", "componentes", "sorpresas", "logros", "cambios", "guillotinas", "refutadas", "veces"},
    "en": {"things", "heartbeats", "beats", "records", "pieces", "lives", "generations", "candidates", "rejections", "warnings",
           "lines", "actions", "memories", "components", "surprises", "achievements", "changes", "guillotines", "times"},
}


@pytest.mark.parametrize("idioma,dic", [("es", ES), ("en", EN)])
def test_ningun_1_cosas(idioma, dic):
    malas = {}
    for clave, plantilla in dic.items():
        texto = _formar(plantilla, 1)
        for m in re.finditer(r"\b1 (?:\w+ )?(\w+)", texto, re.UNICODE):
            if m.group(1).lower() in PLURALES[idioma] and not re.search(r"\b1 de\b", m.group(0)):
                malas[clave] = texto
    assert not malas, malas


@pytest.mark.parametrize("idioma,dic", [("es", ES), ("en", EN)])
def test_los_plurales_tienen_sus_dos_formas(idioma, dic):
    for clave, plantilla in dic.items():
        for m in PLURAL.finditer(plantilla):
            assert m.group(2).strip() and m.group(3).strip() and m.group(2) != m.group(3), (idioma, clave, m.group(0))
        assert "|" not in PLURAL.sub("", plantilla) or "{" not in plantilla.split("|")[0][-1:], clave


def test_los_dos_idiomas_pluralizan_los_mismos_parametros():
    for clave in ES:
        assert {m.group(1) for m in PLURAL.finditer(ES[clave])} <= set(re.findall(r"\{(\w+)[|}]", EN[clave])), clave
        assert {m.group(1) for m in PLURAL.finditer(EN[clave])} <= set(re.findall(r"\{(\w+)[|}]", ES[clave])), clave


def test_ejemplos_de_plurales():
    assert _formar(ES["lab.hechos_aprende"], 1) == "1 cosa aprendida" and _formar(ES["lab.hechos_aprende"], 3) == "3 cosas aprendidas"
    assert _formar(EN["sabe.y_mas"], 1) == "and 1 more thing" and _formar(EN["sabe.y_mas"], 2) == "and 2 more things"
    assert "1 latido" in _formar(ES["hecho.muere"], 1) and "1 latidos" not in _formar(ES["hecho.muere"], 1)
    assert "companero.continuar_ayuda_1" not in ES          # el apaño de la antesala ya no hace falta


# --- claves que forman las vistas nuevas -------------------------------------------------------------------------------------------
def _lista_js(texto, nombre):
    m = re.search(nombre + r"\s*=\s*\[([^\]]*)\]", texto)
    assert m, nombre
    return re.findall(r"'([^']+)'", m.group(1))


def test_claves_de_las_vistas_de_t5b():
    lab = _leer_web("vistas", "lab.js")
    epi = _leer_web("lab", "epistemologia.js")
    ana = _leer_web("lab", "analisis.js")
    bio = _leer_web("lab", "biologia.js")
    vistas = _lista_js(lab, "const VISTAS")
    claves = [f"lab.vista.{v}" for v in vistas]
    claves += [f"lab.detalle_vacio_{v}" for v in ("epistemologia", "biologia", "analisis", "cierre")]
    claves += [f"lab.desde_vista.{v}" for v in ("epistemologia", "analisis")]
    claves += [f"epi.fuente.{f}" for f in _lista_js(epi, "export const FUENTES")]
    claves += [f"epi.estado.{e}" for e in _lista_js(epi, "export const ESTADOS")]
    claves += [f"epi.evento.{e}" for e in ("aprende", "duda", "refuta")] + [f"epi.tipo.{x}" for x in ("proposicion", "requisito")]
    claves += [f"ana.modo.{m}" for m in _lista_js(ana, "export const MODOS")] + ["ana.modo.superpuestas", "ana.modo.lado"]
    claves += [f"ana.ayuda.{m}" for m in _lista_js(ana, "export const MODOS")]
    claves += [f"ana.serie.{s.replace('.', '_').replace('/', '_')}" for s in _lista_js(ana, "export const SERIES_COMPARABLES")]
    for ident, analogo in re.findall(r"\{ id: '(\w+)', columna: '[^']+', analogo: (true|false)", bio):
        claves += [f"bio.serie.{ident}", f"bio.que.{ident}"]
        if analogo == "true":
            claves += [f"bio.analogo.{ident}", f"bio.analogo_corto.{ident}"]
    faltan = [c for c in claves if c not in ES or c not in EN]
    assert len(claves) > 80 and not faltan, faltan


def test_los_enlaces_del_vivero_llevan_a_las_vistas_de_t5b():
    lab = _leer_web("vistas", "lab.js")
    assert "sabe: { vista: 'epistemologia' }" in lab
    assert "caracter: { vista: 'analisis', modo: 'estirpes' }" in lab and "estirpe: { vista: 'analisis', modo: 'estirpes' }" in lab
    assert "lab.desde_t5b" not in lab and "lab.desde_t5b" not in ES
    assert "&mundo=${encodeURIComponent(this.vida.mundo)}" in _leer_web("vistas", "vivero.js")


# --- análogos de Biología: lo que cita la tabla existe ----------------------------------------------------------------------------
# Cada referencia de la tabla (fichero:línea) con algo que esa línea debe contener.
CITAS = {
    "ida/nucleo/soma.py:43": "self.placer / 100.0 - self.estres",
    "ida/nucleo/soma.py:72": "self.placer - 1.0",
    "ida/nucleo/soma.py:73": "DOPAMINA_BASAL",
    "ida/nucleo/soma.py:80": "2.0 * delta[\"alimentacion\"]",
    "ida/nucleo/soma.py:92": "self.dopamina + rpe",
    "ida/nucleo/soma.py:97": "urgencia = max(peligro",
    "ida/nucleo/soma.py:98": "0.7 * self.estres + 0.3 * urgencia",
    "ida/nucleo/soma.py:99": "calma = acotar(1.0 - max(peligro, tension, self.estres))",
    "ida/core/latido.py:256": "error_prediccion",
    "ida/core/latido.py:310": "descanso >= 95.0",
    "ida/core/latido.py:325": "tension = sum(cognitivas)",
    "ida/core/actuar/tribunal.py:50": "base = arousal * estres + c.confianza * (1.0 - estres)",
    "ida/s2/sentir/emocion.py:17": "arousal=ctx.soma.estres",
    "ida/nucleo/arquitectura.py:57": "soma.placer",
    "ida/nucleo/mundo.py:189": "def deficit",
}


def _linea(ruta, n):
    with open(os.path.join(RAIZ, ruta), encoding="utf-8") as f:
        return f.read().splitlines()[n - 1]


def test_las_citas_de_la_tabla_de_analogos_dicen_lo_que_la_tabla_les_atribuye():
    for cita, texto in CITAS.items():
        ruta, n = cita.rsplit(":", 1)
        assert texto in _linea(ruta, int(n)), cita
    bio = _leer_web("lab", "biologia.js")
    for codigo in re.findall(r"codigo: '([^']+)'", bio):
        for ref in codigo.split(" · "):
            ruta, _, lineas = ref.split(" ")[0].partition(":")
            assert os.path.isfile(os.path.join(RAIZ, ruta)), ref
            total = len(open(os.path.join(RAIZ, ruta), encoding="utf-8").read().splitlines())
            for trozo in re.findall(r"\d+(?:-\d+)?", lineas):
                assert all(1 <= int(x) <= total for x in trozo.split("-")), ref


def test_la_dopamina_no_la_lee_ningun_componente_para_decidir():
    """Lo que dice su fila de la tabla: fuera del Soma y de la telemetría, nadie lee ``dopamina``."""
    lectores = []
    for raiz, _, ficheros in os.walk(os.path.join(RAIZ, "ida")):
        if "telemetria" in raiz:
            continue
        for f in ficheros:
            if f.endswith(".py") and f != "soma.py":
                with open(os.path.join(raiz, f), encoding="utf-8") as fh:
                    if "dopamina" in fh.read():
                        lectores.append(f)
    assert lectores == []


def test_series_sin_registros():
    s = Series().resultado()
    assert s["registros"] == 0 and s["saber"] == [] and s["vidas"] == []
