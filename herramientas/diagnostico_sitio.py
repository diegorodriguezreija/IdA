"""Por qué ``Recinto`` no encuentra sitio en Crafter: instrumenta ``Recinto._requisitos`` sin cambiar la conducta.

Cuando ``_requisitos`` no devuelve nada con luz < 0,5, clasifica el latido:
- ``sin acciones que cierren``: la memoria no conoce ninguna acción que cierre un acceso;
- ``material de cierre inalcanzable``: el planificador no sabe conseguir lo que consume ninguna de ellas;
- ``sin candidatos``: ni contando el coste del material hay una forma de 1-3 casillas posible;
- ``candidatos y ninguno completable``: hay candidatos, pero el plan exacto (con el modelo del cuerpo) no cierra ninguno
  de los ``CANDIDATOS_EXACTOS`` más baratos. Para estos, cuenta la forma de esos candidatos: (casillas interiores,
  casillas que cavar, accesos, cierres sin material).

    python herramientas/diagnostico_sitio.py --pasos 3000 --semilla 31

Es un diagnóstico de una vida corta, no una medición. Se lanza solo (sin otros procesos): la guillotina del latido corta
latidos con carga y cambia la vida.
"""

import argparse
import os
import sys
from collections import Counter
from typing import Any, Optional

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--pasos", type=int, default=3000)
    p.add_argument("--semilla", type=int, default=31)
    p.add_argument("--plazo-logico", type=float, default=None, metavar="OPS",
                   help="guillotina lógica (operaciones por ms de plazo), como en evaluar_crafter.py")
    args = p.parse_args()
    import evaluar_crafter as ev
    from ida.sistemas import proteger as P

    razones: Counter = Counter()
    formas: Counter = Counter()
    original = P.Recinto._requisitos

    def envuelto(self: Any, ctx: Any, modelo: Any, aqui: Any, cara: Any, dist: Any, previo: Any, hogar: Any) -> Optional[Any]:
        r = original(self, ctx, modelo, aqui, cara, dist, previo, hogar)
        amb = ctx.onda.ev("Ambiente").get("ambiente")
        if r is not None or amb is None or float(amb.carga.get("luz", 1.0)) >= 0.5:
            return r
        cache: dict = {}
        utiles = []
        for c in modelo.cerradores:
            costes = [self._coste_objeto(ctx, k, modelo.inv, cache) for k, _ in c.requiere]
            if all(x is not None for x in costes):
                utiles.append(sum((x or 0.0) * n for x, (_, n) in zip(costes, c.requiere, strict=True)))
        if not modelo.cerradores:
            razones["sin acciones que cierren"] += 1
        elif not utiles:
            razones["material de cierre inalcanzable para el planificador"] += 1
        else:
            cands = P.candidatos(modelo, aqui, dist, hogar, min(utiles))
            if not cands:
                razones["sin candidatos ni contando el material"] += 1
            else:
                razones["candidatos y ninguno completable"] += 1
                for s in cands[:P.CANDIDATOS_EXACTOS]:
                    formas[(len(s.interior), len(s.excavar), len(s.accesos), s.falta)] += 1
        return r

    P.Recinto._requisitos = envuelto   # type: ignore[method-assign]
    ev.evaluar(args.pasos, args.semilla, vista="oficial", sin_herencia=True, quiet=True, manual="estricto", sin_estrategias_propias=True,
                **({"plazo_logico": args.plazo_logico} if args.plazo_logico else {}))
    print(f"## semilla {args.semilla} · {args.pasos} pasos · latidos con luz < 0,5 en que _requisitos no devuelve nada")
    for k, v in razones.most_common():
        print(f"- {k}: {v}")
    total = sum(formas.values())
    print(f"\nForma de los candidatos no completables ({total}): (interior, cavar, accesos, cierres sin material) → veces")
    for f, v in formas.most_common(10):
        print(f"- {f}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
