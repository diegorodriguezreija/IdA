"""Diagnóstico del paso 0: ¿cuántas veces gana una propuesta de baja urgencia a otra cuya necesidad está más apurada?

Una vida con semilla. En cada latido con más de un candidato de Acción, cuenta una **inversión** si algún
candidato que pierde viene de un impulso con intensidad ≥ ``--apuro`` y al menos ``--margen`` por encima de la
del impulso del ganador. Informa también del estrés medio y de los pares (impulso ganador → impulso apurado).

    python herramientas/diagnostico_intensidad.py --mundo crafter --semilla 31 --sin-estrategias-propias
    python herramientas/diagnostico_intensidad.py --mundo minimo --semilla 1 --latidos 400

Es un diagnóstico de una vida, no una medición (docs/PROPUESTA_PASO0.md, apartado a).
"""

import argparse
import os
import sys
import tempfile
from collections import Counter
from typing import Any, List, Tuple

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--mundo", default="crafter")
    p.add_argument("--semilla", type=int, default=31)
    p.add_argument("--latidos", type=int, default=1500)
    p.add_argument("--sin-estrategias-propias", action="store_true", help="solo Crafter: el suelo, sin estrategias del mundo")
    p.add_argument("--apuro", type=float, default=0.5, help="intensidad a partir de la cual una necesidad está apurada")
    p.add_argument("--margen", type=float, default=0.2, help="cuánto más apurada que la del ganador")
    p.add_argument("--mecanismos", nargs="*", default=[], help="interruptores de Perfil.mecanismos que se encienden (bloques E y F)")
    p.add_argument("--raiz", default=RAIZ, help="raíz del repositorio que se ejecuta (p. ej. un worktree de otro commit)")
    args = p.parse_args()
    sys.path.insert(0, args.raiz)
    from ida.nucleo.mundo import Registro
    from ida.ejecutor import ejecutar
    from ida.mundos import cargar

    if args.sin_estrategias_propias:
        original = cargar(args.mundo).registro   # sin estrategias propias, pero con su cuerpo (D10)
        cargar(args.mundo).registro = lambda self: Registro(cuerpo=original(self).cuerpo)
    if args.mecanismos:
        from dataclasses import replace
        clase = cargar(args.mundo)
        clase.perfil = replace(clase.perfil, mecanismos=replace(clase.perfil.mecanismos, **dict.fromkeys(args.mecanismos, True)))
    intenciones = set(cargar(args.mundo).perfil.intenciones)
    cuenta: Counter = Counter()
    pares: Counter = Counter()
    estres: List[float] = []
    ejemplos: List[Tuple[Any, ...]] = []

    def al(o: Any, onda: Any, r: Any) -> None:
        candidatos = list(onda.acc("Accion").values())
        dec = onda.ef("Decision").get("decision")
        if dec is None or not candidatos:
            return
        impulsos = {**onda.ef("Impulso"), **onda.ef("Intencion")}
        inten = {k: float(pz.carga.get("intensidad", 0.0)) for k, pz in impulsos.items()}
        estres.append(o.soma.estres)
        imp_g = dec.carga.get("origen", {}).get("impulso", "")
        i_g = inten.get(imp_g, 0.0)
        perdedores = {c.carga.get("origen", {}).get("impulso", "") for c in candidatos if c.id not in dec.entradas}
        if len(candidatos) > 1:
            cuenta["competencia"] += 1
        apurados = [(k, inten.get(k, 0.0)) for k in perdedores if k and k != imp_g
                    and inten.get(k, 0.0) >= args.apuro and inten.get(k, 0.0) >= i_g + args.margen]
        if any(k not in intenciones for k, _ in apurados):
            cuenta["inversion_necesidades"] += 1      # pierde una necesidad apurada (no una intención)
        if apurados:
            cuenta["inversion"] += 1
            k, v = max(apurados, key=lambda x: x[1])
            pares[(imp_g or "CORE", k)] += 1
            if len(ejemplos) < 4:
                ejemplos.append((r["latido"], imp_g, round(i_g, 2), str(r["motivo"])[:40], k, round(v, 2), round(o.soma.estres, 3)))

    opciones = {"vista": "oficial"} if args.mundo == "crafter" else {}
    with tempfile.TemporaryDirectory() as datos:
        res = ejecutar(args.mundo, latidos=args.latidos, semilla=args.semilla, consola=False, datos=datos, al_latir=al,
                       opciones_mundo=opciones)
    n = max(1, cuenta["competencia"])
    print(f"## {args.mundo} {'suelo' if args.sin_estrategias_propias else 'con estrategias'} semilla {args.semilla}: "
          f"{res[0]['latidos']} latidos; mecanismos: {', '.join(args.mecanismos) or 'ninguno'}")
    print(f"- latidos con más de un candidato: {cuenta['competencia']}")
    print(f"- gana un impulso menos apurado (perdedor ≥ {args.apuro} y ≥ ganador + {args.margen}): "
          f"{cuenta['inversion']} ({100 * cuenta['inversion'] / n:.1f} %)")
    print(f"- de ellas, con una necesidad apurada que pierde (sin contar intenciones): {cuenta['inversion_necesidades']} "
          f"({100 * cuenta['inversion_necesidades'] / n:.1f} %)")
    print(f"- estrés medio {sum(estres) / max(1, len(estres)):.3f}; latidos con estrés ≥ 0,3: {sum(e >= 0.3 for e in estres)}")
    print("- pares (impulso del ganador → impulso apurado que pierde):", pares.most_common(6))
    for e in ejemplos:
        print("  ejemplo (latido, impulso ganador, intensidad, motivo, impulso apurado, intensidad, estrés):", e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
