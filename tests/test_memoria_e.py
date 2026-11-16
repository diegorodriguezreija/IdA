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
