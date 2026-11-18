"""Diagnóstico del Paso 1 de C.3b: Presencia de vacas en el área de campeo (<= 17) frente a percepción.

Mide cada 50 latidos en semillas 11-20 (3000 latidos, motivación real):
1. Vacas que existen realmente a <= 17 del recinto de la última noche (lectura del mundo).
2. Vacas percibidas por el individuo en esos 50 latidos (Exterocepcion).
3. Casillas a <= 17 del recinto no visitadas en los últimos 150 latidos.
"""

import argparse
import os
import sys
import tempfile
from typing import Any, Dict

import crafter.objects

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from herramientas.benchmark import PERFILES  # noqa: E402
from ida.ejecutor import ejecutar as vivir  # noqa: E402


def diagnosticar_vida(semilla: int, max_latidos: int = 3000) -> Dict[str, Any]:
    estado: Dict[str, Any] = {
        "semilla": semilla,
        "latidos_vividos": 0,
        "causa_muerte": None,
        "vivo": True,
        "ultimo_recinto_e2": None,
        "visitas": {},
        "vacas_vistas_ventana": set(),
        "ventanas": [],
    }

    def al_latir(org: Any, onda: Any, _r: Dict[str, Any]) -> None:
        p = org.mundo.jugador
        pos = (int(p.pos[0]), int(p.pos[1]))
        ciclo = onda.ciclo
        estado["visitas"][pos] = ciclo

        # Detectar recinto si está en dormir
        est = onda.estrategias.get("S2:refugio_nocturno:cobijo")
        paso = est.carga.get("paso") if est is not None else None
        if isinstance(paso, dict) and paso.get("fase") == "dormir" and paso.get("mina") is not None:
            e0, (dx, dy) = paso["mina"]
            e2 = (e0[0] + 2 * dx, e0[1] + 2 * dy)
            estado["ultimo_recinto_e2"] = e2

        # Vacas percibidas en Exterocepcion en este latido
        ext = onda.ev("Exterocepcion")
        if ext:
            for pz in ext.values():
                if pz.clase == "vaca":
                    pos_v = pz.carga.get("datos", {}).get("pos")
                    if pos_v is not None:
                        estado["vacas_vistas_ventana"].add(tuple(pos_v))
                    else:
                        estado["vacas_vistas_ventana"].add(f"vaca_{pz.id}")

        if ciclo % 50 == 0:
            e2 = estado["ultimo_recinto_e2"]
            w = org.mundo.env._world
            area = w.area

            total_vacas_mundo = len([obj for obj in w.objects if isinstance(obj, crafter.objects.Cow)])

            if e2 is not None:
                vacas_reales = [
                    (int(obj.pos[0]), int(obj.pos[1]))
                    for obj in w.objects
                    if isinstance(obj, crafter.objects.Cow)
                    and (abs(int(obj.pos[0]) - e2[0]) + abs(int(obj.pos[1]) - e2[1]) <= 17)
                ]

                casillas_recinto = [
                    (x, y)
                    for x in range(area[0])
                    for y in range(area[1])
                    if (abs(x - e2[0]) + abs(y - e2[1]) <= 17)
                ]
                no_visitadas_150 = [
                    c for c in casillas_recinto
                    if (ciclo - estado["visitas"].get(c, -99999)) > 150
                ]

                snap = {
                    "ciclo": ciclo,
                    "e2": e2,
                    "vacas_mundo": total_vacas_mundo,
                    "vacas_reales_recinto": vacas_reales,
                    "num_vacas_reales": len(vacas_reales),
                    "vacas_percibidas": len(estado["vacas_vistas_ventana"]),
                    "casillas_campeo": len(casillas_recinto),
                    "no_visitadas_150": len(no_visitadas_150),
                    "pct_no_visitadas": round(100.0 * len(no_visitadas_150) / max(1, len(casillas_recinto)), 1),
                }
            else:
                snap = {
                    "ciclo": ciclo,
                    "e2": None,
                    "vacas_mundo": total_vacas_mundo,
                    "vacas_reales_recinto": [],
                    "num_vacas_reales": 0,
                    "vacas_percibidas": len(estado["vacas_vistas_ventana"]),
                    "casillas_campeo": 0,
                    "no_visitadas_150": 0,
                    "pct_no_visitadas": 0.0,
                }
            estado["ventanas"].append(snap)
            estado["vacas_vistas_ventana"] = set()

    with tempfile.TemporaryDirectory(prefix=f"diag_vaca_{semilla}_") as td:
        res = vivir("crafter", latidos=max_latidos, semilla=semilla, generaciones=1, tabula_rasa=True,
                    consola=False, datos=td, al_latir=al_latir, arquetipo_inicial=PERFILES["Equilibrado"])[0]

    estado["vivo"] = bool(res.get("vivo"))
    estado["causa_muerte"] = res.get("causa_muerte")
    estado["latidos_vividos"] = int(res.get("latidos", 0))
    return estado


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--semillas", type=int, nargs="*", default=list(range(11, 21)))
    p.add_argument("--latidos", type=int, default=3000)
    args = p.parse_args()

    resultados = []
    print(f"=== DIAGNÓSTICO DE VACAS C.3b (semillas {args.semillas[0]}-{args.semillas[-1]}, latidos {args.latidos}) ===", flush=True)

    ventanas_con_recinto = 0
    suma_vacas_reales = 0
    suma_vacas_percibidas = 0
    suma_no_visitadas_pct = 0.0

    # Para ventanas con recinto tras la primera noche (ciclo >= 300)
    ventanas_dia1_mas = 0
    vacas_reales_dia1_mas = 0
    vacas_percibidas_dia1_mas = 0

    for sem in args.semillas:
        info = diagnosticar_vida(sem, max_latidos=args.latidos)
        resultados.append(info)
        v_recinto = [v for v in info["ventanas"] if v["e2"] is not None]
        v_d1 = [v for v in v_recinto if v["ciclo"] >= 300]

        reales_media = sum(v["num_vacas_reales"] for v in v_recinto) / max(1, len(v_recinto))
        perc_media = sum(v["vacas_percibidas"] for v in v_recinto) / max(1, len(v_recinto))
        no_vis_media = sum(v["pct_no_visitadas"] for v in v_recinto) / max(1, len(v_recinto))

        print(
            f"Semilla {sem:2d}: L={info['latidos_vividos']:4d} causa={info['causa_muerte']} "
            f"ventanas={len(info['ventanas'])} (con recinto={len(v_recinto)}) | "
            f"vacas reales recinto (media)={reales_media:.2f} | vacas percibidas (media)={perc_media:.2f} | "
            f"casillas no visitadas >150={no_vis_media:.1f} %",
            flush=True,
        )
        for v in v_recinto:
            ventanas_con_recinto += 1
            suma_vacas_reales += v["num_vacas_reales"]
            suma_vacas_percibidas += v["vacas_percibidas"]
            suma_no_visitadas_pct += v["pct_no_visitadas"]

        for v in v_d1:
            ventanas_dia1_mas += 1
            vacas_reales_dia1_mas += v["num_vacas_reales"]
            vacas_percibidas_dia1_mas += v["vacas_percibidas"]

    print("\n=== RESUMEN GLOBAL DIAGNÓSTICO ===")
    print(f"Total ventanas de 50 latidos con recinto: {ventanas_con_recinto}")
    if ventanas_con_recinto > 0:
        media_reales = suma_vacas_reales / ventanas_con_recinto
        media_percibidas = suma_vacas_percibidas / ventanas_con_recinto
        media_reales_150 = media_reales * 3.0  # en 150 latidos (3 ventanas de 50)
        media_no_vis = suma_no_visitadas_pct / ventanas_con_recinto
        print(f"Vacas reales a <= 17 del recinto (media por 50 latidos):  {media_reales:.2f}")
        print(f"Vacas reales a <= 17 del recinto (media por 150 latidos): {media_reales_150:.2f}")
        print(f"Vacas percibidas (media por 50 latidos):                  {media_percibidas:.2f}")
        print(f"Casillas a <= 17 no visitadas hace > 150 latidos:         {media_no_vis:.1f} %")

    if ventanas_dia1_mas > 0:
        media_d1_reales = vacas_reales_dia1_mas / ventanas_dia1_mas
        media_d1_reales_150 = media_d1_reales * 3.0
        media_d1_perc = vacas_percibidas_dia1_mas / ventanas_dia1_mas
        print(f"\nTras la primera noche (L >= 300, {ventanas_dia1_mas} ventanas):")
        print(f"Vacas reales a <= 17 del recinto (media por 50 latidos):  {media_d1_reales:.2f}")
        print(f"Vacas reales a <= 17 del recinto (media por 150 latidos): {media_d1_reales_150:.2f}")
        print(f"Vacas percibidas (media por 50 latidos):                  {media_d1_perc:.2f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
