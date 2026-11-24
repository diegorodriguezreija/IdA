"""Paso 6 de la fase de generalización: la defensa general (docs/ENCARGO_PASO6_DEFENSA.md, sección 5.6).

Mundos de juguete en cuadrícula, sin nada de Crafter:
- un **erizo** que daña por contacto;
- una **torre** que lanza **púas**: cada púa aparece junto a la torre, avanza en línea recta y se deshace al tocar a alguien;
- un **bastón** que, llevado, hace que un erizo caiga con menos golpes.
Nada de eso se le dice a IdA: el daño, el emisor, su alcance y la eficacia del bastón los aprende de lo que percibe.
"""

from typing import Any, Dict, List, Optional, Tuple, cast

from ida.sistemas import amenaza as pel
from ida.nucleo.azar import Azar
from ida.core.latido import Organismo
from ida.nucleo.linaje import Arquetipo
from ida.nucleo.memoria import Memoria
from ida.nucleo.mundo import Efecto, Entidad, Mundo, Necesidad, Observacion, Perfil, Registro
from ida.nucleo.vocabulario import Relacion, Verbo
from ida.sistemas import crear_sistemas

Pos = Tuple[int, int]
NADA = frozenset()


def _peligrosa(clase: str) -> bool:
    return clase in ("erizo", "torre", "pua")


# --- 6a: peligro aprendido -------------------------------------------------------------------------
def test_se_aprende_el_dano_por_contacto():
    p = pel.Peligros()
    aqui = (5, 5)
    assert p.dano_propio("erizo", True) == pel.DANO_PREVIO          # sin experiencia, el previo declarado
    for _ in range(6):     # seis encuentros: un erizo llega, daña 30 dos veces y se va
        p.aprender(aqui, {"e": ("erizo", (5, 6))}, set(), NADA, None, "", None, 0.0, _peligrosa)
        p.aprender(aqui, {"e": ("erizo", (5, 6))}, set(), NADA, None, "", "erizo", 30.0, _peligrosa)
        p.aprender(aqui, {"e": ("erizo", (5, 6))}, set(), NADA, None, "", "erizo", 30.0, _peligrosa)
        p.aprender(aqui, {}, set(), NADA, None, "", None, 0.0, _peligrosa)
    assert p.dano["erizo"].n == 6 and abs(p.dano["erizo"].media - 60.0) < 1e-9
    assert abs(p.dano_por_golpe("erizo", _peligrosa) - (2 * pel.DANO_PREVIO + 12 * 30.0) / 14) < 1e-9
    assert p.dano_propio("erizo", True) > 50.0                         # la experiencia corrige el previo
    assert p.alcance("erizo", _peligrosa) == 1                           # solo por contacto
    # El peligro de un erizo depende de la salud: con poca, más
    comps = p.componentes("erizo", _peligrosa)
    assert p.peligro_a(comps, 1, 100.0) < p.peligro_a(comps, 1, 60.0) < 1.0
    # Los lugares: un gradiente que se anula a alcance + MARGEN_LUGAR casillas
    assert p.peligro_lugar(comps, 1, 100.0) > p.peligro_lugar(comps, 2, 100.0) > p.peligro_lugar(comps, 4, 100.0) == 0.0
    # Lo que no es peligroso ni ha dañado no tiene peligro
    assert p.componentes("piedra", _peligrosa) == []


def test_la_escala_da_el_peligro_antiguo_al_previo_del_manual():
    """g(x) = x / (x + C): el previo del manual a salud completa da 0,8 (el peligro fijo para el que están calibrados los
    umbrales de la base); más pérdida o menos salud, más peligro, sin llegar a 1."""
    p = pel.Peligros()
    comps = p.componentes("erizo", _peligrosa)
    assert abs(p.peligro_a(comps, 1, 100.0) - pel.PELIGRO_PREVIO) < 1e-9
    assert abs(p.peligro_lugar(comps, 1, 100.0) - 0.8 * (1 - 1 / 4)) < 1e-9
    valores = [pel.escala(x) for x in (0.0, 0.05, 0.2, 0.5, 1.0, 3.0)]
    assert valores == sorted(valores) and valores[0] == 0.0 and valores[-1] < 1.0


def test_la_vulnerabilidad_dormido_se_aprende_aparte():
    p = pel.Peligros()
    aqui = (5, 5)
    for _ in range(3):     # dormido: un erizo llega y daña 70
        p.aprender(aqui, {"e": ("erizo", (5, 6))}, set(), NADA, None, "", None, 0.0, _peligrosa, dormido=True)
        p.aprender(aqui, {"e": ("erizo", (5, 6))}, set(), NADA, None, "", "erizo", 70.0, _peligrosa, dormido=True)
        p.aprender(aqui, {}, set(), NADA, None, "", None, 0.0, _peligrosa, dormido=True)
    assert "erizo" not in p.dano_golpe and p.dano_dormido["erizo"].n == 3
    assert p.golpe("erizo", True, dormido=False) == pel.DANO_PREVIO
    assert p.golpe("erizo", True, dormido=True) > 50.0
    despierto, dormido = p.componentes("erizo", _peligrosa), p.componentes("erizo", _peligrosa, dormido=True)
    assert p.peligro_a(dormido, 2, 100.0) > p.peligro_a(despierto, 2, 100.0)


def _lanzamientos(p: pel.Peligros, n: int, recorrido: int, aqui: Pos = (0, 0)) -> None:
    """La torre en (10, 0); cada púa aparece en (9, 0) y avanza hacia la izquierda ``recorrido`` casillas antes de deshacerse."""
    visibles = {(x, y) for x in range(-1, 12) for y in range(-4, 5)}
    k = 0
    for _ in range(n):
        k += 1
        p.aprender(aqui, {"t": ("torre", (10, 0))}, visibles, NADA, None, "", None, 0.0, _peligrosa)
        for paso in range(recorrido):
            p.aprender(aqui, {"t": ("torre", (10, 0)), f"p{k}": ("pua", (9 - paso, 0))}, visibles, NADA, None, "", None, 0.0, _peligrosa)
    p.aprender(aqui, {"t": ("torre", (10, 0))}, visibles, NADA, None, "", None, 0.0, _peligrosa)


def test_se_aprende_un_emisor_y_su_alcance():
    p = pel.Peligros()
    _lanzamientos(p, 4, 5)
    assert p.emitidas("torre") == ["pua"]
    assert p.emision[("torre", "pua")].contingencia() > 0.8
    assert p.alcance("torre", _peligrosa) == 6         # de (10, 0) a (5, 0), y el contacto
    # El emisor hereda el daño de lo que emite, con su alcance: los lugares a 8 casillas aún son peligrosos
    comps = p.componentes("torre", _peligrosa)
    assert 6 in [a for _, a in comps]
    assert p.peligro_lugar(comps, 8, 100.0) > 0.0 == p.peligro_lugar(p.componentes("erizo", _peligrosa), 8, 100.0)
    # Aparecer junto a algo una vez no lo hace emisor
    q = pel.Peligros()
    _lanzamientos(q, 1, 3)
    assert q.emitidas("torre") == []


def test_un_lugar_dentro_del_alcance_de_un_emisor_es_peligroso():
    p = pel.Peligros()
    _lanzamientos(p, 4, 5)
    cerca = Entidad("celda_6_0", "suelo", {"lugar": 1.0}, {"pos": (6, 0)})
    lejos = Entidad("celda_0_0", "suelo", {"lugar": 1.0}, {"pos": (0, 0)})
    torre = Entidad("t", "torre", {"agente": 1.0}, {"pos": (10, 0)})
    pel.estimar([cerca, lejos, torre], (1, 0), p, 100.0, _peligrosa)
    assert cerca.rasgos["peligro"] > lejos.rasgos["peligro"] == 0.0
    assert torre.rasgos["peligro"] > 0.0


def test_el_legado_lleva_lo_aprendido_con_dos_observaciones():
    """Se hereda con la mitad de la evidencia: con 6 lanzamientos quedan 3 «junto», lo justo para seguir siendo emisor."""
    p = pel.Peligros()
    _lanzamientos(p, 6, 5)
    q = pel.Peligros()
    q.heredar_peligros(p.legado_peligros())
    assert q.emitidas("torre") == ["pua"] and q.alcance_emision("torre") == p.alcance_emision("torre")


# --- Mundo de juguete para el Organismo ------------------------------------------------------------------
class MundoErizos(Mundo):
    """Cuadrícula abierta de 11 × 11. Un erizo (5 de vida) se acerca y daña 20 de vitalidad cada 3 latidos en contacto.
    ATACAR quita 1 de vida al erizo, 2 con el bastón. Cuando cae, aparece otro lejos. Con ``da_peligro`` el mundo da su propio
    rasgo ``peligro``; si no, lo calcula la base. El bastón está en el inventario si ``baston``."""

    nombre = "erizos"
    perfil = Perfil(vitales_propios=True, duerme=False, amplitud=200,
                    necesidades=(Necesidad("salud", ("vitalidad",), 100.0), Necesidad("hambre", ("comida",), 95.0, "nutritivo")))

    def __init__(self, baston: bool = False, salud: float = 100.0, quieto: bool = False):
        self.pos: Pos = (5, 5)
        self.erizo: Optional[Pos] = (5, 8)
        self.vida, self.n, self.enfriamiento = 5, 1, 0
        self.salud = salud
        self.inv = {"baston": 1.0 if baston else 0.0, "palo": 1.0}
        self.quieto = quieto
        self.dormido = False
        self.da_peligro = False
        self.t = 0

    def reiniciar(self, semilla: Optional[int]) -> None:
        pass

    def verbos(self):
        return {Verbo.MOVER, Verbo.ATACAR, Verbo.ESPERAR}

    def observar(self) -> Observacion:
        ent: List[Entidad] = []
        if self.erizo is not None:
            d = abs(self.erizo[0] - self.pos[0]) + abs(self.erizo[1] - self.pos[1])
            r = {"proximidad": 1.0 if d <= 1 else max(0.0, 1.0 - d / 9), "agente": 1.0}
            if self.da_peligro:
                r["peligro"] = 0.8
            ent.append(Entidad(f"erizo_{self.n}", "erizo", r, {"pos": self.erizo}))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c = (self.pos[0] + dx, self.pos[1] + dy)
            if 0 <= c[0] < 11 and 0 <= c[1] < 11 and c != self.erizo:
                r = {"lugar": 1.0, "proximidad": 1.0, "novedad": 0.3}
                if self.da_peligro:
                    r["peligro"] = 0.0
                ent.append(Entidad(f"celda_{c[0]}_{c[1]}", "suelo", r, {"pos": c}))
        return Observacion(ubicacion=f"celda_{self.pos[0]}_{self.pos[1]}", entidades=ent, dormido=self.dormido,
                           vitales={"vitalidad": self.salud, "comida": 100.0}, inventario=dict(self.inv))

    def ejecutar(self, verbo: Verbo, objetivo: str, datos: Dict[str, Any]) -> Efecto:
        """El erizo actúa primero (se acerca y, pegado, daña), después el individuo."""
        self.t += 1
        antes = self.salud
        causa = None
        if self.erizo is not None:
            if not self.quieto:
                dx, dy = self.pos[0] - self.erizo[0], self.pos[1] - self.erizo[1]
                if abs(dx) + abs(dy) > 1:
                    paso = (1 if dx > 0 else -1, 0) if abs(dx) >= abs(dy) else (0, 1 if dy > 0 else -1)
                    self.erizo = (self.erizo[0] + paso[0], self.erizo[1] + paso[1])
            if abs(self.erizo[0] - self.pos[0]) + abs(self.erizo[1] - self.pos[1]) <= 1:
                if self.enfriamiento == 0:
                    self.salud -= 20.0
                    causa = "erizo"
                    self.enfriamiento = 3
                else:
                    self.enfriamiento -= 1
        elif self.t % 8 == 0:
            self.erizo = (0, 0) if self.pos != (0, 0) else (10, 10)
        if verbo == Verbo.MOVER and objetivo.startswith("celda_"):
            _, x, y = objetivo.split("_")
            self.pos = (int(x), int(y))
        elif verbo == Verbo.ATACAR and self.erizo is not None and objetivo == f"erizo_{self.n}":
            self.vida -= 2 if self.inv["baston"] else 1
            if self.vida <= 0:
                self.erizo, self.vida, self.n, self.enfriamiento = None, 5, self.n + 1, 0
        return Efecto(True, {"vitalidad": self.salud - antes} if self.salud != antes else {}, causa=causa, muerte=self.salud <= 0)

    def terminado(self) -> bool:
        return self.salud <= 0

    def manual(self) -> Dict[str, Any]:
        return {"hechos": [{"tipo": "proposicion", "sujeto": "erizo", "relacion": "PELIGROSO"}], "inventario": ["baston", "palo"]}

    def registro(self) -> Registro:
        """Como Crafter (D3, D15): el peligro aprendido y la lucha por evaluación, solo si el mundo no da su ``peligro``."""
        return Registro(opcionales=[] if self.da_peligro else ["Amenaza", "Afrontar"])


def _organismo(mundo: MundoErizos, mem: Optional[Memoria] = None) -> Organismo:
    if mem is None:
        mem = Memoria()
        mem.aplicar_manual(mundo.manual())
    return Organismo(mundo, crear_sistemas(), Arquetipo(), mem, Azar(1), con_experiencia=True)


def test_la_base_calcula_el_peligro_si_el_mundo_no_lo_da():
    mundo = MundoErizos()
    org = _organismo(mundo)
    onda = org.latir()
    erizo = onda.ev("Exterocepcion")["erizo_1"]
    assert 0.0 < erizo.rasgo("peligro") < 1.0
    # Si el mundo da su propio peligro, la base no lo toca
    mundo2 = MundoErizos()
    mundo2.da_peligro = True
    onda2 = _organismo(mundo2).latir()
    assert onda2.ev("Exterocepcion")["erizo_1"].rasgo("peligro") == 0.8


def test_un_erizo_que_se_acerca_despierta_al_que_duerme():
    """A salud completa y sin experiencia (solo el previo del manual), un erizo a 2 casillas despierta; a 4, no."""
    for distancia, despierta in ((2, True), (4, False)):
        mundo = MundoErizos(quieto=True)
        mundo.erizo = (5, 5 + distancia)
        mundo.dormido = True
        onda = _organismo(mundo).latir()
        assert (onda.notas.get("despierta") == "alarma") == despierta


def test_viviendo_se_aprende_el_dano_por_contacto():
    mundo = MundoErizos(quieto=True)
    mundo.erizo = (5, 6)
    org = _organismo(mundo)
    for _ in range(12):
        if mundo.terminado():
            break
        org.latir()
    mem = org.memoria
    peligros = mem.seccion("peligros")
    assert peligros.dano_golpe["erizo"].n >= 1
    assert abs(peligros.dano_golpe["erizo"].media - 20.0) < 1e-9
    assert mem.proposicion("erizo", Relacion.PELIGROSO) is not None


# --- 6b: luchar o huir por evaluación ---------------------------------------------------------------------
def _organismo_con_experiencia(mundo: MundoErizos, golpes: Dict[frozenset, int], eventos: int = 4) -> Organismo:
    """Lo que ya se habría aprendido de los erizos: 20 de daño por golpe, 40 por encuentro, ``eventos`` daños en 20 latidos
    de exposición y los derribos dados (objetos llevados -> golpes). D7: la sección «peligros» existe al montarse
    ``Amenaza``, así que se rellena tras montar el Organismo y antes de su primer latido."""
    org = _organismo(mundo)
    if not org.memoria.tiene_seccion("peligros"):
        return org          # un mundo que da su peligro no registra Amenaza: no hay sección «peligros» que rellenar
    p = org.memoria.seccion("peligros")
    p.dano_golpe["erizo"] = pel.Media(5, 20.0)
    p.dano["erizo"] = pel.Media(5, 40.0)
    p.expuestos["erizo"], p.eventos["erizo"] = 20, eventos
    p.derribos["erizo"] = [(k, g) for k, g in golpes.items() for _ in range(2)]
    return org


def _decisiones(mundo: MundoErizos, org: Organismo, latidos: int = 5):
    """Las acciones de unos latidos (el primero puede ser el reflejo de sobresalto) y las estrategias activas en cada uno."""
    acciones, activas = [], []
    for _ in range(latidos):
        if mundo.terminado():
            break
        onda = org.latir()
        acciones.append(onda.reactiva.ef["Accion"]["Accion"].carga)
        activas.append({p.carga["nombre"] for p in onda.estrategias.values()})
    return acciones, activas


def test_afrontar_lucha_con_margen():
    """Un erizo que persigue: tras el sobresalto (3 latidos), con margen no se huye y se lucha hasta derribarlo."""
    mundo = MundoErizos(salud=100.0)
    mundo.erizo = (5, 6)
    acciones, _ = _decisiones(mundo, _organismo_con_experiencia(mundo, {NADA: 3}), latidos=14)
    atacar = [a for a in acciones if a["verbo"] == Verbo.ATACAR]
    assert atacar and all(a["objetivo"] == "erizo_1" and a["motivo"].startswith("afrontar: atacar erizo") for a in atacar)
    assert mundo.n == 2                       # el erizo cayó


def test_afrontar_huye_sin_margen():
    mundo = MundoErizos(quieto=True, salud=40.0)
    mundo.erizo = (5, 6)
    acciones, activas = _decisiones(mundo, _organismo_con_experiencia(mundo, {NADA: 3}))
    assert not any(a["verbo"] == Verbo.ATACAR for a in acciones)
    assert any(a["verbo"] == Verbo.MOVER and "huir" in a["motivo"] for a in acciones)
    assert not any("afrontar" in x for x in activas)


def test_sin_datos_de_eficacia_no_lucha():
    """El previo de golpes es pesimista: con la tasa previa, la lucha no deja margen y se huye."""
    mundo = MundoErizos(quieto=True, salud=100.0)
    mundo.erizo = (5, 6)
    org = _organismo_con_experiencia(mundo, {})
    p = org.memoria.seccion("peligros")
    p.expuestos.clear()
    p.eventos.clear()
    acciones, activas = _decisiones(mundo, org, latidos=1)
    assert not any("afrontar" in x for x in activas)


def test_si_el_mundo_da_su_peligro_no_hay_afrontar():
    """Afrontar solo usa el peligro que calcula la base: en un mundo que da el suyo (mínimo, archivos) no actúa."""
    mundo = MundoErizos(quieto=True, salud=100.0)
    mundo.erizo = (5, 6)
    mundo.da_peligro = True
    _, activas = _decisiones(mundo, _organismo_con_experiencia(mundo, {NADA: 3}))
    assert not any("afrontar" in x for x in activas)


# --- 6c: el arma como meta instrumental --------------------------------------------------------------------
def _derribar(p: pel.Peligros, ident: str, golpes: int, objetos: frozenset) -> None:
    aqui, junto = (5, 5), (5, 6)
    p.aprender(aqui, {ident: ("erizo", junto)}, set(), objetos, None, "", None, 0.0, _peligrosa)
    for k in range(golpes):
        vivo = {ident: ("erizo", junto)} if k < golpes - 1 else {}
        p.aprender(aqui, vivo, set(), objetos, "ATACAR", ident, None, 0.0, _peligrosa)


def test_la_eficacia_depende_del_objeto_llevado():
    p = pel.Peligros()
    baston = frozenset({"baston", "palo"})
    palo = frozenset({"palo"})
    _derribar(p, "e1", 5, palo)
    _derribar(p, "e2", 5, palo)
    _derribar(p, "e3", 2, baston)
    _derribar(p, "e4", 2, baston)
    assert p.derribos["erizo"] == [(palo, 5), (palo, 5), (baston, 2), (baston, 2)]
    assert set(p.reductores()) == {"baston"}          # el palo se llevaba siempre: no explica nada
    assert p.golpes("erizo", palo)[0] == 5.0 and p.golpes("erizo", baston)[0] == 2.0
    assert p.golpes("erizo", frozenset())[0] == 5.0
    assert p.golpes("otra_clase", baston)[0] == pel.GOLPES_PREVIO


def test_se_pide_el_arma_de_forma_instrumental():
    """Con 70 de salud, sin bastón la lucha no deja margen (5 golpes) y con él sí (2): se pide el bastón y se huye."""
    mundo = MundoErizos(quieto=True, salud=70.0)
    mundo.erizo = (5, 6)
    org = _organismo_con_experiencia(mundo, {frozenset({"palo"}): 5, frozenset({"baston", "palo"}): 2}, eventos=9)
    onda = org.latir()
    peticion = onda.ef("Peticion").get("peticion:baston")
    assert peticion is not None
    assert peticion.carga["origen"] == "afrontar" and peticion.carga["cantidad"] == 1.0
    assert any(p.carga["nombre"] == "afrontar" and p.carga["paso"] == "armarse" for p in onda.estrategias.values())


def test_con_el_arma_ya_no_se_pide_y_se_lucha():
    mundo = MundoErizos(baston=True, salud=100.0)
    mundo.erizo = (5, 6)
    org = _organismo_con_experiencia(mundo, {frozenset({"palo"}): 5, frozenset({"baston", "palo"}): 2}, eventos=9)
    acciones, _ = _decisiones(mundo, org, latidos=10)
    assert any(a["verbo"] == Verbo.ATACAR and a["motivo"].startswith("afrontar: atacar") for a in acciones)


def test_no_se_pide_un_objeto_que_no_se_distingue():
    """Bastón y cuerda siempre juntos en los derribos: los dos «reducen» los golpes, pero no se sabe cuál, y no se pide
    ninguno. Con un derribo que los separa, el bastón se distingue y se pide."""
    juntos = frozenset({"baston", "cuerda"})
    derribos = {frozenset(): 5, juntos: 2}
    mundo = MundoErizos(quieto=True, salud=70.0)
    mundo.erizo = (5, 6)
    org = _organismo_con_experiencia(mundo, derribos, eventos=9)
    mem = org.memoria
    p = mem.seccion("peligros")
    assert set(p.reductores()) == {"baston", "cuerda"} and p.distinguibles() == set()
    onda = org.latir()
    assert not onda.ef("Peticion")
    mundo = MundoErizos(quieto=True, salud=70.0)
    mundo.erizo = (5, 6)
    org = _organismo_con_experiencia(mundo, derribos, eventos=9)
    mem = org.memoria
    p = mem.seccion("peligros")
    p.derribos["erizo"].append((frozenset({"baston"}), 2))
    assert p.distinguibles() == {"baston", "cuerda"}
    onda = org.latir()
    assert set(onda.ef("Peticion")) == {"peticion:baston"}


# --- Revisión: umbrales del emisor y clases que se afrontan ----------------------------------------------
def test_el_emisor_pide_tres_veces_junto_y_contingencia():
    p = pel.Peligros()
    _lanzamientos(p, 2, 3)
    assert p.emision[("torre", "pua")].junto == 2 and p.emitidas("torre") == []      # dos veces junto no bastan
    _lanzamientos(p, 1, 3)
    assert p.emitidas("torre") == ["pua"]
    # Tres veces junto pero muchas apariciones lejos: ΔP < 0,6
    q = pel.Peligros()
    _lanzamientos(q, 3, 3)
    q.emision[("torre", "pua")].n += 3
    assert q.emision[("torre", "pua")].contingencia() < pel.EMISION_MINIMA and q.emitidas("torre") == []


def test_afrontar_no_ataca_lo_que_nunca_ha_visto_caer_ni_es_meta():
    """Con una tasa de daño muy baja la lucha saldría favorable incluso con el previo de golpes; aun así, sin derribos de la
    clase ni meta del manual, Afrontar no la considera. Con la meta, sí."""
    from ida.sistemas.requisito import Meta, Requisitos
    for meta in (False, True):
        mundo = MundoErizos(quieto=True, salud=100.0)
        mundo.erizo = (5, 6)
        org = _organismo_con_experiencia(mundo, {}, eventos=0)
        mem = org.memoria
        mem.seccion("peligros").expuestos["erizo"] = 1000
        if meta:
            cast(Requisitos, mem.seccion("requisitos")).metas[(Verbo.ATACAR, "erizo")] = Meta(Verbo.ATACAR, "erizo")
        _, activas = _decisiones(mundo, org, latidos=1)
        assert any("afrontar" in x for x in activas) == meta


# --- 6d: frontera de Crafter ------------------------------------------------------------------------------
def test_crafter_no_escribe_conducta():
    """Paso 6d: ninguna clase de ``ida/mundos/crafter/adaptador.py`` es una estrategia y Crafter no declara estrategias propias."""
    import inspect

    import pytest

    pytest.importorskip("crafter")
    from ida.nucleo.estrategia import ConPropuestas, Definicion, Plan
    from ida.mundos.crafter import MundoCrafter, adaptador

    clases = [c for _, c in inspect.getmembers(adaptador, inspect.isclass) if c.__module__ == adaptador.__name__]
    assert clases     # el adaptador existe
    assert not [c.__name__ for c in clases if issubclass(c, (Definicion, Plan, ConPropuestas))]
    # D16: Crafter solo registra SalirDelRecinto, de ``ida/sistemas/proteger.py`` (pasa a Crafter en A6b)
    estrategias = MundoCrafter().registro().estrategias
    assert list(estrategias) == ["S1"] and not estrategias["S1"].sustituye
    assert [type(d).__name__ for d in estrategias["S1"].añade] == ["SalirDelRecinto"]


def test_la_escala_del_perfil_llega_a_peligros():
    """D15: las constantes de escala de Amenaza son parámetros del mundo (``Perfil.escala``)."""
    from ida.nucleo.mundo import Escala

    p = pel.Peligros()
    assert (p.dano_previo, p.golpes_previo, p.margen_lugar, p.c_escala) == (pel.DANO_PREVIO, pel.GOLPES_PREVIO, pel.MARGEN_LUGAR, pel.ESCALA)
    p = pel.Peligros(escala=Escala(dano_previo=50.0, golpes_previo=4.0, margen_lugar=1))   # A7b: la escala, al construirla
    assert p.dano_propio("erizo", True) == 50.0
    assert p.golpes("erizo", frozenset())[0] == 4.0
    assert abs(p.peligro_a([(50.0, 1)], 1, 100.0) - pel.PELIGRO_PREVIO) < 1e-9   # el previo sigue fijando la escala
    assert p.peligro_lugar([(50.0, 1)], 2, 100.0) == 0.0                          # se anula a alcance + 1


def test_crafter_fija_la_escala_de_antes():
    """A6a no cambia la conducta: Crafter declara en su Perfil los valores que tenían las constantes."""
    import pytest

    pytest.importorskip("crafter")
    from ida.nucleo.mundo import Escala
    from ida.mundos.crafter import MundoCrafter

    assert MundoCrafter.perfil.escala == Escala()
    assert MundoCrafter.perfil.escala.dano_previo == 100.0 * 2.0 / 9.0
    assert MundoCrafter.perfil.escala.reserva == 100.0 * 3.0 / 9.0
    assert MundoCrafter.perfil.escala.coste_sin_sitio == 45.0
