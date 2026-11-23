"""Mapa de Componentes: valida la especificación y genera su documento.

La especificación es ``doc-repositorio/componentes.toml`` (dónde debe vivir cada Componente y dónde
está hoy). Esta herramienta:

- valida sus campos y que cada decisión citada exista en ``docs/DISENO_COMPONENTES.md``;
- genera ``doc-repositorio/06_MAPA_DE_COMPONENTES.md`` (``--escribir``) o comprueba que está al día
  (``--comprobar``, el modo por defecto).

El test ``tests/test_mapa_componentes.py`` usa este módulo y además comprueba que el código montado
coincide con «hoy» en cada mundo.

Uso: ``.venv\\Scripts\\python.exe herramientas/mapa_componentes.py [--escribir | --comprobar]``
"""

from __future__ import annotations

import os
import re
import sys
import tomllib
from collections import Counter
from typing import Any, Dict, List, Set

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESPEC = os.path.join(RAIZ, "doc-repositorio", "componentes.toml")
DOC = os.path.join(RAIZ, "doc-repositorio", "06_MAPA_DE_COMPONENTES.md")
DISENO = os.path.join(RAIZ, "docs", "DISENO_COMPONENTES.md")

TIPOS = {"componente", "estrategia", "biblioteca"}
CLASES = {"general", "opcional", "cuerpo", "mundo"}
PASOS = {"R0", "A1", "A2", "A3", "A4", "A5", "A5a", "A5b", "A6", "A7", "A8", "B1", "B2", "B3", "B4"}
MODULOS = ("Sentir", "Interpretar", "Reaccionar", "Actuar")
UBICACIONES = (
    ["CORE.Sentir", "CORE.Regulacion", "CORE.Actuar"]
    + [f"{s}.{m}" for s in ("S1", "S2", "S3") for m in MODULOS]
)
# Orden del latido para el documento (D1): Core · Sentir, preatención, regulación, S1, S2, S3, Core · Actuar.
ORDEN = ["CORE.Sentir", "PREATENCION", "CORE.Regulacion"] + [f"{s}.{m}" for s in ("S1", "S2", "S3") for m in MODULOS] + ["CORE.Actuar", "cuerpo"]
TITULOS = {
    "CORE.Sentir": "2 · Core · Sentir (en bruto)",
    "PREATENCION": "3 · Preatención (S1 · Sentir, no paga atención, también dormido)",
    "CORE.Regulacion": "5 · Regulación de la Onda (Core)",
    "CORE.Actuar": "7 · Core · Actuar",
    "cuerpo": "Bibliotecas de los cuerpos",
}
CAMPOS = ("nombre", "tipo", "clase", "dueno", "destino", "hoy", "hoy_en", "registran", "sustituye", "paso", "decision", "preatentivo", "aprende", "nota")


def cargar(ruta: str = ESPEC) -> List[Dict[str, Any]]:
    with open(ruta, "rb") as f:
        return list(tomllib.load(f)["componente"])


def objetivo_en(c: Dict[str, Any]) -> Any:
    """En qué mundos debe montarse al llegar a su destino."""
    if c["clase"] == "general":
        return "todos"
    if c["clase"] == "mundo":
        return [c["dueno"]]
    return list(c.get("registran", []))


def hoy_en(c: Dict[str, Any]) -> Any:
    """En qué mundos se monta hoy."""
    if "hoy_en" in c:
        return c["hoy_en"]
    return [c["dueno"]] if c["clase"] == "mundo" else "todos"


def pendiente(c: Dict[str, Any]) -> bool:
    return bool(c["hoy"] != c["destino"] or hoy_en(c) != objetivo_en(c))


def decisiones_existentes(ruta: str = DISENO) -> Set[str]:
    with open(ruta, encoding="utf-8") as f:
        texto = f.read()
    return set(re.findall(r"^### (D\d+)\.", texto, flags=re.MULTILINE)) | {"D1"}


def validar(espec: List[Dict[str, Any]], decisiones: Set[str]) -> List[str]:
    """Errores de la especificación (lista vacía si es válida)."""
    errores: List[str] = []
    vistos: Counter[tuple[str, str, str]] = Counter()
    for c in espec:
        n = c.get("nombre", "?")
        for k in c:
            if k not in CAMPOS:
                errores.append(f"{n}: campo desconocido «{k}»")
        for k in ("nombre", "tipo", "clase", "destino", "hoy", "decision"):
            if k not in c:
                errores.append(f"{n}: falta «{k}»")
        if errores:
            continue
        if c["tipo"] not in TIPOS:
            errores.append(f"{n}: tipo «{c['tipo']}» no válido")
        if c["clase"] not in CLASES:
            errores.append(f"{n}: clase «{c['clase']}» no válida")
        if c["clase"] in ("mundo", "cuerpo") and not c.get("dueno"):
            errores.append(f"{n}: un Componente de {c['clase']} necesita «dueno»")
        if c["clase"] in ("opcional", "cuerpo") and not c.get("registran"):
            errores.append(f"{n}: un Componente {c['clase']} necesita «registran»")
        destinos = UBICACIONES + (["cuerpo"] if c["tipo"] == "biblioteca" else [])
        if c["destino"] not in destinos:
            errores.append(f"{n}: destino «{c['destino']}» no válido")
        if c["tipo"] == "estrategia" and not c["destino"].endswith(".Reaccionar"):
            errores.append(f"{n}: una estrategia vive en Reaccionar")
        hoy = c["hoy"]
        if hoy and not hoy.startswith("fuera:") and hoy not in UBICACIONES + (["cuerpo"] if c["tipo"] == "biblioteca" else []):
            errores.append(f"{n}: hoy «{hoy}» no válido")
        if hoy.startswith("fuera:") and not os.path.exists(os.path.join(RAIZ, hoy[len("fuera:"):])):
            errores.append(f"{n}: el fichero de «{hoy}» no existe")
        if c.get("preatentivo") and c["destino"] != "S1.Sentir":
            errores.append(f"{n}: la preatención vive en S1.Sentir (D5)")
        dec = c["decision"]
        if dec != "previo" and dec not in decisiones:
            errores.append(f"{n}: la decisión «{dec}» no existe en docs/DISENO_COMPONENTES.md")
        if pendiente(c) and c.get("paso") not in PASOS:
            errores.append(f"{n}: está pendiente de llevar a su destino y necesita un «paso» del plan")
        if not pendiente(c) and c.get("paso"):
            errores.append(f"{n}: ya está en su destino; quita «paso»")
        vistos[(n, c["destino"], str(c.get("dueno", "")))] += 1
    for (nombre, destino, dueno), veces in vistos.items():
        if veces > 1:
            errores.append(f"{nombre}: repetido en {destino} ({dueno or 'general'})")
    return errores


def _seccion(c: Dict[str, Any]) -> str:
    return "PREATENCION" if c.get("preatentivo") else str(c["destino"])


def _celda_hoy(c: Dict[str, Any]) -> str:
    hoy = c["hoy"] or "(no existe)"
    if hoy.startswith("fuera:"):
        hoy = f"fuera: `{hoy[len('fuera:'):]}`"
    en = hoy_en(c)
    if c["hoy"] in UBICACIONES and en != objetivo_en(c):
        hoy += f" · en {en if isinstance(en, str) else ', '.join(en)}"
    return hoy


def _clase(c: Dict[str, Any]) -> str:
    if c["clase"] in ("mundo", "cuerpo"):
        return f"{c['clase']}: {c['dueno']}"
    if c["clase"] == "opcional":
        return f"opcional ({', '.join(c['registran'])})"
    return "general"


def generar(espec: List[Dict[str, Any]]) -> str:
    """El documento Markdown, determinista."""
    pend = [c for c in espec if pendiente(c)]
    por_paso = Counter(str(c["paso"]) for c in pend)
    lineas = [
        "# Mapa de Componentes",
        "",
        "> **Generado** por `herramientas/mapa_componentes.py --escribir` desde [`componentes.toml`](componentes.toml). No se edita a mano.",
        "> Diseño y decisiones: [`docs/DISENO_COMPONENTES.md`](../docs/DISENO_COMPONENTES.md).",
        "",
        "Cada fila es un Componente, una estrategia o una biblioteca de un cuerpo, en el orden del latido. "
        "**Destino** es dónde debe vivir; **Hoy**, dónde está en el código (lo comprueba `tests/test_mapa_componentes.py`). "
        "Si no coinciden, **Paso** dice qué paso del plan lo lleva a su destino.",
        "",
        f"**Total:** {len(espec)} · **en su destino:** {len(espec) - len(pend)} · **pendientes:** {len(pend)}"
        + (" (" + ", ".join(f"{p}: {k}" for p, k in sorted(por_paso.items())) + ")" if pend else ""),
        "",
        "**Clase:** general (todos los mundos) · opcional (general, pero solo lo monta quien lo registra) · "
        "cuerpo (familia de cuerpos) · mundo (propio de un mundo).",
        "",
    ]
    for sec in ORDEN:
        filas = [c for c in espec if _seccion(c) == sec]
        if not filas:
            continue
        titulo = TITULOS.get(sec, sec.replace(".", " · "))
        lineas += [f"## {titulo}", "", "| Componente | Tipo | Clase | Hoy | Paso | Decisión | Nota |", "|---|---|---|---|---|---|---|"]
        for c in filas:
            marca = " ✱" if c.get("aprende") else ""
            lineas.append(
                f"| `{c['nombre']}`{marca} | {c['tipo']} | {_clase(c)} | {_celda_hoy(c) if pendiente(c) else '✓'} | "
                f"{c.get('paso', '')} | {c['decision']} | {c.get('nota', '')}"
                + (f" Sustituye a `{c['sustituye']}`." if c.get("sustituye") else "")
                + " |"
            )
        lineas.append("")
    lineas += ["✱ Tiene plasticidad: aprende en el paso 4 del latido (D6).", ""]
    return "\n".join(lineas)


def main(argv: List[str]) -> int:
    espec = cargar()
    errores = validar(espec, decisiones_existentes())
    if errores:
        print("La especificación tiene errores:")
        for e in errores:
            print(f"  - {e}")
        return 1
    texto = generar(espec)
    if "--escribir" in argv:
        with open(DOC, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        print(f"Escrito {os.path.relpath(DOC, RAIZ)}")
        return 0
    actual = open(DOC, encoding="utf-8").read() if os.path.exists(DOC) else ""
    if actual != texto:
        print("doc-repositorio/06_MAPA_DE_COMPONENTES.md no está al día: ejecuta con --escribir.")
        return 1
    print("Mapa de Componentes válido y al día.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
