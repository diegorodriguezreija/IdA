"""Diagnóstico de las partes D y E para C.3d.

D: Análisis detallado de causas de muerte en arnés largo (semillas 11-30, 3000 latidos).
E: Análisis de casos pendientes en arnés 600 (semillas 11-50):
   1. Salida al amanecer en estado crítico (muerte por zombi <= 40 latidos tras abrir).
   2. Sin roca a la vista en latido 120.
"""

from collections import Counter
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from herramientas.benchmark import PERFILES  # noqa: E402
from ida.ejecutor import ejecutar as vivir  # noqa: E402
from ida.mundos.crafter import RefugioNocturno, _dist  # noqa: E402


def _obtener_refugio(org: Any) -> Optional[RefugioNocturno]:
    for s in org.sistemas:
        if s.nombre == "S2":
            for c in s.componentes():
                if type(c).__name__ == "Estrategia":
                    inst = c.catalogo.get("refugio_nocturno")
                    if isinstance(inst, RefugioNocturno):
                        return inst
    return None


def diagnosticar_semilla_d(sem: int, max_latidos: int = 3000) -> Optional[Dict[str, Any]]:
    historial: List[Dict[str, Any]] = []
    causa_muerte: Optional[str] = None
    refugio_instancia: Optional[RefugioNocturno] = None

    def al_latir(org: Any, onda: Any, _r: Dict[str, Any]) -> None:
        nonlocal causa_muerte, refugio_instancia
        p = org.mundo.jugador
        ciclo = onda.ciclo
        inv = p.inventory
        luz = float(org.mundo.env._world.daylight)

        if refugio_instancia is None:
            refugio_instancia = _obtener_refugio(org)

        paso_s2 = (onda.notas.get("estrategias_S2") or {}).get("refugio_nocturno")
        fase = paso_s2.get("fase", "") if isinstance(paso_s2, dict) else ""
        mina = paso_s2.get("mina") if isinstance(paso_s2, dict) else None

        ganador_est = ""
        for sis in ("S1", "S2", "S3"):
            ejec = (onda.notas.get(f"estrategias_{sis}") or {}).get("ejecutada")
            if ejec:
                ganador_est = f"{sis}:{ejec}"
                break
        if not ganador_est:
            evaluados = onda.notas.get("evaluados", [])
            ganador_est = evaluados[0].get("sistema", "desconocida") if evaluados else "desconocida"

        pos = (int(p.pos[0]), int(p.pos[1]))
        galeria: List[Tuple[int, int]] = []
        if mina is not None:
            e0, (dx, dy) = mina
            galeria = [(e0[0] + k * dx, e0[1] + k * dy) for k in (1, 2, 3)]
        dentro = (pos in galeria) or (fase == "dormir")

        ef_ant = org.ultimo_efecto
        if ef_ant and ef_ant.muerte:
            causa_muerte = ef_ant.causa

        historial.append({
            "ciclo": ciclo,
            "fase": fase,
            "ganador": ganador_est,
            "comida": int(inv.get("food", 0)),
            "agua": int(inv.get("drink", 0)),
            "salud": int(p.health),
            "luz": round(luz, 3),
            "dentro": dentro,
            "pos": pos,
            "mina": mina,
        })

    vivir(
        "crafter",
        latidos=max_latidos,
        semilla=sem,
        consola=False,
        sin_experiencia=False,
        al_latir=al_latir,
        opciones_mundo={"perfil": PERFILES["Equilibrado"]},
    )

    if not causa_muerte or not historial:
        return None

    idx_muerte = len(historial) - 1
    info_muerte = historial[idx_muerte]
    idx_30_prev = max(0, idx_muerte - 30)
    info_30_prev = historial[idx_30_prev]
    pasos_prev_20 = historial[max(0, idx_muerte - 20):]

    dia = info_muerte["ciclo"] // 290
    return {
        "semilla": sem,
        "latido": info_muerte["ciclo"],
        "dia": dia,
        "causa": causa_muerte,
        "era_de_dia": info_muerte["luz"] >= 0.5,
        "luz_muerte": info_muerte["luz"],
        "dentro_muerte": info_muerte["dentro"],
        "fase_muerte": info_muerte["fase"],
        "ganador_muerte": info_muerte["ganador"],
        "comida_30_prev": info_30_prev["comida"],
        "agua_30_prev": info_30_prev["agua"],
        "salud_30_prev": info_30_prev["salud"],
        "fases_20_prev": [p["fase"] for p in pasos_prev_20],
        "ganadores_20_prev": [p["ganador"] for p in pasos_prev_20],
    }


def diagnosticar_semilla_e(sem: int, max_latidos: int = 600) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    refugio_inst: Optional[RefugioNocturno] = None
    sello_dia1 = False
    abrio_salida = False
    latido_abrir: Optional[int] = None
    datos_abrir: Dict[str, Any] = {}
    muerto_por_zombi_post_abrir = False
    causa_muerte: Optional[str] = None
    latido_muerte: Optional[int] = None

    sin_roca_l120 = False
    datos_l120: Dict[str, Any] = {}

    def al_latir(org: Any, onda: Any, _r: Dict[str, Any]) -> None:
        nonlocal refugio_inst, sello_dia1, abrio_salida, latido_abrir, datos_abrir
        nonlocal muerto_por_zombi_post_abrir, causa_muerte, latido_muerte, sin_roca_l120, datos_l120
        p = org.mundo.jugador
        ciclo = onda.ciclo
        inv = p.inventory
        luz = float(org.mundo.env._world.daylight)

        if refugio_inst is None:
            refugio_inst = _obtener_refugio(org)

        paso_s2 = (onda.notas.get("estrategias_S2") or {}).get("refugio_nocturno")
        fase = paso_s2.get("fase", "") if isinstance(paso_s2, dict) else ""
        mina = paso_s2.get("mina") if isinstance(paso_s2, dict) else None

        if fase == "dormir" and ciclo < 260:
            sello_dia1 = True

        # Caso E.1: detectar apertura del refugio
        if sello_dia1 and not abrio_salida and fase in ("amanecer", "abastecer"):
            abrio_salida = True
            latido_abrir = ciclo

            pos_j = (int(p.pos[0]), int(p.pos[1]))
            from types import SimpleNamespace
            ctx_sim: Any = SimpleNamespace(onda=onda, latido=ciclo)
            presion = refugio_inst._presion_interna(inv, False) if refugio_inst else 0.0
            urgencia = refugio_inst._conviene_salir(ctx_sim, inv, luz, mina) if refugio_inst else False
            riesgo = refugio_inst._riesgo_exterior(ctx_sim, luz, pos_j) if refugio_inst else 0.0
            agua_dentro = (refugio_inst._agua_accesible_dentro(mina) is not None) if refugio_inst else False

            exter = onda.ev("Exterocepcion") or {}
            hostiles_6 = [
                pz for pz in exter.values()
                if pz.clase in ("zombi", "esqueleto") and "pos" in pz.carga.get("datos", {})
                and _dist(pos_j, (int(pz.carga["datos"]["pos"][0]), int(pz.carga["datos"]["pos"][1]))) <= 6
            ]

            datos_abrir = {
                "semilla": sem,
                "latido_abrir": ciclo,
                "luz": round(luz, 3),
                "comida": int(inv.get("food", 0)),
                "agua": int(inv.get("drink", 0)),
                "salud": int(p.health),
                "presion_interna": round(presion, 3),
                "urgencia_conviene_salir": urgencia,
                "riesgo_exterior": round(riesgo, 3),
                "hostiles_cerca": len(hostiles_6),
                "agua_dentro": agua_dentro,
            }

        ef_ant = org.ultimo_efecto
        if ef_ant and ef_ant.muerte:
            causa_muerte = ef_ant.causa
            latido_muerte = ciclo
            if abrio_salida and latido_abrir is not None:
                if ciclo - latido_abrir <= 40 and ef_ant.causa == "zombi":
                    muerto_por_zombi_post_abrir = True

        # Caso E.2: comprobación en latido 120
        if ciclo == 120:
            mapa = refugio_inst.mapa if refugio_inst else {}
            tiene_roca = any(m in ("stone", "coal") for m in mapa.values())
            if not tiene_roca:
                sin_roca_l120 = True
                pos_j = (int(p.pos[0]), int(p.pos[1]))
                w = org.mundo.env._world
                rocas_mundo: List[Tuple[int, int]] = []
                aguas_mundo: List[Tuple[int, int]] = []
                for x in range(w.area[0]):
                    for y in range(w.area[1]):
                        mat = w[(x, y)][0]
                        if mat in ("stone", "coal"):
                            rocas_mundo.append((x, y))
                        elif mat == "water":
                            aguas_mundo.append((x, y))

                dist_roca_min = min(_dist(pos_j, r) for r in rocas_mundo) if rocas_mundo else 999
                dist_agua_min = min(_dist(pos_j, a) for a in aguas_mundo) if aguas_mundo else 999
                visitadas_cnt = len(refugio_inst.visitadas) if refugio_inst else 0
                rumbo = refugio_inst.rumbo if refugio_inst else (0, 0)

                datos_l120 = {
                    "semilla": sem,
                    "pos_l120": pos_j,
                    "dist_real_roca": dist_roca_min,
                    "dist_real_agua": dist_agua_min,
                    "casillas_visitadas": visitadas_cnt,
                    "casillas_mapa": len(mapa),
                    "rumbo": rumbo,
                }

    vivir(
        "crafter",
        latidos=max_latidos,
        semilla=sem,
        consola=False,
        sin_experiencia=False,
        al_latir=al_latir,
        opciones_mundo={"perfil": PERFILES["Equilibrado"]},
    )

    res_e1 = None
    if muerto_por_zombi_post_abrir:
        datos_abrir["latido_muerte"] = latido_muerte
        datos_abrir["latidos_desde_abrir"] = (latido_muerte - latido_abrir) if latido_muerte and latido_abrir else 0
        res_e1 = datos_abrir

    res_e2 = None
    if sin_roca_l120:
        datos_l120["causa_muerte"] = causa_muerte
        datos_l120["latidos_vividos"] = latido_muerte or max_latidos
        res_e2 = datos_l120

    return res_e1, res_e2


def main() -> None:
    print("=== EJECUTANDO DIAGNÓSTICO D (semillas 11-30, 3000 latidos) ===", flush=True)
    muertes_d = []
    for s in range(11, 31):
        m = diagnosticar_semilla_d(s, 3000)
        if m:
            muertes_d.append(m)

    print("\n=======================================================")
    print("RESULTADOS PARTE D: ¿QUÉ MATA DESPUÉS?")
    print("=======================================================")
    print(f"Total muertes analizadas: {len(muertes_d)}")

    causas_cnt = Counter(m["causa"] for m in muertes_d)
    dias_cnt = Counter(m["dia"] for m in muertes_d)
    print(f"Desglose por causa: {dict(causas_cnt)}")
    print(f"Desglose por día:   {dict(dias_cnt)}")

    situaciones = []
    for m in muertes_d:
        fase_dom = Counter(m["fases_20_prev"]).most_common(1)[0][0] if m["fases_20_prev"] else "?"
        ganador_dom = Counter(m["ganadores_20_prev"]).most_common(1)[0][0] if m["ganadores_20_prev"] else "?"
        sit = (
            f"Causa={m['causa']}, "
            f"{'Dentro' if m['dentro_muerte'] else 'Fuera'}, "
            f"{'Día' if m['era_de_dia'] else 'Noche'}, "
            f"Fase={fase_dom}, "
            f"Ganador={ganador_dom}"
        )
        situaciones.append(sit)

    top5 = Counter(situaciones).most_common(5)
    print("\nTop 5 situaciones de muerte más repetidas:")
    for sit, cnt in top5:
        print(f"  [{cnt:2d} vidas] {sit}")

    print("\nDetalle por muerte:")
    for m in muertes_d:
        f_dom = Counter(m["fases_20_prev"]).most_common(1)[0][0] if m["fases_20_prev"] else "?"
        g_dom = Counter(m["ganadores_20_prev"]).most_common(1)[0][0] if m["ganadores_20_prev"] else "?"
        print(
            f"  Semilla {m['semilla']:2d}: L={m['latido']:4d} (Día {m['dia']}) causa={m['causa']:9s} | "
            f"{'Dentro' if m['dentro_muerte'] else 'Fuera':6s} | {'Día' if m['era_de_dia'] else 'Noche':5s} (luz={m['luz_muerte']:.2f}) | "
            f"Estado -30L: C={m['comida_30_prev']} A={m['agua_30_prev']} S={m['salud_30_prev']} | "
            f"Fase_20={f_dom} Gan_20={g_dom}"
        )

    print("\n=== EJECUTANDO DIAGNÓSTICO E (semillas 11-50, 600 latidos) ===", flush=True)
    e1_list = []
    e2_list = []
    for s in range(11, 51):
        c1, c2 = diagnosticar_semilla_e(s, 600)
        if c1:
            e1_list.append(c1)
        if c2:
            e2_list.append(c2)

    print("\n=======================================================")
    print("RESULTADOS PARTE E.1: SALIDA AL AMANECER EN ESTADO CRÍTICO (muerte zombi <= 40L tras abrir)")
    print("=======================================================")
    print(f"Total vidas afectadas: {len(e1_list)}")
    for c in e1_list:
        print(
            f"  Semilla {c['semilla']:2d}: Abrió en L={c['latido_abrir']} (luz={c['luz']}, C={c['comida']}, A={c['agua']}, S={c['salud']}) | "
            f"presion={c['presion_interna']} conviene_salir={c['urgencia_conviene_salir']} riesgo={c['riesgo_exterior']} "
            f"hostiles_6={c['hostiles_cerca']} agua_dentro={c['agua_dentro']} | "
            f"Murió por zombi en L={c['latido_muerte']} ({c['latidos_desde_abrir']} latidos tras abrir)"
        )

    print("\n=======================================================")
    print("RESULTADOS PARTE E.2: SIN ROCA A LA VISTA EN L120")
    print("=======================================================")
    print(f"Total vidas sin roca en mapa a L120: {len(e2_list)}")
    for c in e2_list:
        print(
            f"  Semilla {c['semilla']:2d}: Pos en L120={c['pos_l120']} | "
            f"Dist real roca más cercana={c['dist_real_roca']} | Dist real agua más cercana={c['dist_real_agua']} | "
            f"Casillas visitadas={c['casillas_visitadas']}, mapa={c['casillas_mapa']} | Rumbo={c['rumbo']} | "
            f"Desenlace: L={c['latidos_vividos']} causa={c['causa_muerte']}"
        )


if __name__ == "__main__":
    main()
