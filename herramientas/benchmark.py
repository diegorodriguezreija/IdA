"""Benchmark por perfiles con el protocolo de ``docs/BENCHMARK_PERFILES_MUNDOS.md``.

N = 10 linajes independientes (semillas 1 a 10, directorio limpio por semilla). Mínimo y archivos:
4 generaciones de 400 latidos; Crafter: 3 generaciones de 600. Se promedia cada linaje y sobre los
10 linajes se da la media con IC 95 % (t de Student, t(0,975; 9) = 2,262); la comparación entre dos
versiones es pareada por semilla. Reloj real, como en el protocolo original.

    python herramientas/benchmark.py ejecutar --raiz <código> --mundo crafter --salida base.json
    python herramientas/benchmark.py comparar base.json nueva.json

``--raiz`` es la carpeta del código que se mide (por ejemplo, un ``git worktree`` de ``main``).
Además de las métricas de vida, recoge por latido, si la versión los tiene: plazo agotado, S3 sin
amplitud o potencia y potencia gastada por sistema (``Onda.consumo``, bloque B); y de S1 (bloque C):
latidos por estrategia activa y ejecutada, abandonos por agotamiento, sustituciones, reflejos y sus
interrupciones, y latidos en que el plus por estrategia activa decide el ganador. Guarda la causa de
muerte de cada vida (la que registra el organismo o, si la versión no la registra, deducida del último
latido) y el resumen compara las muertes por causa.
"""

import argparse
import json
import math
import os
import statistics
import sys
import tempfile
from collections import Counter
from typing import Any, Dict, List

PERFILES = {
    "Equilibrado": {"apertura": 0.50, "responsabilidad": 0.50, "neuroticismo": 0.50, "extraversion": 0.50, "umbral_miedo": 0.60},
    "Valiente": {"apertura": 0.60, "responsabilidad": 0.65, "neuroticismo": 0.20, "extraversion": 0.60, "umbral_miedo": 0.85},
    "Reactivo": {"apertura": 0.40, "responsabilidad": 0.60, "neuroticismo": 0.85, "extraversion": 0.30, "umbral_miedo": 0.35},
}
GRUPOS = [*((n, n, False) for n in PERFILES), ("Sin experiencia", "Equilibrado", True)]
PROTOCOLO = {"minimo": (4, 400), "archivos": (4, 400), "crafter": (3, 600)}
SEMILLAS = range(1, 11)
T_0975_9 = 2.262


def _metricas(mundo: str, r: Dict[str, Any]) -> Dict[str, float]:
    m = {"latidos": float(r["latidos"]), "fitness": float(r["fitness"])}
    p = r["puntuacion"] or {}
    if mundo == "crafter":
        m["logros"] = float(p.get("n_logros", 0))
    elif mundo == "archivos":
        m["nutritivos"], m["toxicos"] = float(p.get("nutritivos", 0)), float(p.get("toxicos", 0))
    elif mundo == "minimo":
        m["setas"] = float(p.get("setas", 0))
    return m


def _causa(resumen: Dict[str, Any], final: Dict[str, Any]) -> str:
    """Causa de muerte de una vida: la que registra el organismo (desde el bloque C); si la versión no
    la registra, se deduce del último latido (causa del último efecto; si no, hambre con la
    alimentación a 0; si no, desgaste). «vive» si acabó viva."""
    if resumen.get("vivo"):
        return "vive"
    if resumen.get("causa_muerte"):
        return str(resumen["causa_muerte"])
    if final.get("causa"):
        return str(final["causa"])
    return "hambre" if final.get("alimentacion", 1.0) <= 0.0 else "desgaste"


def ejecutar(raiz: str, mundo: str, salida: str) -> None:
    sys.path.insert(0, os.path.abspath(raiz))
    from ida.ejecutor import ejecutar as vivir

    generaciones, latidos = PROTOCOLO[mundo]
    filas: List[Dict[str, Any]] = []
    for grupo, perfil, sin_exp in GRUPOS:
        for semilla in SEMILLAS:
            ind: Dict[str, Any] = {"latidos": 0, "plazo": 0, "s3_sin_recursos": 0, "potencia": {"S1": 0.0, "S2": 0.0, "S3": 0.0},
                                   "estrategias": {}, "reflejos": 0, "interrumpe": 0, "plus": 0, "sustituciones": 0}

            finales: List[Dict[str, Any]] = []     # último latido de cada vida, para deducir la causa de muerte

            def al_latir(_o: Any, onda: Any, _r: Dict[str, Any]) -> None:
                ind["latidos"] += 1   # noqa: B023 (se usa en la misma iteración)
                estado = {"causa": getattr(_o.ultimo_efecto, "causa", None) if _o.ultimo_efecto else None,
                          "alimentacion": float(_o.soma.alimentacion)}
                if onda.ciclo == 1 or not finales:   # noqa: B023
                    finales.append(estado)   # noqa: B023
                else:
                    finales[-1] = estado   # noqa: B023
                if onda.guillotina and "plazo" in onda.motivo_guillotina:
                    ind["plazo"] += 1   # noqa: B023
                if onda.notas.get("plus_decide"):
                    ind["plus"] += 1   # noqa: B023
                e1 = onda.notas.get("estrategias_S1")
                if e1:
                    for n in e1["activas"]:
                        ind["estrategias"].setdefault(n, {"activa": 0, "ejecutada": 0, "abandonos": 0})["activa"] += 1   # noqa: B023
                    if e1["ejecutada"]:
                        ind["estrategias"].setdefault(e1["ejecutada"], {"activa": 0, "ejecutada": 0, "abandonos": 0})["ejecutada"] += 1  # noqa: B023
                    for n in e1["abandonos"]:
                        ind["estrategias"].setdefault(n, {"activa": 0, "ejecutada": 0, "abandonos": 0})["abandonos"] += 1   # noqa: B023
                    ind["reflejos"] += int(e1["reflejo"])   # noqa: B023
                    ind["interrumpe"] += int(e1["interrumpe"])   # noqa: B023
                    ind["sustituciones"] += int(e1.get("sustituciones", 0))   # noqa: B023
                consumo = getattr(onda, "consumo", None)
                if consumo is None:
                    return
                s3 = consumo.get("S3", {})
                restante = onda.notas.get("restante", {}).get("S3")
                if s3.get("rechazos_amplitud") or s3.get("recortes_potencia") or (restante and min(restante) <= 0):
                    ind["s3_sin_recursos"] += 1   # noqa: B023
                for s in ("S1", "S2", "S3"):
                    ind["potencia"][s] += consumo.get(s, {}).get("potencia", 0.0)   # noqa: B023

            with tempfile.TemporaryDirectory(prefix=f"ida_bench_{mundo}_") as datos:
                resumenes = vivir(mundo, latidos=latidos, semilla=semilla, generaciones=generaciones, tabula_rasa=True,
                                  consola=False, datos=datos, al_latir=al_latir, sin_experiencia=sin_exp,
                                  arquetipo_inicial=PERFILES[perfil])
            vidas = [_metricas(mundo, r) for r in resumenes]
            causas = [_causa(r, finales[i] if i < len(finales) else {}) for i, r in enumerate(resumenes)]
            filas.append({"grupo": grupo, "semilla": semilla, "vidas": vidas, "causas": causas, "indicadores": ind})
            print(f"{mundo} {grupo} semilla {semilla}: {len(vidas)} vidas", flush=True)
    with open(salida, "w", encoding="utf-8") as f:
        json.dump({"mundo": mundo, "filas": filas}, f)


def _ic(xs: List[float]) -> str:
    media = statistics.fmean(xs)
    medio = T_0975_9 * statistics.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else 0.0
    return f"{media:.2f} ± {medio:.2f}"


def comparar(base: str, nueva: str) -> None:
    with open(base, encoding="utf-8") as f:
        a = json.load(f)
    with open(nueva, encoding="utf-8") as f:
        b = json.load(f)
    mundo = a["mundo"]
    metricas = list(a["filas"][0]["vidas"][0])
    print(f"\n### {mundo} (N = {len(SEMILLAS)} linajes, IC 95 %; Δ = nueva − base, pareado por semilla)\n")
    print("| Grupo | Métrica | Base | Nueva | Δ pareado |\n|---|---|---|---|---|")
    for grupo, _, _ in GRUPOS:
        fa = {r["semilla"]: r for r in a["filas"] if r["grupo"] == grupo}
        fb = {r["semilla"]: r for r in b["filas"] if r["grupo"] == grupo}
        semillas = sorted(set(fa) & set(fb))
        for m in metricas:
            xa = [statistics.fmean(v[m] for v in fa[s]["vidas"]) for s in semillas]
            xb = [statistics.fmean(v[m] for v in fb[s]["vidas"]) for s in semillas]
            print(f"| {grupo} | {m} | {_ic(xa)} | {_ic(xb)} | {_ic([y - x for x, y in zip(xa, xb, strict=True)])} |")
    print("\n| Grupo | Versión | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media S1 / S2 / S3 por latido |")
    print("|---|---|---|---|---|---|")
    for grupo, _, _ in GRUPOS:
        for nombre, datos in (("base", a), ("nueva", b)):
            ind = [r["indicadores"] for r in datos["filas"] if r["grupo"] == grupo]
            n = sum(i["latidos"] for i in ind) or 1
            pot = " / ".join(f"{sum(i['potencia'][s] for i in ind) / n:.2f}" for s in ("S1", "S2", "S3"))
            print(f"| {grupo} | {nombre} | {n} | {sum(i['plazo'] for i in ind)} | {sum(i['s3_sin_recursos'] for i in ind)} | {pot} |")
    print("\n| Grupo | Causa de muerte | Vidas base | Vidas nueva |\n|---|---|---|---|")
    for grupo, _, _ in GRUPOS:
        ca = Counter(c for r in a["filas"] if r["grupo"] == grupo for c in r.get("causas", []))
        cb = Counter(c for r in b["filas"] if r["grupo"] == grupo for c in r.get("causas", []))
        for causa in sorted(set(ca) | set(cb)):
            print(f"| {grupo} | {causa} | {ca.get(causa, 0)} | {cb.get(causa, 0)} |")
    filas_b = [r for r in b["filas"] if r["indicadores"].get("estrategias")]
    if not filas_b:
        return
    print("\n| Grupo | Latidos | Plus decide | Reflejos | Reflejo interrumpe | Sustituciones |\n|---|---|---|---|---|---|")
    for grupo, _, _ in GRUPOS:
        ind = [r["indicadores"] for r in b["filas"] if r["grupo"] == grupo]
        print(f"| {grupo} | {sum(i['latidos'] for i in ind)} | {sum(i['plus'] for i in ind)} | {sum(i['reflejos'] for i in ind)} | "
              f"{sum(i['interrumpe'] for i in ind)} | {sum(i['sustituciones'] for i in ind)} |")
    total: Dict[str, Dict[str, int]] = {}
    for r in filas_b:
        for nombre, c in r["indicadores"]["estrategias"].items():
            t = total.setdefault(nombre, {"activa": 0, "ejecutada": 0, "abandonos": 0})
            for k in t:
                t[k] += c[k]
    print("\n| Estrategia de S1 (todos los grupos) | Latidos activa | Latidos ejecutada | Abandonos por agotamiento |\n|---|---|---|---|")
    for nombre, t in sorted(total.items(), key=lambda kv: -kv[1]["activa"]):
        print(f"| {nombre} | {t['activa']} | {t['ejecutada']} | {t['abandonos']} |")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="orden", required=True)
    e = sub.add_parser("ejecutar")
    e.add_argument("--raiz", required=True)
    e.add_argument("--mundo", required=True, choices=sorted(PROTOCOLO))
    e.add_argument("--salida", required=True)
    c = sub.add_parser("comparar")
    c.add_argument("base")
    c.add_argument("nueva")
    args = p.parse_args()
    if args.orden == "ejecutar":
        ejecutar(args.raiz, args.mundo, args.salida)
    else:
        comparar(args.base, args.nueva)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
