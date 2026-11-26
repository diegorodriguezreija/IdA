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


# --- O20: ritmos del visionado y paso a paso --------------------------------------------------------------------------
from ida.telemetria import catalogo   # noqa: E402

LATIDOS_O20 = 10


def _acciones_o20(datos, regulador):
    acciones = []

    def al_latir(o, onda, registro):
        a = registro["accion"]
        acciones.append(None if a is None else (a["verbo"], a["objetivo"], a["exito"]))

    t0 = time.monotonic()
    ejecutar("minimo", latidos=LATIDOS_O20, semilla=7, consola=False, datos=str(datos), plazo_logico=40.0,
             telemetria_instancia=_Publicador(), ritmo=regulador, al_latir=al_latir)
    return acciones, time.monotonic() - t0


def test_regulador_ritmos_o20():
    r = Regulador("comodo", comodo_ms=200)
    assert r.ms_por_latido(100) == 200 and r.fijar("lento") == "lento" and r.ms_por_latido(100) == 400
    assert r.fijar("x4") == "x4" and r.ms_por_latido(100) == 50
    assert r.fijar("max") == "max" and r.ms_por_latido(100) == 0
    assert r.fijar("x1") == "comodo"                     # sinónimo de T3
    assert r.fijar("pausa") == "pausa" and r.ms_por_latido(100) is None
    assert Regulador("comodo").ms_por_latido(100) == 100   # sin cómodo: el plazo del Perfil (CLI con --ver)
    with pytest.raises(ValueError):
        Regulador("max").paso()                          # paso a paso solo en pausa


def test_los_ritmos_o20_no_cambian_la_conducta(tmp_path):
    """Mínimo con su ritmo cómodo: las mismas acciones con lento, cómodo, ×4 y máximo, y avanzando de uno en uno."""
    comodo = catalogo.ritmo_comodo("minimo")
    assert comodo == 300.0
    resultados = {}
    for ritmo in ("lento", "comodo", "x4", "max"):
        resultados[ritmo] = _acciones_o20(tmp_path / ritmo, Regulador(ritmo, comodo_ms=comodo))
    referencia = resultados["max"][0]
    assert len(referencia) == LATIDOS_O20 and any(referencia)
    for ritmo, (acciones, _) in resultados.items():
        assert acciones == referencia, ritmo
    t = {r: d for r, (_, d) in resultados.items()}
    assert t["lento"] >= LATIDOS_O20 * 0.6 * 0.95 and t["comodo"] >= LATIDOS_O20 * 0.3 * 0.95
    assert t["lento"] > t["comodo"] > t["x4"] > t["max"]

    # paso a paso: en pausa, cada paso deja pasar exactamente un latido (lo que se publica, lo que ve quien mira)
    reg = Regulador("pausa", comodo_ms=comodo)
    publicados = threading.Semaphore(0)

    class _Contador(_Publicador):
        def publicar(self, registro):
            publicados.release()

    salida = {}

    def vivir():
        acciones = []

        def al_latir(o, onda, registro):
            a = registro["accion"]
            acciones.append(None if a is None else (a["verbo"], a["objetivo"], a["exito"]))

        ejecutar("minimo", latidos=LATIDOS_O20, semilla=7, consola=False, datos=str(tmp_path / "paso"), plazo_logico=40.0,
                 telemetria_instancia=_Contador(), ritmo=reg, al_latir=al_latir)
        salida["acciones"] = acciones

    hilo = threading.Thread(target=vivir, daemon=True)
    hilo.start()
    assert publicados.acquire(timeout=20)                 # el primer latido se publica y se queda en pausa
    for _ in range(LATIDOS_O20 - 1):
        assert not publicados.acquire(timeout=0.3)        # quieto hasta el paso
        reg.paso()
        assert publicados.acquire(timeout=10)             # un latido por paso
    reg.paso()                                            # suelta el último (la vida termina)
    hilo.join(timeout=10)
    assert not hilo.is_alive() and salida["acciones"] == referencia
