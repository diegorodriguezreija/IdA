"""Diagnóstico de bucles de PerseguirMetas: rachas de MOVER al mismo lugar y propuestas más repetidas.

Una vida de Crafter con semilla. Sirvió para reproducir el bucle de «ir a mesa» del paso 5 (semilla 31, sin
estrategias propias, con el código de 5cc9c85: ``--raiz`` apuntando a un worktree de ese commit) y comprobar que
desapareció. Con ``--detalle`` imprime cada latido en que se propone ir hacia una clase (posición del jugador,
instancias de esa clase a la vista y quién ganó el Tribunal).

    python herramientas/diagnostico_bucle.py --semilla 31 --sin-estrategias-propias
    python herramientas/diagnostico_bucle.py --semilla 31 --sin-estrategias-propias --detalle mesa --raiz <worktree>
"""

import argparse
import os
import sys
import tempfile
from collections import Counter
from typing import Any, List, Optional, Tuple

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--semilla", type=int, default=31)
    p.add_argument("--latidos", type=int, default=1500)
    p.add_argument("--sin-estrategias-propias", action="store_true", help="el suelo, sin estrategias del mundo")
    p.add_argument("--detalle", default="", help="clase cuyo «ir a <clase>» se detalla latido a latido (p. ej. mesa)")
    p.add_argument("--raiz", default=RAIZ, help="raíz del repositorio que se ejecuta (p. ej. un worktree de otro commit)")
    args = p.parse_args()
    sys.path.insert(0, args.raiz)
    from ida.ejecutor import ejecutar
    from ida.mundos import cargar

    if args.sin_estrategias_propias:
        cargar("crafter").estrategias_propias = lambda self: {}
    props: List[Tuple[int, str, str, str]] = []
    detalle: List[Tuple[Any, ...]] = []

    def al(o: Any, onda: Any, r: Any) -> None:
        ev = onda.notas.get("evaluados", [])
        meta = next((e for e in ev if str(e["motivo"]).startswith("metas:")), None)
        if meta is None:
            return
        props.append((r["latido"], meta["verbo"], meta["objetivo"], meta["motivo"]))
        if args.detalle and f"ir a {args.detalle}" in meta["motivo"]:
            m = o.mundo
            pos = tuple(int(v) for v in m.jugador.pos)
            instancias = [c[2] for c in m._cosas() if c[1] == args.detalle][:2]
            ganador = next((e["motivo"][:45] for e in ev if e["objetivo"] == r["decision"]["objetivo"]), "")
            detalle.append((r["latido"], pos, instancias, meta["objetivo"], round(meta["total"], 3), r["decision"]["verbo"], ganador))

    with tempfile.TemporaryDirectory() as datos:
        res = ejecutar("crafter", latidos=args.latidos, semilla=args.semilla, consola=False, datos=datos, al_latir=al,
                       opciones_mundo={"vista": "oficial"})
    racha, mejor, previo = 0, (0, None), None
    maxima: Tuple[int, Optional[Tuple[int, str, str, str]]] = mejor
    for t in props:
        clave = (t[1], t[2])
        racha = racha + 1 if clave == previo and t[1] == "MOVER" else 1
        previo = clave
        if racha > maxima[0]:
            maxima = (racha, t)
    print(f"{res[0]['latidos']} latidos, {len(res[0]['puntuacion']['logros'])} logros, {len(props)} propuestas de PerseguirMetas")
    print("- racha máxima de MOVER al mismo lugar:", maxima)
    print("- propuestas más repetidas:", Counter((t[1], t[2]) for t in props).most_common(3))
    if args.detalle:
        print(f"- latidos con «ir a {args.detalle}»: {len(detalle)}")
        for f in detalle[:12]:
            print("  (latido, jugador, instancias, destino, total, verbo decidido, motivo ganador):", f)
        print("  posiciones del jugador:", Counter(f[1] for f in detalle).most_common(4))
        print("  ganadores:", Counter(f[6] for f in detalle).most_common(5))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
