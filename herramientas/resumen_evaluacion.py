"""Genera las tablas de resultados y comparativas de evaluación de Crafter.

Soporta tanto la medición de referencia oficial como la evaluación de Paso 5 y Paso 0.
"""

import argparse
import json
import os
import statistics
import sys
from typing import Any, Dict, List, Tuple

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS_DIR = os.path.join(RAIZ, "datos", "evaluacion")


def formatear_float_es(valor: float, decimales: int = 2) -> str:
    """Formatea un float con punto de miles y coma decimal estilo español (p. ej. 1.379,2)."""
    s = f"{valor:,.{decimales}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# =====================================================================
# Informe Paso 5 y Paso 0
# =====================================================================

CONDICIONES_PASO5_PASO0 = [
    {
        "id": "suelo",
        "nombre": "Suelo (referencia `main`)",
        "archivo": "suelo_main.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-estrategias-propias",
    },
    {
        "id": "main",
        "nombre": "`main` sin herencia",
        "archivo": "main_sin_herencia.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia",
    },
    {
        "id": "G1",
        "nombre": "G1 (Paso 5)",
        "archivo": "paso5_G1.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --sin-estrategias-propias --manual estricto",
    },
    {
        "id": "G2",
        "nombre": "G2 (Paso 5)",
        "archivo": "paso5_G2.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --sin-estrategias-propias --manual ampliado",
    },
    {
        "id": "G3",
        "nombre": "G3 (Paso 5)",
        "archivo": "paso5_G3.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --manual estricto",
    },
    {
        "id": "G4",
        "nombre": "G4 (Paso 5)",
        "archivo": "paso5_G4.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --manual ampliado",
    },
    {
        "id": "P1",
        "nombre": "P1 (Paso 0)",
        "archivo": "paso0_P1.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --sin-estrategias-propias --manual estricto --mecanismos urgencia_local",
    },
    {
        "id": "P2",
        "nombre": "P2 (Paso 0)",
        "archivo": "paso0_P2.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --sin-estrategias-propias --manual estricto --mecanismos urgencia_local aliestesia",
    },
    {
        "id": "P3",
        "nombre": "P3 (Paso 0)",
        "archivo": "paso0_P3.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --manual estricto --mecanismos urgencia_local aliestesia",
    },
]

SALIDA_INVARIANCIA = (
    "minimo: OK\n"
    "archivos: OK\n"
    "crafter: semilla 1, latido 1: objetivo 'hierba_31_32' -> 'hierba_32_33' | "
    "semilla 2, latido 1: decisión 'COGER' -> 'MOVER' | semilla 3, latido 1: decisión 'COGER' -> 'MOVER'\n"
    "ajedrez: OK"
)


def cargar_datos_paso5_paso0() -> Dict[str, Dict[str, Any]]:
    datos = {}
    for c in CONDICIONES_PASO5_PASO0:
        ruta = os.path.join(DATOS_DIR, c["archivo"])
        with open(ruta, "r", encoding="utf-8") as f:
            datos[c["id"]] = json.load(f)
    return datos


def generar_tabla_general(datos: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 1. Tabla general",
        "",
        "| Condición | Opciones exactas | Score (%) | IC 95 % (%) | Episodios | Pasos / ep. | Rendimiento (ms/paso) |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in CONDICIONES_PASO5_PASO0:
        cid = c["id"]
        d = datos[cid]
        score_str = formatear_float_es(d["score"])
        ic_str = f"[{formatear_float_es(d['score_ci_95'][0])}, {formatear_float_es(d['score_ci_95'][1])}]"
        ep = d["episodios"]
        pasos_ep = formatear_float_es(d["pasos"] / ep, 1)
        ms_paso = formatear_float_es(d["ms_por_paso"])
        lineas.append(
            f"| **{c['nombre']}** | `{c['opciones']}` | **{score_str}** | {ic_str} | {ep} | {pasos_ep} | {ms_paso} |"
        )
    return "\n".join(lineas)


def generar_tasas_logros(datos: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 2. Tasas por logro (%)",
        "",
        "Porcentaje de episodios donde se obtuvo cada uno de los 22 logros oficiales de Crafter:",
        "",
        "| Logro | Suelo | `main` | G1 | G2 | G3 | G4 | P1 | P2 | P3 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    todos_logros = sorted(datos["suelo"]["tasas_logros"].keys())
    ids = [c["id"] for c in CONDICIONES_PASO5_PASO0]
    for logro in todos_logros:
        valores = [formatear_float_es(datos[cid]["tasas_logros"].get(logro, 0.0)) for cid in ids]
        lineas.append(f"| `{logro}` | {' | '.join(valores)} |")
    return "\n".join(lineas)


def generar_causas_muerte(datos: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 3. Causas de muerte por condición",
        "",
        "Número de episodios y porcentaje sobre el total de episodios de cada condición:",
        "",
        "| Causa | Suelo | `main` | G1 | G2 | G3 | G4 | P1 | P2 | P3 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    todas_causas = sorted(
        {causa for d in datos.values() for causa in d["causas_muerte"]},
        key=lambda x: (x == "cortado por presupuesto", x),
    )
    ids = [c["id"] for c in CONDICIONES_PASO5_PASO0]
    for causa in todas_causas:
        cols = []
        for cid in ids:
            d = datos[cid]
            n = d["causas_muerte"].get(causa, 0)
            pct = formatear_float_es((n / d["episodios"]) * 100.0, 1)
            cols.append(f"{n} ({pct} %)")
        lineas.append(f"| `{causa}` | {' | '.join(cols)} |")
    totales = [str(datos[cid]["episodios"]) for cid in ids]
    lineas.append(f"| **Total episodios** | **{'** | **'.join(totales)}** |")
    return "\n".join(lineas)


def se_solapan(ic1: Tuple[float, float], ic2: Tuple[float, float]) -> bool:
    """Determina si dos intervalos cerrados [a, b] y [c, d] se solapan."""
    return max(ic1[0], ic2[0]) <= min(ic1[1], ic2[1])


def generar_comparaciones(datos: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 4. Comparaciones",
        "",
        "Diferencias de Crafter Score (en puntos porcentuales) y comprobación de solapamiento de intervalos de confianza al 95 %:",
        "",
    ]

    def comparar(nom_a: str, id_a: str, nom_b: str, id_b: str) -> str:
        da, db = datos[id_a], datos[id_b]
        diff = da["score"] - db["score"]
        signo = "+" if diff >= 0 else ""
        diff_str = f"{signo}{formatear_float_es(diff)} pp"
        ic_a = (da["score_ci_95"][0], da["score_ci_95"][1])
        ic_b = (db["score_ci_95"][0], db["score_ci_95"][1])
        solapa = se_solapan(ic_a, ic_b)
        solapa_str = "Sí" if solapa else "No"
        ic_a_str = f"[{formatear_float_es(ic_a[0])}, {formatear_float_es(ic_a[1])}] %"
        ic_b_str = f"[{formatear_float_es(ic_b[0])}, {formatear_float_es(ic_b[1])}] %"
        return (
            f"- **{nom_a} frente a {nom_b}**:\n"
            f"  - Score {nom_a}: {formatear_float_es(da['score'])} % (IC 95 %: {ic_a_str})\n"
            f"  - Score {nom_b}: {formatear_float_es(db['score'])} % (IC 95 %: {ic_b_str})\n"
            f"  - Diferencia de Score ({nom_a} - {nom_b}): {diff_str}\n"
            f"  - ¿Se solapan los IC 95 %?: **{solapa_str}**"
        )

    # 1. G1 frente al suelo
    lineas.append("### G1 frente al suelo")
    lineas.append(comparar("G1", "G1", "Suelo (`main`)", "suelo"))
    lineas.append("")

    # 2. G3 y G4 frente a main
    lineas.append("### G3 y G4 frente a `main` sin herencia")
    lineas.append(comparar("G3", "G3", "`main` sin herencia", "main"))
    lineas.append("")
    lineas.append(comparar("G4", "G4", "`main` sin herencia", "main"))
    lineas.append("")

    # 3. P1 y P2 frente a G1
    lineas.append("### P1 y P2 frente a G1")
    lineas.append(comparar("P1", "P1", "G1", "G1"))
    lineas.append("")
    lineas.append(comparar("P2", "P2", "G1", "G1"))
    lineas.append("")

    # 4. P3 frente a G3
    lineas.append("### P3 frente a G3")
    lineas.append(comparar("P3", "P3", "G3", "G3"))
    lineas.append("")

    return "\n".join(lineas)


def generar_seccion_invariancia() -> str:
    lineas = [
        "## 5. Salida literal de `invariancia.py`",
        "",
        "```",
        SALIDA_INVARIANCIA,
        "```",
    ]
    return "\n".join(lineas)


def generar_informe_paso5_paso0() -> str:
    datos = cargar_datos_paso5_paso0()
    cabecera = [
        "# Medición Oficial: Paso 5 y Paso 0 (Crafter)",
        "",
        "Evaluación oficial en Crafter (100.000 pasos, semilla base 31, vista oficial, sin herencia) "
        "en la rama `feature/paso0` (commit `43f636c`).",
        "",
        "Ficheros de datos utilizados (en `datos/evaluacion/`):",
        "- `suelo_main.json`: suelo de referencia (`main` sin estrategias)",
        "- `main_sin_herencia.json`: referencia `main` con estrategias y sin herencia",
        "- `paso5_G1.json`: G1 (Paso 5, sin estrategias propias, manual estricto)",
        "- `paso5_G2.json`: G2 (Paso 5, sin estrategias propias, manual ampliado)",
        "- `paso5_G3.json`: G3 (Paso 5, manual estricto)",
        "- `paso5_G4.json`: G4 (Paso 5, manual ampliado)",
        "- `paso0_P1.json`: P1 (Paso 0, urgencia_local, manual estricto, sin estrategias propias)",
        "- `paso0_P2.json`: P2 (Paso 0, urgencia_local + aliestesia, manual estricto, sin estrategias propias)",
        "- `paso0_P3.json`: P3 (Paso 0, urgencia_local + aliestesia, manual estricto, con estrategias)",
        "",
    ]
    partes = [
        "\n".join(cabecera),
        generar_tabla_general(datos),
        generar_tasas_logros(datos),
        generar_causas_muerte(datos),
        generar_comparaciones(datos),
        generar_seccion_invariancia(),
    ]
    return "\n\n---\n\n".join(partes) + "\n"


# =====================================================================
# Informe oficial general (retrocompatibilidad con MEDICION_OFICIAL.md)
# =====================================================================

def generar_seccion_3_oficial(datos_crafter: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 3. Comparación global Crafter (100.000 pasos)",
        "",
        "| Condición | Score Crafter (IC 95 %) | Episodios | Pasos / episodio | Rendimiento (ms/paso) | Tiempo total (s) |",
        "|---|---|---|---|---|---|",
    ]
    etiquetas = [
        ("suelo", "**Suelo (`main` sin estrategias)**"),
        ("techo_main", "**Techo `main` (con linaje)**"),
        ("sin_herencia", "**`main` sin herencia**"),
        ("techo_c3d", "**Techo C.3d (`feature/crafter-fase-c`)**"),
    ]
    for clave, etiqueta in etiquetas:
        d = datos_crafter[clave]
        score_str = formatear_float_es(d["score"])
        ic_inf_str = formatear_float_es(d["score_ci_95"][0])
        ic_sup_str = formatear_float_es(d["score_ci_95"][1])
        ep = d["episodios"]
        pasos_ep_str = formatear_float_es(d["pasos"] / ep, 1)
        ms_str = formatear_float_es(d["ms_por_paso"])
        t_str = formatear_float_es(d["tiempo_segundos"], 1)
        lineas.append(
            f"| {etiqueta} | **{score_str} %** [{ic_inf_str}, {ic_sup_str}] % | {ep} | {pasos_ep_str} | {ms_str} ms | {t_str} s |"
        )
    return "\n".join(lineas)


def generar_seccion_4_oficial(datos_crafter: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 4. Tasa de éxito por logro (%)",
        "",
        "Fracción de episodios en que se consiguió el logro al menos una vez (sobre el total de episodios de cada condición):",
        "",
        "| Logro | Suelo (`main`) | Techo `main` | `main` sin herencia | Techo C.3d |",
        "|---|---|---|---|---|",
    ]
    todos_logros = sorted(datos_crafter["techo_main"]["tasas_logros"].keys())
    for logro in todos_logros:
        s = formatear_float_es(datos_crafter["suelo"]["tasas_logros"].get(logro, 0.0))
        tm = formatear_float_es(datos_crafter["techo_main"]["tasas_logros"].get(logro, 0.0))
        sh = formatear_float_es(datos_crafter["sin_herencia"]["tasas_logros"].get(logro, 0.0))
        tc = formatear_float_es(datos_crafter["techo_c3d"]["tasas_logros"].get(logro, 0.0))
        lineas.append(f"| `{logro}` | {s} % | {tm} % | {sh} % | {tc} % |")
    return "\n".join(lineas)


def generar_seccion_5_oficial(datos_crafter: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 5. Causas de muerte / finalización por condición",
        "",
        "| Causa de muerte | Suelo (`main`) | Techo `main` | `main` sin herencia | Techo C.3d |",
        "|---|---|---|---|---|",
    ]
    todas_causas = sorted(
        {c for d in datos_crafter.values() for c in d["causas_muerte"]},
        key=lambda x: (x == "cortado por presupuesto", x),
    )
    for causa in todas_causas:
        cols = []
        for clave in ("suelo", "techo_main", "sin_herencia", "techo_c3d"):
            d = datos_crafter[clave]
            n = d["causas_muerte"].get(causa, 0)
            pct = formatear_float_es((n / d["episodios"]) * 100.0, 1)
            cols.append(f"{n} ({pct} %)")
        lineas.append(f"| `{causa}` | {' | '.join(cols)} |")
    totales = [str(datos_crafter[k]["episodios"]) for k in ("suelo", "techo_main", "sin_herencia", "techo_c3d")]
    lineas.append(f"| **Total episodios** | **{'** | **'.join(totales)}** |")
    return "\n".join(lineas)


def generar_seccion_6_oficial(f_minimo: Dict[str, Any], f_archivos: Dict[str, Any]) -> str:
    intro = (
        "Línea base registrada sobre `main` (4 grupos: Equilibrado, Valiente, Reactivo, Sin experiencia; semillas 1 a 10; "
        "4 generaciones de 400 latidos por celda = 160 vidas por mundo). "
        "Datos procedentes de `datos/evaluacion/ref_generalizacion_minimo.json` y `datos/evaluacion/ref_generalizacion_archivos.json`:"
    )
    encabezado = (
        "| Mundo | Celdas ejecutadas | Vidas totales | Vidas vivas (400 lat.) | Latidos/vida (media / med.) | "
        "Fitness/vida (media / med.) | Muertes por causa | Rendimiento |"
    )
    lineas = [
        "## 6. Referencia de generalización (`ref_generalizacion`)",
        "",
        intro,
        "",
        encabezado,
        "|---|---|---|---|---|---|---|---|",
    ]
    for mundo_nombre, d in (("minimo", f_minimo), ("archivos", f_archivos)):
        n_celdas = len(d["filas"])
        total_vidas = sum(len(r["vidas"]) for r in d["filas"])
        latidos_todas = [v["latidos"] for r in d["filas"] for v in r["vidas"]]
        fitness_todas = [v["fitness"] for r in d["filas"] for v in r["vidas"]]
        causas: Dict[str, int] = {}
        for r in d["filas"]:
            for c in r["causas"]:
                causas[c] = causas.get(c, 0) + 1
        vivas = causas.get("vive", 0)
        vivas_pct_str = formatear_float_es((vivas / total_vidas) * 100.0, 1)
        lat_med_str = formatear_float_es(statistics.fmean(latidos_todas), 1)
        lat_mdn_str = formatear_float_es(statistics.median(latidos_todas), 1)
        fit_med_str = formatear_float_es(statistics.fmean(fitness_todas), 2)
        fit_mdn_str = formatear_float_es(statistics.median(fitness_todas), 2)
        muertes_str = (
            ", ".join(f"{c}: {n}" for c, n in sorted(causas.items(), key=lambda kv: -kv[1]) if c != "vive")
            or "Ninguna"
        )
        t_total_ms = sum(r["indicadores"].get("ms", 0.0) for r in d["filas"])
        latidos_sum = sum(latidos_todas)
        ms_latido_str = formatear_float_es(t_total_ms / latidos_sum if latidos_sum else 0.0, 2)
        lineas.append(
            f"| **`{mundo_nombre}`** | {n_celdas} / {n_celdas} (100 %) | {total_vidas} | {vivas} ({vivas_pct_str} %) | "
            f"{lat_med_str} / {lat_mdn_str} | {fit_med_str} / {fit_mdn_str} | {muertes_str} | {ms_latido_str} ms/latido |"
        )
    lineas.append("| **`ajedrez`** | — | — | — | — | — | Invariancia: **OK** | — |")
    return "\n".join(lineas)


def generar_markdown_oficial() -> str:
    archivos = {
        "suelo": os.path.join(DATOS_DIR, "suelo_main.json"),
        "techo_main": os.path.join(DATOS_DIR, "techo_main.json"),
        "sin_herencia": os.path.join(DATOS_DIR, "main_sin_herencia.json"),
        "techo_c3d": os.path.join(DATOS_DIR, "techo_c3d.json"),
    }
    datos_crafter = {k: json.load(open(v, encoding="utf-8")) for k, v in archivos.items()}
    f_minimo = json.load(open(os.path.join(DATOS_DIR, "ref_generalizacion_minimo.json"), encoding="utf-8"))
    f_archivos = json.load(open(os.path.join(DATOS_DIR, "ref_generalizacion_archivos.json"), encoding="utf-8"))

    s3 = generar_seccion_3_oficial(datos_crafter)
    s4 = generar_seccion_4_oficial(datos_crafter)
    s5 = generar_seccion_5_oficial(datos_crafter)
    s6 = generar_seccion_6_oficial(f_minimo, f_archivos)

    return f"{s3}\n\n---\n\n{s4}\n\n---\n\n{s5}\n\n---\n\n{s6}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oficial", action="store_true", help="Genera las secciones 3 a 6 para MEDICION_OFICIAL.md")
    parser.add_argument("--salida", type=str, default=None, help="Ruta donde guardar el markdown generado")
    args = parser.parse_args()

    if args.oficial:
        salida = generar_markdown_oficial()
    else:
        salida = generar_informe_paso5_paso0()

    if args.salida:
        os.makedirs(os.path.dirname(os.path.abspath(args.salida)), exist_ok=True)
        with open(args.salida, "w", encoding="utf-8") as f:
            f.write(salida)

    print(salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
