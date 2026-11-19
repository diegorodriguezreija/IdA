"""Medición del arnés largo C.4 para semillas 11-30 con motivación real."""

import json
import os
import sys
import tempfile
import time
from typing import Any, Dict, List

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import crafter.objects as co  # noqa: E402
from herramientas.benchmark import PERFILES  # noqa: E402
from ida.ejecutor import ejecutar as vivir  # noqa: E402

CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def ejecutar_medicion(
    semillas: List[int], latidos: int = 3000, salida: str = "datos/benchmarks/c4_medicion_largo.json"
) -> Dict[str, Any]:
    resultados: List[Dict[str, Any]] = []
    t_inicio = time.perf_counter()
    latidos_totales = 0

    for sem in semillas:
        info_vida: Dict[str, Any] = {
            "semilla": sem,
            "bolsillo_plantas": {},
            "colocadas": 0,
            "maduradas": set(),
            "destruidas": [],
            "eat_plant_prev": 0,
            "comidas": 0,
            "dias_min_comida": {},
        }
        prev_adj: Dict[Any, List[str]] = {}

        def al_latir(
            org: Any,
            onda: Any,
            _r: Dict[str, Any],
            iv: Dict[str, Any] = info_vida,
        ) -> None:
            nonlocal prev_adj
            p = org.mundo.jugador
            w = org.mundo.env._world
            t = int(org.mundo.t)
            dia = t // 300
            food = int(p.inventory.get("food", 0))
            if dia not in iv["dias_min_comida"] or food < iv["dias_min_comida"][dia]:
                iv["dias_min_comida"][dia] = food

            eat_plant = int(p.achievements.get("eat_plant", 0))
            if eat_plant > iv["eat_plant_prev"]:
                iv["comidas"] += eat_plant - iv["eat_plant_prev"]
                iv["eat_plant_prev"] = eat_plant

            rn = None
            for sis in org.sistemas:
                if sis.nombre == "S2":
                    for c in sis.componentes():
                        if type(c).__name__ == "Estrategia":
                            rn = c.catalogo._por_nombre.get("refugio_nocturno")

            bolsillos = [tuple(b["pos"]) for b in getattr(rn, "bolsillos", [])]

            current_plants = {}
            for o in w.objects:
                pos = (int(o.pos[0]), int(o.pos[1]))
                if isinstance(o, co.Plant):
                    current_plants[pos] = o
                    if pos in bolsillos:
                        if pos not in iv["bolsillo_plantas"]:
                            iv["bolsillo_plantas"][pos] = {"created_t": t}
                            iv["colocadas"] += 1
                        if o.grown > 300 and pos not in iv["maduradas"]:
                            iv["maduradas"].add(pos)

            for pos in list(iv["bolsillo_plantas"].keys()):
                if pos not in current_plants:
                    causa = prev_adj.get(pos, ["desconocido"])
                    iv["destruidas"].append({"pos": pos, "t": t, "causa": causa})
                    del iv["bolsillo_plantas"][pos]

            new_adj: Dict[Any, List[str]] = {}
            for pos in current_plants:
                adj_monsters = []
                for dx, dy in CARDINAL:
                    c = (pos[0] + dx, pos[1] + dy)
                    obj = w[c][1]
                    if obj is not None and isinstance(obj, (co.Zombie, co.Skeleton, co.Cow)):
                        adj_monsters.append(type(obj).__name__.lower())
                    elif obj is not None and isinstance(obj, co.Arrow):
                        adj_monsters.append("flecha")
                if adj_monsters:
                    new_adj[pos] = adj_monsters
            prev_adj = new_adj

        with tempfile.TemporaryDirectory(prefix=f"ida_c4_largo_{sem}_") as td:
            res = vivir(
                "crafter",
                latidos=latidos,
                semilla=sem,
                generaciones=1,
                tabula_rasa=True,
                consola=False,
                datos=td,
                al_latir=al_latir,
                arquetipo_inicial=PERFILES["Equilibrado"],
            )[0]

        L = int(res.get("latidos", 0))
        latidos_totales += L
        vivo = bool(res.get("vivo"))
        causa = res.get("causa_muerte") if not vivo else None
        dia_muerte = L // 300 if not vivo else None

        registro = {
            "semilla": sem,
            "latidos": L,
            "vivo": vivo,
            "causa_muerte": causa,
            "dia_muerte": dia_muerte,
            "colocadas": info_vida["colocadas"],
            "maduradas": len(info_vida["maduradas"]),
            "comidas": info_vida["comidas"],
            "destruidas": info_vida["destruidas"],
            "min_comida_dias": info_vida["dias_min_comida"],
            "logros": res.get("puntuacion", {}).get("logros", []),
        }
        resultados.append(registro)
        print(
            f"Sem {sem:2d}: L={L:4d} vivo={vivo} causa={causa} dia_muerte={dia_muerte} "
            f"colocadas={registro['colocadas']} maduradas={registro['maduradas']} "
            f"comidas={registro['comidas']} destruidas={len(registro['destruidas'])} "
            f"min_comida={registro['min_comida_dias']}",
            flush=True,
        )

    t_total = time.perf_counter() - t_inicio
    latidos_vals = [r["latidos"] for r in resultados]
    media_latidos = float(np.mean(latidos_vals))
    mediana_latidos = float(np.median(latidos_vals))
    hambre_dia1 = sum(1 for r in resultados if r["causa_muerte"] == "hambre" and r["dia_muerte"] == 1)
    hambre_dia0 = sum(1 for r in resultados if r["causa_muerte"] == "hambre" and r["dia_muerte"] == 0)
    muertes_dia1_todas = sum(1 for r in resultados if r["dia_muerte"] == 1)
    vidas_450 = [r for r in resultados if r["latidos"] > 450]
    vidas_450_comen_planta = sum(1 for r in vidas_450 if r["comidas"] >= 1)
    ms_por_latido = (t_total / max(1, latidos_totales)) * 1000.0

    salida_datos = {
        "tiempo_total_s": t_total,
        "latidos_totales": latidos_totales,
        "ms_por_latido": ms_por_latido,
        "media_latidos": media_latidos,
        "mediana_latidos": mediana_latidos,
        "hambre_dia1": hambre_dia1,
        "hambre_dia0": hambre_dia0,
        "muertes_dia1_todas": muertes_dia1_todas,
        "vidas_mas_450": len(vidas_450),
        "vidas_mas_450_comen_planta": vidas_450_comen_planta,
        "resultados": resultados,
    }

    os.makedirs(os.path.dirname(salida), exist_ok=True)
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(salida_datos, f, indent=2)

    return salida_datos


if __name__ == "__main__":
    semillas_eval = list(range(11, 31))
    ejecutar_medicion(semillas_eval)
