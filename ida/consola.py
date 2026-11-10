"""Salida legible en consola: una línea por latido y, debajo, lo que la experiencia aportó."""

from typing import Any, Dict, List, cast

from ida.core.latido import Organismo
from ida.core.onda import Onda


def resumen_latido(org: Organismo, onda: Onda) -> Dict[str, Any]:
    """Resumen de un latido para la consola y la telemetría."""
    soma = org.soma
    ej = onda.reactiva.ef.get("Ejecucion", {}).get("Ejecucion")
    propuestas: Dict[str, List[str]] = {}
    for e in cast(List[Dict[str, Any]], onda.notas.get("evaluados", [])):
        propuestas.setdefault(e["sistema"], []).append(f"{e['verbo']} {e['objetivo']} ({e['total']:.2f})")
    return {
        "latido": onda.ciclo,
        "ms": onda.notas.get("ms_cognicion", 0.0),
        "plazo_ms": round(onda.frecuencia_ms, 1),
        "amplitud": [onda.amplitud_consumida, onda.amplitud_max],
        "guillotina": onda.motivo_guillotina if onda.guillotina else "",
        "soma": soma.valores(),
        "afecto": soma.afecto.value,
        "indicadores": dict(soma.indicadores),
        "cargando": soma.cargando,
        "propuestas": propuestas,
        "evaluados": onda.notas.get("evaluados", []),
        "decision": {
            "verbo": ej.carga["verbo"].value if ej else "",
            "objetivo": ej.carga["objetivo"] if ej else "",
            "sistema": ej.carga.get("sistema", "") if ej else "",
            "exito": ej.carga.get("exito") if ej else None,
            "mensaje": ej.carga.get("mensaje", "") if ej else "",
        },
        "motivo": ej.carga.get("motivo", "") if ej else "",
        "experiencia": {
            "aprendizaje": onda.notas.get("aprendizaje", []),
            "expectativa": onda.notas.get("expectativa", ""),
            "cambio_decision": bool(onda.notas.get("experiencia_cambio")),
            "episodio": onda.notas.get("episodio", ""),
        },
        "conteo_ev": {k: len(v) for k, v in onda.reactiva.ev.items()},
        "tiempos_ms": {k: round(v, 2) for k, v in sorted(onda.tiempos_ms.items(), key=lambda kv: -kv[1])[:6]},
    }


def linea(r: Dict[str, Any]) -> str:
    s = r["soma"]
    d = r["decision"]
    cabecera = (
        f"L{r['latido']:04d} [{r['ms']:5.1f}/{r['plazo_ms']:.0f}ms A{r['amplitud'][0]:>3}/{r['amplitud'][1]:<3}] "
        f"vit {s['vitalidad']:5.1f} ali {s['alimentacion']:5.1f} ene {s['energia']:5.1f} | {r['afecto']:<10} | "
        f"⇒ {d['verbo']} {d['objetivo']} ({d['sistema']})"
    )
    if r["motivo"]:
        cabecera += f" «{r['motivo']}»"
    if d["exito"] is False:
        cabecera += " ✗"
    if r["guillotina"]:
        cabecera += f" ✂ {r['guillotina']}"
    extra = []
    exp = r["experiencia"]
    for t in exp["aprendizaje"]:
        extra.append(f"      · experiencia: {t}")
    if exp["cambio_decision"]:
        extra.append("      · la experiencia cambió la decisión")
    if exp["expectativa"]:
        extra.append(f"      · proactiva: {exp['expectativa']}")
    if exp["episodio"]:
        extra.append(f"      · {exp['episodio']}")
    return "\n".join([cabecera, *extra])
