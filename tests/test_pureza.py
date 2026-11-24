"""El framework base no sabe en qué mundo está: ni importaciones ni palabras de ningún mundo."""

import ast
import pathlib

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent / "ida"
NUCLEO = sorted((RAIZ / "nucleo").rglob("*.py"))
CORE = sorted((RAIZ / "core").rglob("*.py"))
SISTEMAS = (
    sorted((RAIZ / "s1").rglob("*.py"))
    + sorted((RAIZ / "s2").rglob("*.py"))
    + sorted((RAIZ / "s3").rglob("*.py"))
    + ([RAIZ / "sistemas_comun.py"] if (RAIZ / "sistemas_comun.py").exists() else [])
)
CUERPOS = sorted((RAIZ / "cuerpos").rglob("*.py"))
BASE = NUCLEO + CORE + SISTEMAS

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


def _modulos_importados(arbol: ast.AST) -> list[str]:
    modulos: list[str] = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos.extend(a.name for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.append(nodo.module)
    return modulos


@pytest.mark.parametrize("ruta", BASE, ids=lambda p: p.name)
def test_pureza(ruta: pathlib.Path) -> None:
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


# Reglas de reparto de importaciones (D2, P4):
# nucleo ← core (que incluye latido) ← s1-s3 / comun ← cuerpos ← mundos.
# Ningún paquete importa a los que van detrás de él.


@pytest.mark.parametrize("ruta", NUCLEO, ids=lambda p: p.name)
def test_importaciones_nucleo(ruta: pathlib.Path) -> None:
    """ida/nucleo no importa nada de ida salvo ida/nucleo (D2)."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for m in _modulos_importados(arbol):
        if m == "ida" or m.startswith("ida."):
            assert m == "ida.nucleo" or m.startswith("ida.nucleo."), (
                f"{ruta.relative_to(RAIZ)} no debe importar {m}: nucleo solo importa nucleo"
            )


@pytest.mark.parametrize("ruta", CORE, ids=lambda p: p.name)
def test_importaciones_core(ruta: pathlib.Path) -> None:
    """ida/core solo importa ida/nucleo e ida/core (D2)."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for m in _modulos_importados(arbol):
        if m == "ida" or m.startswith("ida."):
            valido = m in {"ida.nucleo", "ida.core"} or m.startswith("ida.nucleo.") or m.startswith("ida.core.")
            assert valido, f"{ruta.relative_to(RAIZ)} no debe importar {m}: core solo importa nucleo y core"


@pytest.mark.parametrize("ruta", SISTEMAS, ids=lambda p: p.name)
def test_importaciones_sistemas(ruta: pathlib.Path) -> None:
    """ida/s1-s3 y lo común no importan ni ida/cuerpos ni ida/mundos (D2)."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for m in _modulos_importados(arbol):
        assert not (m == "ida.cuerpos" or m.startswith("ida.cuerpos.")), f"{ruta.relative_to(RAIZ)} importa {m}"
        assert not (m == "ida.mundos" or m.startswith("ida.mundos.")), f"{ruta.relative_to(RAIZ)} importa {m}"


@pytest.mark.parametrize("ruta", CUERPOS, ids=lambda p: p.name)
def test_importaciones_cuerpos(ruta: pathlib.Path) -> None:
    """ida/cuerpos no importa ida/mundos (D2)."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for m in _modulos_importados(arbol):
        assert not (m == "ida.mundos" or m.startswith("ida.mundos.")), f"{ruta.relative_to(RAIZ)} importa {m}"
