"""C2: compara dos perfiles de cProfile (base y nueva) de IdA.

Como la reorganización movió ficheros (``ida/core/x.py`` → ``ida/nucleo/x.py``...), compara a tres niveles:
- zonas: IdA, entorno (crafter y sus dependencias), Python y resto;
- ficheros de IdA (ruta relativa a la raíz del árbol);
- funciones por nombre (sin fichero, agregando homónimas como ``reactiva``), que sobreviven a los movimientos.

Uso:
    python comparar_perfiles.py BASE.prof RAIZ_BASE NUEVA.prof RAIZ_NUEVA [--top 40] [--salida informe.md]
"""

import argparse
import os
import pstats
from collections import defaultdict
from typing import Dict, List, Tuple

Clave = Tuple[str, int, str]


def _norm(ruta: str) -> str:
    return os.path.normcase(os.path.abspath(ruta)).replace("\\", "/")


def _cargar(prof: str, raiz: str) -> Dict[str, Dict[str, Tuple[float, float, int]]]:
    """Devuelve {zonas, ficheros, funciones} con (tottime, cumtime, ncalls) agregados."""
    st = pstats.Stats(prof)
    raiz_n = _norm(raiz) + "/"
    zonas: Dict[str, List[float]] = defaultdict(lambda: [0.0, 0.0, 0])
    ficheros: Dict[str, List[float]] = defaultdict(lambda: [0.0, 0.0, 0])
    funciones: Dict[str, List[float]] = defaultdict(lambda: [0.0, 0.0, 0])
    for (fich, _linea, func), (_cc, nc, tt, ct, _callers) in st.stats.items():  # type: ignore[attr-defined]
        f = _norm(fich) if fich not in ("~", "") else "~"
        if f.startswith(raiz_n + "ida/"):
            zona, rel = "IdA", f[len(raiz_n):]
        elif f.startswith(raiz_n):
            zona, rel = "herramientas", f[len(raiz_n):]
        elif "site-packages" in f:
            paquete = f.split("site-packages/")[1].split("/")[0]
            zona, rel = f"entorno:{paquete}", ""
        else:
            zona, rel = "python", ""
        zonas[zona][0] += tt
        zonas[zona][2] += nc
        if rel:
            ficheros[rel][0] += tt
            ficheros[rel][2] += nc
            nombre = func   # sin fichero: sobrevive a los movimientos
            funciones[nombre][0] += tt
            funciones[nombre][1] = max(funciones[nombre][1], ct)
            funciones[nombre][2] += nc
        elif zona == "python":
            nombre = f"<python>:{func}"
            funciones[nombre][0] += tt
            funciones[nombre][2] += nc
    total = sum(v[0] for v in zonas.values())
    return {"zonas": dict(zonas), "ficheros": dict(ficheros), "funciones": dict(funciones),
            "total": {"total": [total, total, 0]}}  # type: ignore[dict-item]


def _tabla(titulo: str, b: Dict, n: Dict, top: int, por_delta: bool = True) -> List[str]:
    claves = set(b) | set(n)
    filas = []
    for k in claves:
        tb = b.get(k, [0.0, 0.0, 0])
        tn = n.get(k, [0.0, 0.0, 0])
        filas.append((k, tb[0], tn[0], tn[0] - tb[0], tb[2], tn[2]))
    filas.sort(key=lambda r: -abs(r[3]) if por_delta else -r[2])
    out = [f"### {titulo}", "", "| Clave | tottime base (s) | tottime nueva (s) | Δ (s) | llamadas base | llamadas nueva |",
           "|---|---|---|---|---|---|"]
    for k, tb, tn, d, cb, cn in filas[:top]:
        out.append(f"| `{k}` | {tb:.2f} | {tn:.2f} | {d:+.2f} | {cb} | {cn} |")
    return out + [""]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("base_prof")
    p.add_argument("base_raiz")
    p.add_argument("nueva_prof")
    p.add_argument("nueva_raiz")
    p.add_argument("--top", type=int, default=40)
    p.add_argument("--salida", default=None)
    a = p.parse_args()
    b = _cargar(a.base_prof, a.base_raiz)
    n = _cargar(a.nueva_prof, a.nueva_raiz)
    tb, tn = b["total"]["total"][0], n["total"]["total"][0]
    lineas = ["## Comparación de perfiles (cProfile; tottime agregado)", "",
              f"Total perfilado: base {tb:.2f} s, nueva {tn:.2f} s, Δ {tn - tb:+.2f} s ({(tn / tb - 1) * 100:+.1f} %).", ""]
    lineas += _tabla("Por zona", b["zonas"], n["zonas"], 20)
    lineas += _tabla("Ficheros de IdA, por Δ", b["ficheros"], n["ficheros"], a.top)
    lineas += _tabla("Funciones, por Δ", b["funciones"], n["funciones"], a.top)
    lineas += _tabla("Funciones más caras en la nueva", b["funciones"], n["funciones"], 25, por_delta=False)
    texto = "\n".join(lineas)
    print(texto)
    if a.salida:
        with open(a.salida, "w", encoding="utf-8") as f:
            f.write(texto + "\n")


if __name__ == "__main__":
    main()
