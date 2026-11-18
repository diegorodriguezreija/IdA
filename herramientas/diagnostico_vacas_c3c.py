"""Diagnóstico C.3c: Análisis de episodios de vacas percibidas (L >= 300).

Para cada episodio de vaca que entra en el campo visual del individuo:
- Variables al detectarla: comida, agua, salud, distancia, luz, nutritivo.
- Propuestas generadas hacia la vaca (Alimentarse, RefugioNocturno, etc.) con arousal/confianza.
- Ganador del Tribunal en cada latido.
- Desenlace: 'comida', 'perdida_de_vista' o 'ignorada'.
- Métricas agregadas y conclusión sobre el cuello de botella (motivación, persecución o combate).
"""

import argparse
from collections import Counter
import json
import os
import sys
import tempfile
from typing import Any, Dict, List, Tuple

import crafter.objects

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from herramientas.benchmark import PERFILES  # noqa: E402
from ida.ejecutor import ejecutar as vivir  # noqa: E402


def diagnosticar_semilla_c3c(semilla: int, max_latidos: int = 3000) -> Dict[str, Any]:
    # Diccionario de episodios completados
    episodios_cerrados: List[Dict[str, Any]] = []
    # Episodios actualmente en curso: id(Cow) -> datos del episodio
    episodios_activos: Dict[int, Dict[str, Any]] = {}
    prev_eat_cow: int = 0
    ep_counter: int = 0

    def al_latir(org: Any, onda: Any, _r: Dict[str, Any]) -> None:
        nonlocal prev_eat_cow, ep_counter
        p = org.mundo.jugador
        ciclo = onda.ciclo
        inv = p.inventory
        luz = float(org.mundo.env._world.daylight)

        curr_eat_cow = int(p.achievements.get("eat_cow", 0))
        comio_vaca_este_latido = (curr_eat_cow > prev_eat_cow)
        prev_eat_cow = curr_eat_cow

        # Solo analizamos a partir del latido 300 (después de la primera noche)
        if ciclo < 300:
            return

        # Vacas actualmente en el mundo
        w = org.mundo.env._world
        cows_en_mundo = {id(obj): obj for obj in w.objects if isinstance(obj, crafter.objects.Cow)}

        # Vacas percibidas en Exterocepcion
        ext = onda.ev("Exterocepcion") or {}
        vacas_percibidas: Dict[int, Tuple[Any, Tuple[int, int]]] = {}  # id(Cow) -> (Pieza, pos)
        for pz in ext.values():
            if pz.clase == "vaca" and "pos" in pz.carga.get("datos", {}):
                raw_pos = pz.carga["datos"]["pos"]
                pos_v: Tuple[int, int] = (int(raw_pos[0]), int(raw_pos[1]))
                # Asociar con la vaca real por posición
                for c_id, c_obj in cows_en_mundo.items():
                    c_pos = (int(c_obj.pos[0]), int(c_obj.pos[1]))
                    if c_pos == pos_v:
                        vacas_percibidas[c_id] = (pz, pos_v)
                        break

        # Candidatos evaluados en el Tribunal
        evaluados = onda.notas.get("evaluados", [])
        ganador_id = evaluados[0].get("id", "") if evaluados else ""
        ganador_motivo = evaluados[0].get("motivo", "") if evaluados else ""
        ganador_sistema = evaluados[0].get("sistema", "") if evaluados else ""

        # Determinar estrategia ganadora
        ganador_est = ""
        for sis in ("S1", "S2", "S3"):
            ejec = (onda.notas.get(f"estrategias_{sis}") or {}).get("ejecutada")
            if ejec:
                ganador_est = f"{sis}:{ejec}"
                break
        if not ganador_est:
            ganador_est = ganador_sistema or "desconocida"

        # Determinar si el jugador está de día y fuera del refugio
        paso_s2 = (onda.notas.get("estrategias_S2") or {}).get("refugio_nocturno")
        mina_s2 = paso_s2.get("mina") if isinstance(paso_s2, dict) else None
        fase_s2 = paso_s2.get("fase") if isinstance(paso_s2, dict) else ""
        galeria = []
        if mina_s2 is not None:
            e0, (dx, dy) = mina_s2
            galeria = [(e0[0] + k * dx, e0[1] + k * dy) for k in (1, 2, 3)]
        pos_jugador = (int(p.pos[0]), int(p.pos[1]))
        esta_dentro = (pos_jugador in galeria) or (fase_s2 == "dormir")
        es_dia = (luz >= 0.5)
        es_dia_y_fuera = es_dia and (not esta_dentro)

        # 1. Actualizar episodios activos y detectar nuevos
        cows_vistas_ahora = set(vacas_percibidas.keys())

        # Revisar vacas vistas ahora
        for c_id, (pz, pos_v) in vacas_percibidas.items():
            dist_jugador = abs(int(p.pos[0]) - pos_v[0]) + abs(int(p.pos[1]) - pos_v[1])
            nutritivo = float(pz.rasgo("nutritivo"))

            # Si es una nueva vaca que entra en la vista
            if c_id not in episodios_activos:
                ep_counter += 1
                c_obj = cows_en_mundo.get(c_id)
                hp_ini = getattr(c_obj, "health", 3) if c_obj else 3
                episodios_activos[c_id] = {
                    "id": ep_counter,
                    "semilla": semilla,
                    "vaca_id": c_id,
                    "latido_inicio": ciclo,
                    "latido_fin": ciclo,
                    "comida_inicio": int(inv.get("food", 0)),
                    "agua_inicio": int(inv.get("drink", 0)),
                    "salud_inicio": int(p.health),
                    "distancia_inicio": dist_jugador,
                    "luz_inicio": round(luz, 3),
                    "nutritivo_inicio": round(nutritivo, 3),
                    "es_dia_y_fuera_inicio": es_dia_y_fuera,
                    "comidas_hist": [int(inv.get("food", 0))],
                    "distancias_hist": [dist_jugador],
                    "hp_vaca_inicio": hp_ini,
                    "hp_vaca_min": hp_ini,
                    "propuestas_vaca": [],
                    "ganador_tribunal": [],
                    "hubo_propuesta_vaca": False,
                    "ganador_fue_vaca": False,
                    "golpes_dados": 0,
                    "desenlace": None,
                }

            ep = episodios_activos[c_id]
            ep["latido_fin"] = ciclo
            ep["comidas_hist"].append(int(inv.get("food", 0)))
            ep["distancias_hist"].append(dist_jugador)

            c_obj = cows_en_mundo.get(c_id)
            if c_obj:
                hp_act = getattr(c_obj, "health", 3)
                if hp_act < ep["hp_vaca_min"]:
                    ep["golpes_dados"] += (ep["hp_vaca_min"] - hp_act)
                    ep["hp_vaca_min"] = hp_act

            # Comprobar propuestas hacia la vaca en este latido
            propuestas_este_latido = []
            for ev in evaluados:
                obj_id = str(ev.get("objetivo", ""))
                motivo = str(ev.get("motivo", ""))
                es_hacia_vaca = (
                    obj_id == pz.id
                    or "vaca" in motivo
                    or "vaca" in obj_id
                    or (pos_v[0] != -1 and f"{pos_v[0]}_{pos_v[1]}" in obj_id)
                )
                if es_hacia_vaca:
                    propuestas_este_latido.append({
                        "id": ev.get("id"),
                        "sistema": ev.get("sistema"),
                        "verbo": ev.get("verbo"),
                        "base": ev.get("base"),
                        "total": ev.get("total"),
                        "motivo": motivo,
                    })

            if propuestas_este_latido:
                ep["hubo_propuesta_vaca"] = True
                ep["propuestas_vaca"].append({
                    "ciclo": ciclo,
                    "propuestas": propuestas_este_latido,
                })

            # Comprobar si el ganador del Tribunal iba hacia la vaca
            ganador_fue_hacia_vaca = (
                pz.id in ganador_id
                or "vaca" in ganador_motivo
                or (pos_v[0] != -1 and f"{pos_v[0]}_{pos_v[1]}" in ganador_id)
            )
            if ganador_fue_hacia_vaca:
                ep["ganador_fue_vaca"] = True

            ep["ganador_tribunal"].append({
                "ciclo": ciclo,
                "estrategia": ganador_est,
                "motivo": ganador_motivo,
                "fue_a_vaca": ganador_fue_hacia_vaca,
            })

        # 2. Cerrar episodios de vacas que ya no están en la vista o que fueron comidas
        for c_id in list(episodios_activos.keys()):
            ep = episodios_activos[c_id]
            # Si comió vaca este latido y la vaca ya no existe en el mundo o estaba al lado
            if comio_vaca_este_latido and (c_id not in cows_en_mundo or c_id not in cows_vistas_ahora):
                ep["desenlace"] = "comida"
                episodios_cerrados.append(ep)
                del episodios_activos[c_id]
            elif c_id not in cows_vistas_ahora:
                # Salió de la vista sin ser comida
                if ep["ganador_fue_vaca"] or ep["golpes_dados"] > 0:
                    ep["desenlace"] = "perdida_de_vista"
                else:
                    ep["desenlace"] = "ignorada"
                episodios_cerrados.append(ep)
                del episodios_activos[c_id]

    with tempfile.TemporaryDirectory(prefix=f"diag_vaca_c3c_{semilla}_") as td:
        res = vivir("crafter", latidos=max_latidos, semilla=semilla, generaciones=1, tabula_rasa=True,
                    consola=False, datos=td, al_latir=al_latir, arquetipo_inicial=PERFILES["Equilibrado"])[0]

    # Cerrar cualquier episodio pendiente al final de la vida
    for _c_id, ep in episodios_activos.items():
        if ep["desenlace"] is None:
            if ep["ganador_fue_vaca"] or ep["golpes_dados"] > 0:
                ep["desenlace"] = "perdida_de_vista"
            else:
                ep["desenlace"] = "ignorada"
        episodios_cerrados.append(ep)

    return {
        "semilla": semilla,
        "latidos": int(res.get("latidos", 0)),
        "vivo": bool(res.get("vivo")),
        "causa_muerte": res.get("causa_muerte"),
        "vacas_comidas_total": int(res.get("puntuacion", {}).get("logros", []).count("eat_cow")),
        "episodios": episodios_cerrados,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--semillas", type=int, nargs="*", default=list(range(11, 21)))
    p.add_argument("--latidos", type=int, default=3000)
    p.add_argument("--salida", type=str, default=None, help="fichero JSON donde guardar los episodios")
    args = p.parse_args()

    print("=== DIAGNÓSTICO C.3c: EPISODIOS DE VACAS PERCIBIDAS (L >= 300) ===", flush=True)
    todos_episodios: List[Dict[str, Any]] = []

    for sem in args.semillas:
        res = diagnosticar_semilla_c3c(sem, max_latidos=args.latidos)
        eps = res["episodios"]
        todos_episodios.extend(eps)
        comidos = sum(1 for e in eps if e["desenlace"] == "comida")
        perdidos = sum(1 for e in eps if e["desenlace"] == "perdida_de_vista")
        ignorados = sum(1 for e in eps if e["desenlace"] == "ignorada")
        pct_c = (100.0 * comidos / max(1, len(eps))) if eps else 0.0

        print(
            f"Semilla {sem:2d}: L={res['latidos']:4d} causa={res['causa_muerte']} | "
            f"Episodios={len(eps):2d} (comidos={comidos}, perdidos={perdidos}, ignorados={ignorados}) | "
            f"% comidos={pct_c:.1f} %",
            flush=True,
        )

    n_tot = len(todos_episodios)
    print("\n=======================================================")
    print(f"RESUMEN AGREGADO DE EPISODIOS (N = {n_tot} episodios, semillas {args.semillas[0]}-{args.semillas[-1]})")
    print("=======================================================")

    if n_tot == 0:
        print("No se registraron episodios de vacas a partir del latido 300.")
        return 0

    comidos_eps = [e for e in todos_episodios if e["desenlace"] == "comida"]
    perdidos_eps = [e for e in todos_episodios if e["desenlace"] == "perdida_de_vista"]
    ignorados_eps = [e for e in todos_episodios if e["desenlace"] == "ignorada"]

    pct_comidos = 100.0 * len(comidos_eps) / n_tot
    pct_perdidos = 100.0 * len(perdidos_eps) / n_tot
    pct_ignorados = 100.0 * len(ignorados_eps) / n_tot

    print("Desglose por desenlace:")
    print(f"  • Comidos:           {len(comidos_eps):2d} ({pct_comidos:.1f} %)")
    print(f"  • Perdidos de vista: {len(perdidos_eps):2d} ({pct_perdidos:.1f} %)")
    print(f"  • Ignorados:         {len(ignorados_eps):2d} ({pct_ignorados:.1f} %)")

    c_media_ignorados = (
        sum(e["comida_inicio"] for e in ignorados_eps) / len(ignorados_eps)
        if ignorados_eps else 0.0
    )
    c_media_comidos = (
        sum(e["comida_inicio"] for e in comidos_eps) / len(comidos_eps)
        if comidos_eps else 0.0
    )
    c_media_perdidos = (
        sum(e["comida_inicio"] for e in perdidos_eps) / len(perdidos_eps)
        if perdidos_eps else 0.0
    )

    print("\nComida media al ver la vaca:")
    print(f"  • En episodios ignorados:         {c_media_ignorados:.2f} (rango: {[e['comida_inicio'] for e in ignorados_eps]})")
    print(f"  • En episodios comidos:           {c_media_comidos:.2f} (rango: {[e['comida_inicio'] for e in comidos_eps]})")
    print(f"  • En episodios perdidos de vista: {c_media_perdidos:.2f}")

    # Umbral de comida por debajo del cual sí va a por la vaca
    eps_con_intento = [e for e in todos_episodios if e["hubo_propuesta_vaca"] or e["ganador_fue_vaca"] or e["desenlace"] == "comida"]
    comidas_con_intento = [e["comida_inicio"] for e in eps_con_intento]
    max_comida_intento = max(comidas_con_intento) if comidas_con_intento else 0
    min_comida_intento = min(comidas_con_intento) if comidas_con_intento else 0
    print(f"\nUmbral de comida cuando sí va a por la vaca (N = {len(eps_con_intento)} intentos):")
    print(f"  • Comida al inicio en intentos: mín={min_comida_intento}, máx={max_comida_intento}, valores={sorted(comidas_con_intento)}")

    # Estrategias que ganan el Tribunal cuando se ignora la vaca
    ganadores_ignorados: Counter = Counter()
    for e in ignorados_eps:
        for g in e["ganador_tribunal"]:
            ganadores_ignorados[g["estrategia"]] += 1

    print(f"\nEstrategias que ganan el Tribunal cuando se ignora la vaca (latidos totales = {sum(ganadores_ignorados.values())}):")
    for est, count in ganadores_ignorados.most_common(10):
        print(f"  • {est:30s}: {count:4d} latidos ({100.0 * count / max(1, sum(ganadores_ignorados.values())):.1f} %)")

    # Detalles sobre persecución y combate
    print("\nAnálisis de persecución y combate:")
    dist_media_ini = sum(e["distancia_inicio"] for e in todos_episodios) / n_tot
    nutr_media_ini = sum(e["nutritivo_inicio"] for e in todos_episodios) / n_tot
    print(f"  • Distancia media inicial: {dist_media_ini:.2f} casillas")
    print(f"  • Valor nutritivo medio:   {nutr_media_ini:.2f}")
    if perdidos_eps:
        golpes_perdidos = [e["golpes_dados"] for e in perdidos_eps]
        print(f"  • Golpes dados en vacas perdidas de vista: {golpes_perdidos} (total={sum(golpes_perdidos)})")
    if comidos_eps:
        golpes_comidos = [e["golpes_dados"] for e in comidos_eps]
        print(f"  • Golpes dados en vacas comidas: {golpes_comidos}")

    # Desglose separando episodios de día y fuera del refugio del resto (B.2)
    subgrupos = [
        ("DE DÍA Y FUERA DEL REFUGIO", [e for e in todos_episodios if e.get("es_dia_y_fuera_inicio", False)]),
        ("RESTO (NOCHE O DENTRO DEL REFUGIO)", [e for e in todos_episodios if not e.get("es_dia_y_fuera_inicio", False)]),
    ]
    print("\n=======================================================")
    print("DESGLOSE POR ENTORNO (DE DÍA Y FUERA DEL REFUGIO vs RESTO)")
    print("=======================================================")
    for nombre_sub, eps_sub in subgrupos:
        n_sub = len(eps_sub)
        print(f"\n--- {nombre_sub} (N = {n_sub}) ---")
        if n_sub == 0:
            print("  (Sin episodios)")
            continue
        c_sub = [e for e in eps_sub if e["desenlace"] == "comida"]
        p_sub = [e for e in eps_sub if e["desenlace"] == "perdida_de_vista"]
        i_sub = [e for e in eps_sub if e["desenlace"] == "ignorada"]
        print(f"  • Comidos:           {len(c_sub):2d} ({100.0 * len(c_sub) / n_sub:.1f} %)")
        print(f"  • Perdidos de vista: {len(p_sub):2d} ({100.0 * len(p_sub) / n_sub:.1f} %)")
        print(f"  • Ignorados:         {len(i_sub):2d} ({100.0 * len(i_sub) / n_sub:.1f} %)")
        cm_c = sum(e["comida_inicio"] for e in c_sub) / len(c_sub) if c_sub else 0.0
        cm_p = sum(e["comida_inicio"] for e in p_sub) / len(p_sub) if p_sub else 0.0
        cm_i = sum(e["comida_inicio"] for e in i_sub) / len(i_sub) if i_sub else 0.0
        print("  Comida media:")
        print(f"    - Comidos:           {cm_c:.2f}")
        print(f"    - Perdidos de vista: {cm_p:.2f}")
        print(f"    - Ignorados:         {cm_i:.2f}")

    if getattr(args, "salida", None):
        os.makedirs(os.path.dirname(os.path.abspath(args.salida)), exist_ok=True)
        with open(args.salida, "w", encoding="utf-8") as f:
            json.dump(todos_episodios, f, indent=2)
        print(f"\nResultados guardados en: {args.salida}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
