"""Paso 0 de la fase de generalización (docs/PROPUESTA_PASO0.md): la intensidad del impulso llega al Tribunal.

- 0a: urgencia local en ``Tribunal.reactiva`` (interruptor ``Perfil.mecanismos.urgencia_local``).
- 0b: aliestesia en la base (interruptor ``Perfil.mecanismos.aliestesia``): ``Memoria.satisface``,
  componente ``Apetencia`` de S1 y ``Alimentarse`` por necesidad.
"""

from dataclasses import replace
from typing import Dict, List, Optional, Tuple

import pytest

from ida.core.arquitectura import Contexto
from ida.core.azar import Azar
from ida.core.latido import Organismo
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.mundo import Efecto, Entidad, MecanismosMemoria, Mundo, Necesidad, Observacion, Perfil
from ida.core.onda import Onda
from ida.core.pieza import Pieza
from ida.core.sentidos import Tribunal
from ida.core.soma import Soma
from ida.core.vocabulario import Verbo
from ida.sistemas import crear_sistemas

CON_0A = Perfil(mecanismos=MecanismosMemoria(urgencia_local=True))


def _candidato(id_: str, impulso: str, arousal: float, confianza: float) -> Pieza:
    return Pieza(id_, "Accion", arousal, confianza, {"verbo": Verbo.MOVER, "objetivo": id_, "clase": "", "motivo": "", "datos": {},
                                                    "origen": {"impulso": impulso, "estrategia": f"est:{id_}"}}, sistema="S1")


def _decidir(perfil: Perfil, estres: float, impulsos: Dict[str, Tuple[str, float]],
             candidatos: List[Tuple[str, str, float, float]]) -> Tuple[str, list]:
    """Un Tribunal con ``impulsos`` (nombre → (canal, intensidad)) y ``candidatos`` (id, impulso, arousal, confianza)."""
    onda = Onda(1, 100, 1e9)
    for nombre, (canal, intensidad) in impulsos.items():
        onda.registrar(canal, Pieza(nombre, canal, intensidad, carga={"intensidad": intensidad, "objetivo": 0.0, "rasgo": None}))
    for c in candidatos:
        onda.proponer("Accion", _candidato(*c))
    ctx = Contexto(onda, Soma(estres=estres), Memoria(), Arquetipo(), Azar(1), perfil, set(Verbo), None, True)
    t = Tribunal()
    t.sistema = "CORE"
    t.reactiva(ctx)
    return ctx.extra["decision"].carga["objetivo"], onda.notas["evaluados"]


def test_interruptor_apagado_por_defecto():
    assert Perfil().mecanismos.urgencia_local is False


def test_urgencia_por_debajo_del_umbral_es_nula():
    assert Tribunal.UMBRAL_URGENCIA == 0.5
    assert Tribunal.urgencia(0.0) == 0.0 and Tribunal.urgencia(0.5) == 0.0
    assert Tribunal.urgencia(0.75) == pytest.approx(0.5)
    assert Tribunal.urgencia(1.0) == pytest.approx(1.0)


@pytest.mark.parametrize("semilla", range(20))
def test_invariancia_por_construccion_con_todas_las_intensidades_bajo_u(semilla):
    """Con todas las intensidades < U, encender 0a no cambia ninguna puntuación ni la decisión."""
    azar = Azar(semilla)
    impulsos = {f"n{i}": ("Impulso", round(azar.uniforme(0.0, 0.4999), 4)) for i in range(4)}
    candidatos = [(f"c{j}", f"n{j % 4}", round(azar.uniforme(0.0, 1.0), 3), round(azar.uniforme(0.35, 1.0), 3)) for j in range(6)]
    estres = round(azar.uniforme(0.0, 1.0), 3)
    sin = _decidir(Perfil(), estres, impulsos, candidatos)
    con = _decidir(CON_0A, estres, impulsos, candidatos)
    assert sin == con


def test_necesidad_apurada_gana_a_otra_con_mas_confianza_y_menos_urgencia():
    """En calma (estrés 0,1), la propuesta de una necesidad a 0,95 pierde sin 0a frente a otra de confianza 0,9
    cuyo impulso está a 0,1, y gana con 0a: su estrés local es u(0,95) = 0,9."""
    impulsos = {"sed": ("Impulso", 0.95), "cobijo": ("Impulso", 0.1)}
    candidatos = [("beber", "sed", 0.95, 0.5), ("refugio", "cobijo", 0.3, 0.9)]
    sin, ev_sin = _decidir(Perfil(), 0.1, impulsos, candidatos)
    con, ev_con = _decidir(CON_0A, 0.1, impulsos, candidatos)
    assert sin == "refugio"
    assert con == "beber"
    base = {e["id"]: e["base"] for e in ev_con}
    assert base["beber"] == pytest.approx(0.95 * 0.9 + 0.5 * 0.1, abs=1e-3)
    assert base["refugio"] == pytest.approx(0.3 * 0.1 + 0.9 * 0.9, abs=1e-3)   # su impulso está bajo U: estrés global


def test_con_estres_global_mayor_manda_el_global():
    """El estrés local es el máximo: con el cuerpo más estresado que la urgencia del impulso, no cambia nada."""
    impulsos = {"sed": ("Impulso", 0.6), "cobijo": ("Impulso", 0.1)}       # u(0,6) = 0,2 < 0,7
    candidatos = [("beber", "sed", 0.7, 0.5), ("refugio", "cobijo", 0.3, 0.9)]
    assert _decidir(Perfil(), 0.7, impulsos, candidatos) == _decidir(CON_0A, 0.7, impulsos, candidatos)


def test_las_intenciones_de_intensidad_fija_no_cambian():
    """Las intenciones del mundo tienen intensidad fija 0,5 (= U): su urgencia es 0 y su puntuación no cambia."""
    impulsos = {"progresar": ("Intencion", 0.5), "hambre": ("Impulso", 0.3)}
    candidatos = [("fabricar", "progresar", 0.5, 0.6), ("comer", "hambre", 0.65, 0.7)]
    for estres in (0.0, 0.3, 0.9):
        _, ev_sin = _decidir(Perfil(), estres, impulsos, candidatos)
        _, ev_con = _decidir(CON_0A, estres, impulsos, candidatos)
        assert ev_sin == ev_con


def test_el_interruptor_se_combina_con_los_demas_mecanismos():
    m = replace(MecanismosMemoria(), urgencia_local=True)
    assert m.urgencia_local and not m.buffer and not m.plan


# --- 0b: aliestesia en la base -------------------------------------------------------------------
# Mundo de juguete: dos necesidades (hambre y sed) y dos clases (baya y charca) que satisfacen cada una la suya.
# El mundo solo dice que las dos son nutritivas (rasgo perceptivo constante); qué satisface qué lo dice el manual
# o lo aprende la experiencia.

NECESIDADES_JUGUETE = (Necesidad("hambre", ("comida",), 95.0, "nutritivo"), Necesidad("sed", ("agua",), 95.0, "nutritivo"))
CON_0B = MecanismosMemoria(urgencia_local=True, aliestesia=True)
MANUAL_JUGUETE = {"hechos": [
    {"tipo": "proposicion", "sujeto": "baya", "relacion": "NUTRITIVO", "veredicto": "afirma", "necesidad": "hambre"},
    {"tipo": "proposicion", "sujeto": "charca", "relacion": "NUTRITIVO", "veredicto": "afirma", "necesidad": "sed"},
]}


class MundoDosNecesidades(Mundo):
    """Una baya y una charca siempre al alcance. Comer la baya sube la comida; beber de la charca, el agua."""

    nombre = "dos_necesidades"
    perfil = Perfil(vitales_propios=True, duerme=False, necesidades=NECESIDADES_JUGUETE, mecanismos=CON_0B)

    def __init__(self, gasto_comida: float = 2.0, gasto_agua: float = 3.0, manual: bool = False):
        self.gasto = {"comida": gasto_comida, "agua": gasto_agua}
        self.con_manual = manual
        self.vit = {"comida": 60.0, "agua": 60.0}

    def reiniciar(self, semilla):
        self.vit = {"comida": 60.0, "agua": 60.0}

    def observar(self) -> Observacion:
        for k, g in self.gasto.items():
            self.vit[k] = max(0.0, self.vit[k] - g)
        entidades = [Entidad("baya_1", "baya", {"proximidad": 1.0, "nutritivo": 0.6}, {"pos": (1, 0)}),
                     Entidad("charca_1", "charca", {"proximidad": 1.0, "nutritivo": 0.6}, {"pos": (0, 1)}),
                     Entidad("celda_a", "suelo", {"lugar": 1.0, "proximidad": 1.0, "novedad": 0.5}, {"pos": (0, 0)})]
        vitales = {"vitalidad": 100.0, "alimentacion": min(self.vit.values()), "energia": 100.0, "descanso": 100.0, **self.vit}
        return Observacion(ubicacion="celda_a", entidades=entidades, vitales=vitales)

    def ejecutar(self, verbo, objetivo, datos) -> Efecto:
        if verbo == Verbo.COMER:
            clave = "comida" if objetivo.startswith("baya") else "agua"
            antes = self.vit[clave]
            self.vit[clave] = min(100.0, self.vit[clave] + 25.0)
            # Como Crafter: comer o beber alimenta aunque la otra necesidad siga baja (``alimentacion`` del soma).
            return Efecto(exito=True, delta={"alimentacion": self.vit[clave] - antes}, obtenido=objetivo.split("_")[0])
        return Efecto(exito=True)

    def verbos(self):
        return {Verbo.COMER, Verbo.MOVER, Verbo.ESPERAR}

    def manual(self):
        return MANUAL_JUGUETE if self.con_manual else {}


def _ctx_juguete(comida: float, agua: float, memoria: Optional[Memoria] = None, mecanismos: MecanismosMemoria = CON_0B):
    """Contexto de S1 con la interocepción, los dos objetos al alcance y los impulsos de hambre y sed."""
    onda = Onda(1, 100, 1e9)
    perfil = Perfil(vitales_propios=True, necesidades=NECESIDADES_JUGUETE, mecanismos=mecanismos)
    for k, v in {"comida": comida, "agua": agua}.items():
        onda.percibir("Interocepcion", Pieza(k, "Interocepcion", carga={"valor": v, "delta": 0.0}, sistema="CORE"))
    for oid, clase, pos in (("baya_1", "baya", (1, 0)), ("charca_1", "charca", (0, 1))):
        rasgos = {"proximidad": 1.0, "nutritivo": 0.6}
        onda.percibir("Exterocepcion", Pieza(oid, "Exterocepcion", carga={"clase": clase, "rasgos": rasgos, "datos": {"pos": pos}}, sistema="CORE"))
        onda.percibir("Objeto", Pieza(oid, "Objeto", 0.5, carga={"clase": clase, "rasgos": rasgos}, sistema="S1"))
    for n in NECESIDADES_JUGUETE:
        i = n.deficit({"comida": comida, "agua": agua}) or 0.0
        onda.registrar("Impulso", Pieza(n.nombre, "Impulso", i, carga={"intensidad": i, "objetivo": 0.0, "rasgo": n.rasgo}, sistema="S1"))
    return Contexto(onda, Soma(), memoria or Memoria(), Arquetipo(), Azar(1), perfil, {Verbo.COMER, Verbo.MOVER, Verbo.ESPERAR}, None, True)


def _propuesta(ctx: Contexto, impulso: str):
    from ida.core.estrategia import nueva
    from ida.sistemas.s1 import Alimentarse

    d = Alimentarse()
    i = float(ctx.onda.ef("Impulso")[impulso].carga["intensidad"])
    assert d.elegible(ctx, impulso, i)
    p = nueva("S1", d, impulso, i, 0.0, 1)
    p = nueva("S1", d, impulso, i, 0.0, 1, paso=d.paso(ctx, p))
    return d.actuar(ctx, p)


def _apetencia(ctx: Contexto) -> None:
    from ida.sistemas.s1 import Apetencia

    a = Apetencia()
    a.sistema = "S1"
    a.reactiva(ctx)


def test_aliestesia_apagada_por_defecto_y_sin_piezas():
    assert Perfil().mecanismos.aliestesia is False
    ctx = _ctx_juguete(20.0, 90.0, mecanismos=MecanismosMemoria())
    _apetencia(ctx)
    assert ctx.onda.ev("Apetencia") == {}


def test_satisface_del_manual():
    mem = Memoria()
    mem.aplicar_manual(MANUAL_JUGUETE)
    assert mem.satisfaccion("baya") == {"hambre": pytest.approx(Memoria.CONFIANZA_MANUAL)}
    assert mem.satisfaccion("charca") == {"sed": pytest.approx(Memoria.CONFIANZA_MANUAL)}
    assert mem.satisfaccion("piedra") is None
    assert mem.satisface[("baya", "hambre")].fuente == "manual"


def test_satisface_de_la_experiencia_corrige_al_manual():
    mem = Memoria()
    mem.aplicar_manual(MANUAL_JUGUETE)
    for _ in range(4):
        mem.aprender_satisface("charca", {"hambre": False, "sed": True})
    s = mem.satisfaccion("charca")
    assert s is not None
    assert s["sed"] == pytest.approx((4 + Memoria.CONFIANZA_MANUAL) / 5)
    assert s["hambre"] == 0.0
    assert mem.satisface[("charca", "sed")].fuente == "manual+experiencia"


def test_apetencia_depende_del_estado_interno():
    """El deseo de cada objeto es Σ intensidad · satisface: con sed, la charca; con hambre, la baya."""
    mem = Memoria()
    mem.aplicar_manual(MANUAL_JUGUETE)
    for comida, agua, mas_deseado in ((90.0, 20.0, "charca_1"), (20.0, 90.0, "baya_1")):
        ctx = _ctx_juguete(comida, agua, mem)
        _apetencia(ctx)
        ap = ctx.onda.ev("Apetencia")
        assert max(ap, key=lambda k: ap[k].carga["deseo"]) == mas_deseado
        assert ap["charca_1"].carga["satisface"] == {"sed": pytest.approx(0.8)}


def test_cada_impulso_come_lo_que_satisface_su_necesidad():
    """Sin el interruptor, hambre y sed eligen el mismo objeto (por nutritivo); con él, cada una el suyo."""
    mem = Memoria()
    mem.aplicar_manual(MANUAL_JUGUETE)
    sin = _ctx_juguete(30.0, 40.0, mem, mecanismos=MecanismosMemoria())
    assert _propuesta(sin, "hambre").objetivo == _propuesta(sin, "sed").objetivo
    ctx = _ctx_juguete(30.0, 40.0, mem)
    _apetencia(ctx)
    hambre, sed = _propuesta(ctx, "hambre"), _propuesta(ctx, "sed")
    assert (hambre.verbo, hambre.objetivo) == (Verbo.COMER, "baya_1")
    assert (sed.verbo, sed.objetivo) == (Verbo.COMER, "charca_1")
    # El arousal sale de la intensidad del impulso de origen: el hambre (más apurada) propone con más arousal.
    assert hambre.arousal > sed.arousal


def test_sin_nada_que_satisfaga_su_necesidad_la_estrategia_no_es_elegible():
    from ida.sistemas.s1 import Alimentarse

    mem = Memoria()
    mem.aplicar_manual({"hechos": [MANUAL_JUGUETE["hechos"][0],
                                   {"tipo": "proposicion", "sujeto": "charca", "relacion": "NUTRITIVO", "veredicto": "afirma", "necesidad": "hambre"}]})
    ctx = _ctx_juguete(30.0, 30.0, mem)
    _apetencia(ctx)
    assert not Alimentarse().elegible(ctx, "sed", 0.68)


def test_en_una_vida_aprende_que_satisface_cada_clase_y_bebe_con_sed():
    """Sin manual: al principio las dos clases valen para las dos necesidades (rasgo ``nutritivo``); con la
    experiencia (qué constante sube al comer) cada clase queda asociada a su necesidad. Y en la segunda mitad
    de la vida, beber ocurre con la sed más apurada que el hambre."""
    mundo = MundoDosNecesidades()
    mundo.reiniciar(1)
    org = Organismo(mundo, crear_sistemas(), Arquetipo(), Memoria("completa"), Azar(1), True)
    comidas: List[Tuple[int, str, float, float]] = []

    def anotar(o, onda):
        ej = onda.reactiva.ef["Accion"]["Accion"]
        if ej.carga["verbo"] == Verbo.COMER:
            inten = {k: float(p.carga["intensidad"]) for k, p in onda.ef("Impulso").items()}
            comidas.append((o.ciclo, ej.carga["clase"], inten.get("hambre", 0.0), inten.get("sed", 0.0)))

    org.vivir(300, al_latir=anotar)
    s = org.memoria.satisface
    assert s[("baya", "hambre")].estimacion >= 0.9 and s[("charca", "sed")].estimacion >= 0.9
    assert s[("baya", "sed")].estimacion <= 0.1 and s[("charca", "hambre")].estimacion <= 0.1
    tarde = [c for c in comidas if c[0] > 150]
    agua = [c for c in tarde if c[1] == "charca"]
    assert tarde and agua
    assert sum(1 for c in agua if c[3] >= c[2]) >= 0.8 * len(agua)
    assert all(c[1] == "baya" for c in tarde if c[2] > c[3] + 0.2)


def test_crafter_con_aliestesia_el_nutritivo_es_perceptivo_y_constante():
    """Con el interruptor, el adaptador de Crafter no decide qué apetece: ``nutritivo`` vale 0,6 en lo que el
    manual declara NUTRITIVO (la planta, solo madura) y 0 en lo demás, sea cual sea la sed o el hambre."""
    pytest.importorskip("crafter")
    from ida.mundos.crafter import NUTRITIVO_MANUAL, MundoCrafter

    original = MundoCrafter.perfil
    try:
        MundoCrafter.perfil = replace(original, mecanismos=MecanismosMemoria(aliestesia=True))
        m = MundoCrafter(vista="oficial")
        m.reiniciar(1)
        assert m.nutritivos == {"agua", "vaca", "planta"}
        valores = set()
        for _ in range(60):
            obs = m.observar()
            valores |= {e.rasgos.get("nutritivo", 0.0) for e in obs.entidades if e.rasgos.get("lugar", 0.0) < 0.5}
            for e in obs.entidades:
                if e.clase in ("agua", "vaca"):
                    assert e.rasgos["nutritivo"] == NUTRITIVO_MANUAL
            m.ejecutar(Verbo.MOVER, f"celda_{m.jugador.pos[0] + 1}_{m.jugador.pos[1]}", {})
        assert valores <= {0.0, NUTRITIVO_MANUAL}
    finally:
        MundoCrafter.perfil = original


def test_crafter_interruptor_del_apano_de_sed_critica():
    """Criterio 4 del paso 0: el apaño de sed crítica de ``RefugioNocturno._motivacion`` (0,92) se puede quitar
    para medir si 0a lo sustituye. Por defecto sigue puesto."""
    pytest.importorskip("crafter")
    from ida.mundos.crafter import MundoCrafter

    assert MundoCrafter().estrategias_propias()["S2"][0].urgencia_sed is True
    assert MundoCrafter(urgencia_sed=0).estrategias_propias()["S2"][0].urgencia_sed is False
