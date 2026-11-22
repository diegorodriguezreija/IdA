"""Genera las tablas de resultados y comparativas de evaluación de Crafter.

Soporta tanto la medición de referencia oficial como la evaluación de Paso 5 y Paso 0.

``--pareada A.json B.json`` compara dos evaluaciones de la misma semilla base episodio a episodio: el episodio i
ocurre en el mismo mundo en las dos (su semilla solo depende de i), así que se emparejan los primeros min(n1, n2)
episodios y se da la diferencia de Score y de cada logro (A − B) con su IC 95 % por bootstrap pareado
(remuestreando índices de episodio). Necesita ``por_episodio`` en los JSON (``evaluar_crafter.py`` lo guarda desde
la deuda 13).

``--pareada-conjunta A1 B1 A2 B2 ...`` junta los episodios emparejados de varias semillas (cada par con su misma
semilla base): la Score y las tasas se calculan con todos juntos y el IC sale de un bootstrap pareado estratificado
por semilla (cada réplica remuestrea dentro de cada semilla tantos episodios como tiene).
"""

import argparse
import json
import math
import os
import random
import statistics
import sys
from typing import Any, Dict, List, Tuple

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS_DIR = os.path.join(RAIZ, "datos", "evaluacion")


def cortados(d: Dict[str, Any]) -> str:
    """Latidos cortados por la guillotina; «no registrado» en los datos anteriores a que ``evaluar_crafter`` los guardara."""
    return str(d["latidos_cortados"]) if "latidos_cortados" in d else "no registrado"


def formatear_float_es(valor: float, decimales: int = 2) -> str:
    """Formatea un float con punto de miles y coma decimal estilo español (p. ej. 1.379,2)."""
    s = f"{valor:,.{decimales}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def se_solapan(ic1: Tuple[float, float], ic2: Tuple[float, float]) -> bool:
    """Determina si dos intervalos cerrados [a, b] y [c, d] se solapan."""
    return max(ic1[0], ic2[0]) <= min(ic1[1], ic2[1])


# =====================================================================
# Comparación pareada episodio a episodio
# =====================================================================

def _score(tasas: List[float]) -> float:
    """Crafter Score (como ``evaluar_crafter.calcular_crafter_score``) con las tasas en %."""
    return math.exp(sum(math.log(1.0 + max(0.0, t)) for t in tasas) / len(tasas)) - 1.0 if tasas else 0.0


def _percentiles(valores: List[float], alpha: float) -> Tuple[float, float]:
    v = sorted(valores)
    n = len(v)
    return v[int((alpha / 2.0) * n)], v[min(n - 1, int((1.0 - alpha / 2.0) * n))]


def comparar_pareado(a: Dict[str, Any], b: Dict[str, Any], n_boot: int = 2000, alpha: float = 0.05,
                     semilla: int = 42) -> Dict[str, Any]:
    """Diferencia A − B de la Score y de cada logro sobre los primeros min(n1, n2) episodios, con su IC por
    bootstrap pareado: cada réplica remuestrea con reemplazo índices de episodio y usa el mismo índice en A y en B.

    Las diferencias van en puntos porcentuales. Lanza ``ValueError`` si los JSON no son de la misma semilla base
    o no guardan ``por_episodio``. Es ``comparar_pareado_conjunto`` con un solo par."""
    res = comparar_pareado_conjunto([(a, b)], n_boot=n_boot, alpha=alpha, semilla=semilla)
    par = res["por_semilla"][0]
    return {**res, "episodios": par["episodios"], "semilla_base": par["semilla_base"]}


def comparar_pareado_conjunto(pares: List[Tuple[Dict[str, Any], Dict[str, Any]]], n_boot: int = 2000, alpha: float = 0.05,
                              semilla: int = 42) -> Dict[str, Any]:
    """Comparación pareada que junta varias semillas. Cada par (A, B) es de la misma semilla base y se empareja como en
    ``comparar_pareado`` (los primeros min(n1, n2) episodios). La Score y las tasas se calculan sobre todos los episodios
    emparejados juntos. El IC es por bootstrap pareado estratificado: cada réplica remuestrea con reemplazo, dentro de
    cada semilla, tantos índices como episodios emparejados tiene, y usa el mismo índice en A y en B.

    Las diferencias van en puntos porcentuales. Lanza ``ValueError`` si un par no es de la misma semilla base o no guarda
    ``por_episodio``."""
    if not pares:
        raise ValueError("hace falta al menos un par")
    for a, b in pares:
        if a.get("semilla_base") != b.get("semilla_base"):
            raise ValueError(f"semillas base distintas: {a.get('semilla_base')} y {b.get('semilla_base')}")
        for nombre, d in (("A", a), ("B", b)):
            if "por_episodio" not in d:
                raise ValueError(f"{nombre} no guarda los logros por episodio (falta 'por_episodio'); guarda: {sorted(d)}")
    logros = sorted({lg for a, b in pares for lg in (*a["tasas_logros"], *b["tasas_logros"])})
    # matrices 0/1 por logro y episodio, con los episodios emparejados de todas las semillas uno tras otro
    estratos: List[Tuple[int, int]] = []        # (desde, n) de cada semilla
    eps_a: List[set] = []
    eps_b: List[set] = []
    for a, b in pares:
        n = min(len(a["por_episodio"]), len(b["por_episodio"]))
        estratos.append((len(eps_a), n))
        eps_a += [set(ep["logros"]) for ep in a["por_episodio"][:n]]
        eps_b += [set(ep["logros"]) for ep in b["por_episodio"][:n]]
    total = len(eps_a)
    if total == 0:
        raise ValueError("ningún episodio emparejado")
    ma = [[1 if lg in ep else 0 for ep in eps_a] for lg in logros]
    mb = [[1 if lg in ep else 0 for ep in eps_b] for lg in logros]

    def medir(idx: List[int]) -> Tuple[float, List[float]]:
        ta = [100.0 * sum(fila[i] for i in idx) / len(idx) for fila in ma]
        tb = [100.0 * sum(fila[i] for i in idx) / len(idx) for fila in mb]
        return _score(ta) - _score(tb), [x - y for x, y in zip(ta, tb, strict=True)]

    d_score, d_logros = medir(list(range(total)))
    rnd = random.Random(semilla)
    boot_score: List[float] = []
    boot_logros: List[List[float]] = [[] for _ in logros]
    for _ in range(n_boot):
        idx = [desde + rnd.randrange(n) for desde, n in estratos for _ in range(n)]
        ds, dl = medir(idx)
        boot_score.append(ds)
        for k, v in enumerate(dl):
            boot_logros[k].append(v)

    def fila(dif: float, boot: List[float]) -> Dict[str, Any]:
        ic = _percentiles(boot, alpha)
        return {"diferencia": dif, "ic": ic, "excluye_cero": ic[0] > 0.0 or ic[1] < 0.0}

    return {
        "episodios_pareados": total,
        "por_semilla": [{"semilla_base": a.get("semilla_base"), "episodios_pareados": n,
                         "episodios": (len(a["por_episodio"]), len(b["por_episodio"]))}
                        for (a, b), (_, n) in zip(pares, estratos, strict=True)],
        "n_boot": n_boot,
        "score": {**fila(d_score, boot_score), "a": _score([100.0 * sum(f) / total for f in ma]),
                  "b": _score([100.0 * sum(f) / total for f in mb])},
        "logros": {lg: fila(d_logros[k], boot_logros[k]) for k, lg in enumerate(logros)},
    }


def generar_tabla_pareada(nombre_a: str, nombre_b: str, res: Dict[str, Any]) -> str:
    """Tabla markdown de ``comparar_pareado``: diferencia A − B, IC 95 % pareado y si excluye el 0."""
    f = formatear_float_es
    s = res["score"]
    lineas = [
        f"### {nombre_a} frente a {nombre_b} (semilla base {res['semilla_base']}, {res['episodios_pareados']} episodios "
        f"pareados de {res['episodios'][0]} y {res['episodios'][1]}, {res['n_boot']} réplicas)",
        "",
        f"Score en los episodios pareados: {f(s['a'])} % frente a {f(s['b'])} %.",
        "",
        "| Medida | Diferencia (pp) | IC 95 % pareado (pp) | ¿Excluye el 0? |",
        "|---|---|---|---|",
    ]

    def linea(etiqueta: str, x: Dict[str, Any]) -> str:
        return (f"| {etiqueta} | {f(x['diferencia'])} | [{f(x['ic'][0])}, {f(x['ic'][1])}] | "
                f"{'**Sí**' if x['excluye_cero'] else 'No'} |")

    lineas.append(linea("**Score**", s))
    lineas += [linea(f"`{lg}`", x) for lg, x in res["logros"].items()]
    return "\n".join(lineas) + "\n"


def generar_tabla_pareada_conjunta(nombres: List[Tuple[str, str]], res: Dict[str, Any]) -> str:
    """Tabla markdown de ``comparar_pareado_conjunto``."""
    f = formatear_float_es
    s = res["score"]
    pares = "; ".join(f"{a} frente a {b} (semilla base {p['semilla_base']}, {p['episodios_pareados']} pareados de "
                      f"{p['episodios'][0]} y {p['episodios'][1]})" for (a, b), p in zip(nombres, res["por_semilla"], strict=True))
    lineas = [
        f"### Comparación pareada conjunta ({res['episodios_pareados']} episodios pareados, {res['n_boot']} réplicas "
        f"estratificadas por semilla)",
        "",
        f"Pares: {pares}.",
        "",
        f"Score en los episodios pareados: {f(s['a'])} % frente a {f(s['b'])} %.",
        "",
        "| Medida | Diferencia (pp) | IC 95 % pareado (pp) | ¿Excluye el 0? |",
        "|---|---|---|---|",
    ]

    def linea(etiqueta: str, x: Dict[str, Any]) -> str:
        return (f"| {etiqueta} | {f(x['diferencia'])} | [{f(x['ic'][0])}, {f(x['ic'][1])}] | "
                f"{'**Sí**' if x['excluye_cero'] else 'No'} |")

    lineas.append(linea("**Score**", s))
    lineas += [linea(f"`{lg}`", x) for lg, x in res["logros"].items()]
    return "\n".join(lineas) + "\n"


# =====================================================================
# Informe Paso 6: La defensa general
# =====================================================================

CONDICIONES_PASO6 = [
    {
        "id": "F1",
        "nombre": "F1",
        "columna": "F1",
        "archivo": "paso3_F1.json",
        "opciones": (
            "--pasos 100000 --semilla 31 --vista oficial --sin-herencia "
            "--sin-estrategias-propias --manual estricto"
        ),
    },
    {
        "id": "D1",
        "nombre": "D1",
        "columna": "D1",
        "archivo": "paso6_D1.json",
        "opciones": (
            "--pasos 100000 --semilla 31 --vista oficial --sin-herencia "
            "--manual estricto --sin-estrategias-propias --mecanismos peligro_aprendido"
        ),
    },
    {
        "id": "D2",
        "nombre": "D2",
        "columna": "D2",
        "archivo": "paso6_D2.json",
        "opciones": (
            "--pasos 100000 --semilla 31 --vista oficial --sin-herencia "
            "--manual estricto --sin-estrategias-propias --mecanismos peligro_aprendido afrontar arma_instrumental"
        ),
    },
    {
        "id": "D4",
        "nombre": "D4",
        "columna": "D4",
        "archivo": "paso6_D4.json",
        "opciones": (
            "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --manual estricto"
        ),
    },
    {
        "id": "F2",
        "nombre": "F2",
        "columna": "F2",
        "archivo": "paso3_F2.json",
        "opciones": (
            "--pasos 100000 --semilla 32 --vista oficial --sin-herencia "
            "--sin-estrategias-propias --manual estricto"
        ),
    },
    {
        "id": "D3",
        "nombre": "D3",
        "columna": "D3",
        "archivo": "paso6_D3.json",
        "opciones": (
            "--pasos 100000 --semilla 32 --vista oficial --sin-herencia "
            "--manual estricto --sin-estrategias-propias --mecanismos peligro_aprendido afrontar arma_instrumental"
        ),
    },
]


def cargar_datos_paso6() -> Dict[str, Dict[str, Any]]:
    datos = {}
    for c in CONDICIONES_PASO6:
        ruta = os.path.join(DATOS_DIR, c["archivo"])
        with open(ruta, "r", encoding="utf-8") as f:
            datos[c["id"]] = json.load(f)
    return datos


def generar_tabla_general_paso6(datos: Dict[str, Dict[str, Any]]) -> str:
    columnas = [c["columna"] for c in CONDICIONES_PASO6]
    ids = [c["id"] for c in CONDICIONES_PASO6]

    scores = [f"**{formatear_float_es(datos[cid]['score'])}**" for cid in ids]
    ics = [
        f"[{formatear_float_es(datos[cid]['score_ci_95'][0])}, {formatear_float_es(datos[cid]['score_ci_95'][1])}]"
        for cid in ids
    ]
    episodios = [str(datos[cid]["episodios"]) for cid in ids]
    pasos_ep = [
        formatear_float_es(datos[cid]["pasos"] / datos[cid]["episodios"], 1)
        for cid in ids
    ]
    ms_paso = [formatear_float_es(datos[cid]["ms_por_paso"]) for cid in ids]
    cort = [cortados(datos[cid]) for cid in ids]

    lineas = [
        "## 1. Tabla general",
        "",
        f"| Métrica | {' | '.join(columnas)} |",
        f"|---|{'---|' * len(columnas)}",
        f"| **Score (%)** | {' | '.join(scores)} |",
        f"| **IC 95 % (%)** | {' | '.join(ics)} |",
        f"| **Episodios** | {' | '.join(episodios)} |",
        f"| **Pasos por episodio** | {' | '.join(pasos_ep)} |",
        f"| **ms por paso** | {' | '.join(ms_paso)} |",
        f"| **Latidos cortados** | {' | '.join(cort)} |",
    ]
    return "\n".join(lineas)


def generar_tasas_logros_paso6(datos: Dict[str, Dict[str, Any]]) -> str:
    columnas = [c["columna"] for c in CONDICIONES_PASO6]
    lineas = [
        "## 2. Tasas por logro (%)",
        "",
        "Porcentaje de episodios donde se obtuvo cada uno de los 22 logros oficiales de Crafter:",
        "",
        f"| Logro | {' | '.join(columnas)} |",
        f"|---|{'---|' * len(columnas)}",
    ]
    todos_logros = sorted(datos["F1"]["tasas_logros"].keys())
    ids = [c["id"] for c in CONDICIONES_PASO6]
    for logro in todos_logros:
        valores = [formatear_float_es(datos[cid]["tasas_logros"].get(logro, 0.0)) for cid in ids]
        lineas.append(f"| `{logro}` | {' | '.join(valores)} |")
    return "\n".join(lineas)


def generar_causas_muerte_paso6(datos: Dict[str, Dict[str, Any]]) -> str:
    columnas = [c["columna"] for c in CONDICIONES_PASO6]
    lineas = [
        "## 3. Causas de muerte por condición",
        "",
        "Número de episodios y porcentaje sobre el total de episodios de cada condición:",
        "",
        f"| Causa | {' | '.join(columnas)} |",
        f"|---|{'---|' * len(columnas)}",
    ]
    todas_causas = sorted(
        {causa for d in datos.values() for causa in d["causas_muerte"]},
        key=lambda x: (x == "cortado por presupuesto", x),
    )
    ids = [c["id"] for c in CONDICIONES_PASO6]
    for causa in todas_causas:
        cols = []
        for cid in ids:
            d = datos[cid]
            n = d["causas_muerte"].get(causa, 0)
            pct = formatear_float_es((n / d["episodios"]) * 100.0, 1)
            cols.append(f"{n} ({pct} %)")
        lineas.append(f"| `{causa}` | {' | '.join(cols)} |")
        if causa == "zombi":
            # Fila combinada zombi + desgaste
            cols_zd = []
            for cid in ids:
                d = datos[cid]
                n_zd = d["causas_muerte"].get("zombi", 0) + d["causas_muerte"].get("desgaste", 0)
                pct_zd = formatear_float_es((n_zd / d["episodios"]) * 100.0, 1)
                cols_zd.append(f"{n_zd} ({pct_zd} %)")
            lineas.append(f"| `zombi + desgaste` | {' | '.join(cols_zd)} |")

    totales = [str(datos[cid]["episodios"]) for cid in ids]
    lineas.append(f"| **Total episodios** | **{'** | **'.join(totales)}** |")
    return "\n".join(lineas)


def generar_comparaciones_paso6(datos: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 4. Comparaciones",
        "",
        "Diferencias de Crafter Score (en puntos porcentuales), comprobación de solapamiento de intervalos de confianza al 95 % "
        "y diferencias en logros clave de combate (`defeat_zombie` y `defeat_skeleton`):",
        "",
    ]

    def comparar(nom_a: str, id_a: str, nom_b: str, id_b: str) -> str:
        da, db = datos[id_a], datos[id_b]
        diff = da["score"] - db["score"]
        signo = "+" if diff >= 0 else ""
        diff_str = f"{signo}{formatear_float_es(diff)} pp"
        ic_a = (da["score_ci_95"][0], da["score_ci_95"][1])
        ic_b = (db["score_ci_95"][0], db["score_ci_95"][1])
        solapa = se_solapan(ic_a, ic_b)
        solapa_str = "Sí" if solapa else "No"
        ic_a_str = f"[{formatear_float_es(ic_a[0])}, {formatear_float_es(ic_a[1])}] %"
        ic_b_str = f"[{formatear_float_es(ic_b[0])}, {formatear_float_es(ic_b[1])}] %"

        z_a = da["tasas_logros"].get("defeat_zombie", 0.0)
        z_b = db["tasas_logros"].get("defeat_zombie", 0.0)
        diff_z = z_a - z_b
        signo_z = "+" if diff_z >= 0 else ""
        diff_z_str = f"{signo_z}{formatear_float_es(diff_z)} pp"

        sk_a = da["tasas_logros"].get("defeat_skeleton", 0.0)
        sk_b = db["tasas_logros"].get("defeat_skeleton", 0.0)
        diff_sk = sk_a - sk_b
        signo_sk = "+" if diff_sk >= 0 else ""
        diff_sk_str = f"{signo_sk}{formatear_float_es(diff_sk)} pp"

        return (
            f"- **{nom_a} frente a {nom_b}**:\n"
            f"  - Score {nom_a}: {formatear_float_es(da['score'])} % (IC 95 %: {ic_a_str})\n"
            f"  - Score {nom_b}: {formatear_float_es(db['score'])} % (IC 95 %: {ic_b_str})\n"
            f"  - Diferencia de Score ({nom_a} - {nom_b}): {diff_str}\n"
            f"  - ¿Se solapan los IC 95 %?: **{solapa_str}**\n"
            f"  - `defeat_zombie`: {formatear_float_es(z_a)} % frente a {formatear_float_es(z_b)} % ({diff_z_str})\n"
            f"  - `defeat_skeleton`: {formatear_float_es(sk_a)} % frente a {formatear_float_es(sk_b)} % ({diff_sk_str})"
        )

    # 1. D1 frente a F1
    lineas.append("### D1 frente a F1 (semilla 31, peligro aprendido)")
    lineas.append(comparar("D1", "D1", "F1", "F1"))
    lineas.append("")

    # 2. D2 frente a F1 y a D1
    lineas.append("### D2 frente a F1 y a D1 (semilla 31, defensa completa)")
    lineas.append(comparar("D2", "D2", "F1", "F1"))
    lineas.append("")
    lineas.append(comparar("D2", "D2", "D1", "D1"))
    lineas.append("")

    # 3. D3 frente a F2
    lineas.append("### D3 frente a F2 (semilla 32, defensa completa)")
    lineas.append(comparar("D3", "D3", "F2", "F2"))
    lineas.append("")

    # 4. D4 frente a D2
    lineas.append("### D4 frente a D2 (semilla 31, comprobación de equivalencia del paso 6d)")
    lineas.append(comparar("D4", "D4", "D2", "D2"))
    lineas.append("")
    lineas.append(
        "**Resultado de la comprobación de equivalencia del 6d:**\n"
        "Se comprobó que borrar `DefensaArmada` y `CerrarDistancia` y retirar los interruptores de `Perfil` "
        "no altera la conducta de Crafter. Al comparar `paso6_D4.json` con `paso6_D2.json` "
        "(ignorando `tiempo_segundos`, `ms_por_paso`, `mecanismos` y `sin_estrategias_propias`), "
        "**todos los campos son idénticos** (Score 14,04 %, IC 95 % [12,92, 15,06] %, 383 episodios, 100.000 pasos "
        "y las tasas de los 22 logros oficiales de Crafter) salvo una única causa de muerte:\n"
        "- En D2: 27 muertes por flecha y 271 por zombi (0 latidos cortados).\n"
        "- En D4: 26 muertes por flecha y 272 por zombi (1 latido cortado).\n"
        "Esta divergencia de un solo caso se debe exclusivamente a que en D4 la guillotina cortó 1 latido por reloj (> 100 ms) "
        "en el episodio 64: dicho episodio duró 167 pasos muriendo por zombi (en vez de 169 pasos muriendo por flecha en D2). "
        "Todos los demás episodios siguieron trayectorias idénticas, dándose por buena la equivalencia."
    )
    lineas.append("")

    return "\n".join(lineas)


def generar_informe_paso6() -> str:
    datos = cargar_datos_paso6()
    cabecera = [
        "# Medición Oficial: Paso 6 — La defensa general (Crafter)",
        "",
        "Evaluación oficial en Crafter (100.000 pasos, vista oficial, sin herencia, manual estricto, sin estrategias propias) "
        "en la rama `feature/defensa` (commit `027062e` para D1-D3; commit `b9daf9c` para D4). "
        "Evalúa el paso 6: la defensa general (peligro aprendido, afrontar —luchar o huir— y arma como meta instrumental) "
        "y la retirada de las estrategias propias de Crafter (paso 6d, pilar 1).",
        "",
        "Ficheros de datos utilizados (en `datos/evaluacion/`):",
        "- `paso3_F1.json`: F1 (Referencia Paso 3, semilla 31, sin estrategias propias)",
        "- `paso6_D1.json`: D1 (Paso 6a, semilla 31, mecanismo `peligro_aprendido`)",
        "- `paso6_D2.json`: D2 (Paso 6 completo, semilla 31, mecanismos `peligro_aprendido`, `afrontar`, `arma_instrumental`)",
        "- `paso6_D4.json`: D4 (Paso 6d en base, semilla 31, sin estrategias propias ni mecanismos)",
        "- `paso3_F2.json`: F2 (Referencia Paso 3, semilla 32, sin estrategias propias)",
        "- `paso6_D3.json`: D3 (Paso 6 completo, semilla 32, mecanismos `peligro_aprendido`, `afrontar`, `arma_instrumental`)",
        "",
        "### Control de latidos cortados (guillotina de 100 ms)",
        "",
        "Criterio de validez: una medición es válida si registra 10 latidos cortados o menos "
        "(menos del 0,01 % de los latidos). En las mediciones evaluadas:",
        "- **F1**: 4 latidos cortados en 4 episodios (0,004 % de los latidos).",
        "- **D1**: 0 latidos cortados.",
        "- **D2**: 0 latidos cortados.",
        "- **D4**: 1 latido cortado en 1 episodio (episodio 64; 0,001 % de los latidos).",
        "- **F2**: 6 latidos cortados en 4 episodios (0,006 % de los latidos).",
        "- **D3**: 0 latidos cortados.",
        "",
    ]
    partes = [
        "\n".join(cabecera),
        generar_tabla_general_paso6(datos),
        generar_tasas_logros_paso6(datos),
        generar_causas_muerte_paso6(datos),
        generar_comparaciones_paso6(datos),
    ]
    return "\n\n---\n\n".join(partes) + "\n"


# =====================================================================
# Informe Cierre Paso 3: Proteger X (refugio general en base)
# =====================================================================

CONDICIONES_CIERRE_PASO3 = [
    {
        "id": "C1",
        "nombre": "C1",
        "columna": "C1",
        "archivo": "cierre0_C1.json",
        "opciones": (
            "--pasos 100000 --semilla 31 --vista oficial --sin-herencia "
            "--sin-estrategias-propias --manual estricto"
        ),
    },
    {
        "id": "L1a",
        "nombre": "L1a",
        "columna": "L1a",
        "archivo": "paso3_L1a.json",
        "opciones": (
            "--pasos 100000 --semilla 31 --vista oficial --sin-herencia "
            "--manual estricto --sin-estrategias-propias --mecanismos proteger"
        ),
    },
    {
        "id": "F1",
        "nombre": "F1",
        "columna": "F1",
        "archivo": "paso3_F1.json",
        "opciones": (
            "--pasos 100000 --semilla 31 --vista oficial --sin-herencia "
            "--sin-estrategias-propias --manual estricto"
        ),
    },
    {
        "id": "C3",
        "nombre": "C3",
        "columna": "C3",
        "archivo": "cierre0_C3.json",
        "opciones": (
            "--pasos 100000 --semilla 32 --vista oficial --sin-herencia "
            "--sin-estrategias-propias --manual estricto"
        ),
    },
    {
        "id": "L1c",
        "nombre": "L1c",
        "columna": "L1c",
        "archivo": "paso3_L1c.json",
        "opciones": (
            "--pasos 100000 --semilla 32 --vista oficial --sin-herencia "
            "--manual estricto --sin-estrategias-propias --mecanismos proteger"
        ),
    },
    {
        "id": "F2",
        "nombre": "F2",
        "columna": "F2",
        "archivo": "paso3_F2.json",
        "opciones": (
            "--pasos 100000 --semilla 32 --vista oficial --sin-herencia "
            "--sin-estrategias-propias --manual estricto"
        ),
    },
    {
        "id": "C2",
        "nombre": "C2",
        "columna": "C2",
        "archivo": "cierre0_C2.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --manual estricto",
    },
    {
        "id": "L2",
        "nombre": "L2",
        "columna": "L2",
        "archivo": "paso3_L2.json",
        "opciones": (
            "--pasos 100000 --semilla 31 --vista oficial --sin-herencia "
            "--manual estricto --mecanismos proteger"
        ),
    },
    {
        "id": "F3",
        "nombre": "F3",
        "columna": "F3",
        "archivo": "paso3_F3.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --manual estricto",
    },
]


def cargar_datos_cierre_paso3() -> Dict[str, Dict[str, Any]]:
    datos = {}
    for c in CONDICIONES_CIERRE_PASO3:
        ruta = os.path.join(DATOS_DIR, c["archivo"])
        with open(ruta, "r", encoding="utf-8") as f:
            datos[c["id"]] = json.load(f)
    return datos


def generar_tabla_general_cierre_paso3(datos: Dict[str, Dict[str, Any]]) -> str:
    columnas = [c["columna"] for c in CONDICIONES_CIERRE_PASO3]
    ids = [c["id"] for c in CONDICIONES_CIERRE_PASO3]

    scores = [f"**{formatear_float_es(datos[cid]['score'])}**" for cid in ids]
    ics = [
        f"[{formatear_float_es(datos[cid]['score_ci_95'][0])}, {formatear_float_es(datos[cid]['score_ci_95'][1])}]"
        for cid in ids
    ]
    episodios = [str(datos[cid]["episodios"]) for cid in ids]
    pasos_ep = [
        formatear_float_es(datos[cid]["pasos"] / datos[cid]["episodios"], 1)
        for cid in ids
    ]
    ms_paso = [formatear_float_es(datos[cid]["ms_por_paso"]) for cid in ids]
    cort = [cortados(datos[cid]) for cid in ids]

    lineas = [
        "## 1. Tabla general",
        "",
        f"| Métrica | {' | '.join(columnas)} |",
        f"|---|{'---|' * len(columnas)}",
        f"| **Score (%)** | {' | '.join(scores)} |",
        f"| **IC 95 % (%)** | {' | '.join(ics)} |",
        f"| **Episodios** | {' | '.join(episodios)} |",
        f"| **Pasos por episodio** | {' | '.join(pasos_ep)} |",
        f"| **ms por paso** | {' | '.join(ms_paso)} |",
        f"| **Latidos cortados** | {' | '.join(cort)} |",
    ]
    return "\n".join(lineas)


def generar_tasas_logros_cierre_paso3(datos: Dict[str, Dict[str, Any]]) -> str:
    columnas = [c["columna"] for c in CONDICIONES_CIERRE_PASO3]
    lineas = [
        "## 2. Tasas por logro (%)",
        "",
        "Porcentaje de episodios donde se obtuvo cada uno de los 22 logros oficiales de Crafter:",
        "",
        f"| Logro | {' | '.join(columnas)} |",
        f"|---|{'---|' * len(columnas)}",
    ]
    todos_logros = sorted(datos["C1"]["tasas_logros"].keys())
    ids = [c["id"] for c in CONDICIONES_CIERRE_PASO3]
    for logro in todos_logros:
        valores = [formatear_float_es(datos[cid]["tasas_logros"].get(logro, 0.0)) for cid in ids]
        lineas.append(f"| `{logro}` | {' | '.join(valores)} |")
    return "\n".join(lineas)


def generar_causas_muerte_cierre_paso3(datos: Dict[str, Dict[str, Any]]) -> str:
    columnas = [c["columna"] for c in CONDICIONES_CIERRE_PASO3]
    lineas = [
        "## 3. Causas de muerte por condición",
        "",
        "Número de episodios y porcentaje sobre el total de episodios de cada condición:",
        "",
        f"| Causa | {' | '.join(columnas)} |",
        f"|---|{'---|' * len(columnas)}",
    ]
    todas_causas = sorted(
        {causa for d in datos.values() for causa in d["causas_muerte"]},
        key=lambda x: (x == "cortado por presupuesto", x),
    )
    ids = [c["id"] for c in CONDICIONES_CIERRE_PASO3]
    for causa in todas_causas:
        cols = []
        for cid in ids:
            d = datos[cid]
            n = d["causas_muerte"].get(causa, 0)
            pct = formatear_float_es((n / d["episodios"]) * 100.0, 1)
            cols.append(f"{n} ({pct} %)")
        lineas.append(f"| `{causa}` | {' | '.join(cols)} |")
    totales = [str(datos[cid]["episodios"]) for cid in ids]
    lineas.append(f"| **Total episodios** | **{'** | **'.join(totales)}** |")
    return "\n".join(lineas)


def generar_comparaciones_cierre_paso3(datos: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 4. Comparaciones",
        "",
        "Diferencias de Crafter Score (en puntos porcentuales) y comprobación de solapamiento de intervalos de confianza al 95 %:",
        "",
    ]

    def comparar(nom_a: str, id_a: str, nom_b: str, id_b: str) -> str:
        da, db = datos[id_a], datos[id_b]
        diff = da["score"] - db["score"]
        signo = "+" if diff >= 0 else ""
        diff_str = f"{signo}{formatear_float_es(diff)} pp"
        ic_a = (da["score_ci_95"][0], da["score_ci_95"][1])
        ic_b = (db["score_ci_95"][0], db["score_ci_95"][1])
        solapa = se_solapan(ic_a, ic_b)
        solapa_str = "Sí" if solapa else "No"
        ic_a_str = f"[{formatear_float_es(ic_a[0])}, {formatear_float_es(ic_a[1])}] %"
        ic_b_str = f"[{formatear_float_es(ic_b[0])}, {formatear_float_es(ic_b[1])}] %"
        return (
            f"- **{nom_a} frente a {nom_b}**:\n"
            f"  - Score {nom_a}: {formatear_float_es(da['score'])} % (IC 95 %: {ic_a_str})\n"
            f"  - Score {nom_b}: {formatear_float_es(db['score'])} % (IC 95 %: {ic_b_str})\n"
            f"  - Diferencia de Score ({nom_a} - {nom_b}): {diff_str}\n"
            f"  - ¿Se solapan los IC 95 %?: **{solapa_str}**"
        )

    # 1. F1 frente a C1 y a L1a
    lineas.append("### F1 frente a C1 y a L1a (semilla 31, sin estrategias propias)")
    lineas.append(comparar("F1", "F1", "C1", "C1"))
    lineas.append("")
    lineas.append(comparar("F1", "F1", "L1a", "L1a"))
    lineas.append("")

    # 2. F2 frente a C3 y a L1c
    lineas.append("### F2 frente a C3 y a L1c (semilla 32, sin estrategias propias)")
    lineas.append(comparar("F2", "F2", "C3", "C3"))
    lineas.append("")
    lineas.append(comparar("F2", "F2", "L1c", "L1c"))
    lineas.append("")

    # 3. F3 frente a C2 y a L2
    lineas.append("### F3 frente a C2 y a L2 (semilla 31, con estrategias propias)")
    lineas.append(comparar("F3", "F3", "C2", "C2"))
    lineas.append("")
    lineas.append(comparar("F3", "F3", "L2", "L2"))
    lineas.append("")

    return "\n".join(lineas)


def generar_comprobacion_reproducibilidad() -> str:
    lineas = [
        "## 5. Comprobación de reproducibilidad (Punto 1)",
        "",
        "Se comprobó la reproducibilidad de la medición de referencia antigua C1 ejecutando el commit `1ecf254` "
        "(rama `feature/cierre-paso0`) con las opciones exactas originales y guardando el resultado en `datos/evaluacion/repro_C1.json`:",
        "",
        "```bash",
        "python herramientas\\evaluar_crafter.py --pasos 100000 --semilla 31 --vista oficial "
        "--sin-herencia --sin-estrategias-propias --manual estricto --salida datos\\evaluacion\\repro_C1.json",
        "```",
        "",
        "Al comparar `repro_C1.json` con `origin/feature/cierre-paso0:datos/evaluacion/cierre0_C1.json`, "
        "ignorando `tiempo_segundos` y `ms_por_paso`, **TODOS los demás campos son estrictamente idénticos**:",
        "- Score: 11,29 %",
        "- IC 95 %: [10,44, 12,01] %",
        "- Episodios: 416 (240,4 pasos/episodio)",
        "- Tasas de los 22 logros oficiales: exactamente iguales en todos los logros.",
        "- Causas de muerte: exactamente iguales en todas las causas.",
        "- Diferencias de reloj: 1.094,6 s (10,95 ms/paso) frente a 1.035,0 s (10,35 ms/paso).",
        "",
        "El fichero `repro_C1.json` no contiene rutas locales y se incluye en el repositorio.",
    ]
    return "\n".join(lineas)


def generar_informe_cierre_paso3() -> str:
    datos = cargar_datos_cierre_paso3()
    cabecera = [
        "# Medición Oficial: Cierre del Paso 3 (Crafter)",
        "",
        "Evaluación oficial en Crafter (100.000 pasos, vista oficial, sin herencia, manual estricto) "
        "en la rama `feature/proteger` (commit `c62b1c5`). "
        "Evalúa el cierre del Paso 3: la capacidad general «proteger X» (el refugio general) "
        "integrada en la base del framework (`ida/`).",
        "",
        "Ficheros de datos utilizados (en `datos/evaluacion/`):",
        "- `cierre0_C1.json`: C1 (Cierre Paso 0, sin estrategias propias, semilla 31)",
        "- `paso3_L1a.json`: L1a (Paso 3 exploratorio, sin estrategias propias, mecanismo proteger, semilla 31)",
        "- `paso3_F1.json`: F1 (Cierre Paso 3, sin estrategias propias, refugio general en base, semilla 31)",
        "- `cierre0_C3.json`: C3 (Cierre Paso 0, sin estrategias propias, semilla 32)",
        "- `paso3_L1c.json`: L1c (Paso 3 exploratorio, sin estrategias propias, mecanismo proteger, semilla 32)",
        "- `paso3_F2.json`: F2 (Cierre Paso 3, sin estrategias propias, refugio general en base, semilla 32)",
        "- `cierre0_C2.json`: C2 (Cierre Paso 0, con estrategias propias restantes, semilla 31)",
        "- `paso3_L2.json`: L2 (Paso 3 exploratorio, con estrategias propias restantes, mecanismo proteger, semilla 31)",
        "- `paso3_F3.json`: F3 (Cierre Paso 3, con estrategias propias restantes, refugio general en base, semilla 31)",
        "",
        "### Control de latidos cortados (guillotina de 100 ms)",
        "",
        "Criterio de validez: una medición es válida si registra 10 latidos cortados o menos "
        "(menos del 0,01 % de los latidos). En las mediciones de cierre:",
        "- **F1**: 4 latidos cortados en 4 episodios (0,004 % de los latidos). "
        "Se adopta como definitiva esta segunda ejecución (Score 12,82 %, 380 episodios). "
        "La primera ejecución registró 1 latido cortado en 1 episodio (Score 12,85 %, 379 episodios).",
        "- **F2**: 6 latidos cortados en 4 episodios (0,006 % de los latidos; Score 13,58 %, 380 episodios).",
        "- **F3**: 1 latido cortado en 1 episodio (0,001 % de los latidos; Score 13,80 %, 358 episodios).",
        "- **C1, C3, C2, L1a, L1c, L2**: anteriores a la instrumentación de conteo de cortes (`no registrado`).",
        "",
    ]
    partes = [
        "\n".join(cabecera),
        generar_tabla_general_cierre_paso3(datos),
        generar_tasas_logros_cierre_paso3(datos),
        generar_causas_muerte_cierre_paso3(datos),
        generar_comparaciones_cierre_paso3(datos),
        generar_comprobacion_reproducibilidad(),
    ]
    return "\n\n---\n\n".join(partes) + "\n"


# =====================================================================
# Informe Paso 3: Proteger X (el refugio general)
# =====================================================================

CONDICIONES_PASO3 = [
    {
        "id": "C1",
        "nombre": "C1",
        "columna": "C1",
        "archivo": "cierre0_C1.json",
        "opciones": (
            "--pasos 100000 --semilla 31 --vista oficial --sin-herencia "
            "--sin-estrategias-propias --manual estricto"
        ),
    },
    {
        "id": "L1a",
        "nombre": "L1a",
        "columna": "L1a",
        "archivo": "paso3_L1a.json",
        "opciones": (
            "--pasos 100000 --semilla 31 --vista oficial --sin-herencia "
            "--manual estricto --sin-estrategias-propias --mecanismos proteger"
        ),
    },
    {
        "id": "L1b",
        "nombre": "L1b",
        "columna": "L1b",
        "archivo": "paso3_L1b.json",
        "opciones": (
            "--pasos 100000 --semilla 31 --vista oficial --sin-herencia "
            "--manual estricto --sin-estrategias-propias --mecanismos proteger alostasis"
        ),
    },
    {
        "id": "C3",
        "nombre": "C3",
        "columna": "C3",
        "archivo": "cierre0_C3.json",
        "opciones": (
            "--pasos 100000 --semilla 32 --vista oficial --sin-herencia "
            "--sin-estrategias-propias --manual estricto"
        ),
    },
    {
        "id": "L1c",
        "nombre": "L1c",
        "columna": "L1c",
        "archivo": "paso3_L1c.json",
        "opciones": (
            "--pasos 100000 --semilla 32 --vista oficial --sin-herencia "
            "--manual estricto --sin-estrategias-propias --mecanismos proteger"
        ),
    },
    {
        "id": "C2",
        "nombre": "C2",
        "columna": "C2",
        "archivo": "cierre0_C2.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --manual estricto",
    },
    {
        "id": "L2",
        "nombre": "L2",
        "columna": "L2",
        "archivo": "paso3_L2.json",
        "opciones": (
            "--pasos 100000 --semilla 31 --vista oficial --sin-herencia "
            "--manual estricto --mecanismos proteger"
        ),
    },
]


def cargar_datos_paso3() -> Dict[str, Dict[str, Any]]:
    datos = {}
    for c in CONDICIONES_PASO3:
        ruta = os.path.join(DATOS_DIR, c["archivo"])
        with open(ruta, "r", encoding="utf-8") as f:
            datos[c["id"]] = json.load(f)
    return datos


def generar_tabla_general_paso3(datos: Dict[str, Dict[str, Any]]) -> str:
    columnas = [c["columna"] for c in CONDICIONES_PASO3]
    ids = [c["id"] for c in CONDICIONES_PASO3]

    scores = [f"**{formatear_float_es(datos[cid]['score'])}**" for cid in ids]
    ics = [
        f"[{formatear_float_es(datos[cid]['score_ci_95'][0])}, {formatear_float_es(datos[cid]['score_ci_95'][1])}]"
        for cid in ids
    ]
    episodios = [str(datos[cid]["episodios"]) for cid in ids]
    pasos_ep = [
        formatear_float_es(datos[cid]["pasos"] / datos[cid]["episodios"], 1)
        for cid in ids
    ]
    ms_paso = [formatear_float_es(datos[cid]["ms_por_paso"]) for cid in ids]
    cort = [cortados(datos[cid]) for cid in ids]

    lineas = [
        "## 1. Tabla general",
        "",
        f"| Métrica | {' | '.join(columnas)} |",
        f"|---|{'---|' * len(columnas)}",
        f"| **Score (%)** | {' | '.join(scores)} |",
        f"| **IC 95 % (%)** | {' | '.join(ics)} |",
        f"| **Episodios** | {' | '.join(episodios)} |",
        f"| **Pasos por episodio** | {' | '.join(pasos_ep)} |",
        f"| **ms por paso** | {' | '.join(ms_paso)} |",
        f"| **Latidos cortados** | {' | '.join(cort)} |",
    ]
    return "\n".join(lineas)


def generar_tasas_logros_paso3(datos: Dict[str, Dict[str, Any]]) -> str:
    columnas = [c["columna"] for c in CONDICIONES_PASO3]
    lineas = [
        "## 2. Tasas por logro (%)",
        "",
        "Porcentaje de episodios donde se obtuvo cada uno de los 22 logros oficiales de Crafter:",
        "",
        f"| Logro | {' | '.join(columnas)} |",
        f"|---|{'---|' * len(columnas)}",
    ]
    todos_logros = sorted(datos["C1"]["tasas_logros"].keys())
    ids = [c["id"] for c in CONDICIONES_PASO3]
    for logro in todos_logros:
        valores = [formatear_float_es(datos[cid]["tasas_logros"].get(logro, 0.0)) for cid in ids]
        lineas.append(f"| `{logro}` | {' | '.join(valores)} |")
    return "\n".join(lineas)


def generar_causas_muerte_paso3(datos: Dict[str, Dict[str, Any]]) -> str:
    columnas = [c["columna"] for c in CONDICIONES_PASO3]
    lineas = [
        "## 3. Causas de muerte por condición",
        "",
        "Número de episodios y porcentaje sobre el total de episodios de cada condición:",
        "",
        f"| Causa | {' | '.join(columnas)} |",
        f"|---|{'---|' * len(columnas)}",
    ]
    todas_causas = sorted(
        {causa for d in datos.values() for causa in d["causas_muerte"]},
        key=lambda x: (x == "cortado por presupuesto", x),
    )
    ids = [c["id"] for c in CONDICIONES_PASO3]
    for causa in todas_causas:
        cols = []
        for cid in ids:
            d = datos[cid]
            n = d["causas_muerte"].get(causa, 0)
            pct = formatear_float_es((n / d["episodios"]) * 100.0, 1)
            cols.append(f"{n} ({pct} %)")
        lineas.append(f"| `{causa}` | {' | '.join(cols)} |")
    totales = [str(datos[cid]["episodios"]) for cid in ids]
    lineas.append(f"| **Total episodios** | **{'** | **'.join(totales)}** |")
    return "\n".join(lineas)


def generar_comparaciones_paso3(datos: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 4. Comparaciones",
        "",
        "Diferencias de Crafter Score (en puntos porcentuales) y comprobación de solapamiento de intervalos de confianza al 95 %:",
        "",
    ]

    def comparar(nom_a: str, id_a: str, nom_b: str, id_b: str) -> str:
        da, db = datos[id_a], datos[id_b]
        diff = da["score"] - db["score"]
        signo = "+" if diff >= 0 else ""
        diff_str = f"{signo}{formatear_float_es(diff)} pp"
        ic_a = (da["score_ci_95"][0], da["score_ci_95"][1])
        ic_b = (db["score_ci_95"][0], db["score_ci_95"][1])
        solapa = se_solapan(ic_a, ic_b)
        solapa_str = "Sí" if solapa else "No"
        ic_a_str = f"[{formatear_float_es(ic_a[0])}, {formatear_float_es(ic_a[1])}] %"
        ic_b_str = f"[{formatear_float_es(ic_b[0])}, {formatear_float_es(ic_b[1])}] %"
        return (
            f"- **{nom_a} frente a {nom_b}**:\n"
            f"  - Score {nom_a}: {formatear_float_es(da['score'])} % (IC 95 %: {ic_a_str})\n"
            f"  - Score {nom_b}: {formatear_float_es(db['score'])} % (IC 95 %: {ic_b_str})\n"
            f"  - Diferencia de Score ({nom_a} - {nom_b}): {diff_str}\n"
            f"  - ¿Se solapan los IC 95 %?: **{solapa_str}**"
        )

    # 1. L1a frente a C1
    lineas.append("### L1a frente a C1")
    lineas.append(comparar("L1a", "L1a", "C1", "C1"))
    lineas.append("")

    # 2. L1b frente a L1a
    lineas.append("### L1b frente a L1a")
    lineas.append(comparar("L1b", "L1b", "L1a", "L1a"))
    lineas.append("")

    # 3. L1c frente a C3
    lineas.append("### L1c frente a C3")
    lineas.append(comparar("L1c", "L1c", "C3", "C3"))
    lineas.append("")

    # 4. L2 frente a C2
    lineas.append("### L2 frente a C2")
    lineas.append(comparar("L2", "L2", "C2", "C2"))
    lineas.append("")

    return "\n".join(lineas)


def generar_informe_paso3() -> str:
    datos = cargar_datos_paso3()
    cabecera = [
        "# Medición Oficial: Paso 3 (Crafter)",
        "",
        "Evaluación oficial en Crafter (100.000 pasos, vista oficial, sin herencia, manual estricto) "
        "en la rama `feature/proteger` (commit `c0fd4e3`). "
        "Evalúa la capacidad general «proteger X» (el refugio general) y la alostasis.",
        "",
        "Ficheros de datos utilizados (en `datos/evaluacion/`):",
        "- `cierre0_C1.json`: C1 (Cierre Paso 0, sin estrategias propias, semilla 31)",
        "- `paso3_L1a.json`: L1a (Paso 3, sin estrategias propias, mecanismo proteger, semilla 31)",
        "- `paso3_L1b.json`: L1b (Paso 3, sin estrategias propias, mecanismos proteger + alostasis, semilla 31)",
        "- `cierre0_C3.json`: C3 (Cierre Paso 0, sin estrategias propias, semilla 32)",
        "- `paso3_L1c.json`: L1c (Paso 3, sin estrategias propias, mecanismo proteger, semilla 32)",
        "- `cierre0_C2.json`: C2 (Cierre Paso 0, con estrategias propias, semilla 31)",
        "- `paso3_L2.json`: L2 (Paso 3, con estrategias propias, mecanismo proteger, semilla 31)",
        "",
    ]
    partes = [
        "\n".join(cabecera),
        generar_tabla_general_paso3(datos),
        generar_tasas_logros_paso3(datos),
        generar_causas_muerte_paso3(datos),
        generar_comparaciones_paso3(datos),
    ]
    return "\n\n---\n\n".join(partes) + "\n"


# =====================================================================
# Informe Cierre Paso 0
# =====================================================================

CONDICIONES_CIERRE_PASO0 = [
    {
        "id": "suelo_linaje",
        "nombre": "Suelo con linaje",
        "columna": "Suelo con linaje",
        "archivo": "suelo_main.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-estrategias-propias",
    },
    {
        "id": "S0",
        "nombre": "S0",
        "columna": "S0",
        "archivo": "suelo_sin_herencia.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --sin-estrategias-propias",
    },
    {
        "id": "G1",
        "nombre": "G1",
        "columna": "G1",
        "archivo": "paso5_G1.json",
        "opciones": (
            "--pasos 100000 --semilla 31 --vista oficial --sin-herencia "
            "--sin-estrategias-propias --manual estricto"
        ),
    },
    {
        "id": "P2",
        "nombre": "P2",
        "columna": "P2",
        "archivo": "paso0_P2.json",
        "opciones": (
            "--pasos 100000 --semilla 31 --vista oficial --sin-herencia "
            "--sin-estrategias-propias --manual estricto --mecanismos urgencia_local aliestesia"
        ),
    },
    {
        "id": "C1",
        "nombre": "C1",
        "columna": "C1",
        "archivo": "cierre0_C1.json",
        "opciones": (
            "--pasos 100000 --semilla 31 --vista oficial --sin-herencia "
            "--sin-estrategias-propias --manual estricto"
        ),
    },
    {
        "id": "C3",
        "nombre": "C3",
        "columna": "C3",
        "archivo": "cierre0_C3.json",
        "opciones": (
            "--pasos 100000 --semilla 32 --vista oficial --sin-herencia "
            "--sin-estrategias-propias --manual estricto"
        ),
    },
    {
        "id": "G3",
        "nombre": "G3",
        "columna": "G3",
        "archivo": "paso5_G3.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --manual estricto",
    },
    {
        "id": "P3",
        "nombre": "P3",
        "columna": "P3",
        "archivo": "paso0_P3.json",
        "opciones": (
            "--pasos 100000 --semilla 31 --vista oficial --sin-herencia "
            "--manual estricto --mecanismos urgencia_local aliestesia"
        ),
    },
    {
        "id": "C2",
        "nombre": "C2",
        "columna": "C2",
        "archivo": "cierre0_C2.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --manual estricto",
    },
]


def cargar_datos_cierre_paso0() -> Dict[str, Dict[str, Any]]:
    datos = {}
    for c in CONDICIONES_CIERRE_PASO0:
        ruta = os.path.join(DATOS_DIR, c["archivo"])
        with open(ruta, "r", encoding="utf-8") as f:
            datos[c["id"]] = json.load(f)
    return datos


def generar_tabla_general_cierre0(datos: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 1. Tabla general",
        "",
        "| Condición | Opciones exactas | Score (%) | IC 95 % (%) | Episodios | Pasos / ep. | Rendimiento (ms/paso) | Latidos cortados |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for c in CONDICIONES_CIERRE_PASO0:
        cid = c["id"]
        d = datos[cid]
        score_str = formatear_float_es(d["score"])
        ic_str = f"[{formatear_float_es(d['score_ci_95'][0])}, {formatear_float_es(d['score_ci_95'][1])}]"
        ep = d["episodios"]
        pasos_ep = formatear_float_es(d["pasos"] / ep, 1)
        ms_paso = formatear_float_es(d["ms_por_paso"])
        lineas.append(
            f"| **{c['nombre']}** | `{c['opciones']}` | **{score_str}** | {ic_str} | {ep} | {pasos_ep} | {ms_paso} | {cortados(d)} |"
        )
    return "\n".join(lineas)


def generar_tasas_logros_cierre0(datos: Dict[str, Dict[str, Any]]) -> str:
    columnas = [c["columna"] for c in CONDICIONES_CIERRE_PASO0]
    lineas = [
        "## 2. Tasas por logro (%)",
        "",
        "Porcentaje de episodios donde se obtuvo cada uno de los 22 logros oficiales de Crafter:",
        "",
        f"| Logro | {' | '.join(columnas)} |",
        f"|---|{'---|' * len(columnas)}",
    ]
    todos_logros = sorted(datos["suelo_linaje"]["tasas_logros"].keys())
    ids = [c["id"] for c in CONDICIONES_CIERRE_PASO0]
    for logro in todos_logros:
        valores = [formatear_float_es(datos[cid]["tasas_logros"].get(logro, 0.0)) for cid in ids]
        lineas.append(f"| `{logro}` | {' | '.join(valores)} |")
    return "\n".join(lineas)


def generar_causas_muerte_cierre0(datos: Dict[str, Dict[str, Any]]) -> str:
    columnas = [c["columna"] for c in CONDICIONES_CIERRE_PASO0]
    lineas = [
        "## 3. Causas de muerte por condición",
        "",
        "Número de episodios y porcentaje sobre el total de episodios de cada condición:",
        "",
        f"| Causa | {' | '.join(columnas)} |",
        f"|---|{'---|' * len(columnas)}",
    ]
    todas_causas = sorted(
        {causa for d in datos.values() for causa in d["causas_muerte"]},
        key=lambda x: (x == "cortado por presupuesto", x),
    )
    ids = [c["id"] for c in CONDICIONES_CIERRE_PASO0]
    for causa in todas_causas:
        cols = []
        for cid in ids:
            d = datos[cid]
            n = d["causas_muerte"].get(causa, 0)
            pct = formatear_float_es((n / d["episodios"]) * 100.0, 1)
            cols.append(f"{n} ({pct} %)")
        lineas.append(f"| `{causa}` | {' | '.join(cols)} |")
    totales = [str(datos[cid]["episodios"]) for cid in ids]
    lineas.append(f"| **Total episodios** | **{'** | **'.join(totales)}** |")
    return "\n".join(lineas)


def generar_comparaciones_cierre0(datos: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 4. Comparaciones",
        "",
        "Diferencias de Crafter Score (en puntos porcentuales) y comprobación de solapamiento de intervalos de confianza al 95 %:",
        "",
    ]

    def comparar(nom_a: str, id_a: str, nom_b: str, id_b: str) -> str:
        da, db = datos[id_a], datos[id_b]
        diff = da["score"] - db["score"]
        signo = "+" if diff >= 0 else ""
        diff_str = f"{signo}{formatear_float_es(diff)} pp"
        ic_a = (da["score_ci_95"][0], da["score_ci_95"][1])
        ic_b = (db["score_ci_95"][0], db["score_ci_95"][1])
        solapa = se_solapan(ic_a, ic_b)
        solapa_str = "Sí" if solapa else "No"
        ic_a_str = f"[{formatear_float_es(ic_a[0])}, {formatear_float_es(ic_a[1])}] %"
        ic_b_str = f"[{formatear_float_es(ic_b[0])}, {formatear_float_es(ic_b[1])}] %"
        return (
            f"- **{nom_a} frente a {nom_b}**:\n"
            f"  - Score {nom_a}: {formatear_float_es(da['score'])} % (IC 95 %: {ic_a_str})\n"
            f"  - Score {nom_b}: {formatear_float_es(db['score'])} % (IC 95 %: {ic_b_str})\n"
            f"  - Diferencia de Score ({nom_a} - {nom_b}): {diff_str}\n"
            f"  - ¿Se solapan los IC 95 %?: **{solapa_str}**"
        )

    # 1. C1 frente a G1 y P2
    lineas.append("### C1 frente a G1 y P2")
    lineas.append(comparar("C1", "C1", "G1", "G1"))
    lineas.append("")
    lineas.append(comparar("C1", "C1", "P2", "P2"))
    lineas.append("")

    # 2. C2 frente a G3 y P3
    lineas.append("### C2 frente a G3 y P3")
    lineas.append(comparar("C2", "C2", "G3", "G3"))
    lineas.append("")
    lineas.append(comparar("C2", "C2", "P3", "P3"))
    lineas.append("")

    # 3. C3 frente a C1
    lineas.append("### C3 frente a C1")
    lineas.append(comparar("C3", "C3", "C1", "C1"))
    lineas.append("")

    # 4. S0 frente al suelo con linaje
    lineas.append("### S0 frente al suelo con linaje")
    lineas.append(comparar("S0", "S0", "Suelo con linaje", "suelo_linaje"))
    lineas.append("")

    return "\n".join(lineas)


def generar_informe_cierre_paso0() -> str:
    datos = cargar_datos_cierre_paso0()
    cabecera = [
        "# Medición Oficial: Cierre del Paso 0 (Crafter)",
        "",
        "Evaluación oficial en Crafter (100.000 pasos, vista oficial, sin herencia) "
        "en la rama `feature/cierre-paso0` (commit `1ecf254`). "
        "Cierra el Paso 0 y verifica la corrección del bloqueo de acciones probabilísticas.",
        "",
        "Ficheros de datos utilizados (en `datos/evaluacion/`):",
        "- `suelo_main.json`: suelo con linaje (referencia `main` sin estrategias)",
        "- `suelo_sin_herencia.json`: S0 (suelo sin herencia, commit congelado `crafter-procedimental-v1`)",
        "- `paso5_G1.json`: G1 (Paso 5, sin estrategias propias, manual estricto, semilla 31)",
        "- `paso0_P2.json`: P2 (Paso 0, urgencia_local + aliestesia, manual estricto, sin estrategias propias, semilla 31)",
        "- `cierre0_C1.json`: C1 (Cierre Paso 0, sin estrategias propias, manual estricto, semilla 31)",
        "- `cierre0_C3.json`: C3 (Cierre Paso 0, sin estrategias propias, manual estricto, semilla 32)",
        "- `paso5_G3.json`: G3 (Paso 5, manual estricto, con estrategias propias, semilla 31)",
        "- `paso0_P3.json`: P3 (Paso 0, urgencia_local + aliestesia, manual estricto, con estrategias propias, semilla 31)",
        "- `cierre0_C2.json`: C2 (Cierre Paso 0, manual estricto, con estrategias propias, semilla 31)",
        "",
    ]
    partes = [
        "\n".join(cabecera),
        generar_tabla_general_cierre0(datos),
        generar_tasas_logros_cierre0(datos),
        generar_causas_muerte_cierre0(datos),
        generar_comparaciones_cierre0(datos),
    ]
    return "\n\n---\n\n".join(partes) + "\n"


# =====================================================================
# Informe Paso 5 y Paso 0
# =====================================================================

CONDICIONES_PASO5_PASO0 = [
    {
        "id": "suelo",
        "nombre": "Suelo (referencia `main`)",
        "archivo": "suelo_main.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-estrategias-propias",
    },
    {
        "id": "main",
        "nombre": "`main` sin herencia",
        "archivo": "main_sin_herencia.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia",
    },
    {
        "id": "G1",
        "nombre": "G1 (Paso 5)",
        "archivo": "paso5_G1.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --sin-estrategias-propias --manual estricto",
    },
    {
        "id": "G2",
        "nombre": "G2 (Paso 5)",
        "archivo": "paso5_G2.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --sin-estrategias-propias --manual ampliado",
    },
    {
        "id": "G3",
        "nombre": "G3 (Paso 5)",
        "archivo": "paso5_G3.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --manual estricto",
    },
    {
        "id": "G4",
        "nombre": "G4 (Paso 5)",
        "archivo": "paso5_G4.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --manual ampliado",
    },
    {
        "id": "P1",
        "nombre": "P1 (Paso 0)",
        "archivo": "paso0_P1.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --sin-estrategias-propias --manual estricto --mecanismos urgencia_local",
    },
    {
        "id": "P2",
        "nombre": "P2 (Paso 0)",
        "archivo": "paso0_P2.json",
        "opciones": (
            "--pasos 100000 --semilla 31 --vista oficial --sin-herencia "
            "--sin-estrategias-propias --manual estricto --mecanismos urgencia_local aliestesia"
        ),
    },
    {
        "id": "P3",
        "nombre": "P3 (Paso 0)",
        "archivo": "paso0_P3.json",
        "opciones": "--pasos 100000 --semilla 31 --vista oficial --sin-herencia --manual estricto --mecanismos urgencia_local aliestesia",
    },
]

SALIDA_INVARIANCIA = (
    "minimo: OK\n"
    "archivos: OK\n"
    "crafter: semilla 1, latido 1: objetivo 'hierba_31_32' -> 'hierba_32_33' | "
    "semilla 2, latido 1: decisión 'COGER' -> 'MOVER' | semilla 3, latido 1: decisión 'COGER' -> 'MOVER'\n"
    "ajedrez: OK"
)


def cargar_datos_paso5_paso0() -> Dict[str, Dict[str, Any]]:
    datos = {}
    for c in CONDICIONES_PASO5_PASO0:
        ruta = os.path.join(DATOS_DIR, c["archivo"])
        with open(ruta, "r", encoding="utf-8") as f:
            datos[c["id"]] = json.load(f)
    return datos


def generar_tabla_general(datos: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 1. Tabla general",
        "",
        "| Condición | Opciones exactas | Score (%) | IC 95 % (%) | Episodios | Pasos / ep. | Rendimiento (ms/paso) | Latidos cortados |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for c in CONDICIONES_PASO5_PASO0:
        cid = c["id"]
        d = datos[cid]
        score_str = formatear_float_es(d["score"])
        ic_str = f"[{formatear_float_es(d['score_ci_95'][0])}, {formatear_float_es(d['score_ci_95'][1])}]"
        ep = d["episodios"]
        pasos_ep = formatear_float_es(d["pasos"] / ep, 1)
        ms_paso = formatear_float_es(d["ms_por_paso"])
        lineas.append(
            f"| **{c['nombre']}** | `{c['opciones']}` | **{score_str}** | {ic_str} | {ep} | {pasos_ep} | {ms_paso} | {cortados(d)} |"
        )
    return "\n".join(lineas)


def generar_tasas_logros(datos: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 2. Tasas por logro (%)",
        "",
        "Porcentaje de episodios donde se obtuvo cada uno de los 22 logros oficiales de Crafter:",
        "",
        "| Logro | Suelo | `main` | G1 | G2 | G3 | G4 | P1 | P2 | P3 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    todos_logros = sorted(datos["suelo"]["tasas_logros"].keys())
    ids = [c["id"] for c in CONDICIONES_PASO5_PASO0]
    for logro in todos_logros:
        valores = [formatear_float_es(datos[cid]["tasas_logros"].get(logro, 0.0)) for cid in ids]
        lineas.append(f"| `{logro}` | {' | '.join(valores)} |")
    return "\n".join(lineas)


def generar_causas_muerte(datos: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 3. Causas de muerte por condición",
        "",
        "Número de episodios y porcentaje sobre el total de episodios de cada condición:",
        "",
        "| Causa | Suelo | `main` | G1 | G2 | G3 | G4 | P1 | P2 | P3 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    todas_causas = sorted(
        {causa for d in datos.values() for causa in d["causas_muerte"]},
        key=lambda x: (x == "cortado por presupuesto", x),
    )
    ids = [c["id"] for c in CONDICIONES_PASO5_PASO0]
    for causa in todas_causas:
        cols = []
        for cid in ids:
            d = datos[cid]
            n = d["causas_muerte"].get(causa, 0)
            pct = formatear_float_es((n / d["episodios"]) * 100.0, 1)
            cols.append(f"{n} ({pct} %)")
        lineas.append(f"| `{causa}` | {' | '.join(cols)} |")
    totales = [str(datos[cid]["episodios"]) for cid in ids]
    lineas.append(f"| **Total episodios** | **{'** | **'.join(totales)}** |")
    return "\n".join(lineas)


def generar_comparaciones(datos: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 4. Comparaciones",
        "",
        "Diferencias de Crafter Score (en puntos porcentuales) y comprobación de solapamiento de intervalos de confianza al 95 %:",
        "",
    ]

    def comparar(nom_a: str, id_a: str, nom_b: str, id_b: str) -> str:
        da, db = datos[id_a], datos[id_b]
        diff = da["score"] - db["score"]
        signo = "+" if diff >= 0 else ""
        diff_str = f"{signo}{formatear_float_es(diff)} pp"
        ic_a = (da["score_ci_95"][0], da["score_ci_95"][1])
        ic_b = (db["score_ci_95"][0], db["score_ci_95"][1])
        solapa = se_solapan(ic_a, ic_b)
        solapa_str = "Sí" if solapa else "No"
        ic_a_str = f"[{formatear_float_es(ic_a[0])}, {formatear_float_es(ic_a[1])}] %"
        ic_b_str = f"[{formatear_float_es(ic_b[0])}, {formatear_float_es(ic_b[1])}] %"
        return (
            f"- **{nom_a} frente a {nom_b}**:\n"
            f"  - Score {nom_a}: {formatear_float_es(da['score'])} % (IC 95 %: {ic_a_str})\n"
            f"  - Score {nom_b}: {formatear_float_es(db['score'])} % (IC 95 %: {ic_b_str})\n"
            f"  - Diferencia de Score ({nom_a} - {nom_b}): {diff_str}\n"
            f"  - ¿Se solapan los IC 95 %?: **{solapa_str}**"
        )

    # 1. G1 frente al suelo
    lineas.append("### G1 frente al suelo")
    lineas.append(comparar("G1", "G1", "Suelo (`main`)", "suelo"))
    lineas.append("")

    # 2. G3 y G4 frente a main
    lineas.append("### G3 y G4 frente a `main` sin herencia")
    lineas.append(comparar("G3", "G3", "`main` sin herencia", "main"))
    lineas.append("")
    lineas.append(comparar("G4", "G4", "`main` sin herencia", "main"))
    lineas.append("")

    # 3. P1 y P2 frente a G1
    lineas.append("### P1 y P2 frente a G1")
    lineas.append(comparar("P1", "P1", "G1", "G1"))
    lineas.append("")
    lineas.append(comparar("P2", "P2", "G1", "G1"))
    lineas.append("")

    # 4. P3 frente a G3
    lineas.append("### P3 frente a G3")
    lineas.append(comparar("P3", "P3", "G3", "G3"))
    lineas.append("")

    return "\n".join(lineas)


def generar_seccion_invariancia() -> str:
    lineas = [
        "## 5. Salida literal de `invariancia.py`",
        "",
        "```",
        SALIDA_INVARIANCIA,
        "```",
    ]
    return "\n".join(lineas)


def generar_informe_paso5_paso0() -> str:
    datos = cargar_datos_paso5_paso0()
    cabecera = [
        "# Medición Oficial: Paso 5 y Paso 0 (Crafter)",
        "",
        "Evaluación oficial en Crafter (100.000 pasos, semilla base 31, vista oficial, sin herencia) "
        "en la rama `feature/paso0` (commit `43f636c`).",
        "",
        "Ficheros de datos utilizados (en `datos/evaluacion/`):",
        "- `suelo_main.json`: suelo de referencia (`main` sin estrategias)",
        "- `main_sin_herencia.json`: referencia `main` con estrategias y sin herencia",
        "- `paso5_G1.json`: G1 (Paso 5, sin estrategias propias, manual estricto)",
        "- `paso5_G2.json`: G2 (Paso 5, sin estrategias propias, manual ampliado)",
        "- `paso5_G3.json`: G3 (Paso 5, manual estricto)",
        "- `paso5_G4.json`: G4 (Paso 5, manual ampliado)",
        "- `paso0_P1.json`: P1 (Paso 0, urgencia_local, manual estricto, sin estrategias propias)",
        "- `paso0_P2.json`: P2 (Paso 0, urgencia_local + aliestesia, manual estricto, sin estrategias propias)",
        "- `paso0_P3.json`: P3 (Paso 0, urgencia_local + aliestesia, manual estricto, con estrategias)",
        "",
    ]
    partes = [
        "\n".join(cabecera),
        generar_tabla_general(datos),
        generar_tasas_logros(datos),
        generar_causas_muerte(datos),
        generar_comparaciones(datos),
        generar_seccion_invariancia(),
    ]
    return "\n\n---\n\n".join(partes) + "\n"


# =====================================================================
# Informe oficial general (retrocompatibilidad con MEDICION_OFICIAL.md)
# =====================================================================

def generar_seccion_3_oficial(datos_crafter: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 3. Comparación global Crafter (100.000 pasos)",
        "",
        "| Condición | Score Crafter (IC 95 %) | Episodios | Pasos / episodio | Rendimiento (ms/paso) | Tiempo total (s) |",
        "|---|---|---|---|---|---|",
    ]
    etiquetas = [
        ("suelo", "**Suelo (`main` sin estrategias)**"),
        ("techo_main", "**Techo `main` (con linaje)**"),
        ("sin_herencia", "**`main` sin herencia**"),
        ("techo_c3d", "**Techo C.3d (`feature/crafter-fase-c`)**"),
    ]
    for clave, etiqueta in etiquetas:
        d = datos_crafter[clave]
        score_str = formatear_float_es(d["score"])
        ic_inf_str = formatear_float_es(d["score_ci_95"][0])
        ic_sup_str = formatear_float_es(d["score_ci_95"][1])
        ep = d["episodios"]
        pasos_ep_str = formatear_float_es(d["pasos"] / ep, 1)
        ms_str = formatear_float_es(d["ms_por_paso"])
        t_str = formatear_float_es(d["tiempo_segundos"], 1)
        lineas.append(
            f"| {etiqueta} | **{score_str} %** [{ic_inf_str}, {ic_sup_str}] % | {ep} | {pasos_ep_str} | {ms_str} ms | {t_str} s |"
        )
    return "\n".join(lineas)


def generar_seccion_4_oficial(datos_crafter: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 4. Tasa de éxito por logro (%)",
        "",
        "Fracción de episodios en que se consiguió el logro al menos una vez (sobre el total de episodios de cada condición):",
        "",
        "| Logro | Suelo (`main`) | Techo `main` | `main` sin herencia | Techo C.3d |",
        "|---|---|---|---|---|",
    ]
    todos_logros = sorted(datos_crafter["techo_main"]["tasas_logros"].keys())
    for logro in todos_logros:
        s = formatear_float_es(datos_crafter["suelo"]["tasas_logros"].get(logro, 0.0))
        tm = formatear_float_es(datos_crafter["techo_main"]["tasas_logros"].get(logro, 0.0))
        sh = formatear_float_es(datos_crafter["sin_herencia"]["tasas_logros"].get(logro, 0.0))
        tc = formatear_float_es(datos_crafter["techo_c3d"]["tasas_logros"].get(logro, 0.0))
        lineas.append(f"| `{logro}` | {s} % | {tm} % | {sh} % | {tc} % |")
    return "\n".join(lineas)


def generar_seccion_5_oficial(datos_crafter: Dict[str, Dict[str, Any]]) -> str:
    lineas = [
        "## 5. Causas de muerte / finalización por condición",
        "",
        "| Causa de muerte | Suelo (`main`) | Techo `main` | `main` sin herencia | Techo C.3d |",
        "|---|---|---|---|---|",
    ]
    todas_causas = sorted(
        {c for d in datos_crafter.values() for c in d["causas_muerte"]},
        key=lambda x: (x == "cortado por presupuesto", x),
    )
    for causa in todas_causas:
        cols = []
        for clave in ("suelo", "techo_main", "sin_herencia", "techo_c3d"):
            d = datos_crafter[clave]
            n = d["causas_muerte"].get(causa, 0)
            pct = formatear_float_es((n / d["episodios"]) * 100.0, 1)
            cols.append(f"{n} ({pct} %)")
        lineas.append(f"| `{causa}` | {' | '.join(cols)} |")
    totales = [str(datos_crafter[k]["episodios"]) for k in ("suelo", "techo_main", "sin_herencia", "techo_c3d")]
    lineas.append(f"| **Total episodios** | **{'** | **'.join(totales)}** |")
    return "\n".join(lineas)


def generar_seccion_6_oficial(f_minimo: Dict[str, Any], f_archivos: Dict[str, Any]) -> str:
    intro = (
        "Línea base registrada sobre `main` (4 grupos: Equilibrado, Valiente, Reactivo, Sin experiencia; semillas 1 a 10; "
        "4 generaciones de 400 latidos por celda = 160 vidas por mundo). "
        "Datos procedentes de `datos/evaluacion/ref_generalizacion_minimo.json` y `datos/evaluacion/ref_generalizacion_archivos.json`:"
    )
    encabezado = (
        "| Mundo | Celdas ejecutadas | Vidas totales | Vidas vivas (400 lat.) | Latidos/vida (media / med.) | "
        "Fitness/vida (media / med.) | Muertes por causa | Rendimiento |"
    )
    lineas = [
        "## 6. Referencia de generalización (`ref_generalizacion`)",
        "",
        intro,
        "",
        encabezado,
        "|---|---|---|---|---|---|---|---|",
    ]
    for mundo_nombre, d in (("minimo", f_minimo), ("archivos", f_archivos)):
        n_celdas = len(d["filas"])
        total_vidas = sum(len(r["vidas"]) for r in d["filas"])
        latidos_todas = [v["latidos"] for r in d["filas"] for v in r["vidas"]]
        fitness_todas = [v["fitness"] for r in d["filas"] for v in r["vidas"]]
        causas: Dict[str, int] = {}
        for r in d["filas"]:
            for c in r["causas"]:
                causas[c] = causas.get(c, 0) + 1
        vivas = causas.get("vive", 0)
        vivas_pct_str = formatear_float_es((vivas / total_vidas) * 100.0, 1)
        lat_med_str = formatear_float_es(statistics.fmean(latidos_todas), 1)
        lat_mdn_str = formatear_float_es(statistics.median(latidos_todas), 1)
        fit_med_str = formatear_float_es(statistics.fmean(fitness_todas), 2)
        fit_mdn_str = formatear_float_es(statistics.median(fitness_todas), 2)
        muertes_str = (
            ", ".join(f"{c}: {n}" for c, n in sorted(causas.items(), key=lambda kv: -kv[1]) if c != "vive")
            or "Ninguna"
        )
        t_total_ms = sum(r["indicadores"].get("ms", 0.0) for r in d["filas"])
        latidos_sum = sum(latidos_todas)
        ms_latido_str = formatear_float_es(t_total_ms / latidos_sum if latidos_sum else 0.0, 2)
        lineas.append(
            f"| **`{mundo_nombre}`** | {n_celdas} / {n_celdas} (100 %) | {total_vidas} | {vivas} ({vivas_pct_str} %) | "
            f"{lat_med_str} / {lat_mdn_str} | {fit_med_str} / {fit_mdn_str} | {muertes_str} | {ms_latido_str} ms/latido |"
        )
    lineas.append("| **`ajedrez`** | — | — | — | — | — | Invariancia: **OK** | — |")
    return "\n".join(lineas)


def generar_markdown_oficial() -> str:
    archivos = {
        "suelo": os.path.join(DATOS_DIR, "suelo_main.json"),
        "techo_main": os.path.join(DATOS_DIR, "techo_main.json"),
        "sin_herencia": os.path.join(DATOS_DIR, "main_sin_herencia.json"),
        "techo_c3d": os.path.join(DATOS_DIR, "techo_c3d.json"),
    }
    datos_crafter = {k: json.load(open(v, encoding="utf-8")) for k, v in archivos.items()}
    f_minimo = json.load(open(os.path.join(DATOS_DIR, "ref_generalizacion_minimo.json"), encoding="utf-8"))
    f_archivos = json.load(open(os.path.join(DATOS_DIR, "ref_generalizacion_archivos.json"), encoding="utf-8"))

    s3 = generar_seccion_3_oficial(datos_crafter)
    s4 = generar_seccion_4_oficial(datos_crafter)
    s5 = generar_seccion_5_oficial(datos_crafter)
    s6 = generar_seccion_6_oficial(f_minimo, f_archivos)

    return f"{s3}\n\n---\n\n{s4}\n\n---\n\n{s5}\n\n---\n\n{s6}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paso6",
        action="store_true",
        help="Genera el informe del Paso 6 (MEDICION_PASO6.md, por defecto)",
    )
    parser.add_argument(
        "--cierre-paso3",
        action="store_true",
        help="Genera el informe de cierre del Paso 3 (MEDICION_CIERRE_PASO3.md)",
    )
    parser.add_argument(
        "--paso3",
        action="store_true",
        help="Genera el informe exploratorio del Paso 3 (MEDICION_PASO3.md)",
    )
    parser.add_argument(
        "--cierre-paso0",
        action="store_true",
        help="Genera el informe de cierre del Paso 0",
    )
    parser.add_argument(
        "--paso5-paso0",
        action="store_true",
        help="Genera el informe de Paso 5 y Paso 0 (MEDICION_PASO5_PASO0.md)",
    )
    parser.add_argument(
        "--oficial",
        action="store_true",
        help="Genera las secciones 3 a 6 para MEDICION_OFICIAL.md",
    )
    parser.add_argument(
        "--pareada",
        nargs=2,
        metavar=("A", "B"),
        default=None,
        help="Compara episodio a episodio dos JSON de la misma semilla base (diferencia A - B con IC pareado)",
    )
    parser.add_argument(
        "--pareada-conjunta",
        nargs="+",
        metavar="JSON",
        default=None,
        help="Pares A1 B1 A2 B2 ... (cada par de la misma semilla base): diferencia A - B con los episodios pareados de "
             "todas las semillas juntos e IC por bootstrap pareado estratificado por semilla",
    )
    parser.add_argument(
        "--salida",
        type=str,
        default=None,
        help="Ruta donde guardar el markdown generado",
    )
    args = parser.parse_args()

    if args.pareada_conjunta:
        if len(args.pareada_conjunta) % 2:
            print("No se puede comparar: --pareada-conjunta necesita pares A B")
            return 1
        datos = []
        for ruta in args.pareada_conjunta:
            with open(ruta, encoding="utf-8") as fh:
                datos.append(json.load(fh))
        try:
            res = comparar_pareado_conjunto([(datos[i], datos[i + 1]) for i in range(0, len(datos), 2)])
        except ValueError as exc:
            print(f"No se puede comparar: {exc}")
            return 1
        nombres = [os.path.splitext(os.path.basename(r))[0] for r in args.pareada_conjunta]
        salida = generar_tabla_pareada_conjunta([(nombres[i], nombres[i + 1]) for i in range(0, len(nombres), 2)], res)
    elif args.pareada:
        datos = []
        for ruta in args.pareada:
            with open(ruta, encoding="utf-8") as fh:
                datos.append(json.load(fh))
        try:
            res = comparar_pareado(datos[0], datos[1])
        except ValueError as exc:
            print(f"No se puede comparar: {exc}")
            return 1
        nombres = [os.path.splitext(os.path.basename(r))[0] for r in args.pareada]
        salida = generar_tabla_pareada(nombres[0], nombres[1], res)
    elif args.oficial:
        salida = generar_markdown_oficial()
    elif args.paso5_paso0:
        salida = generar_informe_paso5_paso0()
    elif args.cierre_paso0:
        salida = generar_informe_cierre_paso0()
    elif args.paso3:
        salida = generar_informe_paso3()
    elif args.cierre_paso3:
        salida = generar_informe_cierre_paso3()
    else:
        salida = generar_informe_paso6()

    if args.salida:
        os.makedirs(os.path.dirname(os.path.abspath(args.salida)), exist_ok=True)
        with open(args.salida, "w", encoding="utf-8") as f:
            f.write(salida)

    print(salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
