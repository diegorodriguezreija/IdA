"""Separación de licencias: python-chess (GPL-3.0-or-later) solo se importa dentro de ida/mundos/ajedrez/.

El resto del repositorio es Apache-2.0 y debe funcionar sin python-chess instalado (ver NOTICE).
"""

import ast
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CARPETA_GPL = RAIZ / "ida" / "mundos" / "ajedrez"


def _importa_chess(ruta: pathlib.Path) -> bool:
    for nodo in ast.walk(ast.parse(ruta.read_text(encoding="utf-8"))):
        if isinstance(nodo, ast.Import) and any(a.name.split(".")[0] == "chess" for a in nodo.names):
            return True
        if isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.module.split(".")[0] == "chess":
            return True
    return False


def test_chess_solo_en_la_carpeta_gpl():
    fuera = [
        str(r.relative_to(RAIZ))
        for r in sorted((RAIZ / "ida").rglob("*.py"))
        if CARPETA_GPL not in r.parents and _importa_chess(r)
    ]
    assert not fuera, f"importan chess fuera de ida/mundos/ajedrez/: {fuera}"


def test_la_carpeta_gpl_tiene_su_licencia():
    assert (CARPETA_GPL / "LICENCIA.md").is_file()
