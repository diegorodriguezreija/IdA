"""Servidor de la aplicación web y de la telemetría, en un hilo aparte (O14). Solo biblioteca estándar.

Escucha en ``127.0.0.1`` (en un contenedor, ``IDA_TELEMETRIA_HOST``). Los POST solo se aceptan si su cabecera
``Origin`` (o, si falta, ``Referer``) es la del propio servidor; si no, 403.

Rutas:
- ``/``              aplicación (``web/index.html``: antesala, Vivero y Laboratorio)
- ``/api/v1/...``    API v1 (``ida/telemetria/api_v1.py``): mundos, instalación, presets, vidas, ritmo, SSE, Vivero y
                     Laboratorio
- ``/escena``        visor de comprobación de ``escena()`` (T2a): dibuja una grabación cargada en el navegador
- ``/web/<ruta>``    ficheros estáticos de ``ida/telemetria/web/`` (solo esa carpeta y tipos conocidos)

El panel y la antesala de antes, su API sin versión (``/eventos``, ``/estado``, ``/iniciar``...) y las rutas del linaje
del panel se retiraron en T6a: cualquier otra ruta da 404.
"""

import json
import os
import queue
import threading
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote, urlparse

from ida.telemetria import api_v1
from ida.telemetria.esquema import VERSION
from ida.telemetria.grabacion import cabecera, commit_actual
from ida.telemetria.instalador import Instalador
from ida.telemetria.laboratorio import Laboratorio
from ida.telemetria.ritmo import RITMOS, Regulador
from ida.telemetria.vivero import Vivero

DIARIO_MAX = 400                # hechos recientes de la vida en curso que se reenvían a quien se conecta tarde


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
        ruta = urlparse(self.path).path
        if ruta.startswith(api_v1.PREFIJO):
            api_v1.atender(self, "GET")
        elif ruta == "/escena" or ruta.startswith("/web/"):
            destino = fichero_web("escena.html" if ruta == "/escena" else ruta[len("/web/"):])
            if destino is None:
                self.send_error(404, "Fichero no encontrado")
                return
            with open(destino, "rb") as f:
                self._responder(f.read(), TIPOS_WEB[os.path.splitext(destino)[1].lower()])
        elif ruta in ("/", "/index.html"):
            with open(APLICACION, "rb") as f:
                self._responder(f.read(), "text/html; charset=utf-8")
        else:
            self.send_error(404, "Ruta no encontrada")

    def do_POST(self) -> None:
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
        self.modo_antesala = modo_antesala   # solo cambia el texto de arranque: la ruta ``/`` es siempre la aplicación
        self.simulacion_activa = False
        self.datos = datos
        from ida.ejecutor import DATOS
        self.vivero = Vivero(datos or DATOS)                      # T4b: compañeros y colección (sección 13)
        self.lab = Laboratorio(datos or DATOS)                    # T5a: directo en memoria, grabar y grabaciones
        self.instalador = instalador or Instalador()
        self.ritmo = Regulador("comodo")                          # O3, O20: ritmo visible de la vida en curso
        self._diario: deque = deque(maxlen=DIARIO_MAX)            # hechos recientes de la vida en curso (con su latido)
        self._requisitos: Dict[Tuple[Any, Any, Any], Dict[str, Any]] = {}   # el último «aprende requisito» de cada acción
        self._reparto: Dict[str, Any] = {"vida": None, "cuenta": {}}   # sistema de cada acción de la vida (desde su inicio)
        self.ultimo_registro: Optional[Dict[str, Any]] = None    # el último registro del latido v1
        self._escena: Optional[Dict[str, Any]] = None             # la última escena de la vida (llega solo cuando cambia)
        self._vida_escena: Any = None
        self._vida: Optional[Dict[str, Any]] = None               # la vida lanzada por la API o seguida desde la CLI
        self._vidas = 0
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
        print(f"[telemetría] aplicación web en http://{'127.0.0.1' if anfitrion == '0.0.0.0' else anfitrion}:{self.puerto}")

    # --- vidas ---------------------------------------------------------------------------------------------------------
    def lanzar(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Lanza una vida (para antes la que hubiera) con una configuración ya comprobada (``api_v1.preparar_vida``).
        Devuelve la descripción de la vida (``vida_actual``)."""
        self.detener_simulacion()
        mundo = config["mundo"]
        archivada = None
        if config.get("tabula_rasa"):
            # T4b: desde la aplicación, «Empezar de cero» archiva la estirpe en la colección; nunca la borra. Solo la CLI
            # (``--tabula-rasa``) conserva su conducta de siempre. La vida anterior ya está parada.
            archivada = self.vivero.archivar(mundo, motivo="empezar_de_cero")
        self._preparar(config, archivada)
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
                    sin_experiencia=bool(config.get("sin_experiencia", False)),
                    tabula_rasa=False,   # ya archivada arriba (T4b): la aplicación nunca borra la estirpe
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

    def acompanar(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Describe una vida que corre fuera del servidor (``python -m ida --mundo M --ver``, T6a): el Vivero y el
        Laboratorio la siguen como una lanzada desde la aplicación. Quien la corre pasa ``telemetria_instancia=self``,
        ``ritmo=self.ritmo`` y ``evento_parada=self.evento_parada`` a ``ejecutar`` y llama a ``fin_acompanada`` al
        acabar. ``config`` lleva lo mismo que ``lanzar`` (``tabula_rasa`` no se atiende aquí: la CLI la aplica a su
        manera, antes de empezar)."""
        self.detener_simulacion()
        self._preparar(config, None)
        if self._vida is not None:
            self._vida["origen"] = "cli"
        self._difundir_registro("vida", self.vida_actual())
        return self.vida_actual() or {}

    def fin_acompanada(self) -> None:
        """La vida seguida con ``acompanar`` ha terminado (o se ha parado desde la aplicación)."""
        self._fin_de_vida()

    def _preparar(self, config: Dict[str, Any], archivada: Optional[Dict[str, Any]]) -> None:
        """El estado de una vida nueva: ritmo, diario, directo del Laboratorio y su descripción (``vida_actual``)."""
        from ida.mundos import cargar

        mundo = config["mundo"]
        self.mundo = mundo
        self.ultimo_registro = None
        self._escena, self._vida_escena = None, None
        self.evento_parada = threading.Event()
        comodo = config.get("ritmo_comodo_ms")   # O20; sin él (la CLI con --ver), el plazo del Perfil, como antes
        self.ritmo = Regulador("comodo", comodo)
        self._diario.clear()
        self._requisitos.clear()
        self._reparto = {"vida": None, "cuenta": {}}
        self._vidas += 1
        tiempo_real = bool(config["tiempo_real"])
        frecuencia = float(cargar(mundo).perfil.frecuencia_ms)
        self._vida = {
            "id": self._vidas, "mundo": mundo, "activa": True, "opciones": dict(config["opciones"]),
            "semilla": config["semilla"], "latidos": config["latidos"], "generaciones": config["generaciones"],
            "arquetipo": config.get("arquetipo"), "con_legado": bool(config.get("legado")),
            "plazo_logico": config["plazo_logico"], "nivel": config["nivel"], "tiempo_real": tiempo_real,
            "frecuencia_ms": frecuencia, "ritmo": None if tiempo_real else "comodo",
            "ritmo_ajustable": not tiempo_real, "ritmos": [] if tiempo_real else list(RITMOS),
            "ritmo_comodo_ms": None if tiempo_real else (frecuencia if comodo is None else float(comodo)),
            "archivada": archivada["id"] if archivada else None,
            "sin_experiencia": bool(config.get("sin_experiencia", False)),
        }
        self.lab.nueva_vida(self._vidas, mundo)   # T5a: el directo del Laboratorio empieza con esta vida
        if config.get("grabar"):
            self.grabar()                          # T5a: grabar desde el primer latido
        self.simulacion_activa = True

    def _fin_de_vida(self) -> None:
        with self._cerrojo:
            if self._vida is None or not self._vida["activa"]:
                return
            self._vida["activa"] = False
        self.simulacion_activa = False
        self.lab.terminar(esperar=False)   # T5a: la grabación se cierra tras escribir el último registro (el de cierre)
        self._difundir_registro("fin", self.vida_actual())

    def vida_de(self, mundo: str) -> bool:
        """¿Hay una vida en marcha en ``mundo``? (escribe en los ficheros de su compañero)."""
        v = self._vida
        return bool(v is not None and v["activa"] and v["mundo"] == mundo and self.simulacion_activa)

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
        vida["grabacion"] = self.lab.grabando() if vida["activa"] else None
        return vida

    def grabar(self) -> Dict[str, Any]:
        """Empieza a grabar la vida en curso (T5a, O7): desde el latido siguiente al último publicado (o desde el primero,
        si aún no ha latido), en ``<datos>/grabaciones/<mundo>-<fecha>.jsonl.gz``, al nivel de la vida."""
        v = self._vida
        if v is None:
            raise ValueError("sin vida")
        r = self.ultimo_registro
        cab = cabecera(v["mundo"], v["nivel"], v["semilla"], v["latidos"], v["generaciones"], v["opciones"], v.get("arquetipo"),
                       v["plazo_logico"], bool(v.get("sin_experiencia")), commit_actual())
        cab["origen"] = "vivero"
        cab["empieza_tras"] = None if r is None else {"vida": r.get("vida"), "latido": r.get("latido")}
        return self.lab.empezar(v["mundo"], cab)

    def fijar_ritmo(self, ritmo: str) -> str:
        """Fija el ritmo (``x1`` se admite como ``comodo``) y lo difunde; devuelve el nombre canónico."""
        canonico = self.ritmo.fijar(ritmo)
        self._difundir_registro("ritmo", {"ritmo": canonico})
        return canonico

    def paso(self) -> Dict[str, Any]:
        """«Paso a paso» (O20): en pausa, deja pasar un latido. ``ValueError`` si la vida no está en pausa."""
        pendientes = self.ritmo.paso()
        r = self.ultimo_registro
        return {"ritmo": self.ritmo.ritmo, "pendientes": pendientes, "latido": None if r is None else r["latido"]}

    def diario(self) -> Dict[str, Any]:
        """Los hechos recientes de la vida en curso (cada uno con ``latido``, ``vida`` y ``generacion``) y el último
        «aprende requisito» de cada acción: lo que necesita quien se conecta tarde para el diario y «Lo que sabe»; y el
        reparto entre sistemas de las acciones de la vida en curso desde su inicio (T4b). ``hasta`` es el último registro
        que ya cuentan (``vida``, ``latido``, ``cierre``): el Vivero no vuelve a sumar ese registro cuando le llega."""
        with self._cerrojo:
            r = self.ultimo_registro
            hasta = None if r is None else {"vida": r.get("vida"), "latido": r.get("latido"), "cierre": bool(r.get("cierre"))}
            return {"hechos": list(self._diario), "requisitos": list(self._requisitos.values()),
                    "reparto": {"vida": self._reparto["vida"], "cuenta": dict(self._reparto["cuenta"])}, "hasta": hasta}

    def detener_simulacion(self) -> None:
        """Detiene de forma cooperativa la simulación en curso si la hubiera (también si está en pausa)."""
        self.evento_parada.set()
        self.ritmo.soltar()
        if self.hilo_simulacion is not None and self.hilo_simulacion.is_alive():
            self.hilo_simulacion.join(timeout=5.0)
        self.simulacion_activa = False
        self._fin_de_vida()

    # --- difusión ------------------------------------------------------------------------------------------------------
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
        """Publica un registro del latido v1 (O2) por la SSE de la API v1, el directo del Laboratorio y el diario. No
        bloquea: el hilo de la vida sigue aunque no haya nadie conectado o un cliente vaya lento. ``ValueError`` si no es
        un registro v1 (desde T6a no hay otra forma)."""
        if registro.get("v") != VERSION:
            raise ValueError(f"se esperaba un registro del latido v{VERSION}, hay v={registro.get('v')!r}")
        if registro.get("vida") != self._vida_escena:
            self._escena, self._vida_escena = None, registro.get("vida")
        if "escena" in registro:
            self._escena = registro["escena"]
        self.lab.poner(registro)     # T5a: al directo del Laboratorio y, si se graba, a la grabación (otro hilo)
        hechos = registro.get("hechos") or []
        accion = registro.get("accion")
        marca = {"latido": registro.get("latido"), "vida": registro.get("vida"), "generacion": registro.get("generacion")}
        if registro.get("cierre"):
            marca["cierre"] = True   # T4b: lo aprendido al morir
        with self._cerrojo:          # el registro, su reparto y sus hechos entran juntos (``diario().hasta`` cuadra)
            self.ultimo_registro = registro
            if not registro.get("cierre") and isinstance(accion, dict) and accion.get("sistema"):
                if self._reparto["vida"] != registro.get("vida"):
                    self._reparto = {"vida": registro.get("vida"), "cuenta": {}}
                cuenta = self._reparto["cuenta"]
                cuenta[accion["sistema"]] = cuenta.get(accion["sistema"], 0) + 1
            for h in hechos:
                h2 = dict(h, **marca)
                self._diario.append(h2)
                if h.get("tipo") == "aprende" and h.get("saber") == "requisito":
                    self._requisitos[(registro.get("vida"), h.get("verbo"), h.get("clase"))] = h2
        self._difundir_registro("registro", registro)

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

    def detener(self) -> None:
        self.detener_simulacion()
        self.lab.cerrar()
        self.activo = False
        self.servidor.shutdown()
        self.servidor.server_close()
