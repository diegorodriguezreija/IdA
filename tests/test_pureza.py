"""El framework base no sabe en qué mundo está: ni importaciones ni palabras de ningún mundo."""

import ast
import pathlib

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent / "ida"
BASE = sorted((RAIZ / "core").rglob("*.py")) + sorted((RAIZ / "sistemas").rglob("*.py"))

IMPORTS_PROHIBIDOS = {
    "ida.mundos", "ida.telemetria", "ida.bibliotecas", "playwright", "chess",
    "crafter", "opentelemetry", "requests", "socket", "http", "shutil", "subprocess",
}
IMPORTS_SOLO_PERSISTENCIA = {"os", "sqlite3", "json"}
PALABRAS_DE_MUNDO = {
    "archivo", "fichero", "carpeta", "directorio", "brote", "byte", ".txt", ".exe",
    "snake", "serpiente", "manzana", "ajedrez", "chess", "tablero", "jaque", "rey",
    "crafter", "zombi", "zombie", "vaca", "esqueleto", "árbol", "madera",
    "lobo", "baya", "seta", "pradera",
}


@pytest.mark.parametrize("ruta", BASE, ids=lambda p: p.name)
def test_pureza(ruta):
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        modulos = []
        if isinstance(nodo, ast.Import):
            modulos = [a.name for a in nodo.names]
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos = [nodo.module]
        for m in modulos:
            assert not any(m == p or m.startswith(p + ".") for p in IMPORTS_PROHIBIDOS), f"{ruta.name} importa {m}"
            if m.split(".")[0] in IMPORTS_SOLO_PERSISTENCIA:
                assert ruta.name in {"persistencia.py", "linaje.py"}, f"{ruta.name} no debe importar {m}"
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
            texto = nodo.value.lower()
            for palabra in PALABRAS_DE_MUNDO:
                assert palabra not in texto.split() and f" {palabra}" not in texto, f"{ruta.name}: palabra de mundo '{palabra}' en {nodo.value!r}"


# Reglas de reparto de importaciones (D2):
# - ida/core NO importa ida/sistemas, ida/cuerpos ni ida/mundos
# - ida/sistemas NO importa ni ida/mundos ni ida/cuerpos
# - ida/cuerpos NO importa ida/mundos
# - ida/mundos puede importar los dos
SISTEMAS = sorted((RAIZ / "sistemas").rglob("*.py"))
CUERPOS = sorted((RAIZ / "cuerpos").rglob("*.py"))


def _modulos_importados(arbol: ast.AST) -> list[str]:
    modulos: list[str] = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos.extend(a.name for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.append(nodo.module)
    return modulos


@pytest.mark.parametrize("ruta", SISTEMAS, ids=lambda p: p.name)
def test_importaciones_sistemas(ruta: pathlib.Path) -> None:
    """ida/sistemas no importa ni ida/mundos ni ida/cuerpos (D2)."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for m in _modulos_importados(arbol):
        assert not (m == "ida.mundos" or m.startswith("ida.mundos.")), f"{ruta.name} importa {m}"
        assert not (m == "ida.cuerpos" or m.startswith("ida.cuerpos.")), f"{ruta.name} importa {m}"


CORE = sorted((RAIZ / "core").rglob("*.py"))


@pytest.mark.parametrize("ruta", CORE, ids=lambda p: p.name)
def test_importaciones_core(ruta: pathlib.Path) -> None:
    """ida/core no importa ida/sistemas, ida/cuerpos ni ida/mundos, ni siquiera en diferido o para tipos (D2, D7)."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for m in _modulos_importados(arbol):
        for p in ("ida.sistemas", "ida.cuerpos", "ida.mundos"):
            assert not (m == p or m.startswith(p + ".")), f"{ruta.name} importa {m}"


@pytest.mark.parametrize("ruta", CUERPOS, ids=lambda p: p.name)
def test_importaciones_cuerpos(ruta: pathlib.Path) -> None:
    """ida/cuerpos no importa ida/mundos (D2)."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for m in _modulos_importados(arbol):
        assert not (m == "ida.mundos" or m.startswith("ida.mundos.")), f"{ruta.name} importa {m}"

