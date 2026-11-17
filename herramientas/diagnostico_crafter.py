"""Diagnóstico de conducta y oscilaciones en Crafter.

Registra por latido para Crafter con el perfil indicado (por defecto Equilibrado, semillas 1 a 10):
- Estrategia ganadora en el Tribunal
- Fase de la estrategia (y fase de anidar)
- Objetivo propuesto
- Posición del jugador
- Distancia al refugio (si se conoce la madriguera)
- Inventario

Detecta oscilaciones de posición A-B-A-B durante 6 latidos o más y las clasifica en:
1. Cambio de ganador en el Tribunal (múltiples estrategias ganadoras en la oscilación).
2. Cambio de objetivo dentro de la misma estrategia (la misma estrategia gana siempre en la oscilación).

Calcula además:
- Porcentaje de vidas que consiguen pico.
- Porcentaje de vidas que anidan (alcanzan fase dormir).
- Distribución de la fase en que anidar se queda atascada.

Uso:
    python herramientas/diagnostico_crafter.py [--semillas 1..10] [--generaciones 1] [--perfil Equilibrado]
"""

import argparse
import os
import sys
import tempfile
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ida.ejecutor import ejecutar as vivir
from herramientas.benchmark import PERFILES


def diagnosticar(
    semillas: List[int],
    perfil: str = "Equilibrado",
    generaciones: int = 1,
    latidos: int = 600,
    silencioso: bool = False,
) -> Dict[str, Any]:
    vidas_totales = 0
    vidas_con_pico = 0
    vidas_anidan = 0
    fases_atascadas: Counter[str] = Counter()
    oscilaciones_tribunal = 0
    oscilaciones_objetivo = 0
    detalle_oscilaciones: List[Dict[str, Any]] = []
    madera_total: List[float] = []
    piedra_total: List[float] = []

    with tempfile.TemporaryDirectory(prefix="ida_diag_crafter_") as td:
        for sem in semillas:
            vidas_registros: List[List[Dict[str, Any]]] = []

            def crear_al_latir(registros_lista: List[List[Dict[str, Any]]]) -> Any:
                def al_latir(org: Any, onda: Any, _r: Dict[str, Any]) -> None:
                    if onda.ciclo == 1 or not registros_lista:
                        registros_lista.append([])
                    registros = registros_lista[-1]

                    yo = onda.ev("Propiocepcion").get("yo")
                    pos: Optional[Tuple[int, int]] = None
                    if yo is not None:
                        partes = str(yo.carga.get("ubicacion", "")).split("_")
                        if len(partes) == 3 and partes[0] == "celda":
                            pos = (int(partes[1]), int(partes[2]))

                    a = onda.ef("Accion").get("Accion")
                    est_id = a.carga.get("origen", {}).get("estrategia") if a is not None else None
                    est = onda.estrategias.get(est_id) if est_id is not None else None
                    est_nom = est.carga.get("nombre") if est is not None else (a.carga.get("sistema") if a is not None else None)
                    fase = est.carga.get("paso") if est is not None else None
                    obj = a.carga.get("objetivo") if a is not None else None

                    inv = dict(yo.carga.get("inventario", {})) if yo is not None else {}
                    tiene_pico = any(inv.get(k, 0) >= 1 for k in ("wood_pickaxe", "stone_pickaxe", "iron_pickaxe"))

                    madriguera = getattr(org.mundo, "madriguera", None)
                    dist_ref: Optional[int] = None
                    if madriguera and pos:
                        e = madriguera.get("e")
                        if e:
                            dist_ref = abs(pos[0] - e[0]) + abs(pos[1] - e[1])

                    anidar_p = next((p for p in onda.estrategias.values() if p.carga.get("nombre") == "anidar"), None)
                    fase_anidar = anidar_p.carga.get("paso") if anidar_p is not None else None

                    registros.append({
                        "ciclo": onda.ciclo,
                        "pos": pos,
                        "est": est_nom,
                        "fase": fase,
                        "obj": obj,
                        "inv": inv,
                        "tiene_pico": tiene_pico,
                        "dist_ref": dist_ref,
                        "fase_anidar": fase_anidar,
                    })
                return al_latir

            vivir(
                "crafter",
                latidos=latidos,
                semilla=sem,
                generaciones=generaciones,
                tabula_rasa=True,
                consola=False,
                datos=td,
                sin_experiencia=False,
                arquetipo_inicial=PERFILES[perfil],
                al_latir=crear_al_latir(vidas_registros),
            )

            # Analizar cada vida por separado
            for registros in vidas_registros:
                vidas_totales += 1
                tuvo_pico = any(r["tiene_pico"] for r in registros)
                anido = any(r["fase_anidar"] == "dormir" for r in registros)
                if tuvo_pico:
                    vidas_con_pico += 1
                if anido:
                    vidas_anidan += 1

                # Máximo de madera y piedra alcanzado en la vida
                max_madera = max((r["inv"].get("wood", 0.0) for r in registros), default=0.0)
                max_piedra = max((r["inv"].get("stone", 0.0) for r in registros), default=0.0)
                madera_total.append(max_madera)
                piedra_total.append(max_piedra)

                # Fase en que se queda atascada anidar (última fase activa o vista)
                ult_fase = "sin_activar"
                for r in reversed(registros):
                    if r["fase_anidar"]:
                        ult_fase = r["fase_anidar"]
                        break
                fases_atascadas[ult_fase] += 1

                # Detección de oscilaciones maximales A-B-A-B (L >= 6)
                n = len(registros)
                i = 0
                while i < n - 5:
                    p0 = registros[i]["pos"]
                    p1 = registros[i + 1]["pos"]
                    if p0 is not None and p1 is not None and p0 != p1:
                        j = i + 2
                        while j < n and registros[j]["pos"] == (p0 if (j - i) % 2 == 0 else p1):
                            j += 1
                        longitud = j - i
                        if longitud >= 6:
                            sub = registros[i:j]
                            ests = {r["est"] for r in sub if r["est"]}
                            tipo = "Tribunal" if len(ests) > 1 else "Objetivo"
                            if tipo == "Tribunal":
                                oscilaciones_tribunal += 1
                            else:
                                oscilaciones_objetivo += 1
                            detalle_oscilaciones.append({
                                "semilla": sem,
                                "inicio": registros[i]["ciclo"],
                                "fin": registros[j - 1]["ciclo"],
                                "longitud": longitud,
                                "tipo": tipo,
                                "estrategias": sorted(ests),
                                "pos_A": p0,
                                "pos_B": p1,
                            })
                            i = j - 1
                    i += 1

    pct_pico = (vidas_con_pico / vidas_totales * 100.0) if vidas_totales else 0.0
    pct_anidan = (vidas_anidan / vidas_totales * 100.0) if vidas_totales else 0.0
    total_osc = oscilaciones_tribunal + oscilaciones_objetivo

    resultado = {
        "perfil": perfil,
        "semillas": semillas,
        "generaciones": generaciones,
        "vidas": vidas_totales,
        "con_pico": vidas_con_pico,
        "pct_con_pico": pct_pico,
        "anidan": vidas_anidan,
        "pct_anidan": pct_anidan,
        "fases_atascadas": dict(fases_atascadas),
        "oscilaciones_total": total_osc,
        "oscilaciones_tribunal": oscilaciones_tribunal,
        "oscilaciones_objetivo": oscilaciones_objetivo,
        "media_max_madera": sum(madera_total) / len(madera_total) if madera_total else 0.0,
        "media_max_piedra": sum(piedra_total) / len(piedra_total) if piedra_total else 0.0,
        "detalle_oscilaciones": detalle_oscilaciones,
    }

    if not silencioso:
        imprimir_informe(resultado)

    return resultado


def imprimir_informe(r: Dict[str, Any]) -> None:
    print(f"\n=== DIAGNÓSTICO CRAFTER ({r['perfil']}, {r['vidas']} vidas, semillas {r['semillas']}) ===")
    print("| Métrica | Valor |")
    print("|---|---|")
    print(f"| Vidas analizadas | {r['vidas']} |")
    print(f"| Consiguen pico | {r['con_pico']}/{r['vidas']} ({r['pct_con_pico']:.1f}%) |")
    print(f"| Anidan (duermen) | {r['anidan']}/{r['vidas']} ({r['pct_anidan']:.1f}%) |")
    print(f"| Oscilaciones totales (L ≥ 6) | {r['oscilaciones_total']} |")
    print(f"| - Por cambio en Tribunal | {r['oscilaciones_tribunal']} |")
    print(f"| - Por cambio de objetivo (misma est.) | {r['oscilaciones_objetivo']} |")
    print(f"| Media máx. madera acumulada | {r['media_max_madera']:.2f} |")
    print(f"| Media máx. piedra acumulada | {r['media_max_piedra']:.2f} |")
    print("\nFases de anidar atascadas:")
    for fase, cnt in sorted(r["fases_atascadas"].items(), key=lambda x: -x[1]):
        print(f"  - {fase}: {cnt} vida(s)")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnóstico de conducta y oscilaciones en Crafter.")
    parser.add_argument("--semillas", type=int, nargs="+", default=list(range(1, 11)), help="Semillas a evaluar")
    parser.add_argument("--perfil", default="Equilibrado", choices=list(PERFILES.keys()), help="Perfil de arquetipo")
    parser.add_argument("--generaciones", "-g", type=int, default=1, help="Generaciones por linaje")
    parser.add_argument("--latidos", type=int, default=600, help="Latidos máximos por vida")
    args = parser.parse_args()

    diagnosticar(args.semillas, perfil=args.perfil, generaciones=args.generaciones, latidos=args.latidos)


if __name__ == "__main__":
    main()
