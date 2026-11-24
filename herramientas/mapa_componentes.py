"""Mapa de Componentes: valida la especificación y genera su documento.

La especificación es ``doc-repositorio/componentes.toml`` (dónde debe vivir cada Componente y dónde
está hoy). Esta herramienta:

- valida sus campos y que cada decisión citada exista en ``docs/DISENO_COMPONENTES.md``;
- genera ``doc-repositorio/06_MAPA_DE_COMPONENTES.md`` (la tabla) y ``doc-repositorio/07_DISENO_VISUAL.md``
  (los diagramas del latido, del núcleo y de cada mundo, en Mermaid) con ``--escribir``, o comprueba que
  están al día (``--comprobar``, el modo por defecto).

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
DOC_VISUAL = os.path.join(RAIZ, "doc-repositorio", "07_DISENO_VISUAL.md")
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
MUNDOS = ("minimo", "archivos", "snake", "ajedrez", "crafter")
NOMBRES_MUNDO = {"minimo": "Mínimo", "archivos": "Archivos", "snake": "Snake", "ajedrez": "Ajedrez", "crafter": "Crafter"}
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
        for m in ([c["dueno"]] if c["clase"] == "mundo" else []) + list(c.get("registran", [])):
            if m not in MUNDOS:
                errores.append(f"{n}: mundo «{m}» desconocido (MUNDOS en herramientas/mapa_componentes.py)")
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


# --- Diseño visual (07_DISENO_VISUAL.md): diagramas Mermaid generados desde la especificación ---

ESTILOS = [
    "classDef general fill:#f1f5f9,stroke:#64748b,color:#0f172a",
    "classDef opcional fill:#dbeafe,stroke:#2563eb,color:#0f172a",
    "classDef cuerpo fill:#dcfce7,stroke:#16a34a,color:#0f172a",
    "classDef mundo fill:#fef3c7,stroke:#d97706,color:#0f172a",
    "classDef paso fill:#ede9fe,stroke:#7c3aed,color:#0f172a",
]
LEYENDA = (
    "**Leyenda.** Rectángulo: Componente · óvalo: estrategia · doble borde: biblioteca del cuerpo · ✱: aprende (paso 4). "
    "Color: gris, general · azul, opcional (general, montado solo por quien lo registra) · verde, del cuerpo · "
    "ámbar, propio del mundo · violeta, paso del latido sin Componentes declarados."
)


def montado_en(c: Dict[str, Any], mundo: str, espec: List[Dict[str, Any]]) -> bool:
    """Si el mundo monta este elemento en su destino (con las sustituciones aplicadas). ``mundo=""``: el núcleo."""
    if c["clase"] == "general":
        return not any(
            o.get("sustituye") == c["nombre"] and o["destino"] == c["destino"] and montado_en(o, mundo, espec) for o in espec
        )
    return bool(mundo) and mundo in objetivo_en(c)


def _id(*partes: str) -> str:
    return "_".join(re.sub(r"[^A-Za-z0-9]", "", p) for p in partes)


def _nodo(c: Dict[str, Any]) -> str:
    texto = c["nombre"] + (" ✱" if c.get("aprende") else "")
    ident = _id(_seccion(c), c["nombre"])
    forma = {"estrategia": f'(["{texto}"])', "biblioteca": f'[["{texto}"]]'}.get(c["tipo"], f'["{texto}"]')
    return f"{ident}{forma}:::{c['clase']}"


def diagrama(espec: List[Dict[str, Any]], mundo: str) -> List[str]:
    """Flujo de un latido con los Componentes que monta ``mundo`` (``""``: solo lo general, el núcleo)."""
    hay = [c for c in espec if montado_en(c, mundo, espec)]

    def en(sec: str, tipo: str = "") -> List[Dict[str, Any]]:
        return [c for c in hay if _seccion(c) == sec and (not tipo or c["tipo"] == tipo)]

    def caja(ident: str, titulo: str, filas: List[Dict[str, Any]], sangria: str = "  ") -> List[str]:
        out = [f'{sangria}subgraph {ident}["{titulo}"]', f"{sangria}  direction TB"]
        out += [f"{sangria}  {_nodo(c)}" for c in filas] or [f'{sangria}  {ident}_vacio["—"]:::general']
        return out + [f"{sangria}end"]

    aprenden = " · ".join(c["nombre"] for c in hay if c.get("aprende")) or "—"
    L = ["```mermaid", "flowchart TB"]
    L.append('  P1["1 · Onda<br/>copia de la anterior; la anterior pasa a la memoria a corto plazo"]:::paso')
    L += caja("P2", "2 · Core · Sentir (en bruto)", en("CORE.Sentir"))
    L += caja("P3", "3 · Preatención (S1 · Sentir; no paga atención; también dormido)", en("PREATENCION"))
    L.append(f'  P4["4 · Plasticidad: aprende del efecto de la acción anterior<br/>{aprenden}"]:::paso')
    L += caja("P5", "5 · Regulación de la Onda (Core)", en("CORE.Regulacion"))
    for s, nombre in (("S1", "supervivencia"), ("S2", "valor"), ("S3", "verdad")):
        L += [f'  subgraph {s}["6 · {s} · {nombre}"]', "    direction LR"]
        for m in MODULOS:
            sec = f"{s}.{m}"
            ident = _id(sec)
            if m == "Reaccionar":
                L += [f'    subgraph {ident}["{m}"]', "      direction TB"]
                L += [f"      {_nodo(c)}" for c in en(sec, "componente")]
                est = en(sec, "estrategia")
                if est:
                    L += caja(_id(sec, "est"), "estrategias", est, "      ")
                L.append("    end")
            else:
                L += caja(ident, m, en(sec), "    ")
        L += [f"    {_id(f'{s}.{MODULOS[i]}')} --> {_id(f'{s}.{MODULOS[i + 1]}')}" for i in range(len(MODULOS) - 1)]
        L.append("  end")
    L += caja("P7", "7 · Core · Actuar", en("CORE.Actuar"))
    L.append('  P8["8 · Cierre: marcar para guardar, episodios, indicadores<br/>→ siguiente latido (paso 1)"]:::paso')
    L += [
        '  P1 -->|"la Onda"| P2',
        '  P2 -->|"piezas en bruto (arousal 0)"| P3',
        '  P3 -->|"piezas anotadas: saliencia y valoración"| P4',
        "  P4 --> P5",
        '  P5 -->|"frecuencia · amplitud · potencia"| S1',
        '  S1 -->|"la misma Onda, con lo que S1 añadió"| S2',
        "  S2 --> S3",
        '  S3 -->|"Actuaciones (guillotina si se agota el plazo)"| P7',
        '  P7 -->|"una primitiva ejecutada"| P8',
    ]
    cuerpo = en("cuerpo")
    if cuerpo:
        usan = " y ".join(c["nombre"] for c in hay if c["clase"] == "cuerpo" and c["tipo"] == "componente")
        L += caja("CU", f"Cuerpo · {cuerpo[0]['dueno']}: bibliotecas que usan {usan}", cuerpo)
        L.append("  P8 ~~~ CU")
    return L + [f"  {e}" for e in ESTILOS] + ["```"]


def _propios(espec: List[Dict[str, Any]], mundo: str) -> List[str]:
    filas = []
    for c in espec:
        if c["clase"] != "general" and montado_en(c, mundo, espec):
            extra = f", sustituye a `{c['sustituye']}`" if c.get("sustituye") else ""
            filas.append(f"- `{c['nombre']}` ({c['tipo']}, {_clase(c)}) en {TITULOS.get(_seccion(c), _seccion(c).replace('.', ' · '))}{extra}")
    return filas


def generar_visual(espec: List[Dict[str, Any]]) -> str:
    """El documento de diagramas, determinista."""
    L = [
        "# Diseño visual: el latido, el núcleo y cada mundo",
        "",
        "> **Generado** por `herramientas/mapa_componentes.py --escribir` desde [`componentes.toml`](componentes.toml). No se edita a mano.",
        "> Tabla completa: [`06_MAPA_DE_COMPONENTES.md`](06_MAPA_DE_COMPONENTES.md) · "
        "Decisiones: [`docs/DISENO_COMPONENTES.md`](../docs/DISENO_COMPONENTES.md).",
        "",
        "## Cómo leerlo",
        "",
        "Cada latido es una **Onda** que recorre ocho pasos, siempre en el mismo orden (D1). La Onda lleva el plazo "
        "(**frecuencia**; si se agota, la **guillotina** corta lo que quede), cuántas piezas caben en la atención "
        "(**amplitud**) y cuánto arousal se puede dar o cambiar (**potencia**). Cada Componente solo produce y cambia "
        "piezas de su tipo.",
        "",
        "- **Pasos 1–5 (Core y preatención):** sentir en bruto, anotar lo saliente y lo valorado, aprender del efecto de "
        "la acción anterior y fijar la Onda. No pagan atención y corren también dormido.",
        "- **Paso 6 (cognición):** S1 → S2 → S3, uno tras otro sobre la misma Onda. En cada sistema, Sentir → Interpretar → "
        "Reaccionar (las estrategias, cada una con su Actuación) → Actuar. Pagan atención y la guillotina puede cortarlos.",
        "- **Pasos 7–8 (Core):** el Tribunal elige una Actuación, el Core ejecuta su primitiva, y el cierre marca qué guardar.",
        "",
        "Un mundo no cambia este flujo: solo **registra** su cuerpo y sus Componentes propios, que se añaden a lo general o "
        "lo sustituyen en el mismo sitio.",
        "",
        LEYENDA,
        "",
        "## El núcleo (lo que monta cualquier mundo)",
        "",
    ]
    L += diagrama(espec, "")
    for mundo in MUNDOS:
        propios = _propios(espec, mundo)
        L += ["", f"## {NOMBRES_MUNDO[mundo]}", ""]
        if not propios:
            L.append("Monta solo el núcleo: el diagrama es el de arriba.")
            continue
        L += ["Añade al núcleo:", ""] + propios + [""] + diagrama(espec, mundo)
    return "\n".join(L) + "\n"


def main(argv: List[str]) -> int:
    espec = cargar()
    errores = validar(espec, decisiones_existentes())
    if errores:
        print("La especificación tiene errores:")
        for e in errores:
            print(f"  - {e}")
        return 1
    documentos = ((DOC, generar(espec)), (DOC_VISUAL, generar_visual(espec)))
    if "--escribir" in argv:
        for ruta, texto in documentos:
            with open(ruta, "w", encoding="utf-8", newline="\n") as f:
                f.write(texto)
            print(f"Escrito {os.path.relpath(ruta, RAIZ)}")
        return 0
    desfasados = []
    for ruta, texto in documentos:
        actual = open(ruta, encoding="utf-8").read() if os.path.exists(ruta) else ""
        if actual != texto:
            desfasados.append(os.path.relpath(ruta, RAIZ))
    if desfasados:
        print(f"No están al día: {', '.join(desfasados)}. Ejecuta con --escribir.")
        return 1
    print("Mapa de Componentes válido y al día (tabla y diagramas).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
