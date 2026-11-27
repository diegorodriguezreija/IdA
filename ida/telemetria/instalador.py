"""Instalación de mundos desde la antesala (O17): ``pip install -e ".[<extra>]"`` con el Python del propio entorno.

Las órdenes son fijas: el extra sale de la lista cerrada de ``pyproject.toml`` (``catalogo.extras_conocidos``) y del
mundo pedido (``catalogo.DEPENDENCIAS``), nunca de texto del cliente. Para Snake se añade
``python -m playwright install chromium``. Se ejecutan desde la raíz del proyecto, una instalación a la vez, en un hilo;
cada línea de salida se guarda y se avisa a quien la sigue por SSE (``GET /api/v1/instalaciones/{id}``).

En una instalación que no es editable (``pip install .``, sin ``pyproject.toml`` al lado; T6a) no hay proyecto que
reinstalar: se instalan los requisitos del extra que dicen los metadatos del paquete instalado
(``catalogo.requisitos_del_extra``), igual de fijos.

``lanzar`` (por defecto ``subprocess.Popen``) se puede sustituir en las pruebas por un proceso simulado.
"""

import itertools
import os
import subprocess
import sys
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from ida.telemetria import catalogo

ESTADOS = ("en_curso", "ok", "error")


class ErrorInstalacion(Exception):
    def __init__(self, codigo: str, mensaje: str, http: int = 400) -> None:
        super().__init__(mensaje)
        self.codigo, self.mensaje, self.http = codigo, mensaje, http


def _popen(orden: List[str], cwd: str) -> Any:
    return subprocess.Popen(orden, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                            text=True, encoding="utf-8", errors="replace", bufsize=1)


def ordenes(mundo: str, extra: str, editable: bool = True) -> List[List[str]]:
    """Las órdenes de instalación de un mundo (lista de argumentos: sin intérprete de órdenes)."""
    if editable:
        salida = [[sys.executable, "-m", "pip", "install", "-e", f".[{extra}]"]]
    else:
        salida = [[sys.executable, "-m", "pip", "install", *catalogo.requisitos_del_extra(extra)]]
    if mundo == "snake":
        salida.append([sys.executable, "-m", "playwright", "install", "chromium"])
    return salida


class Instalacion:
    def __init__(self, ident: str, mundo: str, extra: str, ordenes: List[List[str]]) -> None:
        self.id, self.mundo, self.extra, self.ordenes = ident, mundo, extra, ordenes
        self.lineas: List[str] = []
        self.estado = "en_curso"
        self.codigo: Optional[int] = None
        self.creada = time.time()
        self.cond = threading.Condition()

    def anotar(self, linea: str) -> None:
        with self.cond:
            self.lineas.append(linea)
            self.cond.notify_all()

    def terminar(self, estado: str, codigo: Optional[int]) -> None:
        with self.cond:
            self.estado, self.codigo = estado, codigo
            self.cond.notify_all()

    def resumen(self) -> Dict[str, Any]:
        return {"id": self.id, "mundo": self.mundo, "extra": self.extra, "estado": self.estado, "codigo": self.codigo,
                "lineas": len(self.lineas), "url": f"/api/v1/instalaciones/{self.id}"}


class Instalador:
    def __init__(self, lanzar: Optional[Callable[[List[str], str], Any]] = None, raiz: str = catalogo.RAIZ) -> None:
        self.lanzar = lanzar
        self.raiz = raiz
        self.instalaciones: Dict[str, Instalacion] = {}
        self._cerrojo = threading.Lock()
        self._contador = itertools.count(1)

    def en_curso(self) -> Optional[Instalacion]:
        return next((i for i in self.instalaciones.values() if i.estado == "en_curso"), None)

    def ultima_de(self, mundo: str) -> Optional[Instalacion]:
        delmundo = [i for i in self.instalaciones.values() if i.mundo == mundo]
        return delmundo[-1] if delmundo else None

    def instalar(self, mundo: str) -> Instalacion:
        """Empieza a instalar ``mundo``. ``ErrorInstalacion`` si el mundo no existe, no tiene un extra de la lista o ya
        hay una instalación en curso."""
        if mundo not in catalogo.DEPENDENCIAS:
            raise ErrorInstalacion("mundo_desconocido", f"mundo desconocido: {mundo!r}", 404)
        extra, _ = catalogo.DEPENDENCIAS[mundo]
        conocidos = catalogo.extras_conocidos(self._pyproject())
        if extra is None:
            raise ErrorInstalacion("sin_extra", f"{mundo} no necesita instalar nada")
        editable = catalogo.editable(self.raiz)
        if extra not in conocidos or (not editable and not catalogo.requisitos_del_extra(extra)):
            raise ErrorInstalacion("extra_desconocido", f"el extra {extra!r} no está en pyproject.toml (conocidos: {', '.join(conocidos)})")
        with self._cerrojo:
            if self.en_curso() is not None:
                raise ErrorInstalacion("instalacion_en_curso", "ya hay una instalación en curso", 409)
            inst = Instalacion(f"i{next(self._contador)}", mundo, extra, ordenes(mundo, extra, editable))
            self.instalaciones[inst.id] = inst
        threading.Thread(target=self._correr, args=(inst,), daemon=True).start()
        return inst

    def _pyproject(self) -> str:
        return os.path.join(self.raiz, "pyproject.toml")

    def _correr(self, inst: Instalacion) -> None:
        lanzar = self.lanzar or _popen
        codigo: Optional[int] = 0
        try:
            for orden in inst.ordenes:
                inst.anotar("$ " + " ".join(["python" if i == 0 else a for i, a in enumerate(orden)]))
                proceso = lanzar(orden, self.raiz)
                for linea in proceso.stdout:
                    inst.anotar(str(linea).rstrip("\r\n"))
                codigo = proceso.wait()
                if codigo != 0:
                    break
        except Exception as e:   # el error llega al cliente por la SSE, no tumba el servidor
            inst.anotar(f"[error] {e}")
            codigo = None
        inst.terminar("ok" if codigo == 0 else "error", codigo)
