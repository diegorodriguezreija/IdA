"""Servidor de la aplicación web y de la telemetría, en un hilo aparte (O14). Solo biblioteca estándar.

Escucha en ``127.0.0.1`` (en un contenedor, ``IDA_TELEMETRIA_HOST``). Los POST solo se aceptan si su cabecera
``Origin`` (o, si falta, ``Referer``) es la del propio servidor; si no, 403.

Rutas:
- ``/``                  aplicación (``web/index.html``: antesala, Vivero y Laboratorio); con ``--ver``, el panel
- ``/api/v1/...``        API v1 (``ida/telemetria/api_v1.py``): mundos, instalación, presets, vidas, ritmo, SSE
- ``/antesala-antigua``  antesala de antes (también en ``/antesala``), hasta T6
- ``/panel``             panel HTML de telemetría (hasta T6)
- ``/eventos``            flujo SSE con un resumen por latido
- ``/estado``             último resumen en JSON
- ``/estado_simulacion``  estado de ejecución del organismo
- ``POST /iniciar``       inicia una simulación con parámetros
- ``POST /detener``       detiene la simulación activa
- ``GET /linaje``         consulta el historial y ranking de generaciones
- ``GET /linaje/descargar`` descarga un individuo o el linaje completo en JSON
- ``POST /linaje/fijar``   fija o desfija un individuo para la retención
- ``POST /linaje/restaurar`` valida y extrae parámetros de un JSON restaurado
- ``/escena``             visor de comprobación de ``escena()`` (T2a): dibuja una grabación cargada en el navegador
- ``/web/<ruta>``         ficheros estáticos de ``ida/telemetria/web/`` (solo esa carpeta y tipos conocidos)
"""

import json
import os
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

from ida.historico import cargar_linaje, conmutar_fijado, exportar_individuo, exportar_linaje_completo
from ida.telemetria import api_v1
from ida.telemetria.compat import a_panel
from ida.telemetria.esquema import VERSION
from ida.telemetria.instalador import Instalador
from ida.telemetria.ritmo import Regulador

PLAZO_LOGICO_ANTESALA = 40.0   # O11: como D17
NIVEL_ANTESALA = "completo"     # el panel de hoy enseña los tiempos por Componente (nivel completo); hasta T6


def plazo_por_defecto(mundo: str) -> Optional[float]:
    """O11: lo lanzado desde la antesala usa plazo lógico (40 operaciones por ms), salvo en los mundos de tiempo real,
    que se detectan por el ``Perfil.tiempo_real`` de la clase del mundo (Snake): allí el ritmo lo marca el mundo."""
    from ida.mundos import cargar

    return None if cargar(mundo).perfil.tiempo_real else PLAZO_LOGICO_ANTESALA


def opciones_por_defecto(mundo: str, dadas: Dict[str, Any]) -> Dict[str, Any]:
    """O8: lo lanzado desde la antesala usa los valores por defecto declarados por el mundo (``Mundo.opciones()``, los
    de la medición oficial donde la hay), sustituidos por los que lleguen del formulario, ya comprobados."""
    from ida.mundos import cargar
    from ida.mundos.opciones import con_defectos

    return con_defectos(cargar(mundo).opciones(), dadas, mundo)


WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
TIPOS_WEB = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
             ".json": "application/json; charset=utf-8", ".png": "image/png", ".svg": "image/svg+xml"}
ANFITRIONES_LOCALES = ("127.0.0.1", "localhost", "[::1]")


def fichero_web(ruta: str) -> Optional[str]:
    """La ruta en disco de ``web/<ruta>`` si es un fichero de un tipo conocido dentro de ``web/``; si no, None."""
    raiz = os.path.realpath(WEB)
    destino = os.path.realpath(os.path.join(raiz, unquote(ruta).lstrip("/\\")))
    if not destino.startswith(raiz + os.sep) or not os.path.isfile(destino):
        return None
    return destino if os.path.splitext(destino)[1].lower() in TIPOS_WEB else None


PANEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "panel.html")
ANTESALA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "antesala.html")
APLICACION = os.path.join(WEB, "index.html")


def origen_de(cabeceras: Any) -> str:
    """``esquema://anfitrion[:puerto]`` de la cabecera Origin o, si falta, de Referer ("" si no hay ninguna)."""
    origen = (cabeceras.get("Origin") or "").strip()
    if origen and origen != "null":
        return origen.rstrip("/")
    referer = (cabeceras.get("Referer") or "").strip()
    if referer:
        u = urlparse(referer)
        if u.scheme and u.netloc:
            return f"{u.scheme}://{u.netloc}"
    return ""


def origenes_propios(puerto: int) -> Tuple[str, ...]:
    return tuple(f"http://{a}:{puerto}" for a in ANFITRIONES_LOCALES)


class _Manejador(BaseHTTPRequestHandler):
    servidor_tel: "Telemetria" = None  # type: ignore

    def log_message(self, *args) -> None:   # silencio en consola
        pass

    def do_GET(self) -> None:
        tel = self.servidor_tel
        url = urlparse(self.path)
        ruta = url.path
        params = parse_qs(url.query)
        mundo_query = params.get("mundo", [tel.mundo or "minimo"])[0]

        if ruta.startswith(api_v1.PREFIJO):
            api_v1.atender(self, "GET")
        elif ruta == "/eventos":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            cola = tel._suscribir()
            try:
                if tel.ultimo is not None:
                    self._enviar(tel.ultimo)
                while tel.activo:
                    try:
                        self._enviar(cola.get(timeout=1.0))
                    except queue.Empty:
                        self.wfile.write(b": latido\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
            finally:
                tel._desuscribir(cola)
        elif ruta == "/estado":
            self._responder(json.dumps(tel.ultimo or {}, ensure_ascii=False, default=str).encode("utf-8"), "application/json")
        elif ruta == "/estado_simulacion":
            resp = {"activa": tel.simulacion_activa, "mundo": tel.mundo}
            self._responder(json.dumps(resp, ensure_ascii=False).encode("utf-8"), "application/json")
        elif ruta == "/linaje":
            datos = cargar_linaje(mundo_query)
            self._responder(json.dumps(datos, ensure_ascii=False).encode("utf-8"), "application/json")
        elif ruta == "/linaje/descargar":
            ind_id = params.get("individuo", [None])[0]
            if ind_id:
                doc = exportar_individuo(mundo_query, ind_id)
                nombre_archivo = f"ida-individuo-{ind_id}.json"
            else:
                doc = exportar_linaje_completo(mundo_query)
                nombre_archivo = f"ida-linaje-{mundo_query}.json"
            if doc is None:
                self.send_error(404, "Individuo o linaje no encontrado")
                return
            cuerpo = json.dumps(doc, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{nombre_archivo}"')
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)
        elif ruta in ("/antesala", "/antesala-antigua"):
            with open(ANTESALA, "rb") as f:
                self._responder(f.read(), "text/html; charset=utf-8")
        elif ruta == "/panel":
            with open(PANEL, "rb") as f:
                self._responder(f.read(), "text/html; charset=utf-8")
        elif ruta == "/escena" or ruta.startswith("/web/"):
            destino = fichero_web("escena.html" if ruta == "/escena" else ruta[len("/web/"):])
            if destino is None:
                self.send_error(404, "Fichero no encontrado")
                return
            with open(destino, "rb") as f:
                self._responder(f.read(), TIPOS_WEB[os.path.splitext(destino)[1].lower()])
        elif ruta in ("/", "/index.html"):
            # La aplicación; con ``--ver`` (sin antesala) y una vida en marcha, el panel de siempre
            archivo = PANEL if (tel.simulacion_activa and not tel.modo_antesala) else APLICACION
            with open(archivo, "rb") as f:
                self._responder(f.read(), "text/html; charset=utf-8")
        else:
            self.send_error(404, "Ruta no encontrada")

    def do_POST(self) -> None:
        tel = self.servidor_tel
        ruta = self.path.split("?")[0]
        try:
            longitud = int(self.headers.get("Content-Length", 0))
        except ValueError:
            longitud = 0
        bruto = self.rfile.read(longitud) if longitud > 0 else b""
        if not self._origen_valido():
            self._json(403, api_v1.ErrorApi(403, "origen_no_permitido", "POST solo desde el propio servidor").cuerpo())
            return
        if ruta.startswith(api_v1.PREFIJO):
            api_v1.atender(self, "POST", bruto)
            return
        cuerpo = bruto.decode("utf-8", errors="replace") if bruto else "{}"
        try:
            datos = json.loads(cuerpo) if cuerpo else {}
        except Exception:
            datos = {}

        if ruta == "/iniciar":
            try:
                tel.iniciar_simulacion(datos)
                self._responder(json.dumps({"ok": True, "url": "/panel"}).encode("utf-8"), "application/json")
            except Exception as e:
                self._responder(json.dumps({"ok": False, "error": str(e)}).encode("utf-8"), "application/json", codigo=400)
        elif ruta == "/detener":
            tel.detener_simulacion()
            self._responder(json.dumps({"ok": True}).encode("utf-8"), "application/json")
        elif ruta == "/linaje/fijar":
            mundo = datos.get("mundo") or tel.mundo or "minimo"
            ind_id = datos.get("individuo")
            if not ind_id:
                self._responder(json.dumps({"ok": False, "error": "falta individuo"}).encode("utf-8"), "application/json", codigo=400)
                return
            fijado = datos.get("fijado")
            nuevo = conmutar_fijado(mundo, ind_id, fijado)
            self._responder(json.dumps({"ok": True, "fijado": nuevo}).encode("utf-8"), "application/json")
        elif ruta == "/linaje/restaurar":
            mundo = datos.get("mundo") or tel.mundo or "minimo"
            arquetipo = datos.get("arquetipo")
            legado = datos.get("legado", {})
            if not arquetipo and "arquetipo_actual" in datos:
                arquetipo = datos.get("arquetipo_actual")
            elif not arquetipo and "generaciones" in datos and datos["generaciones"]:
                arquetipo = datos["generaciones"][-1].get("arquetipo")
            self._responder(json.dumps({"ok": True, "mundo": mundo, "arquetipo": arquetipo, "legado": legado}).encode("utf-8"), "application/json")
        else:
            self.send_error(404, "Ruta no encontrada")

    def _origen_valido(self) -> bool:
        return origen_de(self.headers) in origenes_propios(self.servidor_tel.puerto)

    def _json(self, codigo: int, obj: Any) -> None:
        self._responder(json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8"), "application/json; charset=utf-8", codigo)

    def _sse_cabecera(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

    def _sse(self, evento: str, datos: Any) -> None:
        cuerpo = json.dumps(datos, ensure_ascii=False, default=str)
        self.wfile.write(f"event: {evento}\ndata: {cuerpo}\n\n".encode("utf-8"))
        self.wfile.flush()

    def _sse_comentario(self) -> None:
        self.wfile.write(b": latido\n\n")
        self.wfile.flush()

    def _enviar(self, datos: Dict[str, Any]) -> None:
        self.wfile.write(b"data: " + json.dumps(datos, ensure_ascii=False, default=str).encode("utf-8") + b"\n\n")
        self.wfile.flush()

    def _responder(self, cuerpo: bytes, tipo: str, codigo: int = 200) -> None:
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)


class Telemetria:
    def __init__(self, mundo: str = "", puerto: int = 8000, anfitrion: str = "", modo_antesala: bool = False,
                 datos: Optional[str] = None, instalador: Optional[Instalador] = None):
        """``datos``: raíz de los datos de las vidas lanzadas desde la aplicación (cada mundo en ``<datos>/<mundo>``);
        por defecto, ``datos/<mundo>`` del proyecto. ``instalador``: el de los mundos (O17); en las pruebas, uno con un
        proceso simulado."""
        self.mundo = mundo
        self.activo = True
        self.modo_antesala = modo_antesala
        self.simulacion_activa = bool(mundo and not modo_antesala)
        self.datos = datos
        self.instalador = instalador or Instalador()
        self.ritmo = Regulador("x1")                              # O3: ritmo visible de la vida en curso
        self.ultimo: Optional[Dict[str, Any]] = None             # lo último enviado al panel (forma de antes)
        self.ultimo_registro: Optional[Dict[str, Any]] = None    # el último registro del latido v1
        self._escena: Optional[Dict[str, Any]] = None             # la última escena de la vida (llega solo cuando cambia)
        self._vida_escena: Any = None
        self._vida: Optional[Dict[str, Any]] = None               # la vida lanzada por la API o por /iniciar
        self._vidas = 0
        self._colas: List[queue.Queue] = []
        self._colas_registro: List[queue.Queue] = []
        self.evento_parada = threading.Event()
        self.hilo_simulacion: Optional[threading.Thread] = None
        # Solo en local por defecto; en un contenedor, IDA_TELEMETRIA_HOST=0.0.0.0 (lo pone docker compose).
        anfitrion = anfitrion or os.environ.get("IDA_TELEMETRIA_HOST", "127.0.0.1")
        self._cerrojo = threading.Lock()
        manejador = type("Manejador", (_Manejador,), {"servidor_tel": self})
        servidor: Optional[ThreadingHTTPServer] = None
        for p in (puerto, 8080, 8081, 8888, 0):
            try:
                servidor = ThreadingHTTPServer((anfitrion, p), manejador)
                break
            except OSError:
                continue
        if servidor is None:
            raise OSError("no hay ningún puerto libre para la telemetría")
        self.servidor: ThreadingHTTPServer = servidor
        self.servidor.daemon_threads = True
        self.puerto = self.servidor.server_address[1]
        self.hilo = threading.Thread(target=self.servidor.serve_forever, daemon=True)
        self.hilo.start()
        etiqueta = "aplicación web" if not self.simulacion_activa else "panel"
        print(f"[telemetría] {etiqueta} en http://{'127.0.0.1' if anfitrion == '0.0.0.0' else anfitrion}:{self.puerto}")

    # --- vidas ---------------------------------------------------------------------------------------------------------
    def iniciar_simulacion(self, config: Dict[str, Any]) -> None:
        """``POST /iniciar`` de la antesala antigua (hasta T6): la configuración de antes, con sus valores por defecto."""
        from ida.mundos import cargar

        mundo = config.get("mundo", "minimo")
        opciones = opciones_por_defecto(mundo, config.get("opciones") or {})   # antes del hilo: el error llega a /iniciar
        plazo = config["plazo_logico"] if "plazo_logico" in config else plazo_por_defecto(mundo)
        self.lanzar({
            "mundo": mundo,
            "opciones": opciones,
            "latidos": int(config.get("latidos", 300)),
            "semilla": int(config.get("semilla", 1)),
            "generaciones": int(config.get("generaciones", 1)),
            "sin_experiencia": bool(config.get("sin_experiencia", False)),
            "tabula_rasa": bool(config.get("tabula_rasa", False)),
            "cada": int(config.get("cada", 10)),
            "otel": bool(config.get("otel", False)),
            "arquetipo": config.get("arquetipo"),
            "legado": config.get("legado"),
            "nivel": str(config.get("nivel", NIVEL_ANTESALA)),
            "plazo_logico": None if plazo is None else float(plazo),
            "tiempo_real": bool(cargar(mundo).perfil.tiempo_real),
        })

    def lanzar(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Lanza una vida (para antes la que hubiera) con una configuración ya comprobada (``api_v1.preparar_vida`` o
        ``iniciar_simulacion``). Devuelve la descripción de la vida (``vida_actual``)."""
        from ida.mundos import cargar

        self.detener_simulacion()
        mundo = config["mundo"]
        self.mundo = mundo
        self.ultimo = None
        self.ultimo_registro = None
        self._escena, self._vida_escena = None, None
        self.evento_parada = threading.Event()
        self.ritmo = Regulador("x1")
        self._vidas += 1
        tiempo_real = bool(config["tiempo_real"])
        self._vida = {
            "id": self._vidas, "mundo": mundo, "activa": True, "opciones": dict(config["opciones"]),
            "semilla": config["semilla"], "latidos": config["latidos"], "generaciones": config["generaciones"],
            "arquetipo": config.get("arquetipo"), "con_legado": bool(config.get("legado")),
            "plazo_logico": config["plazo_logico"], "nivel": config["nivel"], "tiempo_real": tiempo_real,
            "frecuencia_ms": float(cargar(mundo).perfil.frecuencia_ms), "ritmo": None if tiempo_real else "x1",
            "ritmo_ajustable": not tiempo_real,
        }
        self.simulacion_activa = True
        evento_parada, regulador = self.evento_parada, self.ritmo
        datos = os.path.join(self.datos, mundo) if self.datos else None

        def _tarea():
            from ida.ejecutor import ejecutar
            try:
                ejecutar(
                    mundo=mundo,
                    latidos=config["latidos"],
                    semilla=config["semilla"],
                    generaciones=config["generaciones"],
                    ver=False,
                    sin_experiencia=bool(config.get("sin_experiencia", False)),
                    tabula_rasa=bool(config.get("tabula_rasa", False)),
                    cada=int(config.get("cada", 10)),
                    datos=datos,
                    opciones_mundo=config["opciones"],
                    telemetria_instancia=self,
                    evento_parada=evento_parada,
                    otel=bool(config.get("otel", False)),
                    arquetipo_inicial=config.get("arquetipo"),
                    legado_inicial=config.get("legado"),
                    nivel=config["nivel"],
                    plazo_logico=config["plazo_logico"],
                    ritmo=regulador,
                )
            except Exception as exc:
                print(f"[telemetría] error en la simulación: {exc}")
                if self._vida is not None:
                    self._vida["error"] = str(exc)
            finally:
                self._fin_de_vida()

        self._difundir_registro("vida", self.vida_actual())   # antes del primer registro: quien sigue la SSE la conoce
        self.hilo_simulacion = threading.Thread(target=_tarea, daemon=True)
        self.hilo_simulacion.start()
        return self.vida_actual() or {}

    def _fin_de_vida(self) -> None:
        with self._cerrojo:
            if self._vida is None or not self._vida["activa"]:
                return
            self._vida["activa"] = False
        self.simulacion_activa = False
        if self.ultimo is not None:
            self._difundir(dict(self.ultimo, simulacion_activa=False, evento="fin_simulacion"))
        self._difundir_registro("fin", self.vida_actual())

    def vida_actual(self) -> Optional[Dict[str, Any]]:
        """La vida lanzada más reciente (en curso o terminada), con su ritmo y el último latido visto; ``None`` si no hay."""
        if self._vida is None:
            return None
        vida = dict(self._vida)
        if vida["ritmo_ajustable"]:
            vida["ritmo"] = self.ritmo.ritmo
        r = self.ultimo_registro
        if r is not None:
            vida.update(latido=r["latido"], vida=r["vida"], generacion=r["generacion"], individuo=r["individuo"])
        return vida

    def fijar_ritmo(self, ritmo: str) -> None:
        self.ritmo.fijar(ritmo)
        self._difundir_registro("ritmo", {"ritmo": ritmo})

    def detener_simulacion(self) -> None:
        """Detiene de forma cooperativa la simulación en curso si la hubiera (también si está en pausa)."""
        self.evento_parada.set()
        self.ritmo.soltar()
        if self.hilo_simulacion is not None and self.hilo_simulacion.is_alive():
            self.hilo_simulacion.join(timeout=5.0)
        self.simulacion_activa = False
        self._fin_de_vida()

    # --- difusión ------------------------------------------------------------------------------------------------------
    def _suscribir(self) -> queue.Queue:
        cola: queue.Queue = queue.Queue(maxsize=200)
        with self._cerrojo:
            self._colas.append(cola)
        return cola

    def _desuscribir(self, cola: queue.Queue) -> None:
        with self._cerrojo:
            if cola in self._colas:
                self._colas.remove(cola)

    def suscribir_registro(self) -> queue.Queue:
        cola: queue.Queue = queue.Queue(maxsize=200)
        with self._cerrojo:
            self._colas_registro.append(cola)
        return cola

    def desuscribir_registro(self, cola: queue.Queue) -> None:
        with self._cerrojo:
            if cola in self._colas_registro:
                self._colas_registro.remove(cola)

    def ultimo_con_escena(self) -> Optional[Dict[str, Any]]:
        """El último registro con la escena vigente (la escena solo llega cuando cambia: quien se conecta tarde la
        necesita para dibujar)."""
        r = self.ultimo_registro
        if r is None or "escena" in r or self._escena is None:
            return r
        return dict(r, escena=self._escena)

    def publicar(self, registro: Dict[str, Any]) -> None:
        """Publica un registro del latido v1 (O2): tal cual por la SSE de la API v1 y, para el panel y la antesala de
        antes, con la forma de antes (``compat.a_panel``, hasta T6). Un diccionario sin ``v`` se difunde tal cual."""
        if registro.get("v") != VERSION:     # forma de antes (compatibilidad hasta T6): se difunde tal cual
            self._difundir(registro)
            return
        if registro.get("vida") != self._vida_escena:
            self._escena, self._vida_escena = None, registro.get("vida")
        if "escena" in registro:
            self._escena = registro["escena"]
        self.ultimo_registro = registro
        self._difundir_registro("registro", registro)
        self._difundir(a_panel(registro))

    @staticmethod
    def _poner(cola: queue.Queue, dato: Any) -> None:
        """No bloquea: si un cliente va lento, se descartan sus eventos más antiguos."""
        try:
            cola.put_nowait(dato)
        except queue.Full:
            try:
                cola.get_nowait()
                cola.put_nowait(dato)
            except (queue.Empty, queue.Full):
                pass

    def _difundir_registro(self, evento: str, dato: Any) -> None:
        with self._cerrojo:
            colas = list(self._colas_registro)
        for c in colas:
            self._poner(c, (evento, dato))

    def _difundir(self, datos: Dict[str, Any]) -> None:
        datos = dict(datos, mundo=self.mundo)
        if "simulacion_activa" not in datos:
            datos["simulacion_activa"] = self.simulacion_activa
        self.ultimo = datos
        with self._cerrojo:
            colas = list(self._colas)
        for c in colas:
            self._poner(c, datos)

    def detener(self) -> None:
        self.detener_simulacion()
        self.activo = False
        self.servidor.shutdown()
        self.servidor.server_close()
