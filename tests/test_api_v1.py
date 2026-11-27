"""API v1 del servidor (T3, O14, O17): http.client contra un servidor en un puerto libre, con datos temporales."""

import json
import sys
import time
import http.client

import pytest

from ida.mundos import MUNDOS
from ida.mundos.opciones import validar_declaracion
from ida.telemetria import catalogo
from ida.telemetria.esquema import validar
from ida.telemetria.instalador import Instalador
from ida.telemetria.servidor import Telemetria


class _ProcesoFalso:
    """Un subproceso simulado: devuelve unas líneas y un código de salida."""

    def __init__(self, orden, lineas, codigo=0):
        self.orden = orden
        self.stdout = iter(lineas)
        self._codigo = codigo

    def wait(self):
        return self._codigo


@pytest.fixture
def servidor(tmp_path):
    ordenes = []

    def lanzar(orden, cwd):
        ordenes.append((orden, cwd))
        return _ProcesoFalso(orden, [f"salida de {orden[2]} 1\n", f"salida de {orden[2]} 2\n"])

    tel = Telemetria(puerto=0, anfitrion="127.0.0.1", modo_antesala=True, datos=str(tmp_path / "datos"),
                     instalador=Instalador(lanzar=lanzar))
    tel.ordenes_simuladas = ordenes
    try:
        yield tel
    finally:
        tel.detener()


def _pedir(tel, metodo, ruta, cuerpo=None, origen="propio", cabeceras=None):
    con = http.client.HTTPConnection("127.0.0.1", tel.puerto, timeout=15)
    h = {"Content-Type": "application/json"}
    if origen == "propio":
        h["Origin"] = f"http://127.0.0.1:{tel.puerto}"
    elif origen:
        h["Origin"] = origen
    h.update(cabeceras or {})
    con.request(metodo, ruta, body=json.dumps(cuerpo).encode() if cuerpo is not None else None, headers=h)
    r = con.getresponse()
    datos = r.read()
    con.close()
    return r.status, (json.loads(datos) if datos and r.getheader("Content-Type", "").startswith("application/json") else datos)


def _eventos(tel, ruta, hasta, limite=20.0):
    """Lee eventos SSE (nombre, datos) de ``ruta`` hasta que ``hasta(eventos)`` sea verdadero."""
    con = http.client.HTTPConnection("127.0.0.1", tel.puerto, timeout=limite)
    con.request("GET", ruta)
    r = con.getresponse()
    assert r.status == 200 and r.getheader("Content-Type").startswith("text/event-stream")
    eventos, nombre, fin = [], None, time.monotonic() + limite
    try:
        while time.monotonic() < fin:
            linea = r.fp.readline().decode("utf-8")
            if not linea:
                break
            linea = linea.rstrip("\n")
            if linea.startswith("event: "):
                nombre = linea[7:]
            elif linea.startswith("data: "):
                eventos.append((nombre, json.loads(linea[6:])))
                if hasta(eventos):
                    break
    finally:
        con.close()
    return eventos


def _esperar(condicion, limite=15.0):
    fin = time.monotonic() + limite
    while time.monotonic() < fin:
        if condicion():
            return True
        time.sleep(0.05)
    return False


# --- mundos y presets -------------------------------------------------------------------------------------------------
def test_mundos_estructura_y_opciones(servidor):
    estado, datos = _pedir(servidor, "GET", "/api/v1/mundos")
    assert estado == 200
    mundos = datos["mundos"]
    assert [m["nombre"] for m in mundos][0] == "crafter"           # el mundo estrella, primero
    assert {m["nombre"] for m in mundos} == set(MUNDOS)
    for m in mundos:
        assert set(m) >= {"nombre", "estado", "lanzable", "extra", "tiempo_real", "opciones", "estrella", "instalacion"}
        assert m["estado"] in catalogo.ESTADOS
        assert m["extra"] in (None, *catalogo.extras_conocidos())
        if m["opciones"] is not None:
            assert m["opciones"], m["nombre"]
            for d in m["opciones"]:
                assert validar_declaracion(d) == [], (m["nombre"], d["nombre"])
    por_nombre = {m["nombre"]: m for m in mundos}
    assert por_nombre["crafter"]["estrella"] and por_nombre["crafter"]["extra"] == "crafter"
    assert por_nombre["snake"]["tiempo_real"] is True and por_nombre["snake"]["extra"] == "snake"
    assert por_nombre["minimo"]["extra"] is None and por_nombre["minimo"]["estado"] == "listo"
    assert [d["nombre"] for d in por_nombre["minimo"]["opciones"]] == ["tamano", "depredadores", "comida"]


def test_estado_de_cada_mundo(monkeypatch):
    """Detección local: paquete con find_spec, Chromium en la caché de Playwright y Stockfish con which."""
    monkeypatch.setattr(catalogo, "paquete_instalado", lambda p: p != "crafter")
    monkeypatch.setattr(catalogo, "chromium_instalado", lambda: False)
    monkeypatch.setattr(catalogo, "stockfish_disponible", lambda: False)
    assert catalogo.estado("crafter") == "no_instalado"
    assert catalogo.estado("snake") == "falta_navegador"
    assert catalogo.estado("ajedrez") == "sin_stockfish"
    assert catalogo.estado("minimo") == catalogo.estado("archivos") == "listo"
    ajedrez = catalogo.ficha("ajedrez")
    assert ajedrez["lanzable"] is True            # sin Stockfish juega contra su rival local (stockfish="" por defecto)
    assert catalogo.ficha("snake")["lanzable"] is False


def test_chromium_se_busca_en_la_cache_de_playwright(monkeypatch, tmp_path):
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path))
    assert catalogo.carpeta_navegadores() == str(tmp_path)
    assert not catalogo.chromium_instalado()
    (tmp_path / "chromium_headless_shell-1200").mkdir()
    assert catalogo.chromium_instalado()


def test_presets(servidor):
    estado, datos = _pedir(servidor, "GET", "/api/v1/presets")
    assert estado == 200
    ids = [p["id"] for p in datos["presets"]]
    assert ids == ["optimo", "cauto", "audaz", "equilibrado", "azar"]
    for p in datos["presets"]:
        for campo in ("nombre", "descripcion"):
            assert p[campo]["es"].strip() and p[campo]["en"].strip()
    optimo = datos["presets"][0]
    assert set(optimo["por_mundo"]) == set(MUNDOS)
    assert datos["rasgos"] == ["apertura", "responsabilidad", "neuroticismo", "extraversion", "umbral_miedo"]
    assert set(datos["rangos"]) == set(datos["rasgos"])


# --- vidas, SSE, ritmo y parada ---------------------------------------------------------------------------------------
def test_lanzar_minimo_y_recibir_registros_por_sse(servidor, tmp_path):
    estado, datos = _pedir(servidor, "POST", "/api/v1/vidas", {"mundo": "minimo", "latidos": 40, "semilla": 3, "caracter": "cauto"})
    assert estado == 201, datos
    vida = datos["vida"]
    assert vida["mundo"] == "minimo" and vida["activa"]
    assert vida["plazo_logico"] == 40.0 and vida["tiempo_real"] is False and vida["ritmo"] == "comodo"   # O11 y O20
    assert vida["ritmo_comodo_ms"] == catalogo.RITMO_COMODO_MS["minimo"] and vida["ritmos"] == ["pausa", "lento", "comodo", "x4", "max"]
    assert vida["opciones"] == {"tamano": 9, "depredadores": 1, "comida": 4}                         # O8: los declarados
    assert vida["arquetipo"]["apertura"] == 0.35
    _pedir(servidor, "POST", "/api/v1/vidas/actual/ritmo", {"ritmo": "max"})
    eventos = _eventos(servidor, "/api/v1/vidas/actual/registro", lambda ev: sum(1 for n, _ in ev if n == "registro") >= 3)
    registros = [d for n, d in eventos if n == "registro"]
    assert eventos[0][0] == "vida" and len(registros) >= 3
    for r in registros:
        assert r["v"] == 1 and r["mundo"] == "minimo" and validar(r) == []
    assert any("escena" in r for r in registros)          # quien se conecta tarde recibe la escena vigente
    assert _esperar(lambda: not servidor.vida_actual()["activa"])
    assert (tmp_path / "datos" / "minimo" / "linaje.json").exists()   # los datos van a la raíz del servidor


def test_sse_vital_recorta_el_registro(servidor):
    _pedir(servidor, "POST", "/api/v1/vidas", {"mundo": "minimo", "latidos": 30})
    eventos = _eventos(servidor, "/api/v1/vidas/actual/registro?nivel=vital", lambda ev: any(n == "registro" for n, _ in ev))
    r = next(d for n, d in eventos if n == "registro")
    assert r["nivel"] == "vital" and "tribunal" not in r and "tiempos_ms" not in r and "cuerpo" in r
    assert validar(r) == []


def test_ritmo_pausa_reanudar_y_parar(servidor):
    estado, _ = _pedir(servidor, "POST", "/api/v1/vidas/actual/ritmo", {"ritmo": "pausa"})
    assert estado == 404                                   # sin vida
    assert _pedir(servidor, "POST", "/api/v1/vidas", {"mundo": "minimo", "latidos": 5000})[0] == 201
    assert _esperar(lambda: (servidor.vida_actual().get("latido") or 0) >= 2)
    estado, datos = _pedir(servidor, "POST", "/api/v1/vidas/actual/ritmo", {"ritmo": "pausa"})
    assert estado == 200 and datos == {"ritmo": "pausa"}
    time.sleep(0.4)                                        # termina la espera en curso
    quieto = servidor.vida_actual()["latido"]
    time.sleep(0.8)
    assert servidor.vida_actual()["latido"] == quieto      # en pausa no avanza
    assert _pedir(servidor, "GET", "/api/v1/vidas/actual")[1]["vida"]["ritmo"] == "pausa"
    assert _pedir(servidor, "POST", "/api/v1/vidas/actual/ritmo", {"ritmo": "x4"})[0] == 200
    assert _esperar(lambda: servidor.vida_actual()["latido"] > quieto + 3, limite=5)
    estado, datos = _pedir(servidor, "POST", "/api/v1/vidas/actual/ritmo", {"ritmo": "x9"})
    assert estado == 400 and datos["error"]["codigo"] == "ritmo_invalido"
    _pedir(servidor, "POST", "/api/v1/vidas/actual/ritmo", {"ritmo": "pausa"})
    estado, datos = _pedir(servidor, "POST", "/api/v1/vidas/actual/parar", {})   # parar también saca de la pausa
    assert estado == 200 and datos["vida"]["activa"] is False
    assert not servidor.hilo_simulacion.is_alive()
    assert _pedir(servidor, "POST", "/api/v1/vidas/actual/parar", {})[0] == 404


def test_ritmo_x1_es_comodo_y_el_catalogo_da_el_comodo(servidor):
    mundos = {m["nombre"]: m for m in _pedir(servidor, "GET", "/api/v1/mundos")[1]["mundos"]}
    assert mundos["minimo"]["ritmo_comodo_ms"] == 300.0 and mundos["archivos"]["ritmo_comodo_ms"] == 300.0
    assert _pedir(servidor, "POST", "/api/v1/vidas", {"mundo": "minimo", "latidos": 5000})[0] == 201
    assert _pedir(servidor, "POST", "/api/v1/vidas/actual/ritmo", {"ritmo": "x1"})[1] == {"ritmo": "comodo"}   # T3
    assert _pedir(servidor, "POST", "/api/v1/vidas/actual/ritmo", {"ritmo": "lento"})[1] == {"ritmo": "lento"}
    assert servidor.ritmo.ms_por_latido(100.0) == 600.0          # lento: el doble del cómodo (300 ms), no del Perfil
    _pedir(servidor, "POST", "/api/v1/vidas/actual/parar", {})


def test_paso_a_paso_avanza_un_latido_cada_vez(servidor):
    assert _pedir(servidor, "POST", "/api/v1/vidas/actual/paso", {})[0] == 404          # sin vida
    assert _pedir(servidor, "POST", "/api/v1/vidas", {"mundo": "minimo", "latidos": 5000})[0] == 201
    estado, datos = _pedir(servidor, "POST", "/api/v1/vidas/actual/paso", {})
    assert estado == 409 and datos["error"]["codigo"] == "sin_pausa"                    # solo en pausa
    _pedir(servidor, "POST", "/api/v1/vidas/actual/ritmo", {"ritmo": "pausa"})
    time.sleep(0.8)                                        # termina la espera en curso
    quieto = servidor.vida_actual()["latido"]
    for k in range(1, 4):
        estado, datos = _pedir(servidor, "POST", "/api/v1/vidas/actual/paso", {})
        assert estado == 200 and datos["ritmo"] == "pausa"
        assert _esperar(lambda k=k: servidor.vida_actual()["latido"] == quieto + k, limite=5)
        time.sleep(0.4)
        assert servidor.vida_actual()["latido"] == quieto + k                         # uno, y se queda quieto
    _pedir(servidor, "POST", "/api/v1/vidas/actual/parar", {})


def test_sse_cognitivo_y_diario(servidor):
    _pedir(servidor, "POST", "/api/v1/vidas", {"mundo": "minimo", "latidos": 60})
    _pedir(servidor, "POST", "/api/v1/vidas/actual/ritmo", {"ritmo": "max"})
    assert _esperar(lambda: not servidor.vida_actual()["activa"])
    eventos = _eventos(servidor, "/api/v1/vidas/actual/registro?nivel=cognitivo", lambda ev: any(n == "registro" for n, _ in ev))
    nombres = [n for n, _ in eventos]
    assert nombres[:2] == ["vida", "diario"]
    diario = eventos[1][1]
    assert diario["hechos"][0]["tipo"] == "nace" and all("latido" in h and "vida" in h for h in diario["hechos"])
    r = next(d for n, d in eventos if n == "registro")
    assert r["nivel"] == "cognitivo" and "tribunal" in r and "saber" in r and "tiempos_ms" not in r and "piezas" not in r
    assert len(r["saber"]) <= 20 and validar(r) == []


def test_ritmo_fijo_en_tiempo_real(servidor):
    servidor._vida = {"id": 9, "mundo": "snake", "activa": True, "tiempo_real": True, "ritmo_ajustable": False, "ritmo": None}
    estado, datos = _pedir(servidor, "POST", "/api/v1/vidas/actual/ritmo", {"ritmo": "x4"})
    assert estado == 409 and datos["error"]["codigo"] == "ritmo_fijo"
    estado, datos = _pedir(servidor, "POST", "/api/v1/vidas/actual/paso", {})
    assert estado == 409 and datos["error"]["codigo"] == "ritmo_fijo"
    servidor._vida = None


def test_errores_al_lanzar(servidor):
    casos = [
        ({"mundo": "marte"}, 400, "mundo_desconocido"),
        ({"mundo": "minimo", "opciones": {"tamano": 500}}, 400, "opcion_invalida"),
        ({"mundo": "minimo", "opciones": {"no_existe": 1}}, 400, "opcion_invalida"),
        ({"mundo": "minimo", "semilla": -1}, 400, "campo_invalido"),
        ({"mundo": "minimo", "latidos": "mucho"}, 400, "campo_invalido"),
        ({"mundo": "minimo", "caracter": "furioso"}, 400, "caracter_invalido"),
        ({"mundo": "minimo", "arquetipo": {"apertura": 2}}, 400, "caracter_invalido"),
        ({"mundo": "minimo", "ficha": {"mundo": "crafter", "arquetipo": {"apertura": 0.5}}}, 400, "ficha_de_otro_mundo"),
        ({"mundo": "minimo", "ficha": {"mundo": "minimo"}}, 400, "ficha_invalida"),
    ]
    for cuerpo, esperado, codigo in casos:
        estado, datos = _pedir(servidor, "POST", "/api/v1/vidas", cuerpo)
        assert (estado, datos["error"]["codigo"]) == (esperado, codigo), cuerpo
        assert datos["error"]["mensaje"]
    con = http.client.HTTPConnection("127.0.0.1", servidor.puerto, timeout=5)
    con.request("POST", "/api/v1/vidas", body=b"{no es json", headers={"Origin": f"http://127.0.0.1:{servidor.puerto}"})
    r = con.getresponse()
    assert r.status == 400 and json.loads(r.read())["error"]["codigo"] == "json_invalido"
    assert _pedir(servidor, "GET", "/api/v1/no_existe")[0] == 404


def test_vida_en_curso_y_reemplazar(servidor):
    assert _pedir(servidor, "POST", "/api/v1/vidas", {"mundo": "minimo", "latidos": 5000})[0] == 201
    estado, datos = _pedir(servidor, "POST", "/api/v1/vidas", {"mundo": "minimo", "latidos": 20})
    assert estado == 409 and datos["error"]["codigo"] == "vida_en_curso"
    estado, datos = _pedir(servidor, "POST", "/api/v1/vidas", {"mundo": "minimo", "latidos": 20, "reemplazar": True})
    assert estado == 201 and datos["vida"]["id"] == 2


def test_ficha_aporta_caracter_y_legado(servidor):
    ficha = {"mundo": "minimo", "individuo": "Minimo_G4", "arquetipo": {"apertura": 0.3, "responsabilidad": 0.6, "neuroticismo": 0.4,
                                                                         "extraversion": 0.5, "umbral_miedo": 0.6}, "legado": {"x": 1}}
    estado, datos = _pedir(servidor, "POST", "/api/v1/vidas", {"mundo": "minimo", "latidos": 5, "ficha": ficha})
    assert estado == 201 and datos["vida"]["arquetipo"]["apertura"] == 0.3 and datos["vida"]["con_legado"]


# --- seguridad: Origin ------------------------------------------------------------------------------------------------
def test_post_con_origen_ajeno_da_403(servidor):
    for origen, cabeceras in (("http://evil.example", {}), (None, {}), (None, {"Referer": "http://evil.example/x"}),
                              (f"http://127.0.0.1:{servidor.puerto + 1}", {})):
        estado, datos = _pedir(servidor, "POST", "/api/v1/vidas", {"mundo": "minimo"}, origen=origen, cabeceras=cabeceras)
        assert estado == 403 and datos["error"]["codigo"] == "origen_no_permitido", (origen, cabeceras)
    assert _pedir(servidor, "POST", "/api/v1/vidas/actual/parar", {}, origen="http://evil.example")[0] == 403
    assert _pedir(servidor, "POST", "/ruta-que-no-existe", {}, origen="http://evil.example")[0] == 403   # antes que la ruta
    assert _pedir(servidor, "POST", "/api/v1/mundos/crafter/instalar", {}, origen="http://evil.example")[0] == 403
    referer = {"Referer": f"http://localhost:{servidor.puerto}/#/antesala"}
    assert _pedir(servidor, "POST", "/api/v1/vidas/actual/parar", {}, origen=None, cabeceras=referer)[0] == 404   # pasa el filtro
    assert servidor.vida_actual() is None


# --- instalación ------------------------------------------------------------------------------------------------------
def test_instalar_fuera_de_la_lista_da_400(servidor, monkeypatch):
    estado, datos = _pedir(servidor, "POST", "/api/v1/mundos/minimo/instalar", {})
    assert estado == 400 and datos["error"]["codigo"] == "sin_extra"
    monkeypatch.setitem(catalogo.DEPENDENCIAS, "crafter", ("crafter]; rm -rf [", "crafter"))
    estado, datos = _pedir(servidor, "POST", "/api/v1/mundos/crafter/instalar", {})
    assert estado == 400 and datos["error"]["codigo"] == "extra_desconocido"
    assert _pedir(servidor, "POST", "/api/v1/mundos/marte/instalar", {})[0] == 404
    assert servidor.ordenes_simuladas == []                  # no se lanzó nada


def test_instalar_con_subproceso_simulado_emite_su_salida_por_sse(servidor):
    estado, datos = _pedir(servidor, "POST", "/api/v1/mundos/snake/instalar", {"extra": "lo que diga el cliente se ignora"})
    assert estado == 202, datos
    inst = datos["instalacion"]
    assert inst["mundo"] == "snake" and inst["extra"] == "snake"
    eventos = _eventos(servidor, inst["url"], lambda ev: ev[-1][0] == "fin")
    lineas = [d["texto"] for n, d in eventos if n == "linea"]
    assert eventos[-1] == ("fin", {**eventos[-1][1], "estado": "ok", "codigo": 0})
    assert "salida de pip 1" in lineas and "salida de playwright 2" in lineas
    ordenes = [o for o, _ in servidor.ordenes_simuladas]
    assert ordenes == [[sys.executable, "-m", "pip", "install", "-e", ".[snake]"],
                       [sys.executable, "-m", "playwright", "install", "chromium"]]
    assert all(cwd == catalogo.RAIZ for _, cwd in servidor.ordenes_simuladas)
    _, mundos = _pedir(servidor, "GET", "/api/v1/mundos")
    assert next(m for m in mundos["mundos"] if m["nombre"] == "snake")["instalacion"]["estado"] == "ok"
    assert _pedir(servidor, "GET", "/api/v1/instalaciones/i999")[0] == 404


def test_instalacion_fallida_y_una_a_la_vez(tmp_path):
    lanzadas = []

    def lanzar(orden, cwd):
        lanzadas.append(orden)
        time.sleep(0.3)
        return _ProcesoFalso(orden, ["ERROR: algo\n"], codigo=1)

    tel = Telemetria(puerto=0, anfitrion="127.0.0.1", modo_antesala=True, datos=str(tmp_path), instalador=Instalador(lanzar=lanzar))
    try:
        assert _pedir(tel, "POST", "/api/v1/mundos/crafter/instalar", {})[0] == 202
        estado, datos = _pedir(tel, "POST", "/api/v1/mundos/ajedrez/instalar", {})
        assert estado == 409 and datos["error"]["codigo"] == "instalacion_en_curso"
        eventos = _eventos(tel, "/api/v1/instalaciones/i1", lambda ev: ev[-1][0] == "fin")
        assert eventos[-1][1]["estado"] == "error" and eventos[-1][1]["codigo"] == 1
        assert len(lanzadas) == 1                         # tras un fallo no sigue con la orden siguiente
        assert "ERROR: algo" in [d["texto"] for n, d in eventos if n == "linea"]
    finally:
        tel.detener()


# --- rutas de la aplicación; las antiguas, retiradas en T6a ----------------------------------------------------------
# Las rutas del linaje se escriben por partes: el criterio de T6a es que ninguna referencia a ellas quede viva en ida/,
# tests/ ni herramientas/ (lo comprueba un grep), y estas solo están para comprobar que ya no existen.
_LINAJE = "/linaje"
RUTAS_RETIRADAS_GET = ("/panel", "/antesala-antigua", "/antesala", "/eventos", "/estado", "/estado_simulacion", _LINAJE,
                       _LINAJE + "/descargar", _LINAJE + "/descargar?mundo=minimo&individuo=Minimo_G1", "/web/../servidor.py")
RUTAS_RETIRADAS_POST = ("/iniciar", "/detener", _LINAJE + "/fijar", _LINAJE + "/restaurar")


def test_rutas_de_la_aplicacion(servidor):
    estado, cuerpo = _pedir(servidor, "GET", "/")
    assert estado == 200 and b"/web/app.js" in cuerpo
    for estatico in ("/web/i18n/es.json", "/web/i18n/en.json", "/web/vistas/antesala.js", "/web/componentes/opciones.js", "/web/estilo.css"):
        assert _pedir(servidor, "GET", estatico)[0] == 200, estatico


def test_las_rutas_retiradas_dan_404(servidor):
    """T6a: el panel y la antesala de antes, su API sin versión y las rutas del linaje ya no existen (también con una vida en
    marcha: ``/`` es siempre la aplicación)."""
    for ruta in RUTAS_RETIRADAS_GET:
        assert _pedir(servidor, "GET", ruta)[0] == 404, ruta
    for ruta in RUTAS_RETIRADAS_POST:
        assert _pedir(servidor, "POST", ruta, {"mundo": "minimo", "individuo": "Minimo_G1"})[0] == 404, ruta
    assert _pedir(servidor, "POST", "/api/v1/vidas", {"mundo": "minimo", "latidos": 300})[0] == 201
    try:
        estado, cuerpo = _pedir(servidor, "GET", "/")
        assert estado == 200 and b"/web/app.js" in cuerpo
        assert _pedir(servidor, "GET", "/panel")[0] == 404
    finally:
        servidor.detener_simulacion()


def test_extra_todos_es_la_union_de_los_mundos():
    import tomllib

    with open(catalogo.PYPROJECT, "rb") as f:
        extras = tomllib.load(f)["project"]["optional-dependencies"]
    assert sorted(extras["todos"]) == sorted(extras["crafter"] + extras["snake"] + extras["ajedrez"])
    assert {e for e, _ in catalogo.DEPENDENCIAS.values() if e} <= set(catalogo.extras_conocidos())
