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
    assert onda.ef("Feedback")["feedback:S1"].carga["valor"] == 0.0                     # sin latido previo
    _, onda2 = latido(2, 71.25, ef_anterior=onda.reactiva.ef)
    assert onda2.ef("Feedback")["feedback:S1"].carga["por_impulso"]["hambre"] == pytest.approx(0.25)   # bajó el hambre


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
    comp = _comp(lambda: Estrategia(est.Catalogo([_def("a", 10), _def("b", 5), _def("ultimo", 0, ultimo=True)]), impulso_critico="seguridad"))
    activas: dict = {}
    vistas = []
    for n in range(1, 50):
        en_curso = next(iter(activas), None)
        _s1_latido(n, activas, None, comp, 0.9, perfil, ejecutada=en_curso)
        vistas.append(next(iter(activas.values())).carga["nombre"])
    assert vistas[0] == "a" and "b" in vistas and vistas[-1] == "ultimo"      # a → b → último recurso, sin soltar el impulso
    assert vistas.index("b") < vistas.index("ultimo")


def test_sustituir_la_estrategia_activa_exige_un_margen_claro():
    from ida.sistemas.s1 import Estrategia

    def secuencia(prioridad_nueva):
        comp = _comp(lambda: Estrategia(est.Catalogo([_def("huir", 10), _def("plantar_cara", prioridad_nueva, elegible=lambda n: n >= 3)])))
        activas: dict = {}
        nombres = []
        for n in range(1, 5):
            onda = _s1_latido(n, activas, None, comp, 0.6, Perfil())
            nombres.append(next(iter(activas.values())).carga["nombre"])
        return nombres, onda

    nombres, _ = secuencia(15)          # 0,65 frente a 0,60: menos que el margen (0,2), sigue la activa
    assert nombres == ["huir"] * 4
    nombres, onda = secuencia(50)       # 1,00 frente a 0,60: margen claro, la sustituye
    assert nombres == ["huir", "huir", "plantar_cara", "plantar_cara"]
    assert onda.notas["estrategias_S1"]["activas"] == ["plantar_cara"]


def test_el_reflejo_salta_por_cambio_brusco_no_por_nivel():
    from ida.core.pieza import Pieza
    from ida.sistemas.s1 import Reflejo

    def sobresalto(antes, ahora, umbral_miedo=0.6):
        ef_anterior = {"Supervivencia": {"alarma": Pieza("alarma", "Supervivencia", carga={"peligro": antes})}}
        onda = Onda(2, 100, 1e9, ef_anterior=ef_anterior)
        ctx = _ctx(onda)
        ctx.arquetipo = Arquetipo(umbral_miedo=umbral_miedo)
        onda.percibir("Supervivencia", Pieza("alarma", "Supervivencia", carga={"peligro": ahora, "clase_amenaza": "x"}))
        _comp(Reflejo).reactiva(ctx)
        return "sobresalto" in onda.ef("Reflejo")

    assert sobresalto(0.1, 0.6)                 # salto de 0,5 ≥ 0,4 (umbral de miedo de referencia, 0,6)
    assert not sobresalto(0.7, 0.9)             # peligro alto pero sostenido: no es reflejo
    # El umbral escala con umbral_miedo: valiente (0,85) necesita ≥ 0,567; reactivo (0,35), ≥ 0,233
    assert not sobresalto(0.1, 0.6, umbral_miedo=0.85)
    assert sobresalto(0.1, 0.7, umbral_miedo=0.85)
    assert sobresalto(0.1, 0.35, umbral_miedo=0.35)


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


def test_seguir_en_movimiento_es_ultimo_recurso_sin_esperar_y_cede():
    from ida.core.pieza import Pieza
    from ida.sistemas.s1 import Estrategia, SeguirEnMovimiento

    comp = _comp(lambda: Estrategia(est.Catalogo([_def("comer", 10, elegible=lambda n: n >= 3), SeguirEnMovimiento()])))
    activas: dict = {}
    nombres = []
    for n in range(1, 5):
        onda = Onda(n, 100, 1e9, estrategias=activas)
        ctx = Contexto(onda, Soma(), Memoria(), Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER}, con_experiencia=False)
        onda.percibir("Exterocepcion", Pieza("celda", "Exterocepcion", carga={"clase": "suelo", "rasgos": {"lugar": 1.0}}))
        imp = _comp(lambda: _Tipo("Impulso"))
        imp.registrar(ctx, imp.pieza(ctx, "seguridad", 0.5, carga={"intensidad": 0.5, "objetivo": 0.0, "rasgo": None}))
        comp.reactiva(ctx)
        nombres.append([p.carga["nombre"] for p in activas.values()])
    assert nombres == [["seguir_en_movimiento"], ["seguir_en_movimiento"], ["comer"], ["comer"]]


def test_alimentarse_elige_el_objeto_por_valor_y_si_se_valora_mal_vuelve_a_buscar():
    from ida.core.pieza import Pieza
    from ida.sistemas.s1 import Alimentarse

    def fase(valencia):
        ef_anterior = {"Valor": {"s1": Pieza("s1", "Valor", carga={"valencia": valencia})}}
        onda = Onda(2, 100, 1e9, ef_anterior=ef_anterior)
        ctx = Contexto(onda, Soma(alimentacion=50.0), Memoria(), Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER, Verbo.COMER})
        onda.percibir("Objeto", Pieza("s1", "Objeto", 0.5, carga={"clase": "x", "rasgos": {"nutritivo": 0.8, "proximidad": 0.95}}))
        onda.percibir("Exterocepcion", Pieza("c1", "Exterocepcion", carga={"clase": "suelo", "rasgos": {"lugar": 1.0, "novedad": 0.6}}))
        d = Alimentarse()
        e = est.nueva("S1", d, "hambre", 0.5, 0.0, 2)
        e = est.nueva("S1", d, "hambre", 0.5, 0.0, 2, paso=d.paso(ctx, e))
        return e.carga["paso"], d.actuar(ctx, e)

    paso, propuesta = fase(0.3)
    assert paso == "comer" and propuesta.verbo == Verbo.COMER and propuesta.objetivo == "s1"
    paso, propuesta = fase(-0.3)                 # se valora mal: no se come, se busca en otro sitio
    assert paso == "buscar" and propuesta.verbo == Verbo.MOVER and propuesta.objetivo == "c1"


# --- Decisión 7 del autor sobre C1 ---------------------------------------------------------------
def _latido_con_feedback(n, activas, comp, intensidad, feedback, ejecutada):
    from ida.core.pieza import Pieza

    ef_anterior = {}
    if ejecutada is not None:
        ef_anterior["Accion"] = {"Accion": Pieza("Accion", "Accion", carga={"verbo": Verbo.MOVER, "origen": {"estrategia": ejecutada}})}
    onda = Onda(n, 100, 1e9, ef_anterior=ef_anterior, estrategias=activas)
    ctx = Contexto(onda, Soma(), Memoria(), Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER, Verbo.ESPERAR})
    fb = _comp(lambda: _Tipo("Feedback"))
    fb.registrar(ctx, fb.pieza(ctx, "feedback:S1", 0.0, carga={"por_impulso": {"seguridad": feedback}}))
    imp = _comp(lambda: _Tipo("Impulso"))
    imp.registrar(ctx, imp.pieza(ctx, "seguridad", intensidad, carga={"intensidad": intensidad, "objetivo": 0.0, "rasgo": None}))
    comp.reactiva(ctx)
    return onda


def test_el_valor_se_aprende_por_feedback_y_al_alcanzar_el_objetivo_queda_completada():
    from ida.sistemas.s1 import Estrategia

    comp = _comp(lambda: Estrategia(est.Catalogo([_def("a", 10)])))
    activas: dict = {}
    _latido_con_feedback(1, activas, comp, 0.8, 0.0, None)                    # se activa con intensidad 0,8
    p = activas["S1:a:seguridad"]
    _latido_con_feedback(2, activas, comp, 0.4, 0.4, p.id)                    # se ejecutó: el déficit bajó 0,4
    assert p.carga["merito"] == pytest.approx(0.4) and p.carga["estado"] == est.ACTIVA
    _latido_con_feedback(3, activas, comp, 0.0, 0.4, p.id)                    # objetivo alcanzado
    assert p.carga["estado"] == est.COMPLETADA and p.id not in activas
    # mérito 0,8 / tramo 0,8 = 1; valor = 0,5 + 0,5 × 0,8 (fuerza = intensidad inicial) × (1 − 0,5) = 0,7
    assert comp.valor[("seguridad", "a")] == pytest.approx(0.7)


def test_el_plus_por_estrategia_activa_se_apaga_al_acercarse_al_objetivo():
    from ida.core.pieza import Pieza
    from ida.core.sentidos import Tribunal

    def plus(progreso, agotamiento=0.0):
        e = est.nueva("S1", _Huir(), "seguridad", 0.8, 0.0, 1)
        e.carga.update({"progreso": progreso, "agotamiento": agotamiento})
        previa = Pieza("Accion", "Accion", carga={"verbo": Verbo.MOVER, "origen": {"estrategia": e.id}})
        onda = Onda(2, 10, 1e9, ef_anterior={"Accion": {"Accion": previa}}, estrategias={e.id: e})
        ctx = _ctx(onda)
        onda.proponer("Accion", Pieza("c", "Accion", 0.5, 0.6, {"verbo": Verbo.MOVER, "objetivo": "c", "clase": "", "motivo": "",
                                                               "datos": {}, "origen": {"estrategia": e.id}}, sistema="S1"))
        t = Tribunal()
        t.sistema = "CORE"
        t.reactiva(ctx)
        return onda.notas["evaluados"][0]["plus"]

    assert plus(0.0) == pytest.approx(0.1)
    assert plus(0.5) == pytest.approx(0.05)
    assert plus(0.9) == pytest.approx(0.01)
    assert plus(0.5, agotamiento=0.5) == pytest.approx(0.025)


def test_cerrar_una_estrategia_desde_un_autor_ajeno_se_rechaza():
    activas: dict = {}
    onda = Onda(1, 10, 1e9, estrategias=activas)
    p = onda.activar(est.nueva("S1", _Huir(), "seguridad", 0.8, 0.0, 1), _comp(_Estrategia))
    with pytest.raises(PiezaAjena):
        onda.cerrar(p, est.AGOTADA, _comp(_Otro))
    assert p.id in activas and p.carga["estado"] == est.ACTIVA


def test_con_la_seta_rechazada_al_alcance_y_una_baya_a_la_vista_va_hacia_la_baya():
    """Caso de la semilla 7 del Valiente en el mínimo: el olor del lugar lleva a la seta (0,7, al lado),
    más que a la baya (0,6, a tres casillas); la estrategia debe ir hacia la baya, no buscar ni volver."""
    from ida.core.pieza import Pieza
    from ida.sistemas.s1 import Alimentarse

    ef_anterior = {"Valor": {"seta": Pieza("seta", "Valor", carga={"valencia": -0.2})}}
    onda = Onda(2, 100, 1e9, ef_anterior=ef_anterior)
    ctx = Contexto(onda, Soma(alimentacion=30.0), Memoria(), Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER, Verbo.COMER})
    for pid, clase, prox, pos in (("seta", "seta", 1.0, (1, 0)), ("baya", "baya", 0.4, (0, 3))):
        rasgos = {"nutritivo": 0.75, "proximidad": prox}
        onda.percibir("Exterocepcion", Pieza(pid, "Exterocepcion", carga={"clase": clase, "rasgos": rasgos, "datos": {"pos": pos}}))
        onda.percibir("Objeto", Pieza(pid, "Objeto", 0.5, carga={"clase": clase, "rasgos": rasgos}))
    for pid, nutritivo, pos in (("celda_1_0", 0.7, (1, 0)), ("celda_0_1", 0.6, (0, 1)), ("celda_-1_0", 0.0, (-1, 0))):
        onda.percibir("Exterocepcion", Pieza(pid, "Exterocepcion", carga={"clase": "pradera", "datos": {"pos": pos},
                                                                       "rasgos": {"lugar": 1.0, "nutritivo": nutritivo, "novedad": 0.5}}))
    d = Alimentarse()
    e = est.nueva("S1", d, "hambre", 0.7, 0.0, 2)
    e = est.nueva("S1", d, "hambre", 0.7, 0.0, 2, paso=d.paso(ctx, e))
    propuesta = d.actuar(ctx, e)
    assert e.carga["paso"] == "acercarse"
    assert propuesta.verbo == Verbo.MOVER and propuesta.objetivo == "celda_0_1"      # hacia la baya, no hacia la seta


def test_feedback_de_s2_placer_y_estres():
    from ida.sistemas.s2 import Feedback

    onda1 = Onda(1, 100, 1e9)
    ctx1 = Contexto(onda1, Soma(placer=20.0, estres=0.5), Memoria(), Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER})
    fb = _comp(Feedback)
    fb.sistema = "S2"
    fb.reactiva(ctx1)
    onda2 = Onda(2, 100, 1e9, ef_anterior=onda1.reactiva.ef)
    ctx2 = Contexto(onda2, Soma(placer=40.0, estres=0.3), Memoria(), Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER})
    fb.reactiva(ctx2)
    assert onda2.ef("Feedback")["feedback:S2"].carga["valor"] == pytest.approx(0.2 + 0.2)     # más placer, menos estrés


def test_intencion_saber_y_las_del_mundo():
    from ida.core.memoria import Proposicion
    from ida.core.pieza import Pieza
    from ida.core.vocabulario import Relacion
    from ida.sistemas.s3 import Intencion

    mem = Memoria()
    mem.saber[("x", Relacion.NUTRITIVO)] = Proposicion("x", Relacion.NUTRITIVO, confianza=0.3)
    onda = Onda(1, 100, 1e9)
    ctx = Contexto(onda, Soma(), mem, Arquetipo(), Azar(1), Perfil(intenciones=("progresar",)), {Verbo.MOVER})
    onda.percibir("Objeto", Pieza("o1", "Objeto", 0.5, carga={"clase": "x", "rasgos": {}}))
    i = _comp(Intencion)
    i.sistema = "S3"
    i.reactiva(ctx)
    assert onda.ef("Intencion")["saber"].carga["intensidad"] == 1.0          # todo lo que sabe de x es hipótesis
    assert onda.ef("Intencion")["progresar"].carga["intensidad"] == 0.5


def test_estrategias_de_conocimiento_de_s3_actuan_sobre_la_conclusion_de_logica():
    from ida.core.pieza import Pieza
    from ida.sistemas.s3 import ComerLoNutritivo

    onda = Onda(1, 100, 1e9)
    ctx = Contexto(onda, Soma(), Memoria(), Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER, Verbo.COMER})
    onda.percibir("Objeto", Pieza("b1", "Objeto", 0.5, carga={"clase": "b", "rasgos": {"proximidad": 0.95}}))
    onda.percibir("Logica", Pieza("conclusion", "Logica", 0.6, 0.9, carga={"conclusion": "COMER", "objetivo": "b1", "texto": "b nutre"}))
    d = ComerLoNutritivo()
    propuesta = d.actuar(ctx, None)
    assert d.elegible(ctx, "hambre", 0.5) and propuesta.verbo == Verbo.COMER and propuesta.objetivo == "b1"
    assert propuesta.confianza == 0.9


def test_alimentarse_con_prudencia_rechaza_indicios_de_dano_y_lo_desconocido():
    from ida.core.memoria import Proposicion
    from ida.core.pieza import Pieza
    from ida.core.vocabulario import Relacion
    from ida.mundos.archivos import AlimentarseConPrudencia

    mem = Memoria()
    mem.saber[("mala", Relacion.PELIGROSO)] = Proposicion("mala", Relacion.PELIGROSO, confianza=0.4)
    buena = Proposicion("buena", Relacion.NUTRITIVO, confianza=0.95)
    buena.confirmaciones = 10
    mem.saber[("buena", Relacion.NUTRITIVO)] = buena
    onda = Onda(5, 100, 1e9)
    ctx = Contexto(onda, Soma(), mem, Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER, Verbo.COMER})
    for clase in ("mala", "nueva", "buena"):
        onda.percibir("Exterocepcion", Pieza(clase, "Exterocepcion", carga={"clase": clase, "rasgos": {}}))
    d = AlimentarseConPrudencia()
    assert d.nombre == "alimentarse"                                   # sustituye a la genérica en su mundo
    assert d.rechaza(ctx, Pieza("m", "Objeto", carga={"clase": "mala"}))      # indicios de daño (0,4 ≥ 0,35)
    assert mem.demostrada("buena", Relacion.NUTRITIVO, 5)
    assert d.rechaza(ctx, Pieza("n", "Objeto", carga={"clase": "nueva"}))      # neofobia: hay algo que se sabe que nutre
    assert not d.rechaza(ctx, Pieza("b", "Objeto", carga={"clase": "buena"}))


def test_s3_controla_los_impulsos_segun_la_certeza_y_el_tribunal_lo_suma():
    from ida.core.memoria import Proposicion
    from ida.core.pieza import Pieza
    from ida.core.sentidos import Tribunal
    from ida.core.vocabulario import Relacion
    from ida.sistemas.s3 import Creencia
    from ida.sistemas.s3 import Impulso as ImpulsoS3

    mem = Memoria()
    p = Proposicion("lobo", Relacion.PELIGROSO, confianza=0.9)
    p.confirmaciones = 10
    mem.saber[("lobo", Relacion.PELIGROSO)] = p
    onda = Onda(5, 100, 1e9)
    ctx = Contexto(onda, Soma(estres=1.0), mem, Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER})
    onda.percibir("Objeto", Pieza("l1", "Objeto", 0.5, carga={"clase": "lobo", "rasgos": {"proximidad": 0.8}}))
    s1 = _comp(lambda: _Tipo("Impulso"))
    seg = s1.registrar(ctx, s1.pieza(ctx, "seguridad", 0.5, carga={"intensidad": 0.5, "objetivo": 0.0, "rasgo": None}))
    _comp(Creencia).reactiva(ctx)                                            # S3·Interpretar: lo que sostiene
    control = _comp(ImpulsoS3)
    control.sistema = "S3"
    control.reactiva(ctx)
    trust = onda.ef("Creencia")["lobo|PELIGROSO"].carga["trust"]
    assert trust == pytest.approx(0.9 / 1.1, abs=1e-3)                        # sin valor de S2: fuente afectiva 0
    assert seg.arousal == pytest.approx(0.5 + 0.2 * trust)                   # sube en proporción a la certeza
    onda.proponer("Accion", Pieza("a", "Accion", 0.5, 0.5, {"verbo": Verbo.MOVER, "objetivo": "a", "clase": "", "motivo": "",
                                                          "datos": {}, "origen": {"impulso": "seguridad"}}, sistema="S1"))
    t = Tribunal()
    t.sistema = "CORE"
    t.reactiva(ctx)
    assert onda.notas["evaluados"][0]["base"] == pytest.approx(0.5 + 0.2 * trust, abs=1e-3)  # el Tribunal suma la modulación (estrés 1)


def test_feedback_de_s3_error_de_prediccion():
    from ida.sistemas.s3 import Feedback

    mem = Memoria()
    onda1 = Onda(1, 100, 1e9)
    fb = _comp(Feedback)
    fb.sistema = "S3"
    fb.reactiva(Contexto(onda1, Soma(), mem, Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER}))
    mem.aciertos, mem.fallos = mem.aciertos + 3, mem.fallos + 1
    onda2 = Onda(2, 100, 1e9, ef_anterior=onda1.reactiva.ef)
    fb.reactiva(Contexto(onda2, Soma(), mem, Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER}))
    assert onda2.ef("Feedback")["feedback:S3"].carga["valor"] == 2.0


def test_valencia_explicita_en_soma_y_emocion():
    from ida.sistemas.s2 import Emocion

    assert Soma(placer=60.0, estres=0.2).valencia == pytest.approx(0.4)
    assert Soma(placer=0.0, estres=0.9).valencia == pytest.approx(-0.9)
    onda = Onda(1, 100, 1e9)
    ctx = Contexto(onda, Soma(placer=60.0, estres=0.2), Memoria(), Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER})
    e = _comp(Emocion)
    e.reactiva(ctx)
    p = onda.ef("Emocion")["emocion"]
    assert p.carga["valencia"] == pytest.approx(0.4) and p.arousal == pytest.approx(0.2)


def test_habituacion_y_sensibilizacion_en_supervivencia():
    from ida.core.memoria import Proposicion
    from ida.core.pieza import Pieza
    from ida.core.vocabulario import Relacion
    from ida.sistemas.s1 import relacion_supervivencia

    mem = Memoria()
    ctx = Contexto(Onda(5, 100, 1e9), Soma(), mem, Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER})
    sombra = Pieza("s", "Objeto", carga={"clase": "sombra", "rasgos": {}})
    assert relacion_supervivencia(ctx, sombra, 0.4, 0.0) == ("neutro", 0.0, 1.0)            # desconocido
    mem.clases_vistas["sombra"] = 20                                                        # 20 encuentros sin daño
    categoria, trust, factor = relacion_supervivencia(ctx, sombra, 0.4, 0.0)
    assert categoria == "neutro" and trust == 1.0 and factor == pytest.approx(0.6)          # habituado
    mem.saber[("sombra", Relacion.PELIGROSO)] = Proposicion("sombra", Relacion.PELIGROSO, confianza=0.8)
    categoria, trust, factor = relacion_supervivencia(ctx, sombra, 0.4, 0.0)
    assert categoria == "peligro" and factor == pytest.approx(1.4)                          # sensibilizado tras un daño


def test_valor_con_cuatro_dimensiones_y_valencia_combinada():
    from ida.core.pieza import Pieza
    from ida.sistemas.s2 import Valor

    onda = Onda(1, 100, 1e9)
    ctx = Contexto(onda, Soma(alimentacion=10.0), Memoria(), Arquetipo(neuroticismo=0.5), Azar(1), Perfil(), {Verbo.MOVER})
    onda.percibir("Objeto", Pieza("v1", "Objeto", 0.5, carga={"clase": "v", "rasgos": {"nutritivo": 0.8, "peligro": 0.4, "agente": 1.0}}))
    _comp(Valor).reactiva(ctx)
    c = onda.ev("Valor")["v1"].carga
    assert set(c) >= {"motivacional", "potencia", "sentimental", "social", "valencia"} and c["social"] == 0.0
    assert c["potencia"] == pytest.approx(0.4)
    assert c["valencia"] == pytest.approx(0.5 * c["motivacional"] + 0.5 * c["sentimental"] - 0.4 * 0.5, abs=1e-3)


def test_creencia_con_trust_y_fuentes_incluida_la_afectiva():
    from ida.core.memoria import Proposicion
    from ida.core.pieza import Pieza
    from ida.core.vocabulario import Relacion
    from ida.sistemas.s3 import Creencia

    mem = Memoria()
    mem.saber[("x", Relacion.PELIGROSO)] = Proposicion("x", Relacion.PELIGROSO, confianza=0.5, heredada=True)
    onda = Onda(3, 100, 1e9)
    ctx = Contexto(onda, Soma(), mem, Arquetipo(), Azar(1), Perfil(), {Verbo.MOVER})
    onda.percibir("Valor", Pieza("o", "Valor", carga={"clase": "x", "valencia": -0.6}))
    _comp(Creencia).reactiva(ctx)
    c = onda.ef("Creencia")["x|PELIGROSO"].carga
    assert c["fuentes"]["herencia"] is True and c["fuentes"]["afectiva"] == pytest.approx(0.6)
    assert c["trust"] == pytest.approx((0.5 + 0.1 * 0.6) / 1.1, abs=1e-3) and c["sostiene"] is False
