"""Esquema del registro del latido, versión 1 (O2, O4, O5), y su validador con la biblioteca estándar.

El registro lo produce ``ida.telemetria.observador.Observador`` al final de cada latido. Tiene tres niveles; cada
uno incluye al anterior:

- ``vital``: ritmo, cuerpo, química, afecto, necesidades, acción, puntuación y logros, hechos, experiencia (las frases de
  la consola de siempre), memoria (recuentos), contadores, arquetipo y vista de texto.
- ``cognitivo``: la Onda (canales, piezas de ``ev`` y ``acc`` con su autoría, flujo, consumo), el Tribunal con sus
  candidatos, las estrategias y lo que se sabe (las 20 proposiciones de más confianza).
- ``completo``: tiempos por Componente, fases del latido y todas las piezas de ``ef`` con su registro.

Las versiones futuras solo **añaden** campos: el validador de v1 acepta campos que no conoce. Quitar o renombrar un
campo exige ``v: 2`` y un conversor de las grabaciones antiguas.

Mini-lenguaje de tipos de ``ESQUEMA``: ``"int"``, ``"num"`` (entero o real, no booleano), ``"str"``, ``"bool"``,
``"any"``; ``("opt", T)`` (T o ``None``); ``("list", T)``; ``("map", T)`` (claves de texto, valores T); un ``dict`` es
un objeto con esos campos, y un campo que empieza por ``?`` es opcional.
"""

from typing import Any, Dict, List, Tuple

VERSION = 1
NIVELES = ("vital", "cognitivo", "completo")

# Campos que dependen del reloj de pared (o, con plazo lógico, de las operaciones): no cuentan al comparar grabaciones.
CAMPOS_TIEMPO = ("ritmo.ms", "ritmo.ms_total", "tiempos_ms", "fases")

_PIEZA_COGNITIVA = {"id": "str", "canal": "str", "fase": "str", "tipo": "str", "arousal": "num", "confianza": "num",
                    "origen": "str", "sistema": "str"}

ESQUEMA: Dict[str, Dict[str, Any]] = {
    "base": {
        "v": "int", "nivel": "str", "latido": "int", "vida": "int", "generacion": "int", "individuo": "str",
        "mundo": "str", "con_experiencia": "bool",
    },
    "vital": {
        "ritmo": {"ms": "num", "ms_total": "num", "plazo_ms": "num", "amplitud": ("list", "int"), "potencia": ("list", "num"),
                  "guillotina": "str", "logico": "bool"},
        "cuerpo": {"vitalidad": "num", "alimentacion": "num", "energia": "num", "descanso": "num", "dormido": "bool",
                   "cargando": ("opt", "str"), "vivo": "bool"},
        "quimica": {"dopamina": "num", "placer": "num", "estres": "num"},
        "afecto": {"estado": "str", "valencia": "num", "indicadores": ("map", "num")},
        "necesidades": ("list", {"nombre": "str", "deficit": "num"}),
        "accion": ("opt", {"verbo": "str", "objetivo": "str", "clase": "str", "sistema": "str", "exito": ("opt", "bool"),
                           "mensaje": "str", "motivo": "str", "?estrategia": ("opt", "str")}),
        "score": {"puntuacion": ("map", "any"), "logros": ("list", "str")},
        "hechos": ("list", {"tipo": "str"}),
        "experiencia": {"aprendizaje": ("list", "str"), "expectativa": "str", "cambio_decision": "bool", "episodio": "str"},
        "memoria": {"aciertos": "int", "sorpresas": "int", "episodios": "int", "demostradas": "int", "hipotesis": "int",
                    "refutadas": "int", "recuerdos": "int", "heredados": "int"},
        "contadores": ("map", "int"),
        "arquetipo": ("map", "num"),
        "vista": "str",
    },
    "cognitivo": {
        "onda": {
            "canales": ("map", {"ev": "int", "acc": "int", "ef": "int"}),
            "piezas": ("list", _PIEZA_COGNITIVA),
            "flujo": ("list", {"pieza": "str", "de": "str", "a": "str", "op": "str"}),
            "consumo": ("map", ("map", "num")),
            "restante": ("map", ("list", "num")),
            "operaciones": "int",
            "guillotina": "bool",
            "excepciones": ("map", "int"),
        },
        "tribunal": {
            "ganador": ("opt", {"id": "str", "sistema": "str"}),
            "candidatos": ("list", {"id": "str", "sistema": "str", "verbo": "str", "objetivo": "str", "motivo": "str",
                                    "base": "num", "activa": "num", "proactiva": "num", "plus": "num", "total": "num"}),
            "cambio_experiencia": "bool",
            "plus_decide": "bool",
        },
        "estrategias": {
            "activas": ("list", {"id": "str", "sistema": "str", "nombre": "str"}),
            "por_sistema": ("map", ("map", "any")),
        },
        "saber": ("list", {"sujeto": "str", "relacion": "str", "estado": "str", "confianza": "num", "heredada": "bool",
                           "autoridad": "bool"}),
    },
    "completo": {
        "tiempos_ms": ("map", "num"),
        "fases": ("list", ("list", "any")),
        "piezas": ("list", {**_PIEZA_COGNITIVA, "creada": "int", "actualizada": "int", "entradas": ("list", "any"),
                            "carga": ("map", "any"), "registro": ("list", ("map", "any"))}),
    },
}

# Catálogo de hechos v1 (O5): tipo -> parámetros obligatorios (con su tipo). Pueden llevar más parámetros.
HECHOS: Dict[str, Dict[str, Any]] = {
    "nace": {"individuo": "str", "generacion": "int", "heredados": "int"},
    "primera_vez": {"verbo": "str", "clase": "str"},
    "aprende": {"saber": "str", "clase": "str", "fuente": "str", "confianza": "num"},
    "duda": {"clase": "str", "relacion": "str", "confianza": "num"},
    "refuta": {"clase": "str", "relacion": "str", "confianza": "num"},
    "sorpresa": {"origen": "str", "clase": "str"},
    "logro": {"nombre": "str"},
    "peligro": {"clase": "str", "estado": "str", "dano": ("opt", "num"), "confianza": "num"},
    "estrategia": {"sistema": "str", "nombre": "str", "cambio": "str"},
    "duerme": {},
    "despierta": {"motivo": "str"},
    "muere": {"causa": "str", "latidos": "int", "puntuacion": ("map", "any")},
}

# Parámetros obligatorios según la variante de ``aprende`` (``saber``).
APRENDE: Dict[str, Dict[str, Any]] = {
    "proposicion": {"relacion": "str", "estado": "str"},
    "requisito": {"verbo": "str", "requiere": ("map", "any"), "cerca": ("list", "str"), "efecto": ("map", "any"),
                  "confirmado": "bool"},
}


def _tipo(valor: Any, spec: Any, ruta: str, errores: List[str]) -> None:
    if isinstance(spec, str):
        ok = {
            "int": isinstance(valor, int) and not isinstance(valor, bool),
            "num": isinstance(valor, (int, float)) and not isinstance(valor, bool),
            "str": isinstance(valor, str),
            "bool": isinstance(valor, bool),
            "any": True,
        }[spec]
        if not ok:
            errores.append(f"{ruta}: se esperaba {spec}, hay {type(valor).__name__}")
    elif isinstance(spec, tuple):
        clase, interno = spec
        if clase == "opt":
            if valor is not None:
                _tipo(valor, interno, ruta, errores)
        elif clase == "list":
            if not isinstance(valor, list):
                errores.append(f"{ruta}: se esperaba una lista, hay {type(valor).__name__}")
                return
            for i, v in enumerate(valor):
                _tipo(v, interno, f"{ruta}[{i}]", errores)
        elif clase == "map":
            if not isinstance(valor, dict):
                errores.append(f"{ruta}: se esperaba un objeto, hay {type(valor).__name__}")
                return
            for k, v in valor.items():
                if not isinstance(k, str):
                    errores.append(f"{ruta}: clave no textual {k!r}")
                _tipo(v, interno, f"{ruta}.{k}", errores)
    elif isinstance(spec, dict):
        _objeto(valor, spec, ruta, errores)


def _objeto(valor: Any, campos: Dict[str, Any], ruta: str, errores: List[str]) -> None:
    if not isinstance(valor, dict):
        errores.append(f"{ruta or 'registro'}: se esperaba un objeto, hay {type(valor).__name__}")
        return
    for nombre, spec in campos.items():
        opcional = nombre.startswith("?")
        clave = nombre[1:] if opcional else nombre
        sub = f"{ruta}.{clave}" if ruta else clave
        if clave not in valor:
            if not opcional:
                errores.append(f"{sub}: falta")
            continue
        _tipo(valor[clave], spec, sub, errores)


def _hecho(h: Any, ruta: str, errores: List[str]) -> None:
    if not isinstance(h, dict) or not isinstance(h.get("tipo"), str):
        return   # ya lo señala el esquema
    tipo = h["tipo"]
    if tipo not in HECHOS:
        errores.append(f"{ruta}: tipo de hecho desconocido {tipo!r}")
        return
    _objeto(h, HECHOS[tipo], ruta, errores)
    if tipo == "aprende" and isinstance(h.get("saber"), str):
        if h["saber"] not in APRENDE:
            errores.append(f"{ruta}.saber: variante desconocida {h['saber']!r}")
        else:
            _objeto(h, APRENDE[h["saber"]], ruta, errores)


def niveles_de(nivel: str) -> Tuple[str, ...]:
    """Las partes del esquema que lleva un registro de ``nivel`` (cada nivel incluye al anterior)."""
    return ("base",) + NIVELES[: NIVELES.index(nivel) + 1]


def validar(registro: Any) -> List[str]:
    """Errores del registro frente al esquema v1 (lista vacía: válido)."""
    errores: List[str] = []
    if not isinstance(registro, dict):
        return [f"registro: se esperaba un objeto, hay {type(registro).__name__}"]
    if registro.get("v") != VERSION:
        errores.append(f"v: se esperaba {VERSION}, hay {registro.get('v')!r}")
    nivel = registro.get("nivel")
    if nivel not in NIVELES:
        errores.append(f"nivel: se esperaba uno de {NIVELES}, hay {nivel!r}")
        nivel = "vital"
    for parte in niveles_de(nivel):
        _objeto(registro, ESQUEMA[parte], "", errores)
    for i, h in enumerate(registro.get("hechos") or []):
        _hecho(h, f"hechos[{i}]", errores)
    return errores


def es_valido(registro: Any) -> bool:
    return not validar(registro)
