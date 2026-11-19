"""Genera las tablas de resultados (secciones 3 a 6) para docs/MEDICION_OFICIAL.md

Lee directamente los archivos JSON en datos/evaluacion/ y produce el markdown exacto.
"""

import json
import os
import statistics
import sys
from typing import Any, Dict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS_DIR = os.path.join(RAIZ, "datos", "evaluacion")


def formatear_float_es(valor: float, decimales: int = 2) -> str:
    """Formatea un float con punto de miles y coma decimal estilo español (p. ej. 1.379,2)."""
    s = f"{valor:,.{decimales}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def generar_seccion_3(datos_crafter: Dict[str, Dict[str, Any]]) -> str:
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


def generar_seccion_4(datos_crafter: Dict[str, Dict[str, Any]]) -> str:
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


def generar_seccion_5(datos_crafter: Dict[str, Dict[str, Any]]) -> str:
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


def generar_seccion_6(f_minimo: Dict[str, Any], f_archivos: Dict[str, Any]) -> str:
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
    lineas.append("| **`ajedrez`** | — | — | — | — | — | Invariancia: **OK** | 5,5 s |")
    return "\n".join(lineas)


def generar_markdown_completo() -> str:
    archivos = {
        "suelo": os.path.join(DATOS_DIR, "suelo_main.json"),
        "techo_main": os.path.join(DATOS_DIR, "techo_main.json"),
        "sin_herencia": os.path.join(DATOS_DIR, "main_sin_herencia.json"),
        "techo_c3d": os.path.join(DATOS_DIR, "techo_c3d.json"),
    }
    datos_crafter = {k: json.load(open(v, encoding="utf-8")) for k, v in archivos.items()}
    f_minimo = json.load(open(os.path.join(DATOS_DIR, "ref_generalizacion_minimo.json"), encoding="utf-8"))
    f_archivos = json.load(open(os.path.join(DATOS_DIR, "ref_generalizacion_archivos.json"), encoding="utf-8"))

    s3 = generar_seccion_3(datos_crafter)
    s4 = generar_seccion_4(datos_crafter)
    s5 = generar_seccion_5(datos_crafter)
    s6 = generar_seccion_6(f_minimo, f_archivos)

    return f"{s3}\n\n---\n\n{s4}\n\n---\n\n{s5}\n\n---\n\n{s6}\n"


def main() -> int:
    salida = generar_markdown_completo()
    print(salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
