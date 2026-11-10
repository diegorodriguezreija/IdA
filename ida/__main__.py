"""Punto de entrada: ``python -m ida`` (antesala web) o ``python -m ida --mundo <nombre> [opciones]``."""

import argparse
import sys
import time
import webbrowser

from ida.ejecutor import ejecutar
from ida.mundos import MUNDOS


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(prog="python -m ida", description="IdA – Identidad Artificial")
    p.add_argument("--mundo", required=False, default=None, choices=sorted(MUNDOS), help="mundo a ejecutar (si se omite, abre la antesala web)")
    p.add_argument("--web", action="store_true", help="abre la antesala interactiva en el navegador")
    p.add_argument("--latidos", type=int, default=300, help="latidos máximos por vida")
    p.add_argument("--semilla", type=int, default=1)
    p.add_argument("--generaciones", type=int, default=1, help="vidas sucesivas del linaje")
    p.add_argument("--ver", action="store_true", help="panel de telemetría en el navegador")
    p.add_argument("--otel", action="store_true", help="envía trazas y métricas por OpenTelemetry (extra [observabilidad])")
    p.add_argument("--sin-experiencia", action="store_true", help="apaga las dimensiones activa y proactiva")
    p.add_argument("--tabula-rasa", action="store_true", help="borra el linaje y la memoria del mundo antes de empezar")
    p.add_argument("--cada", type=int, default=1, help="imprimir un latido de cada N (siempre se imprimen los aprendizajes)")
    p.add_argument("--opcion", action="append", default=[], metavar="CLAVE=VALOR", help="opción propia del mundo")
    a = p.parse_args(argv)

    if a.mundo is None or a.web:
        from ida.telemetria.servidor import Telemetria
        tel = Telemetria(modo_antesala=True)
        url = f"http://127.0.0.1:{tel.puerto}"
        try:
            webbrowser.open(url)
        except Exception:
            pass
        print(f"\n[antesala] Servidor interactivo listo en {url}")
        print("[antesala] Elige mundo y parámetros en el navegador. Pulsa Ctrl+C para salir.\n")
        try:
            while tel.activo:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n[antesala] Deteniendo servidor...")
            tel.detener()
        return 0

    opciones = {}
    for o in a.opcion:
        clave, _, valor = o.partition("=")
        opciones[clave] = int(valor) if valor.isdigit() else valor
    ejecutar(a.mundo, a.latidos, a.semilla, a.generaciones, a.ver, a.sin_experiencia, a.tabula_rasa, cada=a.cada, opciones_mundo=opciones, otel=a.otel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
