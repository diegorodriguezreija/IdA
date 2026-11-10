"""El framework base no sabe en qué mundo está: ni importaciones ni palabras de ningún mundo."""

import ast
import pathlib

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent / "ida"
BASE = sorted((RAIZ / "core").rglob("*.py")) + sorted((RAIZ / "sistemas").rglob("*.py"))

IMPORTS_PROHIBIDOS = {"ida.mundos", "ida.telemetria", "playwright", "chess", "crafter", "opentelemetry", "requests", "socket", "http", "shutil", "subprocess"}
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
