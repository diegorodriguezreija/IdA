"""Vivero: el compañero de cada mundo, la colección y las fichas de individuo v1 (O9, O10; sección 13 del diseño).

En disco (``raiz`` es ``datos/`` del proyecto o lo que se dé con ``--datos``)::

    <raiz>/<mundo>/linaje.json, memoria.db*     el compañero: la estirpe viva de ese mundo
    <raiz>/vivero/indice.json                   índice de la colección (se rehace si falta o no cuadra)
    <raiz>/vivero/fichas/<id>.json              fichas v1
    <raiz>/vivero/estirpes/<id>/                estirpes archivadas (sus ficheros y estirpe.json)

**Nada se borra ni se sobrescribe sin confirmación.** Las únicas funciones que quitan algo del disco son:

- ``archivar`` (y quien la llama: ``adoptar``): copia los ficheros de la estirpe al archivo, comprueba la copia y solo
  entonces quita los originales;
- ``adoptar`` de una estirpe archivada: la devuelve a su mundo (mueve, no borra);
- ``confirmar_borrado``: borra una ficha o una estirpe archivada, solo con el testigo que dio ``pedir_borrado``.

Todo lo que se escribe es atómico (temporal y ``os.replace``) y nunca encima de un fichero existente de la colección.
"""

import json
import os
import re
import secrets
import shutil
import threading
import time
from dataclasses import fields
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ida.historico import calcular_fitness
from ida.mundos import MUNDOS
from ida.nucleo.linaje import RASGOS_CARACTER, Arquetipo

TIPO_FICHA = "ida_ficha"
VERSION_FICHA = 1
FICHEROS_ESTIRPE = ("linaje.json", "memoria.db", "memoria.db-wal", "memoria.db-shm")
ID_VALIDO = re.compile(r"^[a-z]+-\d{8}-\d{6}-[0-9a-f]{6}$")
NOMBRE_MAX = 60
TESTIGO_S = 120.0
CAMPOS_ARQUETIPO = tuple(f.name for f in fields(Arquetipo))


class ErrorVivero(Exception):
    """Un error del Vivero con su código de la API (``error.<codigo>`` en la interfaz)."""

    def __init__(self, http: int, codigo: str, mensaje: str) -> None:
        super().__init__(mensaje)
        self.http, self.codigo, self.mensaje = http, codigo, mensaje


# --- utilidades de disco -----------------------------------------------------------------------------------------------
def _escribir_json(ruta: str, datos: Any, nuevo: bool = False) -> None:
    """Escritura atómica. Con ``nuevo``, falla si el fichero ya existe (nunca se pisa una ficha)."""
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    if nuevo and os.path.exists(ruta):
        raise FileExistsError(ruta)
    tmp = f"{ruta}.{secrets.token_hex(4)}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    if nuevo and os.path.exists(ruta):   # pragma: no cover - carrera improbable
        os.remove(tmp)
        raise FileExistsError(ruta)
    os.replace(tmp, ruta)


def _leer_json(ruta: str, intentos: int = 3) -> Optional[Any]:
    """Lee un JSON; ``None`` si no existe. Reintenta un poco: el ejecutor puede estar escribiendo el linaje."""
    for i in range(intentos):
        if not os.path.exists(ruta):
            return None
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            if i == intentos - 1:
                raise
            time.sleep(0.05)
    return None   # pragma: no cover


def ahora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def nuevo_id(mundo: str) -> str:
    return f"{mundo}-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}"


def validar_id(id_: Any) -> str:
    if not isinstance(id_, str) or not ID_VALIDO.match(id_):
        raise ErrorVivero(400, "id_invalido", f"identificador no válido: {id_!r}")
    return id_


def validar_nombre(nombre: Any) -> str:
    if not isinstance(nombre, str) or not nombre.strip() or len(nombre.strip()) > NOMBRE_MAX or any(c in nombre for c in "\r\n\t"):
        raise ErrorVivero(400, "nombre_invalido", f"el nombre debe tener entre 1 y {NOMBRE_MAX} caracteres, sin saltos de línea")
    return nombre.strip()


def _commit() -> Optional[str]:
    from ida.telemetria.grabacion import commit_actual   # git rev-parse HEAD en local, sin red
    try:
        return commit_actual()
    except Exception:   # pragma: no cover
        return None


# --- vidas, Score y arquetipos -------------------------------------------------------------------------------------------
def _num(x: Any) -> Optional[float]:
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def vida_de_generacion(mundo: str, g: Dict[str, Any]) -> Dict[str, Any]:
    """Una vida de la ficha a partir de una generación del linaje (o de una ficha antigua)."""
    punt: Dict[str, Any] = g["puntuacion"] if isinstance(g.get("puntuacion"), dict) else {}
    arq: Dict[str, Any] = g["arquetipo"] if isinstance(g.get("arquetipo"), dict) else {}
    score = _num(g.get("score"))
    if score is None:
        score = _num(g.get("fitness"))
    if score is None:
        score = round(calcular_fitness(mundo, {"puntuacion": punt, "latidos": g.get("latidos", 0)}), 2)
    logros = g.get("logros") if isinstance(g.get("logros"), list) else punt.get("logros")
    generacion = g.get("generacion", arq.get("generacion", 1))
    return {
        "individuo": str(g.get("individuo") or f"{mundo.capitalize()}_G{generacion}"),
        "generacion": int(generacion) if isinstance(generacion, (int, float)) else 1,
        "latidos": int(g["latidos"]) if _num(g.get("latidos")) is not None else None,
        "score": score,
        "causa_muerte": g.get("causa_muerte") if isinstance(g.get("causa_muerte"), str) else None,
        "vivo": g.get("vivo") if isinstance(g.get("vivo"), bool) else None,
        "logros": [str(x) for x in logros] if isinstance(logros, list) else [],
        "puntuacion": punt,
        **({"arquetipo": {r: float(arq[r]) for r in RASGOS_CARACTER if _num(arq.get(r)) is not None}} if arq else {}),
    }


def completar_arquetipo(arq: Dict[str, Any], mundo: str, generacion: int) -> Dict[str, Any]:
    """El arquetipo con exactamente los campos de ``Arquetipo`` (se completan los que falten), rasgos en [0, 1]."""
    base = Arquetipo(linaje=mundo.capitalize(), generacion=int(generacion))
    salida: Dict[str, Any] = {}
    for campo in CAMPOS_ARQUETIPO:
        v = arq.get(campo, getattr(base, campo))
        if campo in RASGOS_CARACTER:
            n = _num(v)
            if n is None or not 0.0 <= n <= 1.0:
                raise ErrorVivero(400, "ficha_invalida", f"carácter de la ficha: {campo} = {v!r} (se esperaba un número en [0, 1])")
            v = round(n, 3)
        elif campo == "generacion":
            v = int(v) if _num(v) is not None and int(v) >= 1 else int(generacion)
        elif campo in ("nombre", "linaje"):
            v = str(v) if isinstance(v, str) and v else getattr(base, campo)
        elif campo == "padre":
            v = str(v) if isinstance(v, str) and v else None
        salida[campo] = v
    return salida


def _orden_generacion(gens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def clave(g: Dict[str, Any]) -> Tuple[int, str]:
        arq = g.get("arquetipo") or {}
        n = g.get("generacion", arq.get("generacion", 0) if isinstance(arq, dict) else 0)
        return (int(n) if isinstance(n, (int, float)) else 0, str(g.get("individuo", "")))
    return sorted(gens, key=clave)


def _mejor(vidas: List[Dict[str, Any]]) -> Optional[float]:
    scores = [v["score"] for v in vidas if _num(v.get("score")) is not None]
    return max(scores) if scores else None


# --- el compañero ----------------------------------------------------------------------------------------------------------
class Vivero:
    """La colección y los compañeros bajo ``raiz``. Seguro entre hilos (un cerrojo para todo lo que escribe)."""

    def __init__(self, raiz: str) -> None:
        self.raiz = os.path.abspath(raiz)
        self.dir = os.path.join(self.raiz, "vivero")
        self.dir_fichas = os.path.join(self.dir, "fichas")
        self.dir_estirpes = os.path.join(self.dir, "estirpes")
        self._cerrojo = threading.RLock()
        self._testigos: Dict[str, Tuple[str, float]] = {}   # testigo -> (id, caduca)

    # --- rutas ---------------------------------------------------------------------------------------------------------
    def dir_mundo(self, mundo: str) -> str:
        if mundo not in MUNDOS:
            raise ErrorVivero(404, "mundo_desconocido", f"mundo desconocido: {mundo!r}")
        return os.path.join(self.raiz, mundo)

    def _ruta_ficha(self, id_: str) -> str:
        return os.path.join(self.dir_fichas, f"{validar_id(id_)}.json")

    def _ruta_estirpe(self, id_: str) -> str:
        return os.path.join(self.dir_estirpes, validar_id(id_))

    # --- compañero -----------------------------------------------------------------------------------------------------
    def linaje(self, mundo: str) -> Optional[Dict[str, Any]]:
        datos = _leer_json(os.path.join(self.dir_mundo(mundo), "linaje.json"))
        return datos if isinstance(datos, dict) else None

    @staticmethod
    def _resumen_linaje(mundo: str, datos: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        gens = _orden_generacion([g for g in (datos or {}).get("generaciones", []) if isinstance(g, dict)])
        vidas = [vida_de_generacion(mundo, g) for g in gens]
        arq = (datos or {}).get("arquetipo") or {}
        ultimo = vidas[-1] if vidas else None
        return {
            "mundo": mundo,
            "existe": bool(datos) and (bool(vidas) or bool(arq)),
            "individuo": ultimo["individuo"] if ultimo else (f"{arq.get('linaje', mundo.capitalize())}_G{arq.get('generacion', 1)}" if arq else None),
            "generacion": int(arq.get("generacion", ultimo["generacion"] if ultimo else 0)) if (arq or ultimo) else 0,
            "generaciones": len(vidas),
            "mejor_score": _mejor(vidas),
            "ultimo": ultimo,
            "arquetipo": {r: arq.get(r) for r in RASGOS_CARACTER} if arq else None,
            "nombre": (datos or {}).get("nombre") or (ultimo["individuo"] if ultimo else None),
            "adoptada_de": (datos or {}).get("adoptada_de"),
            "linaje": vidas,
        }

    def companero(self, mundo: str, con_linaje: bool = True) -> Dict[str, Any]:
        r = self._resumen_linaje(mundo, self.linaje(mundo))
        if not con_linaje:
            r.pop("linaje")
        return r

    def companeros(self) -> List[Dict[str, Any]]:
        return [self.companero(m, con_linaje=False) for m in MUNDOS]

    # --- fichas ----------------------------------------------------------------------------------------------------------
    def ficha_del_companero(self, mundo: str, nombre: Optional[str] = None) -> Dict[str, Any]:
        """La ficha v1 del compañero: su último individuo con el historial de la estirpe (sin guardarla)."""
        datos = self.linaje(mundo)
        r = self._resumen_linaje(mundo, datos)
        if not r["existe"] or datos is None:
            raise ErrorVivero(404, "sin_companero", f"{mundo}: no hay compañero (ninguna vida terminada)")
        arq = completar_arquetipo(datos.get("arquetipo") or {}, mundo, r["generacion"] or 1)
        return {
            "tipo": TIPO_FICHA, "version": VERSION_FICHA, "id": None,
            "nombre": validar_nombre(nombre) if nombre is not None else (r["nombre"] or r["individuo"]),
            "mundo": mundo, "individuo": r["individuo"], "generacion": int(arq["generacion"]),
            "arquetipo": arq, "legado": datos.get("legado") or {}, "vidas": r["linaje"],
            "mejor_score": r["mejor_score"], "fecha": ahora_iso(), "commit": _commit(), "origen": "companero", "avisos": [],
        }

    def guardar(self, mundo: str, nombre: Optional[str] = None) -> Dict[str, Any]:
        """Guarda el compañero como ficha nueva en la colección (nunca encima de otra)."""
        ficha = self.ficha_del_companero(mundo, nombre)
        return self._guardar_ficha(ficha)

    def _guardar_ficha(self, ficha: Dict[str, Any]) -> Dict[str, Any]:
        with self._cerrojo:
            for _ in range(5):
                ficha["id"] = nuevo_id(ficha["mundo"])
                try:
                    _escribir_json(self._ruta_ficha(ficha["id"]), ficha, nuevo=True)
                    break
                except FileExistsError:   # pragma: no cover - otro id
                    continue
            self._rehacer_indice()
        return ficha

    def importar(self, doc: Any) -> Dict[str, Any]:
        """Convierte una ficha (v1 o antigua) y la guarda como ficha nueva. Devuelve la ficha (con sus ``avisos``)."""
        return self._guardar_ficha(convertir(doc))

    # --- estirpes archivadas ------------------------------------------------------------------------------------------------
    def archivar(self, mundo: str, motivo: str = "archivar") -> Optional[Dict[str, Any]]:
        """Archiva el compañero de ``mundo`` en la colección. ``None`` si no había. Copia, comprueba y solo entonces quita
        los originales (nunca ``rmtree``). El bioma de archivos y cualquier otra cosa del mundo se quedan donde están."""
        with self._cerrojo:
            origen = self.dir_mundo(mundo)
            presentes = [f for f in FICHEROS_ESTIRPE if os.path.isfile(os.path.join(origen, f))]
            if not presentes:
                return None
            datos = self.linaje(mundo) if "linaje.json" in presentes else None
            r = self._resumen_linaje(mundo, datos)
            id_ = nuevo_id(mundo)
            destino = self._ruta_estirpe(id_)
            while os.path.exists(destino):   # pragma: no cover
                id_ = nuevo_id(mundo)
                destino = self._ruta_estirpe(id_)
            os.makedirs(destino)
            meta = {"id": id_, "mundo": mundo, "nombre": r["nombre"] or r["individuo"] or mundo.capitalize(),
                    "archivada": ahora_iso(), "motivo": motivo, "generaciones": r["generaciones"],
                    "generacion": r["generacion"], "mejor_score": r["mejor_score"], "ultimo": r["ultimo"],
                    "ficheros": presentes, "incompleta": True}
            _escribir_json(os.path.join(destino, "estirpe.json"), meta, nuevo=True)
            for f in presentes:
                a, b = os.path.join(origen, f), os.path.join(destino, f)
                shutil.copy2(a, b)
                if os.path.getsize(a) != os.path.getsize(b):   # pragma: no cover - la copia no cuadra: no se quita nada
                    raise ErrorVivero(500, "error_interno", f"la copia de {f} no coincide; no se ha quitado nada")
            meta["incompleta"] = False
            _escribir_json(os.path.join(destino, "estirpe.json"), meta)
            for f in presentes:          # la copia está completa y comprobada: ahora sí se quitan los originales
                os.remove(os.path.join(origen, f))
            self._rehacer_indice()
            return meta

    @staticmethod
    def _ficha(ruta: str) -> Dict[str, Any]:
        f = _leer_json(ruta)
        if not isinstance(f, dict):
            raise ErrorVivero(500, "error_interno", f"ficha ilegible: {os.path.basename(ruta)}")
        return f

    def _meta_estirpe(self, id_: str) -> Optional[Dict[str, Any]]:
        meta = _leer_json(os.path.join(self._ruta_estirpe(id_), "estirpe.json"))
        return meta if isinstance(meta, dict) else None

    def _linaje_archivado(self, id_: str) -> Optional[Dict[str, Any]]:
        datos = _leer_json(os.path.join(self._ruta_estirpe(id_), "linaje.json"))
        return datos if isinstance(datos, dict) else None

    def ficha_de_estirpe(self, id_: str) -> Dict[str, Any]:
        """La ficha v1 del último individuo de una estirpe archivada (para exportarla)."""
        meta = self._meta_estirpe(id_)
        datos = self._linaje_archivado(id_)
        if meta is None or datos is None:
            raise ErrorVivero(404, "elemento_desconocido", f"estirpe desconocida o sin linaje: {id_}")
        mundo = meta["mundo"]
        r = self._resumen_linaje(mundo, datos)
        arq = completar_arquetipo(datos.get("arquetipo") or {}, mundo, r["generacion"] or 1)
        return {"tipo": TIPO_FICHA, "version": VERSION_FICHA, "id": None, "nombre": meta.get("nombre") or r["individuo"],
                "mundo": mundo, "individuo": r["individuo"], "generacion": int(arq["generacion"]), "arquetipo": arq,
                "legado": datos.get("legado") or {}, "vidas": r["linaje"], "mejor_score": r["mejor_score"],
                "fecha": ahora_iso(), "commit": _commit(), "origen": "companero", "avisos": []}

    # --- consultar ---------------------------------------------------------------------------------------------------------
    def elemento(self, id_: str) -> Dict[str, Any]:
        """Una ficha (entera) o una estirpe archivada (metadatos y linaje)."""
        validar_id(id_)
        ruta = self._ruta_ficha(id_)
        if os.path.isfile(ruta):
            return dict(self._ficha(ruta), tipo_elemento="ficha")
        meta = self._meta_estirpe(id_)
        if meta is not None:
            r = self._resumen_linaje(meta["mundo"], self._linaje_archivado(id_))
            return dict(meta, tipo_elemento="estirpe", linaje=r["linaje"], arquetipo=r["arquetipo"])
        raise ErrorVivero(404, "elemento_desconocido", f"no hay ninguna ficha ni estirpe {id_}")

    def _entradas(self) -> List[Dict[str, Any]]:
        entradas: List[Dict[str, Any]] = []
        if os.path.isdir(self.dir_fichas):
            for nombre in sorted(os.listdir(self.dir_fichas)):
                if not nombre.endswith(".json") or not ID_VALIDO.match(nombre[:-5]):
                    continue
                try:
                    f = _leer_json(os.path.join(self.dir_fichas, nombre))
                except (json.JSONDecodeError, OSError):
                    continue
                if not isinstance(f, dict):
                    continue
                entradas.append({"tipo": "ficha", "id": nombre[:-5], "mundo": f.get("mundo"), "nombre": f.get("nombre"),
                                 "individuo": f.get("individuo"), "generacion": f.get("generacion"),
                                 "vidas": len(f.get("vidas") or []), "mejor_score": f.get("mejor_score"),
                                 "fecha": f.get("fecha"), "origen": f.get("origen"), "avisos": f.get("avisos") or [],
                                 "arquetipo": {r: (f.get("arquetipo") or {}).get(r) for r in RASGOS_CARACTER}})
        if os.path.isdir(self.dir_estirpes):
            for nombre in sorted(os.listdir(self.dir_estirpes)):
                if not ID_VALIDO.match(nombre):
                    continue
                try:
                    meta = self._meta_estirpe(nombre)
                except (json.JSONDecodeError, OSError):
                    continue
                if meta is None:
                    continue
                ultimo = meta.get("ultimo") or {}
                entradas.append({"tipo": "estirpe", "id": nombre, "mundo": meta.get("mundo"), "nombre": meta.get("nombre"),
                                 "individuo": ultimo.get("individuo"), "generacion": meta.get("generacion"),
                                 "vidas": meta.get("generaciones"), "mejor_score": meta.get("mejor_score"),
                                 "fecha": meta.get("archivada"), "motivo": meta.get("motivo"),
                                 "incompleta": bool(meta.get("incompleta")),
                                 "arquetipo": {r: (ultimo.get("arquetipo") or {}).get(r) for r in RASGOS_CARACTER}})
        return entradas

    def _rehacer_indice(self) -> List[Dict[str, Any]]:
        entradas = self._entradas()
        _escribir_json(os.path.join(self.dir, "indice.json"), {"version": 1, "actualizado": ahora_iso(), "elementos": entradas})
        return entradas

    def coleccion(self, mundo: Optional[str] = None) -> Dict[str, Any]:
        """Fichas, estirpes archivadas y compañeros, con el ranking por mundo (mejor Score, de mayor a menor)."""
        if mundo is not None and mundo not in MUNDOS:
            raise ErrorVivero(404, "mundo_desconocido", f"mundo desconocido: {mundo!r}")
        with self._cerrojo:
            entradas = self._entradas()
            if os.path.isdir(self.dir):
                indice = _leer_json(os.path.join(self.dir, "indice.json"))
                if not isinstance(indice, dict) or indice.get("elementos") != entradas:
                    self._rehacer_indice()
        if mundo is not None:
            entradas = [e for e in entradas if e["mundo"] == mundo]
        companeros = [c for c in self.companeros() if c["existe"] and (mundo is None or c["mundo"] == mundo)]
        ranking: Dict[str, List[Dict[str, Any]]] = {}
        for c in companeros:
            ranking.setdefault(c["mundo"], []).append({"tipo": "companero", "id": None, "mundo": c["mundo"], "nombre": c["nombre"],
                                                       "individuo": c["individuo"], "generacion": c["generacion"],
                                                       "mejor_score": c["mejor_score"]})
        for e in entradas:
            if e["mundo"] in MUNDOS:
                ranking.setdefault(e["mundo"], []).append({k: e.get(k) for k in ("tipo", "id", "mundo", "nombre", "individuo", "generacion", "mejor_score")})
        for lista in ranking.values():
            lista.sort(key=lambda x: -(x["mejor_score"] if _num(x["mejor_score"]) is not None else float("-inf")))
            for i, x in enumerate(lista, 1):
                x["puesto"] = i
        return {"fichas": [e for e in entradas if e["tipo"] == "ficha"], "estirpes": [e for e in entradas if e["tipo"] == "estirpe"],
                "companeros": companeros, "ranking": ranking}

    # --- cambiar -----------------------------------------------------------------------------------------------------------
    def renombrar(self, id_: str, nombre: Any) -> Dict[str, Any]:
        nombre = validar_nombre(nombre)
        with self._cerrojo:
            ruta = self._ruta_ficha(id_)
            if os.path.isfile(ruta):
                f = self._ficha(ruta)
                f["nombre"] = nombre
                _escribir_json(ruta, f)
            else:
                meta = self._meta_estirpe(id_)
                if meta is None:
                    raise ErrorVivero(404, "elemento_desconocido", f"no hay ninguna ficha ni estirpe {id_}")
                meta["nombre"] = nombre
                meta["renombrada"] = True
                _escribir_json(os.path.join(self._ruta_estirpe(id_), "estirpe.json"), meta)
            self._rehacer_indice()
        return self.elemento(id_)

    def adoptar(self, id_: str) -> Dict[str, Any]:
        """Hace compañero a una ficha o a una estirpe archivada. El compañero de antes se archiva (nunca se borra)."""
        with self._cerrojo:
            el = self.elemento(id_)
            mundo = el["mundo"]
            if mundo not in MUNDOS:
                raise ErrorVivero(400, "ficha_invalida", f"mundo desconocido en el elemento: {mundo!r}")
            if el["tipo_elemento"] == "estirpe" and el.get("incompleta"):
                raise ErrorVivero(409, "elemento_incompleto", "esa estirpe quedó a medio archivar: no se puede adoptar")
            archivada = self.archivar(mundo, motivo="adoptar")
            destino = self.dir_mundo(mundo)
            os.makedirs(destino, exist_ok=True)
            if el["tipo_elemento"] == "ficha":
                linaje = linaje_de_ficha(el)
                _escribir_json(os.path.join(destino, "linaje.json"), linaje)
            else:
                origen = self._ruta_estirpe(id_)
                ficheros = [f for f in FICHEROS_ESTIRPE if os.path.isfile(os.path.join(origen, f))]
                for f in ficheros:   # el destino está libre: archivar acaba de quitar los ficheros del compañero
                    shutil.copy2(os.path.join(origen, f), os.path.join(destino, f))
                    if os.path.getsize(os.path.join(origen, f)) != os.path.getsize(os.path.join(destino, f)):   # pragma: no cover
                        raise ErrorVivero(500, "error_interno", f"la copia de {f} no coincide; la estirpe sigue archivada")
                datos = _leer_json(os.path.join(destino, "linaje.json"))
                if el.get("renombrada") and isinstance(datos, dict):   # el nombre que le dio el usuario
                    datos["nombre"] = el["nombre"]
                    _escribir_json(os.path.join(destino, "linaje.json"), datos)
                shutil.rmtree(origen)   # la estirpe vuelve a su mundo: está entera en <datos>/<mundo>/
            self._rehacer_indice()
            return {"companero": self.companero(mundo), "archivada": archivada}

    # --- borrar (dos pasos) --------------------------------------------------------------------------------------------------
    def pedir_borrado(self, id_: str) -> Dict[str, Any]:
        """Primer paso: no borra nada. Devuelve un testigo de un solo uso (``TESTIGO_S`` segundos) y lo que se borraría."""
        el = self.elemento(id_)
        testigo = secrets.token_urlsafe(18)
        with self._cerrojo:
            ahora = time.monotonic()
            self._testigos = {t: v for t, v in self._testigos.items() if v[1] > ahora}
            self._testigos[testigo] = (id_, ahora + TESTIGO_S)
        resumen = {k: el.get(k) for k in ("id", "tipo_elemento", "mundo", "nombre", "individuo", "generacion", "mejor_score")}
        return {"testigo": testigo, "caduca_s": TESTIGO_S, "elemento": resumen}

    def confirmar_borrado(self, id_: str, testigo: Any) -> Dict[str, Any]:
        """Segundo paso: borra la ficha o la estirpe archivada, solo con el testigo que dio ``pedir_borrado`` para ella."""
        validar_id(id_)
        with self._cerrojo:
            dato = self._testigos.pop(testigo, None) if isinstance(testigo, str) else None
            if dato is None or dato[0] != id_ or dato[1] < time.monotonic():
                if dato is not None and dato[0] != id_:
                    self._testigos[testigo] = dato   # era de otro elemento: sigue valiendo para el suyo
                raise ErrorVivero(400, "testigo_invalido", "falta el testigo, ha caducado, ya se usó o es de otro elemento: no se borra nada")
            ruta = self._ruta_ficha(id_)
            if os.path.isfile(ruta):
                os.remove(ruta)
            elif os.path.isdir(self._ruta_estirpe(id_)):
                shutil.rmtree(self._ruta_estirpe(id_))
            else:
                raise ErrorVivero(404, "elemento_desconocido", f"no hay ninguna ficha ni estirpe {id_}")
            self._rehacer_indice()
        return {"borrado": id_}


# --- ficha -> linaje ---------------------------------------------------------------------------------------------------------
def linaje_de_ficha(ficha: Dict[str, Any]) -> Dict[str, Any]:
    """El ``linaje.json`` de una estirpe que empieza con una ficha adoptada: su arquetipo (del que muta la generación
    siguiente), su legado y su historial."""
    mundo = ficha["mundo"]
    arq = completar_arquetipo(ficha.get("arquetipo") or {}, mundo, int(ficha.get("generacion") or 1))
    generaciones = []
    for v in ficha.get("vidas") or []:
        g = {"individuo": v.get("individuo"), "latidos": v.get("latidos"), "vivo": v.get("vivo"),
             "causa_muerte": v.get("causa_muerte"), "puntuacion": v.get("puntuacion") or {}, "fitness": v.get("score"),
             "logros": v.get("logros") or [], "fijado": False}
        rasgos = v.get("arquetipo") or {}
        g["arquetipo"] = dict({k: arq[k] for k in ("nombre", "linaje")}, generacion=v.get("generacion"), padre=None,
                              **{r: rasgos.get(r, arq[r]) for r in RASGOS_CARACTER})
        generaciones.append(g)
    linaje: Dict[str, Any] = {"generaciones": generaciones, "arquetipo": arq, "legado": ficha.get("legado") or {},
                              "adoptada_de": ficha.get("id")}
    if ficha.get("nombre") and ficha.get("nombre") != ficha.get("individuo"):   # renombrada: la estirpe se llama así
        linaje["nombre"] = ficha["nombre"]
    return linaje


# --- conversión de fichas ------------------------------------------------------------------------------------------------------
def convertir(doc: Any) -> Dict[str, Any]:
    """Una ficha v1 a partir de una ficha v1 o de una antigua (``ida_individuo_v1``, ``ida_linaje_completo_v1`` o el JSON
    que aceptaba la antesala de T3). Lo que falta se apunta en ``avisos``."""
    if not isinstance(doc, dict):
        raise ErrorVivero(400, "ficha_invalida", "la ficha debe ser un objeto JSON")
    mundo = str(doc.get("mundo") or "").lower()
    if mundo not in MUNDOS:
        raise ErrorVivero(400, "ficha_invalida" if not mundo else "mundo_desconocido",
                          "la ficha no dice de qué mundo es" if not mundo else f"mundo desconocido en la ficha: {mundo!r}")
    avisos: List[str] = []
    tipo = doc.get("tipo")
    if tipo == TIPO_FICHA:
        if doc.get("version") != VERSION_FICHA:
            raise ErrorVivero(400, "ficha_invalida", f"versión de ficha desconocida: {doc.get('version')!r}")
        vidas = [vida_de_generacion(mundo, v) for v in doc.get("vidas") or [] if isinstance(v, dict)]
        arq_doc = doc.get("arquetipo") or {}
        origen = "importada"
        avisos = [str(a) for a in doc.get("avisos") or []]
    else:
        origen = "panel"
        gens = [g for g in doc.get("generaciones") or [] if isinstance(g, dict)]
        if tipo == "ida_linaje_completo_v1" or (gens and not doc.get("arquetipo")):
            vidas = [vida_de_generacion(mundo, g) for g in _orden_generacion(gens)]
            arq_doc = doc.get("arquetipo_actual") or doc.get("arquetipo") or (gens and _orden_generacion(gens)[-1].get("arquetipo")) or {}
        else:
            arq_doc = doc.get("arquetipo") or doc.get("arquetipo_actual") or {}
            g = {"individuo": doc.get("individuo"), "generacion": doc.get("generacion", (arq_doc or {}).get("generacion")),
                 "latidos": doc.get("latidos"), "vivo": doc.get("vivo"), "puntuacion": doc.get("puntuacion"),
                 "fitness": doc.get("fitness"), "causa_muerte": doc.get("causa_muerte"), "arquetipo": arq_doc}
            tiene_vida = any(doc.get(k) is not None for k in ("latidos", "puntuacion", "fitness"))
            vidas = [vida_de_generacion(mundo, g)] if tiene_vida else []
            avisos.append("historial: la ficha antigua solo trae una vida" if tiene_vida else "historial: la ficha antigua no trae ninguna vida")
        avisos.append("fecha: la ficha antigua no la trae; se pone la de la importación")
        avisos.append("commit: la ficha antigua no lo trae")
        if vidas and any(v["causa_muerte"] is None and v["vivo"] is not True for v in vidas):
            avisos.append("causa de muerte: no la trae")
        if vidas and not any(v["logros"] for v in vidas) and mundo == "crafter":
            avisos.append("logros: no los trae")
    if not isinstance(arq_doc, dict):
        raise ErrorVivero(400, "ficha_invalida", "arquetipo: debe ser un objeto")
    legado = doc.get("legado") or {}
    if not isinstance(legado, dict):
        raise ErrorVivero(400, "ficha_invalida", "legado: debe ser un objeto")
    if not arq_doc and not legado:
        raise ErrorVivero(400, "ficha_invalida", "la ficha no trae carácter ni legado")
    if not any(v for v in legado.values()) and "legado: vacío, la descendencia no hereda saber" not in avisos:
        avisos.append("legado: vacío, la descendencia no hereda saber")
    generacion = doc.get("generacion") or (arq_doc or {}).get("generacion") or (vidas[-1]["generacion"] if vidas else 1)
    if not arq_doc:
        avisos.append("carácter: no lo trae; se usa el equilibrado")
        arq_doc = dict.fromkeys(RASGOS_CARACTER, 0.5)
        arq_doc["umbral_miedo"] = 0.6
    arq = completar_arquetipo(arq_doc, mundo, int(generacion) if _num(generacion) is not None else 1)
    individuo = doc.get("individuo") or (vidas[-1]["individuo"] if vidas else f"{arq['linaje']}_G{arq['generacion']}")
    nombre = doc.get("nombre") if isinstance(doc.get("nombre"), str) and doc.get("nombre") else individuo
    return {
        "tipo": TIPO_FICHA, "version": VERSION_FICHA, "id": None,
        "nombre": validar_nombre(str(nombre)[:NOMBRE_MAX]), "mundo": mundo, "individuo": str(individuo),
        "generacion": int(arq["generacion"]), "arquetipo": arq, "legado": legado, "vidas": vidas,
        "mejor_score": _mejor(vidas), "fecha": doc.get("fecha") if tipo == TIPO_FICHA and doc.get("fecha") else ahora_iso(),
        "commit": doc.get("commit") if tipo == TIPO_FICHA else None, "origen": origen, "avisos": avisos,
    }
