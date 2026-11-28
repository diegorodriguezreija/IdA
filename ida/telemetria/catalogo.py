"""Catálogo de mundos para la API v1 (O14, O17): estado de instalación, extra que lo instala y opciones declaradas.

La detección no usa la red ni importa las dependencias de los mundos:

- **Paquetes de Python**: ``importlib.util.find_spec`` del paquete del que depende el mundo (``crafter``, ``playwright``,
  ``chess``). Solo busca en las rutas de importación; no ejecuta el paquete.
- **Chromium de Playwright** (Snake): que estén en la caché de navegadores de Playwright las carpetas de la revisión que
  pide el Playwright instalado (``chromium-<rev>`` y ``chromium_headless_shell-<rev>``, leídas de
  ``playwright/driver/package/browsers.json`` sin importar el paquete). Una carpeta de otra revisión, de una
  instalación anterior, no basta: Playwright no la usa. Si ``browsers.json`` no se puede leer, basta cualquier carpeta
  ``chromium-*`` o ``chromium_headless_shell-*``. La caché es la de Playwright (``PLAYWRIGHT_BROWSERS_PATH`` si está fijada; si no, la de cada sistema:
  ``%LOCALAPPDATA%\\ms-playwright`` en Windows, ``~/Library/Caches/ms-playwright`` en macOS y
  ``$XDG_CACHE_HOME/ms-playwright`` o ``~/.cache/ms-playwright`` en Linux). Es un ``os.listdir``.
- **Stockfish** (ajedrez): ``shutil.which("stockfish")``. Sin Stockfish el ajedrez juega contra su rival local
  (``RivalLocal``, el de por defecto: la opción ``stockfish`` vacía), así que el estado ``sin_stockfish`` es lanzable.

Los extras se leen de ``[project.optional-dependencies]`` de ``pyproject.toml`` (``tomllib``): es la lista cerrada de
lo que se puede instalar. Nunca se instala un texto que venga del cliente.
"""

import importlib
import json
import importlib.util
import os
import shutil
import sys
import tomllib
from typing import Any, Dict, List, Optional, Tuple

from ida.mundos import MUNDOS, cargar

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYPROJECT = os.path.join(RAIZ, "pyproject.toml")
DISTRIBUCION = "ida-identidad-artificial"   # el nombre del paquete en pyproject.toml ([project] name)

# Mundo -> (extra de pyproject, paquete del que depende). Mínimo y archivos no tienen dependencias.
DEPENDENCIAS: Dict[str, Tuple[Optional[str], Optional[str]]] = {
    "minimo": (None, None),
    "archivos": (None, None),
    "crafter": ("crafter", "crafter"),
    "snake": ("snake", "playwright"),
    "ajedrez": ("ajedrez", "chess"),
}
# Orden en la antesala: Crafter, el mundo estrella, primero.
ORDEN = ("crafter", "minimo", "archivos", "snake", "ajedrez")
ESTRELLA = "crafter"

# O20: ritmo cómodo para seguir cada mundo a ojo, en ms por latido. Es de la telemetría, no del motor: el plazo del latido
# (``Perfil.frecuencia_ms``) no cambia. ``None``: mundo de tiempo real (el ritmo lo marca el mundo).
# - ajedrez, 1000 ms: cada latido es una jugada de IdA y la respuesta del rival; con menos de un segundo no da tiempo a ver
#   las dos piezas moverse.
# - Crafter, 250 ms: un paso por casilla; a 4 casillas por segundo se sigue a IdA por el mapa y se ven las criaturas.
# - mínimo y archivos, 300 ms: casi todos los latidos son un movimiento o una espera; con menos, el diario corre más de
#   lo que se lee.
RITMO_COMODO_MS: Dict[str, Optional[float]] = {"ajedrez": 1000.0, "crafter": 250.0, "minimo": 300.0, "archivos": 300.0,
                                               "snake": None}
RITMO_COMODO_DEFECTO = 300.0


def ritmo_comodo(mundo: str) -> Optional[float]:
    """Ms por latido del ritmo cómodo de un mundo (O20); ``None`` en los de tiempo real."""
    c = clase(mundo)
    if c is not None and c.perfil.tiempo_real:
        return None
    return RITMO_COMODO_MS.get(mundo, RITMO_COMODO_DEFECTO)


ESTADOS = ("listo", "no_instalado", "falta_navegador", "sin_stockfish")
LANZABLES = ("listo", "sin_stockfish")


def editable(raiz: str = RAIZ) -> bool:
    """¿Corre IdA desde una copia del repositorio (con ``pyproject.toml``)? Si no, es un ``pip install .`` normal (T6a)."""
    return os.path.isfile(os.path.join(raiz, "pyproject.toml"))


def extras_conocidos(ruta: str = PYPROJECT) -> List[str]:
    """Los extras de ``[project.optional-dependencies]`` de ``pyproject.toml``. En una instalación que no es editable no hay
    ``pyproject.toml``: salen de los metadatos del paquete instalado (``Provides-Extra``). Vacío si no hay ninguno."""
    if not os.path.isfile(ruta):
        return sorted(_metadatos_extras())
    try:
        with open(ruta, "rb") as f:
            datos = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return []
    return sorted(datos.get("project", {}).get("optional-dependencies", {}))


def _metadatos_extras() -> List[str]:
    from importlib import metadata

    try:
        return list(metadata.metadata(DISTRIBUCION).get_all("Provides-Extra") or [])
    except metadata.PackageNotFoundError:
        return []


def requisitos_del_extra(extra: str) -> List[str]:
    """Los requisitos de un extra según los metadatos del paquete instalado (``crafter>=1.8``...), sin el marcador. Para
    instalar un mundo desde una instalación que no es editable: ``pip install`` de esos requisitos."""
    from importlib import metadata

    try:
        requisitos = metadata.requires(DISTRIBUCION) or []
    except metadata.PackageNotFoundError:
        return []
    salida = []
    for req in requisitos:
        texto, _, marcador = req.partition(";")
        marcador = marcador.replace(" ", "").replace("'", '"')
        if f'extra=="{extra}"' in marcador:
            salida.append(texto.strip())
    return salida


def paquete_instalado(paquete: str) -> bool:
    try:
        return importlib.util.find_spec(paquete) is not None
    except (ImportError, ValueError):
        return False


def carpeta_navegadores() -> str:
    """La caché de navegadores de Playwright en este sistema (no comprueba que exista)."""
    fijada = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")
    if fijada and fijada != "0":
        return fijada
    if fijada == "0":   # Playwright los guarda dentro de su propio paquete
        espec = importlib.util.find_spec("playwright")
        base = os.path.dirname(espec.origin) if espec and espec.origin else ""
        return os.path.join(base, "driver", "package", ".local-browsers")
    if sys.platform.startswith("win"):
        return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "ms-playwright")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Caches/ms-playwright")
    return os.path.join(os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")), "ms-playwright")


def browsers_json() -> str:
    """La ruta de ``browsers.json`` del Playwright instalado, o ``""`` si no está (no importa el paquete)."""
    try:
        espec = importlib.util.find_spec("playwright")
    except (ImportError, ValueError):
        return ""
    if not espec or not espec.origin:
        return ""
    return os.path.join(os.path.dirname(espec.origin), "driver", "package", "browsers.json")


def revisiones_chromium(ruta: Optional[str] = None) -> Optional[Dict[str, str]]:
    """Las carpetas de Chromium que pide el Playwright instalado, como ``{"chromium": "chromium-1255", ...}``.

    ``None`` si ``browsers.json`` no está o no se entiende."""
    ruta = browsers_json() if ruta is None else ruta
    if not ruta:
        return None
    try:
        with open(ruta, encoding="utf-8") as f:
            navegadores = json.load(f)["browsers"]
        salida = {n["name"]: n["name"].replace("-", "_") + "-" + str(n["revision"])
                  for n in navegadores if n.get("name") in ("chromium", "chromium-headless-shell")}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None
    return salida or None


def chromium_instalado() -> bool:
    try:
        nombres = set(os.listdir(carpeta_navegadores()))
    except OSError:
        return False
    carpetas = revisiones_chromium()
    if carpetas is None:
        return any(n.startswith(("chromium-", "chromium_headless_shell-")) for n in nombres)
    return all(c in nombres for c in carpetas.values())


def stockfish_disponible() -> bool:
    return shutil.which("stockfish") is not None


def observabilidad() -> bool:
    """¿Está el extra ``[observabilidad]`` (el SDK de OpenTelemetry y su exportador OTLP)? Sin importarlo."""
    try:
        return all(importlib.util.find_spec(m) is not None
                   for m in ("opentelemetry.sdk", "opentelemetry.exporter.otlp.proto.http"))
    except (ImportError, ValueError):   # un paquete padre que falta
        return False


def estado(mundo: str) -> str:
    """``listo``, ``no_instalado``, ``falta_navegador`` (Snake sin Chromium) o ``sin_stockfish`` (ajedrez, lanzable)."""
    _, paquete = DEPENDENCIAS.get(mundo, (None, None))
    if paquete and not paquete_instalado(paquete):
        return "no_instalado"
    if mundo == "snake" and not chromium_instalado():
        return "falta_navegador"
    if mundo == "ajedrez" and not stockfish_disponible():
        return "sin_stockfish"
    return "listo"


def clase(mundo: str) -> Optional[Any]:
    """La clase del mundo, o ``None`` si sus dependencias no están (el ajedrez importa ``chess`` al cargarse)."""
    try:
        return cargar(mundo)
    except ImportError:
        return None


def ficha(mundo: str, extras: Optional[List[str]] = None) -> Dict[str, Any]:
    """La entrada de ``GET /api/v1/mundos`` de un mundo."""
    extra, _ = DEPENDENCIAS.get(mundo, (None, None))
    extras = extras_conocidos() if extras is None else extras
    c = clase(mundo)
    est = estado(mundo)
    return {
        "nombre": mundo,
        "estado": est,
        "lanzable": est in LANZABLES and c is not None,
        "extra": extra if extra in extras else None,
        "tiempo_real": bool(c.perfil.tiempo_real) if c is not None else None,
        "frecuencia_ms": float(c.perfil.frecuencia_ms) if c is not None else None,
        "ritmo_comodo_ms": ritmo_comodo(mundo) if c is not None else RITMO_COMODO_MS.get(mundo, RITMO_COMODO_DEFECTO),
        "estrella": mundo == ESTRELLA,
        "opciones": c.opciones() if c is not None else None,
    }


def mundos() -> List[Dict[str, Any]]:
    importlib.invalidate_caches()   # lo instalado durante la sesión se ve sin reiniciar el servidor
    extras = extras_conocidos()
    nombres = [m for m in ORDEN if m in MUNDOS] + [m for m in MUNDOS if m not in ORDEN]
    return [ficha(m, extras) for m in nombres]
