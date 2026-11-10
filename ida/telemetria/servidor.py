"""Servidor de telemetría en un hilo aparte. Publicar no bloquea el latido.

Rutas:
- ``/``         panel HTML
- ``/eventos``  flujo SSE con un resumen por latido
- ``/estado``   último resumen en JSON
"""

import json
import os
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional

PANEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "panel.html")


class _Manejador(BaseHTTPRequestHandler):
    servidor_tel: "Telemetria" = None  # type: ignore

    def log_message(self, *args) -> None:   # silencio en consola
        pass

    def do_GET(self) -> None:
        tel = self.servidor_tel
        if self.path.startswith("/eventos"):
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
        elif self.path.startswith("/estado"):
            self._responder(json.dumps(tel.ultimo or {}, ensure_ascii=False, default=str).encode("utf-8"), "application/json")
        else:
            with open(PANEL, "rb") as f:
                self._responder(f.read(), "text/html; charset=utf-8")

    def _enviar(self, datos: Dict[str, Any]) -> None:
        self.wfile.write(b"data: " + json.dumps(datos, ensure_ascii=False, default=str).encode("utf-8") + b"\n\n")
        self.wfile.flush()

    def _responder(self, cuerpo: bytes, tipo: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)


class Telemetria:
    def __init__(self, mundo: str = "", puerto: int = 8000, anfitrion: str = ""):
        self.mundo = mundo
        self.activo = True
        self.ultimo: Optional[Dict[str, Any]] = None
        self._colas: List[queue.Queue] = []
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
        print(f"[telemetría] panel en http://{'127.0.0.1' if anfitrion == '0.0.0.0' else anfitrion}:{self.puerto}")

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
        self.activo = False
        self.servidor.shutdown()
        self.servidor.server_close()
