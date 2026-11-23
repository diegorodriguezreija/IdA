"""Arnés de equivalencia para la reorganización por Componentes.

Permite generar la línea base desde una referencia git (por defecto eaeadaa) y
comparar el árbol actual con la línea base para comprobar la equivalencia de conducta.

Uso:
    python herramientas/equivalencia.py --base [--ref eaeadaa]   genera la línea base
    python herramientas/equivalencia.py                           compara el árbol actual con la base
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Set

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

SEMILLAS = (31, 32)
PASOS = 3000
PLAZO_LOGICO = "40"
REF_DEFECTO = "eaeadaa"
DIR_DATOS = os.path.join(RAIZ, "datos", "equivalencia")
CLAVES_IGNORADAS: Set[str] = {"tiempo_segundos", "ms_por_paso", "plazo_logico"}


def resolver_hash_git(ref: str) -> str:
    """Obtiene el hash de commit completo para una referencia git."""
    res = subprocess.run(["git", "rev-parse", ref], capture_output=True, text=True, check=True, cwd=RAIZ)
    return res.stdout.strip()


def ejecutar_evaluacion(raiz_arbol: str, semilla: int, salida_json: str) -> None:
    """Ejecuta evaluar_crafter.py del árbol indicado con los parámetros fijados."""
    script_evaluar = os.path.join(raiz_arbol, "herramientas", "evaluar_crafter.py")
    cmd = [
        sys.executable,
        script_evaluar,
        "--pasos",
        str(PASOS),
        "--semilla",
        str(semilla),
        "--vista",
        "oficial",
        "--sin-herencia",
        "--manual",
        "estricto",
        "--plazo-logico",
        PLAZO_LOGICO,
        "--quiet",
        "--salida",
        salida_json,
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True, cwd=raiz_arbol)


def generar_base(ref: str) -> int:
    """Genera la línea base en datos/equivalencia/ clonando ref en un worktree temporal fuera del repo."""
    os.makedirs(DIR_DATOS, exist_ok=True)
    hash_ref = resolver_hash_git(ref)
    comando_exacto = f"{os.path.basename(sys.executable)} " + " ".join(sys.argv)

    tmp_dir = tempfile.gettempdir()
    wt_dir = os.path.join(tmp_dir, f"ida_wt_base_{os.getpid()}")
    try:
        subprocess.run(["git", "worktree", "add", "--detach", wt_dir, ref], capture_output=True, text=True, check=True, cwd=RAIZ)
        for s in SEMILLAS:
            salida = os.path.join(DIR_DATOS, f"base_{s}.json")
            ejecutar_evaluacion(wt_dir, s, salida)

        ref_txt = os.path.join(DIR_DATOS, "base_ref.txt")
        with open(ref_txt, "w", encoding="utf-8") as f:
            f.write(f"{hash_ref}\n{comando_exacto}\n")
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", wt_dir], capture_output=True, text=True, cwd=RAIZ)
    return 0


def comparar_estructuras(base: Any, actual: Any, ruta: str = "") -> List[str]:
    """Compara recursivamente dos estructuras ignorando CLAVES_IGNORADAS a cualquier profundidad."""
    diferencias: List[str] = []
    if isinstance(base, dict) and isinstance(actual, dict):
        todas_claves = sorted(set(base.keys()) | set(actual.keys()))
        for k in todas_claves:
            if k in CLAVES_IGNORADAS:
                continue
            subruta = f"{ruta}.{k}" if ruta else str(k)
            if k not in base:
                diferencias.append(f"{subruta}: <no presente en base> → {actual[k]!r}")
            elif k not in actual:
                diferencias.append(f"{subruta}: {base[k]!r} → <no presente en actual>")
            else:
                diferencias.extend(comparar_estructuras(base[k], actual[k], subruta))
    elif isinstance(base, list) and isinstance(actual, list):
        if len(base) != len(actual):
            diferencias.append(f"{ruta}: longitud {len(base)} → {len(actual)}")
        for i in range(min(len(base), len(actual))):
            subruta = f"{ruta}[{i}]"
            diferencias.extend(comparar_estructuras(base[i], actual[i], subruta))
    else:
        if base != actual:
            diferencias.append(f"{ruta}: {base!r} → {actual!r}")
    return diferencias


def comparar_con_base() -> int:
    """Ejecuta las mediciones en el árbol actual y las compara con la línea base."""
    for s in SEMILLAS:
        base_path = os.path.join(DIR_DATOS, f"base_{s}.json")
        if not os.path.exists(base_path):
            print(f"Error: falta el fichero de base {base_path}. Ejecuta primero con --base.", file=sys.stderr)
            print("EQUIVALENCIA: FALLA")
            return 1

    todas_identicas = True
    with tempfile.TemporaryDirectory(prefix="ida_equiv_actual_") as tmp_actual:
        for s in SEMILLAS:
            salida_actual = os.path.join(tmp_actual, f"actual_{s}.json")
            ejecutar_evaluacion(RAIZ, s, salida_actual)

            base_path = os.path.join(DIR_DATOS, f"base_{s}.json")
            with open(base_path, encoding="utf-8") as fb, open(salida_actual, encoding="utf-8") as fa:
                base_json: Dict[str, Any] = json.load(fb)
                actual_json: Dict[str, Any] = json.load(fa)

            diffs = comparar_estructuras(base_json, actual_json)
            if not diffs:
                print(f"{s}: IDÉNTICO")
            else:
                todas_identicas = False
                for d in diffs[:20]:
                    print(d)

    proc_inv = subprocess.run([sys.executable, os.path.join(RAIZ, "herramientas", "invariancia.py")], capture_output=True, text=True, cwd=RAIZ)
    if proc_inv.stdout:
        sys.stdout.write(proc_inv.stdout)
    if proc_inv.stderr:
        sys.stderr.write(proc_inv.stderr)

    if todas_identicas and proc_inv.returncode == 0:
        print("EQUIVALENCIA: OK")
        return 0

    print("EQUIVALENCIA: FALLA")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", action="store_true", help="genera la línea base")
    parser.add_argument("--ref", default=REF_DEFECTO, help=f"referencia git para la base (por defecto {REF_DEFECTO})")
    args = parser.parse_args()

    if args.base:
        return generar_base(args.ref)
    return comparar_con_base()


if __name__ == "__main__":
    raise SystemExit(main())
