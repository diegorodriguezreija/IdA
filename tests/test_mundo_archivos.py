"""Mundo de archivos: vive, aprende y nunca toca nada fuera de su bioma. Telemetría sin bloqueo."""

import json
import os
import urllib.request

import pytest

from ida.core.vocabulario import Verbo
from ida.ejecutor import ejecutar
from ida.mundos.archivos import MundoArchivos, clase_de, tensor_bytes


def test_clase_y_tensor():
    assert clase_de("depredador_12.exe") == "depredador"
    assert clase_de("Boletus_edulis.brote") == "Boletus_edulis"
    organico = tensor_bytes("x.brote", b"NUTRIENTE_PURO_1024_BYTES" * 20)
    assert organico["periodicidad"] > 0.9 and organico["cinetico"] == 0.0
    assert tensor_bytes("depredador_1.exe", b"X")["cinetico"] > 0.5


def test_no_sale_del_bioma(tmp_path):
    m = MundoArchivos(datos=str(tmp_path))
    m.reiniciar(1)
    fuera = tmp_path / "intocable.txt"
    fuera.write_text("no me borres")
    with pytest.raises(PermissionError):
        m._seguro(str(fuera))
    ef = m.ejecutar(Verbo.COMER, "../intocable.txt", {})
    assert not ef.exito and fuera.read_text() == "no me borres"


def test_vida_completa_en_archivos(tmp_path):
    resumen = ejecutar("archivos", latidos=200, semilla=2, generaciones=1, consola=False, datos=str(tmp_path))[0]
    assert resumen["latidos"] > 50
    assert os.path.exists(tmp_path / "linaje.json") and os.path.exists(tmp_path / "memoria.db")
    assert any("nutre" in t for t in resumen["conocimiento"])


def test_telemetria_publica_sin_bloquear():
    from ida.telemetria.servidor import Telemetria

    tel = Telemetria(mundo="prueba", puerto=0)
    try:
        tel.publicar({"latido": 7})
        with urllib.request.urlopen(f"http://127.0.0.1:{tel.puerto}/estado", timeout=5) as r:
            assert json.loads(r.read())["latido"] == 7
    finally:
        tel.detener()
