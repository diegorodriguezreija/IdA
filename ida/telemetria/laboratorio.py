"""Laboratorio (T5a, O7): memoria del directo, grabación desde el Vivero y grabaciones guardadas.

Todo sale del registro del latido v1 que ya publica el servidor (``Telemetria.publicar``): no se pide nada al motor y
nada de esto cambia la conducta de IdA (O3). Tres piezas:

- ``Directo``: los últimos ``LATIDOS_DIRECTO`` registros de la vida en curso, comprimidos en memoria del servidor, para
  abrir el directo en el Laboratorio sin grabar. Cada uno lleva su escena vigente (la escena solo viaja cuando cambia).
- ``Grabaciones``: las grabaciones de ``<datos>/grabaciones/<mundo>-<AAAAMMDD>-<HHMMSS>.jsonl.gz`` (el formato de
  ``ida/telemetria/grabacion.py``): listar, abrir por índice y por latido, descargar y borrar en dos pasos con testigo.
- ``Laboratorio``: un hilo propio que recibe los registros en orden, los guarda en el directo y, si se graba, los
  escribe en la grabación. Así el hilo de la vida solo encola: comprimir y escribir no alargan el latido.

**Por qué N = 2000.** Un registro completo de Crafter ocupa de media 62 KB en JSON y 10,3 KB comprimido con zlib de
nivel 1 (120 latidos, semilla 31, plazo lógico 40; máximo 12,1 KB): 2000 latidos son unos 21 MB de memoria. Es la vida
entera de casi todo lo que se lanza desde la antesala (300 latidos por defecto) y, a ritmo cómodo en Crafter (250 ms por
latido), algo más de 8 minutos de lo que se acaba de ver. Más latidos se graban.
"""

import gzip
import json
import os
import queue
import re
import secrets
import threading
import time
import zlib
from collections import OrderedDict, deque
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional, Tuple

from ida.telemetria.grabacion import FORMATO, Grabacion

LATIDOS_DIRECTO = 2000          # registros de la vida en curso en memoria del servidor (justificación arriba)
TESTIGO_S = 120.0               # vida de un testigo de borrado, como en la colección (sección 13.3)
GRABACIONES_EN_CACHE = 2        # grabaciones abiertas a la vez (su índice y sus líneas comprimidas)
ID_GRABACION = re.compile(r"^[a-z]+-\d{8}-\d{6}(-\d{1,3})?$")
EXTENSION = ".jsonl.gz"
# Hechos que marcan la línea de tiempo (los cambios de estrategia son muchos y técnicos: no van al índice).
HECHOS_INDICE = frozenset({"nace", "primera_vez", "aprende", "logro", "peligro", "sorpresa", "duda", "refuta", "muere",
                           "duerme", "despierta"})


class ErrorLab(Exception):
    """Un error del Laboratorio con su código de la API (``error.<codigo>`` en la interfaz)."""

    def __init__(self, http: int, codigo: str, mensaje: str) -> None:
        super().__init__(mensaje)
        self.http, self.codigo, self.mensaje = http, codigo, mensaje


def _json(datos: Any) -> str:
    return json.dumps(datos, ensure_ascii=False, separators=(",", ":"), default=str)


def entrada_indice(r: Dict[str, Any], n: int) -> Dict[str, Any]:
    """Lo que la línea de tiempo necesita de un registro: dónde está, sus hechos y si el tribunal o la guillotina
    tuvieron algo que decir."""
    entrada: Dict[str, Any] = {
        "n": n, "vida": r.get("vida"), "generacion": r.get("generacion"), "latido": r.get("latido"),
        "hechos": [h for h in (r.get("hechos") or []) if isinstance(h, dict) and h.get("tipo") in HECHOS_INDICE],
        "guillotina": bool((r.get("ritmo") or {}).get("guillotina")),
        "sistema": str((r.get("accion") or {}).get("sistema") or ""),
        "candidatos": len((r.get("tribunal") or {}).get("candidatos") or []),
        "dormido": bool((r.get("cuerpo") or {}).get("dormido")),
        "nivel": r.get("nivel"),
    }
    if r.get("cierre"):
        entrada["cierre"] = True
    return entrada


class Medias:
    """Media por clave de los tiempos de cada Componente (``tiempos_ms``) y de cada fase del latido (``fases``) sobre un
    conjunto de registros que puede perder los más antiguos (el directo)."""

    def __init__(self) -> None:
        self.tiempos: Dict[str, List[float]] = {}   # clave -> [suma, latidos en los que corrió]
        self.fases: Dict[str, List[float]] = {}
        self.registros = 0
        self.guillotinas = 0

    @staticmethod
    def _de(r: Dict[str, Any]) -> Tuple[Dict[str, float], Dict[str, float], bool]:
        tiempos = {str(k): float(v) for k, v in (r.get("tiempos_ms") or {}).items() if isinstance(v, (int, float))}
        fases: Dict[str, float] = {}
        for f in r.get("fases") or []:
            if isinstance(f, list) and len(f) == 3:
                fases[str(f[0])] = fases.get(str(f[0]), 0.0) + float(f[2]) - float(f[1])
        return tiempos, fases, bool((r.get("ritmo") or {}).get("guillotina"))

    def sumar(self, r: Dict[str, Any], signo: int = 1) -> Tuple[Dict[str, float], Dict[str, float], bool]:
        datos = self._de(r) if signo > 0 else (r["_t"], r["_f"], r["_g"])
        tiempos, fases, guillotina = datos
        for destino, origen in ((self.tiempos, tiempos), (self.fases, fases)):
            for k, v in origen.items():
                acc = destino.setdefault(k, [0.0, 0.0])
                acc[0] += signo * v
                acc[1] += signo
                if acc[1] <= 0:
                    del destino[k]
        self.registros += signo
        self.guillotinas += signo * int(guillotina)
        return datos

    def resumen(self) -> Dict[str, Any]:
        def medias(d: Dict[str, List[float]]) -> Dict[str, Any]:
            return {k: {"media": round(s / n, 4), "latidos": int(n)} for k, (s, n) in sorted(d.items()) if n > 0}
        return {"tiempos_medios": medias(self.tiempos), "fases_medias": medias(self.fases), "registros": self.registros,
                "guillotinas": self.guillotinas}


class Directo:
    """Los últimos ``maximo`` registros de la vida lanzada en curso, comprimidos, con su escena vigente."""

    def __init__(self, maximo: int = LATIDOS_DIRECTO) -> None:
        self.maximo = maximo
        self._cerrojo = threading.Lock()
        self._reiniciar(None, None)

    def _reiniciar(self, lanzamiento: Any, mundo: Optional[str]) -> None:
        self.lanzamiento = lanzamiento      # el id de la vida lanzada (``vida_actual()["id"]``)
        self.mundo = mundo
        self._entradas: Deque[Tuple[Dict[str, Any], bytes, Dict[str, Any]]] = deque()
        self._n = 0
        self._medias = Medias()
        self._escena: Optional[Dict[str, Any]] = None
        self._vida_escena: Any = None

    def reiniciar(self, lanzamiento: Any, mundo: Optional[str]) -> None:
        with self._cerrojo:
            self._reiniciar(lanzamiento, mundo)

    def anadir(self, registro: Dict[str, Any]) -> Dict[str, Any]:
        """Guarda un registro y lo devuelve con su escena vigente."""
        if registro.get("vida") != self._vida_escena:
            self._escena, self._vida_escena = None, registro.get("vida")
        if "escena" in registro:
            self._escena = registro["escena"]
        elif self._escena is not None:
            registro = dict(registro, escena=self._escena)
        comprimido = zlib.compress(_json(registro).encode("utf-8"), 1)
        with self._cerrojo:
            entrada = entrada_indice(registro, self._n)
            t, f, g = self._medias.sumar(registro)
            self._entradas.append((entrada, comprimido, {"_t": t, "_f": f, "_g": g}))
            self._n += 1
            while len(self._entradas) > self.maximo:
                _, _, viejo = self._entradas.popleft()
                self._medias.sumar(viejo, -1)
        return registro

    def indice(self, desde: int = 0) -> Dict[str, Any]:
        with self._cerrojo:
            entradas = [e for e, _, _ in self._entradas if e["n"] >= desde]
            primero = self._entradas[0][0]["n"] if self._entradas else self._n
            return {"lanzamiento": self.lanzamiento, "mundo": self.mundo, "maximo": self.maximo, "primero": primero,
                    "siguiente": self._n, "indice": entradas, **self._medias.resumen()}

    def registro(self, n: int) -> Dict[str, Any]:
        with self._cerrojo:
            if not self._entradas or not self._entradas[0][0]["n"] <= n < self._n:
                raise ErrorLab(404, "latido_fuera", f"el latido {n} no está en la memoria del directo (últimos {self.maximo})")
            _, comprimido, _ = self._entradas[n - self._entradas[0][0]["n"]]
        return dict(json.loads(zlib.decompress(comprimido)))


class _Abierta:
    """Una grabación leída entera: la cabecera, el índice, cada línea comprimida y dónde está su escena vigente."""

    def __init__(self, ruta: str) -> None:
        self.cabecera: Dict[str, Any] = {}
        self.lineas: List[bytes] = []
        self.escena_de: List[int] = []        # índice de la línea con la escena vigente (-1 si no hay)
        self.indice: List[Dict[str, Any]] = []
        self.medias = Medias()
        self.truncada = False
        try:
            with gzip.open(ruta, "rt", encoding="utf-8") as f:
                for texto in f:
                    if not texto.strip():
                        continue
                    datos = json.loads(texto)
                    if not self.cabecera:
                        if not isinstance(datos, dict) or datos.get("tipo") != "cabecera" or datos.get("formato") != FORMATO:
                            raise ErrorLab(400, "grabacion_invalida", "no es una grabación de IdA (falta la cabecera)")
                        self.cabecera = datos
                        continue
                    self._linea(texto, datos)
        except (OSError, EOFError, zlib.error, json.JSONDecodeError, UnicodeDecodeError) as e:
            if not self.cabecera:
                raise ErrorLab(400, "grabacion_invalida", f"no se puede leer: {e}") from None
            self.truncada = True          # una grabación cortada (p. ej. sin cerrar): vale hasta la última línea entera
        if not self.cabecera:
            raise ErrorLab(400, "grabacion_invalida", "grabación vacía")

    def _linea(self, texto: str, r: Dict[str, Any]) -> None:
        i = len(self.lineas)
        previa = self.escena_de[-1] if self.escena_de else -1
        if previa >= 0 and self.indice[-1]["vida"] != r.get("vida"):
            previa = -1
        self.escena_de.append(i if "escena" in r else previa)
        self.lineas.append(zlib.compress(texto.encode("utf-8"), 1))
        self.indice.append(entrada_indice(r, i))
        self.medias.sumar(r)

    def registro(self, n: int) -> Dict[str, Any]:
        if not 0 <= n < len(self.lineas):
            raise ErrorLab(404, "latido_fuera", f"la grabación tiene {len(self.lineas)} registros; no hay el {n}")
        r = dict(json.loads(zlib.decompress(self.lineas[n])))
        e = self.escena_de[n]
        if "escena" not in r and e >= 0:
            r["escena"] = json.loads(zlib.decompress(self.lineas[e]))["escena"]
        return r


class Grabaciones:
    """La carpeta ``<datos>/grabaciones``: listar, abrir, descargar y borrar en dos pasos."""

    def __init__(self, carpeta: str) -> None:
        self.carpeta = carpeta
        self._cerrojo = threading.Lock()
        self._testigos: Dict[str, Tuple[str, float]] = {}
        self._abiertas: "OrderedDict[Tuple[str, float, int], _Abierta]" = OrderedDict()
        self.en_curso: Optional[str] = None            # la que se está escribiendo (no se abre, descarga ni borra)
        self.registros: Dict[str, int] = {}            # registros escritos de las grabadas en esta sesión

    def ruta(self, id_: Any) -> str:
        if not isinstance(id_, str) or not ID_GRABACION.match(id_):
            raise ErrorLab(400, "id_invalido", f"identificador de grabación no válido: {id_!r}")
        return os.path.join(self.carpeta, id_ + EXTENSION)

    def existente(self, id_: Any) -> str:
        ruta = self.ruta(id_)
        if not os.path.isfile(ruta):
            raise ErrorLab(404, "grabacion_desconocida", f"no hay ninguna grabación {id_!r}")
        return ruta

    def nueva(self, mundo: str) -> Tuple[str, str]:
        """Un identificador y una ruta libres: ``<mundo>-<AAAAMMDD>-<HHMMSS>`` (con ``-2``, ``-3``... si ya existe)."""
        base = f"{mundo}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        os.makedirs(self.carpeta, exist_ok=True)
        for k in range(1, 1000):
            id_ = base if k == 1 else f"{base}-{k}"
            ruta = self.ruta(id_)
            if not os.path.exists(ruta):
                return id_, ruta
        raise ErrorLab(409, "grabacion_en_curso", "demasiadas grabaciones en el mismo segundo")   # pragma: no cover

    @staticmethod
    def _cabecera(ruta: str) -> Optional[Dict[str, Any]]:
        try:
            with gzip.open(ruta, "rt", encoding="utf-8") as f:
                primera = f.readline()
            cab = json.loads(primera)
        except (OSError, EOFError, zlib.error, json.JSONDecodeError, UnicodeDecodeError):
            return None
        return cab if isinstance(cab, dict) and cab.get("tipo") == "cabecera" and cab.get("formato") == FORMATO else None

    def resumen(self, id_: str) -> Dict[str, Any]:
        ruta = self.ruta(id_)
        en_curso = id_ == self.en_curso
        cab = self._cabecera(ruta) or {}
        est = os.stat(ruta)
        registros = self.registros.get(id_)
        for (rid, _, _), abierta in self._abiertas.items():
            if rid == ruta:
                registros = len(abierta.lineas)
        return {
            "id": id_, "mundo": cab.get("mundo") or id_.split("-")[0], "creada": cab.get("creada"), "nivel": cab.get("nivel"),
            "semilla": cab.get("semilla"), "commit": cab.get("commit"), "empieza_tras": cab.get("empieza_tras"),
            "bytes": int(est.st_size), "registros": registros, "en_curso": en_curso, "valida": bool(cab) or en_curso,
        }

    def listar(self) -> List[Dict[str, Any]]:
        if not os.path.isdir(self.carpeta):
            return []
        ids = [f[: -len(EXTENSION)] for f in os.listdir(self.carpeta) if f.endswith(EXTENSION)]
        lista = [self.resumen(i) for i in ids if ID_GRABACION.match(i)]
        return sorted(lista, key=lambda g: (str(g["creada"] or ""), g["id"]), reverse=True)

    def abrir(self, id_: str) -> _Abierta:
        if id_ == self.en_curso:
            raise ErrorLab(409, "grabacion_en_curso", "esta grabación aún se está escribiendo: termínala para abrirla")
        ruta = self.existente(id_)
        est = os.stat(ruta)
        clave = (ruta, est.st_mtime, est.st_size)
        with self._cerrojo:
            if clave in self._abiertas:
                self._abiertas.move_to_end(clave)
                return self._abiertas[clave]
        abierta = _Abierta(ruta)
        with self._cerrojo:
            self._abiertas[clave] = abierta
            for vieja in [k for k in self._abiertas if k[0] == ruta and k != clave]:
                del self._abiertas[vieja]
            while len(self._abiertas) > GRABACIONES_EN_CACHE:
                self._abiertas.popitem(last=False)
        return abierta

    def indice(self, id_: str) -> Dict[str, Any]:
        a = self.abrir(id_)
        return {"grabacion": self.resumen(id_), "cabecera": a.cabecera, "truncada": a.truncada, "indice": a.indice,
                **a.medias.resumen()}

    def pedir_borrado(self, id_: str) -> Dict[str, Any]:
        """Primer paso: no borra nada. Un testigo de un solo uso (``TESTIGO_S`` s) y lo que se borraría."""
        self.existente(id_)
        if id_ == self.en_curso:
            raise ErrorLab(409, "grabacion_en_curso", "no se borra una grabación que aún se está escribiendo")
        testigo = secrets.token_urlsafe(18)
        ahora = time.monotonic()
        with self._cerrojo:
            self._testigos = {t: v for t, v in self._testigos.items() if v[1] > ahora}
            self._testigos[testigo] = (id_, ahora + TESTIGO_S)
        return {"testigo": testigo, "caduca_s": TESTIGO_S, "grabacion": self.resumen(id_)}

    def confirmar_borrado(self, id_: str, testigo: Any) -> Dict[str, Any]:
        """Segundo paso: borra la grabación, solo con el testigo que dio ``pedir_borrado`` para ella."""
        ruta = self.existente(id_)
        with self._cerrojo:
            dato = self._testigos.pop(testigo, None) if isinstance(testigo, str) else None
            if dato is None or dato[0] != id_ or dato[1] <= time.monotonic():
                if dato is not None and dato[0] != id_ and dato[1] > time.monotonic():
                    self._testigos[testigo] = dato   # era de otra grabación: sigue valiendo para la suya
                raise ErrorLab(400, "testigo_invalido", "falta el testigo, ha caducado, ya se usó o es de otra grabación: no se borra nada")
            for clave in [k for k in self._abiertas if k[0] == ruta]:
                del self._abiertas[clave]
        os.remove(ruta)
        self.registros.pop(id_, None)
        return {"borrada": id_}


class _EnCurso:
    def __init__(self, id_: str, ruta: str, cabecera: Dict[str, Any]) -> None:
        self.id, self.ruta, self.cabecera = id_, ruta, cabecera
        self.escritor = Grabacion(ruta, cabecera)
        self.activa = False          # el hilo la activa al llegar a su marca: graba desde el latido siguiente
        self.vida_escena: Any = None
        self.primero: Optional[Dict[str, Any]] = None

    def resumen(self) -> Dict[str, Any]:
        return {"id": self.id, "registros": self.escritor.registros, "nivel": self.cabecera.get("nivel"),
                "empieza_tras": self.cabecera.get("empieza_tras"), "primero": self.primero}


class Laboratorio:
    """El hilo que guarda el directo y escribe la grabación, en el orden en que se publicaron los registros."""

    def __init__(self, datos: str, maximo: int = LATIDOS_DIRECTO) -> None:
        self.directo = Directo(maximo)
        self.grabaciones = Grabaciones(os.path.join(datos, "grabaciones"))
        self._cola: "queue.Queue[Tuple[Any, ...]]" = queue.Queue()
        self._grabacion: Optional[_EnCurso] = None   # la pedida (la API la ve en cuanto se pide)
        self._cerrojo = threading.Lock()
        self._hilo = threading.Thread(target=self._trabajar, name="ida-laboratorio", daemon=True)
        self._hilo.start()

    # --- desde el servidor -----------------------------------------------------------------------------------------
    def poner(self, registro: Dict[str, Any]) -> None:
        """Un registro del latido v1 recién publicado. Solo encola: no bloquea la vida."""
        self._cola.put(("registro", registro))

    def nueva_vida(self, lanzamiento: Any, mundo: str) -> None:
        self._cola.put(("reiniciar", lanzamiento, mundo))

    def grabando(self) -> Optional[Dict[str, Any]]:
        g = self._grabacion
        return None if g is None else g.resumen()

    def empezar(self, mundo: str, cabecera: Dict[str, Any]) -> Dict[str, Any]:
        """Empieza a grabar: la grabación recibe los registros que se publiquen desde ahora (el latido siguiente)."""
        with self._cerrojo:
            if self._grabacion is not None:
                raise ErrorLab(409, "grabacion_en_curso", f"ya se está grabando ({self._grabacion.id})")
            id_, ruta = self.grabaciones.nueva(mundo)
            g = _EnCurso(id_, ruta, cabecera)
            self._grabacion = g
            self.grabaciones.en_curso = id_
        self._cola.put(("activar", g))
        return g.resumen()

    def terminar(self, esperar: bool = True, limite: float = 30.0) -> Optional[Dict[str, Any]]:
        """Termina la grabación en curso (después de escribir lo que ya estaba en la cola). ``None`` si no había."""
        with self._cerrojo:
            g = self._grabacion
            self._grabacion = None
        if g is None:
            return None
        hecho = threading.Event()
        self._cola.put(("terminar", g, hecho))
        if esperar:
            hecho.wait(limite)
        return g.resumen()

    def esperar_cola(self, limite: float = 10.0) -> None:
        """Espera a que el hilo haya procesado todo lo encolado hasta ahora (pruebas y fin de vida)."""
        hecho = threading.Event()
        self._cola.put(("marca", hecho))
        hecho.wait(limite)

    def cerrar(self) -> None:
        self.terminar(esperar=True, limite=10.0)
        self._cola.put(("salir",))
        self._hilo.join(timeout=5.0)

    # --- el hilo -----------------------------------------------------------------------------------------------------
    def _trabajar(self) -> None:
        activa: Optional[_EnCurso] = None
        while True:
            orden = self._cola.get()
            tipo = orden[0]
            try:
                if tipo == "registro":
                    r = orden[1]
                    con_escena = self.directo.anadir(r)
                    if activa is not None:
                        self._escribir(activa, r, con_escena)
                elif tipo == "reiniciar":
                    self.directo.reiniciar(orden[1], orden[2])
                elif tipo == "activar":
                    activa = orden[1]
                    activa.activa = True
                elif tipo == "terminar":
                    g, hecho = orden[1], orden[2]
                    g.escritor.cerrar()
                    self.grabaciones.registros[g.id] = g.escritor.registros
                    if self.grabaciones.en_curso == g.id:
                        self.grabaciones.en_curso = None
                    if activa is g:
                        activa = None
                    hecho.set()
                elif tipo == "marca":
                    orden[1].set()
                elif tipo == "salir":
                    return
            except Exception as e:   # pragma: no cover - el hilo no se cae por un registro
                print(f"[laboratorio] {tipo}: {e}")

    @staticmethod
    def _escribir(g: _EnCurso, r: Dict[str, Any], con_escena: Dict[str, Any]) -> None:
        """Escribe un registro. El primero de la grabación y el primero de cada vida llevan siempre su escena vigente
        (``con_escena``, el registro con la escena que guarda el directo): la grabación puede empezar a media vida, cuando
        la escena no ha cambiado, y el lector la reconstruye desde la última que llegó en la vida."""
        vida = r.get("vida")
        if g.escritor.registros == 0 or vida != g.vida_escena:
            g.vida_escena = vida
            r = con_escena
            if g.primero is None:
                g.primero = {"vida": vida, "latido": r.get("latido")}
        g.escritor.escribir(r)
