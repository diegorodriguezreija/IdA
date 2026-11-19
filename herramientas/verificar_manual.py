"""Verifica literalmente las citas de los manuales de Crafter (paso 2.1 de la fase de generalización).

- Manual estricto (``ida/mundos/crafter_manual.json``): cada cita debe aparecer en el texto del artículo
  (PDF de arXiv:2109.06780v2, extraído con ``pdftotext``) o en el README de ``danijar/crafter``.
- Manual ampliado (``ida/mundos/crafter_manual_ampliado.json``): cada cita de código debe aparecer en la
  línea que indica su ``lugar`` (``crafter/<fichero>:<línea>``) del paquete ``crafter`` instalado.

La comparación normaliza el texto (NFKC, guiones de corte de línea y espacios), nada más.

    python herramientas/verificar_manual.py --pdf f:/fuentes/crafter.pdf --readme f:/fuentes/README.md

Devuelve 0 si todas las citas se encuentran y 1 si falta alguna (y la lista).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from typing import Any, Dict, List

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESTRICTO = os.path.join(RAIZ, "ida", "mundos", "crafter_manual.json")
AMPLIADO = os.path.join(RAIZ, "ida", "mundos", "crafter_manual_ampliado.json")


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKC", texto)
    texto = re.sub(r"-\s*\n\s*", "", texto)          # palabra cortada a final de línea
    return re.sub(r"\s+", " ", texto).strip()


def texto_pdf(ruta: str) -> str:
    if shutil.which("pdftotext") is None:
        raise SystemExit("Falta pdftotext (poppler) para extraer el texto del PDF.")
    salida = subprocess.run(["pdftotext", "-enc", "UTF-8", ruta, "-"], capture_output=True, check=True)
    return normalizar(salida.stdout.decode("utf-8", errors="replace"))


def verificar_estricto(hechos: List[Dict[str, Any]], articulo: str, readme: str) -> List[str]:
    faltan = []
    for h in hechos:
        cita = normalizar(h["cita"])
        if len(cita.split()) >= 15:
            faltan.append(f"{h['id']}: cita de 15 palabras o más")
        donde = readme if str(h.get("lugar", "")).startswith("README") else articulo
        if cita not in donde:
            faltan.append(f"{h['id']}: no aparece «{h['cita']}» ({h.get('lugar', '')})")
    return faltan


def verificar_codigo(hechos: List[Dict[str, Any]]) -> List[str]:
    import crafter

    base = os.path.dirname(os.path.dirname(crafter.__file__))
    faltan = []
    for h in hechos:
        m = re.fullmatch(r"(crafter/[\w.]+):(\d+)", str(h.get("lugar", "")))
        if m is None:
            faltan.append(f"{h['id']}: lugar sin formato crafter/<fichero>:<línea>")
            continue
        with open(os.path.join(base, m.group(1)), encoding="utf-8") as f:
            lineas = f.read().splitlines()
        linea = normalizar(lineas[int(m.group(2)) - 1]) if int(m.group(2)) <= len(lineas) else ""
        if normalizar(h["cita"]) not in linea:
            faltan.append(f"{h['id']}: «{h['cita']}» no está en {h['lugar']} («{linea}»)")
    return faltan


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--pdf", required=True, help="PDF del artículo (fuera del repositorio)")
    p.add_argument("--readme", required=True, help="README.md de danijar/crafter")
    args = p.parse_args()

    articulo = texto_pdf(args.pdf)
    with open(args.readme, encoding="utf-8") as f:
        readme = normalizar(f.read())
    with open(ESTRICTO, encoding="utf-8") as f:
        estricto = json.load(f)["hechos"]
    with open(AMPLIADO, encoding="utf-8") as f:
        ampliado = json.load(f)["hechos"]

    faltan = verificar_estricto(estricto, articulo, readme) + verificar_codigo(ampliado)
    print(f"estricto: {len(estricto)} hechos; ampliado: {len(ampliado)} hechos de código")
    for linea in faltan:
        print("  FALTA", linea)
    print("OK" if not faltan else f"{len(faltan)} citas sin verificar")
    return 1 if faltan else 0


if __name__ == "__main__":
    sys.exit(main())
