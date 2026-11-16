"""Estrategias (bloque C): tipo de pieza, progreso, agotamiento y conservación entre latidos."""

import pytest

from ida.core import estrategia as est
from ida.core.arquitectura import Componente, Contexto
from ida.core.azar import Azar
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.mundo import Perfil
from ida.core.onda import Onda, PiezaAjena
from ida.core.soma import Soma
from ida.core.vocabulario import Verbo


class _Estrategia(Componente):
    tipo = "Estrategia"


class _Otro(Componente):
    tipo = "Valor"


class _Huir(est.Definicion):
    nombre = "huir"
    impulsos = ("seguridad",)


def _ctx(onda: Onda) -> Contexto:
    return Contexto(onda, Soma(), Memoria(), Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER})


def _comp(cls):
    c = cls()
    c.sistema = "S1"
    return c


def test_pieza_estrategia_y_progreso_sobre_la_intensidad_cruda():
    p = est.nueva("S1", _Huir(), "seguridad", 0.8, 0.0, latido=5)
    assert p.id == "S1:huir:seguridad" and p.tipo == "Estrategia" and p.carga["estado"] == est.ACTIVA
    assert p.carga["valor_inicial"] == pytest.approx(0.8) and p.carga["inicio"] == 5
    assert est.progreso(p.carga, 0.4) == pytest.approx(0.5)
    assert est.progreso(p.carga, 0.9) == 0.0 and est.progreso(p.carga, 0.0) == 1.0


def test_agotamiento_tras_la_gracia_sube_sin_progreso_y_baja_con_el():
    p = est.nueva("S1", _Huir(), "seguridad", 0.8, 0.0, latido=0)
    c = dict(p.carga)
    c.update(est.avanzar(c, 0.8, True, latido=2, gracia=3, ritmo_esperado=0.02))    # en la gracia: no sube
    assert c["agotamiento"] == 0.0 and c["esfuerzo"] == 1
    for t in range(3, 8):
        c.update(est.avanzar(c, 0.8, False, latido=t, gracia=3, ritmo_esperado=0.02))
    assert c["agotamiento"] == pytest.approx(5 * est.SUBIDA_AGOTAMIENTO) and c["esfuerzo"] == 1
    c.update(est.avanzar(c, 0.4, True, latido=8, gracia=3, ritmo_esperado=0.02))      # progresa: baja
    assert c["agotamiento"] == pytest.approx(5 * est.SUBIDA_AGOTAMIENTO - est.BAJADA_AGOTAMIENTO)


def test_la_onda_conserva_las_estrategias_entre_latidos_y_comprueba_la_propiedad():
    activas: dict = {}
    onda1 = Onda(1, 10, 1e9, estrategias=activas)
    ctx1, e = _ctx(onda1), _comp(_Estrategia)
    p = onda1.activar(est.nueva("S1", _Huir(), "seguridad", 0.8, 0.0, 1), e)
    assert onda1.ef("Estrategia")[p.id] is p and onda1.amplitud_consumida == 0      # estado, no atención
    with pytest.raises(PiezaAjena):
        onda1.activar(est.nueva("S1", _Huir(), "otra", 0.5, 0.0, 1), _comp(_Otro))
    onda2 = Onda(2, 10, 1e9, estrategias=activas)
    assert onda2.estrategias[p.id] is p                                              # sigue activa
    onda2.cerrar(p, est.AGOTADA, e)
    assert p.id not in activas and p.carga["estado"] == est.AGOTADA
    assert ctx1.onda is onda1


def test_accion_traduce_la_estrategia_activa_y_el_origen_llega_al_estado_final():
    from ida.core.mundo import Efecto
    from ida.core.sentidos import Tribunal, aplicar_efecto
    from ida.sistemas.comun import Accion

    class _HuirA(est.Definicion):
        nombre = "huir"
        impulsos = ("seguridad",)

        def actuar(self, ctx, estrategia):
            return est.Propuesta(Verbo.MOVER, "refugio", 0.9, 0.8, "huir al refugio")

    activas: dict = {}
    onda = Onda(3, 10, 1e9, estrategias=activas)
    ctx = _ctx(onda)
    onda.activar(est.nueva("S1", _HuirA(), "seguridad", 0.8, 0.0, 3), _comp(_Estrategia))
    accion = _comp(lambda: Accion(est.Catalogo([_HuirA()])))
    accion.reactiva(ctx)
    c = onda.acc("Accion")[f"S1:{Verbo.MOVER.value}:refugio"]
    assert c.carga["origen"] == {"impulso": "seguridad", "estrategia": "S1:huir:seguridad"}
    tribunal = Tribunal()
    tribunal.sistema = "CORE"
    tribunal.reactiva(ctx)
    d = ctx.extra["decision"]
    assert d.carga["origen"]["estrategia"] == "S1:huir:seguridad"
    aplicar_efecto(ctx, Verbo.MOVER, d, Efecto())
    assert onda.ef("Accion")["Accion"].carga["origen"]["impulso"] == "seguridad"


def test_necesidades_declaradas_y_feedback_de_s1():
    from ida.core.mundo import NECESIDADES_BASE, Necesidad
    from ida.core.pieza import Pieza
    from ida.sistemas.s1 import Feedback, deficits

    sed = Necesidad("sed", ("agua",), 95.0)
    assert sed.deficit({"agua": 47.5}) == pytest.approx(0.5) and sed.deficit({"agua": 100.0}) == 0.0
    assert sed.deficit({"otra": 1.0}) is None
    cansancio = next(n for n in NECESIDADES_BASE if n.nombre == "cansancio")
    assert cansancio.deficit({"energia": 90.0, "descanso": 30.0}) == pytest.approx(0.5)   # cuenta la más baja

    def latido(n, alimentacion, ef_anterior=None):
        onda = Onda(n, 50, 1e9, ef_anterior=ef_anterior)
        ctx = _ctx(onda)
        onda.percibir("Interocepcion", Pieza("alimentacion", "Interocepcion", carga={"valor": alimentacion}))
        fb = _comp(Feedback)
        fb.reactiva(ctx)
        return ctx, onda

    ctx, onda = latido(1, 47.5)
    assert deficits(ctx)["hambre"] == pytest.approx(0.5) and deficits(ctx)["seguridad"] == 0.0
    assert onda.ef("Feedback")["feedback"].carga["valor"] == 0.0                     # sin latido previo
    _, onda2 = latido(2, 71.25, ef_anterior=onda.reactiva.ef)
    assert onda2.ef("Feedback")["feedback"].carga["por_impulso"]["hambre"] == pytest.approx(0.25)   # bajó el hambre


def test_tribunal_suma_el_plus_a_la_estrategia_en_curso():
    from ida.core.pieza import Pieza
    from ida.core.sentidos import Tribunal

    def candidato(id_, conf, origen=None):
        carga = {"verbo": Verbo.MOVER, "objetivo": id_, "clase": "", "motivo": "", "datos": {}}
        if origen:
            carga["origen"] = origen
        return Pieza(id_, "Accion", 0.5, conf, carga, sistema="S1")

    def decidir(activa: bool):
        estrategia = est.nueva("S1", _Huir(), "seguridad", 0.8, 0.0, 1)
        previa = Pieza("Accion", "Accion", carga={"verbo": Verbo.MOVER, "origen": {"estrategia": estrategia.id}})
        onda = Onda(2, 10, 1e9, ef_anterior={"Accion": {"Accion": previa}}, estrategias={estrategia.id: estrategia} if activa else {})
        ctx = _ctx(onda)
        onda.proponer("Accion", candidato("otro", 0.64))
        onda.proponer("Accion", candidato("seguir", 0.60, {"impulso": "seguridad", "estrategia": estrategia.id}))
        t = Tribunal()
        t.sistema = "CORE"
        t.reactiva(ctx)
        return ctx.extra["decision"].carga["objetivo"], onda.notas.get("plus_decide")

    assert decidir(activa=True) == ("seguir", True)         # 0,60 + 0,1 de plus supera a 0,64
    assert decidir(activa=False) == ("otro", None)          # cerrada: sin plus


# --- C1.5: S1 con impulsos, estrategias y reflejo ------------------------------------------------
def _s1_latido(n, activas, previo_ef, estrategia_comp, intensidad, perfil, ejecutada=None, alarmas=(None, None)):
    from ida.core.pieza import Pieza

    ef_anterior = dict(previo_ef or {})
    if ejecutada is not None:
        ef_anterior["Accion"] = {"Accion": Pieza("Accion", "Accion", carga={"verbo": Verbo.MOVER, "origen": {"estrategia": ejecutada}})}
    onda = Onda(n, 100, 1e9, ef_anterior=ef_anterior, estrategias=activas)
    ctx = Contexto(onda, Soma(), Memoria(), Arquetipo(), Azar(1), perfil, {Verbo.MOVER, Verbo.ESPERAR}, con_experiencia=False)
    imp = _comp(lambda: _Tipo("Impulso"))
    imp.registrar(ctx, imp.pieza(ctx, "seguridad", intensidad, carga={"intensidad": intensidad, "objetivo": 0.0, "rasgo": None}))
    estrategia_comp.reactiva(ctx)
    return onda


class _Tipo(Componente):
    def __init__(self, tipo):
        super().__init__(tipo)
        self.tipo = tipo


def _def(nombre, prioridad, elegible=lambda n: True, ultimo=False):
    class D(est.Definicion):
        impulsos = ("seguridad",)

        def elegible(self, ctx, impulso, intensidad):
            return elegible(ctx.latido)

        def actuar(self, ctx, estrategia):
            return est.Propuesta(Verbo.ESPERAR, "", 0.5, 0.5, nombre)

    d = D()
    d.nombre, d.prioridad, d.ultimo_recurso = nombre, prioridad, ultimo
    return d


def test_agotar_seguridad_cambia_de_estrategia_y_al_final_ultimo_recurso():
    from ida.sistemas.s1 import Estrategia

    perfil = Perfil(gracia_estrategia=0, enfriamiento_estrategia=1000)
    comp = _comp(lambda: Estrategia(est.Catalogo([_def("a", 10), _def("b", 5), _def("ultimo", 0, ultimo=True)])))
    activas: dict = {}
    vistas = []
    for n in range(1, 50):
        en_curso = next(iter(activas), None)
        _s1_latido(n, activas, None, comp, 0.9, perfil, ejecutada=en_curso)
        vistas.append(next(iter(activas.values())).carga["nombre"])
    assert vistas[0] == "a" and "b" in vistas and vistas[-1] == "ultimo"      # a → b → último recurso, sin soltar el impulso
    assert vistas.index("b") < vistas.index("ultimo")


def test_una_estrategia_mas_especifica_sustituye_a_la_activa():
    from ida.sistemas.s1 import Estrategia

    comp = _comp(lambda: Estrategia(est.Catalogo([_def("buscar", 5), _def("comer", 10, elegible=lambda n: n >= 3)])))
    activas: dict = {}
    nombres = []
    for n in range(1, 5):
        onda = _s1_latido(n, activas, None, comp, 0.6, Perfil())
        nombres.append(next(iter(activas.values())).carga["nombre"])
    assert nombres == ["buscar", "buscar", "comer", "comer"]
    assert onda.notas["estrategias_S1"]["activas"] == ["comer"]


def test_el_reflejo_salta_por_cambio_brusco_no_por_nivel():
    from ida.core.pieza import Pieza
    from ida.sistemas.s1 import Reflejo

    def sobresalto(antes, ahora):
        ef_anterior = {"Supervivencia": {"alarma": Pieza("alarma", "Supervivencia", carga={"peligro": antes})}}
        onda = Onda(2, 100, 1e9, ef_anterior=ef_anterior)
        ctx = _ctx(onda)
        onda.percibir("Supervivencia", Pieza("alarma", "Supervivencia", carga={"peligro": ahora, "clase_amenaza": "x"}))
        _comp(Reflejo).reactiva(ctx)
        return "sobresalto" in onda.ef("Reflejo")

    assert sobresalto(0.1, 0.6)                 # salto de 0,5 ≥ 0,4
    assert not sobresalto(0.7, 0.9)             # peligro alto pero sostenido: no es reflejo


def test_defensa_armada_de_crafter_lee_la_percepcion():
    from ida.core.pieza import Pieza
    from ida.mundos.crafter import DefensaArmada

    def eleccion(vitalidad, inventario):
        onda = Onda(1, 100, 1e9)
        ctx = _ctx(onda)
        onda.percibir("Interocepcion", Pieza("vitalidad", "Interocepcion", carga={"valor": vitalidad}))
        onda.percibir("Propiocepcion", Pieza("yo", "Propiocepcion", carga={"ubicacion": "celda_5_5", "inventario": inventario}))
        onda.percibir("Exterocepcion", Pieza("z1", "Exterocepcion", carga={"clase": "zombi", "rasgos": {"proximidad": 0.95, "peligro": 0.8}}))
        d = DefensaArmada()
        return d.elegible(ctx, "seguridad", 0.8), d.actuar(ctx, None)

    ok, propuesta = eleccion(6 / 9 * 100, {"wood_sword": 1})
    assert ok and propuesta.verbo == Verbo.ATACAR and propuesta.arousal == 0.96
    assert eleccion(6 / 9 * 100, {})[0] is False                  # sin espada en el inventario percibido
    assert eleccion(3 / 9 * 100, {"wood_sword": 1})[0] is False   # salud 3 < 4
