"""Empaquetado (T6a): la configuración de ``pyproject.toml`` incluye cada paquete de ``ida/`` y cada fichero que no es
Python y se usa al correr (la web entera, los manuales de Crafter, la licencia del rival de ajedrez).

Sin setuptools (no es dependencia de IdA): se aplican aquí las reglas de ``[tool.setuptools.packages.find]`` (``include``
y ``exclude`` con comodines, sin paquetes de espacio de nombres) y de ``[tool.setuptools.package-data]`` (comodines
relativos a la carpeta del paquete, ``**`` para cualquier profundidad). La prueba de verdad, ``pip install .`` en un venv
limpio, está en ``docs/DISENO_OBSERVABILIDAD.md`` (sección 16).
"""

import fnmatch
import os
import re
import tomllib

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDA = os.path.join(RAIZ, "ida")


def _config():
    with open(os.path.join(RAIZ, "pyproject.toml"), "rb") as f:
        return tomllib.load(f)["tool"]["setuptools"]


def _paquetes_en_disco():
    """Cada carpeta de ``ida/`` con ``__init__.py``, como nombre de paquete."""
    salida = set()
    for carpeta, subcarpetas, ficheros in os.walk(IDA):
        subcarpetas[:] = [s for s in subcarpetas if s != "__pycache__"]
        if "__init__.py" in ficheros:
            salida.add(os.path.relpath(carpeta, RAIZ).replace(os.sep, "."))
    return salida


def _encontrados(cfg):
    """Lo que ``packages.find`` encuentra con esta configuración (sin espacios de nombres: solo carpetas con ``__init__``)."""
    find = cfg["packages"]["find"]
    assert find.get("namespaces") is False, "sin namespaces, una carpeta de datos nunca se toma por paquete"
    incluir, excluir = find.get("include", ["*"]), find.get("exclude", [])
    return {p for p in _paquetes_en_disco()
            if any(fnmatch.fnmatchcase(p, i) for i in incluir) and not any(fnmatch.fnmatchcase(p, e) for e in excluir)}


def _regex(patron: str) -> "re.Pattern[str]":
    """Comodín de package-data a expresión regular: ``**/`` es cualquier número de carpetas; ``*`` no cruza carpetas."""
    partes, i = [], 0
    while i < len(patron):
        if patron.startswith("**/", i):
            partes.append(r"(?:[^/]+/)*")
            i += 3
        elif patron[i] == "*":
            partes.append(r"[^/]*")
            i += 1
        elif patron[i] == "?":
            partes.append(r"[^/]")
            i += 1
        else:
            partes.append(re.escape(patron[i]))
            i += 1
    return re.compile("".join(partes) + r"\Z")


def _datos_incluidos(cfg, paquetes):
    """Ficheros que no son Python incluidos por package-data: cada patrón es relativo a la carpeta de su paquete."""
    datos = cfg.get("package-data", {})
    incluidos = set()
    for paquete, patrones in datos.items():
        assert paquete in paquetes, f"package-data de {paquete}, que no es un paquete incluido"
        base = os.path.join(RAIZ, *paquete.split("."))
        regex = [_regex(p) for p in patrones]
        for carpeta, subcarpetas, ficheros in os.walk(base):
            subcarpetas[:] = [s for s in subcarpetas if s != "__pycache__"]
            for f in ficheros:
                rel = os.path.relpath(os.path.join(carpeta, f), base).replace(os.sep, "/")
                if any(r.match(rel) for r in regex):
                    incluidos.add(os.path.relpath(os.path.join(carpeta, f), RAIZ).replace(os.sep, "/"))
    return incluidos


def _ficheros_de_datos():
    """Todo lo que hay en ``ida/`` y no es código Python (ni caché)."""
    salida = set()
    for carpeta, subcarpetas, ficheros in os.walk(IDA):
        subcarpetas[:] = [s for s in subcarpetas if s != "__pycache__"]
        for f in ficheros:
            if not f.endswith((".py", ".pyc")):
                salida.add(os.path.relpath(os.path.join(carpeta, f), RAIZ).replace(os.sep, "/"))
    return salida


def test_la_configuracion_incluye_todos_los_paquetes():
    cfg = _config()
    en_disco, encontrados = _paquetes_en_disco(), _encontrados(cfg)
    assert {"ida", "ida.telemetria", "ida.mundos.ajedrez", "ida.mundos.crafter", "ida.mundos.minimo", "ida.mundos.archivos",
            "ida.mundos.snake"} <= en_disco
    assert en_disco - encontrados == set(), f"paquetes que pip no instalaría: {sorted(en_disco - encontrados)}"


def test_la_configuracion_incluye_los_ficheros_de_datos():
    """La web entera (vistas, lab, componentes, i18n, sprites), los manuales de Crafter y la licencia del rival."""
    cfg = _config()
    datos = _ficheros_de_datos()
    incluidos = _datos_incluidos(cfg, _encontrados(cfg))
    assert datos - incluidos == set(), f"ficheros que pip no instalaría: {sorted(datos - incluidos)}"
    web = {d for d in datos if d.startswith("ida/telemetria/web/")}
    for parte in ("index.html", "app.js", "vistas/", "lab/", "componentes/", "i18n/es.json", "i18n/en.json", "i18n/clases/"):
        assert any(d.startswith("ida/telemetria/web/" + parte) for d in web), parte
    for mundo in ("minimo", "archivos", "crafter", "snake", "ajedrez"):
        assert any(d.startswith(f"ida/telemetria/web/sprites/{mundo}/") for d in web), mundo
    assert {"ida/mundos/crafter/crafter_manual.json", "ida/mundos/ajedrez/LICENCIA.md"} <= incluidos


def test_la_web_no_es_un_paquete_y_no_hay_datos_sueltos():
    """Sin ``include-package-data`` (en Windows confunde rutas y avisa) y sin carpetas de datos tomadas por paquetes."""
    cfg = _config()
    assert cfg.get("include-package-data") is False
    assert not any(p.startswith("ida.telemetria.web") for p in _encontrados(cfg))
