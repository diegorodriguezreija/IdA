"""Tests del Core: onda y guillotina, tribunal, memoria, soma y linaje."""

import pytest

from ida.core.arquitectura import Componente, Contexto, Modulo
from ida.core.azar import Azar
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.mundo import Entidad, Perfil
from ida.core.onda import LatidoAgotado, Onda
from ida.core.pieza import Episodio, Pieza
from ida.core.sentidos import Tribunal
from ida.core.soma import Soma
from ida.core.vocabulario import EstadoSaber, Relacion, Verbo


class RelojFalso:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def _ctx(onda, soma=None, memoria=None, verbos=None):
    return Contexto(onda, soma or Soma(), memoria or Memoria(), Arquetipo(), Azar(1), Perfil(),
                    verbos or set(Verbo), None, True)


# --- Onda y guillotina -------------------------------------------------------
def test_ei_es_de_solo_lectura():
    p = Pieza("x", "Escena")
    onda = Onda(2, 10, 100.0, ef_anterior={"Escena": {"x": p}})
    with pytest.raises(TypeError):
        onda.reactiva.ei["Escena"]["y"] = p


def test_guillotina_por_amplitud():
    onda = Onda(1, 2, 1000.0)
    onda.percibir("A", Pieza("a", "A"))
    onda.percibir("A", Pieza("b", "A"))
    with pytest.raises(LatidoAgotado):
        onda.percibir("A", Pieza("c", "A"))


def test_guillotina_por_tiempo():
    reloj = RelojFalso()
    onda = Onda(1, 100, 50.0, reloj=reloj)
    onda.control_vital(1)
    reloj.t = 0.051
    with pytest.raises(LatidoAgotado):
        onda.control_vital(1)


def test_modulo_exento_no_paga_ni_se_corta():
    reloj = RelojFalso()
    onda = Onda(1, 0, 10.0, reloj=reloj)
    reloj.t = 1.0   # plazo ya superado

    class Sensor(Componente):
        tipo = "S"

        def reactiva(self, ctx):
            self.percibir(ctx, self.pieza(ctx, "s", 0.5))

    Modulo("Sentir", [Sensor()], exento=True).ejecutar(_ctx(onda))
    assert "s" in onda.ev("S")


def test_proponer_mismo_id_conserva_el_mas_urgente():
    """Un impulso de explorar no puede pisar uno de huir."""
    onda = Onda(1, 10, 100.0)
    onda.proponer("Ejecucion", Pieza("S1:MOVER:a", "Ejecucion", arousal=0.9))
    onda.proponer("Ejecucion", Pieza("S1:MOVER:a", "Ejecucion", arousal=0.3))
    assert onda.acc("Ejecucion")["S1:MOVER:a"].arousal == pytest.approx(0.9)


# --- Tribunal ----------------------------------------------------------------
def _candidato(id_, verbo, arousal, confianza, clase=""):
    return Pieza(id_, "Ejecucion", arousal, confianza, {"verbo": verbo, "objetivo": id_, "clase": clase, "motivo": "", "datos": {}}, sistema="S1")


def test_tribunal_con_estres_manda_la_urgencia_y_en_calma_la_confianza():
    for estres, esperado in ((0.95, "urgente"), (0.0, "seguro")):
        onda = Onda(1, 10, 100.0)
        onda.proponer("Ejecucion", _candidato("urgente", Verbo.MOVER, 0.95, 0.4))
        onda.proponer("Ejecucion", _candidato("seguro", Verbo.MOVER, 0.3, 0.9))
        ctx = _ctx(onda, soma=Soma(estres=estres))
        Tribunal().reactiva(ctx)
        assert ctx.extra["decision"].carga["objetivo"] == esperado


def test_la_experiencia_sesga_y_puede_cambiar_la_decision():
    mem = Memoria()
    for t in range(5):
        mem.aprender(Verbo.COMER, "seta", {"vitalidad": -12.0}, None, None, True, t)
    onda = Onda(10, 10, 100.0)
    onda.proponer("Ejecucion", _candidato("seta_1", Verbo.COMER, 0.6, 0.7, "seta"))
    onda.proponer("Ejecucion", _candidato("celda", Verbo.MOVER, 0.5, 0.65, "pradera"))
    ctx = _ctx(onda, memoria=mem)
    ctx.perfil = Perfil(peso_experiencia=0.3)
    Tribunal().reactiva(ctx)
    assert ctx.extra["decision"].carga["objetivo"] == "celda"
    assert onda.notas["experiencia_cambio"] is True


def test_acecho_con_poca_confianza():
    onda = Onda(1, 10, 100.0)
    onda.proponer("Ejecucion", _candidato("x", Verbo.MOVER, 0.2, 0.2))
    ctx = _ctx(onda)
    Tribunal().reactiva(ctx)
    assert ctx.extra["decision"].carga["verbo"] == Verbo.ACECHAR


# --- Memoria y conocimiento --------------------------------------------------
def test_demostrada_exige_confirmaciones_y_se_puede_perder():
    mem = Memoria()
    for t in range(2):
        mem.aprender(Verbo.COMER, "baya", {"alimentacion": 20.0}, None, None, True, t)
    assert mem.proposicion("baya", Relacion.NUTRITIVO).estado(2) == EstadoSaber.HIPOTESIS
    for t in range(2, 6):
        mem.aprender(Verbo.COMER, "baya", {"alimentacion": 20.0}, None, None, True, t)
    assert mem.demostrada("baya", Relacion.NUTRITIVO, 50)
    mem.aprender(Verbo.COMER, "baya", {}, None, None, True, 60)
    assert not mem.demostrada("baya", Relacion.NUTRITIVO, 61)


def test_el_dano_se_atribuye_a_la_causa_y_no_a_lo_que_se_hacia():
    mem = Memoria()
    mem.aprender(Verbo.COMER, "baya", {"alimentacion": 20.0, "vitalidad": -8.0}, "lobo", "baya", True, 1)
    assert mem.proposicion("lobo", Relacion.PELIGROSO) is not None
    assert mem.proposicion("baya", Relacion.PELIGROSO) is None


def test_herencia_entra_como_hipotesis_y_necesita_experiencia_propia():
    padre = Memoria()
    for t in range(6):
        padre.aprender(Verbo.COMER, "baya", {"alimentacion": 20.0}, None, None, True, t)
    hijo = Memoria()
    assert hijo.heredar(padre.legado(100)) > 0
    assert not hijo.demostrada("baya", Relacion.NUTRITIVO, 100)
    hijo.aprender(Verbo.COMER, "baya", {"alimentacion": 20.0}, None, None, True, 101)
    hijo.aprender(Verbo.COMER, "baya", {"alimentacion": 20.0}, None, None, True, 102)
    assert hijo.demostrada("baya", Relacion.NUTRITIVO, 140)


def test_memoria_apagada_no_aprende():
    mem = Memoria("apagada")
    mem.aprender(Verbo.COMER, "baya", {"alimentacion": 20.0}, None, None, True, 1)
    assert not mem.saber and not mem.registros


def test_hipocampo_grafo_ruta_y_olvido():
    mem = Memoria()
    mem.registrar_transicion("A", "B", 1)
    mem.registrar_transicion("B", "C", 2)
    mem.registrar_transicion("C", "D", 3)
    mem.registrar_transicion("D", "A", 4)   # ciclo
    assert mem.ruta("A", "C") == "B"
    assert mem.ruta("A", "D") == "B"
    assert mem.ruta("A", "A") is None
    assert mem.ruta("A", "Z") is None

    # Recordar dónde está una clase y olvidarla por desuso al dormir
    mem.registrar_donde("comida", "C", 5)
    assert mem.donde_esta("comida") == "C"
    # La transición C->D se refuerza con usos, A->B queda sin refuerzo
    mem.registrar_transicion("C", "D", 400)
    res = mem.consolidar(400)
    assert res["aristas_olvidadas"] >= 1
    assert mem.donde_esta("comida") is None


def test_hipocampo_capacidad_maxima_y_apagada():
    mem_apagada = Memoria("apagada")
    mem_apagada.registrar_transicion("A", "B", 1)
    mem_apagada.registrar_donde("agua", "A", 1)
    assert mem_apagada.ruta("A", "B") is None
    assert mem_apagada.donde_esta("agua") is None

    mem = Memoria()
    for i in range(Memoria.MAX_NODOS_MAPA + 15):
        mem.registrar_transicion(f"N{i}", f"N{i + 1}", i + 1)
    assert len(mem.mapa) <= Memoria.MAX_NODOS_MAPA


def test_hipocampo_no_hereda_en_legado():
    padre = Memoria()
    padre.registrar_transicion("X", "Y", 1)
    padre.registrar_donde("agua", "Y", 2)
    leg = padre.legado(10)
    hijo = Memoria()
    hijo.heredar(leg)
    assert not hijo.mapa and not hijo.donde


def test_replay_sueno_trayectoria_resuelta_y_danio():
    mem = Memoria()
    mem.registrar_transicion("A", "B", 1)
    mem.registrar_transicion("B", "C", 2)

    # Trayectoria resuelta positiva A -> B -> C con balance +1.0
    ep1 = Episodio(id="ep_test_1", inicio=1, fin=3, balance=1.0, resuelto=True, trayectoria=["A", "B", "C"])
    mem.episodios.append(ep1)
    res = mem.consolidar(10)
    assert res["episodios_replay"] == 1
    # V(C) = 1.0 > V(B) = 0.8 > V(A) = 0.64 > 0
    assert mem.valor_lugar("C") > mem.valor_lugar("B") > mem.valor_lugar("A") > 0.0
    assert mem.mapa["A"]["B"].valor_replay == pytest.approx(0.8)
    assert mem.mapa["B"]["C"].valor_replay == pytest.approx(1.0)

    # Trayectoria adversa con daño/muerte X -> Y -> Z con balance -2.0
    mem2 = Memoria()
    mem2.registrar_transicion("X", "Y", 1)
    mem2.registrar_transicion("Y", "Z", 2)
    ep2 = Episodio(id="ep_test_2", inicio=1, fin=3, balance=-2.0, resuelto=False, trayectoria=["X", "Y", "Z"])
    mem2.episodios.append(ep2)
    mem2.consolidar(10)
    # Valencia negativa decreciente en magnitud desde el evento adverso Z:
    # V(Z) = -2.0 < V(Y) = -1.6 < V(X) = -1.28 < 0
    assert mem2.valor_lugar("Z") < mem2.valor_lugar("Y") < mem2.valor_lugar("X") < 0.0
    assert abs(mem2.valor_lugar("Z")) > abs(mem2.valor_lugar("Y")) > abs(mem2.valor_lugar("X"))


def test_replay_sueno_eliminacion_bucles():
    mem = Memoria()
    mem.registrar_transicion("A", "B", 1)
    mem.registrar_transicion("B", "C", 2)
    mem.registrar_transicion("B", "A", 3)
    # Bucle A -> B -> A -> B -> C
    ep = Episodio(id="ep_loop", inicio=1, fin=5, balance=1.0, resuelto=True, trayectoria=["A", "B", "A", "B", "C"])
    mem.episodios.append(ep)
    mem.consolidar(10)
    # Tras eliminar bucles, ruta simple es A -> B -> C
    assert mem.valor_lugar("C") > mem.valor_lugar("B") > mem.valor_lugar("A") > 0.0


def test_replay_sueno_desempate_en_ruta():
    mem = Memoria()
    # Dos caminos de igual longitud de A a D:
    # Camino 1: A -> B -> D
    # Camino 2: A -> C -> D
    mem.registrar_transicion("A", "B", 1)
    mem.registrar_transicion("B", "D", 2)
    mem.registrar_transicion("A", "C", 3)
    mem.registrar_transicion("C", "D", 4)
    # Consolidar experiencia positiva sobre el camino 2 (A -> C -> D)
    ep = Episodio(id="ep_c", inicio=1, fin=3, balance=1.5, resuelto=True, trayectoria=["A", "C", "D"])
    mem.episodios.append(ep)
    mem.consolidar(10)
    # ruta(A, D) debe desempatar eligiendo 'C' porque valor_replay de A->C es mayor que A->B
    assert mem.ruta("A", "D") == "C"

    # Si con_replay está apagado, desempataría por inserción/usos sin mirar valor_replay
    mem_sin = Memoria(con_replay=False)
    mem_sin.registrar_transicion("A", "B", 1)
    mem_sin.registrar_transicion("B", "D", 2)
    mem_sin.registrar_transicion("A", "C", 3)
    mem_sin.registrar_transicion("C", "D", 4)
    mem_sin.episodios.append(ep)
    mem_sin.consolidar(10)
    assert mem_sin.ruta("A", "D") == "B"


# --- Soma, linaje y contrato -------------------------------------------------
def test_presupuesto_varia_con_el_estado():
    s = Soma(energia=100.0)
    f1, a1 = s.presupuesto(100.0, 100)
    s.energia = 20.0
    s.indicadores["peligro"] = 1.0
    f2, a2 = s.presupuesto(100.0, 100)
    assert a2 < a1 and f2 < f1
    s.dormido = True
    assert s.presupuesto(100.0, 100)[1] == 20


def test_arquetipos_distintos_por_individuo():
    padre = Arquetipo.nuevo(Azar(5))
    hijo = padre.mutar(Azar(6))
    assert hijo.generacion == 2 and hijo.padre == padre.id
    assert hijo.texto() != padre.texto()


def test_entidad_rechaza_rasgos_desconocidos():
    with pytest.raises(ValueError):
        Entidad("x", "cosa", {"brillo": 1.0})
