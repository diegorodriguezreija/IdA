"""Mide el consumo de atención por latido y por sistema, sin modificar ``ida/`` (paso B0).

Por cada latido despierto y cada sistema (S1, S2, S3) registra:
- ``piezas``: piezas nuevas en lo percibido (``ev``) o propuesto (``acc``), con o sin coste;
- ``coste``: amplitud consumida (lo que hoy cobra ``Onda.control_vital``);
- ``arousal``: suma del arousal otorgado a esas piezas nuevas;
- ``ajeno``: suma de |Δ arousal| en piezas de ``ev``/``acc`` de otro sistema que ya existían.
Y por latido: la amplitud máxima y si hubo guillotina (y por qué).

    python herramientas/consumo.py [--mundos minimo archivos crafter ajedrez] [--latidos 400]

Usa las semillas 1 a 3 y congela el reloj de la Onda como ``herramientas/invariancia.py``.
"""

import argparse
import os
import statistics
import sys
import tempfile
from collections import defaultdict
from typing import Any, Dict, List, Tuple

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from invariancia import _congelar_reloj  # noqa: E402

from ida.core.arquitectura import Sistema  # noqa: E402
from ida.ejecutor import ejecutar  # noqa: E402

SEMILLAS = (1, 2, 3)
METRICAS = ("piezas", "coste", "arousal", "ajeno")


def _foto(onda: Any) -> Dict[Tuple[str, str, str], Tuple[float, str]]:
    r = onda.reactiva
    return {(fase, canal, pid): (p.arousal, p.sistema)
            for fase, canales in (("ev", r.ev), ("acc", r.acc)) for canal, d in canales.items() for pid, p in d.items()}


MUESTRAS: Dict[str, List[Dict[str, float]]] = defaultdict(list)


def instrumentar() -> None:
    original = Sistema.latir

    def latir(self: Sistema, ctx: Any) -> None:
        onda = ctx.onda
        antes, coste0 = _foto(onda), onda.amplitud_consumida
        try:
            original(self, ctx)
        finally:
            despues = _foto(onda)
            nuevas = [despues[k][0] for k in despues if k not in antes]
            ajeno = sum(abs(despues[k][0] - a) for k, (a, sis) in antes.items() if k in despues and sis != self.nombre)
            MUESTRAS[self.nombre].append({"latido": (id(ctx.memoria), onda.ciclo), "piezas": len(nuevas),
                                          "coste": onda.amplitud_consumida - coste0, "arousal": sum(nuevas), "ajeno": ajeno})

    Sistema.latir = latir  # type: ignore[method-assign]


def percentil(xs: List[float], q: float) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))] if xs else 0.0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--mundos", nargs="*", default=["minimo", "archivos", "crafter", "ajedrez"])
    p.add_argument("--latidos", type=int, default=400)
    args = p.parse_args()
    _congelar_reloj()
    instrumentar()

    for mundo in args.mundos:
        MUESTRAS.clear()
        muestras = MUESTRAS
        amplitudes: List[int] = []
        guillotinas: Dict[str, int] = defaultdict(int)
        latidos = 0

        def al_latir(_o: Any, onda: Any, _r: Dict[str, Any]) -> None:
            nonlocal latidos
            latidos += 1
            amplitudes.append(onda.amplitud_max)  # noqa: B023 (se usa en la misma iteración)
            if onda.guillotina:
                guillotinas["amplitud" if "amplitud" in onda.motivo_guillotina else "plazo"] += 1  # noqa: B023

        for s in SEMILLAS:
            with tempfile.TemporaryDirectory(prefix=f"ida_consumo_{mundo}_{s}_") as datos:
                ejecutar(mundo, latidos=args.latidos, semilla=s, generaciones=1, tabula_rasa=True,
                         consola=False, datos=datos, al_latir=al_latir)
        print(f"== {mundo}: {latidos} latidos; amplitud máx. mediana {statistics.median(amplitudes):.0f} "
              f"(p5 {percentil(amplitudes, 0.05):.0f}, p95 {percentil(amplitudes, 0.95):.0f}); "
              f"guillotinas {dict(guillotinas)}")
        print(f"   {'sistema':<7} {'n':>5} " + " ".join(f"{m + ' med/p95':>16}" for m in METRICAS))
        for sis in sorted(muestras):
            filas = muestras[sis]
            celdas = " ".join(f"{statistics.median([f[m] for f in filas]):>7.2f}/{percentil([f[m] for f in filas], 0.95):<8.2f}"
                              for m in METRICAS)
            print(f"   {sis:<7} {len(filas):>5} {celdas}")
        por_latido: Dict[Any, Dict[str, float]] = defaultdict(lambda: dict.fromkeys(METRICAS, 0.0))
        for filas in muestras.values():
            for f in filas:
                for m in METRICAS:
                    por_latido[f["latido"]][m] += f[m]
        if por_latido:
            celdas = " ".join(f"{statistics.median([t[m] for t in por_latido.values()]):>7.2f}/"
                              f"{percentil([t[m] for t in por_latido.values()], 0.95):<8.2f}" for m in METRICAS)
            print(f"   {'total':<7} {len(por_latido):>5} {celdas}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
