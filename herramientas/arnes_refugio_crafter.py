"""Arnés de prueba de la Fase A (competencia de RefugioNocturno en Crafter).

Prueba la estrategia RefugioNocturno con motivación dominante sin alterar el Perfil fusionado en
ida/mundos/crafter.py (sección 6, Fase A de docs/ENCARGO_CRAFTER_NOCHE.md).

Semillas 11 a 30, 1 vida por semilla, 600 latidos.
Mide:
- porcentaje de vidas selladas (y cuántas antes de que la luz baje de 0,5);
- latido y nivel de luz en el momento del primer sellado;
- porcentaje de las selladas que pasan la noche sin daño dentro y cuántas logran wake_up;
- causa de cada fallo (sin árboles, sin roca adecuada, interrumpida por un zombi, lava, orientación o tiempo).
"""

import argparse
from collections import Counter
from dataclasses import replace
import json
import os
import sys
import tempfile
from typing import Any, Dict, List, Optional

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from herramientas.benchmark import PERFILES  # noqa: E402
from ida.core.mundo import Necesidad  # noqa: E402
from ida.ejecutor import ejecutar as vivir  # noqa: E402
from ida.mundos import cargar  # noqa: E402
from ida.mundos.crafter import RefugioNocturno  # noqa: E402


def _nicho_candidato_hierba(mundo_env: Any, mina: Any) -> bool:
    """Comprueba si en alguno de los 4 laterales de e2 o e3 el material original/actual del mundo es 'grass'."""
    try:
        e0, (dx, dy) = mina
        e2 = (e0[0] + 2 * dx, e0[1] + 2 * dy)
        e3 = (e0[0] + 3 * dx, e0[1] + 3 * dy)
        laterales = [
            (e3[0] - dy, e3[1] + dx),
            (e3[0] + dy, e3[1] - dx),
            (e2[0] - dy, e2[1] + dx),
            (e2[0] + dy, e2[1] - dx),
        ]
        w = mundo_env._world
        for c in laterales:
            if 0 <= c[0] < w.area[0] and 0 <= c[1] < w.area[1]:
                if w[c][0] == "grass":
                    return True
    except Exception:
        pass
    return False


def _serializar_json(obj: Any) -> Any:
    if isinstance(obj, (tuple, list)):
        return [_serializar_json(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _serializar_json(v) for k, v in obj.items()}
    if isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    return str(obj)


def evaluar_fase_a(semillas: List[int], latidos: int = 600, perfil: str = "Equilibrado", detalle: bool = True,
                   real: bool = False, salida: Optional[str] = None) -> Dict[str, Any]:
    """Con ``real`` la estrategia compite con su motivación real (Perfil fusionado, sin ``dominante``):
    es el modo de ajuste de la Fase B. Sin él, es la prueba de competencia de la Fase A."""
    clase_mundo = cargar("crafter")
    perfil_original = clase_mundo.perfil
    init_original = RefugioNocturno.__init__

    def _init_dominante(self: RefugioNocturno) -> None:
        init_original(self)
        self.dominante = True

    if not real:
        # Activar el impulso cobijo en el arnés y marcar la estrategia como dominante solo durante la prueba
        necesidades_arnes = tuple(n for n in perfil_original.necesidades if n.nombre != "cobijo") + (Necesidad("cobijo", ("cobijo",), 100.0),)
        clase_mundo.perfil = replace(perfil_original, necesidades=necesidades_arnes)
        RefugioNocturno.__init__ = _init_dominante  # type: ignore[method-assign]

    resultados: List[Dict[str, Any]] = []
    try:
        for sem in semillas:
            info_vida: Dict[str, Any] = {
                "semilla": sem,
                "sellada": False,
                "sellada_antes_05": False,
                "latido_sello": None,
                "paso_sello": None,
                "luz_sello": None,
                "dano_dentro": False,
                "wake_up": False,
                "salud_al_sellar": None,
                "max_madera": 0,
                "tuvo_pico": False,
                "tuvo_espada": False,
                "tuvo_mina": False,
                "fases_vistas": [],
                "ultima_fase": "ninguna",
                "causa_muerte": None,
                "vivo_final": True,
                "latidos_vividos": 0,
                "logros": [],
                "inv_sello": None,
                "salida": None,
                "bebe_tras_salida": None,
                "come_tras_salida": None,
                "dano_tras_salida": 0,
                "inv_final": None,
                "ejecutadas": {},
                "noches_superadas": 0,
                "dias": [],
                "refugios_usados": [],
                "refugios_con_hierba_lateral": 0,
                "repite_refugio_count": 0,
                "cambio_refugio_count": 0,
            }

            estado_largo: Dict[str, Any] = {
                "dia_actual": -1,
                "prev_cow": 0,
                "prev_plant": 0,
                "en_noche": False,
                "ultimo_refugio": None,
                "refugio_noche_actual": None,
                "noche_registrada": -1,
            }

            def al_latir(org: Any, onda: Any, _r: Dict[str, Any], iv: Dict[str, Any] = info_vida,
                         el: Dict[str, Any] = estado_largo) -> None:
                p = org.mundo.jugador
                inv = p.inventory
                luz = float(org.mundo.env._world.daylight)
                paso_m = int(org.mundo.t)
                dia = paso_m // 300

                # Seguimiento diario (C.3)
                if dia != el["dia_actual"]:
                    el["dia_actual"] = dia
                    iv["dias"].append({
                        "dia": dia,
                        "min_comida": int(inv.get("food", 0)),
                        "min_agua": int(inv.get("drink", 0)),
                        "vacas_comidas": 0,
                        "plantas_comidas": 0,
                        "max_dist_refugio_previo": None,
                    })

                d_info = iv["dias"][-1]
                c_val = int(inv.get("food", 0))
                a_val = int(inv.get("drink", 0))
                if c_val < d_info["min_comida"]:
                    d_info["min_comida"] = c_val
                if a_val < d_info["min_agua"]:
                    d_info["min_agua"] = a_val

                ach = getattr(p, "achievements", {})
                cows_tot = int(ach.get("eat_cow", 0))
                plants_tot = int(ach.get("eat_plant", 0))
                if cows_tot > el["prev_cow"]:
                    d_info["vacas_comidas"] += (cows_tot - el["prev_cow"])
                    el["prev_cow"] = cows_tot
                if plants_tot > el["prev_plant"]:
                    d_info["plantas_comidas"] += (plants_tot - el["prev_plant"])
                    el["prev_plant"] = plants_tot

                if el["ultimo_refugio"] is not None:
                    u_e0, (u_dx, u_dy) = el["ultimo_refugio"]
                    u_e2 = (u_e0[0] + 2 * u_dx, u_e0[1] + 2 * u_dy)
                    dist_r = abs(int(p.pos[0]) - u_e2[0]) + abs(int(p.pos[1]) - u_e2[1])
                    if d_info["max_dist_refugio_previo"] is None or dist_r > d_info["max_dist_refugio_previo"]:
                        d_info["max_dist_refugio_previo"] = dist_r

                # Noches superadas y transición de noche
                if luz < 0.3:
                    if not el["en_noche"]:
                        el["en_noche"] = True
                elif el["en_noche"] and luz >= 0.5:
                    el["en_noche"] = False
                    iv["noches_superadas"] += 1
                    if el["refugio_noche_actual"] is not None:
                        el["ultimo_refugio"] = el["refugio_noche_actual"]

                iv["max_madera"] = max(iv["max_madera"], int(inv.get("wood", 0)))
                if inv.get("wood_pickaxe", 0) >= 1:
                    iv["tuvo_pico"] = True
                if inv.get("wood_sword", 0) >= 1:
                    iv["tuvo_espada"] = True
                previo = iv.get("_inv_previo")
                salida = iv["salida"]
                if salida is not None and previo is not None:
                    if iv["bebe_tras_salida"] is None and inv.get("drink", 0) > previo["drink"]:
                        iv["bebe_tras_salida"] = onda.ciclo - salida["latido"]
                    if iv["come_tras_salida"] is None and inv.get("food", 0) > previo["food"]:
                        iv["come_tras_salida"] = onda.ciclo - salida["latido"]
                    if int(p.health) < previo["health"]:
                        iv["dano_tras_salida"] += previo["health"] - int(p.health)
                iv["_inv_previo"] = {"drink": int(inv.get("drink", 0)), "food": int(inv.get("food", 0)), "health": int(p.health)}
                iv["inv_final"] = (int(inv.get("food", 0)), int(inv.get("drink", 0)), int(inv.get("energy", 0)), int(p.health),
                                   int(inv.get("stone", 0)))
                for sis in ("S1", "S2", "S3"):
                    ejecutada = (onda.notas.get(f"estrategias_{sis}") or {}).get("ejecutada")
                    if ejecutada:
                        iv["ejecutadas"][ejecutada] = iv["ejecutadas"].get(ejecutada, 0) + 1

                est = onda.estrategias.get("S2:refugio_nocturno:cobijo")
                paso = est.carga.get("paso") if est is not None else None
                if isinstance(paso, dict):
                    fase = paso.get("fase", "?")
                    iv["ultima_fase"] = fase
                    if not iv["fases_vistas"] or iv["fases_vistas"][-1] != fase:
                        iv["fases_vistas"].append(fase)
                    if paso.get("mina") is not None:
                        iv["tuvo_mina"] = True
                    if fase == "dormir":
                        if paso.get("mina") is not None and el.get("noche_registrada") != dia:
                            mina_act = paso["mina"]
                            el["noche_registrada"] = dia
                            el["refugio_noche_actual"] = mina_act
                            hierba = _nicho_candidato_hierba(org.mundo.env, mina_act)
                            repite = False
                            dist_prev = None
                            if iv["refugios_usados"]:
                                prev_ref = iv["refugios_usados"][-1]["refugio"]
                                repite = (mina_act == prev_ref)
                                dist_prev = 0 if repite else (abs(mina_act[0][0] - prev_ref[0][0]) + abs(mina_act[0][1] - prev_ref[0][1]))
                                if repite:
                                    iv["repite_refugio_count"] += 1
                                else:
                                    iv["cambio_refugio_count"] += 1
                            iv["refugios_usados"].append({
                                "noche": iv["noches_superadas"],
                                "dia": dia,
                                "latido": onda.ciclo,
                                "refugio": mina_act,
                                "repite": repite,
                                "dist_previo": dist_prev,
                                "hierba_lateral": hierba,
                            })
                            if hierba:
                                iv["refugios_con_hierba_lateral"] += 1
                        if not iv["sellada"]:
                            iv["sellada"] = True
                            iv["latido_sello"] = onda.ciclo
                            iv["paso_sello"] = org.mundo.t
                            iv["luz_sello"] = round(luz, 3)
                            iv["sellada_antes_05"] = luz >= 0.5
                            iv["salud_al_sellar"] = int(p.health)
                            iv["inv_sello"] = (int(inv.get("food", 0)), int(inv.get("drink", 0)), int(p.health))
                            iv["primera_noche_terminada"] = False
                        elif not iv.get("primera_noche_terminada", False):
                            # Daño causado por un monstruo mientras el jugador está dentro del refugio sellado en este latido
                            ef_ant = org.ultimo_efecto
                            if iv.get("fase_previa") == "dormir" and luz < 0.5 and ef_ant is not None:
                                if ef_ant.causa in ("zombi", "esqueleto", "flecha"):
                                    iv["dano_dentro"] = True
                    else:
                        if iv["sellada"] and fase == "amanecer":
                            iv["primera_noche_terminada"] = True
                            if iv["salida"] is None:
                                iv["salida"] = {"latido": onda.ciclo, "luz": round(luz, 2), "comida": int(inv.get("food", 0)),
                                                "agua": int(inv.get("drink", 0)), "salud": int(p.health)}
                    iv["fase_previa"] = fase

            with tempfile.TemporaryDirectory(prefix=f"ida_fase_a_{sem}_") as td:
                res = vivir("crafter", latidos=latidos, semilla=sem, generaciones=1, tabula_rasa=True,
                            consola=False, datos=td, al_latir=al_latir, arquetipo_inicial=PERFILES[perfil])[0]

            logros = res.get("puntuacion", {}).get("logros", [])
            info_vida["logros"] = logros
            info_vida["wake_up"] = "wake_up" in logros
            info_vida["vivo_final"] = bool(res.get("vivo"))
            info_vida["causa_muerte"] = res.get("causa_muerte")
            info_vida["latidos_vividos"] = int(res.get("latidos", 0))

            # Clasificación de causa de fallo si no selló o si no selló antes de luz 0.5
            causa_fallo = "ok"
            if not info_vida["sellada"]:
                if info_vida["causa_muerte"] == "lava":
                    causa_fallo = "lava"
                elif not info_vida["tuvo_pico"]:
                    causa_fallo = "sin_arboles" if info_vida["max_madera"] < 3 else "orientacion_mesa"
                elif not info_vida["tuvo_mina"]:
                    causa_fallo = "sin_roca_adecuada"
                elif info_vida["causa_muerte"] in ("zombi", "esqueleto", "flecha"):
                    causa_fallo = f"interrumpida_{info_vida['causa_muerte']}"
                else:
                    causa_fallo = f"tiempo_en_{info_vida['ultima_fase']}"
            elif not info_vida["sellada_antes_05"]:
                causa_fallo = f"sello_tardio(luz={info_vida['luz_sello']})"
            info_vida["causa_fallo"] = causa_fallo
            resultados.append(info_vida)
            if detalle and real:
                if latidos > 600:
                    dias_res = [
                        f"d{d['dia']}:c{d['min_comida']}/a{d['min_agua']}/v{d['vacas_comidas']}/p{d['plantas_comidas']}"
                        for d in info_vida["dias"]
                    ]
                    refs_res = [
                        f"n{n['noche']}:({n['refugio'][0]},{n['refugio'][1]})"
                        f"{'[rep]' if n['repite'] else ''}{'[hierba]' if n['hierba_lateral'] else ''}"
                        for n in info_vida["refugios_usados"]
                    ]
                    rep_txt = (
                        f"noches={info_vida['noches_superadas']} refugios={len(info_vida['refugios_usados'])} "
                        f"(hierba={info_vida['refugios_con_hierba_lateral']}, repite={info_vida['repite_refugio_count']})"
                    )
                    print(
                        f"Semilla {sem:2d}: L={info_vida['latidos_vividos']} vivo={info_vida['vivo_final']} "
                        f"causa={info_vida['causa_muerte']} {rep_txt}",
                        flush=True,
                    )
                    print(f"   Días: {' '.join(dias_res)}", flush=True)
                    if refs_res:
                        print(f"   Refugios: {' '.join(refs_res)}", flush=True)
                else:
                    print(
                        f"Semilla {sem:2d}: L_sello={info_vida['latido_sello']} luz={info_vida['luz_sello']} "
                        f"sello(c,a,s)={info_vida['inv_sello']} salida={info_vida['salida']} "
                        f"bebe+{info_vida['bebe_tras_salida']} come+{info_vida['come_tras_salida']} "
                        f"dano_fuera={info_vida['dano_tras_salida']} final(c,a,e,s,piedra)={info_vida['inv_final']} "
                        f"vivo={info_vida['vivo_final']} causa={info_vida['causa_muerte']} L={info_vida['latidos_vividos']} "
                        f"wake={info_vida['wake_up']} logros={len(logros)}",
                        flush=True,
                    )
            elif detalle:
                print(
                    f"Semilla {sem:2d}: sellada={info_vida['sellada']} (antes_05={info_vida['sellada_antes_05']}) "
                    f"L_sello={info_vida['latido_sello']} luz={info_vida['luz_sello']} "
                    f"daño_dentro={info_vida['dano_dentro']} wake_up={info_vida['wake_up']} "
                    f"latidos={info_vida['latidos_vividos']} estado={causa_fallo} fases={info_vida['fases_vistas']}",
                    flush=True,
                )
    finally:
        clase_mundo.perfil = perfil_original
        RefugioNocturno.__init__ = init_original  # type: ignore[method-assign]

    n = len(resultados)
    selladas = [r for r in resultados if r["sellada"]]
    selladas_05 = [r for r in resultados if r["sellada_antes_05"]]
    sin_dano = [r for r in selladas if not r["dano_dentro"]]
    con_wake = [r for r in resultados if r["wake_up"]]

    salidas = [r for r in resultados if r["salida"] is not None]
    resumen = {
        "n": n,
        "vivas": sum(1 for r in resultados if r["vivo_final"]),
        "causas": dict(Counter(r["causa_muerte"] for r in resultados if not r["vivo_final"])),
        "salidas": len(salidas),
        "logros_medios": sum(len(r["logros"]) for r in resultados) / max(1, n),
        "latidos_medios": sum(r["latidos_vividos"] for r in resultados) / max(1, n),
        "selladas": len(selladas),
        "pct_selladas": 100.0 * len(selladas) / max(1, n),
        "selladas_antes_05": len(selladas_05),
        "pct_selladas_antes_05": 100.0 * len(selladas_05) / max(1, n),
        "sin_dano_de_selladas": len(sin_dano),
        "pct_sin_dano_de_selladas": 100.0 * len(sin_dano) / max(1, len(selladas)),
        "wake_up": len(con_wake),
        "pct_wake_up": 100.0 * len(con_wake) / max(1, n),
        # Métricas multidia / horizonte largo (C.3):
        "noches_superadas_totales": sum(r["noches_superadas"] for r in resultados),
        "noches_superadas_media": sum(r["noches_superadas"] for r in resultados) / max(1, n),
        "refugios_usados_totales": sum(len(r["refugios_usados"]) for r in resultados),
        "refugios_con_hierba_totales": sum(r["refugios_con_hierba_lateral"] for r in resultados),
        "repite_refugio_totales": sum(r["repite_refugio_count"] for r in resultados),
        "cambio_refugio_totales": sum(r["cambio_refugio_count"] for r in resultados),
        "resultados": resultados,
    }
    if salida:
        os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)
        with open(salida, "w", encoding="utf-8") as f:
            json.dump(_serializar_json(resumen), f, indent=2)

    if detalle:
        print("\n=== RESUMEN FASE A ===")
        print(f"Vidas selladas totales:        {resumen['selladas']}/{n} ({resumen['pct_selladas']:.1f} %)")
        print(f"Vidas selladas con luz >= 0.5: {resumen['selladas_antes_05']}/{n} ({resumen['pct_selladas_antes_05']:.1f} %)")
        print(f"Selladas sin daño nocturno:    {resumen['sin_dano_de_selladas']}/{len(selladas)} ({resumen['pct_sin_dano_de_selladas']:.1f} %)")
        print(f"Vidas con wake_up:             {resumen['wake_up']}/{n} ({resumen['pct_wake_up']:.1f} %)")
        if real:
            beben = [r for r in salidas if r["bebe_tras_salida"] is not None]
            luz_media = sum(r["salida"]["luz"] for r in salidas) / max(1, len(salidas))
            espera = sum(r["bebe_tras_salida"] for r in beben) / max(1, len(beben))
            ejecutadas: Counter = Counter()
            for r in resultados:
                ejecutadas.update(r["ejecutadas"])
            print(f"Vivas al final:                {resumen['vivas']}/{n}  causas={resumen['causas']}")
            print(f"Salen del refugio:             {len(salidas)}  luz media {luz_media:.2f}  beben tras salir {len(beben)} "
                  f"(latidos medios {espera:.1f})  daño fuera {sum(r['dano_tras_salida'] for r in salidas)}")
            print(f"Logros medios {resumen['logros_medios']:.2f}  latidos medios {resumen['latidos_medios']:.1f}")
            print(f"Latidos ejecutados por estrategia: {dict(ejecutadas.most_common(8))}")
        if latidos > 600:
            print("\n=== RESUMEN HORIZONTE LARGO (C.3) ===")
            print(f"Vivas:                         {resumen['vivas']}/{n}")
            print(f"Causas de muerte:              {resumen['causas']}")
            print(f"Noches superadas medias:       {resumen['noches_superadas_media']:.1f}")
            print(f"Refugios con hierba lateral:   {resumen['refugios_con_hierba_totales']}/{resumen['refugios_usados_totales']} noches")
            print(f"Refugio repetido vs cambiado:  {resumen['repite_refugio_totales']} repetidos / {resumen['cambio_refugio_totales']} cambiados")
            dias_dist = [d["max_dist_refugio_previo"] for r in resultados for d in r["dias"] if d["max_dist_refugio_previo"] is not None]
            if dias_dist:
                menores_18 = sum(1 for d in dias_dist if d < 18)
                print(f"Días con max_dist al refugio previo < 18: {menores_18}/{len(dias_dist)} ({100.0 * menores_18 / len(dias_dist):.1f} %)")
    return resumen


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--semillas", type=int, nargs="*", default=list(range(11, 31)))
    p.add_argument("--latidos", type=int, default=600)
    p.add_argument("--perfil", default="Equilibrado", choices=sorted(PERFILES))
    p.add_argument("--real", action="store_true", help="motivación real (Fase B): sin dominante ni cambios de Perfil")
    p.add_argument("--salida", type=str, default=None, help="fichero JSON donde guardar los resultados")
    args = p.parse_args()
    evaluar_fase_a(args.semillas, args.latidos, args.perfil, real=args.real, salida=args.salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
