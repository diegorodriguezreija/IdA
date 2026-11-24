"""Evaluación oficial de Crafter para IdA (Hafner, 2021).

Ejecuta episodios sucesivos bajo un linaje continuo hasta acumular N pasos (--pasos).
Calcula la Crafter Score oficial, la tasa de éxito por logro, la puntuación de la primera vida,
el intervalo de confianza del 95 % por remuestreo de episodios (bootstrap) y el desglose de causas de muerte.

Reproducibilidad: el Core corta un latido que pasa de ``Perfil.frecuencia_ms`` en tiempo de reloj (guillotina); con la
máquina cargada (varias evaluaciones a la vez) se cortan latidos que solos no se cortarían y la vida cambia. El JSON
guarda los latidos cortados (``latidos_cortados`` y por episodio) y el resumen los imprime. ``--verificar-determinismo N``
ejecuta dos veces los primeros N pasos y falla si las decisiones difieren.

``--plazo-logico OPS`` cambia el plazo de reloj de la guillotina por uno lógico (deuda 13): el latido se mide en
operaciones (llamadas a ``Onda.control_vital``) a razón de OPS operaciones por milisegundo de plazo, y la misma semilla
da la misma vida aunque la máquina esté cargada. Sin la opción, la guillotina sigue cortando por reloj.

El JSON guarda por episodio (``por_episodio``) los pasos, la causa de muerte y los logros, para la comparación
pareada de ``resumen_evaluacion.py --pareada``.

Uso:
    python herramientas/evaluar_crafter.py --pasos 10000 --semilla 31
    python herramientas/evaluar_crafter.py --verificar-determinismo 2000 --semilla 31 --sin-herencia --sin-estrategias-propias
    python herramientas/evaluar_crafter.py --pasos 100000 --semilla 31 --vista oficial
    python herramientas/evaluar_crafter.py --pasos 100000 --semilla 31 --sin-estrategias-propias
    python herramientas/evaluar_crafter.py --pasos 100000 --semilla 31 --plazo-logico 6
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

from ida.nucleo.azar import Azar  # noqa: E402
from ida.core.latido import Organismo  # noqa: E402
from ida.nucleo.linaje import Arquetipo, Linaje  # noqa: E402
from ida.nucleo.memoria import Memoria  # noqa: E402
from ida.nucleo.mundo import Registro  # noqa: E402
from ida.nucleo.persistencia import Persistencia  # noqa: E402
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
    mecanismos: Optional[List[str]] = None,
    traza: Optional[List[Tuple[int, int, str, str]]] = None,
    plazo_logico: Optional[float] = None,
    legado_salida: Optional[str] = None,
) -> Dict[str, Any]:
    """``traza``: si se da, se le añade (episodio, latido, verbo, objetivo) de cada acción ejecutada.
    ``plazo_logico``: operaciones por ms de plazo (guillotina lógica); ``None`` = plazo de reloj."""
    import crafter.constants

    logros_oficiales = sorted(crafter.constants.achievements)

    clase_crafter = cargar("crafter")
    registro_original = clase_crafter.registro
    if sin_estrategias_propias:
        clase_crafter.registro = lambda self: Registro(cuerpo=registro_original(self).cuerpo)   # conserva el cuerpo (D10)
    perfil_original = clase_crafter.perfil
    if mecanismos:      # interruptores de Perfil.mecanismos (bloques E y F)
        from dataclasses import replace
        clase_crafter.perfil = replace(perfil_original, mecanismos=replace(perfil_original.mecanismos, **dict.fromkeys(mecanismos, True)))

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
    legados: Optional[List[Dict[str, Any]]] = [] if legado_salida else None

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
            org.ops_por_ms = plazo_logico
            persistencia.nueva_vida()
            org.al_dormir = lambda o: persistencia.volcar(o.memoria, o.arquetipo.id, o.ciclo)

            t0_ep = time.perf_counter()
            if traza is None:
                vividos = org.vivir(max_latidos_ep)
            else:
                def anotar(o: Any, onda: Any, ep: int = g + 1) -> None:
                    a = onda.reactiva.ef.get("Accion", {}).get("Accion")
                    traza.append((ep, o.ciclo, str(getattr(a.carga.get("verbo"), "value", "")) if a else "",
                                  str(a.carga.get("objetivo", "")) if a else ""))
                vividos = org.vivir(max_latidos_ep, al_latir=anotar)
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
            legado_ep = memoria.legado(org.ciclo)
            linaje.registrar(arq, resumen, legado_ep)
            if legados is not None:
                legados.append(legado_ep)

            ep_info = {
                "episodio": g + 1,
                "semilla": azar_g.semilla,
                "pasos": vividos,
                "vivo": org.soma.esta_vivo,
                "causa_muerte": causa_muerte,
                "logros": logros_ep,
                "t_segundos": t_ep,
                "latidos_cortados": org.contadores["guillotinas"],
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
            clase_crafter.registro = registro_original
        clase_crafter.perfil = perfil_original
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

    if legado_salida and legados is not None:
        import json

        os.makedirs(os.path.dirname(os.path.abspath(legado_salida)), exist_ok=True)
        with open(legado_salida, "w", encoding="utf-8") as f:
            json.dump(legados, f, indent=2)

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
        "mecanismos": sorted(mecanismos or []),
        "latidos_cortados": sum(ep["latidos_cortados"] for ep in episodios),
        "latidos_cortados_por_episodio": [ep["latidos_cortados"] for ep in episodios],
        "plazo_logico": plazo_logico,
        "por_episodio": [{"pasos": ep["pasos"], "causa_muerte": ep["causa_muerte"], "vivo": ep["vivo"],
                          "logros": sorted(ep["logros"])} for ep in episodios],
    }


def imprimir_informe(res: Dict[str, Any]) -> None:
    print("\n" + "=" * 65)
    print(" EVALUACIÓN OFICIAL CRAFTER · IdA")
    print("=" * 65)
    config_estr = "SIN estrategias propias (suelo)" if res["sin_estrategias_propias"] else "CON estrategias propias"
    herencia_str = "SIN herencia" if res["sin_herencia"] else "CON linaje"
    print(f"Configuración: Perfil {res['perfil']} · Vista {res['vista']} · {config_estr} · {herencia_str}")
    print(f"Mecanismos:    {', '.join(res.get('mecanismos') or []) or 'ninguno'}")
    print(f"Presupuesto:   {res['pasos']} pasos en {res['episodios']} episodios (semilla base {res['semilla_base']})")
    print(f"Rendimiento:   {res['tiempo_segundos']:.1f} s total ({res['ms_por_paso']:.2f} ms/paso)")
    cortados = res.get("latidos_cortados", 0)
    con_cortes = sum(1 for n in res.get("latidos_cortados_por_episodio", []) if n)
    plazo = f"plazo lógico, {res['plazo_logico']:g} operaciones/ms" if res.get("plazo_logico") else "plazo de reloj"
    print(f"Guillotina:    {plazo}; {cortados} latidos cortados en {con_cortes} episodios"
          + ("" if not cortados or res.get("plazo_logico") else "  ⚠ resultado no reproducible: repetir sin otros procesos"))
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


def verificar_determinismo(args: argparse.Namespace) -> int:
    """Dos ejecuciones de los primeros N pasos: deben dar la misma secuencia de acciones (episodio, latido, verbo, objetivo).
    Devuelve 0 si coinciden y 1 si no, con el primer latido distinto y los latidos cortados de cada ejecución."""
    trazas: List[List[Tuple[int, int, str, str]]] = []
    cortados: List[int] = []
    for _ in range(2):
        traza: List[Tuple[int, int, str, str]] = []
        res = evaluar(args.verificar_determinismo, args.semilla, perfil=args.perfil, vista=args.vista, longitud_episodio=args.longitud,
                      sin_estrategias_propias=args.sin_estrategias_propias, sin_herencia=args.sin_herencia, manual=args.manual,
                      quiet=True, mecanismos=args.mecanismos, traza=traza, plazo_logico=args.plazo_logico)
        trazas.append(traza)
        cortados.append(int(res["latidos_cortados"]))
    a, b = trazas
    distinto = next((i for i, (x, y) in enumerate(zip(a, b, strict=False)) if x != y), None)
    if distinto is None and len(a) != len(b):
        distinto = min(len(a), len(b))
    print(f"Determinismo ({args.verificar_determinismo} pasos, semilla {args.semilla}): {len(a)} y {len(b)} acciones; "
          f"latidos cortados {cortados[0]} y {cortados[1]}")
    if distinto is None:
        print("OK: las dos ejecuciones coinciden.")
        return 0
    x = a[distinto] if distinto < len(a) else None
    y = b[distinto] if distinto < len(b) else None
    print(f"DIFIEREN en la acción {distinto}: {x} frente a {y}")
    return 1


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
    parser.add_argument("--legado-salida", type=str, default=None, help="Ruta de archivo JSON donde guardar la lista de legados de cada vida")
    parser.add_argument("--quiet", action="store_true", help="Silencia el registro por episodio")
    parser.add_argument("--mecanismos", nargs="*", default=[],
                        help="Interruptores de Perfil.mecanismos que se encienden (bloques E y F)")
    parser.add_argument("--plazo-logico", type=float, default=None, metavar="OPS",
                        help="Guillotina lógica: OPS operaciones (llamadas a control_vital) por ms de plazo, en vez de reloj")
    parser.add_argument("--verificar-determinismo", type=int, default=None, metavar="N",
                        help="Ejecuta dos veces los primeros N pasos con la misma configuración y falla si las decisiones difieren")
    args = parser.parse_args()
    if args.verificar_determinismo is not None:
        return verificar_determinismo(args)

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
        mecanismos=args.mecanismos,
        plazo_logico=args.plazo_logico,
        legado_salida=args.legado_salida,
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
