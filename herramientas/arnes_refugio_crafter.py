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
import os
import sys
import tempfile
from typing import Any, Dict, List

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from herramientas.benchmark import PERFILES  # noqa: E402
from ida.core.mundo import Necesidad  # noqa: E402
from ida.ejecutor import ejecutar as vivir  # noqa: E402
from ida.mundos import cargar  # noqa: E402
from ida.mundos.crafter import RefugioNocturno  # noqa: E402


def evaluar_fase_a(semillas: List[int], latidos: int = 600, perfil: str = "Equilibrado", detalle: bool = True,
                   real: bool = False) -> Dict[str, Any]:
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
            }

            def al_latir(org: Any, onda: Any, _r: Dict[str, Any], iv: Dict[str, Any] = info_vida) -> None:
                p = org.mundo.jugador
                inv = p.inventory
                luz = float(org.mundo.env._world.daylight)
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
        "resultados": resultados,
    }
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
    return resumen


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--semillas", type=int, nargs="*", default=list(range(11, 31)))
    p.add_argument("--latidos", type=int, default=600)
    p.add_argument("--perfil", default="Equilibrado", choices=sorted(PERFILES))
    p.add_argument("--real", action="store_true", help="motivación real (Fase B): sin dominante ni cambios de Perfil")
    args = p.parse_args()
    evaluar_fase_a(args.semillas, args.latidos, args.perfil, real=args.real)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
