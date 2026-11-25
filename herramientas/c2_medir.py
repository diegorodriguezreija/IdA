"""C2: medición en reposo del coste por paso de dos versiones de IdA en Crafter.

Ejecuta, alternando el orden, ``herramientas/evaluar_crafter.py`` de cada árbol (cada árbol con su propio
código: el script inserta su raíz en ``sys.path``) con los parámetros de la medición oficial y plazo lógico,
de modo que el tiempo no cambia la conducta. Después:

1. comprueba que la conducta es la misma en las dos versiones (JSON sin los campos de tiempo);
2. resume ms por paso por versión y semilla (mediana, mínimo, máximo) y el cociente nueva / base;
3. con ``--perfil``, perfila con cProfile una ejecución de cada versión (semilla 31) y guarda los ``.prof``.

Uso (Windows, desde cualquier sitio):
    python c2_medir.py --base F:\\tmp\\ida_v4 --nueva F:\\code\\IdA --salida F:\\tmp\\c2 --reps 3 --pasos 3000 --perfil
"""

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from typing import Any, Dict, List

CLAVES_TIEMPO = {"tiempo_segundos", "ms_por_paso", "plazo_logico"}
ARGS_FIJOS = ["--vista", "oficial", "--sin-herencia", "--manual", "estricto", "--plazo-logico", "40", "--quiet"]


def _sin_tiempo(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: _sin_tiempo(v) for k, v in x.items() if k not in CLAVES_TIEMPO}
    if isinstance(x, list):
        return [_sin_tiempo(v) for v in x]
    return x


def _commit(raiz: str) -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=raiz, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "?"


def _comprobar_arbol(raiz: str) -> str:
    """Devuelve la ruta de ``ida`` que importa el script de ese árbol; para si no es la del árbol."""
    codigo = ("import sys, os; sys.path.insert(0, sys.argv[1]); import ida; "
              "print(os.path.dirname(os.path.abspath(ida.__file__)))")
    ruta = subprocess.run([sys.executable, "-c", codigo, raiz], capture_output=True, text=True,
                          check=True).stdout.strip()
    esperada = os.path.join(os.path.abspath(raiz), "ida")
    if os.path.normcase(ruta) != os.path.normcase(esperada):
        sys.exit(f"PARA: el árbol {raiz} importa ida desde {ruta}, no desde {esperada}")
    return ruta


def _ejecutar(raiz: str, semilla: int, pasos: int, salida: str, perfil: str = "") -> float:
    script = os.path.join(raiz, "herramientas", "evaluar_crafter.py")
    if not os.path.isfile(script):
        sys.exit(f"PARA: no existe {script}")
    cmd = [sys.executable]
    if perfil:
        cmd += ["-m", "cProfile", "-o", perfil]
    cmd += [script, "--pasos", str(pasos), "--semilla", str(semilla), "--salida", salida] + ARGS_FIJOS
    t0 = time.perf_counter()
    subprocess.run(cmd, cwd=raiz, check=True, stdout=subprocess.DEVNULL)
    return time.perf_counter() - t0


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True, help="árbol de la versión base (v4)")
    p.add_argument("--nueva", required=True, help="árbol de la versión nueva (v5)")
    p.add_argument("--salida", required=True)
    p.add_argument("--reps", type=int, default=3)
    p.add_argument("--pasos", type=int, default=3000)
    p.add_argument("--semillas", type=int, nargs="+", default=[31, 32])
    p.add_argument("--perfil", action="store_true", help="además, una ejecución con cProfile por versión (semilla 31)")
    a = p.parse_args()
    os.makedirs(a.salida, exist_ok=True)

    arboles = {"base": a.base, "nueva": a.nueva}
    info: Dict[str, Any] = {"python": sys.version, "plataforma": platform.platform(), "pasos": a.pasos,
                            "reps": a.reps, "semillas": a.semillas, "argumentos": ARGS_FIJOS}
    for v, r in arboles.items():
        info[v] = {"raiz": os.path.abspath(r), "commit": _commit(r), "ida": _comprobar_arbol(r)}
    print(json.dumps(info, indent=2, ensure_ascii=False))

    filas: List[Dict[str, Any]] = []
    for rep in range(a.reps):
        for i, s in enumerate(a.semillas):
            orden = ["base", "nueva"] if (rep + i) % 2 == 0 else ["nueva", "base"]
            for v in orden:
                fichero = os.path.join(a.salida, f"{v}_{s}_r{rep}.json")
                pared = _ejecutar(arboles[v], s, a.pasos, fichero)
                with open(fichero, encoding="utf-8") as f:
                    ms = float(json.load(f)["ms_por_paso"])
                filas.append({"version": v, "semilla": s, "rep": rep, "ms_por_paso": ms, "pared_s": round(pared, 2)})
                print(f"rep {rep} semilla {s} {v:5s}: {ms:.2f} ms/paso ({pared:.1f} s de pared)", flush=True)

    # 1. Conducta idéntica
    conducta_ok = True
    for s in a.semillas:
        with open(os.path.join(a.salida, f"base_{s}_r0.json"), encoding="utf-8") as f:
            b = _sin_tiempo(json.load(f))
        with open(os.path.join(a.salida, f"nueva_{s}_r0.json"), encoding="utf-8") as f:
            n = _sin_tiempo(json.load(f))
        igual = b == n
        conducta_ok &= igual
        print(f"Conducta semilla {s}: {'IDÉNTICA' if igual else 'DISTINTA'}")

    # 2. Resumen
    resumen: Dict[str, Any] = {}
    lineas = ["| Semilla | Versión | Mediana ms/paso | Mín | Máx | N |", "|---|---|---|---|---|---|"]
    for s in a.semillas:
        for v in ("base", "nueva"):
            xs = [f["ms_por_paso"] for f in filas if f["semilla"] == s and f["version"] == v]
            resumen[f"{v}_{s}"] = {"mediana": statistics.median(xs), "min": min(xs), "max": max(xs), "n": len(xs)}
            lineas.append(f"| {s} | {v} | {statistics.median(xs):.2f} | {min(xs):.2f} | {max(xs):.2f} | {len(xs)} |")
    lineas.append("")
    lineas.append("| Semilla | Cociente nueva/base (medianas) | Cociente (mínimos) |")
    lineas.append("|---|---|---|")
    for s in a.semillas:
        b, n = resumen[f"base_{s}"], resumen[f"nueva_{s}"]
        lineas.append(f"| {s} | {n['mediana'] / b['mediana']:.3f} | {n['min'] / b['min']:.3f} |")
    tabla = "\n".join(lineas)
    print(tabla)

    # 3. Perfiles
    if a.perfil:
        for v in ("base", "nueva"):
            prof = os.path.join(a.salida, f"perfil_{v}_31.prof")
            pared = _ejecutar(arboles[v], 31, a.pasos, os.path.join(a.salida, f"perfil_{v}_31.json"), perfil=prof)
            print(f"perfil {v}: {prof} ({pared:.1f} s)")

    with open(os.path.join(a.salida, "c2_resumen.json"), "w", encoding="utf-8") as f:
        json.dump({"info": info, "filas": filas, "resumen": resumen, "conducta_identica": conducta_ok},
                  f, indent=2, ensure_ascii=False)
    with open(os.path.join(a.salida, "c2_tabla.md"), "w", encoding="utf-8") as f:
        f.write(tabla + "\n")
    print("CONDUCTA: " + ("IDÉNTICA" if conducta_ok else "DISTINTA (PARA y avisa)"))


if __name__ == "__main__":
    main()
