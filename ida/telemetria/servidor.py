"""Servidor de telemetría y antesala web en un hilo aparte.

Rutas:
- ``/``                  antesala (si no hay simulación) o panel en vivo (si la hay)
- ``/antesala``          antesala interactiva para configurar y lanzar mundos
- ``/panel``             panel HTML de telemetría
- ``/eventos``            flujo SSE con un resumen por latido
- ``/estado``             último resumen en JSON
- ``/estado_simulacion``  estado de ejecución del organismo
- ``POST /iniciar``       inicia una simulación con parámetros
- ``POST /detener``       detiene la simulación activa
"""

import json
import os
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional

PANEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "panel.html")
ANTESALA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "antesala.html")


class _Manejador(BaseHTTPRequestHandler):
    servidor_tel: "Telemetria" = None  # type: ignore

    def log_message(self, *args) -> None:   # silencio en consola
        pass

    def do_GET(self) -> None:
        tel = self.servidor_tel
        ruta = self.path.split("?")[0]
        if ruta == "/eventos":
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
        elif ruta == "/antesala":
            with open(ANTESALA, "rb") as f:
                self._responder(f.read(), "text/html; charset=utf-8")
        elif ruta == "/panel":
            with open(PANEL, "rb") as f:
                self._responder(f.read(), "text/html; charset=utf-8")
        else:
            # En la raíz (/), si hay simulación activa muestra el panel; si no, la antesala
            archivo = PANEL if tel.simulacion_activa else ANTESALA
            with open(archivo, "rb") as f:
                self._responder(f.read(), "text/html; charset=utf-8")

    def do_POST(self) -> None:
        tel = self.servidor_tel
        ruta = self.path.split("?")[0]
        longitud = int(self.headers.get("Content-Length", 0))
        cuerpo = self.rfile.read(longitud).decode("utf-8") if longitud > 0 else "{}"
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
        else:
            self.send_error(404, "Ruta no encontrada")

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
    def __init__(self, mundo: str = "", puerto: int = 8000, anfitrion: str = "", modo_antesala: bool = False):
        self.mundo = mundo
        self.activo = True
        self.simulacion_activa = bool(mundo and not modo_antesala)
        self.ultimo: Optional[Dict[str, Any]] = None
        self._colas: List[queue.Queue] = []
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
        etiqueta = "antesala web" if not self.simulacion_activa else "panel"
        print(f"[telemetría] {etiqueta} en http://{'127.0.0.1' if anfitrion == '0.0.0.0' else anfitrion}:{self.puerto}")

    def iniciar_simulacion(self, config: Dict[str, Any]) -> None:
        """Inicia una simulación en un hilo en segundo plano reutilizando este servidor de telemetría."""
        self.detener_simulacion()
        mundo = config.get("mundo", "minimo")
        self.mundo = mundo
        self.ultimo = None
        self.evento_parada.clear()
        self.simulacion_activa = True

        def _tarea():
            from ida.ejecutor import ejecutar
            try:
                ejecutar(
                    mundo=mundo,
                    latidos=int(config.get("latidos", 300)),
                    semilla=int(config.get("semilla", 1)),
                    generaciones=int(config.get("generaciones", 1)),
                    ver=False,
                    sin_experiencia=bool(config.get("sin_experiencia", False)),
                    tabula_rasa=bool(config.get("tabula_rasa", False)),
                    cada=int(config.get("cada", 10)),
                    opciones_mundo=config.get("opciones", {}),
                    telemetria_instancia=self,
                    evento_parada=self.evento_parada,
                )
            except Exception as exc:
                print(f"[telemetría] error en la simulación: {exc}")

        self.hilo_simulacion = threading.Thread(target=_tarea, daemon=True)
        self.hilo_simulacion.start()

    def detener_simulacion(self) -> None:
        """Detiene de forma cooperativa la simulación en curso si la hubiera."""
        self.evento_parada.set()
        if self.hilo_simulacion is not None and self.hilo_simulacion.is_alive():
            self.hilo_simulacion.join(timeout=2.0)
        self.simulacion_activa = False

    def _suscribir(self) -> queue.Queue:
        cola: queue.Queue = queue.Queue(maxsize=200)
        with self._cerrojo:
            self._colas.append(cola)
        return cola

    def _desuscribir(self, cola: queue.Queue) -> None:
        with self._cerrojo:
            if cola in self._colas:
                self._colas.remove(cola)

    def publicar(self, datos: Dict[str, Any]) -> None:
        """No bloquea: si un cliente va lento, se descartan sus eventos más antiguos."""
        datos = dict(datos, mundo=self.mundo)
        self.ultimo = datos
        with self._cerrojo:
            colas = list(self._colas)
        for c in colas:
            try:
                c.put_nowait(datos)
            except queue.Full:
                try:
                    c.get_nowait()
                    c.put_nowait(datos)
                except (queue.Empty, queue.Full):
                    pass

    def detener(self) -> None:
        self.detener_simulacion()
        self.activo = False
        self.servidor.shutdown()
        self.servidor.server_close()
