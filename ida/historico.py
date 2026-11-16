"""Gestión del histórico de linajes, cálculo de fitness y política de retención.

Permite conservar las 5 mejores generaciones de todos los tiempos según fitness,
las generaciones fijadas por el usuario (📌) y las más recientes hasta un máximo
de 20 generaciones en total. Proporciona además exportación y restauración reproducible.
"""

import json
import os
from typing import Any, Dict, List, Optional, Set

MAX_GENERACIONES: int = 20
TOP_K_FITNESS: int = 5


def calcular_fitness(mundo: str, gen: Dict[str, Any]) -> float:
    """Calcula un valor escalar de fitness para una generación según el mundo."""
    pt = gen.get("puntuacion") or {}
    latidos = float(gen.get("latidos", 0))

    if mundo == "snake":
        pts = float(pt.get("puntos", 0))
        longitud = float(pt.get("longitud", 0))
        # Puntos primarios, longitud y latidos como desempate
        return pts * 10.0 + longitud * 2.0 + (latidos * 0.01)

    elif mundo == "crafter":
        logros = pt.get("logros") or []
        n_logros = float(pt.get("n_logros", len(logros)))
        pasos = float(pt.get("pasos", latidos))
        return n_logros * 1000.0 + pasos

    elif mundo == "ajedrez":
        res = str(pt.get("resultado", "")).upper()
        base = 2000.0 if "VICTORIA" in res else (1000.0 if "TABLAS" in res else 100.0)
        mat = pt.get("material", [0, 0])
        diff_mat = float(mat[0] - mat[1]) if isinstance(mat, (list, tuple)) and len(mat) >= 2 else 0.0
        jugadas = float(pt.get("jugadas", 0))
        return base + diff_mat * 50.0 + jugadas

    elif mundo == "archivos":
        comido = pt.get("comido") or {}
        if "nutritivos" in pt or "toxicos" in pt:
            sanos = float(pt.get("nutritivos", 0))
            toxicos = float(pt.get("toxicos", 0))
            return max(0.0, sanos * 50.0 - toxicos * 100.0 + latidos * 2.0)
        total_comido = float(sum(comido.values())) if isinstance(comido, dict) else 0.0
        return total_comido * 50.0 + latidos

    elif mundo == "minimo":
        bayas = float(pt.get("bayas", 0))
        setas = float(pt.get("setas", 0))
        return bayas * 20.0 + setas * 5.0 + latidos

    return latidos


def rasgo_dominante(arquetipo: Dict[str, Any]) -> Dict[str, Any]:
    """Determina el rasgo predominante o más destacado de un arquetipo."""
    etiquetas = {
        "apertura": ("Curioso / Explorador", "Apertura"),
        "responsabilidad": ("Prudente / Metódico", "Responsabilidad"),
        "neuroticismo": ("Reactivo / Alerta", "Neuroticismo"),
        "extraversion": ("Sociable / Activo", "Extraversión"),
        "umbral_miedo": ("Resiliente / Impertérrito", "Umbral de miedo"),
    }
    mejor_rasgo = "apertura"
    max_val = -1.0
    for r, (_, _) in etiquetas.items():
        v = float(arquetipo.get(r, 0.5))
        if v > max_val:
            max_val = v
            mejor_rasgo = r

    desc, nombre = etiquetas[mejor_rasgo]
    return {"rasgo": mejor_rasgo, "nombre": nombre, "descripcion": desc, "valor": round(max_val, 3)}


def aplicar_politica_retencion(
    mundo: str,
    generaciones: List[Dict[str, Any]],
    max_total: int = MAX_GENERACIONES,
    top_k: int = TOP_K_FITNESS,
) -> List[Dict[str, Any]]:
    """Aplica selección natural por fitness: elimina por abajo los peores, respetando fijados."""
    if not generaciones:
        return []

    # Enriquecer cada generación con su fitness y marcas si no lo tienen
    for g in generaciones:
        if "fitness" not in g or g["fitness"] is None:
            g["fitness"] = round(calcular_fitness(mundo, g), 2)
        if "fijado" not in g:
            g["fijado"] = False

    if len(generaciones) <= max_total:
        return sorted(generaciones, key=lambda x: float(x.get("fitness", 0.0)), reverse=True)

    # 1. Identificar fijados por el usuario (protegidos contra selección natural)
    fijados_ids: Set[str] = {g["individuo"] for g in generaciones if g.get("fijado")}

    # 2. Ordenar por fitness descendente (los mejores primero, los peores abajo)
    ordenados = sorted(generaciones, key=lambda x: float(x.get("fitness", 0.0)), reverse=True)

    # 3. Conservar fijados y los mejores no fijados hasta completar max_total
    a_conservar: Set[str] = set(fijados_ids)
    for g in ordenados:
        if len(a_conservar) >= max_total:
            break
        a_conservar.add(g["individuo"])

    # 4. Retornar los supervivientes ordenados por fitness descendente
    supervivientes = [g for g in generaciones if g["individuo"] in a_conservar]
    return sorted(supervivientes, key=lambda x: float(x.get("fitness", 0.0)), reverse=True)


def ruta_linaje(mundo: str, datos_dir: Optional[str] = None) -> str:
    """Ruta al archivo linaje.json de un mundo."""
    base = datos_dir or os.path.join("datos", mundo)
    return os.path.join(base, "linaje.json")


def cargar_linaje(mundo: str, datos_dir: Optional[str] = None) -> Dict[str, Any]:
    """Carga y enriquece el linaje de un mundo con marcas de ranking (top 1, top 5)."""
    ruta = ruta_linaje(mundo, datos_dir)
    if not os.path.exists(ruta):
        return {"generaciones": [], "arquetipo": None, "legado": {}}

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except Exception:
        return {"generaciones": [], "arquetipo": None, "legado": {}}

    generaciones = datos.get("generaciones", [])
    for g in generaciones:
        g["fitness"] = round(calcular_fitness(mundo, g), 2)
        if "fijado" not in g:
            g["fijado"] = False
        arq = g.get("arquetipo", {})
        g["dominante"] = rasgo_dominante(arq)

    # Ordenar por fitness descendente (el mejor arriba, el peor abajo)
    generaciones.sort(key=lambda x: float(x.get("fitness", 0.0)), reverse=True)

    # Añadir flags de ranking para visualización
    if generaciones:
        top1_id = generaciones[0]["individuo"]
        top5_ids = {g["individuo"] for g in generaciones[:TOP_K_FITNESS]}
        for g in generaciones:
            g["es_top1"] = (g["individuo"] == top1_id)
            g["es_top5"] = (g["individuo"] in top5_ids)

    datos["generaciones"] = generaciones
    return datos


def guardar_linaje_con_retencion(
    mundo: str,
    datos: Dict[str, Any],
    datos_dir: Optional[str] = None,
    max_total: int = MAX_GENERACIONES,
    top_k: int = TOP_K_FITNESS,
) -> None:
    """Aplica la retención y guarda el archivo linaje.json."""
    generaciones = datos.get("generaciones", [])
    retenidas = aplicar_politica_retencion(mundo, generaciones, max_total=max_total, top_k=top_k)
    datos["generaciones"] = retenidas

    ruta = ruta_linaje(mundo, datos_dir)
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def conmutar_fijado(mundo: str, individuo_id: str, fijado: Optional[bool] = None, datos_dir: Optional[str] = None) -> bool:
    """Fija o desfija un individuo en linaje.json para evitar su purga por retención."""
    ruta = ruta_linaje(mundo, datos_dir)
    if not os.path.exists(ruta):
        return False

    with open(ruta, "r", encoding="utf-8") as f:
        datos = json.load(f)

    nuevo_estado = False
    encontrado = False
    for g in datos.get("generaciones", []):
        if g.get("individuo") == individuo_id:
            actual = bool(g.get("fijado", False))
            nuevo_estado = (not actual) if fijado is None else bool(fijado)
            g["fijado"] = nuevo_estado
            encontrado = True
            break

    if encontrado:
        guardar_linaje_con_retencion(mundo, datos, datos_dir=datos_dir)

    return nuevo_estado


def exportar_individuo(mundo: str, individuo_id: str, datos_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Exporta el snapshot completo y reproducible de un individuo específico."""
    lin = cargar_linaje(mundo, datos_dir)
    for g in lin.get("generaciones", []):
        if g.get("individuo") == individuo_id:
            return {
                "tipo": "ida_individuo_v1",
                "mundo": mundo,
                "individuo": individuo_id,
                "generacion": g.get("arquetipo", {}).get("generacion", 1),
                "arquetipo": g.get("arquetipo"),
                "fitness": g.get("fitness"),
                "puntuacion": g.get("puntuacion"),
                "latidos": g.get("latidos"),
                "vivo": g.get("vivo"),
                "vitalidad": g.get("vitalidad"),
                "conocimiento": g.get("conocimiento", []),
                "legado": lin.get("legado", {}),
                "dominante": g.get("dominante"),
            }
    return None


def exportar_linaje_completo(mundo: str, datos_dir: Optional[str] = None) -> Dict[str, Any]:
    """Exporta el linaje completo para descarga y archivo."""
    lin = cargar_linaje(mundo, datos_dir)
    return {
        "tipo": "ida_linaje_completo_v1",
        "mundo": mundo,
        "arquetipo_actual": lin.get("arquetipo"),
        "legado": lin.get("legado", {}),
        "generaciones": lin.get("generaciones", []),
    }
