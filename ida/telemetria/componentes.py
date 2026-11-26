"""Mapa de Componentes para el Laboratorio (T5a, O13): ``doc-repositorio/componentes.toml`` servido por la API.

La misma fuente que los diagramas 06 y 07 (``herramientas/mapa_componentes.py``): nada se copia a mano. Para cada
elemento da sus campos de la especificación (con ``analogo`` y ``descripcion`` en es/en), su clave en los tiempos del
registro del latido (``tiempos_ms``) y en qué mundos se monta. Para cada decisión citada, su título y su texto en
``docs/DISENO_COMPONENTES.md`` (en español: el documento de diseño solo existe en español).

Si la instalación no trae ``doc-repositorio/`` ni ``docs/`` (un ``pip install`` que no sea editable), el catálogo no
está disponible: la API lo dice (``componentes_no_disponibles``) y el Laboratorio enseña los tiempos sin fichas.
"""

import os
import re
import threading
import tomllib
from typing import Any, Dict, List, Optional, Tuple

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ESPEC = os.path.join(RAIZ, "doc-repositorio", "componentes.toml")
DISENO = os.path.join(RAIZ, "docs", "DISENO_COMPONENTES.md")
# Los mundos del mapa (los de ``herramientas/mapa_componentes.py``, en su orden).
MUNDOS_MAPA = ("minimo", "archivos", "snake", "ajedrez", "crafter")

_cerrojo = threading.Lock()
_cache: Dict[str, Any] = {"clave": None, "datos": None}


class SinCatalogo(Exception):
    """La instalación no trae la especificación (``doc-repositorio/componentes.toml``)."""


def objetivo_en(c: Dict[str, Any]) -> Any:
    if c["clase"] == "general":
        return "todos"
    if c["clase"] == "mundo":
        return [c["dueno"]]
    return list(c.get("registran", []))


def montado_en(c: Dict[str, Any], mundo: str, espec: List[Dict[str, Any]]) -> bool:
    """Si ``mundo`` monta este elemento en su destino, con las sustituciones aplicadas (la misma regla que
    ``mapa_componentes.montado_en``; lo comprueba ``tests/test_laboratorio.py``)."""
    if c["clase"] == "general":
        return not any(
            o.get("sustituye") == c["nombre"] and o["destino"] == c["destino"] and montado_en(o, mundo, espec) for o in espec
        )
    return bool(mundo) and mundo in objetivo_en(c)


def ubicacion(c: Dict[str, Any]) -> Tuple[str, str]:
    """(sistema, módulo): ``("CORE", "Sentir")``, ``("S1", "Reaccionar")``... o ``("cuerpo", "")``."""
    if c["destino"] == "cuerpo":
        return "cuerpo", ""
    sistema, modulo = c["destino"].split(".")
    return sistema, modulo


def clave_tiempo(c: Dict[str, Any]) -> Optional[str]:
    """La clave del elemento en ``tiempos_ms``: ``CORE.Interocepcion``, ``preatencion:S1.Saliencia``, ``S2.Valor``; el
    Actuador mide por verbo (``CORE.Actuador_<VERBO>``) y lo agrupa la interfaz. Las estrategias corren dentro de
    ``Estrategia`` y las bibliotecas dentro de quien las usa: no tienen tiempo propio."""
    if c["tipo"] != "componente":
        return None
    sistema, _ = ubicacion(c)
    if c.get("preatentivo"):
        return f"preatencion:{sistema}.{c['nombre']}"
    return f"{sistema}.{c['nombre']}"


def decisiones(ruta: str = DISENO) -> Dict[str, Dict[str, str]]:
    """``{D<n>: {titulo, texto}}`` de ``docs/DISENO_COMPONENTES.md``: las secciones ``### D<n>. Título`` y, para D1,
    la sección «El latido (D1)»."""
    with open(ruta, encoding="utf-8") as f:
        texto = f.read()
    salida: Dict[str, Dict[str, str]] = {}
    for m in re.finditer(r"^### (D\d+)\. (.+?)\n(.*?)(?=^### |^## |\Z)", texto, flags=re.MULTILINE | re.DOTALL):
        salida[m.group(1)] = {"titulo": m.group(2).strip(), "texto": m.group(3).strip()}
    d1 = re.search(r"^## \d+\. El latido \(D1\)\n(.*?)(?=^## |\Z)", texto, flags=re.MULTILINE | re.DOTALL)
    if d1:
        salida["D1"] = {"titulo": "El latido", "texto": d1.group(1).strip()}
    return salida


def _construir() -> Dict[str, Any]:
    with open(ESPEC, "rb") as f:
        espec = list(tomllib.load(f)["componente"])
    dec = decisiones() if os.path.exists(DISENO) else {}
    componentes = []
    for c in espec:
        sistema, modulo = ubicacion(c)
        componentes.append({
            "nombre": c["nombre"], "tipo": c["tipo"], "clase": c["clase"], "dueno": c.get("dueno"),
            "destino": c["destino"], "hoy": c["hoy"], "sistema": sistema, "modulo": modulo,
            "preatentivo": bool(c.get("preatentivo")), "aprende": bool(c.get("aprende")),
            "decision": c["decision"], "sustituye": c.get("sustituye"), "nota": c.get("nota", ""),
            "analogo": dict(c.get("analogo") or {"es": "", "en": ""}),
            "descripcion": dict(c.get("descripcion") or {"es": "", "en": ""}),
            "clave_tiempo": clave_tiempo(c),
            "mundos": [m for m in MUNDOS_MAPA if montado_en(c, m, espec)],
            "nucleo": montado_en(c, "", espec),
        })
    citadas = {c["decision"] for c in componentes if c["decision"] != "previo"} | {"D1", "D5", "D6", "D12", "D14"}
    return {"componentes": componentes, "decisiones": {k: v for k, v in dec.items() if k in citadas},
            "mundos": list(MUNDOS_MAPA)}


def catalogo() -> Dict[str, Any]:
    """El catálogo, leído de nuevo si la especificación o el diseño cambian en disco."""
    if not os.path.exists(ESPEC):
        raise SinCatalogo(ESPEC)
    clave = (os.path.getmtime(ESPEC), os.path.getmtime(DISENO) if os.path.exists(DISENO) else 0.0)
    with _cerrojo:
        if _cache["clave"] != clave:
            _cache["datos"] = _construir()
            _cache["clave"] = clave
        return dict(_cache["datos"])
