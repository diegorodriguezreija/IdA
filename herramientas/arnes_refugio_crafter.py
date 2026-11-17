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


def evaluar_fase_a(semillas: List[int], latidos: int = 600, perfil: str = "Equilibrado", detalle: bool = True) -> Dict[str, Any]:
    clase_mundo = cargar("crafter")
    perfil_original = clase_mundo.perfil
    init_original = RefugioNocturno.__init__

    def _init_dominante(self: RefugioNocturno) -> None:
        init_original(self)
        self.dominante = True

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
            if detalle:
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

    resumen = {
        "n": n,
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
    return resumen


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--semillas", type=int, nargs="*", default=list(range(11, 31)))
    p.add_argument("--latidos", type=int, default=600)
    p.add_argument("--perfil", default="Equilibrado", choices=sorted(PERFILES))
    args = p.parse_args()
    evaluar_fase_a(args.semillas, args.latidos, args.perfil)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
