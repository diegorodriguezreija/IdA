"""Punto de entrada: ``python -m ida --mundo <nombre> [opciones]``."""

import argparse
import sys

from ida.ejecutor import ejecutar
from ida.mundos import MUNDOS


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(prog="python -m ida", description="IdA – Identidad Artificial")
    p.add_argument("--mundo", required=True, choices=sorted(MUNDOS))
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
    opciones = {}
    for o in a.opcion:
        clave, _, valor = o.partition("=")
        opciones[clave] = int(valor) if valor.isdigit() else valor
    ejecutar(a.mundo, a.latidos, a.semilla, a.generaciones, a.ver, a.sin_experiencia, a.tabula_rasa, cada=a.cada, opciones_mundo=opciones, otel=a.otel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
