"""Bloque E: mecanismos de memoria (decisiones 19 a 22), cada uno detrás de su interruptor."""

import pytest

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


def test_repaso_en_calma_refuerza_lo_reciente():
    from dataclasses import replace

    from ida.core.arquitectura import Contexto
    from ida.core.azar import Azar
    from ida.core.linaje import Arquetipo
    from ida.core.memoria import Proposicion
    from ida.core.onda import Onda
    from ida.core.soma import Soma
    from ida.core.vocabulario import Afecto, Relacion, Verbo
    from ida.sistemas.s2 import Recuerdo

    mem = Memoria()
    mem.grafo = {"Objeto:seta": {"fuerza": 1.0, "ultimo": 90, "clase": "seta"}}
    h = Proposicion("seta", Relacion.PELIGROSO, confianza=0.4, actualizada=10)
    mem.saber[("seta", Relacion.PELIGROSO)] = h
    perfil = replace(Perfil(), mecanismos=MecanismosMemoria(repaso=True))
    soma = Soma()
    soma.afecto = Afecto.CALMA
    ctx = Contexto(Onda(100, 100, 1e9), soma, mem, Arquetipo(), Azar(1), perfil, {Verbo.MOVER})
    r = Recuerdo()
    r.sistema = "S2"
    r.activa(ctx)
    assert "repaso:Objeto:seta" in ctx.onda.ev("Recuerdo")
    assert mem.grafo["Objeto:seta"]["fuerza"] == pytest.approx(1.1) and h.c_exp == pytest.approx(0.42) and h.actualizada == 100
    soma.afecto = Afecto.MIEDO                                       # sin calma no se repasa
    ctx2 = Contexto(Onda(101, 100, 1e9), soma, mem, Arquetipo(), Azar(1), perfil, {Verbo.MOVER})
    r.activa(ctx2)
    assert not ctx2.onda.ev("Recuerdo")


def test_tasa_de_herencia_filtra_lo_de_mas_confianza():
    legado = {"proposiciones": [{"sujeto": f"c{i}", "relacion": "NUTRITIVO", "confianza": 0.5 + i / 10} for i in range(4)],
              "registros": [{"verbo": "COMER", "clase": f"c{i}", "n": i + 2, "media": 0.1} for i in range(4)]}
    entero, mitad, nada = Memoria(), Memoria(), Memoria()
    assert entero.heredar(legado) == 8
    assert mitad.heredar(legado, 0.5) == 4
    assert {s for s, _ in mitad.saber} == {"c2", "c3"} and {c for _, c in mitad.registros} == {"c2", "c3"}
    assert nada.heredar(legado, 0.0) == 0


def test_emision_de_creencias_acotada():
    from ida.core.arquitectura import Contexto
    from ida.core.azar import Azar
    from ida.core.linaje import Arquetipo
    from ida.core.memoria import Proposicion
    from ida.core.onda import Onda
    from ida.core.soma import Soma
    from ida.core.vocabulario import Relacion, Verbo
    from ida.sistemas.s3 import Creencia

    mem = Memoria()
    for i in range(200):
        mem.saber[(f"c{i}", Relacion.NUTRITIVO)] = Proposicion(f"c{i}", Relacion.NUTRITIVO, confianza=i / 400)
    ctx = Contexto(Onda(1, 100, 1e9), Soma(), mem, Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER})
    c = Creencia()
    c.sistema = "S3"
    c.reactiva(ctx)
    emitidas = ctx.onda.ef("Creencia")
    assert len(emitidas) == Creencia.MAX_CREENCIAS
    assert "c199|NUTRITIVO" in emitidas and "c0|NUTRITIVO" not in emitidas


def test_reduccion_respeta_el_decay_del_dano():
    from ida.core.vocabulario import Relacion, Verbo

    mem = Memoria()
    mem.aprender(Verbo.COMER, "toxico", {"vitalidad": -10.0}, None, None, True, 1)      # daño alto: arousal 1
    mem.aprender(Verbo.COMER, "leve", {"vitalidad": -2.0}, None, None, True, 1)         # daño leve: arousal 0,2
    alto, leve = mem.saber[("toxico", Relacion.PELIGROSO)], mem.saber[("leve", Relacion.PELIGROSO)]
    assert alto.decay == 0.0 and leve.decay == pytest.approx(0.04)
    nutre = mem.proposicion("x", Relacion.NUTRITIVO, crear=True)
    assert nutre is not None and nutre.decay == pytest.approx(0.05)
    c_alto, c_leve, c_nutre = alto.c_exp, leve.c_exp, nutre.c_exp
    mem.reducir(100)
    assert alto.c_exp == c_alto
    assert leve.c_exp == pytest.approx(c_leve * 0.96) and nutre.c_exp == pytest.approx(c_nutre * 0.95)


# --- Bloque F --------------------------------------------------------------


def test_expectativa_modelo_y_generalizacion_por_concepto():
    mem = Memoria()
    assert mem.esperar("S1", "comer", "baya") is None
    assert mem.contrastar("S1", "comer", "baya", {"hambre": -0.3}, 1) is None       # sin expectativa: solo aprende
    assert mem.esperar("S1", "comer", "baya") == ({"hambre": -0.3}, "episodios")
    aciertos = mem.aciertos
    assert mem.contrastar("S1", "comer", "baya", {"hambre": -0.28}, 2) == pytest.approx(0.02) and mem.aciertos == aciertos + 1
    fallos = mem.fallos
    assert mem.contrastar("S1", "comer", "baya", {"hambre": 0.2}, 3) >= Memoria.UMBRAL_SORPRESA and mem.fallos == fallos + 1
    mem.instancia("b1", "baya", {"nutritivo": 0.8, "color": 0.5}, 1)
    mem.instancia("m1", "mora", {"nutritivo": 0.75, "color": 0.55}, 1)
    mem.instancia("p1", "piedra", {"nutritivo": 0.0, "color": 0.1}, 1)
    assert mem.esperar("S1", "comer", "mora")[1] == "concepto"                       # se parece a la baya
    assert mem.esperar("S1", "comer", "piedra") is None
    mem.grafo["Objeto:piedra"] = {"fuerza": 1.0, "valencia": -0.6, "usos": 2}
    assert mem.esperar("S2", "comer", "piedra") == ({"valencia": -0.3}, "grafo")


def test_expectativas_en_una_vida_con_el_interruptor():
    from dataclasses import replace

    from ida.core.azar import Azar
    from ida.core.latido import Organismo
    from ida.core.linaje import Arquetipo
    from ida.mundos.minimo import MundoMinimo
    from ida.sistemas import crear_sistemas

    mundo = MundoMinimo()
    mundo.perfil = replace(mundo.perfil, mecanismos=replace(mundo.perfil.mecanismos, expectativa=True))
    mundo.reiniciar(3)
    azar = Azar(3)
    org = Organismo(mundo, crear_sistemas(), Arquetipo.nuevo(azar), Memoria(mundo.perfil.memoria), azar, True)
    sistemas = set()
    org.vivir(300, al_latir=lambda o, onda: sistemas.update(p.sistema for p in onda.reactiva.ef.get("Expectativa", {}).values()))
    assert sistemas == {"S1", "S2"}
    assert any(k[0] == "S1" for k in org.memoria.modelo) and any(k[0] == "S2" for k in org.memoria.modelo)


def test_camino_completo_por_el_mapa():
    mem = Memoria()
    for a, b in (("a", "b"), ("b", "c"), ("c", "d"), ("b", "a")):
        mem.registrar_transicion(a, b, 1)
    assert mem.camino("a", "d") == ["a", "b", "c", "d"]
    assert mem.ruta("a", "d") == "b"
    assert mem.camino("d", "a") is None and mem.camino("a", "a") is None


def test_plan_consume_pasos_rehace_y_falla():
    from types import SimpleNamespace

    from ida.core.estrategia import Plan, Propuesta, nueva, paso_actual, progreso_plan
    from ida.core.vocabulario import Verbo

    class Contar(Plan):
        nombre = "contar"
        construidos = 0

        def construir(self, ctx, estrategia):
            self.construidos += 1
            return [{"meta": n} for n in (1, 2, 3)]

        def cumplido(self, ctx, paso, estado):
            return paso["meta"] <= ctx.hecho

        def fallido(self, ctx, paso, estado):
            return ctx.sorpresa

        def actuar(self, ctx, estrategia):
            return Propuesta(Verbo.MOVER, "x", 0.5, 1.0, "")

    con = SimpleNamespace(perfil=Perfil(mecanismos=MecanismosMemoria(plan=True)), hecho=0, sorpresa=False)
    d = Contar()
    p = nueva("S3", d, "progresar", 0.8, 0.0, 1)
    p.carga["paso"] = d.paso(con, p)
    assert progreso_plan(p.carga["paso"]) == 0.0 and paso_actual(p) == {"meta": 1}
    con.hecho = 2
    p.carga["paso"] = d.paso(con, p)
    assert progreso_plan(p.carga["paso"]) == pytest.approx(2 / 3) and paso_actual(p) == {"meta": 3}
    con.sorpresa = True
    p.carga["paso"] = d.paso(con, p)                       # primera sorpresa: se rehace
    assert d.construidos == 2 and p.carga["paso"]["rehecho"] == 1 and not p.carga["paso"]["fallido"]
    p.carga["paso"] = d.paso(con, p)                       # segunda: falla
    assert p.carga["paso"]["fallido"] and paso_actual(p) is None
    sin = SimpleNamespace(perfil=Perfil(), hecho=0, sorpresa=False)
    q = nueva("S3", d, "progresar", 0.8, 0.0, 1)
    assert d.paso(sin, q) == 0                             # sin interruptor, como antes


def test_planes_en_una_vida_con_el_interruptor():
    from dataclasses import replace

    from ida.core.azar import Azar
    from ida.core.latido import Organismo
    from ida.core.linaje import Arquetipo
    from ida.mundos.minimo import MundoMinimo
    from ida.sistemas import crear_sistemas

    mundo = MundoMinimo()
    mundo.perfil = replace(mundo.perfil, mecanismos=replace(mundo.perfil.mecanismos, expectativa=True, plan=True))
    mundo.reiniciar(1)
    azar = Azar(1)
    org = Organismo(mundo, crear_sistemas(), Arquetipo.nuevo(azar), Memoria(mundo.perfil.memoria), azar, True)
    planes = []
    org.vivir(400, al_latir=lambda o, onda: planes.extend(p.carga["paso"] for p in onda.estrategias.values()
                                                           if p.carga["nombre"] == "recordar_comida"))
    assert org.ciclo > 0
    assert planes and all(isinstance(e, dict) and "pasos" in e for e in planes)
    assert max(int(e["i"]) for e in planes) >= 2                          # la cadena se consume paso a paso


def test_ningun_mundo_activa_los_mecanismos_de_memoria():
    """Cierre de E y F (docs/VEREDICTO_E_F.md): código fusionado, mecanismos apagados en todos los mundos."""
    import importlib.util

    from ida.mundos import MUNDOS, cargar

    for nombre in MUNDOS:
        if nombre == "ajedrez" and importlib.util.find_spec("chess") is None:
            continue
        if nombre == "crafter" and importlib.util.find_spec("crafter") is None:
            continue
        assert cargar(nombre).perfil.mecanismos == MecanismosMemoria(), nombre
