"""Paso 3 de la fase de generalización: proteger X (docs/ENCARGO_PASO3_PROTEGER.md, sección 6.5).

Mundo de juguete en cuadrícula, sin nada de Crafter: suelo transitable, roca que no lo es. COGER roca la convierte en
hueco (transitable) y da una roca; USAR «poner_roca» pone una roca en la casilla de delante. El cuerpo se mueve como en
muchos juegos de rejilla: hacia una casilla libre avanza y queda mirando hacia allí; hacia una bloqueada solo se gira.
Nada de eso se le dice a IdA: lo aprende (o, en los tests de elección de sitio, se le da ya aprendido para aislar la parte
que se prueba).
"""

from dataclasses import replace
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Set, Tuple

import pytest

from ida.core.azar import Azar
from ida.core.latido import Organismo
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.mundo import Alta, Efecto, Entidad, Mundo, Necesidad, Observacion, Perfil, Registro
from ida.core.pieza import Pieza
from ida.core.vocabulario import Verbo
from ida.cuerpos.cuadricula import Cuadricula
from ida.sistemas import crear_sistemas
from ida.cuerpos.cuadricula.buscador import buscar_postura
from ida.mundos.crafter.s1.interpretar.recinto import Modelo, Recinto
from ida.mundos.crafter.s1.reaccionar.estrategias.salir_del_recinto import SalirDelRecinto

from _secciones import memoria_con_secciones

Pos = Tuple[int, int]
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
LIBRES = {"suelo", "hueco"}


class MundoCueva(Mundo):
    """Cuadrícula finita. ``luz`` (0-100) es la constante del cobijo; ``bajada`` la reduce cada latido."""

    nombre = "cueva"
    perfil = Perfil(vitales_propios=True, duerme=True, amplitud=200,
                    necesidades=(Necesidad("cobijo", ("cobijo",), 100.0), Necesidad("hambre", ("comida",), 95.0, "nutritivo")),
                    intenciones=("progresar",))

    def __init__(self, mapa: Dict[Pos, str], pos: Pos, cara: Pos = (0, 1), luz: float = 10.0, bajada: float = 0.0,
                 comida: float = 100.0, gasto: float = 0.0, rocas: int = 0):
        self.mapa, self.pos, self.cara = dict(mapa), pos, cara
        self.luz, self.bajada, self.comida, self.gasto = luz, bajada, comida, gasto
        self.inv = {"roca": float(rocas)}

    def reiniciar(self, semilla: Optional[int]) -> None:
        pass

    def registro(self) -> Registro:
        """Cuadrícula con orientación, como Crafter (D10), y lo de protegerse que registra Crafter (D3, D16)."""
        return Registro(cuerpo=Cuadricula(), componentes={"S1.Interpretar": Alta(añade=[Recinto()])},
                        estrategias={"S1": Alta(añade=[SalirDelRecinto()])}, opcionales=["Amenaza", "Afrontar", "Proteger"])

    def libre(self, p: Pos) -> bool:
        return self.mapa.get(p) in LIBRES

    def observar(self) -> Observacion:
        x0, y0 = self.pos
        vista = {(x, y): c for (x, y), c in self.mapa.items() if abs(x - x0) <= 4 and abs(y - y0) <= 4}
        entidades = [Entidad(f"{c}_{x}_{y}", c, {"proximidad": 1.0 if abs(x - x0) + abs(y - y0) <= 1 else
                                                max(0.0, 1.0 - (abs(x - x0) + abs(y - y0)) / 9)}, {"pos": (x, y)})
                     for (x, y), c in sorted(vista.items(), key=lambda kv: (kv[1] != "cantera", abs(kv[0][0] - x0) + abs(kv[0][1] - y0)))
                     if c in ("roca", "cantera")][:14]
        for dx, dy in DIRS:
            v = (x0 + dx, y0 + dy)
            if self.libre(v):
                entidades.append(Entidad(f"celda_{v[0]}_{v[1]}", "suelo", {"lugar": 1.0, "proximidad": 1.0, "novedad": 0.5}, {"pos": v}))
        f = (x0 + self.cara[0], y0 + self.cara[1])
        vitales = {"vitalidad": 100.0, "alimentacion": self.comida, "energia": 100.0, "descanso": 100.0,
                   "cobijo": max(0.0, self.luz), "comida": self.comida}
        return Observacion(ubicacion=f"celda_{x0}_{y0}", entidades=entidades, vitales=vitales, inventario=dict(self.inv),
                           cuerpo={"orientacion": self.cara, "casillas": vista,
                                   "delante": {"id": f"{self.mapa.get(f, 'borde')}_{f[0]}_{f[1]}", "clase": self.mapa.get(f, "borde")}})

    def ejecutar(self, verbo: Verbo, objetivo: str, datos: Dict) -> Efecto:
        self.luz -= self.bajada
        self.comida = max(0.0, self.comida - self.gasto)
        partes = str(objetivo).rsplit("_", 2)
        destino = (int(partes[1]), int(partes[2])) if len(partes) == 3 and partes[1].lstrip("-").isdigit() else None
        cerca = destino is not None and abs(destino[0] - self.pos[0]) + abs(destino[1] - self.pos[1]) == 1
        if verbo == Verbo.MOVER and cerca:
            self.cara = (destino[0] - self.pos[0], destino[1] - self.pos[1])
            if self.libre(destino):
                self.pos = destino
            return Efecto(exito=True)
        if verbo == Verbo.COGER and cerca:
            self.cara = (destino[0] - self.pos[0], destino[1] - self.pos[1])
            if self.mapa.get(destino) == "cantera":       # da roca y sigue ahí
                self.inv["roca"] += 1
                return Efecto(exito=True, obtenido="roca")
            if self.mapa.get(destino) == "roca":
                self.mapa[destino] = "hueco"
                self.inv["roca"] += 1
                return Efecto(exito=True, obtenido="roca")
            return Efecto(exito=False)
        if verbo == Verbo.USAR and (datos.get("receta") or objetivo) == "poner_roca":
            f = (self.pos[0] + self.cara[0], self.pos[1] + self.cara[1])
            if self.inv["roca"] >= 1 and self.libre(f):
                self.mapa[f] = "roca"
                self.inv["roca"] -= 1
                return Efecto(exito=True)
            return Efecto(exito=False)
        return Efecto(exito=verbo in (Verbo.ESPERAR, Verbo.DORMIR))

    def verbos(self) -> Set[Verbo]:
        return {Verbo.MOVER, Verbo.COGER, Verbo.USAR, Verbo.ESPERAR, Verbo.DORMIR}

    def manual(self) -> Dict:
        return {"inventario": ["roca"], "hechos": [
            {"tipo": "requisito", "verbo": "USAR", "objetivo": "poner_roca", "requiere_inventario": {"roca": 1}, "requiere_cerca": [],
             "aparece": ["roca"]},
            {"tipo": "requisito", "verbo": "COGER", "objetivo": "roca", "requiere_inventario": {}, "requiere_cerca": [], "efecto": {"roca": 1}},
            {"tipo": "requisito", "verbo": "COGER", "objetivo": "cantera", "requiere_inventario": {}, "requiere_cerca": [], "efecto": {"roca": 1}},
        ]}

    def encerrado(self) -> bool:
        """Recinto real: 1-3 casillas libres conectadas sin vecinas libres fuera."""
        comp, frontera = {self.pos}, [self.pos]
        while frontera:
            p = frontera.pop()
            for d in DIRS:
                v = (p[0] + d[0], p[1] + d[1])
                if v not in comp and self.libre(v):
                    comp.add(v)
                    frontera.append(v)
                    if len(comp) > 3:
                        return False
        return True


def _campo(ancho: int = 14, alto: int = 11, roca: Optional[Set[Pos]] = None) -> Dict[Pos, str]:
    """Campo de suelo rodeado de roca, con roca además en ``roca``."""
    mapa = {(x, y): "suelo" for x in range(ancho) for y in range(alto)}
    for x in range(ancho):
        mapa[(x, 0)] = mapa[(x, alto - 1)] = "roca"
    for y in range(alto):
        mapa[(0, y)] = mapa[(ancho - 1, y)] = "roca"
    for p in roca or set():
        mapa[p] = "roca"
    return mapa


def _memoria(mundo: MundoCueva, aprendida: bool) -> Memoria:
    mem = memoria_con_secciones()   # D7: el mapa local es la sección del cuerpo
    mem.aplicar_manual(mundo.manual())
    if aprendida:      # lo que se aprende en los primeros latidos de una vida, dado para aislar la elección del sitio
        mem.paso_libre.update({"suelo": 1, "hueco": 1})
        mem.paso_bloqueado["roca"] = 1
        _mapa(mem).aprender_cuerpo("mover", True, True, True)
        _mapa(mem).aprender_cuerpo("mover", False, False, True)
        _mapa(mem).aprender_cuerpo("interactuar", True, False, True)
        _mapa(mem).aprender_transformacion(Verbo.COGER, "roca", "roca", "hueco")
    return mem


def _vivir(mundo: MundoCueva, mem: Memoria, latidos: int, al_latir=None) -> Organismo:
    org = Organismo(mundo, crear_sistemas(), Arquetipo(), mem, Azar(1), con_experiencia=True)
    org.vivir(latidos, al_latir=al_latir)
    return org


# --- 1. el modelo del cuerpo se aprende ------------------------------------------------------------
def _obs(pos: Pos, cara: Pos, mapa: Dict[Pos, str]) -> Observacion:
    m = MundoCueva(mapa, pos, cara)
    return m.observar()


def _aprender_mapa(mem: Memoria, obs: Observacion, accion: Optional[Dict[str, Any]]) -> None:
    """Lo que hacía ``Organismo._aprender_mapa`` (hasta A5a): el ``aprender`` del cuerpo cuadrícula (``ModeloDirecto`` y
    después ``MapaLocal``), con un contexto mínimo: la memoria, la Observación, las piezas que emitirían los sensores con
    ella (``Propiocepcion`` «yo» y ``Exterocepcion``) y la acción anterior en ``ei["Accion"]``."""
    exterocepcion = {e.id: Pieza(id=e.id, tipo="Exterocepcion", carga={"clase": e.clase, "rasgos": dict(e.rasgos), "datos": dict(e.datos)})
                     for e in obs.entidades}
    yo = Pieza(id="yo", tipo="Propiocepcion", carga={"ubicacion": obs.ubicacion, "inventario": dict(obs.inventario or {}),
                                                    "cuerpo": dict(obs.cuerpo or {})})
    ev = {"Exterocepcion": exterocepcion, "Propiocepcion": {"yo": yo}}
    ei = {"Accion": {"Accion": SimpleNamespace(carga=accion)}} if accion is not None else {}
    onda = SimpleNamespace(ev=lambda canal: ev.get(canal, {}), ei=lambda canal: ei.get(canal, {}))
    ctx = SimpleNamespace(memoria=mem, observacion=obs, onda=onda)
    for comp in Cuadricula().componentes().values():
        for c in comp:
            c.de_cuerpo = "cuadricula"   # lo pone el Organismo al montarlos
            c.aprender(ctx)   # type: ignore[arg-type]


def _mapa(mem: Memoria) -> Any:
    """D7: la sección «cuadricula» (del cuerpo), para escribir en ella lo ya aprendido."""
    return mem.seccion_propia("cuadricula", "cuadricula")


def test_el_modelo_del_cuerpo_se_aprende_por_propiocepcion():
    """Tras MOVER hacia una casilla libre, la posición cambia y queda mirando hacia allí; hacia una bloqueada, solo gira.
    La memoria lo aprende de lo percibido antes y después (``ModeloDirecto`` del cuerpo cuadrícula), sin que nadie se lo diga."""
    mapa = {(x, 0): "suelo" for x in range(4)} | {(4, 0): "roca"} | {(x, y): "roca" for x in range(5) for y in (-1, 1)}
    mem = memoria_con_secciones()   # D7: el mapa local es la sección del cuerpo
    secuencia = [  # (posición, orientación) percibidas y la acción del latido anterior
        ((1, 0), (0, 1), None),
        ((2, 0), (1, 0), {"verbo": Verbo.MOVER, "objetivo": "celda_2_0"}),
        ((3, 0), (1, 0), {"verbo": Verbo.MOVER, "objetivo": "celda_3_0"}),
        ((3, 0), (0, 1), {"verbo": Verbo.MOVER, "objetivo": "celda_3_1"}),      # hacia la roca de abajo: solo gira
        ((2, 0), (-1, 0), {"verbo": Verbo.MOVER, "objetivo": "celda_2_0"}),
    ]
    for pos, cara, accion in secuencia:
        _aprender_mapa(mem, _obs(pos, cara, mapa), accion)
    assert mem.transitable("suelo") is True and mem.transitable("roca") is False
    assert mem.modelo_cuerpo("mover", True) == (True, True)
    assert mem.modelo_cuerpo("mover", False) == (False, True)


def test_el_modelo_del_cuerpo_se_aprende_viviendo():
    """En una vida, sin nada dado, IdA aprende la regla del movimiento hacia casillas libres y qué clases son transitables."""
    mundo = MundoCueva(_campo(), (5, 5), luz=90.0)
    mem = _memoria(mundo, aprendida=False)
    _vivir(mundo, mem, 40)
    assert mem.transitable("suelo") is True
    assert mem.modelo_cuerpo("mover", True) == (True, True)


# --- 2. el buscador ---------------------------------------------------------------------------------
def _modelo(mapa: Dict[Pos, str]) -> Modelo:
    mem = _memoria(MundoCueva(mapa, (0, 0)), aprendida=True)
    mem.casillas.update(mapa)
    return Modelo(mem, {}, set())


def test_el_buscador_encuentra_como_quedar_mirando_a_una_casilla_libre():
    """En un pasillo (-1,0)-(0,0)-(1,0), para quedar en (0,0) mirando a (-1,0) (libre) hay que ir a (1,0) y volver."""
    mapa = {(-1, 0): "suelo", (0, 0): "suelo", (1, 0): "suelo"} | {(x, y): "roca" for x in range(-2, 3) for y in (-1, 1)}
    mapa |= {(-2, 0): "roca", (2, 0): "roca"}
    plan = buscar_postura(_modelo(mapa), (0, 0), (1, 0), (0, 0), (-1, 0))
    assert plan == [("mover", (1, 0)), ("mover", (0, 0))]


def test_el_buscador_no_encuentra_como_mirar_al_acceso_desde_una_sola_casilla():
    """Con una sola casilla interior no se puede quedar dentro mirando al acceso: es lo que obliga a 2 interiores."""
    mapa = {(0, 0): "suelo", (1, 0): "suelo", (2, 0): "suelo"} | {(x, y): "roca" for x in range(-1, 3) for y in (-1, 1)}
    mapa[(-1, 0)] = "roca"
    assert buscar_postura(_modelo(mapa), (0, 0), (-1, 0), (0, 0), (1, 0)) is None


# --- 3. Proteger elige el sitio más barato y lo completa -------------------------------------------
def test_proteger_elige_el_sitio_mas_barato_y_lo_completa():
    """Dos masas de roca: una a 3 pasos (x ≥ 9) y otra más lejos (x ≤ 2). Sin material, solo puede cavar. Elige la cercana,
    cava 2 casillas (la segunda interior sale del buscador), vuelve una para quedar mirando al acceso, lo cierra y duerme."""
    roca = {(x, y) for x in range(9, 13) for y in range(1, 10)} | {(x, y) for x in range(1, 3) for y in range(1, 10)}
    mundo = MundoCueva(_campo(roca=roca), (6, 5), luz=10.0)
    mem = _memoria(mundo, aprendida=True)
    motivos: List[str] = []

    def al_latir(o, onda):
        ej = onda.reactiva.ef.get("Accion", {}).get("Accion")
        motivos.append(str(ej.carga.get("motivo", "")) if ej is not None else "")

    _vivir(mundo, mem, 30, al_latir)
    assert mundo.encerrado(), motivos
    assert mundo.pos[0] >= 9, mundo.pos                      # en la masa cercana
    assert sum(1 for p, c in mundo.mapa.items() if c == "hueco") == 2
    assert any(m.startswith("proteger: cerrar") for m in motivos)
    assert "proteger: dentro, dormir" in motivos


def test_sin_material_lo_consigue_con_el_planificador_y_cierra():
    """Sin roca en el inventario y sin saber que cavar abre espacio, ningún sitio es factible. El material de cierre es un
    requisito de USAR: Proteger lo pide al planificador (meta instrumental), que lleva a conseguir roca (de lo que la da) y,
    con ella, acaba encerrado. Al coger roca
    aprende además qué deja en la casilla, así que el sitio final puede ser otro que el hueco del principio."""
    mapa = _campo(roca={(x, y) for x in range(1, 13) for y in range(1, 10)} - {(3, 5), (4, 5), (5, 5)} - {(x, 6) for x in range(5, 12)})
    mapa[(11, 7)] = "suelo"
    mapa[(12, 6)] = "cantera"
    mundo = MundoCueva(mapa, (8, 6), cara=(1, 0), luz=10.0)
    mem = _memoria(mundo, aprendida=False)
    mem.paso_libre.update({"suelo": 1})
    mem.paso_bloqueado.update({"roca": 1, "cantera": 1})
    _mapa(mem).aprender_cuerpo("mover", True, True, True)
    _mapa(mem).aprender_cuerpo("mover", False, False, True)
    _mapa(mem).aprender_cuerpo("interactuar", True, False, True)
    motivos: List[str] = []

    def al_latir(o, onda):
        ej = onda.reactiva.ef.get("Accion", {}).get("Accion")
        motivos.append(str(ej.carga.get("motivo", "")) if ej is not None else "")

    _vivir(mundo, mem, 40, al_latir)
    assert any(m.startswith("proteger: pide roca") for m in motivos), motivos   # meta instrumental, la propone S3
    assert mundo.encerrado(), (mundo.pos, motivos)
    assert any(m.startswith("proteger: cerrar") for m in motivos)


def test_sin_la_necesidad_de_cobijo_no_hay_proteger():
    """Proteger está siempre activo, pero solo responde al impulso ``cobijo``: un mundo que no lo declara no lo ve actuar
    (el mapa local sí se aprende, porque el mundo da posiciones y casillas)."""
    roca = {(x, y) for x in range(9, 13) for y in range(1, 10)}
    mundo = MundoCueva(_campo(roca=roca), (6, 5), luz=10.0)
    mundo.perfil = replace(MundoCueva.perfil, necesidades=tuple(n for n in MundoCueva.perfil.necesidades if n.nombre != "cobijo"))
    mem = _memoria(mundo, aprendida=True)
    motivos: List[str] = []

    def al_latir(o, onda):
        ej = onda.reactiva.ef.get("Accion", {}).get("Accion")
        motivos.append(str(ej.carga.get("motivo", "")) if ej is not None else "")

    _vivir(mundo, mem, 20, al_latir)
    assert mem.casillas
    assert not any(m.startswith("proteger") for m in motivos)


# --- 4. la alostasis adelanta la intensidad ---------------------------------------------------------
def _intensidades(mundo: MundoCueva, mem: Memoria, latidos: int) -> List[Dict[str, Dict]]:
    mem.casillas.update(mundo.mapa)      # el campo ya se conoce (mapa recordado): el sitio está lejos pero se sabe dónde
    registro: List[Dict[str, Dict]] = []
    _vivir(mundo, mem, latidos, lambda o, onda: registro.append({n: dict(p.carga) for n, p in onda.reactiva.ef.get("Impulso", {}).items()}))
    return registro


def test_la_alostasis_adelanta_la_intensidad_del_cobijo():
    """La luz baja 2 por latido y el sitio está lejos (roca solo al otro lado del campo): la intensidad del cobijo es la del
    déficit previsto a T pasos (coste del sitio), mayor que el déficit de ahora."""
    roca = {(x, y) for x in range(1, 3) for y in range(1, 10)}
    mundo = MundoCueva(_campo(ancho=16, roca=roca), (13, 5), luz=95.0, bajada=2.0)
    mem = _memoria(mundo, aprendida=True)
    registro = _intensidades(mundo, mem, 40)
    adelantos = [r["cobijo"]["intensidad"] - r["cobijo"]["deficit"] for r in registro if "cobijo" in r and r["cobijo"].get("horizonte", 0) > 0]
    assert adelantos and max(adelantos) > 0.05
    con_horizonte = [r["cobijo"] for r in registro if "cobijo" in r and r["cobijo"].get("horizonte", 0) > 0]
    assert all(c["intensidad"] >= c["deficit"] for c in con_horizonte)


def test_sin_tendencia_no_hay_anticipacion():
    """Una necesidad que no cambia (luz fija) no se anticipa aunque haya sitio."""
    roca = {(x, y) for x in range(1, 3) for y in range(1, 10)}
    mundo = MundoCueva(_campo(ancho=16, roca=roca), (13, 5), luz=60.0)
    registro = _intensidades(mundo, _memoria(mundo, aprendida=True), 20)
    assert all(r["cobijo"]["intensidad"] == r["cobijo"]["deficit"] for r in registro if "cobijo" in r)


# --- Crafter: el refugio lo da la base (3c) ---------------------------------------------------------
def test_crafter_no_tiene_refugio_propio():
    pytest.importorskip("crafter")
    from ida.mundos import crafter
    from ida.mundos.crafter import MundoCrafter

    # D16: la única estrategia que registra Crafter es SalirDelRecinto (su fichero pasa a Crafter en A6b)
    assert [type(d).__name__ for d in MundoCrafter().registro().estrategias["S1"].añade] == ["SalirDelRecinto"]
    assert not MundoCrafter().registro().estrategias["S1"].sustituye
    assert not hasattr(crafter, "RefugioNocturno")


# --- inducción entre clases: menos confianza que lo observado y se corrige con el primer intento -------------
def _memoria_induccion() -> Memoria:
    """Coger «tronco» lo dejó transitable (observado). «Bloque» es no transitable y recogible (su COGER da algo), sin observar."""
    mem = memoria_con_secciones()   # D7: el mapa local es la sección del cuerpo
    mem.aplicar_manual({"inventario": ["tronco", "bloque"], "hechos": [
        {"tipo": "requisito", "verbo": "COGER", "objetivo": "tronco", "requiere_inventario": {}, "requiere_cerca": [], "efecto": {"tronco": 1}},
        {"tipo": "requisito", "verbo": "COGER", "objetivo": "bloque", "requiere_inventario": {}, "requiere_cerca": [], "efecto": {"bloque": 1}},
    ]})
    mem.paso_libre.update({"suelo": 1})
    mem.paso_bloqueado.update({"tronco": 1, "bloque": 1})
    _mapa(mem).aprender_transformacion(Verbo.COGER, "tronco", "tronco", "suelo")
    return mem


def test_lo_inferido_pesa_menos_que_lo_observado():
    m = Modelo(_memoria_induccion(), {}, set())
    assert m.abre("tronco") is True and not m.inferida("tronco")
    assert m.abre("bloque") is True and m.inferida("bloque")
    assert m.confianza_cavar("bloque") < m.confianza_cavar("tronco")


def test_lo_inferido_se_corrige_con_el_primer_intento_real():
    """Si coger «bloque» sale pero la casilla no cambia, ya no se cree que abra espacio; si la deja transitable, pasa a ser
    observado y pesa como lo observado."""
    mem = _memoria_induccion()
    _mapa(mem).aprender_transformacion(Verbo.COGER, "bloque", "bloque", "bloque")     # intento real: no cambia
    m = Modelo(mem, {}, set())
    assert m.abre("bloque") is False
    assert m.falta_para_cavar("bloque") is None
    mem2 = _memoria_induccion()
    _mapa(mem2).aprender_transformacion(Verbo.COGER, "bloque", "bloque", "suelo")     # intento real: abre
    m2 = Modelo(mem2, {}, set())
    assert m2.abre("bloque") is True and not m2.inferida("bloque")
    assert m2.confianza_cavar("bloque") == m2.confianza_cavar("tronco")


def test_el_latido_registra_que_una_accion_con_exito_no_cambio_la_casilla():
    mapa = {(0, 0): "suelo", (1, 0): "bloque"} | {(x, y): "bloque" for x in range(-1, 2) for y in (-1, 1)} | {(-1, 0): "bloque"}
    mem = memoria_con_secciones()   # D7: el mapa local es la sección del cuerpo
    _aprender_mapa(mem, _obs((0, 0), (1, 0), mapa), None)
    accion = {"verbo": Verbo.COGER, "objetivo": "bloque_1_0", "clase": "bloque", "exito": True}
    _aprender_mapa(mem, _obs((0, 0), (1, 0), mapa), accion)
    assert mem.resultado(Verbo.COGER, "bloque", "bloque") == "bloque"
    fallida = {"verbo": Verbo.COGER, "objetivo": "bloque_1_0", "clase": "otra", "exito": False}
    _aprender_mapa(mem, _obs((0, 0), (1, 0), mapa), fallida)
    assert (Verbo.COGER, "otra") not in mem.transformaciones           # sin éxito y sin cambio no dice nada


def test_para_abrir_solo_coge_una_pared_vecina():
    """Recinto de 2 casillas (1,0)+(2,0); la única pared cavable, (0,0), es vecina de (1,0). Desde (2,0) no se coge a dos
    casillas: primero se va a (1,0)."""
    from ida.mundos.crafter.s1.interpretar.recinto import _abrir
    mapa = {(1, 0): "suelo", (2, 0): "suelo", (0, 0): "roca"} | {(x, y): "muro" for x in range(-1, 4) for y in (-1, 1)} | {(3, 0): "muro"}
    mem = _memoria(MundoCueva(mapa, (2, 0)), aprendida=True)
    mem.paso_bloqueado["muro"] = 1
    mem.casillas.update(mapa)
    m = Modelo(mem, {}, set())
    assert _abrir(m, ((1, 0), (2, 0)), (2, 0)) == [{"verbo": Verbo.MOVER, "objetivo": "celda_1_0", "clase": "suelo"}]
    assert _abrir(m, ((1, 0), (2, 0)), (1, 0))[0]["objetivo"] == "roca_0_0"


# --- salir del recinto: una necesidad de fuera apurada saca de él de día ---------------------------
def _encerrado_de_dia(comida: float) -> Tuple[MundoCueva, Memoria]:
    """Dentro de un recinto de 2 casillas excavado en roca, de día (cobijo sin déficit) y sin peligro."""
    roca = {(x, y) for x in range(1, 13) for y in range(1, 10)} - {(6, 5), (6, 6)}
    mundo = MundoCueva(_campo(roca=roca), (6, 5), luz=100.0, comida=comida)
    mem = _memoria(mundo, aprendida=True)
    mem.casillas.update(mundo.mapa)
    return mundo, mem


def test_de_dia_una_necesidad_de_fuera_apurada_abre_el_recinto():
    mundo, mem = _encerrado_de_dia(comida=10.0)
    assert mundo.encerrado()
    motivos: List[str] = []

    def al_latir(o, onda):
        ej = onda.reactiva.ef.get("Accion", {}).get("Accion")
        motivos.append(str(ej.carga.get("motivo", "")) if ej is not None else "")

    _vivir(mundo, mem, 15, al_latir)
    assert any(m.startswith("salir del recinto: abrir roca (hambre") for m in motivos), motivos
    assert not mundo.encerrado()


def test_sin_necesidad_apurada_no_sale_del_recinto():
    """Con la comida llena (sin déficit) nada saca del recinto."""
    mundo, mem = _encerrado_de_dia(comida=100.0)
    motivos: List[str] = []
    def al_latir(o, onda):
        ej = onda.reactiva.ef.get("Accion", {}).get("Accion")
        motivos.append(str(ej.carga.get("motivo", "")) if ej is not None else "")

    _vivir(mundo, mem, 10, al_latir)
    assert not any(m.startswith("salir del recinto") for m in motivos)
    assert mundo.encerrado()


def test_el_riesgo_de_salir_solo_cuenta_desde_el_umbral_de_miedo():
    from ida.sistemas.proteger import riesgo_exterior

    def ctx(peligro: float) -> Any:
        alarma = SimpleNamespace(carga={"peligro": peligro})
        onda = SimpleNamespace(ev=lambda canal: {"alarma": alarma} if canal == "Supervivencia" else {})
        return SimpleNamespace(onda=onda, arquetipo=SimpleNamespace(umbral_miedo=0.5))

    assert riesgo_exterior(ctx(0.3)) == 0.0
    assert riesgo_exterior(ctx(0.9)) == 0.9


def test_dentro_de_un_recinto_no_se_huye():
    """Dentro de un recinto, Huir no es elegible aunque el peligro supere el umbral de miedo: el refugio ya protege."""
    from ida.sistemas.s1 import Huir
    recinto_dentro = SimpleNamespace(carga={"dentro": True})
    onda = SimpleNamespace(ef=lambda canal: {"recinto": recinto_dentro} if canal == "Recinto" else {})
    ctx = SimpleNamespace(onda=onda, arquetipo=SimpleNamespace(umbral_miedo=0.5))
    assert not Huir().elegible(ctx, "seguridad", 0.95)
