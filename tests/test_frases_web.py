"""Frases del Vivero (T4a, O5, O16): plantillas de hechos y etiquetas de las clases de cada mundo, en es y en.

- Cada mundo tiene ``web/i18n/clases/<mundo>.json`` con sus clases (forma con artículo definido e indefinido y, en
  español, su género), sus frases de acción, sus logros y las claves de su puntuación, en los dos idiomas.
- **Cobertura:** toda clase que un mundo emite en su escena o en sus hechos tiene etiqueta. Las clases se buscan de dos
  formas: las que declara el código del mundo (tablas del adaptador, manual de Crafter, índice de sprites) y las que
  salen de verdad en una vida corta de cada mundo que se puede lanzar sin red (mínimo, archivos, Crafter y ajedrez;
  Snake necesita la web real).
- Las plantillas comunes (``web/i18n/es.json`` y ``en.json``) cubren cada tipo de hecho del catálogo v1, cada verbo,
  cada relación, cada estrategia (plan) y cada impulso o necesidad (motivo).
"""

import importlib
import json
import os
import pkgutil
import re

import pytest

import ida
from ida.ejecutor import ejecutar
from ida.mundos import MUNDOS, cargar
from ida.nucleo.estrategia import Definicion
from ida.nucleo.vocabulario import Relacion, Verbo
from ida.telemetria.esquema import HECHOS
from ida.telemetria.servidor import WEB

CLASES = os.path.join(WEB, "i18n", "clases")
IDIOMAS = ("es", "en")
MARCAS = re.compile(r"\{(\w+)\}")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


ES, EN = _leer(os.path.join(WEB, "i18n", "es.json")), _leer(os.path.join(WEB, "i18n", "en.json"))
ETIQUETAS = {m: _leer(os.path.join(CLASES, f"{m}.json")) for m in MUNDOS if os.path.exists(os.path.join(CLASES, f"{m}.json"))}


# --- forma de los ficheros por mundo ---------------------------------------------------------------------------------
def test_cada_mundo_tiene_sus_etiquetas():
    assert set(ETIQUETAS) == set(MUNDOS)
    for m, d in ETIQUETAS.items():
        assert d["mundo"] == m and isinstance(d["clases"], dict) and d["clases"], m


@pytest.mark.parametrize("mundo", sorted(MUNDOS))
def test_etiquetas_completas_en_los_dos_idiomas(mundo):
    d = ETIQUETAS[mundo]
    for clase, e in d["clases"].items():
        for i in IDIOMAS:
            assert e[i]["el"].strip() and e[i]["un"].strip(), (mundo, clase, i)
        assert e["es"]["g"] in ("m", "f"), (mundo, clase)
    for clave, a in d.get("acciones", {}).items():
        for forma in ("inf", "pres"):
            es, en = a["es"][forma], a["en"][forma]
            assert es.strip() and en.strip(), (mundo, clave, forma)
            assert set(MARCAS.findall(es)) == set(MARCAS.findall(en)) <= {"el", "un", "objetivo"}, (mundo, clave, forma)
    for seccion in ("logros", "puntos", "valores"):
        for clave, textos in d.get(seccion, {}).items():
            assert all(textos.get(i, "").strip() for i in IDIOMAS), (mundo, seccion, clave)


# --- cobertura: clases que declara el código de cada mundo ----------------------------------------------------------
def _sprites(mundo):
    ruta = os.path.join(WEB, "sprites", mundo, "indice.json")
    if not os.path.exists(ruta):
        return set()
    claves = _leer(ruta)["mapa_sprites"]
    return {k.split(".")[0] for k in claves if k != "?" and not k.startswith("yo")}


def _declaradas(mundo):
    clases = set(_sprites(mundo))
    if mundo == "crafter":
        from ida.mundos.crafter import adaptador as a
        clases |= set(a.MATERIALES.values()) | set(a.OBJETOS.values()) | set(a.SUELOS.values())
        clases |= set(a.INVENTARIO) | set(a.INVENTARIO.values()) | set(a.VITALES_JUEGO) | set(a.VITALES_JUEGO.values())
        clases.add("suelo")
        for nombre in a.MANUALES.values():
            for h in _leer(os.path.join(os.path.dirname(a.__file__), nombre))["hechos"]:
                clases |= {h[k] for k in ("sujeto", "objetivo") if h.get(k)}
                clases |= set(h.get("requiere_inventario") or {}) | set(h.get("requiere_cerca") or [])
    elif mundo == "ajedrez":
        from ida.mundos import ajedrez as a
        piezas = set(a.NOMBRE.values())
        clases |= piezas | {f"captura_{p}" for p in piezas} | {f"{p}_atacado" for p in piezas}
        clases |= {"jaque", "jaque_recibido", "jaque_mate", "enroque"}
    elif mundo == "archivos":
        from ida.mundos.archivos import adaptador as a
        clases |= {a.clase_de(n) for n in (*a.COMESTIBLES, *a.TOXICOS, *a.AMBIENTE)} | {"brote", "depredador", "mensaje", "carpeta", "raiz"}
    elif mundo == "snake":
        clases |= {"fondo", "cuerpo", "comida", "casilla", "pared"}   # escena() y las Entidad de observar()
    elif mundo == "minimo":
        clases |= {"pradera", "baya", "seta", "piedra", "lobo"}
    return clases


@pytest.mark.parametrize("mundo", sorted(MUNDOS))
def test_clases_declaradas_tienen_etiqueta(mundo):
    faltan = sorted(_declaradas(mundo) - set(ETIQUETAS[mundo]["clases"]))
    assert not faltan, (mundo, faltan)


def test_logros_de_crafter_tienen_etiqueta():
    constantes = pytest.importorskip("crafter.constants")
    assert set(constantes.achievements) == set(ETIQUETAS["crafter"]["logros"])
    assert ETIQUETAS["crafter"]["total_logros"] == len(constantes.achievements)


# --- cobertura: clases que salen de verdad en una vida corta ---------------------------------------------------------
VIDAS = {"minimo": ({}, 300), "archivos": ({}, 300), "ajedrez": ({}, 150),
         "crafter": ({"vista": "oficial", "longitud": 10000}, 400)}


def _emitidas(mundo, tmp_path):
    opciones, latidos = VIDAS[mundo]
    clases, puntos, causas = set(), set(), set()

    def al_latir(o, onda, r):
        e = r.get("escena")
        if e:
            for fila in e.get("celdas", []):
                clases.update(c for c in fila if c)
            for x in e.get("entidades", []) + e.get("nodos", []) + e.get("piezas", []):
                clases.add(x["clase"])
            clases.update(e.get("inventario", {}))
        if r["accion"] and r["accion"]["clase"]:
            clases.add(r["accion"]["clase"])
        for h in r["hechos"]:
            if h.get("clase"):
                clases.add(h["clase"])
            clases.update(h.get("requiere") or {})
            clases.update(h.get("efecto") or {})
            clases.update(h.get("cerca") or [])
            if h["tipo"] == "muere":
                causas.add(h["causa"])
        clases.update(p["sujeto"] for p in r.get("saber", []))
        puntos.update(r["score"]["puntuacion"])

    ejecutar(mundo, latidos=latidos, semilla=31, consola=False, datos=str(tmp_path / mundo), plazo_logico=40.0,
             nivel="cognitivo", opciones_mundo=opciones, al_latir=al_latir)
    return clases, puntos, causas


@pytest.mark.parametrize("mundo", sorted(VIDAS))
def test_clases_emitidas_en_una_vida_tienen_etiqueta(mundo, tmp_path):
    if mundo in ("crafter", "ajedrez"):
        pytest.importorskip("crafter" if mundo == "crafter" else "chess")
    clases, puntos, causas = _emitidas(mundo, tmp_path)
    d = ETIQUETAS[mundo]
    assert clases, mundo
    assert not sorted(clases - set(d["clases"])), (mundo, sorted(clases - set(d["clases"])))
    assert not sorted(puntos - set(d["puntos"])), (mundo, sorted(puntos - set(d["puntos"])))
    for causa in causas:   # una causa de muerte es una clase del mundo o una necesidad (muerte.<n>)
        assert causa in d["clases"] or f"muerte.{causa}" in ES, (mundo, causa)


# --- plantillas comunes ----------------------------------------------------------------------------------------------
PLANTILLAS_HECHO = {
    "nace": ["hecho.nace"], "primera_vez": ["hecho.primera_vez"], "aprende": ["hecho.aprende", "hecho.sospecha"],
    "duda": ["hecho.duda"], "refuta": ["hecho.refuta"],
    "sorpresa": ["hecho.sorpresa_mejor", "hecho.sorpresa_peor", "hecho.sorpresa_sin", "hecho.sorpresa_modelo", "hecho.sorpresa_modelo_sin"],
    "logro": ["hecho.logro"], "peligro": ["hecho.peligro", "hecho.peligro_hipotesis"],
    "estrategia": ["hecho.plan_inicio", "hecho.plan_fin"], "duerme": ["hecho.duerme"],
    "despierta": ["hecho.despierta", "hecho.despierta_alarma", "hecho.despierta_descansada"], "muere": ["hecho.muere"],
}


def test_cada_tipo_de_hecho_tiene_plantilla_en_los_dos_idiomas():
    assert set(PLANTILLAS_HECHO) == set(HECHOS)          # un tipo nuevo en el catálogo pide su plantilla
    for claves in PLANTILLAS_HECHO.values():
        for clave in claves:
            assert clave in ES and clave in EN, clave


def test_verbos_y_relaciones_tienen_plantilla():
    for v in Verbo:
        for forma in ("pres", "inf"):
            assert f"verbo.{v.name}.{forma}" in ES, v
    for r in Relacion:
        for g in ("m", "f"):
            assert f"saber.{r.name}.{g}" in ES, r


def _definiciones():
    for m in pkgutil.walk_packages(ida.__path__, "ida."):
        try:
            importlib.import_module(m.name)
        except ImportError:      # un mundo sin sus dependencias
            continue
    vistas, pendientes = set(), list(Definicion.__subclasses__())
    while pendientes:
        c = pendientes.pop()
        if c not in vistas:
            vistas.add(c)
            pendientes.extend(c.__subclasses__())
    # solo las que fijan su propio nombre (las bases heredan el «estrategia» de Definicion)
    return [c for c in vistas if isinstance(c.__dict__.get("nombre"), str) and c.__dict__["nombre"]]


def test_cada_plan_y_cada_motivo_tienen_texto():
    definiciones = _definiciones()
    assert len(definiciones) >= 15
    faltan = sorted({f"plan.{c.nombre}" for c in definiciones} - set(ES))
    assert not faltan, faltan
    impulsos = {i for c in definiciones for i in (getattr(c, "impulsos", ()) or ())}
    for m in MUNDOS:
        try:
            impulsos |= {n.nombre for n in cargar(m).perfil.necesidades}
        except ImportError:
            continue
    faltan = sorted(f"motivo.{i}" for i in impulsos if f"motivo.{i}" not in ES)
    assert not faltan, faltan
