"""Diagnóstico del paso 0: ¿qué fracción de las propuestas de PerseguirMetas gana el Tribunal y contra quién pierde?

Una vida de Crafter con semilla. Para cada latido en que ``PerseguirMetas`` propone, clasifica el resultado:
gana, acecha, queda fuera de los 8 mejores que registra el Tribunal (``onda.notas["evaluados"]``) o pierde
contra otro candidato (sistema y comienzo del motivo), con los totales medios del ganador y de PerseguirMetas.

    python herramientas/diagnostico_tribunal.py --semilla 31 --sin-estrategias-propias
    python herramientas/diagnostico_tribunal.py --semilla 31

Es un diagnóstico de una vida, no una medición (docs/PROPUESTA_PASO0.md, apartado a).
"""

import argparse
import os
import sys
import tempfile
from collections import defaultdict
from typing import Any, Dict, List

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _media(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def _etiqueta(e: Dict[str, Any]) -> str:
    motivo = str(e["motivo"])
    cabeza = motivo.split(":")[0] if ":" in motivo[:25] else " ".join(motivo.split()[:2])
    return f"{e['sistema']} · {cabeza}"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--semilla", type=int, default=31)
    p.add_argument("--latidos", type=int, default=1500)
    p.add_argument("--sin-estrategias-propias", action="store_true", help="el suelo, sin estrategias del mundo")
    p.add_argument("--raiz", default=RAIZ, help="raíz del repositorio que se ejecuta (p. ej. un worktree de otro commit)")
    args = p.parse_args()
    sys.path.insert(0, args.raiz)
    from ida.nucleo.mundo import Registro
    from ida.ejecutor import ejecutar
    from ida.mundos import cargar
    from ida.sistemas.s3 import PerseguirMetas

    if args.sin_estrategias_propias:
        original = cargar("crafter").registro   # sin estrategias propias, pero con su cuerpo (D10)
        cargar("crafter").registro = lambda self: Registro(cuerpo=original(self).cuerpo)
    propuestos: List[int] = []
    original = PerseguirMetas.proponer

    def proponer(self: Any, ctx: Any, verbo: Any, objetivo: str, a: float, c: float, motivo: str, clase: str = "", **d: Any) -> None:
        propuestos.append(ctx.latido)
        original(self, ctx, verbo, objetivo, a, c, motivo, clase, **d)

    setattr(PerseguirMetas, "proponer", proponer)  # noqa: B010 (se envuelve para contar)
    resultados = {"gana": 0, "acecha": 0, "fuera_top8": 0, "pierde": 0}
    totales: Dict[str, List[float]] = {"gana": [], "pierde": []}
    rivales: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"n": 0, "rival": [], "metas": []})

    def al(o: Any, onda: Any, r: Any) -> None:
        if not propuestos or propuestos[-1] != r["latido"]:
            return
        ev = onda.notas.get("evaluados", [])
        meta = next((e for e in ev if str(e["motivo"]).startswith("metas:")), None)
        dec, motivo = r["decision"], str(r.get("motivo", ""))
        if meta is None:
            resultados["fuera_top8"] += 1
        elif motivo.startswith("acecha: metas:"):
            resultados["acecha"] += 1
        elif motivo == meta["motivo"] and dec["objetivo"] == meta["objetivo"]:
            resultados["gana"] += 1
            totales["gana"].append(meta["total"])
        else:
            ganador = next((e for e in ev if e["objetivo"] == dec["objetivo"] and e["motivo"] == motivo), ev[0])
            resultados["pierde"] += 1
            totales["pierde"].append(meta["total"])
            g = rivales[_etiqueta(ganador)]
            g["n"] += 1
            g["rival"].append(ganador["total"])
            g["metas"].append(meta["total"])

    with tempfile.TemporaryDirectory() as datos:
        res = ejecutar("crafter", latidos=args.latidos, semilla=args.semilla, consola=False, datos=datos, al_latir=al,
                       opciones_mundo={"vista": "oficial"})
    n = len(propuestos)
    condicion = "suelo" if args.sin_estrategias_propias else "con estrategias"
    print(f"## {condicion}, semilla {args.semilla}: {res[0]['latidos']} latidos, {n} propuestas de PerseguirMetas, "
          f"{len(res[0]['puntuacion']['logros'])} logros")
    for k, v in resultados.items():
        print(f"- {k}: {v} ({100 * v / max(1, n):.1f} %)")
    print(f"- total medio de PerseguirMetas: al ganar {_media(totales['gana']):.3f}; al perder {_media(totales['pierde']):.3f}")
    print("| Pierde contra | Veces | % de derrotas | Total medio del ganador | Total medio de PerseguirMetas |")
    print("|---|---|---|---|---|")
    for k, g in sorted(rivales.items(), key=lambda kv: -kv[1]["n"]):
        print(f"| {k} | {g['n']} | {100 * g['n'] / max(1, resultados['pierde']):.0f} % | {_media(g['rival']):.3f} | {_media(g['metas']):.3f} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
