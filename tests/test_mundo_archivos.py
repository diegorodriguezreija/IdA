"""Mundo de archivos: vive, aprende y nunca toca nada fuera de su bioma. Telemetría sin bloqueo."""

import json
import os
import urllib.request

import pytest

from ida.nucleo.vocabulario import Verbo
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


def test_telemetria_publica_sin_bloquear(tmp_path):
    """Publicar un registro del latido v1 no bloquea el hilo de la vida, aunque no haya nadie conectado ni un cliente lo
    lea, y lo publicado se lee luego por la API v1 (T6a: antes, un diccionario sin ``v`` por ``/estado``)."""
    import time

    from ida.telemetria.servidor import Telemetria

    registros = []
    ejecutar("archivos", latidos=3, semilla=2, consola=False, datos=str(tmp_path / "a"), plazo_logico=40, nivel="cognitivo",
             al_latir=lambda o, onda, r: registros.append(r))
    assert registros and all(r["v"] == 1 for r in registros)
    tel = Telemetria(mundo="archivos", puerto=0, datos=str(tmp_path / "datos"))
    try:
        cola = tel.suscribir_registro()          # un cliente que no lee: su cola se llena y se descarta lo más antiguo
        t0 = time.monotonic()
        for i in range(500):
            tel.publicar(dict(registros[-1], latido=i))
        assert time.monotonic() - t0 < 10 and cola.qsize() <= 200
        assert tel.vida_actual() is None and tel.ultimo_registro["latido"] == 499
        with pytest.raises(ValueError):
            tel.publicar({"latido": 7})          # ya no hay forma de antes: solo el registro v1
        tel.desuscribir_registro(cola)
        tel.lab.esperar_cola()                   # el directo del Laboratorio se llena en su propio hilo
        with urllib.request.urlopen(f"http://127.0.0.1:{tel.puerto}/api/v1/vidas/actual/latidos", timeout=5) as r:
            indice = json.loads(r.read())
        assert indice["siguiente"] == 500 and indice["indice"][-1]["latido"] == 499
        with urllib.request.urlopen(f"http://127.0.0.1:{tel.puerto}/api/v1/vidas/actual/latidos/499", timeout=5) as r:
            assert json.loads(r.read())["registro"]["latido"] == 499
    finally:
        tel.detener()
