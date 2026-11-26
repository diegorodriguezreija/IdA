"""Grabación de vidas (O7): ``.jsonl.gz`` con una cabecera y un registro del latido por línea.

La primera línea es la cabecera (``"tipo": "cabecera"``): formato, versión del esquema, commit (si git lo da sin red ni
credenciales), mundo, opciones, semilla, arquetipo inicial, latidos, plazo lógico, nivel y fecha. Cada línea siguiente
es un registro del latido v1 (``ida/telemetria/esquema.py``), en orden; con varias generaciones, las vidas van seguidas
y se distinguen por ``vida``.

El gzip se escribe sin nombre ni fecha en su cabecera (``mtime=0``): dos grabaciones de la misma vida con plazo lógico
solo difieren en los campos de tiempo (``esquema.CAMPOS_TIEMPO`` y ``creada`` de la cabecera).
"""

import gzip
import io
import json
import os
import subprocess
import time
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

from ida.telemetria.esquema import CAMPOS_TIEMPO, VERSION

FORMATO = "ida-grabacion"
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def commit_actual(raiz: str = RAIZ) -> Optional[str]:
    """El commit del árbol (``git rev-parse HEAD``, local), con ``+cambios`` si hay cambios sin confirmar; ``None`` si
    git no está o no responde. No usa la red ni credenciales."""
    entorno = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0")
    try:
        cabeza = subprocess.run(["git", "rev-parse", "HEAD"], cwd=raiz, capture_output=True, text=True, timeout=5,
                                env=entorno, check=True).stdout.strip()
        cambios = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=raiz, capture_output=True,
                                 text=True, timeout=5, env=entorno, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return f"{cabeza}+cambios" if cambios else cabeza


def cabecera(mundo: str, nivel: str, semilla: int, latidos: int, generaciones: int = 1, opciones: Optional[Dict[str, Any]] = None,
             arquetipo: Optional[Dict[str, Any]] = None, plazo_logico: Optional[float] = None, sin_experiencia: bool = False,
             commit: Optional[str] = None) -> Dict[str, Any]:
    return {
        "tipo": "cabecera", "formato": FORMATO, "esquema": VERSION, "commit": commit, "mundo": mundo,
        "opciones": dict(opciones or {}), "semilla": semilla, "arquetipo": arquetipo, "latidos": latidos,
        "generaciones": generaciones, "plazo_logico": plazo_logico, "nivel": nivel, "sin_experiencia": sin_experiencia,
        "creada": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def _linea(datos: Dict[str, Any]) -> str:
    return json.dumps(datos, ensure_ascii=False, separators=(",", ":"), default=str) + "\n"


class Grabacion:
    """Escribe una grabación. Uso: ``with Grabacion(ruta, cabecera) as g: g.escribir(registro)``."""

    def __init__(self, ruta: str, cab: Dict[str, Any]):
        carpeta = os.path.dirname(os.path.abspath(ruta))
        os.makedirs(carpeta, exist_ok=True)
        self.ruta = ruta
        self._bruto = open(ruta, "wb")
        self._gz = gzip.GzipFile(filename="", mode="wb", fileobj=self._bruto, mtime=0)
        self._texto = io.TextIOWrapper(self._gz, encoding="utf-8", newline="\n")
        self.registros = 0
        self._texto.write(_linea(cab))

    def escribir(self, registro: Dict[str, Any]) -> None:
        self._texto.write(_linea(registro))
        self.registros += 1

    def cerrar(self) -> None:
        if not self._texto.closed:
            self._texto.close()      # cierra también el gzip
            self._bruto.close()

    def __enter__(self) -> "Grabacion":
        return self

    def __exit__(self, *_: Any) -> None:
        self.cerrar()


def iterar(ruta: str) -> Iterator[Dict[str, Any]]:
    """Las líneas de una grabación, ya decodificadas: la cabecera y después cada registro, en orden."""
    with gzip.open(ruta, "rt", encoding="utf-8") as f:
        for linea in f:
            if linea.strip():
                yield json.loads(linea)


def leer(ruta: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """La cabecera y la secuencia de registros de una grabación."""
    lineas = iterar(ruta)
    cab = next(lineas, None)
    if not isinstance(cab, dict) or cab.get("tipo") != "cabecera" or cab.get("formato") != FORMATO:
        raise ValueError(f"{ruta}: no es una grabación de IdA (falta la cabecera)")
    return cab, list(lineas)


def escenas(registros: Iterable[Dict[str, Any]]) -> Iterator[Optional[Dict[str, Any]]]:
    """La escena de cada registro, reconstruida (O6): el registro solo la lleva cuando cambia, así que la de un latido es
    la última que llegó en su vida (``None`` si el mundo no da escena)."""
    actual: Optional[Dict[str, Any]] = None
    vida = None
    for r in registros:
        if r.get("vida") != vida:
            vida, actual = r.get("vida"), None
        if "escena" in r:
            actual = r["escena"]
        yield actual


def sin_tiempos(datos: Dict[str, Any]) -> Dict[str, Any]:
    """Copia de un registro (o de la cabecera) sin los campos de tiempo, para comparar grabaciones."""
    copia = json.loads(json.dumps(datos))
    copia.pop("creada", None)
    for campo in CAMPOS_TIEMPO:
        partes = campo.split(".")
        d = copia
        for p in partes[:-1]:
            d = d.get(p, {}) if isinstance(d, dict) else {}
        if isinstance(d, dict):
            d.pop(partes[-1], None)
    return copia


def comparar(ruta_a: str, ruta_b: str) -> Optional[str]:
    """``None`` si las dos grabaciones son iguales línea a línea salvo los campos de tiempo; si no, la primera diferencia."""
    a, b = iterar(ruta_a), iterar(ruta_b)
    i = 0
    while True:
        la, lb = next(a, None), next(b, None)
        if la is None and lb is None:
            return None
        if la is None or lb is None:
            return f"línea {i}: una grabación termina antes"
        if sin_tiempos(la) != sin_tiempos(lb):
            return f"línea {i}: distinta (latido {la.get('latido', '-')})"
        i += 1
