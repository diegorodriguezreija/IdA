"""Idiomas de la aplicación web (O16, O18): es.json y en.json con las mismas claves, y toda clave usada existe.

Búsqueda estática en ``web/**/*.js`` y ``web/**/*.html``: llamadas ``t('clave')``, atributos ``data-i18n``,
``data-i18n-aria``, ``data-i18n-title`` y ``data-i18n-placeholder``, y cualquier texto entre comillas con forma de clave
cuyo primer tramo sea un espacio de nombres del diccionario (p. ej. ``'lab.lista.latido'`` en una lista). Las claves
que se forman en ejecución (``error.<codigo>``, ``mundo.<m>.nombre``...) se comprueban por familia contra su fuente.
"""

import json
import os
import re

from ida.mundos import MUNDOS
from ida.nucleo.vocabulario import Afecto
from ida.telemetria import api_v1, catalogo, presets
from ida.telemetria.ritmo import RITMOS
from ida.telemetria.servidor import WEB

I18N = os.path.join(WEB, "i18n")


def _dic(idioma):
    with open(os.path.join(I18N, f"{idioma}.json"), encoding="utf-8") as f:
        return json.load(f)


ES, EN = _dic("es"), _dic("en")


def _fuentes():
    for raiz, dirs, ficheros in os.walk(WEB):
        dirs[:] = [d for d in dirs if d not in ("sprites", "i18n", "vendor")]
        for f in ficheros:
            if f.endswith((".js", ".html")):
                ruta = os.path.join(raiz, f)
                with open(ruta, encoding="utf-8") as fh:
                    yield os.path.relpath(ruta, WEB), fh.read()


LLAMADA = re.compile(r"\bt\(\s*['\"]([A-Za-z0-9_.]+)['\"]")
ATRIBUTO = re.compile(r"data-i18n(?:-aria|-title|-placeholder)?=\"([A-Za-z0-9_.]+)\"")
LITERAL = re.compile(r"['\"]([a-z_]+(?:\.[A-Za-z0-9_]+)+)['\"]")


def test_mismas_claves_en_los_dos_idiomas():
    assert set(ES) == set(EN), {"solo_es": sorted(set(ES) - set(EN)), "solo_en": sorted(set(EN) - set(ES))}
    for clave in ES:
        assert ES[clave].strip() and EN[clave].strip(), clave
        assert set(re.findall(r"\{(\w+)\}", ES[clave])) == set(re.findall(r"\{(\w+)\}", EN[clave])), clave


def test_toda_clave_usada_existe():
    espacios = {k.split(".")[0] for k in ES}
    usadas = {}
    for ruta, texto in _fuentes():
        for patron in (LLAMADA, ATRIBUTO):
            for clave in patron.findall(texto):
                usadas.setdefault(clave, ruta)
        for clave in LITERAL.findall(texto):
            if clave.split(".")[0] in espacios:
                usadas.setdefault(clave, ruta)
    assert len(usadas) > 100                       # la búsqueda encuentra lo que se usa
    faltan = {c: r for c, r in usadas.items() if c not in ES}
    assert not faltan, faltan


def test_claves_que_se_forman_en_ejecucion():
    familias = (
        [f"mundo.{m}.{c}" for m in MUNDOS for c in ("nombre", "desc")]
        + [f"estado.{e}" for e in catalogo.ESTADOS] + [f"estado.ayuda.{e}" for e in catalogo.ESTADOS]
        + [f"error.{c}" for c in (*api_v1.CODIGOS, "red")]
        + [f"rasgo.{r}.{c}" for r in presets.RASGOS for c in ("nombre", "desc")]
        + [f"ritmo.{r}" for r in RITMOS]
        + [f"cuerpo.{m}" for m in ("vitalidad", "alimentacion", "energia", "descanso")]
        + [f"afecto.{a.value}" for a in Afecto]
    )
    faltan = [c for c in familias if c not in ES]
    assert not faltan, faltan


def test_los_codigos_de_error_de_la_api_estan_declarados():
    """Cada código que lanza la API está en CODIGOS (y por tanto traducido)."""
    with open(api_v1.__file__, encoding="utf-8") as f:
        fuente = f.read()
    lanzados = set(re.findall(r"ErrorApi\(\d+, \"([a-z_]+)\"", fuente))
    with open(os.path.join(os.path.dirname(api_v1.__file__), "instalador.py"), encoding="utf-8") as f:
        lanzados |= set(re.findall(r"ErrorInstalacion\(\"([a-z_]+)\"", f.read()))
    assert lanzados and lanzados <= set(api_v1.CODIGOS), sorted(lanzados - set(api_v1.CODIGOS))
