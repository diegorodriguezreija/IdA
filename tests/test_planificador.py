"""Paso 5 de la fase de generalización: metas, planificador general (PerseguirMetas) y aprendizaje de requisitos."""

from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from ida.core.memoria import Memoria
from ida.core.pieza import Pieza
from ida.core.vocabulario import Verbo
from ida.sistemas.s3 import PerseguirMetas

# Mundo de juguete: la meta es USAR «hacer_a», que requiere B; B se obtiene cogiendo C.
MANUAL = {
    "inventario": ["b", "llave"],
    "hechos": [
        {"tipo": "meta", "verbo": "USAR", "objetivo": "hacer_a"},
        {"tipo": "requisito", "verbo": "USAR", "objetivo": "hacer_a", "requiere_inventario": {"b": None}},
        {"tipo": "requisito", "verbo": "COGER", "objetivo": "c", "requiere_inventario": {}, "efecto": {"b": 1}},
    ],
}


class _Onda:
    def __init__(self, canales: Dict[str, Dict[str, Pieza]]):
        self.canales = canales

    def ev(self, canal: str) -> Dict[str, Pieza]:
        return self.canales.get(canal, {})


def _entidad(id_: str, clase: str, proximidad: float, lugar: float = 0.0, pos: Optional[tuple] = None) -> Pieza:
    return Pieza(id=id_, tipo="Exterocepcion", carga={"clase": clase, "rasgos": {"proximidad": proximidad, "lugar": lugar},
                                                       "datos": {"pos": pos} if pos else {}})


def _ctx(memoria: Memoria, entidades: List[Pieza], inventario: Dict[str, float], delante: Optional[Dict[str, str]] = None,
         latido: int = 1, ubicacion: str = "aqui") -> Any:
    yo = Pieza(id="yo", tipo="Propiocepcion", carga={"inventario": inventario, "cuerpo": {"delante": delante} if delante else {}})
    onda = _Onda({"Exterocepcion": {e.id: e for e in entidades}, "Propiocepcion": {"yo": yo}})
    return SimpleNamespace(memoria=memoria, onda=onda, con_experiencia=True, latido=latido,
                           observacion=SimpleNamespace(ubicacion=ubicacion), verbos=set(Verbo))


def test_planificador_encadena_hacia_atras():
    m = Memoria()
    m.aplicar_manual(MANUAL)
    ctx = _ctx(m, [_entidad("c_1", "c", 1.0)], {})
    plan = PerseguirMetas()
    assert plan.elegible(ctx, "progresar", 0.5)
    propuestas = plan.actuar(ctx, None)
    assert [(p.verbo, p.objetivo) for p in propuestas] == [(Verbo.COGER, "c_1")]
    assert propuestas[0].motivo == "metas: hacer_a ← falta b ← COGER c"

    ctx = _ctx(m, [_entidad("c_1", "c", 1.0)], {"b": 1.0})      # con B ya se puede
    assert [(p.verbo, p.objetivo) for p in plan.actuar(ctx, None)] == [(Verbo.USAR, "hacer_a")]


def test_con_manual_vacio_no_es_elegible():
    m = Memoria()
    m.aplicar_manual({})
    assert not PerseguirMetas().elegible(_ctx(m, [], {}), "progresar", 0.5)


def test_meta_conseguida_por_inventario_o_por_vital():
    m = Memoria()
    m.aplicar_manual({"hechos": [{"tipo": "meta", "verbo": "USAR", "objetivo": "hacer_a"},
                                 {"tipo": "meta", "verbo": "COMER", "objetivo": "agua"}]})
    assert not m.registrar_meta(Verbo.USAR, "hacer_a", True, {"b": 1.0}, {"b": 1.0}, {})       # éxito sin efecto
    assert m.registrar_meta(Verbo.USAR, "hacer_a", True, {"b": 1.0}, {"b": 0.0}, {})
    assert not m.registrar_meta(Verbo.COMER, "agua", False, None, None, {"alimentacion": 11.0})
    assert m.registrar_meta(Verbo.COMER, "agua", True, None, None, {"alimentacion": 11.0})     # cambia una vital
    assert all(meta.conseguida for meta in m.metas.values())


def test_induccion_por_diferencia():
    m = Memoria()
    m.aprender_requisito(Verbo.COGER, "c", {}, {}, set(), True)                     # falla sin llave
    m.aprender_requisito(Verbo.COGER, "c", {"llave": 1.0}, {"llave": 1.0, "b": 1.0}, set(), True)
    r = m.requisitos[(Verbo.COGER, "c")]
    assert r.fuente == "experiencia" and r.requiere_inventario == {"llave": 1} and r.efecto == {"b": 1}


def test_reintento_tras_novedad():
    m = Memoria()
    for _ in range(3):
        m.aprender_requisito(Verbo.COGER, "c", {}, {}, set(), True)
    assert m.bloqueada(Verbo.COGER, "c")
    m.aprender_requisito(Verbo.COGER, "otra", {}, {"llave": 1.0}, set(), True)      # gana un objeto nuevo
    assert not m.bloqueada(Verbo.COGER, "c")


def test_efecto_probabilistico_no_se_bloquea():
    m = Memoria()
    m.aprender_requisito(Verbo.COGER, "c", {}, {"b": 1.0}, set(), True)
    for _ in range(5):
        m.aprender_requisito(Verbo.COGER, "c", {"b": 1.0}, {"b": 1.0}, set(), True)
    assert not m.bloqueada(Verbo.COGER, "c")


def test_donde_se_puede_colocar_y_lo_que_aparece():
    m = Memoria()
    m.aplicar_manual(MANUAL)
    m.aprender_requisito(Verbo.USAR, "hacer_a", {"b": 1.0}, {"b": 1.0}, set(), True, delante="agua")
    m.aprender_requisito(Verbo.USAR, "hacer_a", {"b": 1.0}, {"b": 0.0}, set(), True, cerca_despues={"a"}, delante="suelo")
    r = m.requisitos[(Verbo.USAR, "hacer_a")]
    assert r.requiere_delante == {"suelo"} and r.delante_fallido == {"agua"} and r.aparece == {"a"}


def test_exploracion_de_efectos_prueba_lo_de_delante():
    m = Memoria()
    m.aplicar_manual({"hechos": [{"tipo": "meta", "verbo": "USAR", "objetivo": "imposible"}],
                      "inventario": []})
    m.fallos_seguidos[(Verbo.USAR, "imposible")] = 3                                 # bloqueada: no hay plan
    ctx = _ctx(m, [], {}, delante={"id": "d_1_2", "clase": "d"}, latido=5)
    propuestas = PerseguirMetas().actuar(ctx, None)
    assert [(p.verbo, p.objetivo) for p in propuestas] == [(Verbo.COGER, "d_1_2")]


MANUAL_CERCA = {"hechos": [{"tipo": "meta", "verbo": "USAR", "objetivo": "hacer_x"},
                           {"tipo": "requisito", "verbo": "USAR", "objetivo": "hacer_x", "requiere_cerca": ["taller"]}]}


def test_prueba_antes_de_caminar_y_aprende_el_radio():
    m = Memoria()
    m.aplicar_manual(MANUAL_CERCA)
    vista = [_entidad("taller_2_0", "taller", 0.78, pos=(2, 0)), _entidad("celda_1_0", "suelo", 1.0, lugar=1.0, pos=(1, 0))]
    ctx = _ctx(m, vista, {}, ubicacion="celda_0_0")
    plan = PerseguirMetas()
    assert [(p.verbo, p.objetivo) for p in plan.actuar(ctx, None)] == [(Verbo.USAR, "hacer_x")]   # a 2: se prueba
    m.aprender_requisito(Verbo.USAR, "hacer_x", {}, {}, set(), True, distancias={"taller": (0, 2)})   # falla desde (0, 2)
    assert [(p.verbo, p.objetivo) for p in plan.actuar(ctx, None)] == [(Verbo.MOVER, "celda_1_0")]  # ahora camina

    m2 = Memoria()
    m2.aplicar_manual(MANUAL_CERCA)
    m2.aprender_requisito(Verbo.USAR, "hacer_x", {}, {"cosa": 1.0}, set(), True, distancias={"taller": (0, 2)})   # funciona
    assert m2.requisitos[(Verbo.USAR, "hacer_x")].cerca_ok == {"taller": {(0, 2)}}


def test_antibloqueo_aparca_un_destino_que_no_se_acerca():
    m = Memoria()
    m.aplicar_manual({"hechos": [{"tipo": "meta", "verbo": "COGER", "objetivo": "c"}]})
    vista = [_entidad("c_3_0", "c", 0.6, pos=(3, 0)), _entidad("celda_1_0", "suelo", 1.0, lugar=1.0, pos=(1, 0))]
    plan = PerseguirMetas()
    for latido in range(1, 10):     # 1 propuesta inicial + 8 sin acercarse (la posición no cambia)
        ctx = _ctx(m, vista, {}, ubicacion="celda_0_0", latido=latido)
        assert [(p.verbo, p.objetivo) for p in plan.actuar(ctx, None)] == [(Verbo.MOVER, "celda_1_0")]
    ctx = _ctx(m, vista, {}, ubicacion="celda_0_0", latido=11)
    assert plan.actuar(ctx, None) == []                                   # aparcado
    ctx = _ctx(m, vista, {}, ubicacion="celda_0_0", latido=9 + PerseguirMetas.APARCAR + 1)
    assert [(p.verbo, p.objetivo) for p in plan.actuar(ctx, None)] == [(Verbo.MOVER, "celda_1_0")]   # vuelve a intentarlo
