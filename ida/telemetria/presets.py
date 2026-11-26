"""Presets de carácter de la antesala (``GET /api/v1/presets``).

Son los de ``antesala.html`` (``CONFIG_OPTIMA`` y ``PRESETS_ARQUETIPO``), con nombre y descripción en es/en. «Recomendado»
depende del mundo (``por_mundo``); «Azar» no fija rasgos (``arquetipo: None``): los deriva la semilla, como
``Arquetipo.nuevo``. Los rangos de los deslizadores son los de la antesala de siempre.
"""

from typing import Any, Dict, List, Mapping, Optional

RASGOS = ("apertura", "responsabilidad", "neuroticismo", "extraversion", "umbral_miedo")

RANGOS: Dict[str, Dict[str, float]] = {
    "apertura": {"min": 0.15, "max": 0.85, "paso": 0.05},
    "responsabilidad": {"min": 0.15, "max": 0.85, "paso": 0.05},
    "neuroticismo": {"min": 0.15, "max": 0.85, "paso": 0.05},
    "extraversion": {"min": 0.15, "max": 0.85, "paso": 0.05},
    "umbral_miedo": {"min": 0.45, "max": 0.75, "paso": 0.05},
}

OPTIMO_POR_MUNDO: Dict[str, Dict[str, float]] = {
    "minimo": {"apertura": 0.50, "responsabilidad": 0.65, "neuroticismo": 0.60, "extraversion": 0.40, "umbral_miedo": 0.50},
    "archivos": {"apertura": 0.45, "responsabilidad": 0.70, "neuroticismo": 0.55, "extraversion": 0.35, "umbral_miedo": 0.55},
    # Crafter: el arquetipo de la medición oficial (perfil Equilibrado de herramientas/evaluar_crafter.py), O8.
    # El de la antesala antigua (0.55/0.70/0.45/0.30/0.65) está sin medir: PENDIENTES V4.
    "crafter": {"apertura": 0.50, "responsabilidad": 0.50, "neuroticismo": 0.50, "extraversion": 0.50, "umbral_miedo": 0.60},
    "ajedrez": {"apertura": 0.40, "responsabilidad": 0.75, "neuroticismo": 0.35, "extraversion": 0.30, "umbral_miedo": 0.70},
    "snake": {"apertura": 0.45, "responsabilidad": 0.65, "neuroticismo": 0.60, "extraversion": 0.30, "umbral_miedo": 0.50},
}

PRESETS: List[Dict[str, Any]] = [
    {
        "id": "optimo",
        "icono": "⭐",
        "nombre": {"es": "Recomendado", "en": "Recommended"},
        "descripcion": {"es": "El carácter con el que se mide IdA en este mundo (en Crafter, el de la medición oficial).",
                        "en": "The character IdA is measured with in this world (in Crafter, the official benchmark one)."},
        "arquetipo": None,
        "por_mundo": OPTIMO_POR_MUNDO,
    },
    {
        "id": "cauto",
        "icono": "🛡️",
        "nombre": {"es": "Cauto", "en": "Cautious"},
        "descripcion": {"es": "Superviviente: prudente, alerta y con aversión al riesgo.",
                        "en": "Survivor: prudent, alert and risk-averse."},
        "arquetipo": {"apertura": 0.35, "responsabilidad": 0.75, "neuroticismo": 0.70, "extraversion": 0.30, "umbral_miedo": 0.48},
    },
    {
        "id": "audaz",
        "icono": "🧭",
        "nombre": {"es": "Audaz", "en": "Bold"},
        "descripcion": {"es": "Explorador: curioso, tolera el peligro y busca lo nuevo.",
                        "en": "Explorer: curious, tolerates danger and seeks novelty."},
        "arquetipo": {"apertura": 0.75, "responsabilidad": 0.40, "neuroticismo": 0.35, "extraversion": 0.60, "umbral_miedo": 0.70},
    },
    {
        "id": "equilibrado",
        "icono": "⚖️",
        "nombre": {"es": "Equilibrado", "en": "Balanced"},
        "descripcion": {"es": "Rasgos neutrales, en el punto medio.",
                        "en": "Neutral traits, right in the middle."},
        "arquetipo": {"apertura": 0.50, "responsabilidad": 0.50, "neuroticismo": 0.50, "extraversion": 0.50, "umbral_miedo": 0.60},
    },
    {
        "id": "azar",
        "icono": "🎲",
        "nombre": {"es": "Al azar", "en": "Random"},
        "descripcion": {"es": "Lo deriva la semilla: cada semilla, un carácter distinto.",
                        "en": "Derived from the seed: each seed, a different character."},
        "arquetipo": None,
    },
]

PRESETS_POR_ID = {p["id"]: p for p in PRESETS}


def arquetipo_de(preset: str, mundo: str) -> Optional[Dict[str, float]]:
    """Los rasgos de un preset en un mundo (``None`` para «azar»). ``KeyError`` si el preset no existe."""
    p = PRESETS_POR_ID[preset]
    if p["id"] == "optimo":
        return dict(OPTIMO_POR_MUNDO.get(mundo, PRESETS_POR_ID["equilibrado"]["arquetipo"]))
    return dict(p["arquetipo"]) if p["arquetipo"] is not None else None


def validar_arquetipo(arq: Any) -> Dict[str, float]:
    """Los cinco rasgos, comprobados (números en [0, 1]); ``ValueError`` con un mensaje claro si no."""
    if not isinstance(arq, Mapping):
        raise ValueError("el carácter debe ser un objeto con los cinco rasgos")
    salida: Dict[str, float] = {}
    for r in RASGOS:
        v = arq.get(r)
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError(f"rasgo {r!r}: falta o no es un número")
        if not 0.0 <= float(v) <= 1.0:
            raise ValueError(f"rasgo {r!r}: {v} fuera de [0, 1]")
        salida[r] = float(v)
    return salida


def respuesta() -> Dict[str, Any]:
    return {"presets": PRESETS, "rasgos": list(RASGOS), "rangos": RANGOS}
