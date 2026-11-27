"""Punto de entrada: ``python -m ida`` (aplicación web, en la antesala) o ``python -m ida --mundo <nombre> [opciones]``."""

import argparse
import os
import sys
import time
import webbrowser

from ida.ejecutor import ejecutar
from ida.mundos import MUNDOS


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(prog="python -m ida", description="IdA – Identidad Artificial")
    p.add_argument("--mundo", required=False, default=None, choices=sorted(MUNDOS),
                   help="mundo a ejecutar (si se omite, abre la aplicación web en la antesala)")
    p.add_argument("--web", action="store_true", help="abre la aplicación web (antesala) en el navegador")
    p.add_argument("--no-navegador", action="store_true",
                   help="arranca el servidor de la aplicación (sin --mundo, o con --ver) sin abrir el navegador")
    p.add_argument("--latidos", type=int, default=300, help="latidos máximos por vida")
    p.add_argument("--semilla", type=int, default=1)
    p.add_argument("--generaciones", type=int, default=1, help="vidas sucesivas del linaje")
    p.add_argument("--ver", action="store_true", help="sigue la vida en la aplicación web (el Vivero, con el Laboratorio a mano)")
    p.add_argument("--otel", action="store_true", help="envía trazas y métricas por OpenTelemetry (extra [observabilidad])")
    p.add_argument("--sin-experiencia", action="store_true", help="apaga las dimensiones activa y proactiva")
    p.add_argument("--tabula-rasa", action="store_true", help="borra el linaje y la memoria del mundo antes de empezar")
    p.add_argument("--cada", type=int, default=1, help="imprimir un latido de cada N (siempre se imprimen los aprendizajes)")
    p.add_argument("--opcion", action="append", default=[], metavar="CLAVE=VALOR", help="opción propia del mundo")
    p.add_argument("--biblioteca", default=None, choices=["nula", "fija", "erronea"], help="biblioteca externa de autoridad")
    p.add_argument("--grabar", default=None, metavar="RUTA", help="graba la vida en RUTA (.jsonl.gz): cabecera y un registro por latido")
    p.add_argument("--datos", default=None, metavar="RUTA",
                   help="directorio de datos del mundo (por defecto, datos/<mundo>); sin --mundo, raíz de los datos de las vidas "
                        "lanzadas desde la aplicación (RUTA/<mundo>)")
    p.add_argument("--nivel", default=None, choices=["vital", "cognitivo", "completo"],
                   help="nivel del registro del latido (por defecto, cognitivo; completo con --ver o --otel)")
    p.add_argument("--plazo-logico", type=float, default=None, metavar="OPS",
                   help="plazo lógico de la guillotina: OPS operaciones por ms (vidas reproducibles); por defecto, reloj")
    a = p.parse_args(argv)

    if a.mundo is None or a.web:
        from ida.telemetria.servidor import Telemetria
        tel = Telemetria(modo_antesala=True, datos=a.datos)
        url = f"http://127.0.0.1:{tel.puerto}/#/antesala"
        if not a.no_navegador:
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

    from ida.mundos import cargar
    from ida.mundos.opciones import OpcionInvalida, convertir

    opciones = {}
    for o in a.opcion:
        clave, _, valor = o.partition("=")
        opciones[clave] = int(valor) if valor.isdigit() else valor
    try:
        convertir(cargar(a.mundo).opciones(), opciones, a.mundo)   # O8: se comprueba antes de crear nada
    except OpcionInvalida as e:
        p.error(str(e))
    nivel = a.nivel or ("completo" if a.ver or a.otel else "cognitivo")
    argumentos = {
        "mundo": a.mundo, "latidos": a.latidos, "semilla": a.semilla, "generaciones": a.generaciones, "sin_experiencia": a.sin_experiencia,
        "tabula_rasa": a.tabula_rasa, "cada": a.cada, "opciones_mundo": opciones, "otel": a.otel, "biblioteca": a.biblioteca, "nivel": nivel,
        "grabar": a.grabar, "plazo_logico": a.plazo_logico, "datos": a.datos,
    }
    if not a.ver:
        ejecutar(**argumentos)
        return 0
    return _ver(a, opciones, argumentos)


def _ver(a: argparse.Namespace, opciones: dict, argumentos: dict) -> int:
    """``--ver``: la vida corre aquí y la aplicación web la sigue en el Vivero (T6a). Al terminar, el servidor sigue
    abierto para mirarla en el Laboratorio hasta Ctrl+C."""
    from ida.mundos import cargar
    from ida.mundos.opciones import con_defectos
    from ida.telemetria.servidor import Telemetria

    clase = cargar(a.mundo)
    raiz = None   # la raíz de los datos del Vivero: la de siempre, o la carpeta que contiene la de --datos si es «<raíz>/<mundo>»
    if a.datos and os.path.basename(os.path.normpath(a.datos)) == a.mundo:
        raiz = os.path.dirname(os.path.normpath(a.datos)) or "."
    tel = Telemetria(mundo=a.mundo, datos=raiz)
    tel.acompanar({
        "mundo": a.mundo, "opciones": con_defectos(clase.opciones(), opciones, a.mundo), "semilla": a.semilla,
        "latidos": a.latidos, "generaciones": a.generaciones, "arquetipo": None, "legado": None,
        "plazo_logico": a.plazo_logico, "nivel": argumentos["nivel"], "tiempo_real": bool(clase.perfil.tiempo_real),
        "sin_experiencia": a.sin_experiencia,
    })
    url = f"http://127.0.0.1:{tel.puerto}/#/vivero"
    print(f"[ver] La vida se sigue en {url}")
    if not a.no_navegador:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        ejecutar(**argumentos, telemetria_instancia=tel, ritmo=tel.ritmo, evento_parada=tel.evento_parada)
    finally:
        tel.fin_acompanada()
    print(f"[ver] La vida ha terminado; sigue en {url} (y en el Laboratorio). Pulsa Ctrl+C para salir.")
    try:
        while tel.activo:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    tel.detener()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
