"""Diagnóstico del paso 3 (proteger X) en Crafter: noches dentro de un recinto, wake_up y propuestas de Proteger.

Ejecuta ``evaluar_crafter.evaluar`` (vista oficial, sin herencia) con un gancho en cada latido y cuenta:
- **noches:** tramos con luz < 0,3. Una noche «termina dentro de un recinto» si, en su último latido oscuro, el jugador
  está en un recinto **real** del mundo (no en lo que cree IdA): un conjunto conectado de 1-3 casillas transitables sin
  ninguna vecina transitable para un zombi (hierba, arena o camino). Las noches que el episodio no termina se cuentan aparte;
- episodios con ``wake_up``, causas de muerte y latidos ganados por Proteger;
- **propuestas de Proteger:** motivos de unas 20 propuestas a lo largo del anochecer (luz de 0,7 a 0,2) del episodio en que
  más propone, ganen o no, con su total en el Tribunal.

    python herramientas/diagnostico_proteger.py --pasos 3000 --semilla 31 --sin-estrategias-propias

Es un diagnóstico de pocas vidas, no una medición.
"""

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))

TRANSITABLES_ZOMBI = {"grass", "sand", "path"}
OSCURO = 0.3


def recinto_real(world: Any, pos: Tuple[int, int]) -> bool:
    """El jugador está en 1-3 casillas transitables conectadas sin vecinas por las que pueda llegar un zombi."""
    comp, frontera = {pos}, [pos]
    while frontera:
        x, y = frontera.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            v = (x + dx, y + dy)
            if v in comp or not (0 <= v[0] < world.area[0] and 0 <= v[1] < world.area[1]):
                continue
            mat, obj = world[v]
            if mat in TRANSITABLES_ZOMBI and obj is None:
                comp.add(v)
                if len(comp) > 3:
                    return False
                frontera.append(v)
            elif mat in TRANSITABLES_ZOMBI:      # ocupada por una criatura: no está cerrada
                return False
    return True


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--pasos", type=int, default=3000)
    p.add_argument("--semilla", type=int, default=31)
    p.add_argument("--manual", default="estricto")
    p.add_argument("--sin-estrategias-propias", action="store_true")
    p.add_argument("--mecanismos", nargs="*", default=[])
    p.add_argument("--propuestas", type=int, default=20, help="propuestas de Proteger que se muestran en un anochecer")
    p.add_argument("--salida", default=None, help="JSON con el resumen por episodio")
    p.add_argument("--plazo-logico", type=float, default=None, metavar="OPS",
                   help="guillotina lógica (operaciones por ms de plazo), como en evaluar_crafter.py")
    args = p.parse_args()
    import evaluar_crafter as ev
    from ida.core import latido

    eps: List[Dict[str, Any]] = []
    anochecer: List[Tuple[int, int, float, str, float, bool]] = []
    vivir_original = latido.Organismo.vivir

    def al_latir(org: Any, onda: Any) -> None:
        e = eps[-1]
        w, jug = org.mundo.env._world, org.mundo.jugador
        n = e["latidos"] = e["latidos"] + 1
        luz = float(w.daylight)
        pos = (int(jug.pos[0]), int(jug.pos[1]))
        dentro = recinto_real(w, pos)
        oscuro = luz < OSCURO
        if oscuro and not e["_oscuro"]:
            e["noches"].append({"inicio": n, "fin": None, "dentro_al_final": None, "latidos_dentro": 0})
        if oscuro:
            e["noches"][-1]["latidos_dentro"] += int(dentro)
            e["noches"][-1]["_ultimo_dentro"] = dentro
        elif e["_oscuro"]:
            noche = e["noches"][-1]
            noche["fin"], noche["dentro_al_final"] = n - 1, bool(noche.pop("_ultimo_dentro", False))
        e["_oscuro"] = oscuro
        e["_anochecido"] = e["_anochecido"] or luz < 0.2       # solo el primer anochecer de cada episodio
        e["latidos_dentro"] += int(dentro)
        ej = onda.reactiva.ef.get("Accion", {}).get("Accion")
        motivo = str(ej.carga.get("motivo") or "") if ej is not None else ""
        if motivo.startswith("proteger:"):
            e["gana_proteger"][motivo.split("·")[0].strip()[:40]] += 1
        if 0.2 <= luz <= 0.7 and not e["_anochecido"]:
            evaluados = onda.notas.get("evaluados") or []
            for i, x in enumerate(evaluados):
                if str(x.get("motivo", "")).startswith("proteger:"):
                    anochecer.append((e["indice"], n, round(luz, 2), str(x["motivo"]), float(x["total"]), i == 0))
        e["logros"] = sorted(org.mundo.logros())

    def vivir(self: Any, max_latidos: int, al_latir_externo: Any = None) -> int:
        eps.append({"indice": len(eps), "latidos": 0, "noches": [], "_oscuro": False, "_anochecido": False, "latidos_dentro": 0,
                    "gana_proteger": Counter(), "logros": []})
        r = vivir_original(self, max_latidos, al_latir=al_latir)
        e = eps[-1]
        e["causa"] = self.causa_muerte if not self.soma.esta_vivo else None
        if e["noches"] and e["noches"][-1]["fin"] is None:
            e["noches"][-1].pop("_ultimo_dentro", None)
        return r

    latido.Organismo.vivir = vivir   # type: ignore[method-assign]
    kw: Dict[str, Any] = {"vista": "oficial", "sin_herencia": True, "quiet": True, "manual": args.manual,
                          "sin_estrategias_propias": args.sin_estrategias_propias, "mecanismos": args.mecanismos,
                          "contar": "latidos"}    # --pasos son latidos, como en sus datos (contabilidad anterior a P0)
    if args.plazo_logico:
        kw["plazo_logico"] = args.plazo_logico
    res = ev.evaluar(args.pasos, args.semilla, **kw)

    noches = [x for e in eps for x in e["noches"]]
    completas = [x for x in noches if x["fin"] is not None]
    causas = Counter(str(e.get("causa")) for e in eps)
    gana: Counter = Counter()
    for e in eps:
        gana.update(e["gana_proteger"])
    print(f"## semilla {args.semilla} · {args.pasos} pasos · mecanismos {args.mecanismos or 'ninguno'} · "
          f"{'sin' if args.sin_estrategias_propias else 'con'} estrategias propias · score {res['score']}")
    print(f"- episodios: {len(eps)}; pasos por episodio: {sum(e['latidos'] for e in eps) / max(1, len(eps)):.1f} latidos")
    print(f"- episodios con wake_up: {sum('wake_up' in e['logros'] for e in eps)} de {len(eps)}")
    print(f"- noches (luz < {OSCURO}): {len(noches)}; terminadas: {len(completas)}; "
          f"terminan dentro de un recinto real: {sum(1 for x in completas if x['dentro_al_final'])}")
    print(f"- latidos de noche dentro de un recinto real: {sum(x['latidos_dentro'] for x in noches)} de "
          f"{sum(((x['fin'] or 0) - x['inicio'] + 1) for x in completas)} (noches terminadas, aprox.)")
    print(f"- causas de muerte: {dict(causas.most_common())}")
    print(f"- latidos que gana Proteger, por motivo: {dict(gana.most_common(10))}")
    por_ep = Counter(x[0] for x in anochecer)
    elegido: Optional[int] = min(por_ep, key=lambda i: (-por_ep[i], i)) if por_ep else None
    tramo = [x for x in anochecer if x[0] == elegido]
    if tramo:
        paso = max(1, len(tramo) // args.propuestas)
        print(f"- propuestas de Proteger en el anochecer del episodio {elegido} (el que más propone; luz 0,7 a 0,2; {len(tramo)} en total):")
        for _, n, luz, motivo, total, gana_x in tramo[::paso][:args.propuestas]:
            print(f"  latido {n:4d} · luz {luz:.2f} · total {total:.3f}{' (gana)' if gana_x else ''} · {motivo}")
    if args.salida:
        with open(args.salida, "w", encoding="utf-8") as f:
            json.dump({"score": res["score"], "episodios": [{k: (dict(v) if isinstance(v, Counter) else v) for k, v in e.items()
                                                             if not k.startswith("_")} for e in eps]}, f, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
