"""El código general no usa conceptos de un cuerpo concreto (C1b, D10).

Recorre con AST los ficheros de ``ida/nucleo``, ``ida/core``, ``ida/s1``-``ida/s3`` e ``ida/sistemas_comun.py`` y
revisa identificadores, atributos, nombres de argumentos, importaciones y literales de cadena (no los comentarios ni
las docstrings). La geometría de un cuerpo (vecinos, distancia, la convención de identificadores con posición) la da
el cuerpo a través de ``Cuerpo`` (``ida/nucleo/mundo.py``); lo de cada familia vive en ``ida/cuerpos/``.

Sin lista de excepciones.
"""

import ast
import pathlib
import unicodedata
from typing import Iterator, List, Set, Tuple

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent / "ida"
GENERAL = (
    sorted((RAIZ / "nucleo").rglob("*.py"))
    + sorted((RAIZ / "core").rglob("*.py"))
    + sorted((RAIZ / "s1").rglob("*.py"))
    + sorted((RAIZ / "s2").rglob("*.py"))
    + sorted((RAIZ / "s3").rglob("*.py"))
    + ([RAIZ / "sistemas_comun.py"] if (RAIZ / "sistemas_comun.py").exists() else [])
)
CONCEPTOS_DE_CUERPO = ("casilla", "cuadricula", "rejilla", "manhattan", "direcciones", "pos_de", "cavar")


def _normalizar(texto: str) -> str:
    """Minúsculas y sin acentos."""
    descompuesto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def _docstrings(arbol: ast.AST) -> Set[int]:
    """Identidades de los nodos que son docstrings (primera expresión de cadena de un módulo, clase o función)."""
    ids: Set[int] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and nodo.body:
            primero = nodo.body[0]
            if isinstance(primero, ast.Expr) and isinstance(primero.value, ast.Constant) and isinstance(primero.value.value, str):
                ids.add(id(primero.value))
    return ids


def _textos(arbol: ast.AST) -> Iterator[Tuple[int, str, str]]:
    """(línea, tipo, texto) de cada identificador, atributo, argumento, importación y literal de cadena."""
    docs = _docstrings(arbol)
    for nodo in ast.walk(arbol):
        linea = getattr(nodo, "lineno", 0)
        if isinstance(nodo, ast.Name):
            yield linea, "nombre", nodo.id
        elif isinstance(nodo, ast.Attribute):
            yield linea, "atributo", nodo.attr
        elif isinstance(nodo, ast.arg):
            yield linea, "argumento", nodo.arg
        elif isinstance(nodo, ast.keyword) and nodo.arg is not None:
            yield linea, "argumento", nodo.arg
        elif isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield linea, "definición", nodo.name
        elif isinstance(nodo, (ast.Global, ast.Nonlocal)):
            for n in nodo.names:
                yield linea, "nombre", n
        elif isinstance(nodo, ast.alias):
            yield linea, "importación", nodo.name
            if nodo.asname:
                yield linea, "importación", nodo.asname
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            yield linea, "importación", nodo.module
        elif isinstance(nodo, ast.Constant) and isinstance(nodo.value, str) and id(nodo) not in docs:
            yield linea, "cadena", nodo.value


def _infracciones(ruta: pathlib.Path) -> List[str]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    salida = []
    for linea, tipo, texto in _textos(arbol):
        normal = _normalizar(texto)
        for concepto in CONCEPTOS_DE_CUERPO:
            if concepto in normal:
                salida.append(f"{ruta.relative_to(RAIZ.parent)}:{linea}: {tipo} {texto!r} contiene '{concepto}'")
    return salida


@pytest.mark.parametrize("ruta", GENERAL, ids=lambda p: str(p.relative_to(RAIZ)))
def test_sin_conceptos_de_cuerpo(ruta: pathlib.Path) -> None:
    infracciones = _infracciones(ruta)
    assert not infracciones, "conceptos de un cuerpo concreto en código general:\n" + "\n".join(infracciones)


def test_detecta_conceptos() -> None:
    """El detector ve identificadores, atributos y cadenas (con mayúsculas y acentos), y no ve docstrings."""
    codigo = (
        '"""casilla en la docstring del módulo"""\n'
        "def f(Rejilla):\n"
        '    """manhattan en una docstring"""\n'
        "    x.pos_de = 1\n"
        "    return 'Cuadrícula'\n"
    )
    textos = [_normalizar(t) for _, _, t in _textos(ast.parse(codigo))]
    encontrados = {c for c in CONCEPTOS_DE_CUERPO for t in textos if c in t}
    assert encontrados == {"rejilla", "pos_de", "cuadricula"}
