"""Visor de comprobación de escena (T2a/T2b): ficheros estáticos de ``web/`` y sprites de Crafter, Mínimo, Archivos y Snake."""

import json
import os
import urllib.error
import urllib.request

from ida.mundos.archivos.adaptador import AMBIENTE, COMESTIBLES, TOXICOS, clase_de
from ida.mundos.crafter.adaptador import INVENTARIO, MATERIALES, OBJETOS, ORIENTACION, SUELOS, VITALES_JUEGO
from ida.telemetria.servidor import WEB, Telemetria, fichero_web


def test_fichero_web_no_sale_de_web():
    assert fichero_web("escena.html") == os.path.realpath(os.path.join(WEB, "escena.html"))
    assert fichero_web("sprites/crafter/indice.json")
    assert fichero_web("sprites/minimo/indice.json")
    assert fichero_web("sprites/archivos/indice.json")
    assert fichero_web("sprites/snake/indice.json")
    assert fichero_web("../servidor.py") is None
    assert fichero_web("..%2Fservidor.py") is None
    assert fichero_web("sprites/crafter/LICENSE") is None      # tipo no servido
    assert fichero_web("no_existe.js") is None


def test_indice_de_sprites_de_crafter_completo():
    """Cada clase que puede dar la escena de Crafter tiene sprite, y cada sprite del índice existe."""
    directorio = os.path.join(WEB, "sprites", "crafter")
    with open(os.path.join(directorio, "indice.json"), encoding="utf-8") as f:
        mapa = json.load(f)["mapa_sprites"]
    claves = (set(MATERIALES.values()) | set(SUELOS.values()) | set(OBJETOS.values()) - {"planta", "flecha"}
              | {"planta", "planta.madura"} | {f"flecha.{o}" for o in ORIENTACION.values()}
              | {f"yo.{o}" for o in ORIENTACION.values()} | {"yo.dormido"}
              | set(INVENTARIO.values()) | set(VITALES_JUEGO.values()) | {"?"})
    assert claves <= set(mapa), sorted(claves - set(mapa))
    for fichero in set(mapa.values()):
        assert os.path.isfile(os.path.join(directorio, fichero)), fichero
    copiados = {f for f in os.listdir(directorio) if f.endswith(".png")}
    assert copiados == set(mapa.values())                     # solo los que usa la escena
    assert os.path.isfile(os.path.join(directorio, "LICENSE"))


def test_indice_de_sprites_de_minimo_completo():
    """Cada clase que emite mínimo tiene entrada en su indice.json y el SVG existe."""
    directorio = os.path.join(WEB, "sprites", "minimo")
    with open(os.path.join(directorio, "indice.json"), encoding="utf-8") as f:
        mapa = json.load(f)["mapa_sprites"]
    esperadas = {"pradera", "baya", "seta", "piedra", "lobo", "yo", "?"}
    assert esperadas <= set(mapa), sorted(esperadas - set(mapa))
    for fichero in set(mapa.values()):
        assert os.path.isfile(os.path.join(directorio, fichero)), fichero


def test_indice_de_sprites_de_archivos_completo():
    """Cada clase que emite archivos tiene entrada en su indice.json y el SVG existe."""
    directorio = os.path.join(WEB, "sprites", "archivos")
    with open(os.path.join(directorio, "indice.json"), encoding="utf-8") as f:
        mapa = json.load(f)["mapa_sprites"]
    clases_archivos = {clase_de(x) for x in COMESTIBLES + TOXICOS + list(AMBIENTE)} | {"brote", "depredador", "mensaje"}
    esperadas = {"raiz", "carpeta", "yo", "?"} | clases_archivos
    assert esperadas <= set(mapa), sorted(esperadas - set(mapa))
    for fichero in set(mapa.values()):
        assert os.path.isfile(os.path.join(directorio, fichero)), fichero


def test_indice_de_sprites_de_snake_completo():
    """Cada clase que emite snake tiene entrada en su indice.json y el SVG existe."""
    directorio = os.path.join(WEB, "sprites", "snake")
    with open(os.path.join(directorio, "indice.json"), encoding="utf-8") as f:
        mapa = json.load(f)["mapa_sprites"]
    esperadas = {"fondo", "cuerpo", "cuerpo.cabeza", "cuerpo.cuerpo", "comida",
                 "yo.norte", "yo.sur", "yo.este", "yo.oeste", "yo.muerta", "yo", "?"}
    assert esperadas <= set(mapa), sorted(esperadas - set(mapa))
    for fichero in set(mapa.values()):
        assert os.path.isfile(os.path.join(directorio, fichero)), fichero


def test_servidor_sirve_el_visor():
    tel = Telemetria(puerto=0, anfitrion="127.0.0.1", modo_antesala=True)
    try:
        base = f"http://127.0.0.1:{tel.puerto}"
        with urllib.request.urlopen(f"{base}/escena", timeout=5) as r:
            assert r.headers["Content-Type"].startswith("text/html") and b"escena.js" in r.read()
        with urllib.request.urlopen(f"{base}/web/escena.js", timeout=5) as r:
            assert r.headers["Content-Type"].startswith("text/javascript")
        with urllib.request.urlopen(f"{base}/web/sprites/crafter/cow.png", timeout=5) as r:
            assert r.headers["Content-Type"] == "image/png"
        with urllib.request.urlopen(f"{base}/web/sprites/minimo/baya.svg", timeout=5) as r:
            assert r.headers["Content-Type"].startswith("image/svg+xml")
        try:
            urllib.request.urlopen(f"{base}/web/../servidor.py", timeout=5)
            raise AssertionError("debía dar 404")
        except urllib.error.HTTPError as e:
            assert e.code == 404
    finally:
        tel.detener()
