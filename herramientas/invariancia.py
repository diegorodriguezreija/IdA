"""Comprueba que un cambio no altera la conducta de IdA con semilla.

Ejecuta minimo, archivos, crafter y ajedrez con las semillas 1 a 3 y 400 latidos (una vida por
semilla, directorio de datos limpio) y registra en cada latido la decisión (verbo y objetivo), las
constantes vitales y la amplitud consumida, y al final la puntuación.

    python herramientas/invariancia.py --referencia   # guarda la referencia (antes de cambiar nada)
    python herramientas/invariancia.py                # compara: "OK" o el primer latido distinto

Las etiquetas (nombres de componentes y canales) no se comparan, porque los renombres las cambian.

La guillotina por plazo mira el reloj de pared (``Onda.control_vital``), así que una vida podría
variar con la carga de la máquina. Para comparar conducta, la herramienta congela el reloj de la
Onda: el plazo no corta nunca y la guillotina por amplitud sigue igual. No modifica ``ida/``.
"""

import argparse
import json
import os
import sys
import tempfile
from typing import Any, Dict, List, Optional

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from ida.nucleo.onda import Onda  # noqa: E402
from ida.ejecutor import ejecutar  # noqa: E402

MUNDOS = ("minimo", "archivos", "crafter", "ajedrez")
SEMILLAS = (1, 2, 3)
LATIDOS = 400
REFERENCIA = os.path.join(RAIZ, "datos", "invariancia", "referencia.json")
DECIMALES = 9


def _apagar_mecanismos(mundos, activos=()) -> None:
    """La invariancia compara con base-v2.0: todos los mecanismos (bloques E y F) apagados, salvo
    los que se pidan con ``--mecanismos`` (p. ej. ``buffer``)."""
    from dataclasses import replace

    from ida.nucleo.mundo import MecanismosMemoria
    from ida.mundos import cargar

    for m in mundos:
        clase = cargar(m)
        clase.perfil = replace(clase.perfil, mecanismos=MecanismosMemoria(**dict.fromkeys(activos, True)))


def _congelar_reloj() -> None:
    """Sustituye el reloj por defecto de la Onda por uno fijo (solo en este proceso)."""
    defectos = list(Onda.__init__.__defaults__ or ())
    defectos[-1] = lambda: 0.0          # último parámetro: ``reloj``
    Onda.__init__.__defaults__ = tuple(defectos)


def _redondear(valores: Dict[str, Any]) -> Dict[str, Any]:
    return {k: round(v, DECIMALES) if isinstance(v, float) else v for k, v in sorted(valores.items())}


def vida(mundo: str, semilla: int) -> Dict[str, Any]:
    latidos: List[List[Any]] = []

    def al_latir(_o: Any, _onda: Any, r: Dict[str, Any]) -> None:
        d = r["decision"]
        latidos.append([r["latido"], d["verbo"], d["objetivo"], _redondear(r["soma"]), r["amplitud"][0]])

    with tempfile.TemporaryDirectory(prefix=f"ida_inv_{mundo}_{semilla}_") as datos:
        resumenes = ejecutar(mundo, latidos=LATIDOS, semilla=semilla, generaciones=1, tabula_rasa=True,
                             consola=False, datos=datos, al_latir=al_latir)
    puntuacion = resumenes[0]["puntuacion"] if resumenes else None
    return {"latidos": latidos, "puntuacion": json.loads(json.dumps(puntuacion, default=str))}


def primera_diferencia(ref: Dict[str, Any], act: Dict[str, Any]) -> Optional[str]:
    campos = ("latido", "decisión", "objetivo", "vitales", "amplitud")
    for a, b in zip(ref["latidos"], act["latidos"], strict=False):   # la duración se compara después
        for i, campo in enumerate(campos):
            if a[i] != b[i]:
                return f"latido {a[0]}: {campo} {a[i]!r} -> {b[i]!r}"
    if len(ref["latidos"]) != len(act["latidos"]):
        return f"duración {len(ref['latidos'])} -> {len(act['latidos'])} latidos"
    if ref["puntuacion"] != act["puntuacion"]:
        return f"puntuación {ref['puntuacion']!r} -> {act['puntuacion']!r}"
    return None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--referencia", action="store_true", help="guarda la referencia en lugar de comparar")
    p.add_argument("--mundos", nargs="*", default=list(MUNDOS))
    p.add_argument("--mecanismos", nargs="*", default=[], help="interruptores de Perfil.mecanismos que se encienden (por defecto, ninguno)")
    args = p.parse_args()
    _congelar_reloj()
    _apagar_mecanismos(args.mundos, args.mecanismos)

    actual = {f"{m}:{s}": vida(m, s) for m in args.mundos for s in SEMILLAS}
    if args.referencia:
        os.makedirs(os.path.dirname(REFERENCIA), exist_ok=True)
        with open(REFERENCIA, "w", encoding="utf-8") as f:
            json.dump(actual, f)
        for clave, v in actual.items():
            print(f"{clave}: referencia guardada ({len(v['latidos'])} latidos, puntuación {v['puntuacion']})")
        return 0

    with open(REFERENCIA, encoding="utf-8") as f:
        referencia = json.load(f)
    fallos = 0
    for m in args.mundos:
        diferencias = []
        for s in SEMILLAS:
            clave = f"{m}:{s}"
            d = primera_diferencia(referencia[clave], json.loads(json.dumps(actual[clave])))
            if d:
                diferencias.append(f"semilla {s}, {d}")
        fallos += bool(diferencias)
        print(f"{m}: " + ("OK" if not diferencias else " | ".join(diferencias)))
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
