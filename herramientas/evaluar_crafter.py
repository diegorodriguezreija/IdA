"""Evaluación oficial de Crafter para IdA (Hafner, 2021).

Ejecuta episodios sucesivos bajo un linaje continuo hasta acumular N pasos (--pasos).
Calcula la Crafter Score oficial, la tasa de éxito por logro, la puntuación de la primera vida,
el intervalo de confianza del 95 % por remuestreo de episodios (bootstrap) y el desglose de causas de muerte.

Uso:
    python herramientas/evaluar_crafter.py --pasos 10000 --semilla 31
    python herramientas/evaluar_crafter.py --pasos 100000 --semilla 31 --vista oficial
    python herramientas/evaluar_crafter.py --pasos 100000 --semilla 31 --sin-estrategias-propias
"""

import argparse
import math
import os
import random
import shutil
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from ida.core.azar import Azar  # noqa: E402
from ida.core.latido import Organismo  # noqa: E402
from ida.core.linaje import Arquetipo, Linaje  # noqa: E402
from ida.core.memoria import Memoria  # noqa: E402
from ida.core.persistencia import Persistencia  # noqa: E402
from ida.mundos import cargar  # noqa: E402
from ida.sistemas import crear_sistemas  # noqa: E402

PERFILES = {
    "Equilibrado": {"apertura": 0.50, "responsabilidad": 0.50, "neuroticismo": 0.50, "extraversion": 0.50, "umbral_miedo": 0.60},
    "Osado": {"apertura": 0.85, "responsabilidad": 0.50, "neuroticismo": 0.20, "extraversion": 0.80, "umbral_miedo": 0.40},
    "Prudente": {"apertura": 0.25, "responsabilidad": 0.70, "neuroticismo": 0.75, "extraversion": 0.30, "umbral_miedo": 0.75},
    "Reactivo": {"apertura": 0.50, "responsabilidad": 0.20, "neuroticismo": 0.80, "extraversion": 0.50, "umbral_miedo": 0.50},
}


def calcular_crafter_score(tasas_exito: Dict[str, float]) -> float:
    """Calcula Crafter Score = exp(mean(ln(1 + s_i))) - 1 con s_i en %."""
    if not tasas_exito:
        return 0.0
    suma_ln = sum(math.log(1.0 + max(0.0, s)) for s in tasas_exito.values())
    media_ln = suma_ln / len(tasas_exito)
    return float(math.exp(media_ln) - 1.0)


def bootstrap_ci(
    episodios: List[Dict[str, Any]],
    logros: List[str],
    n_boot: int = 2000,
    alpha: float = 0.05,
    semilla: int = 42,
) -> Tuple[float, float]:
    """Intervalo de confianza empírico para la Crafter Score por remuestreo de episodios con reemplazo."""
    n = len(episodios)
    if n <= 1:
        s = calcular_crafter_score(
            {logro: 100.0 if any(logro in ep["logros"] for ep in episodios) else 0.0 for logro in logros}
        )
        return (s, s)

    rnd = random.Random(semilla)
    scores: List[float] = []
    logros_set = set(logros)

    for _ in range(n_boot):
        muestra = [rnd.choice(episodios) for _ in range(n)]
        tasas = {}
        for l in logros_set:
            exitos = sum(1 for ep in muestra if l in ep["logros"])
            tasas[l] = (exitos / n) * 100.0
        scores.append(calcular_crafter_score(tasas))

    scores.sort()
    idx_inf = int((alpha / 2.0) * n_boot)
    idx_sup = int((1.0 - alpha / 2.0) * n_boot)
    idx_sup = min(idx_sup, n_boot - 1)
    return (scores[idx_inf], scores[idx_sup])


def evaluar(
    pasos_objetivo: int,
    semilla_base: int,
    perfil: str = "Equilibrado",
    vista: str = "oficial",
    longitud_episodio: int = 10000,
    sin_estrategias_propias: bool = False,
    sin_herencia: bool = False,
    manual: str = "estricto",
    quiet: bool = False,
) -> Dict[str, Any]:
    import crafter.constants

    logros_oficiales = sorted(crafter.constants.achievements)

    clase_crafter = cargar("crafter")
    estrategias_originales = clase_crafter.estrategias_propias
    if sin_estrategias_propias:
        clase_crafter.estrategias_propias = lambda self: {}

    temp_dir = tempfile.mkdtemp(prefix="ida_eval_crafter_")
    m = clase_crafter(vista=vista, longitud=longitud_episodio, manual=manual)

    azar = Azar(semilla_base)
    linaje = Linaje(os.path.join(temp_dir, "linaje.json"))
    persistencia = Persistencia(os.path.join(temp_dir, "memoria.db"))

    pasos_acumulados = 0
    episodios: List[Dict[str, Any]] = []
    t_inicio = time.perf_counter()
    g = 0
    vivencia: Optional[Dict[str, float]] = None
    p_params = PERFILES.get(perfil, PERFILES["Equilibrado"])

    try:
        while pasos_acumulados < pasos_objetivo:
            azar_g = azar.derivar(g + 1)
            if sin_herencia:
                arq = Arquetipo(linaje="Crafter", **p_params)
                legado_a_heredar = {}
            else:
                padre = linaje.ultimo_arquetipo()
                if padre:
                    arq = padre.mutar(azar_g, vivencia)
                else:
                    arq = Arquetipo(linaje="Crafter", **p_params)
                legado_a_heredar = linaje.legado() or {}

            memoria = Memoria(m.perfil.memoria)
            memoria.aplicar_manual(m.manual())       # paso 2: el manual del mundo, antes de heredar (también sin herencia)
            if legado_a_heredar:
                memoria.heredar(legado_a_heredar, m.perfil.mecanismos.tasa_herencia)

            pasos_restantes = pasos_objetivo - pasos_acumulados
            max_latidos_ep = min(longitud_episodio, pasos_restantes)

            m.reiniciar(azar_g.semilla, longitud=longitud_episodio)
            org = Organismo(m, crear_sistemas(), arq, memoria, azar_g, con_experiencia=True)
            persistencia.nueva_vida()
            org.al_dormir = lambda o: persistencia.volcar(o.memoria, o.arquetipo.id, o.ciclo)

            t0_ep = time.perf_counter()
            vividos = org.vivir(max_latidos_ep)
            t_ep = time.perf_counter() - t0_ep
            pasos_acumulados += vividos

            persistencia.volcar(memoria, arq.id, org.ciclo)

            total = max(1, vividos)
            vivencia = {
                "fraccion_miedo": org.contadores["miedo"] / total,
                "fraccion_calma": org.contadores["calma"] / total,
                "fraccion_hambre": org.contadores["hambre"] / total,
            }

            # Un episodio que llega a longitud_episodio (10000) o que sigue vivo abre vida nueva sin causa de muerte
            causa_muerte = org.causa_muerte if not org.soma.esta_vivo else None
            logros_ep = set(m.logros())

            resumen = {
                "latidos": vividos,
                "vivo": org.soma.esta_vivo,
                "causa_muerte": causa_muerte,
                "puntuacion": m.puntuacion(),
                "guillotinas": org.contadores["guillotinas"],
            }
            linaje.registrar(arq, resumen, memoria.legado(org.ciclo))

            ep_info = {
                "episodio": g + 1,
                "semilla": azar_g.semilla,
                "pasos": vividos,
                "vivo": org.soma.esta_vivo,
                "causa_muerte": causa_muerte,
                "logros": logros_ep,
                "t_segundos": t_ep,
            }
            episodios.append(ep_info)

            if not quiet:
                estado = "vivo" if org.soma.esta_vivo else f"muerto ({causa_muerte or 'desconocida'})"
                print(
                    f"Episodio {g + 1:3d} (semilla {azar_g.semilla:6d}): {vividos:5d} pasos ({pasos_acumulados:6d}/{pasos_objetivo}), "
                    f"{len(logros_ep):2d} logros, {estado} · {t_ep:.1f}s"
                )

            g += 1
    finally:
        m.cerrar()
        persistencia.cerrar()
        if sin_estrategias_propias:
            clase_crafter.estrategias_propias = estrategias_originales
        shutil.rmtree(temp_dir, ignore_errors=True)

    t_total = time.perf_counter() - t_inicio
    ms_por_paso = (t_total * 1000.0) / max(1, pasos_acumulados)

    # Tasas de éxito por logro
    n_ep = len(episodios)
    tasas_exito: Dict[str, float] = {}
    for l in logros_oficiales:
        count = sum(1 for ep in episodios if l in ep["logros"])
        tasas_exito[l] = round((count / n_ep) * 100.0, 2)

    score_total = calcular_crafter_score(tasas_exito)
    ci_inf, ci_sup = bootstrap_ci(episodios, logros_oficiales, n_boot=2000, semilla=semilla_base)

    # Desglose de causas de muerte / finalización
    causas_conteo: Dict[str, int] = {}
    for ep in episodios:
        c = ep["causa_muerte"] if ep["causa_muerte"] is not None else ("cortado por presupuesto" if ep["vivo"] else "desconocida")
        causas_conteo[c] = causas_conteo.get(c, 0) + 1

    return {
        "pasos": pasos_acumulados,
        "episodios": n_ep,
        "tiempo_segundos": round(t_total, 2),
        "ms_por_paso": round(ms_por_paso, 2),
        "score": round(score_total, 2),
        "score_ci_95": (round(ci_inf, 2), round(ci_sup, 2)),
        "tasas_logros": tasas_exito,
        "causas_muerte": causas_conteo,
        "perfil": perfil,
        "semilla_base": semilla_base,
        "vista": vista,
        "sin_estrategias_propias": sin_estrategias_propias,
        "sin_herencia": sin_herencia,
        "manual": manual,
    }


def imprimir_informe(res: Dict[str, Any]) -> None:
    print("\n" + "=" * 65)
    print(" EVALUACIÓN OFICIAL CRAFTER · IdA")
    print("=" * 65)
    config_estr = "SIN estrategias propias (suelo)" if res["sin_estrategias_propias"] else "CON estrategias propias"
    herencia_str = "SIN herencia" if res["sin_herencia"] else "CON linaje"
    print(f"Configuración: Perfil {res['perfil']} · Vista {res['vista']} · {config_estr} · {herencia_str}")
    print(f"Presupuesto:   {res['pasos']} pasos en {res['episodios']} episodios (semilla base {res['semilla_base']})")
    print(f"Rendimiento:   {res['tiempo_segundos']:.1f} s total ({res['ms_por_paso']:.2f} ms/paso)")
    print("-" * 65)
    etiqueta_score = "Score sin herencia" if res["sin_herencia"] else "Score con linaje"
    print(f"{etiqueta_score:<24}: {res['score']:.2f} %  (IC 95 %: [{res['score_ci_95'][0]:.2f}, {res['score_ci_95'][1]:.2f}] %)")
    print("-" * 65)
    print("Tasa de éxito por logro (22 oficiales):")
    for logro, tasa in sorted(res["tasas_logros"].items(), key=lambda x: (-x[1], x[0])):
        barra = "█" * int(tasa // 5)
        print(f"  {logro:<22} {tasa:6.2f} %  {barra}")
    print("-" * 65)
    print("Causas de muerte / finalización:")
    for causa, n in sorted(res["causas_muerte"].items(), key=lambda x: -x[1]):
        pct = (n / res["episodios"]) * 100.0
        print(f"  {causa:<22} {n:4d} episodios ({pct:5.1f} %)")
    print("=" * 65 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pasos", type=int, default=10000, help="Presupuesto total de pasos acumulados")
    parser.add_argument("--semilla", type=int, default=31, help="Semilla base inicial")
    parser.add_argument("--perfil", type=str, default="Equilibrado", choices=list(PERFILES.keys()), help="Perfil psicológico")
    parser.add_argument("--vista", type=str, default="oficial", choices=["oficial", "cuadrada"], help="Tipo de vista")
    parser.add_argument("--longitud", type=int, default=10000, help="Límite de pasos por episodio (oficial = 10000)")
    parser.add_argument("--sin-estrategias-propias", action="store_true", help="Evalúa el suelo (sin estrategias propias de Crafter)")
    parser.add_argument("--sin-herencia", action="store_true", help="Cada episodio empieza sin legado (sin herencia entre vidas)")
    parser.add_argument("--manual", type=str, default="estricto", choices=["estricto", "ampliado"],
                        help="Manual declarativo de Crafter (paso 2)")
    parser.add_argument("--salida", type=str, default=None, help="Ruta de archivo JSON donde guardar el resultado")
    parser.add_argument("--quiet", action="store_true", help="Silencia el registro por episodio")
    args = parser.parse_args()

    res = evaluar(
        pasos_objetivo=args.pasos,
        semilla_base=args.semilla,
        perfil=args.perfil,
        vista=args.vista,
        longitud_episodio=args.longitud,
        sin_estrategias_propias=args.sin_estrategias_propias,
        sin_herencia=args.sin_herencia,
        manual=args.manual,
        quiet=args.quiet,
    )
    imprimir_informe(res)
    if args.salida:
        import json

        os.makedirs(os.path.dirname(os.path.abspath(args.salida)), exist_ok=True)
        with open(args.salida, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
