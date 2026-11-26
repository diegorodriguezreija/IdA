"""API v1 del servidor (O14): ``/api/v1/...``, JSON y SSE, solo biblioteca estándar.

Rutas (detalle de cuerpos y errores en ``docs/DISENO_OBSERVABILIDAD.md``, sección «API v1»):

- ``GET  /api/v1/mundos``                      mundos con su estado, extra, tiempo real y opciones declaradas
- ``POST /api/v1/mundos/{m}/instalar``         instala el extra del mundo (202 con la instalación)
- ``GET  /api/v1/instalaciones/{id}``          SSE con la salida de una instalación (``linea``, ``fin``)
- ``GET  /api/v1/presets``                     presets de carácter (es/en) y rangos de los rasgos
- ``POST /api/v1/vidas``                       lanza una vida (201)
- ``GET  /api/v1/vidas/actual``                la vida en curso (o ``null``)
- ``GET  /api/v1/vidas/actual/registro``       SSE de registros del latido v1 (``registro``, ``vida``, ``fin``)
- ``POST /api/v1/vidas/actual/ritmo``          ``{"ritmo": "pausa" | "x1" | "x4" | "max"}``
- ``POST /api/v1/vidas/actual/parar``          para la vida en curso

Errores: ``{"error": {"codigo": ..., "mensaje": ..., "campo"?: ...}}`` con 400, 403, 404, 409 o 500.
"""

import json
import queue
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from ida.mundos import MUNDOS
from ida.mundos.opciones import OpcionInvalida, con_defectos
from ida.telemetria import catalogo, presets
from ida.telemetria.esquema import ESQUEMA, NIVELES
from ida.telemetria.instalador import ErrorInstalacion
from ida.telemetria.ritmo import RITMOS

if TYPE_CHECKING:   # pragma: no cover
    from ida.telemetria.servidor import Telemetria, _Manejador

PREFIJO = "/api/v1/"
PLAZO_LOGICO = 40.0          # O11: como D17
LIMITES = {"latidos": (1, 1_000_000), "generaciones": (1, 100), "semilla": (0, 2_147_483_646)}
DEFECTOS = {"latidos": 300, "generaciones": 1, "semilla": 1}
NIVEL_DEFECTO = "completo"   # el panel clásico enseña los tiempos por Componente (hasta T6)
CAMPOS_VITAL = set(ESQUEMA["base"]) | set(ESQUEMA["vital"]) | {"escena"}

# Códigos de error de la API (la interfaz los traduce con la clave i18n «error.<codigo>»).
CODIGOS = ("json_invalido", "origen_no_permitido", "ruta_desconocida", "mundo_desconocido", "mundo_no_instalado",
           "opcion_invalida", "campo_invalido", "caracter_invalido", "ficha_invalida", "ficha_de_otro_mundo",
           "vida_en_curso", "sin_vida", "ritmo_invalido", "ritmo_fijo", "sin_extra", "extra_desconocido",
           "instalacion_en_curso", "instalacion_desconocida", "error_interno")


class ErrorApi(Exception):
    def __init__(self, http: int, codigo: str, mensaje: str, campo: Optional[str] = None) -> None:
        super().__init__(mensaje)
        self.http, self.codigo, self.mensaje, self.campo = http, codigo, mensaje, campo

    def cuerpo(self) -> Dict[str, Any]:
        error: Dict[str, Any] = {"codigo": self.codigo, "mensaje": self.mensaje}
        if self.campo:
            error["campo"] = self.campo
        return {"error": error}


# --- validación de una vida -------------------------------------------------------------------------------------------
def _entero(datos: Mapping[str, Any], campo: str) -> int:
    valor = datos.get(campo, DEFECTOS[campo])
    lo, hi = LIMITES[campo]
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor != int(valor):
        raise ErrorApi(400, "campo_invalido", f"{campo}: se esperaba un entero, hay {valor!r}", campo)
    if not lo <= int(valor) <= hi:
        raise ErrorApi(400, "campo_invalido", f"{campo}: {int(valor)} fuera de [{lo}, {hi}]", campo)
    return int(valor)


def leer_ficha(ficha: Any, mundo: str) -> Tuple[Optional[Dict[str, float]], Dict[str, Any]]:
    """Carácter y legado de una ficha de individuo (el JSON que descarga hoy el panel: ``arquetipo``,
    ``arquetipo_actual`` o la última de ``generaciones``, y ``legado``). Lo aprendido es de cada mundo: una ficha de
    otro mundo es un error."""
    if not isinstance(ficha, dict):
        raise ErrorApi(400, "ficha_invalida", "la ficha debe ser un objeto JSON", "ficha")
    de = str(ficha.get("mundo") or "").lower()
    if de and de != mundo:
        raise ErrorApi(400, "ficha_de_otro_mundo", f"la ficha es de {de!r} y la vida, de {mundo!r}: lo aprendido no pasa de un mundo a otro", "ficha")
    arq = ficha.get("arquetipo") or ficha.get("arquetipo_actual")
    if not arq and isinstance(ficha.get("generaciones"), list) and ficha["generaciones"]:
        ultima = ficha["generaciones"][-1]
        arq = ultima.get("arquetipo") if isinstance(ultima, dict) else None
    legado = ficha.get("legado") or {}
    if not isinstance(legado, dict):
        raise ErrorApi(400, "ficha_invalida", "legado: debe ser un objeto", "ficha")
    if not arq and not legado:
        raise ErrorApi(400, "ficha_invalida", "la ficha no trae carácter ni legado", "ficha")
    caracter = None
    if arq:
        completo = {r: arq.get(r, presets.PRESETS_POR_ID["equilibrado"]["arquetipo"][r]) for r in presets.RASGOS}
        try:
            caracter = presets.validar_arquetipo(completo)
        except ValueError as e:
            raise ErrorApi(400, "ficha_invalida", f"carácter de la ficha: {e}", "ficha") from None
    return caracter, legado


def preparar_vida(datos: Any) -> Dict[str, Any]:
    """La configuración de ``Telemetria.lanzar`` a partir del cuerpo de ``POST /api/v1/vidas``, comprobada."""
    if not isinstance(datos, dict):
        raise ErrorApi(400, "json_invalido", "el cuerpo debe ser un objeto JSON")
    mundo = datos.get("mundo")
    if mundo not in MUNDOS:
        raise ErrorApi(400, "mundo_desconocido", f"mundo desconocido: {mundo!r} (conocidos: {', '.join(MUNDOS)})", "mundo")
    c = catalogo.clase(mundo)
    est = catalogo.estado(mundo)
    if c is None or est not in catalogo.LANZABLES:
        raise ErrorApi(409, "mundo_no_instalado", f"{mundo}: {est}; instálalo desde la antesala", "mundo")
    opciones = datos.get("opciones") or {}
    if not isinstance(opciones, dict):
        raise ErrorApi(400, "opcion_invalida", "opciones: debe ser un objeto", "opciones")
    try:
        opciones = con_defectos(c.opciones(), opciones, mundo)   # O8: los declarados, con lo que llegue del formulario
    except OpcionInvalida as e:
        raise ErrorApi(400, "opcion_invalida", str(e), "opciones") from None
    caracter: Optional[Dict[str, float]] = None
    legado: Dict[str, Any] = {}
    if datos.get("ficha") is not None:
        caracter, legado = leer_ficha(datos["ficha"], mundo)
    if datos.get("arquetipo") is not None:
        try:
            caracter = presets.validar_arquetipo(datos["arquetipo"])
        except ValueError as e:
            raise ErrorApi(400, "caracter_invalido", str(e), "arquetipo") from None
    elif caracter is None:
        preset = datos.get("caracter", "optimo")
        if preset not in presets.PRESETS_POR_ID:
            raise ErrorApi(400, "caracter_invalido", f"carácter desconocido: {preset!r} (conocidos: {', '.join(presets.PRESETS_POR_ID)})", "caracter")
        caracter = presets.arquetipo_de(preset, mundo)
    nivel = datos.get("nivel", NIVEL_DEFECTO)
    if nivel not in NIVELES:
        raise ErrorApi(400, "campo_invalido", f"nivel: uno de {', '.join(NIVELES)}", "nivel")
    for campo in ("sin_experiencia", "tabula_rasa"):
        if not isinstance(datos.get(campo, False), bool):
            raise ErrorApi(400, "campo_invalido", f"{campo}: debe ser booleano", campo)
    tiempo_real = bool(c.perfil.tiempo_real)
    return {
        "mundo": mundo,
        "opciones": opciones,
        "arquetipo": caracter,
        "legado": legado or None,
        "semilla": _entero(datos, "semilla"),
        "latidos": _entero(datos, "latidos"),
        "generaciones": _entero(datos, "generaciones"),
        "sin_experiencia": bool(datos.get("sin_experiencia", False)),
        "tabula_rasa": bool(datos.get("tabula_rasa", False)),
        "nivel": nivel,
        "plazo_logico": None if tiempo_real else PLAZO_LOGICO,   # O11
        "tiempo_real": tiempo_real,
    }


def recortar_vital(registro: Dict[str, Any]) -> Dict[str, Any]:
    """El registro reducido al nivel vital (para el Vivero: menos datos por la SSE)."""
    salida = {k: v for k, v in registro.items() if k in CAMPOS_VITAL}
    salida["nivel"] = "vital"
    return salida


# --- atención de rutas ------------------------------------------------------------------------------------------------
def atender(h: "_Manejador", metodo: str, cuerpo: bytes = b"") -> None:
    tel: "Telemetria" = h.servidor_tel
    url = urlparse(h.path)
    partes = [p for p in url.path[len(PREFIJO):].split("/") if p]
    query = parse_qs(url.query)
    try:
        if metodo == "POST":
            if not h._origen_valido():
                raise ErrorApi(403, "origen_no_permitido", "POST solo desde el propio servidor (cabecera Origin o Referer)")
            try:
                datos = json.loads(cuerpo.decode("utf-8")) if cuerpo.strip() else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise ErrorApi(400, "json_invalido", "el cuerpo no es JSON válido") from None
            _post(h, tel, partes, datos)
        else:
            _get(h, tel, partes, query)
    except ErrorApi as e:
        h._json(e.http, e.cuerpo())
    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
        pass
    except Exception as e:   # pragma: no cover - el servidor no se cae por un fallo de una ruta
        h._json(500, ErrorApi(500, "error_interno", str(e)).cuerpo())


def _desconocida() -> ErrorApi:
    return ErrorApi(404, "ruta_desconocida", "ruta desconocida")


def _get(h: "_Manejador", tel: "Telemetria", partes: list, query: Dict[str, list]) -> None:
    if partes == ["mundos"]:
        lista = catalogo.mundos()
        for m in lista:
            inst = tel.instalador.ultima_de(m["nombre"])
            m["instalacion"] = inst.resumen() if inst is not None else None
        h._json(200, {"mundos": lista})
    elif partes == ["presets"]:
        h._json(200, presets.respuesta())
    elif partes == ["vidas", "actual"]:
        h._json(200, {"vida": tel.vida_actual()})
    elif partes == ["vidas", "actual", "registro"]:
        _sse_registro(h, tel, vital=query.get("nivel", [""])[0] == "vital")
    elif len(partes) == 2 and partes[0] == "instalaciones":
        inst = tel.instalador.instalaciones.get(partes[1])
        if inst is None:
            raise ErrorApi(404, "instalacion_desconocida", f"instalación desconocida: {partes[1]!r}")
        _sse_instalacion(h, inst)
    else:
        raise _desconocida()


def _post(h: "_Manejador", tel: "Telemetria", partes: list, datos: Any) -> None:
    if len(partes) == 3 and partes[0] == "mundos" and partes[2] == "instalar":
        try:
            inst = tel.instalador.instalar(partes[1])
        except ErrorInstalacion as e:
            raise ErrorApi(e.http, e.codigo, e.mensaje) from None
        h._json(202, {"instalacion": inst.resumen()})
    elif partes == ["vidas"]:
        config = preparar_vida(datos)
        if tel.simulacion_activa and not datos.get("reemplazar", False):
            raise ErrorApi(409, "vida_en_curso", "ya hay una vida en curso: párala o envía \"reemplazar\": true")
        h._json(201, {"vida": tel.lanzar(config)})
    elif partes == ["vidas", "actual", "ritmo"]:
        vida = tel.vida_actual()
        if vida is None or not vida["activa"]:
            raise ErrorApi(404, "sin_vida", "no hay ninguna vida en curso")
        ritmo = datos.get("ritmo") if isinstance(datos, dict) else None
        if ritmo not in RITMOS:
            raise ErrorApi(400, "ritmo_invalido", f"ritmo: uno de {', '.join(RITMOS)}", "ritmo")
        if vida["tiempo_real"]:
            raise ErrorApi(409, "ritmo_fijo", f"{vida['mundo']} es un mundo de tiempo real: el ritmo lo marca el mundo")
        tel.fijar_ritmo(ritmo)
        h._json(200, {"ritmo": ritmo})
    elif partes == ["vidas", "actual", "parar"]:
        vida = tel.vida_actual()
        if vida is None or not vida["activa"]:
            raise ErrorApi(404, "sin_vida", "no hay ninguna vida en curso")
        tel.detener_simulacion()
        h._json(200, {"vida": tel.vida_actual()})
    else:
        raise _desconocida()


# --- SSE --------------------------------------------------------------------------------------------------------------
def _sse_registro(h: "_Manejador", tel: "Telemetria", vital: bool) -> None:
    h._sse_cabecera()
    cola = tel.suscribir_registro()
    try:
        vida = tel.vida_actual()
        if vida is not None:
            h._sse("vida", vida)
            ultimo = tel.ultimo_con_escena()
            if ultimo is not None:
                h._sse("registro", recortar_vital(ultimo) if vital else ultimo)
        while tel.activo:
            try:
                evento, dato = cola.get(timeout=1.0)
            except queue.Empty:
                h._sse_comentario()
                continue
            if evento == "registro" and vital:
                dato = recortar_vital(dato)
            h._sse(evento, dato)
    finally:
        tel.desuscribir_registro(cola)


def _sse_instalacion(h: "_Manejador", inst: Any) -> None:
    h._sse_cabecera()
    enviadas = 0
    while True:
        with inst.cond:
            if enviadas >= len(inst.lineas) and inst.estado == "en_curso":
                inst.cond.wait(timeout=1.0)
            nuevas = inst.lineas[enviadas:]
            estado = inst.estado
        for linea in nuevas:
            h._sse("linea", {"texto": linea})
        enviadas += len(nuevas)
        if estado != "en_curso" and enviadas >= len(inst.lineas):
            h._sse("fin", inst.resumen())
            return
        if not nuevas:
            h._sse_comentario()
