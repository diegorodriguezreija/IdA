"""Diagnóstico de logros de Crafter: retoño (collect_sapling, place_plant), esqueleto (defeat_skeleton) y sueño (wake_up).

Ejecuta ``evaluar_crafter.evaluar`` (vista oficial, sin herencia, con estrategias) con un gancho en cada latido y
guarda una traza por episodio: acción ganadora y su motivo, las 3 mejores propuestas del Tribunal, luz, energía,
salud, comida, bebida, si duerme, espada, suelo y distancia al esqueleto y al zombi más cercanos a la vista
(9×7). Además cuenta los intentos de COGER hierba y si la acción está bloqueada (``Memoria.bloqueada``, si existe).

    python herramientas/diagnostico_logros.py --pasos 3000 --semilla 31 --manual estricto --salida diag.json
    python herramientas/diagnostico_logros.py --raiz <worktree de main> --pasos 3000 --semilla 31 --salida main.json

``--raiz`` ejecuta el código de otro árbol (p. ej. un worktree de ``main``, que no tiene ``--manual``). Es un
diagnóstico de pocas vidas, no una medición.
"""

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _motivo(m: str) -> str:
    return (m.split(":")[0] + ":" + m.split(":")[1][:28]) if ":" in m else m[:30]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--pasos", type=int, default=3000)
    p.add_argument("--semilla", type=int, default=31)
    p.add_argument("--manual", default=None, help="manual de Crafter (solo ramas con paso 2)")
    p.add_argument("--raiz", default=RAIZ, help="raíz del repositorio que se ejecuta")
    p.add_argument("--salida", default=None, help="JSON con la traza por episodio")
    args = p.parse_args()
    sys.path.insert(0, args.raiz)
    sys.path.insert(0, os.path.join(args.raiz, "herramientas"))
    import evaluar_crafter as ev
    from ida.core import latido
    from ida.core.vocabulario import Verbo

    eps: List[Dict[str, Any]] = []
    vivir_original = latido.Organismo.vivir

    def al_latir(org: Any, onda: Any) -> None:
        e = eps[-1]
        w, jug = org.mundo.env._world, org.mundo.jugador
        n = e["latidos"] = e["latidos"] + 1
        ej = onda.reactiva.ef.get("Accion", {}).get("Accion")
        c = ej.carga if ej is not None else {}
        verbo = c["verbo"].value if c.get("verbo") is not None else None
        clase, motivo = str(c.get("clase") or ""), str(c.get("motivo") or "")
        mem = org.memoria
        if verbo == "COGER" and clase == "hierba":
            e["coger_hierba"].append([n, int(bool(c.get("exito")))])
        if hasattr(mem, "bloqueada") and mem.bloqueada(Verbo.COGER, "hierba"):
            e["latidos_bloqueada"] += 1
        px, py = int(jug.pos[0]), int(jug.pos[1])

        def cerca(nombre: str) -> Any:
            return min((abs(o.pos[0] - px) + abs(o.pos[1] - py) for o in w.objects if type(o).__name__ == nombre
                        and abs(o.pos[0] - px) <= 4 and abs(o.pos[1] - py) <= 3), default=None)

        inv = jug.inventory
        top = [[str(x.get("motivo", ""))[:60], x.get("total")] for x in (onda.notas.get("evaluados") or [])[:3]]
        e["traza"].append([n, verbo, clase, motivo[:60], round(float(w.daylight), 2), inv["energy"], inv["health"], inv["food"],
                           inv["drink"], int(bool(jug.sleeping)), inv.get("wood_sword", 0) + inv.get("stone_sword", 0),
                           w[(px, py)][0], cerca("Skeleton"), cerca("Zombie"), top])
        e["logros"] = sorted(org.mundo.logros())

    def vivir(self: Any, max_latidos: int, al_latir_externo: Any = None) -> int:
        eps.append({"latidos": 0, "coger_hierba": [], "latidos_bloqueada": 0, "traza": [], "logros": []})
        r = vivir_original(self, max_latidos, al_latir=al_latir)
        eps[-1]["causa"] = self.causa_muerte if not self.soma.esta_vivo else None
        return r

    latido.Organismo.vivir = vivir   # type: ignore[method-assign]
    kw: Dict[str, Any] = {"vista": "oficial", "sin_herencia": True, "quiet": True}
    if args.manual:
        kw["manual"] = args.manual
    res = ev.evaluar(args.pasos, args.semilla, **kw)

    t: Counter = Counter()
    ganan_cerca_esqueleto: Counter = Counter()
    for e in eps:
        t["episodios"] += 1
        for logro in ("collect_sapling", "place_plant", "defeat_skeleton", "wake_up"):
            t[logro] += logro in e["logros"]
        t["coger_hierba"] += len(e["coger_hierba"])
        t["latidos_bloqueada"] += e["latidos_bloqueada"]
        anochecer = next((x for x in e["traza"] if x[0] > 50 and x[4] < 0.3), None)
        if anochecer is not None:
            t["llegan_al_anochecer"] += 1
            t["en_camino_al_anochecer"] += anochecer[11] == "path"
            t["duermen"] += any(x[9] for x in e["traza"])
        for x in e["traza"]:
            t["latidos_esqueleto_a_la_vista"] += x[12] is not None
            t["gana_huir_de_flecha"] += "huir de flecha" in x[3]
            t["huir_de_flecha_entre_3_mejores"] += any("huir de flecha" in y[0] for y in x[14])
            t["gana_acortar_distancia_a_esqueleto"] += "acortar distancia a esqueleto" in x[3]
            t["atacar_esqueleto"] += x[1] == "ATACAR" and x[2] == "esqueleto"
            t["gana_dormir_de_dia"] += "dormir de día" in x[3]
            if x[12] is not None and x[12] <= 4 and x[10] >= 1 and x[6] >= 5:
                ganan_cerca_esqueleto[_motivo(x[3])] += 1
    print(f"## raíz {args.raiz} · semilla {args.semilla} · {args.pasos} pasos · score {res['score']}")
    for k, v in t.items():
        print(f"- {k}: {v}")
    print("- ganadores con esqueleto a ≤ 4, espada y salud ≥ 5:", ganan_cerca_esqueleto.most_common(8))
    if args.salida:
        with open(args.salida, "w", encoding="utf-8") as f:
            json.dump({"score": res["score"], "semilla": args.semilla, "pasos": args.pasos, "episodios": eps}, f, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
