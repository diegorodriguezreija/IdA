"""API v1 del servidor (O14): ``/api/v1/...``, JSON y SSE, solo biblioteca estándar.

Rutas (detalle de cuerpos y errores en ``docs/DISENO_OBSERVABILIDAD.md``, sección «API v1»):

- ``GET  /api/v1/mundos``                      mundos con su estado, extra, tiempo real y opciones declaradas
- ``POST /api/v1/mundos/{m}/instalar``         instala el extra del mundo (202 con la instalación)
- ``GET  /api/v1/instalaciones/{id}``          SSE con la salida de una instalación (``linea``, ``fin``)
- ``GET  /api/v1/presets``                     presets de carácter (es/en) y rangos de los rasgos
- ``POST /api/v1/vidas``                       lanza una vida (201)
- ``GET  /api/v1/vidas/actual``                la vida en curso (o ``null``)
- ``GET  /api/v1/vidas/actual/registro``       SSE de registros del latido v1 (``vida``, ``diario``, ``registro``, ``ritmo``,
                                               ``fin``); ``?nivel=vital`` o ``?nivel=cognitivo`` lo recorta a ese nivel
- ``POST /api/v1/vidas/actual/ritmo``          ``{"ritmo": "pausa" | "lento" | "comodo" | "x4" | "max"}`` (``x1`` = ``comodo``)
- ``POST /api/v1/vidas/actual/paso``           en pausa, deja pasar un latido (O20)
- ``POST /api/v1/vidas/actual/parar``          para la vida en curso
- ``GET  /api/v1/companeros[/{m}]``             el compañero de cada mundo (T4b); con ``{m}``, también su linaje
- ``POST /api/v1/companeros/{m}/guardar``      guarda el compañero como ficha en la colección
- ``POST /api/v1/companeros/{m}/archivar``     archiva el compañero en la colección (nunca lo borra)
- ``GET  /api/v1/companeros/{m}/exportar``     la ficha v1 del compañero, para descargar
- ``GET  /api/v1/coleccion[?mundo=m]``         fichas, estirpes archivadas, compañeros y ranking por mundo
- ``GET  /api/v1/coleccion/{id}[/exportar]``   una ficha o estirpe archivada (o su ficha v1, para descargar)
- ``POST /api/v1/coleccion/importar``          importa una ficha (v1 o antigua del panel) como ficha nueva
- ``POST /api/v1/coleccion/{id}/renombrar``    ``{"nombre": ...}``
- ``POST /api/v1/coleccion/{id}/adoptar``      la hace compañero (el de antes se archiva)
- ``POST /api/v1/coleccion/{id}/borrar``       primer paso: un testigo; no borra nada
- ``POST /api/v1/coleccion/{id}/borrar/confirmar``  ``{"testigo": ...}``: borra

Errores: ``{"error": {"codigo": ..., "mensaje": ..., "campo"?: ...}}`` con 400, 403, 404, 409 o 500.
"""

import json
import queue
from typing import TYPE_CHECKING, Any, Callable, Dict, Mapping, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from ida.mundos import MUNDOS
from ida.mundos.opciones import OpcionInvalida, con_defectos
from ida.telemetria import catalogo, presets
from ida.telemetria.esquema import ESQUEMA, NIVELES
from ida.telemetria.instalador import ErrorInstalacion
from ida.telemetria.ritmo import RITMOS, SINONIMOS
from ida.telemetria.vivero import ErrorVivero

if TYPE_CHECKING:   # pragma: no cover
    from ida.telemetria.servidor import Telemetria, _Manejador

PREFIJO = "/api/v1/"
PLAZO_LOGICO = 40.0          # O11: como D17
LIMITES = {"latidos": (1, 1_000_000), "generaciones": (1, 100), "semilla": (0, 2_147_483_646)}
DEFECTOS = {"latidos": 300, "generaciones": 1, "semilla": 1}
NIVEL_DEFECTO = "completo"   # el panel clásico enseña los tiempos por Componente (hasta T6)
CAMPOS_VITAL = {c.lstrip("?") for c in (*ESQUEMA["base"], *ESQUEMA["vital"])}
CAMPOS_COGNITIVO = CAMPOS_VITAL | {c.lstrip("?") for c in ESQUEMA["cognitivo"]}
SABER_COGNITIVO = 20   # como el observador al nivel cognitivo

# Códigos de error de la API (la interfaz los traduce con la clave i18n «error.<codigo>»).
CODIGOS = ("json_invalido", "origen_no_permitido", "ruta_desconocida", "mundo_desconocido", "mundo_no_instalado",
           "opcion_invalida", "campo_invalido", "caracter_invalido", "ficha_invalida", "ficha_de_otro_mundo",
           "vida_en_curso", "sin_vida", "ritmo_invalido", "ritmo_fijo", "sin_pausa", "sin_extra", "extra_desconocido",
           "instalacion_en_curso", "instalacion_desconocida", "error_interno",
           # T4b: compañero y colección
           "sin_companero", "id_invalido", "elemento_desconocido", "elemento_incompleto", "nombre_invalido", "testigo_invalido")


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
    elif "caracter" in datos or caracter is None:   # un preset explícito manda sobre el carácter de la ficha
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
        "ritmo_comodo_ms": catalogo.ritmo_comodo(mundo),         # O20
    }


def recortar_vital(registro: Dict[str, Any]) -> Dict[str, Any]:
    """El registro reducido al nivel vital (menos datos por la SSE)."""
    salida = {k: v for k, v in registro.items() if k in CAMPOS_VITAL}
    salida["nivel"] = "vital"
    return salida


def recortar_cognitivo(registro: Dict[str, Any]) -> Dict[str, Any]:
    """El registro reducido al nivel cognitivo (el del Vivero, O19): sin tiempos, fases ni piezas de ``ef``, y ``saber``
    con las 20 proposiciones de más confianza. Un registro vital se queda como está."""
    if registro.get("nivel") == "vital":
        return registro
    salida = {k: v for k, v in registro.items() if k in CAMPOS_COGNITIVO}
    if isinstance(salida.get("saber"), list):
        salida["saber"] = salida["saber"][:SABER_COGNITIVO]
    salida["nivel"] = "cognitivo"
    return salida


RECORTES = {"vital": recortar_vital, "cognitivo": recortar_cognitivo}


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
    except ErrorVivero as e:
        h._json(e.http, ErrorApi(e.http, e.codigo, e.mensaje).cuerpo())
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
        _sse_registro(h, tel, RECORTES.get(query.get("nivel", [""])[0]))
    elif partes and partes[0] in ("companeros", "coleccion"):
        _get_vivero(h, tel, partes, query)
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
        if ritmo not in RITMOS and ritmo not in SINONIMOS:
            raise ErrorApi(400, "ritmo_invalido", f"ritmo: uno de {', '.join(RITMOS)}", "ritmo")
        if vida["tiempo_real"]:
            raise ErrorApi(409, "ritmo_fijo", f"{vida['mundo']} es un mundo de tiempo real: el ritmo lo marca el mundo")
        h._json(200, {"ritmo": tel.fijar_ritmo(ritmo)})
    elif partes == ["vidas", "actual", "paso"]:
        vida = tel.vida_actual()
        if vida is None or not vida["activa"]:
            raise ErrorApi(404, "sin_vida", "no hay ninguna vida en curso")
        if vida["tiempo_real"]:
            raise ErrorApi(409, "ritmo_fijo", f"{vida['mundo']} es un mundo de tiempo real: el ritmo lo marca el mundo")
        try:
            h._json(200, tel.paso())
        except ValueError:
            raise ErrorApi(409, "sin_pausa", "«paso a paso» solo con la vida en pausa") from None
    elif partes and partes[0] in ("companeros", "coleccion"):
        _post_vivero(h, tel, partes, datos)
    elif partes == ["vidas", "actual", "parar"]:
        vida = tel.vida_actual()
        if vida is None or not vida["activa"]:
            raise ErrorApi(404, "sin_vida", "no hay ninguna vida en curso")
        tel.detener_simulacion()
        h._json(200, {"vida": tel.vida_actual()})
    else:
        raise _desconocida()


# --- compañero y colección (T4b, sección 13) ----------------------------------------------------------------------------
def _mundo(nombre: str) -> str:
    if nombre not in MUNDOS:
        raise ErrorApi(404, "mundo_desconocido", f"mundo desconocido: {nombre!r} (conocidos: {', '.join(MUNDOS)})")
    return nombre


def _descarga(h: "_Manejador", doc: Dict[str, Any]) -> None:
    """La ficha como fichero JSON para descargar (nombre de fichero solo con caracteres seguros)."""
    base = "".join(c if c.isalnum() or c in "-_." else "_" for c in f"ida-ficha-{doc.get('mundo')}-{doc.get('individuo')}")
    cuerpo = json.dumps(doc, ensure_ascii=False, indent=2).encode("utf-8")
    h.send_response(200)
    h.send_header("Content-Type", "application/json; charset=utf-8")
    h.send_header("Content-Disposition", f'attachment; filename="{base}.json"')
    h.send_header("Content-Length", str(len(cuerpo)))
    h.end_headers()
    h.wfile.write(cuerpo)


def _sin_vida_en(tel: "Telemetria", mundo: str) -> None:
    if tel.vida_de(mundo):
        raise ErrorApi(409, "vida_en_curso", f"hay una vida de {mundo} en marcha y escribe en su estirpe: párala antes")


def _get_vivero(h: "_Manejador", tel: "Telemetria", partes: list, query: Dict[str, list]) -> None:
    viv = tel.vivero
    if partes == ["companeros"]:
        h._json(200, {"companeros": viv.companeros()})
    elif len(partes) == 2 and partes[0] == "companeros":
        h._json(200, {"companero": viv.companero(_mundo(partes[1]))})
    elif len(partes) == 3 and partes[0] == "companeros" and partes[2] == "exportar":
        _descarga(h, viv.ficha_del_companero(_mundo(partes[1])))
    elif partes == ["coleccion"]:
        mundo = query.get("mundo", [None])[0]
        h._json(200, viv.coleccion(_mundo(mundo) if mundo is not None else None))
    elif len(partes) == 2 and partes[0] == "coleccion":
        h._json(200, {"elemento": viv.elemento(partes[1])})
    elif len(partes) == 3 and partes[0] == "coleccion" and partes[2] == "exportar":
        el = viv.elemento(partes[1])
        if el["tipo_elemento"] == "ficha":
            ficha = {k: v for k, v in el.items() if k != "tipo_elemento"}
        else:
            ficha = viv.ficha_de_estirpe(partes[1])
        _descarga(h, ficha)
    else:
        raise _desconocida()


def _post_vivero(h: "_Manejador", tel: "Telemetria", partes: list, datos: Any) -> None:
    viv = tel.vivero
    cuerpo = datos if isinstance(datos, dict) else {}
    if len(partes) == 3 and partes[0] == "companeros" and partes[2] == "guardar":
        nombre = cuerpo.get("nombre")
        h._json(201, {"ficha": viv.guardar(_mundo(partes[1]), nombre)})
    elif len(partes) == 3 and partes[0] == "companeros" and partes[2] == "archivar":
        mundo = _mundo(partes[1])
        _sin_vida_en(tel, mundo)
        h._json(200, {"archivada": viv.archivar(mundo, motivo="archivar")})
    elif partes == ["coleccion", "importar"]:
        if "ficha" not in cuerpo:
            raise ErrorApi(400, "ficha_invalida", "falta la ficha", "ficha")
        ficha = viv.importar(cuerpo["ficha"])
        h._json(201, {"ficha": ficha, "avisos": ficha["avisos"]})
    elif len(partes) == 3 and partes[0] == "coleccion" and partes[2] == "renombrar":
        h._json(200, {"elemento": viv.renombrar(partes[1], cuerpo.get("nombre"))})
    elif len(partes) == 3 and partes[0] == "coleccion" and partes[2] == "adoptar":
        el = viv.elemento(partes[1])
        _sin_vida_en(tel, el["mundo"])
        h._json(200, viv.adoptar(partes[1]))
    elif len(partes) == 3 and partes[0] == "coleccion" and partes[2] == "borrar":
        h._json(200, viv.pedir_borrado(partes[1]))
    elif len(partes) == 4 and partes[0] == "coleccion" and partes[2:] == ["borrar", "confirmar"]:
        h._json(200, viv.confirmar_borrado(partes[1], cuerpo.get("testigo")))
    else:
        raise _desconocida()


# --- SSE --------------------------------------------------------------------------------------------------------------
def _sse_registro(h: "_Manejador", tel: "Telemetria", recorte: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]]) -> None:
    h._sse_cabecera()
    cola = tel.suscribir_registro()
    try:
        vida = tel.vida_actual()
        if vida is not None:
            h._sse("vida", vida)
            h._sse("diario", tel.diario())      # lo de antes de conectarse: el diario y «Lo que sabe» no empiezan vacíos
            ultimo = tel.ultimo_con_escena()
            if ultimo is not None:
                h._sse("registro", recorte(ultimo) if recorte else ultimo)
        while tel.activo:
            try:
                evento, dato = cola.get(timeout=1.0)
            except queue.Empty:
                h._sse_comentario()
                continue
            if evento == "registro" and recorte:
                dato = recorte(dato)
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
