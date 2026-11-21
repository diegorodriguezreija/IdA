"""Paso 5 de la fase de generalización: metas, planificador general (PerseguirMetas) y aprendizaje de requisitos."""

from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest

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

    def ef(self, canal: str) -> Dict[str, Pieza]:      # lo registrado en el latido (p. ej. peticiones): nada en estos tests
        return {}


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


def test_meta_del_manual_no_se_bloquea():
    """Una acción que el manual declara (meta o requisito) puede salir aunque falle seguido: no se bloquea, y su
    tasa estimada cuenta la declaración como un éxito. Una que nadie declara y nunca ha funcionado, sí se bloquea."""
    m = Memoria()
    m.aplicar_manual({"hechos": [{"tipo": "meta", "verbo": "COGER", "objetivo": "hierba"}]})
    for _ in range(3):
        m.aprender_requisito(Verbo.COGER, "hierba", {}, {}, set(), False)
        m.aprender_requisito(Verbo.COGER, "piedra", {}, {}, set(), False)
    assert m.puede_salir(Verbo.COGER, "hierba") and not m.bloqueada(Verbo.COGER, "hierba")
    assert m.tasa_estimada(Verbo.COGER, "hierba") == 1.0 / 4.0          # (0 + 1) / (0 + 3 + 1)
    assert not m.puede_salir(Verbo.COGER, "piedra") and m.bloqueada(Verbo.COGER, "piedra")
    assert m.tasa_estimada(Verbo.COGER, "piedra") == 0.0


def test_el_coste_del_paso_es_uno_entre_la_tasa():
    """El planificador cuenta los fallos esperados antes del éxito: 1 / tasa − 1. Con 3 fallos y la declaración
    del manual (tasa 1/4), 3; sin intentos, 0, como una acción que siempre funciona."""
    m = Memoria()
    m.aplicar_manual({"inventario": [], "hechos": [{"tipo": "meta", "verbo": "COGER", "objetivo": "hierba"}]})
    plan = PerseguirMetas()
    ctx = _ctx(m, [_entidad("hierba_1", "hierba", 1.0)], {})
    assert plan._resolver(ctx, (Verbo.COGER, "hierba"), {}, frozenset(), 0).coste == 0.0
    for _ in range(3):
        m.aprender_requisito(Verbo.COGER, "hierba", {}, {}, set(), False)
    paso = plan._resolver(ctx, (Verbo.COGER, "hierba"), {}, frozenset(), 0)
    assert (paso.verbo, paso.objetivo) == (Verbo.COGER, "hierba_1")
    assert paso.coste == pytest.approx(3.0)


def test_donde_se_puede_colocar_y_lo_que_aparece():
    m = Memoria()
    m.aplicar_manual(MANUAL)
    m.aprender_requisito(Verbo.USAR, "hacer_a", {"b": 1.0}, {"b": 1.0}, set(), True, delante="agua")
    m.aprender_requisito(Verbo.USAR, "hacer_a", {"b": 1.0}, {"b": 0.0}, set(), True, cerca_despues={"a"}, delante="suelo")
    r = m.requisitos[(Verbo.USAR, "hacer_a")]
    assert r.requiere_delante == {"suelo"} and r.delante_fallido == {"agua"} and r.aparece == {"a"}


def test_exploracion_de_efectos_prueba_lo_de_delante():
    m = Memoria()
    # Sin plan: la meta requiere una llave que ninguna acción conocida da. (Antes se forzaba con la meta bloqueada
    # por fallos seguidos; una meta del manual ya no se bloquea: ver test_meta_del_manual_no_se_bloquea.)
    m.aplicar_manual({"hechos": [{"tipo": "meta", "verbo": "USAR", "objetivo": "imposible"},
                                 {"tipo": "requisito", "verbo": "USAR", "objetivo": "imposible", "requiere_inventario": {"llave": 1}}],
                      "inventario": ["llave"]})
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


# --- Efecto probabilístico en un mundo de juguete ---------------------------------------------------------------
class MundoRetono:
    """Hierba siempre al alcance. COGER hierba da un retoño con probabilidad ``p`` (como en Crafter, 0,1); si no sale,
    no es éxito. El manual solo declara la meta (coger hierba con efecto), no la probabilidad."""

    def __new__(cls, *a, **k):
        from ida.core.mundo import Efecto, Entidad, Mundo, Observacion, Perfil

        class _Mundo(Mundo):
            nombre = "retono"
            perfil = Perfil(vitales_propios=True, duerme=False, intenciones=("progresar",))

            def __init__(self, p: float = 0.1, semilla: int = 1):
                import random

                self.p, self.azar, self.inv = p, random.Random(semilla), {"reton": 0.0}
                self.intentos = 0

            def reiniciar(self, semilla):
                self.inv = {"reton": 0.0}

            def observar(self):
                entidades = [Entidad("hierba_1", "hierba", {"proximidad": 1.0}, {"pos": (1, 0)}),
                             Entidad("celda_a", "suelo", {"lugar": 1.0, "proximidad": 1.0, "novedad": 0.0}, {"pos": (0, 0)})]
                vitales = {"vitalidad": 100.0, "alimentacion": 100.0, "energia": 100.0, "descanso": 100.0}
                return Observacion(ubicacion="celda_0_0", entidades=entidades, vitales=vitales, inventario=dict(self.inv),
                                   cuerpo={"delante": {"id": "hierba_1", "clase": "hierba"}})

            def ejecutar(self, verbo, objetivo, datos):
                if verbo == Verbo.COGER and objetivo.startswith("hierba"):
                    self.intentos += 1
                    if self.azar.random() < self.p:
                        self.inv["reton"] += 1
                        return Efecto(exito=True, obtenido="reton")
                    return Efecto(exito=False)
                return Efecto(exito=True)

            def verbos(self):
                return {Verbo.COGER, Verbo.MOVER, Verbo.ESPERAR}

            def manual(self):
                return {"inventario": ["reton"], "hechos": [{"tipo": "meta", "verbo": "COGER", "objetivo": "hierba"}]}

        return _Mundo(*a, **k)


def _vivir_retono(semilla: int, latidos: int = 150):
    from ida.core.azar import Azar
    from ida.core.latido import Organismo
    from ida.core.linaje import Arquetipo
    from ida.sistemas import crear_sistemas

    mundo = MundoRetono(p=0.1, semilla=semilla)
    memoria = Memoria()
    memoria.aplicar_manual(mundo.manual())
    org = Organismo(mundo, crear_sistemas(), Arquetipo(), memoria, Azar(semilla), con_experiencia=True)
    bloqueos = []
    org.vivir(latidos, al_latir=lambda o, _onda: bloqueos.append(o.memoria.bloqueada(Verbo.COGER, "hierba")))
    return mundo, org.memoria, bloqueos


@pytest.mark.parametrize("semilla", range(1, 11))
def test_efecto_con_probabilidad_0_1_no_se_bloquea_y_acaba_saliendo(semilla):
    """Con el bloqueo por 3 fallos seguidos, el retoño no saldría en el 73 % de las vidas (0,9³). La meta del manual
    dice que puede salir: no se bloquea nunca y se sigue intentando hasta conseguirlo."""
    mundo, memoria, bloqueos = _vivir_retono(semilla)
    assert not any(bloqueos)
    assert memoria.metas[(Verbo.COGER, "hierba")].conseguida and mundo.inv["reton"] >= 1


# --- reutilizar lo construido: ir a la X recordada frente a producir otra -----------------------------------------
MANUAL_BANCO = {
    "inventario": ["madera"],
    "hechos": [
        {"tipo": "meta", "verbo": "USAR", "objetivo": "hacer_a"},
        {"tipo": "requisito", "verbo": "USAR", "objetivo": "hacer_a", "requiere_inventario": {"madera": None}, "requiere_cerca": ["banco"]},
        {"tipo": "requisito", "verbo": "USAR", "objetivo": "poner_banco", "requiere_inventario": {"madera": None}, "aparece": ["banco"]},
        {"tipo": "requisito", "verbo": "COGER", "objetivo": "arbol", "requiere_inventario": {}, "efecto": {"madera": 1}},
    ],
}


def _pasillo(banco_en: int, consumo_aprendido: bool = True) -> Any:
    """Un pasillo de suelo recordado (mapa local) de (0, 0) a (banco_en − 1, 0) y un banco en (banco_en, 0), fuera de la vista.
    Con ``consumo_aprendido``, la experiencia ya sabe que poner un banco gasta una madera."""
    m = Memoria()
    m.aplicar_manual(MANUAL_BANCO)
    m.casillas.update({(x, 0): "suelo" for x in range(banco_en)})
    m.casillas[(banco_en, 0)] = "banco"
    m.paso_libre["suelo"] = 1
    m.paso_bloqueado["banco"] = 1
    if consumo_aprendido:
        m.aprender_requisito(Verbo.USAR, "poner_banco", {"madera": 2.0}, {"madera": 1.0}, set(), True, cerca_despues={"banco"})
    lugar = _entidad("celda_1_0", "suelo", 1.0, lugar=1.0, pos=(1, 0))
    return _ctx(m, [lugar], {"madera": 2.0}, ubicacion="celda_0_0")


def test_va_al_banco_recordado_si_cuesta_menos_que_poner_otro():
    """Poner otro banco gasta una madera, y aquí no hay de dónde sacar más (coste alto de reponerla): con el banco
    recordado a 6 pasos, el planificador vuelve a él por el mapa local en vez de poner otro."""
    propuestas = PerseguirMetas().actuar(_pasillo(7), None)
    assert [(p.verbo, p.objetivo) for p in propuestas] == [(Verbo.MOVER, "celda_1_0")]
    assert "volver a banco (mapa, 6 pasos)" in propuestas[0].motivo


def test_pone_otro_banco_si_el_recordado_queda_mas_caro():
    """Con el banco recordado a 37 pasos, reponer la madera (30) más poner el banco cuesta menos: pone otro."""
    propuestas = PerseguirMetas().actuar(_pasillo(38), None)
    assert [(p.verbo, p.objetivo) for p in propuestas] == [(Verbo.USAR, "poner_banco")]


def test_sin_saber_lo_que_consume_poner_es_casi_gratis():
    """Sin experiencia de lo que consume poner un banco, producir no cuesta reponer nada y gana aunque el recordado esté cerca."""
    propuestas = PerseguirMetas().actuar(_pasillo(7, consumo_aprendido=False), None)
    assert [(p.verbo, p.objetivo) for p in propuestas] == [(Verbo.USAR, "poner_banco")]


def test_primero_lo_que_se_lleva_despues_el_sitio():
    """Sin madera, con un árbol a la vista en otra dirección (más caro que el banco, recordado a 6 pasos): primero va a por
    la madera (lo que se usa junto al banco) y no al banco, que obligaría a volver."""
    ctx = _pasillo(7)
    ctx.onda.canales["Exterocepcion"]["arbol_1"] = _entidad("arbol_1", "arbol", 0.2, pos=(0, 8))
    ctx.onda.canales["Exterocepcion"]["celda_0_1"] = _entidad("celda_0_1", "suelo", 1.0, lugar=1.0, pos=(0, 1))
    ctx.onda.canales["Propiocepcion"]["yo"].carga["inventario"] = {}
    propuestas = PerseguirMetas().actuar(ctx, None)
    assert [(p.verbo, p.objetivo) for p in propuestas] == [(Verbo.MOVER, "celda_0_1")]
