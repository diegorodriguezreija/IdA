"""Bloque E: mecanismos de memoria (decisiones 19 a 22), cada uno detrás de su interruptor."""

from ida.core.memoria import Memoria
from ida.core.mundo import MecanismosMemoria, Perfil


def test_interruptores_apagados_por_defecto():
    m = Perfil().mecanismos
    assert m == MecanismosMemoria() and not any([m.buffer, m.consolidacion, m.conceptos, m.reduccion, m.evocacion, m.repaso])
    assert m.tasa_herencia == 1.0


def test_buffer_diurno_de_tamano_fijo_guarda_lo_mejor_puntuado():
    mem = Memoria()
    mem.CAPACIDAD_DIURNO = 3
    mem.marcar(1, [{"id": "a", "arousal": 0.2}, {"id": "b", "arousal": 0.9}], feedback=0.0, resumen={"verbo": "MOVER"})
    mem.marcar(2, [{"id": "c", "arousal": 0.5}, {"id": "d", "arousal": 0.1}], feedback=0.5, resumen={})
    ids = sorted(p["id"] for _, _, p in mem.diurno)
    assert len(mem.diurno) == 3 and ids == ["b", "c", "d"]     # d (0,1 + 0,5) entra; a (0,2) sale
    assert [d["latido"] for d in mem.dia] == [1, 2] and mem.dia[1]["feedback"] == 0.5


def test_consolidacion_pasa_el_bufer_al_grafo_y_lo_vacia():
    mem = Memoria()
    mem.marcar(1, [{"id": "s1", "tipo": "Objeto", "clase": "seta", "arousal": 0.6},
                   {"id": "l1", "tipo": "Objeto", "clase": "lobo", "arousal": 0.9}], feedback=-0.2, resumen={})
    mem.marcar(2, [{"id": "s2", "tipo": "Objeto", "clase": "seta", "arousal": 0.5}], feedback=0.0, resumen={})
    r = mem.consolidar_dia(3)
    assert r["piezas_consolidadas"] == 3 and not mem.diurno and not mem.dia
    seta = mem.grafo["Objeto:seta"]
    assert seta["usos"] == 2 and seta["fuerza"] == round(0.4 + 0.5, 4) and seta["valencia"] == -0.2
    assert mem.relaciones[("Objeto:lobo", "Objeto:seta")] == 0.4     # coincidieron en el latido 1
    assert len(mem.dias) == 1 and mem.dias[0]["latidos"] == 2


def test_conceptos_con_prototipo_promediado_e_ids_sin_significado():
    mem = Memoria()
    cid = mem.instancia("vaca_1", "vaca", {"nutritivo": 0.8, "peligro": 0.0}, 1)
    assert mem.instancia("vaca_2", "vaca", {"nutritivo": 0.4}, 2) == cid == "c1"     # mismo concepto
    c = mem.concepto("vaca")
    assert c["etiqueta"] == "vaca" and c["n"] == 2 and c["prototipo"]["nutritivo"] == 0.6
    assert mem.instancias["vaca_2"]["concepto"] == "c1"
    assert mem.instancia("lobo", "lobo", {"peligro": 0.8}, 3) == "c2"
