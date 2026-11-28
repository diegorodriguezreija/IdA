"""Diagnóstico de la deuda 14 en Crafter: la cadena de herramientas tras colocar la mesa.

Ejecuta ``evaluar_crafter.evaluar`` (vista oficial, sin herencia, manual estricto, con las estrategias del mundo) con un gancho
en cada latido. No cambia la conducta. Con ``--salida`` guarda un JSON por semilla; con ``--resumir`` junta varios.

Lo que mide (sección 2, 14.1, de ``docs/ENCARGO_DEUDA14_HERRAMIENTAS.md``), en los episodios con mesa y sin pico o sin
espada de madera al acabar:

1. **Madera en el inventario** en los latidos en que una mesa está al alcance (en el 3 × 3 del jugador, la regla de
   Crafter para fabricar), desde la primera mesa: distribución y cuántas veces había 0.
2. **La meta del planificador** en los 50 latidos siguientes a la primera mesa: la meta de la propuesta de
   ``PerseguirMetas`` («metas: X»; ninguna si no propone), y la distancia (Chebyshev) a la mesa más cercana.
3. **Quién gana el Tribunal** cuando la mesa está al alcance, hay madera ≥ 1, falta la herramienta y no se fabrica, y
   si ``PerseguirMetas`` proponía fabricarla (con su puesto entre los evaluados).
4. **Muertes antes de volver a la mesa:** episodios que mueren sin la herramienta, latidos entre la primera mesa y la
   muerte, si vuelven al alcance de una mesa después de alejarse y latidos desde la última vez al alcance.

Además, por semilla: Score, pico, espada, ``wake_up`` y muertes por zombi (tasas sobre todos los episodios).

    python herramientas/diagnostico_deuda14.py --pasos 10000 --semilla 31 --plazo-logico 40 --salida d31.json
    python herramientas/diagnostico_deuda14.py --resumir d31.json d32.json d33.json

La mesa y su distancia son las del mundo (``_mat_map``), no lo que cree IdA. Las semillas, **una tras otra**.
"""

import argparse
import json
import os
import statistics
import sys
import time
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))

HERRAMIENTAS = (("make_wood_pickaxe", "pico"), ("make_wood_sword", "espada"))
VENTANA = 50


def _motivo(texto: str) -> str:
    """La primera parte de un motivo (antes de «·» y de «←»)."""
    return texto.split("·")[0].split("←")[0].strip()[:60]


def _estrategia(carga: Dict[str, Any]) -> str:
    e = str(carga.get("origen", {}).get("estrategia", ""))
    return e.split(":")[1] if e.count(":") >= 1 else (e or str(carga.get("sistema", "")) or "ninguna")


def _meta(motivo: str) -> str:
    """La meta de una propuesta de ``PerseguirMetas`` («metas: X ← …» → X)."""
    return _motivo(motivo)[len("metas:"):].strip() if motivo.startswith("metas:") else ""


def _distancia_mesa(w: Any, pos: Tuple[int, int]) -> Optional[int]:
    """Distancia de Chebyshev a la mesa más cercana del mundo (None si no hay ninguna). ≤ 1 es «al alcance»."""
    import numpy as np
    ident = w._mat_ids.get("table")
    if ident is None:
        return None
    celdas = np.argwhere(w._mat_map == ident)
    if not len(celdas):
        return None
    return int(np.abs(celdas - np.array(pos)).max(axis=1).min())


class Episodio:
    def __init__(self, indice: int) -> None:
        self.indice = indice
        self.n = 0
        self.logros: Dict[str, int] = {}
        self.filas: List[List[Any]] = []    # desde la primera mesa: ver CAMPOS
        self.madera_al_colocar: Optional[int] = None
        self.causa: Optional[str] = None
        self.vivo = False
        self.guillotinas = 0
        self.ms_max = 0.0

    def latido(self, org: Any, onda: Any) -> None:
        self.n += 1
        n = self.n
        w, jug = org.mundo.env._world, org.mundo.jugador
        pos = (int(jug.pos[0]), int(jug.pos[1]))
        inv = {k: int(v) for k, v in jug.inventory.items()}
        self.ms_max = max(self.ms_max, float(onda.notas.get("ms_total", 0.0) or 0.0))
        nuevos = [x for x in org.mundo.logros() if x not in self.logros]
        for x in nuevos:
            self.logros[x] = n
        if "place_table" not in self.logros:
            return
        if self.madera_al_colocar is None:
            self.madera_al_colocar = inv.get("wood", 0)
        accion = onda.reactiva.ef.get("Accion", {}).get("Accion")
        carga = dict(accion.carga) if accion is not None else {}
        candidatos = list(onda.reactiva.acc.get("Accion", {}).values())
        evaluados = onda.notas.get("evaluados") or []
        meta, meta_puesto = "", None
        propone = {h: False for h, _ in HERRAMIENTAS}
        puesto = {h: None for h, _ in HERRAMIENTAS}
        for c in candidatos:
            motivo = str(c.carga.get("motivo", ""))
            m = _meta(motivo)
            if m:
                meta = m
                meta_puesto = next((i + 1 for i, e in enumerate(evaluados) if e.get("id") == c.id), 99)
            for h, _ in HERRAMIENTAS:
                if getattr(c.carga.get("verbo"), "value", "") == "USAR" and c.carga.get("objetivo") == h:
                    propone[h] = True
                    puesto[h] = next((i + 1 for i, e in enumerate(evaluados) if e.get("id") == c.id), 99)
        d = _distancia_mesa(w, pos)
        gana = f"{_estrategia(carga)} · {_motivo(str(carga.get('motivo', '')))}"
        ganador_total = float(evaluados[0]["total"]) if evaluados else 0.0
        self.filas.append([n - self.logros["place_table"], inv.get("wood", 0), d, meta, meta_puesto, gana, round(ganador_total, 3),
                           [h for h, _ in HERRAMIENTAS if h in self.logros], [h for h in nuevos if h.startswith("make_")],
                           [h for h, _ in HERRAMIENTAS if propone[h]], {h: puesto[h] for h, _ in HERRAMIENTAS if puesto[h]}])

    def resumen(self) -> Dict[str, Any]:
        return {"indice": self.indice, "latidos": self.n, "causa_muerte": self.causa, "vivo": self.vivo, "logros": self.logros,
                "madera_al_colocar": self.madera_al_colocar, "guillotinas": self.guillotinas, "ms_max": round(self.ms_max, 1),
                "filas": self.filas}


CAMPOS = ("k", "madera", "dist", "meta", "meta_puesto", "gana", "ganador_total", "hechas", "nuevas", "propone", "puesto")


def ejecutar(args: argparse.Namespace) -> int:
    import evaluar_crafter as ev
    from ida.core import latido

    eps: List[Episodio] = []
    vivir_original = latido.Organismo.vivir

    def vivir(self: Any, max_latidos: int, al_latir_externo: Any = None) -> int:
        eps.append(Episodio(len(eps)))
        r = vivir_original(self, max_latidos, al_latir=eps[-1].latido)
        eps[-1].vivo = bool(self.soma.esta_vivo)
        eps[-1].causa = self.causa_muerte if not self.soma.esta_vivo else None
        eps[-1].guillotinas = int(self.contadores.get("guillotinas", 0))
        return r

    latido.Organismo.vivir = vivir   # type: ignore[method-assign,assignment]
    t0 = time.perf_counter()
    # Con las estrategias del mundo: desde A6a, Recinto y SalirDelRecinto son de Crafter y «sin estrategias propias» ya no
    # es el suelo con que se escribió este diagnóstico. --pasos son latidos, como en sus datos (contabilidad anterior a P0).
    res = ev.evaluar(args.pasos, args.semilla, vista="oficial", sin_herencia=True, quiet=True, manual="estricto",
                     mecanismos=args.mecanismos or None, plazo_logico=args.plazo_logico, contar="latidos")
    datos = {"semilla": args.semilla, "pasos": args.pasos, "score": res["score"], "mecanismos": sorted(args.mecanismos or []),
             "plazo_logico": args.plazo_logico, "tiempo_segundos": round(time.perf_counter() - t0, 1),
             "tasas_logros": res["tasas_logros"], "causas_muerte": res["causas_muerte"], "campos": CAMPOS,
             "episodios": [e.resumen() for e in eps]}
    os.makedirs(os.path.dirname(os.path.abspath(args.salida)), exist_ok=True)
    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)
    print(f"semilla {args.semilla}: {len(eps)} episodios, score {res['score']}, {datos['tiempo_segundos']} s → {args.salida}")
    return 0


# ---------------------------------------------------------------------------
def _pct(a: float, b: float) -> str:
    return f"{a:.0f} ({100 * a / b:.1f} %)".replace(".", ",") if b else "0"


def _med(xs: List[float]) -> str:
    return f"{statistics.median(xs):.0f}" if xs else "—"


def _cuartiles(xs: List[float]) -> str:
    if len(xs) < 4:
        return "—"
    q = statistics.quantiles(xs, n=4)
    return f"{q[0]:.0f}-{q[2]:.0f}"


def _filas(e: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [dict(zip(CAMPOS, f, strict=True)) for f in e["filas"]]


def resumir(rutas: List[str]) -> int:
    corridas = [json.load(open(r, encoding="utf-8")) for r in rutas]
    eps = [e for c in corridas for e in c["episodios"]]
    print(f"Semillas {', '.join(str(c['semilla']) for c in corridas)} · {', '.join(str(c['pasos']) for c in corridas)} pasos · "
          f"mecanismos: {', '.join(corridas[0].get('mecanismos') or []) or 'ninguno'} · {len(eps)} episodios · "
          f"latidos cortados: {sum(e['guillotinas'] for e in eps)} · máximo de ms por latido (reloj): "
          f"{max(e['ms_max'] for e in eps):.1f} · tiempo: {', '.join(str(c['tiempo_segundos']) for c in corridas)} s\n")

    print("### Por semilla\n")
    print("| Semilla | Episodios | Score | Pico | Espada | `wake_up` | Muertes por zombi | Pasos por episodio |")
    print("|---|---|---|---|---|---|---|---|")
    for c in corridas:
        n = len(c["episodios"])
        t = c["tasas_logros"]
        z = c["causas_muerte"].get("zombi", 0)
        print(f"| {c['semilla']} | {n} | {c['score']:.2f} | {t['make_wood_pickaxe']:.2f} | {t['make_wood_sword']:.2f} | "
              f"{t['wake_up']:.2f} | {_pct(z, n)} | {statistics.mean(e['latidos'] for e in c['episodios']):.1f} |".replace(".", ","))

    mesa = [e for e in eps if "place_table" in e["logros"]]
    print(f"\nEpisodios con mesa: {_pct(len(mesa), len(eps))}. Madera justo después de la primera mesa: "
          f"{dict(sorted(Counter(e['madera_al_colocar'] for e in mesa).items()))}.\n")
    print("| Herramienta | Tras la mesa | Latidos desde la mesa: mediana (p25-p75) |\n|---|---|---|")
    for h, _ in HERRAMIENTAS:
        d = [e["logros"][h] - e["logros"]["place_table"] for e in mesa if h in e["logros"]]
        print(f"| {h} | {_pct(len(d), len(mesa))} | {_med(d)} ({_cuartiles(d)}) |")

    for h, nombre in HERRAMIENTAS:
        sin = [e for e in mesa if h not in e["logros"]]
        con = [e for e in mesa if h in e["logros"]]
        print(f"\n## Con mesa y sin {nombre} ({len(sin)} episodios)\n")

        # 1) madera con la mesa al alcance
        def madera_alcance(grupo: List[Dict[str, Any]], antes_de: Optional[str]) -> List[int]:
            xs = []
            for e in grupo:
                for f in _filas(e):
                    if antes_de and antes_de in f["hechas"]:
                        break
                    if f["dist"] is not None and f["dist"] <= 1:
                        xs.append(f["madera"])
            return xs
        xs = madera_alcance(sin, None)
        ys = madera_alcance(con, h)
        total_lat = sum(len(e["filas"]) for e in sin)
        print(f"**1. Madera con una mesa al alcance.** Latidos con la mesa al alcance: {_pct(len(xs), total_lat)} de los latidos "
              f"desde la mesa.\n")
        print("| Madera | Sin " + nombre + " (latidos) | Con " + nombre + ", antes de fabricarlo (latidos) |\n|---|---|---|")
        cx, cy = Counter(xs), Counter(ys)
        for k in sorted(set(cx) | set(cy)):
            print(f"| {k} | {_pct(cx[k], len(xs))} | {_pct(cy[k], len(ys))} |")
        ep_cero = sum(1 for e in sin if any(f["dist"] is not None and f["dist"] <= 1 for f in _filas(e))
                      and all(f["madera"] == 0 for f in _filas(e) if f["dist"] is not None and f["dist"] <= 1))
        ep_alcance = sum(1 for e in sin if any(f["dist"] is not None and f["dist"] <= 1 for f in _filas(e)))
        print(f"\nEpisodios sin {nombre} que tienen la mesa al alcance algún latido: {ep_alcance}; de ellos, con 0 de madera en "
              f"todos esos latidos: {ep_cero}.\n")

        # 2) meta y distancia en los 50 latidos siguientes
        metas: Counter = Counter()
        tramos: Dict[str, List[int]] = {"1-10": [], "11-25": [], "26-50": []}
        al_alcance: Dict[str, List[int]] = {k: [] for k in tramos}
        for e in sin:
            for f in _filas(e):
                if not 1 <= f["k"] <= VENTANA:
                    continue
                metas[f["meta"] or "(PerseguirMetas no propone meta)"] += 1
                tramo = "1-10" if f["k"] <= 10 else ("11-25" if f["k"] <= 25 else "26-50")
                if f["dist"] is not None:
                    tramos[tramo].append(f["dist"])
                    al_alcance[tramo].append(int(f["dist"] <= 1))
        tm = sum(metas.values())
        print(f"**2. Meta de PerseguirMetas en los {VENTANA} latidos tras la mesa** ({tm} latidos).\n")
        print("| Meta | Latidos |\n|---|---|")
        for m, k in metas.most_common(10):
            print(f"| {m} | {_pct(k, tm)} |")
        print("\n| Latidos tras la mesa | Distancia a la mesa: mediana (p25-p75) | Al alcance |\n|---|---|---|")
        for t in tramos:
            print(f"| {t} | {_med(tramos[t])} ({_cuartiles(tramos[t])}) | {_pct(sum(al_alcance[t]), len(al_alcance[t]))} |")
        muertos_ventana = sum(1 for e in sin if not e["vivo"] and len(e["filas"]) <= VENTANA)
        print(f"\nEpisodios que mueren dentro de la ventana: {muertos_ventana}.\n")

        # 3) quién gana con mesa, madera y sin fabricar
        gana: Counter = Counter()
        propone, puestos = 0, []
        for e in sin:
            for f in _filas(e):
                if f["dist"] is not None and f["dist"] <= 1 and f["madera"] >= 1 and h not in f["nuevas"]:
                    gana[f["gana"]] += 1
                    if h in f["propone"]:
                        propone += 1
                        puestos.append(f["puesto"][h])
        tg = sum(gana.values())
        print(f"**3. Quién gana con la mesa al alcance, madera ≥ 1 y sin fabricar** ({tg} latidos).\n")
        print("| Estrategia · motivo | Latidos |\n|---|---|")
        for m, k in gana.most_common(10):
            print(f"| {m} | {_pct(k, tg)} |")
        print(f"\nPerseguirMetas propone fabricar el {nombre} en {_pct(propone, tg)} de esos latidos; puesto entre los evaluados "
              f"(mediana): {_med(puestos)}.\n")

        # 4) muertes antes de volver a la mesa
        muertos = [e for e in sin if not e["vivo"]]
        hasta_muerte = [len(e["filas"]) for e in muertos]
        vuelven, nunca, desde_ultima = 0, 0, []
        for e in muertos:
            fs = _filas(e)
            alc = [f["dist"] is not None and f["dist"] <= 1 for f in fs]
            salio = next((i for i, a in enumerate(alc) if not a), None)
            volvio = salio is not None and any(alc[salio:])
            vuelven += int(volvio)
            nunca += int(salio is not None and not volvio)
            ultima = max((i for i, a in enumerate(alc) if a), default=None)
            desde_ultima.append(len(fs) - 1 - ultima if ultima is not None else len(fs))
        print(f"**4. Muertes.** Mueren sin el {nombre}: {_pct(len(muertos), len(sin))}; causas: "
              f"{dict(Counter(e['causa_muerte'] for e in muertos).most_common())}.\n")
        print(f"- Latidos entre la primera mesa y la muerte: mediana {_med(hasta_muerte)} ({_cuartiles(hasta_muerte)}).")
        print(f"- Se alejan de la mesa y no vuelven a tenerla al alcance antes de morir: {nunca}; vuelven al menos una vez: {vuelven}.")
        print(f"- Latidos desde la última vez con una mesa al alcance hasta la muerte: mediana {_med(desde_ultima)} "
              f"({_cuartiles(desde_ultima)}).")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--pasos", type=int, default=10000)
    p.add_argument("--semilla", type=int, default=31)
    p.add_argument("--mecanismos", nargs="*", default=[])
    p.add_argument("--plazo-logico", type=float, default=None, metavar="OPS")
    p.add_argument("--salida", default="diagnostico_deuda14.json")
    p.add_argument("--resumir", nargs="*", default=None)
    args = p.parse_args()
    if args.resumir:
        return resumir(args.resumir)
    return ejecutar(args)


if __name__ == "__main__":
    raise SystemExit(main())
