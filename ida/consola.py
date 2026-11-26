"""Salida legible en consola: una línea por latido y, debajo, lo que la experiencia aportó.

Se forma desde el registro del latido v1 (O2, ``ida/telemetria/observador.py``): la consola no lee el organismo. La
salida es la de siempre, byte a byte.
"""

from typing import Any, Dict


def linea(r: Dict[str, Any]) -> str:
    """La línea de consola de un registro del latido (basta el nivel vital)."""
    ritmo, s, a = r["ritmo"], r["cuerpo"], r["accion"] or {}
    verbo, objetivo, sistema = a.get("verbo", ""), a.get("objetivo", ""), a.get("sistema", "")
    cabecera = (
        f"L{r['latido']:04d} [{ritmo['ms']:5.1f}/{ritmo['plazo_ms']:.0f}ms A{ritmo['amplitud'][0]:>3}/{ritmo['amplitud'][1]:<3}] "
        f"vit {s['vitalidad']:5.1f} ali {s['alimentacion']:5.1f} ene {s['energia']:5.1f} | {r['afecto']['estado']:<10} | "
        f"⇒ {verbo} {objetivo} ({sistema})"
    )
    if a.get("motivo"):
        cabecera += f" «{a['motivo']}»"
    if a.get("exito") is False:
        cabecera += " ✗"
    if ritmo["guillotina"]:
        cabecera += f" ✂ {ritmo['guillotina']}"
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


def imprimir_latido(r: Dict[str, Any], cada: int) -> bool:
    """Si el latido se imprime: uno de cada ``cada``, y siempre los que traen aprendizaje o guillotina."""
    return r["latido"] % cada == 0 or bool(r["experiencia"]["aprendizaje"]) or bool(r["ritmo"]["guillotina"])
