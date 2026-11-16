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


def test_reduccion_nocturna_proporcional_y_poda():
    from ida.core.memoria import Proposicion
    from ida.core.vocabulario import Relacion

    mem = Memoria()
    mem.grafo = {"Objeto:a": {"fuerza": 1.0}, "Objeto:b": {"fuerza": 0.05}}
    mem.relaciones = {("Objeto:a", "Objeto:b"): 0.5}
    mem.saber[("x", Relacion.NUTRITIVO)] = Proposicion("x", Relacion.NUTRITIVO, confianza=0.5)
    mem.saber[("y", Relacion.NUTRITIVO)] = Proposicion("y", Relacion.NUTRITIVO, confianza=0.15)
    podado = mem.reducir(10)
    assert mem.grafo["Objeto:a"]["fuerza"] == 0.9 and "Objeto:b" not in mem.grafo     # 0,045 < 0,05: podado
    assert not mem.relaciones                                                          # su nodo b ya no está
    assert mem.saber[("x", Relacion.NUTRITIVO)].confianza == 0.475 and ("y", Relacion.NUTRITIVO) not in mem.saber
    assert podado == 3


def test_recuperacion_evocada_trae_y_reconsolida():
    from dataclasses import replace

    from ida.core.arquitectura import Contexto
    from ida.core.azar import Azar
    from ida.core.linaje import Arquetipo
    from ida.core.memoria import Proposicion
    from ida.core.onda import Onda
    from ida.core.pieza import Pieza
    from ida.core.soma import Soma
    from ida.core.vocabulario import Relacion, Verbo
    from ida.sistemas.s2 import Recuerdo

    mem = Memoria()
    p = Proposicion("baya", Relacion.NUTRITIVO, confianza=0.8, actualizada=1)
    mem.saber[("baya", Relacion.NUTRITIVO)] = p
    mem.registrar_donde("baya", "celda_1_1", 1)
    perfil = replace(Perfil(), mecanismos=MecanismosMemoria(evocacion=True))
    onda = Onda(50, 100, 1e9)
    ctx = Contexto(onda, Soma(alimentacion=20.0), mem, Arquetipo(), Azar(1), perfil, {Verbo.MOVER})
    imp = Pieza("hambre", "Impulso", 0.7, carga={"intensidad": 0.7, "objetivo": 0.0, "rasgo": "nutritivo"}, sistema="S1")
    onda.registrar("Impulso", imp)
    r = Recuerdo()
    r.sistema = "S2"
    r.activa(ctx)
    rec = onda.ev("Recuerdo")["baya|NUTRITIVO"]
    assert rec.carga["donde"] == "celda_1_1" and rec.confianza == 0.8
    assert p.actualizada == 50 and any(e[2]["tipo"] == "Recuerdo" for e in mem.diurno)   # reconsolidado
    apagado = Contexto(Onda(51, 100, 1e9), Soma(alimentacion=20.0), mem, Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER})
    r.activa(apagado)
    assert not apagado.onda.ev("Recuerdo")                                                   # sin el interruptor, nada
