"""Ritmo visible (O3): el regulador espera entre latidos y no cambia la conducta."""

import threading
import time

import pytest

from ida.ejecutor import ejecutar
from ida.telemetria.ritmo import Regulador


def test_regulador_espera_segun_el_ritmo():
    r = Regulador("x1")
    t0 = time.monotonic()
    r.esperar(120)
    assert 0.11 <= time.monotonic() - t0 < 0.5
    r.fijar("x4")
    t0 = time.monotonic()
    r.esperar(400)
    assert 0.09 <= time.monotonic() - t0 < 0.4
    r.fijar("max")
    t0 = time.monotonic()
    r.esperar(10_000)
    assert time.monotonic() - t0 < 0.05
    with pytest.raises(ValueError):
        r.fijar("x2")


def test_pausa_espera_hasta_reanudar_y_parar_la_suelta():
    r = Regulador("pausa")
    hecho = threading.Event()
    hilo = threading.Thread(target=lambda: (r.esperar(10), hecho.set()), daemon=True)
    hilo.start()
    assert not hecho.wait(0.4)                 # en pausa no sigue
    r.fijar("max")
    assert hecho.wait(1.0)                     # al reanudar, sigue
    r.fijar("pausa")
    parada = threading.Event()
    hecho.clear()
    threading.Thread(target=lambda: (r.esperar(10, parada), hecho.set()), daemon=True).start()
    assert not hecho.wait(0.3)
    parada.set()
    assert hecho.wait(1.0)                     # la parada saca de la pausa


class _Publicador:
    """Lo mínimo de una telemetría: el ejecutor publica en ella y, por haberla, aplica el ritmo."""
    mundo = ""

    def publicar(self, registro):
        pass


def _acciones(datos, ritmo):
    acciones = []

    def al_latir(o, onda, registro):
        a = registro["accion"]
        acciones.append(None if a is None else (a["verbo"], a["objetivo"], a["exito"]))

    t0 = time.monotonic()
    ejecutar("minimo", latidos=30, semilla=7, consola=False, datos=str(datos), plazo_logico=40.0,
             telemetria_instancia=_Publicador(), ritmo=Regulador(ritmo), al_latir=al_latir)
    return acciones, time.monotonic() - t0


def test_el_ritmo_no_cambia_la_conducta(tmp_path):
    """Con ×1 (100 ms entre latidos en mínimo), una vida hace exactamente las mismas acciones que a ritmo máximo."""
    lentas, t_x1 = _acciones(tmp_path / "x1", "x1")
    rapidas, t_max = _acciones(tmp_path / "max", "max")
    assert len(lentas) == 30 and any(lentas)
    assert lentas == rapidas
    assert t_x1 >= 30 * 0.1 * 0.95 > t_max        # ×1 de verdad espera; máximo, no
