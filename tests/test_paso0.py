"""Paso 0 de la fase de generalización (docs/PROPUESTA_PASO0.md): la intensidad del impulso llega al Tribunal.

- 0a (urgencia local en ``Tribunal.reactiva``) se retiró: resultado negativo (``docs/PROPUESTA_PASO0.md``, «Resultado»).
- 0b: aliestesia en la base, activa donde el mundo registra ``Apetencia`` (D3, D15; antes ``Perfil.aliestesia``):
  ``Memoria.satisface``, componente ``Apetencia`` de S1 y ``Alimentarse`` por necesidad.
"""

from typing import List, Optional, Tuple

import pytest

from ida.core.arquitectura import Contexto
from ida.core.azar import Azar
from ida.core.latido import Organismo
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.mundo import Efecto, Entidad, MecanismosMemoria, Mundo, Necesidad, Observacion, Perfil, Registro
from ida.core.onda import Onda
from ida.core.pieza import Pieza
from ida.core.soma import Soma
from ida.core.vocabulario import Verbo
from ida.sistemas import crear_sistemas

# --- 0b: aliestesia en la base -------------------------------------------------------------------
# Mundo de juguete: dos necesidades (hambre y sed) y dos clases (baya y charca) que satisfacen cada una la suya.
# El mundo solo dice que las dos son nutritivas (rasgo perceptivo constante); qué satisface qué lo dice el manual
# o lo aprende la experiencia.

NECESIDADES_JUGUETE = (Necesidad("hambre", ("comida",), 95.0, "nutritivo"), Necesidad("sed", ("agua",), 95.0, "nutritivo"))
# Las mismas, con la sed sin rasgo: una sola necesidad por rasgo, sin aliestesia (como mínimo y archivos).
UNA_POR_RASGO = (NECESIDADES_JUGUETE[0], Necesidad("sed", ("agua",), 95.0))
MANUAL_JUGUETE = {"hechos": [
    {"tipo": "proposicion", "sujeto": "baya", "relacion": "NUTRITIVO", "veredicto": "afirma", "necesidad": "hambre"},
    {"tipo": "proposicion", "sujeto": "charca", "relacion": "NUTRITIVO", "veredicto": "afirma", "necesidad": "sed"},
]}


class MundoDosNecesidades(Mundo):
    """Una baya y una charca siempre al alcance. Comer la baya sube la comida; beber de la charca, el agua."""

    nombre = "dos_necesidades"
    perfil = Perfil(vitales_propios=True, duerme=False, necesidades=NECESIDADES_JUGUETE)

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

    def registro(self) -> Registro:
        return Registro(opcionales=["Apetencia"])   # dos necesidades con el mismo rasgo: aliestesia (D3, D15)


def _ctx_juguete(comida: float, agua: float, memoria: Optional[Memoria] = None, necesidades: Tuple[Necesidad, ...] = NECESIDADES_JUGUETE):
    """Contexto de S1 con la interocepción, los dos objetos al alcance y los impulsos de hambre y sed."""
    onda = Onda(1, 100, 1e9)
    perfil = Perfil(vitales_propios=True, necesidades=necesidades)
    for k, v in {"comida": comida, "agua": agua}.items():
        onda.percibir("Interocepcion", Pieza(k, "Interocepcion", carga={"valor": v, "delta": 0.0}, sistema="CORE"))
    for oid, clase, pos in (("baya_1", "baya", (1, 0)), ("charca_1", "charca", (0, 1))):
        rasgos = {"proximidad": 1.0, "nutritivo": 0.6}
        onda.percibir("Exterocepcion", Pieza(oid, "Exterocepcion", carga={"clase": clase, "rasgos": rasgos, "datos": {"pos": pos}}, sistema="CORE"))
        onda.percibir("Objeto", Pieza(oid, "Objeto", 0.5, carga={"clase": clase, "rasgos": rasgos}, sistema="S1"))
    for n in NECESIDADES_JUGUETE:
        i = n.deficit({"comida": comida, "agua": agua}) or 0.0
        onda.registrar("Impulso", Pieza(n.nombre, "Impulso", i, carga={"intensidad": i, "objetivo": 0.0, "rasgo": n.rasgo}, sistema="S1"))
    # Un mundo cuyas necesidades comparten rasgo registra Apetencia (D15); con una necesidad por rasgo, no.
    registrados = {"Apetencia"} if necesidades == NECESIDADES_JUGUETE else set()
    return Contexto(onda, Soma(), memoria or Memoria(), Arquetipo(), Azar(1), perfil, {Verbo.COMER, Verbo.MOVER, Verbo.ESPERAR}, None, True,
                    registrados=registrados)


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


def test_aliestesia_solo_donde_se_registra_apetencia():
    """Sin perilla (D15): la aliestesia existe donde el mundo registra ``Apetencia``. El mínimo y archivos (una sola
    necesidad con rasgo) no la registran (``test_mapa_componentes``) y no la montan; el mundo de dos necesidades con el mismo rasgo, sí."""
    from ida.mundos.minimo import MundoMinimo

    assert not hasattr(Perfil(), "aliestesia")
    assert not hasattr(MecanismosMemoria(), "aliestesia")
    for mundo, monta in ((MundoMinimo(), False), (MundoDosNecesidades(), True)):
        org = Organismo(mundo, crear_sistemas(), Arquetipo(), Memoria("completa"), Azar(1), True)
        assert ("Apetencia" in org.registrados) is monta
        assert any(type(c).__name__ == "Apetencia" for s in org.sistemas for c in s.componentes()) is monta


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
    # Línea base 0 (nada sube sin comer): ΔP = 1, combinado con el manual (peso 1), como antes.
    assert s["sed"] == pytest.approx((4 * 1.0 + Memoria.CONFIANZA_MANUAL) / 5)
    assert s["hambre"] == 0.0                                   # el manual no la declara y nunca subió
    assert mem.satisface[("charca", "sed")].fuente == "manual+experiencia"


def _vivir_contingencia(latidos: int = 600) -> Memoria:
    """Secuencia sintética de una vida: se come baya cada 7 latidos; la «luz» sube sola 10 latidos de cada 40
    (como el amanecer), coma o no; la «comida» solo sube al comer baya."""
    mem = Memoria()
    for t in range(latidos):
        luz_sube = (t % 40) < 10
        if t % 7 == 0:
            mem.aprender_satisface("baya", {"comida": True, "luz": luz_sube})
        else:
            mem.actualizar_linea_base({"comida": False, "luz": luz_sube})
    return mem


def test_contingencia_una_necesidad_que_sube_sola_no_se_atribuye_a_la_clase():
    mem = _vivir_contingencia()
    s = mem.satisface[("baya", "luz")]
    assert s.sube / s.n > 0.15                                   # coincidencia: muchas comidas caen al «amanecer»
    assert mem.estimacion_satisface("baya", "luz") <= 0.1       # contingencia: ΔP ≈ 0


def test_contingencia_una_necesidad_que_solo_sube_al_comer_si_se_atribuye():
    mem = _vivir_contingencia()
    assert mem.linea_base["comida"] == 0.0
    assert mem.estimacion_satisface("baya", "comida") >= 0.9


def test_una_coincidencia_aislada_no_basta_en_una_clase_del_manual():
    """Comer vaca una vez al amanecer (la luz sube sola): sin previo, ΔP = 1 − línea base. El manual declara la
    vaca para el hambre, no para la luz: la luz parte de 0 con peso ``PREVIO`` y una coincidencia no la lleva lejos."""
    mem = Memoria()
    mem.aplicar_manual({"hechos": [{"tipo": "proposicion", "sujeto": "vaca", "relacion": "NUTRITIVO", "necesidad": "comida"}]})
    for t in range(80):
        mem.actualizar_linea_base({"comida": False, "luz": (t % 40) < 10})
    mem.aprender_satisface("vaca", {"comida": True, "luz": True})
    assert mem.estimacion_satisface("vaca", "luz") <= 0.25
    assert mem.estimacion_satisface("vaca", "comida") >= 0.8


def test_sin_manual_el_previo_es_la_percepcion():
    """Una clase de la que el manual no habla: el rasgo perceptivo es el previo y la experiencia lo corrige."""
    mem = Memoria()
    previos = {"comida": 0.6, "agua": 0.6}
    assert mem.satisfaccion("baya", previos) is None
    mem.aprender_satisface("baya", {"comida": True, "agua": False})
    s = mem.satisfaccion("baya", previos)
    assert s == {"comida": pytest.approx((1.0 + 3 * 0.6) / 4), "agua": pytest.approx(3 * 0.6 / 4)}
    for _ in range(40):
        mem.aprender_satisface("baya", {"comida": True, "agua": False})
    assert mem.estimacion_satisface("baya", "agua", previos) < 0.1


def test_la_contingencia_compara_con_la_linea_base_del_mismo_momento():
    """Si casi siempre se come en la fase en que la luz sube sola, P(sube | comer) es alta; pero la línea base de
    ese momento también. Comparada con la línea base al final (otra fase), parecería contingente; no lo es."""
    mem = Memoria()
    for t in range(600):
        fase_sube = (t % 150) < 75                    # sube sola media «jornada», baja la otra media
        if fase_sube and t % 5 == 0:                   # se come solo en la fase de subida
            mem.aprender_satisface("baya", {"luz": True})
        else:
            mem.actualizar_linea_base({"luz": fase_sube})
    assert mem.satisface[("baya", "luz")].sube / mem.satisface[("baya", "luz")].n == 1.0
    assert mem.linea_base["luz"] < 0.5                 # al final, en la fase de bajada
    assert mem.estimacion_satisface("baya", "luz") <= 0.2      # residuo: la línea base tarda unos latidos en seguir la fase


def test_la_linea_base_es_una_media_movil():
    mem = Memoria()
    for _ in range(200):
        mem.actualizar_linea_base({"luz": True})
    for _ in range(Memoria.VENTANA_BASE * 3):
        mem.actualizar_linea_base({"luz": False})
    assert mem.linea_base["luz"] < 0.1                          # olvida lo antiguo: no es la media de toda la vida


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
    """Sin aliestesia (una necesidad por rasgo), hambre y sed eligen el mismo objeto (por nutritivo); con ella, cada una el suyo."""
    mem = Memoria()
    mem.aplicar_manual(MANUAL_JUGUETE)
    sin = _ctx_juguete(30.0, 40.0, mem, necesidades=UNA_POR_RASGO)
    assert _propuesta(sin, "hambre").objetivo == _propuesta(sin, "sed").objetivo
    ctx = _ctx_juguete(30.0, 40.0, mem)
    _apetencia(ctx)
    hambre, sed = _propuesta(ctx, "hambre"), _propuesta(ctx, "sed")
    assert (hambre.verbo, hambre.objetivo) == (Verbo.COMER, "baya_1")
    assert (sed.verbo, sed.objetivo) == (Verbo.COMER, "charca_1")
    # El arousal sale de la intensidad del impulso de origen: el hambre (más apurada) propone con más arousal.
    assert hambre.arousal > sed.arousal


def test_lo_que_no_parece_comestible_no_apetece_aunque_su_clase_satisfaga():
    """La memoria dice a qué necesidad sirve una clase, no si este objeto es comestible ahora (p. ej. una planta
    que aún no está madura): sin el rasgo perceptivo, no hay apetencia."""
    mem = Memoria()
    mem.aplicar_manual(MANUAL_JUGUETE)
    ctx = _ctx_juguete(20.0, 20.0, mem)
    ctx.onda.ev("Objeto")["baya_1"].carga["rasgos"]["nutritivo"] = 0.0
    _apetencia(ctx)
    assert set(ctx.onda.ev("Apetencia")) == {"charca_1"}


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
    e = org.memoria.estimacion_satisface
    assert e("baya", "hambre") >= 0.9 and e("charca", "sed") >= 0.9
    assert e("baya", "sed") <= 0.1 and e("charca", "hambre") <= 0.1
    tarde = [c for c in comidas if c[0] > 150]
    agua = [c for c in tarde if c[1] == "charca"]
    assert tarde and agua
    assert sum(1 for c in agua if c[3] >= c[2]) >= 0.8 * len(agua)
    assert all(c[1] == "baya" for c in tarde if c[2] > c[3] + 0.2)


def test_crafter_el_nutritivo_es_perceptivo_y_constante():
    """Nadie en Crafter decide qué apetece en la percepción (``_deseo`` ya no existe): ``ValoracionCrafter`` (A4) pone
    ``nutritivo`` 0,6 en lo que el manual declara NUTRITIVO (la planta, solo madura) y 0 en lo demás, sea cual sea la
    sed o el hambre."""
    pytest.importorskip("crafter")
    from ida.mundos.crafter import NUTRITIVO_MANUAL, MundoCrafter
    from ida.mundos.crafter_valoracion import ValoracionCrafter

    assert not hasattr(MundoCrafter, "_deseo")
    m = MundoCrafter(vista="oficial")
    m.reiniciar(1)
    assert "Apetencia" in m.registro().opcionales           # hambre y sed comparten «nutritivo»: aliestesia (D15)
    assert m.nutritivos == {"agua", "vaca", "planta"}
    azar = Azar(1)
    org = Organismo(m, crear_sistemas(), Arquetipo.nuevo(azar), Memoria(m.perfil.memoria), azar)
    assert any(isinstance(c, ValoracionCrafter) for c in org.preatencion.componentes)
    valores = set()
    vistas = 0
    for _ in range(60):
        m.jugador.inventory["drink"] = 2                     # sed apurada: el agua no vale más por ello
        onda = org.latir()
        piezas = list(onda.ev("Exterocepcion").values())
        valores |= {p.rasgo("nutritivo") for p in piezas if p.rasgo("lugar") < 0.5}
        for p in piezas:
            if p.clase in ("agua", "vaca"):
                assert p.rasgo("nutritivo") == NUTRITIVO_MANUAL
                vistas += 1
        if not org.soma.esta_vivo:
            break
    assert valores <= {0.0, NUTRITIVO_MANUAL} and vistas

