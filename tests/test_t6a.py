"""T6a: cierre técnico de la línea T. Mensaje para un Python antiguo, series largas con ``?cada=k`` que conservan los
hechos, instalación de mundos desde un ``pip install .`` no editable, ``--ver`` en el Vivero y OpenTelemetry desde la
API. (Las rutas retiradas están en ``tests/test_api_v1.py``; OTel, en ``tests/test_observabilidad.py``; la configuración
de paquetes, en ``tests/test_empaquetado.py``.)"""

import ast
import http.client
import json
import os
import sys
from collections import namedtuple

import pytest

import ida.__main__ as entrada
from ida.ejecutor import ejecutar
from ida.telemetria import analisis, api_v1, catalogo, instalador
from ida.telemetria.grabacion import leer
from ida.telemetria.servidor import Telemetria

VersionFalsa = namedtuple("VersionFalsa", "major minor micro releaselevel serial")


# --- Python antiguo -----------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("version", [(3, 11, 9, "final", 0), (3, 8, 10, "final", 0), (3, 6, 0, "final", 0)])
def test_python_antiguo_dice_que_hace_falta_sin_traza(monkeypatch, capsys, version):
    llamado = []
    monkeypatch.setattr(sys, "version_info", VersionFalsa(*version))
    monkeypatch.setattr(entrada, "_main", lambda argv: llamado.append(argv) or 0)   # no llega al resto de la CLI
    assert entrada.main([]) == 1
    salida = capsys.readouterr()
    assert not llamado and salida.out == ""
    texto = salida.err
    actual = ".".join(str(x) for x in version[:3])
    assert f"IdA necesita Python 3.12 o posterior, y este es Python {actual}" in texto
    assert "py install 3.12" in texto and "python --version" in texto and "Traceback" not in texto


def test_python_reciente_sigue(monkeypatch):
    monkeypatch.setattr(sys, "version_info", VersionFalsa(3, 12, 0, "final", 0))
    monkeypatch.setattr(entrada, "_main", lambda argv: 7)
    assert entrada.main([]) == 7 and entrada.aviso_python((3, 15, 1)) is None


def test_el_modulo_de_entrada_no_usa_sintaxis_moderna():
    """Cualquier Python 3 debe poder leer ``ida/__main__.py`` para llegar a la comprobación: ni f-strings, ni
    anotaciones (``X | Y`` se evalúa al definir), ni sintaxis posterior a 3.7; y nada de IdA se importa arriba."""
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ida", "__main__.py")
    with open(ruta, encoding="utf-8") as f:
        fuente = f.read()
    arbol = ast.parse(fuente, feature_version=(3, 7))
    for nodo in ast.walk(arbol):
        assert not isinstance(nodo, (ast.JoinedStr, ast.AnnAssign, ast.NamedExpr)), (type(nodo).__name__, getattr(nodo, "lineno", "?"))
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            assert nodo.returns is None, nodo.name
            assert all(a.annotation is None for a in [*nodo.args.args, *nodo.args.kwonlyargs]), nodo.name
    arriba = [n for n in arbol.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    assert [a.name for n in arriba for a in n.names] == ["sys"]


# --- series largas -------------------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def grabacion_con_muertes(tmp_path_factory):
    """Dos vidas de mínimo que mueren (cuatro lobos, una baya): daños, aprendizajes, muertes y registros de cierre."""
    d = tmp_path_factory.mktemp("t6a")
    ruta = str(d / "datos" / "grabaciones" / "minimo-20261127-120000.jsonl.gz")
    os.makedirs(os.path.dirname(ruta))
    ejecutar("minimo", latidos=600, semilla=31, generaciones=2, consola=False, datos=str(d / "datos" / "minimo"), plazo_logico=40,
             nivel="cognitivo", grabar=ruta, opciones_mundo={"depredadores": 4, "comida": 1, "tamano": 7})
    _, regs = leer(ruta)
    return str(d / "datos"), regs


def _comprobar_reducidas(completa, reducida, cada):
    cols, n = reducida["columnas"], reducida["columnas"]["n"]
    assert reducida["cada"] == cada and reducida["registros_totales"] == completa["registros"]
    assert reducida["registros"] == len(n) and all(len(c) == len(n) for c in cols.values())
    assert n == sorted(n) and n[0] == completa["columnas"]["n"][0] and n[-1] == completa["columnas"]["n"][-1]
    assert reducida["hechos"] == completa["hechos"] and reducida["saber"] == completa["saber"] and reducida["vidas"] == completa["vidas"]
    en_series = set(n)
    for h in completa["hechos"]:
        assert h["n"] in en_series, h                                    # ningún hecho marcado cae entre muestras
    for i, x in enumerate(completa["columnas"]["n"]):
        if completa["columnas"]["cierre"][i]:
            assert x in en_series                                        # ni un cierre
    pos = {x: i for i, x in enumerate(completa["columnas"]["n"])}
    for nombre, col in cols.items():                                     # cada fila es la de la serie entera
        assert col == [completa["columnas"][nombre][pos[x]] for x in n], nombre
    for v in completa["vidas"]:
        assert v["desde"] in en_series and v["hasta"] in en_series       # el principio y el fin de cada vida


def test_reducir_conserva_los_hechos_marcados(grabacion_con_muertes):
    _, regs = grabacion_con_muertes
    completa = analisis.series_de(regs)
    tipos = {h["tipo"] for h in completa["hechos"]}
    assert {"muere", "dano", "aprende"} <= tipos and sum(completa["columnas"]["cierre"]) == 2
    # Mínimo no da logros: se añade uno entre dos muestras para ver que su fila se queda.
    con_logro = dict(completa, hechos=[*completa["hechos"], {"n": 13, "tipo": "logro", "nombre": "prueba"}])
    for cada in (2, 7, 25):
        reducida = analisis.reducir(con_logro, cada)
        _comprobar_reducidas(con_logro, reducida, cada)
        assert 13 in reducida["columnas"]["n"]
        assert reducida["registros"] < completa["registros"]
    assert analisis.reducir(completa, 1)["columnas"] == completa["columnas"]
    with pytest.raises(ValueError):
        analisis.reducir(completa, 0)


def test_reducir_por_defecto_respeta_el_maximo(grabacion_con_muertes):
    _, regs = grabacion_con_muertes
    completa = analisis.series_de(regs)
    assert analisis.reducir(completa)["cada"] == 1                       # 116 filas: por debajo de MAX_PUNTOS
    reducida = analisis.reducir(completa, maximo=20)
    assert reducida["cada"] == -(-completa["registros"] // 20)
    _comprobar_reducidas(completa, reducida, reducida["cada"])
    regulares = [x for x in reducida["columnas"]["n"] if x % reducida["cada"] == 0]
    assert len(regulares) <= 20


def _get(tel, ruta):
    con = http.client.HTTPConnection("127.0.0.1", tel.puerto, timeout=30)
    con.request("GET", ruta)
    r = con.getresponse()
    datos = json.loads(r.read())
    con.close()
    return r.status, datos


def test_api_de_series_con_cada(grabacion_con_muertes, monkeypatch):
    datos, regs = grabacion_con_muertes
    tel = Telemetria(puerto=0, datos=datos)
    try:
        estado, lista = _get(tel, "/api/v1/grabaciones")
        gid = lista["grabaciones"][0]["id"]
        estado, completa = _get(tel, f"/api/v1/grabaciones/{gid}/series")
        assert estado == 200 and completa["cada"] == 1 and completa["registros"] == completa["registros_totales"] == len(regs)
        estado, reducida = _get(tel, f"/api/v1/grabaciones/{gid}/series?cada=10")
        assert estado == 200 and reducida["grabacion"]["id"] == gid
        _comprobar_reducidas(completa, reducida, 10)
        monkeypatch.setattr(analisis, "MAX_PUNTOS", 30)                   # el máximo por defecto se aplica sin ?cada
        monkeypatch.setattr(analisis.reducir, "__defaults__", (None, 30))
        estado, defecto = _get(tel, f"/api/v1/grabaciones/{gid}/series")
        assert defecto["cada"] == -(-len(regs) // 30)
        _comprobar_reducidas(completa, defecto, defecto["cada"])
        for malo in ("0", "-3", "x", "1.5"):
            estado, error = _get(tel, f"/api/v1/grabaciones/{gid}/series?cada={malo}")
            assert estado == 400 and error["error"]["codigo"] == "campo_invalido" and error["error"]["campo"] == "cada"
        estado, directo = _get(tel, "/api/v1/vidas/actual/series?cada=3")
        assert estado == 200 and directo["cada"] == 3
    finally:
        tel.detener()


# --- instalar mundos desde una instalación no editable ---------------------------------------------------------------
def test_ordenes_de_instalacion_editable_y_no_editable(monkeypatch):
    assert instalador.ordenes("crafter", "crafter")[0][-2:] == ["-e", ".[crafter]"]
    monkeypatch.setattr(catalogo, "requisitos_del_extra", lambda extra: {"snake": ["playwright>=1.40"]}.get(extra, []))
    assert instalador.ordenes("snake", "snake", editable=False) == [
        [sys.executable, "-m", "pip", "install", "playwright>=1.40"], [sys.executable, "-m", "playwright", "install", "chromium"]]


def test_extras_y_requisitos_de_los_metadatos(monkeypatch, tmp_path):
    from importlib import metadata

    class Meta:
        def get_all(self, clave):
            return ["crafter", "ajedrez"] if clave == "Provides-Extra" else None

    monkeypatch.setattr(metadata, "metadata", lambda nombre: Meta())
    monkeypatch.setattr(metadata, "requires", lambda nombre: [
        'crafter>=1.8; extra == "crafter"', "chess>=1.10 ; extra=='ajedrez'", 'pytest>=8; extra == "dev"'])
    assert catalogo.extras_conocidos(str(tmp_path / "no-hay-pyproject.toml")) == ["ajedrez", "crafter"]
    assert catalogo.requisitos_del_extra("crafter") == ["crafter>=1.8"]
    assert catalogo.requisitos_del_extra("ajedrez") == ["chess>=1.10"]
    assert catalogo.requisitos_del_extra("snake") == []
    assert not catalogo.editable(str(tmp_path)) and catalogo.editable(catalogo.RAIZ)


def test_el_instalador_no_editable_instala_los_requisitos(monkeypatch, tmp_path):
    from importlib import metadata

    monkeypatch.setattr(metadata, "metadata", lambda nombre: type("M", (), {"get_all": lambda self, c: ["crafter"]})())
    monkeypatch.setattr(metadata, "requires", lambda nombre: ['crafter>=1.8; extra == "crafter"'])
    lanzadas = []

    class Proceso:
        stdout = iter(["hecho\n"])

        def wait(self):
            return 0

    inst = instalador.Instalador(lanzar=lambda orden, cwd: lanzadas.append(orden) or Proceso(), raiz=str(tmp_path))
    i = inst.instalar("crafter")
    with i.cond:
        i.cond.wait_for(lambda: i.estado != "en_curso", timeout=10)
    assert i.estado == "ok" and lanzadas == [[sys.executable, "-m", "pip", "install", "crafter>=1.8"]]


# --- --ver: la aplicación sigue la vida de la CLI en el Vivero --------------------------------------------------------
def test_ver_abre_el_vivero_con_la_vida_de_la_cli(monkeypatch, tmp_path, capsys):
    import webbrowser

    abiertas, vistas = [], {}
    monkeypatch.setattr(webbrowser, "open", lambda url: abiertas.append(url))
    original = Telemetria.fin_acompanada

    def fin(self):
        original(self)
        self.lab.esperar_cola()
        vistas["vida"] = self.vida_actual()
        vistas["indice"] = self.lab.directo.indice()
        self.activo = False                     # sin esperar a Ctrl+C

    monkeypatch.setattr(Telemetria, "fin_acompanada", fin)
    datos = tmp_path / "raiz" / "minimo"
    assert entrada.main(["--mundo", "minimo", "--latidos", "8", "--semilla", "3", "--ver", "--plazo-logico", "40",
                         "--datos", str(datos), "--opcion", "comida=3"]) == 0
    salida = capsys.readouterr().out
    assert "/#/vivero" in salida and abiertas and abiertas[0].endswith("/#/vivero")
    vida = vistas["vida"]
    assert vida["origen"] == "cli" and vida["mundo"] == "minimo" and not vida["activa"] and vida["latido"] == 8
    assert vida["nivel"] == "completo" and vida["semilla"] == 3 and vida["opciones"]["comida"] == 3
    assert vistas["indice"]["siguiente"] == 8                          # el directo del Laboratorio la tiene entera
    assert os.path.exists(datos / "linaje.json")                       # los datos van donde dijo --datos


def test_ver_sin_navegador(monkeypatch, tmp_path):
    import webbrowser

    abiertas = []
    monkeypatch.setattr(webbrowser, "open", lambda url: abiertas.append(url))
    monkeypatch.setattr(Telemetria, "fin_acompanada", lambda self: setattr(self, "activo", False))
    assert entrada.main(["--mundo", "minimo", "--latidos", "2", "--ver", "--no-navegador", "--plazo-logico", "40",
                         "--datos", str(tmp_path / "minimo")]) == 0
    assert abiertas == []


# --- OpenTelemetry desde la API ------------------------------------------------------------------------------------------
def test_otel_desde_la_api(monkeypatch):
    monkeypatch.setattr(catalogo, "observabilidad", lambda: False)
    with pytest.raises(api_v1.ErrorApi) as e:
        api_v1.preparar_vida({"mundo": "minimo", "otel": True})
    assert e.value.http == 409 and e.value.codigo == "sin_observabilidad" and "sin_observabilidad" in api_v1.CODIGOS
    with pytest.raises(api_v1.ErrorApi) as e:
        api_v1.preparar_vida({"mundo": "minimo", "otel": "si"})
    assert e.value.codigo == "campo_invalido"
    assert api_v1.preparar_vida({"mundo": "minimo"})["otel"] is False
    monkeypatch.setattr(catalogo, "observabilidad", lambda: True)
    assert api_v1.preparar_vida({"mundo": "minimo", "otel": True})["otel"] is True


def test_mundos_dice_si_hay_observabilidad(tmp_path):
    tel = Telemetria(puerto=0, datos=str(tmp_path))
    try:
        estado, datos = _get(tel, "/api/v1/mundos")
        assert estado == 200 and datos["observabilidad"] is catalogo.observabilidad()
    finally:
        tel.detener()
