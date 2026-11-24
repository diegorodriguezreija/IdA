"""Diagnóstico de la deuda 14: por qué ``PerseguirMetas`` no propone ninguna meta en muchos latidos tras la mesa.

Ejecuta ``evaluar_crafter.evaluar`` (vista oficial, sin herencia, manual estricto, sin estrategias propias) y clasifica
cada latido desde la primera mesa de cada episodio en una sola causa, en este orden:

1. ``dormido``: no hubo cognición en el latido (dormía al empezarlo);
2. ``guillotina``: el latido se cortó antes de terminar S3;
3. ``estrategia no activa``: la Acción de S3 no llamó a ``PerseguirMetas`` (no hay estrategia activa para «progresar»);
4. ``sin plan``: la llamó y ninguna meta pendiente tiene plan (``_explorar_efectos``); se separa si había metas pendientes;
5. ``solo peticiones``: la llamó, no salió meta y propuso solo peticiones de otras estrategias (sin plan propio);
6. ``rechazada por amplitud``: propuso una meta, pero la pieza no llegó a los candidatos (``Onda.proponer`` sin amplitud);
7. ``propone meta``: hay un candidato «metas: …».

No cambia la conducta: las envolturas llaman a los métodos originales y devuelven lo mismo. Las semillas, una tras otra.

    python herramientas/diagnostico_sin_meta.py --pasos 3000 --semilla 31 --plazo-logico 40 --salida s31.json
    python herramientas/diagnostico_sin_meta.py --resumir s31.json s32.json s33.json
"""

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))

CAUSAS = ("dormido", "guillotina", "estrategia no activa", "sin plan (con metas pendientes)", "sin plan (sin metas pendientes)",
          "solo peticiones", "rechazada por amplitud", "propone meta")
VENTANA = 50


def ejecutar(args: argparse.Namespace) -> int:
    import evaluar_crafter as ev
    from ida.core import latido
    from ida.s3.reaccionar.estrategias import PerseguirMetas

    estado: Dict[str, Any] = {}
    filas: List[Dict[str, Any]] = []
    actuar_original = PerseguirMetas.actuar
    explorar_original = PerseguirMetas._explorar_efectos

    def actuar(self: Any, ctx: Any, estrategia: Any) -> Any:
        estado["llamada"] = True
        estado["explora"] = False
        res = actuar_original(self, ctx, estrategia)
        estado["propuestas"] = [(p.verbo.value, p.objetivo, p.motivo) for p in res]
        req = ctx.memoria.seccion("requisitos") if ctx.memoria.tiene_seccion("requisitos") else None
        metas = req.metas if req is not None else {}
        pendientes = sorted(m.objetivo for m in metas.values() if not m.conseguida and m.verbo in self.VERBOS_PLAN)
        estado["pendientes"] = len(pendientes)
        estado["metas_pendientes"] = pendientes
        estado["visibles"] = sorted({str(p.carga.get("clase", "")) for p in ctx.onda.ev("Exterocepcion").values()})
        mapa = ctx.memoria.seccion("cuadricula") if ctx.memoria.tiene_seccion("cuadricula") else None
        estado["mapa"] = sorted(set(mapa.casillas.values())) if mapa is not None else []
        return res

    def explorar(self: Any, ctx: Any) -> None:
        estado["explora"] = True
        explorar_original(self, ctx)

    PerseguirMetas.actuar = actuar                     # type: ignore[method-assign]
    PerseguirMetas._explorar_efectos = explorar        # type: ignore[method-assign]

    episodio = {"i": -1, "mesa": None}
    vivir_original = latido.Organismo.vivir

    def al_latir(org: Any, onda: Any) -> None:
        n = org.ciclo
        if episodio["mesa"] is None and "place_table" in org.mundo.logros():
            episodio["mesa"] = n
        if episodio["mesa"] is not None:
            acc = onda.reactiva.acc.get("Accion", {})
            metas = [p for p in acc.values() if str(p.carga.get("motivo", "")).startswith("metas:")]
            propuestas = estado.get("propuestas", []) if estado.get("llamada") else []
            de_meta = [p for p in propuestas if p[2].startswith("metas:")]
            if "restante" not in onda.notas:      # sin cognición en este latido (dormía al empezarlo)
                causa = "dormido"
            elif onda.guillotina:
                causa = "guillotina"
            elif not estado.get("llamada"):
                causa = "estrategia no activa"
            elif metas:
                causa = "propone meta"
            elif de_meta:
                causa = "rechazada por amplitud"
            elif estado.get("explora"):
                causa = "sin plan (con metas pendientes)" if estado.get("pendientes") else "sin plan (sin metas pendientes)"
            else:
                causa = "solo peticiones"
            activas = (onda.notas.get("estrategias_S3") or {}).get("activas", [])
            consumo = onda.consumo.get("S3", {})
            filas.append({"ep": episodio["i"], "k": n - episodio["mesa"], "causa": causa, "activas_s3": activas,
                          "amplitud_agotada": bool(onda.amplitud_agotada), "rechazos_s3": int(consumo.get("rechazos_amplitud", 0)),
                          "amplitud_max": int(onda.amplitud_max),
                          "consumo": {k: int(v.get("amplitud", 0)) for k, v in onda.consumo.items()},
                          "rechazos": {k: int(v.get("rechazos_amplitud", 0)) for k, v in onda.consumo.items() if v.get("rechazos_amplitud")},
                          "percibidas": len(onda.reactiva.ev.get("Exterocepcion", {})),
                          "metas_pendientes": estado.get("metas_pendientes", []), "visibles": estado.get("visibles", []),
                          "mapa": estado.get("mapa", []),
                          "peligro": round(float(org.soma.indicadores.get("peligro", 0.0)), 2),
                          "luz": round(float(org.mundo.env._world.daylight), 2)})
        estado.clear()

    def vivir(self: Any, max_latidos: int, al_latir_externo: Any = None) -> int:
        episodio["i"] += 1
        episodio["mesa"] = None
        return vivir_original(self, max_latidos, al_latir=al_latir)

    latido.Organismo.vivir = vivir   # type: ignore[method-assign,assignment]
    res = ev.evaluar(args.pasos, args.semilla, vista="oficial", sin_herencia=True, quiet=True, manual="estricto",
                     sin_estrategias_propias=True, plazo_logico=args.plazo_logico, mecanismos=args.mecanismos or None)
    datos = {"semilla": args.semilla, "pasos": args.pasos, "score": res["score"], "episodios": res["episodios"],
             "mecanismos": sorted(args.mecanismos or []),
             "latidos_cortados": res["latidos_cortados"], "filas": filas}
    os.makedirs(os.path.dirname(os.path.abspath(args.salida)), exist_ok=True)
    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)
    print(f"semilla {args.semilla}: {res['episodios']} episodios, score {res['score']}, {len(filas)} latidos tras la mesa → {args.salida}")
    return 0


def _pct(a: int, b: int) -> str:
    return f"{a} ({100 * a / b:.1f} %)".replace(".", ",") if b else "0"


def resumir(rutas: List[str]) -> int:
    corridas = [json.load(open(r, encoding="utf-8")) for r in rutas]
    print(f"Semillas {', '.join(str(c['semilla']) for c in corridas)} · {', '.join(str(c['pasos']) for c in corridas)} pasos · "
          f"episodios {', '.join(str(c['episodios']) for c in corridas)} · score {', '.join(str(c['score']) for c in corridas)} · "
          f"latidos cortados {sum(c['latidos_cortados'] for c in corridas)} · "
          f"mecanismos: {', '.join(corridas[0].get('mecanismos') or []) or 'ninguno'}\n")
    for titulo, filtro in ((f"Los {VENTANA} latidos tras la primera mesa", lambda f: 1 <= f["k"] <= VENTANA),
                           ("Todos los latidos desde la primera mesa", lambda f: f["k"] >= 1)):
        filas = [f for c in corridas for f in c["filas"] if filtro(f)]
        cuenta = Counter(f["causa"] for f in filas)
        print(f"### {titulo} ({len(filas)} latidos)\n")
        print("| Causa | " + " | ".join(f"Semilla {c['semilla']}" for c in corridas) + " | Total |")
        print("|---|" + "---|" * (len(corridas) + 1))
        for causa in CAUSAS:
            por = [sum(1 for f in c["filas"] if filtro(f) and f["causa"] == causa) for c in corridas]
            tot = [sum(1 for f in c["filas"] if filtro(f)) for c in corridas]
            print(f"| {causa} | " + " | ".join(_pct(x, t) for x, t in zip(por, tot, strict=True)) + f" | {_pct(cuenta[causa], len(filas))} |")
        sin = [f for f in filas if f["causa"] != "propone meta"]
        print(f"\nLatidos sin meta: {_pct(len(sin), len(filas))}. Con la amplitud agotada en el latido: "
              f"{_pct(sum(f['amplitud_agotada'] for f in sin), len(sin))}; con algún rechazo por amplitud en S3: "
              f"{_pct(sum(f['rechazos_s3'] > 0 for f in sin), len(sin))}.\n")
        print("| Causa | Latidos | Amplitud agotada | Peligro (mediana) | Entidades percibidas (mediana) | Amplitud máx. (mediana) | "
              "Consumo de amplitud S1 / S2 / S3 (medianas) |\n|---|---|---|---|---|---|---|")
        for causa in CAUSAS:
            g = [f for f in filas if f["causa"] == causa]
            if not g or causa == "dormido":
                continue
            med = lambda xs: sorted(xs)[len(xs) // 2]  # noqa: E731
            cons = " / ".join(str(med([f["consumo"].get(k, 0) for f in g])) for k in ("S1", "S2", "S3"))
            print(f"| {causa} | {len(g)} | {_pct(sum(f['amplitud_agotada'] for f in g), len(g))} | {med([f['peligro'] for f in g]):.2f} | "
                  f"{med([f['percibidas'] for f in g])} | {med([f['amplitud_max'] for f in g])} | {cons} |".replace(".", ","))
        print()
        no_activa = [f for f in filas if f["causa"] == "estrategia no activa"]
        if no_activa:
            print("Estrategias activas de S3 cuando `perseguir_metas` no lo está:\n")
            print("| Activas en S3 | Latidos |\n|---|---|")
            for k, n in Counter(", ".join(sorted(f["activas_s3"])) or "ninguna" for f in no_activa).most_common(8):
                print(f"| {k} | {_pct(n, len(no_activa))} |")
            peligro = sorted(f["peligro"] for f in no_activa)
            print(f"\nPeligro (indicador del soma) en esos latidos: mediana {peligro[len(peligro) // 2]:.2f}; "
                  f"luz < 0,3 en {_pct(sum(f['luz'] < 0.3 for f in no_activa), len(no_activa))}.\n".replace(".", ",", 1))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--pasos", type=int, default=3000)
    p.add_argument("--semilla", type=int, default=31)
    p.add_argument("--plazo-logico", type=float, default=None, metavar="OPS")
    p.add_argument("--mecanismos", nargs="*", default=[], help="interruptores de Perfil.mecanismos que se encienden")
    p.add_argument("--salida", default="diagnostico_sin_meta.json")
    p.add_argument("--resumir", nargs="*", default=None)
    args = p.parse_args()
    if args.resumir:
        return resumir(args.resumir)
    return ejecutar(args)


if __name__ == "__main__":
    raise SystemExit(main())
