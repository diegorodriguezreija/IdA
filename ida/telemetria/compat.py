"""Capa de compatibilidad del registro del latido v1 con el resumen de antes (``panel.html``, ``antesala.html`` y
``otel.py``).

RETIRAR EN T6: cuando el Vivero y el Laboratorio sustituyan al panel y OTel se alimente del registro directamente (O15),
este módulo desaparece. Mientras tanto, ``a_panel`` rehace desde el registro el diccionario que el panel y OTel
esperaban, con las mismas claves. Lo que el nivel del registro no trae (los tiempos por Componente fuera del nivel
completo; la Onda, el Tribunal y lo que se sabe en el nivel vital) llega vacío.
"""

from typing import Any, Dict, List

from ida.nucleo.vocabulario import EstadoSaber, Relacion

_ESTADOS = {e.name.lower(): e.value for e in EstadoSaber}


def _texto_saber(p: Dict[str, Any]) -> str:
    """El texto de siempre de una proposición (``Proposicion.texto``) desde su forma estructurada."""
    origen = [o for o, si in (("heredada", p["heredada"]), ("autoridad", p["autoridad"])) if si]
    extra = f", {', '.join(origen)}" if origen else ""
    relacion = Relacion[p["relacion"]].value if p["relacion"] in Relacion.__members__ else p["relacion"]
    return f"«{p['sujeto']} {relacion}» ({_ESTADOS.get(p['estado'], p['estado'])}{extra}, {p['confianza']:.2f})"


def a_panel(r: Dict[str, Any]) -> Dict[str, Any]:
    """El resumen del latido con la forma de antes, desde un registro del latido v1. RETIRAR EN T6."""
    ritmo, accion = r["ritmo"], r["accion"] or {}
    tribunal = r.get("tribunal", {})
    candidatos: List[Dict[str, Any]] = tribunal.get("candidatos", [])
    propuestas: Dict[str, List[str]] = {}
    for e in candidatos:
        propuestas.setdefault(e["sistema"], []).append(f"{e['verbo']} {e['objetivo']} ({e['total']:.2f})")
    canales = r.get("onda", {}).get("canales", {})
    tiempos = r.get("tiempos_ms", {})
    return {
        "latido": r["latido"],
        "ms": ritmo["ms"],
        "plazo_ms": ritmo["plazo_ms"],
        "amplitud": list(ritmo["amplitud"]),
        "guillotina": ritmo["guillotina"],
        "soma": {k: r["cuerpo"][k] for k in ("vitalidad", "alimentacion", "energia", "descanso")} | dict(r["quimica"]),
        "afecto": r["afecto"]["estado"],
        "indicadores": dict(r["afecto"]["indicadores"]),
        "cargando": r["cuerpo"]["cargando"],
        "propuestas": propuestas,
        "evaluados": candidatos,
        "decision": {k: accion.get(k, "" if k != "exito" else None) for k in ("verbo", "objetivo", "sistema", "exito", "mensaje")},
        "motivo": accion.get("motivo", ""),
        "experiencia": dict(r["experiencia"]),
        "conteo_ev": {c: n["ev"] for c, n in canales.items() if n["ev"]},
        "tiempos_ms": {k: round(v, 2) for k, v in sorted(tiempos.items(), key=lambda kv: -kv[1])[:6]},
        "vista": r["vista"],
        "conocimiento": [_texto_saber(p) for p in r.get("saber", [])[:20]],
        "individuo": r["individuo"],
        "generacion": r["generacion"],
        "arquetipo": dict(r["arquetipo"]),
        "memoria": dict(r["memoria"]),
        "contadores": dict(r["contadores"]),
        "puntuacion": r["score"]["puntuacion"],
        "sin_experiencia": not r["con_experiencia"],
        "hechos": list(r["hechos"]),
    }
