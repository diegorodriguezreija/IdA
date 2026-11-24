"""Recinto: interpretación del espacio para protegerse en Crafter (D16).

Construcción y búsqueda de recintos, cavar y cerrar accesos.
"""

from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, FrozenSet, Iterable, List, Optional, Set, Tuple, cast

from ida.core.arquitectura import Componente, Contexto
from ida.core.memoria import DIRECCIONES, Memoria, Pos, pos_de
from ida.core.pieza import acotar
from ida.core.vocabulario import Verbo
from ida.cuerpos.cuadricula.buscador import mover
from ida.cuerpos.cuadricula.geometria import Accion, _bfs, _manhattan, _suma, _vecinas, entorno
from ida.cuerpos.cuadricula.memoria import MapaCuadricula
from ida.sistemas.proteger import TIPO_RECINTO
from ida.sistemas.requisito import Requisitos
from ida.sistemas.s3 import PerseguirMetas

MAX_INTERIOR = 3          # un recinto tiene 1-3 casillas (encargo, sección 2)
ALCANCE_SITIO = 15        # pasos máximos hasta un sitio candidato (3.3)
PROFUNDIDAD_PLAN = 30     # acciones máximas del plan local de un sitio (cavar, moverse, cerrar)
CANDIDATOS_EXACTOS = 6    # sitios más baratos por la estimación rápida que se planifican del todo
CADA_EVALUACION = 5       # latidos entre evaluaciones completas de sitios (entretanto se replanifica el actual)
MARGEN_SITIO = 0.25       # histéresis: otro sitio sustituye al actual si cuesta al menos un 25 % menos...
MARGEN_SITIO_MIN = 3.0    # ...y al menos 3 pasos menos
BONO_HOGAR = 5.0          # preferencia por el recinto recordado (hogar), en pasos
COSTE_SIN_SITIO = 3 * ALCANCE_SITIO   # horizonte del cobijo sin ningún sitio posible


# --- percepción ----------------------------------------------------------------------------------
def _yo(ctx: Contexto) -> Dict[str, Any]:
    yo = ctx.onda.ev("Propiocepcion").get("yo")
    return dict(yo.carga) if yo is not None else {}


def posicion(ctx: Contexto) -> Optional[Pos]:
    return pos_de(ctx.ubicacion())


def orientacion(ctx: Contexto) -> Optional[Pos]:
    o = (_yo(ctx).get("cuerpo") or {}).get("orientacion")
    return (int(o[0]), int(o[1])) if isinstance(o, (list, tuple)) and len(o) == 2 else None


def inventario(ctx: Contexto) -> Dict[str, float]:
    return {str(k): float(v) for k, v in (_yo(ctx).get("inventario") or {}).items()}


def _peligros(ctx: Contexto) -> Set[Pos]:
    """Posiciones de lo peligroso percibido ahora (criaturas o casillas)."""
    salida: Set[Pos] = set()
    for p in ctx.onda.ev("Exterocepcion").values():
        if p.rasgo("lugar") < 0.5 and p.rasgo("peligro") >= 0.5:
            pos = p.carga.get("datos", {}).get("pos")
            if isinstance(pos, (list, tuple)) and len(pos) == 2:
                salida.add((int(pos[0]), int(pos[1])))
    return salida


# --- modelo local del mundo (lo que la memoria sabe de él) ---------------------------------------
@dataclass(frozen=True)
class Cerrador:
    """Una acción USAR que cierra un acceso: la casilla de delante deja de ser transitable."""

    objetivo: str
    unidades: int                              # cuántas veces se puede hacer con el inventario de ahora
    requiere: FrozenSet[Tuple[str, int]]       # objetos de inventario que consume y cuántos
    no_sirve: FrozenSet[str]                   # clases de delante sobre las que solo ha fallado


class Modelo:
    """Vista del mapa local para planificar: qué casillas son libres, accesos, cavables; con qué se cierra y cuánto."""

    def __init__(self, mem: Memoria, inv: Dict[str, float], peligros: Set[Pos]):
        self.mem = mem
        self.mapa = cast(MapaCuadricula, mem.seccion("cuadricula"))
        self.req = cast(Requisitos, mem.seccion("requisitos"))
        self.casillas = self.mapa.casillas
        self.inv = inv
        self.peligros = peligros
        self.mover_libre = self.mapa.modelo_cuerpo("mover", True)
        self.mover_bloqueado = self.mapa.modelo_cuerpo("mover", False)
        self.interactuar = self.mapa.modelo_cuerpo("interactuar", True)
        self.cerradores = self._cerradores()
        self._cavables: Dict[str, Optional[Dict[str, float]]] = {}
        self._libre: Dict[Optional[str], bool] = {}
        self._acceso: Dict[Optional[str], bool] = {}
        self._cerrable: Dict[Optional[str], bool] = {}
        self._unidades: Dict[FrozenSet[Pos], int] = {}
        relevantes = {k for r in self.req.requisitos.values() for k in r.requiere_inventario} | {k for c in self.cerradores for k, _ in c.requiere}
        # Lo que determina un plan local, además del sitio y el inicio (clave de la caché de planes de ``Recinto``).
        self.firma = (self.mapa.version_mapa, frozenset(peligros), tuple(sorted((k, inv.get(k, 0.0)) for k in relevantes)),
                      self.mover_libre, self.mover_bloqueado, self.interactuar)
        # Clases no transitables cuyo resultado al cogerlas se ha observado, y cuántas quedaron transitables (inducción).
        observadas = {a for (v, _), t in self.mapa.transformaciones.items() if v == Verbo.COGER for (a, _d) in t
                      if self.mapa.transitable(a) is False}
        abren = {a for a in observadas if self.mapa.transitable(self.mapa.resultado(Verbo.COGER, a, a)) is True}
        self._abre_alguna = bool(abren)
        self.induccion = (len(abren) + 1.0) / (len(observadas) + 2.0)    # regla de sucesión de Laplace

    # Casillas (lo que depende solo de la clase se calcula una vez por clase y modelo: coste de cálculo)
    def libre(self, p: Pos) -> bool:
        clase = self.casillas.get(p)
        v = self._libre.get(clase)
        if v is None:
            v = self._libre[clase] = self.mapa.transitable(clase) is True
        return v and p not in self.peligros

    def conocida(self, p: Pos) -> bool:
        return p in self.casillas

    def acceso(self, p: Pos) -> bool:
        clase = self.casillas.get(p)
        v = self._acceso.get(clase)
        if v is None:
            v = self._acceso[clase] = self.mapa.transitable_peligro(clase)
        return v

    def rinde(self, p: Pos) -> Optional[Dict[str, float]]:
        """Si la casilla se puede cavar ahora, lo que da al inventario (``{}`` si nada); None si no se puede."""
        clase = self.casillas.get(p)
        if clase is None:
            return None
        if clase not in self._cavables:
            self._cavables[clase] = self._rinde_clase(clase)
        return self._cavables[clase]

    def abre(self, clase: str) -> Optional[bool]:
        """Si cavar ``clase`` la deja transitable: lo observado (True o False); sin observarlo, True por inducción si coger
        otra clase no transitable la dejó transitable y esta se sabe recogible (su COGER tiene efecto, del manual o de la
        experiencia); None si no hay base para decirlo. El primer intento real (con éxito) lo sustituye por lo observado."""
        if self.mapa.transitable(clase) is not False:
            return None
        despues = self.mapa.resultado(Verbo.COGER, clase, clase)
        if despues is not None:
            return self.mapa.transitable(despues) is True
        r = self.req.requisitos.get((Verbo.COGER, clase))
        return True if self._abre_alguna and r is not None and any(n > 0 for n in r.efecto.values()) else None

    def inferida(self, clase: str) -> bool:
        """Que cavar ``clase`` abre espacio se infiere (inducción), no se ha observado."""
        return self.mapa.resultado(Verbo.COGER, clase, clase) is None and self.abre(clase) is True

    def confianza_cavar(self, clase: str) -> float:
        """Tasa estimada de cavar la clase; si que abre espacio es inferido, por la confianza de la inducción
        (``induccion``, menor que 1): lo inferido pesa menos que lo observado."""
        c = self.req.tasa_estimada(Verbo.COGER, clase)
        return c * self.induccion if self.inferida(clase) else c

    def falta_para_cavar(self, clase: str) -> Optional[Dict[str, float]]:
        """Lo que falta en el inventario para cavar ``clase`` (vacío si nada); None si cavarla no abre espacio."""
        if not self.abre(clase):
            return None
        r = self.req.requisitos.get((Verbo.COGER, clase))
        if r is None:
            return {}
        return {k: float(max(1, n or 1)) - self.inv.get(k, 0.0) for k, n in r.requiere_inventario.items()
                if self.inv.get(k, 0.0) < max(1, n or 1)}

    def _rinde_clase(self, clase: str) -> Optional[Dict[str, float]]:
        """Cavar ``clase`` ahora: abre espacio (``abre``) y se cumple su requisito. Devuelve lo que da al inventario."""
        if self.falta_para_cavar(clase) != {}:
            return None
        r = self.req.requisitos.get((Verbo.COGER, clase))
        return {k: float(n) for k, n in (r.efecto if r is not None else {}).items() if n > 0}

    # Cierre
    def _cerradores(self) -> List[Cerrador]:
        salida: List[Cerrador] = []
        for (verbo, objetivo), r in sorted(self.req.requisitos.items(), key=lambda kv: (kv[0][0].value, kv[0][1])):
            if verbo != Verbo.USAR or r.requiere_cerca or not r.requiere_inventario:
                continue
            aprendidas = {d for (_, d) in self.mapa.transformaciones.get((verbo, objetivo), {})}
            if aprendidas:
                cierra = any(not self.mapa.transitable_peligro(d) for d in aprendidas)
            else:
                cierra = any(self.mapa.transitable(a) is False and a not in self.mapa.peligro_sobre for a in r.aparece)
            if not cierra:
                continue
            requiere = {k: max(1, n or 1) for k, n in r.requiere_inventario.items()}
            unidades = min(int(self.inv.get(k, 0.0) // n) for k, n in requiere.items())
            salida.append(Cerrador(objetivo, unidades, frozenset(requiere.items()), frozenset(r.delante_fallido)))
        return salida

    def unidades(self, cavadas: Iterable[Pos] = ()) -> int:
        """Cierres posibles con el inventario de ahora más lo que den las casillas ``cavadas``."""
        clave = frozenset(cavadas)
        if clave not in self._unidades:
            self._unidades[clave] = self._contar_unidades(clave)
        return self._unidades[clave]

    def _contar_unidades(self, cavadas: FrozenSet[Pos]) -> int:
        extra: Dict[str, float] = {}
        for p in cavadas:
            for k, n in (self.rinde(p) or {}).items():
                extra[k] = extra.get(k, 0.0) + n
        return sum(min(int((self.inv.get(k, 0.0) + extra.get(k, 0.0)) // n) for k, n in c.requiere) for c in self.cerradores)

    def cerrable(self, p: Pos) -> bool:
        clase = self.casillas.get(p)
        v = self._cerrable.get(clase)
        if v is None:
            v = self._cerrable[clase] = any(clase not in c.no_sirve for c in self.cerradores)
        return v

    def cerrador_para(self, p: Pos) -> Optional[Cerrador]:
        clase = self.casillas.get(p)
        validos = [c for c in self.cerradores if c.unidades > 0 and clase not in c.no_sirve]
        return max(validos, key=lambda c: (c.unidades, c.objetivo)) if validos else None


@dataclass(frozen=True)
class EstadoPlan:
    pos: Pos
    cara: Optional[Pos]
    cavadas: FrozenSet[Pos]
    cerradas: FrozenSet[Pos]


def planificar(modelo: Modelo, pos: Pos, cara: Optional[Pos], interior: Tuple[Pos, ...], excavar: FrozenSet[Pos],
               accesos: FrozenSet[Pos]) -> Optional[List[Accion]]:
    """Plan local para completar el recinto ``interior`` desde (``pos``, ``cara``): cavar ``excavar``, cerrar ``accesos``
    y acabar dentro, sin salir del entorno del sitio (``entorno``). Acciones: MOVER (modelo del cuerpo), COGER sobre una
    casilla vecina por cavar (orienta según el modelo aprendido de interactuar) y USAR sobre la casilla de delante si es un
    acceso abierto y queda material."""
    ventana = entorno(interior)
    unidades: Dict[FrozenSet[Pos], int] = {}
    dentro = set(interior)
    orienta = modelo.interactuar[1] if modelo.interactuar is not None else False

    def sucesores(e: EstadoPlan) -> Iterable[Tuple[Accion, EstadoPlan]]:
        x, y = e.pos
        for d in DIRECCIONES:
            t = (x + d[0], y + d[1])
            if t not in ventana:
                continue
            pasable = t in e.cavadas or (modelo.libre(t) and t not in e.cerradas)
            r = mover(modelo, e.pos, e.cara, d, pasable)
            if r is not None and r != (e.pos, e.cara):
                yield ("mover", t), EstadoPlan(r[0], r[1], e.cavadas, e.cerradas)
            if t in excavar and t not in e.cavadas:
                yield ("coger", t), EstadoPlan(e.pos, d if orienta else e.cara, e.cavadas | {t}, e.cerradas)
        if e.cara is not None:
            f = _suma(e.pos, e.cara)
            if e.cavadas not in unidades:
                unidades[e.cavadas] = modelo.unidades(e.cavadas)
            if f in accesos and f not in e.cerradas and len(e.cerradas) < unidades[e.cavadas]:
                yield ("usar", f), EstadoPlan(e.pos, e.cara, e.cavadas, e.cerradas | {f})

    def meta(e: EstadoPlan) -> bool:
        return e.pos in dentro and e.cavadas == excavar and e.cerradas == accesos

    return _bfs(EstadoPlan(pos, cara, frozenset(), frozenset()), sucesores, meta, PROFUNDIDAD_PLAN)


# --- recintos y sitios -------------------------------------------------------------------------------
def accesos_de(modelo: Modelo, interior: Iterable[Pos]) -> Optional[FrozenSet[Pos]]:
    """Vecinas del conjunto transitables para un peligro (None si alguna vecina no se conoce)."""
    dentro = set(interior)
    salida: Set[Pos] = set()
    for p in dentro:
        for v in _vecinas(p):
            if v in dentro:
                continue
            if not modelo.conocida(v):
                return None
            if modelo.acceso(v):
                salida.add(v)
    return frozenset(salida)


def recinto_actual(modelo: Modelo, aqui: Pos) -> Optional[Tuple[Pos, ...]]:
    """Si ``aqui`` está en un recinto: sus casillas (conjunto conectado de casillas transitables, 1-3, sin accesos)."""
    if modelo.mapa.transitable(modelo.casillas.get(aqui)) is not True:
        return None
    comp, frontera = {aqui}, [aqui]
    while frontera:
        p = frontera.pop()
        for v in _vecinas(p):
            if v not in comp and modelo.mapa.transitable(modelo.casillas.get(v)) is True:
                comp.add(v)
                if len(comp) > MAX_INTERIOR:
                    return None
                frontera.append(v)
    accesos = accesos_de(modelo, comp)
    return tuple(sorted(comp)) if accesos is not None and not accesos else None


def rutas(modelo: Modelo, aqui: Pos, alcance: int = ALCANCE_SITIO) -> Tuple[Dict[Pos, int], Dict[Pos, Pos]]:
    """Distancias en pasos por casillas libres desde ``aqui`` (hasta ``alcance``) y el predecesor de cada una."""
    dist, previo = {aqui: 0}, {}
    cola: Deque[Pos] = deque([aqui])
    while cola:
        p = cola.popleft()
        if dist[p] >= alcance:
            continue
        for v in _vecinas(p):
            if v not in dist and modelo.libre(v):
                dist[v] = dist[p] + 1
                previo[v] = p
                cola.append(v)
    return dist, previo


@dataclass
class Sitio:
    interior: Tuple[Pos, ...]
    excavar: FrozenSet[Pos]
    accesos: FrozenSet[Pos]
    entrada: Pos
    estimado: float
    coste: float = 0.0
    plan: Optional[List[Accion]] = None     # plan local (desde ``entrada`` o desde la posición actual)
    desde_aqui: bool = False                # el plan empieza en la posición actual (si no, en la entrada)
    falta: int = 0                          # cierres para los que aún no hay material


def candidatos(modelo: Modelo, aqui: Pos, dist: Dict[Pos, int], hogar: Optional[Pos],
               coste_unidad: Optional[float] = None) -> List[Sitio]:
    """Sitios posibles con su coste estimado (sin orientación), del más barato al más caro. Con ``coste_unidad`` (pasos para
    conseguir el material de un cierre más), también los sitios a los que les falta material, con ese coste añadido."""
    celdas: Set[Pos] = set(dist)
    for _ in range(2):          # casillas cavables hasta 2 pasos dentro de lo no transitable
        celdas |= {v for p in list(celdas) for v in _vecinas(p) if modelo.rinde(v) is not None}
    sitios: List[Sitio] = []
    vistos: Set[Tuple[Pos, ...]] = set()
    vecinas_acceso: Dict[Pos, Optional[FrozenSet[Pos]]] = {}     # por casilla: sus vecinas que son acceso (None: alguna desconocida)
    no_cerrables: Set[Pos] = set()
    for p in celdas:
        vecinas_acceso[p] = accesos_de(modelo, (p,))
        no_cerrables |= {v for v in vecinas_acceso[p] or () if not modelo.cerrable(v)}
    for a in sorted(celdas):
        for forma in ((a,), (a, _suma(a, (1, 0))), (a, _suma(a, (0, 1)))):
            interior = tuple(sorted(forma))
            if interior in vistos or not all(p in celdas for p in interior):
                continue
            vistos.add(interior)
            excavar = frozenset(p for p in interior if p not in dist)
            if any(modelo.rinde(p) is None for p in excavar):
                continue
            if any(_manhattan(p, q) <= 1 for p in interior for q in modelo.peligros):
                continue         # un peligro dentro o junto al sitio
            partes = [vecinas_acceso[p] for p in interior]
            if any(x is None for x in partes):
                continue
            accesos = frozenset(v for x in partes for v in x or ()) - set(interior)     # = accesos_de(modelo, interior)
            if accesos & no_cerrables:
                continue
            falta = max(0, len(accesos) - modelo.unidades(excavar))
            if falta and coste_unidad is None:
                continue
            entradas = [(dist[p], p) for p in interior if p in dist]
            entradas += [(dist[v], v) for p in excavar for v in _vecinas(p) if v in dist and v not in interior]
            if not entradas:
                continue
            d, entrada = min(entradas)
            estimado = d + len(excavar) + len(accesos) - (BONO_HOGAR if hogar is not None and hogar in interior else 0.0)
            estimado += falta * (coste_unidad or 0.0)
            sitios.append(Sitio(interior, excavar, accesos, entrada, estimado, falta=falta))
    sitios.sort(key=lambda s: (s.estimado, s.interior))
    return sitios


def completar(modelo: Modelo, sitio: Sitio, aqui: Pos, cara: Optional[Pos], dist: Dict[Pos, int],
              previo: Dict[Pos, Pos], hogar: Optional[Pos], cache: Optional[Dict[Any, Optional[List[Accion]]]] = None) -> bool:
    """Plan local exacto del sitio y su coste. Si ``aqui`` está en el entorno del sitio, el plan empieza aquí (y no sale del
    entorno, así que el latido siguiente también); si no, en la entrada, llegando por la ruta más corta (con la orientación de
    llegada que da el modelo del cuerpo)."""
    cerca = aqui in entorno(sitio.interior)
    if cerca:
        inicio, cara0, offset = aqui, cara, 0
    else:
        inicio, offset = sitio.entrada, dist[sitio.entrada]
        antes = previo.get(sitio.entrada)
        cara0 = cara
        if antes is not None and modelo.mover_libre is not None and modelo.mover_libre[1]:
            cara0 = (sitio.entrada[0] - antes[0], sitio.entrada[1] - antes[1])
    clave = (inicio, cara0, sitio.interior, sitio.excavar, sitio.accesos, modelo.firma)
    if cache is not None and clave in cache:
        plan = cache[clave]
    else:
        plan = planificar(modelo, inicio, cara0, sitio.interior, sitio.excavar, sitio.accesos)
        if cache is not None:
            cache[clave] = plan
    if plan is None:
        return False
    sitio.plan, sitio.desde_aqui = plan, cerca
    sitio.coste = offset + len(plan) - (BONO_HOGAR if hogar is not None and hogar in sitio.interior else 0.0)
    return True


def _abrir(modelo: Modelo, interior: Tuple[Pos, ...], aqui: Pos) -> List[Dict[str, Any]]:
    """Cómo salir del recinto: COGER sobre una pared que se pueda cavar y esté al lado (primero las que cerró el propio
    individuo); si ninguna está al lado, MOVER a la casilla interior que tiene una (COGER solo actúa sobre lo vecino)."""
    paredes = sorted({v for p in interior for v in _vecinas(p) if v not in interior and modelo.rinde(v) is not None},
                     key=lambda p: (p not in modelo.mapa.cierres, p))
    vecinas = [p for p in paredes if _manhattan(p, aqui) == 1]
    if vecinas:
        return [{"verbo": Verbo.COGER, "objetivo": f"{modelo.casillas[p]}_{p[0]}_{p[1]}", "clase": modelo.casillas[p]} for p in vecinas]
    for pared in paredes:
        desde = next((p for p in interior if _manhattan(p, pared) == 1), None)
        if desde is not None:
            return [{"verbo": Verbo.MOVER, "objetivo": f"celda_{desde[0]}_{desde[1]}", "clase": modelo.casillas.get(desde, "")}]
    return []


# --- componente de Interpretar ---------------------------------------------------------------------
class Recinto(Componente):
    """Interpreta el espacio para protegerse: una pieza ``recinto`` con
    ``dentro`` (y las casillas del recinto), el sitio elegido, la primera acción de su plan, su coste en pasos (lo usa la
    alostasis del cobijo) y su confianza (tasas estimadas de las acciones de cavar y cerrar), y las paredes que se pueden
    abrir. Evalúa todos los candidatos cada ``CADA_EVALUACION`` latidos o cuando cambia el inventario; entretanto, replanifica
    solo el sitio actual.
    Histéresis: otro sitio sustituye al actual solo si es claramente más barato."""

    tipo = TIPO_RECINTO
    entradas = ("Propiocepcion",)

    def __init__(self) -> None:
        super().__init__("Recinto")
        self._memoria: Optional[int] = None
        self._sitio: Optional[Tuple[Pos, ...]] = None
        self._ultima = -10**9
        self._ultimo_requisitos = -10**9
        self._sel_requisitos: Optional[Dict[str, Any]] = None
        self._inventario: Dict[str, float] = {}
        self._planes: Dict[Any, Optional[List[Accion]]] = {}     # caché de planes locales (coste de cálculo)
        self._planificador = PerseguirMetas()

    def reactiva(self, ctx: Contexto) -> None:
        if not ctx.con_experiencia or not ctx.memoria.activa:
            return
        aqui = posicion(ctx)
        sec_cuad = cast(MapaCuadricula, ctx.memoria.seccion("cuadricula")) if ctx.memoria.tiene_seccion("cuadricula") else None
        if aqui is None or sec_cuad is None or not sec_cuad.casillas:
            return
        if self._memoria != id(ctx.memoria):          # vida nueva
            self._memoria, self._sitio, self._ultima = id(ctx.memoria), None, -10**9
            self._ultimo_requisitos, self._sel_requisitos, self._planificador = -10**9, None, PerseguirMetas()
            self._planes.clear()
        cara = orientacion(ctx)
        inv = inventario(ctx)
        sec_req = cast(Requisitos, ctx.memoria.seccion("requisitos")) if ctx.memoria.tiene_seccion("requisitos") else None
        objetos = sec_req.objetos(inv) if sec_req is not None else {k: float(v) for k, v in inv.items()}
        if objetos != self._inventario:   # los objetos que se tienen cambian qué sitios son completables: se reevalúa ya
            self._inventario, self._ultima, self._ultimo_requisitos = objetos, -10**9, -10**9
        modelo = Modelo(ctx.memoria, inv, _peligros(ctx))
        if len(self._planes) > 2000 or any(k[-1][0] != sec_cuad.version_mapa for k in list(self._planes)[:1]):
            self._planes.clear()      # el mapa ha cambiado: los planes guardados ya no valen
        hogar = pos_de(ctx.memoria.hogar()) if ctx.perfil.hogar else None
        dentro = recinto_actual(modelo, aqui)
        carga: Dict[str, Any] = {"dentro": dentro is not None, "interior": list(dentro or ()), "coste": None, "confianza": 0.0,
                                 "accion": None, "explicacion": "", "abrir": [], "requiere": {}}
        if dentro is not None:
            if ctx.perfil.hogar:
                ctx.memoria.recordar_lugar(ctx.ubicacion(), 1.0, autor=type(self).__name__)
            carga.update(coste=0.0, confianza=1.0, explicacion="dentro del recinto",
                         abrir=_abrir(modelo, dentro, aqui))
            self._sitio = dentro
            self.registrar(ctx, self.pieza(ctx, "recinto", arousal=0.0, carga=carga))
            return
        dist, previo = rutas(modelo, aqui)
        sitio = self._elegir(ctx, modelo, aqui, cara, dist, previo, hogar)
        if sitio is not None and sitio.plan is not None:
            accion = self._primera(modelo, sitio, aqui, previo)
            if accion is not None:
                carga.update(coste=round(sitio.coste, 2), confianza=round(self._confianza(ctx, modelo, sitio), 4), accion=accion,
                             interior=list(sitio.interior), explicacion=self._explicar(sitio, accion))
        elif sitio is None:
            if ctx.latido - self._ultimo_requisitos >= CADA_EVALUACION:     # sin elección, tampoco se rehace antes
                self._sel_requisitos = self._requisitos(ctx, modelo, aqui, cara, dist, previo, hogar)
            carga.update(self._sel_requisitos or {})
        self.registrar(ctx, self.pieza(ctx, "recinto", arousal=0.0, carga=carga))

    def _coste_objeto(self, ctx: Contexto, objeto: str, inv: Dict[str, float], cache: Dict[str, Optional[float]]) -> Optional[float]:
        """Pasos estimados por el planificador del paso 5 para tener una unidad más de ``objeto`` (None si nada lo da)."""
        if objeto not in cache:
            paso = self._planificador.conseguir(ctx, objeto, {**inv, objeto: 0.0})
            cache[objeto] = None if paso is None else paso.coste + 1.0
        return cache[objeto]

    def _requisitos(self, ctx: Contexto, modelo: Modelo, aqui: Pos, cara: Optional[Pos], dist: Dict[Pos, int],
                    previo: Dict[Pos, Pos], hogar: Optional[Pos]) -> Optional[Dict[str, Any]]:
        """Sin sitio completable con lo que se tiene: el mejor sitio cuyos requisitos sin cumplir se pueden conseguir, con el
        coste completo (3.4 del encargo; metas instrumentales). Requisitos: el objeto que pide cavar una clase (p. ej. una
        herramienta) y el material de los cierres que faltan, ambos requisitos de acciones de la memoria. El coste de cada
        unidad lo da el planificador del paso 5 (``PerseguirMetas.conseguir``). El plan del sitio se comprueba con el
        buscador sobre un inventario previsto que ya tiene lo que falta. Lo que falta no lo propone ``Recinto``: ``Proteger``
        lo pide al planificador (``requiere``). Se rehace cada ``CADA_EVALUACION`` latidos, con histéresis."""
        self._ultimo_requisitos = ctx.latido
        inv = modelo.inv
        cache: Dict[str, Optional[float]] = {}
        # Requisitos para cavar: clases que abrirían espacio si se tuviera lo que pide su COGER.
        coste_cavar: Dict[str, float] = {}
        herramientas: Dict[str, float] = {}
        for clase in sorted(set(modelo.casillas.values())):
            falta = modelo.falta_para_cavar(clase)
            if not falta:
                continue
            costes = [self._coste_objeto(ctx, k, inv, cache) for k in sorted(falta)]
            if any(c is None for c in costes):
                continue
            coste_cavar[clase] = sum((c or 0.0) * falta[k] for c, k in zip(costes, sorted(falta), strict=True))
            for k, n in falta.items():
                herramientas[k] = max(herramientas.get(k, 0.0), inv.get(k, 0.0) + n)
        # Material: el cierre más barato por unidad.
        cierre: Optional[Tuple[float, Cerrador]] = None
        for c in modelo.cerradores:
            costes = [self._coste_objeto(ctx, k, inv, cache) for k, _ in c.requiere]
            if any(x is None for x in costes):
                continue
            por_unidad = sum((x or 0.0) * n for x, (_, n) in zip(costes, c.requiere, strict=True))
            if cierre is None or por_unidad < cierre[0]:
                cierre = (por_unidad, c)
        if cierre is None and not coste_cavar:
            return None           # nada que conseguir haría completable un sitio
        con_herramientas = Modelo(modelo.mem, {**inv, **herramientas}, modelo.peligros)
        extra = {k: con_herramientas.inv.get(k, 0.0) + n * 2 * len(DIRECCIONES) for k, n in cierre[1].requiere} if cierre else {}
        previsto = Modelo(modelo.mem, {**con_herramientas.inv, **extra}, modelo.peligros)
        previa = self._sel_requisitos
        elegido: Optional[Tuple[Sitio, Dict[str, float]]] = None
        anterior: Optional[Tuple[Sitio, Dict[str, float]]] = None
        for s in candidatos(con_herramientas, aqui, dist, hogar, cierre[0] if cierre else None)[:CANDIDATOS_EXACTOS]:
            clases = sorted({modelo.casillas[p] for p in s.excavar if modelo.casillas.get(p) in coste_cavar})
            if (s.falta == 0 and not clases) or not completar(previsto, s, aqui, cara, dist, previo, hogar, self._planes):
                continue
            requiere: Dict[str, float] = {}
            for clase in clases:
                for k, n in (modelo.falta_para_cavar(clase) or {}).items():
                    requiere[k] = max(requiere.get(k, 0.0), inv.get(k, 0.0) + n)
            if s.falta and cierre is not None:
                for k, n in cierre[1].requiere:
                    requiere[k] = requiere.get(k, inv.get(k, 0.0)) + s.falta * n
            s.coste += s.falta * (cierre[0] if cierre else 0.0) + sum(coste_cavar[c] for c in clases)
            if previa is not None and list(s.interior) == previa["interior"]:
                anterior = (s, requiere)
            if elegido is None or s.coste < elegido[0].coste:
                elegido = (s, requiere)
        if anterior is not None and elegido is not None and \
                elegido[0].coste > anterior[0].coste - max(MARGEN_SITIO_MIN, MARGEN_SITIO * anterior[0].coste):
            elegido = anterior
        if elegido is None:
            return None
        s, requiere = elegido
        donde = "+".join(f"{x},{y}" for x, y in s.interior)
        pide = ", ".join(f"{k} {n:g}" for k, n in sorted(requiere.items()))
        confianza = self._confianza(ctx, previsto, s)
        return {"coste": round(s.coste, 2), "confianza": round(confianza, 4), "interior": list(s.interior), "requiere": requiere,
                "explicacion": f"conseguir {pide} · sitio {donde} · cavar {len(s.excavar)}, cerrar {len(s.accesos)}, coste {s.coste:.0f}"}

    def _elegir(self, ctx: Contexto, modelo: Modelo, aqui: Pos, cara: Optional[Pos], dist: Dict[Pos, int],
                previo: Dict[Pos, Pos], hogar: Optional[Pos]) -> Optional[Sitio]:
        actual: Optional[Sitio] = None
        if self._sitio is not None:
            actual = self._reconstruir(modelo, self._sitio, dist, hogar)
            if actual is not None and not completar(modelo, actual, aqui, cara, dist, previo, hogar, self._planes):
                actual = None
        perdido = self._sitio is not None and actual is None
        if ctx.latido - self._ultima < CADA_EVALUACION and not perdido:
            return actual          # sin sitio, tampoco se busca otro hasta la próxima evaluación
        self._ultima = ctx.latido
        mejor: Optional[Sitio] = None
        for s in candidatos(modelo, aqui, dist, hogar)[:CANDIDATOS_EXACTOS]:
            if actual is not None and s.interior == actual.interior:
                continue
            if completar(modelo, s, aqui, cara, dist, previo, hogar, self._planes) and (mejor is None or s.coste < mejor.coste):
                mejor = s
        if actual is not None and (mejor is None or mejor.coste > actual.coste - max(MARGEN_SITIO_MIN, MARGEN_SITIO * actual.coste)):
            mejor = actual
        self._sitio = mejor.interior if mejor is not None else None
        return mejor

    @staticmethod
    def _reconstruir(modelo: Modelo, interior: Tuple[Pos, ...], dist: Dict[Pos, int], hogar: Optional[Pos]) -> Optional[Sitio]:
        """El sitio actual con el mapa de ahora (sin enumerar todos los candidatos)."""
        excavar = frozenset(p for p in interior if p not in dist)
        if any(modelo.rinde(p) is None for p in excavar) or any(_manhattan(p, q) <= 1 for p in interior for q in modelo.peligros):
            return None
        accesos = accesos_de(modelo, interior)
        if accesos is None or not all(modelo.cerrable(p) for p in accesos):
            return None
        if len(accesos) > modelo.unidades(excavar):
            return None
        entradas = [(dist[p], p) for p in interior if p in dist]
        entradas += [(dist[v], v) for p in excavar for v in _vecinas(p) if v in dist and v not in interior]
        if not entradas:
            return None
        d, entrada = min(entradas)
        return Sitio(interior, excavar, accesos, entrada, float(d + len(excavar) + len(accesos)))

    @staticmethod
    def _primera(modelo: Modelo, sitio: Sitio, aqui: Pos, previo: Dict[Pos, Pos]) -> Optional[Dict[str, Any]]:
        """La acción de este latido: el primer paso de la ruta hasta la entrada o la primera acción del plan local."""
        if not sitio.desde_aqui:
            camino = [sitio.entrada]
            while camino[-1] != aqui and camino[-1] in previo:
                camino.append(previo[camino[-1]])
            if camino[-1] != aqui or len(camino) < 2:
                return None
            siguiente = camino[-2]
            return {"verbo": Verbo.MOVER, "objetivo": f"celda_{siguiente[0]}_{siguiente[1]}", "clase": modelo.casillas.get(siguiente, ""),
                    "que": "ir"}
        if not sitio.plan:
            return None
        tipo, p = sitio.plan[0]
        clase = modelo.casillas.get(p, "")
        if tipo == "mover":
            return {"verbo": Verbo.MOVER, "objetivo": f"celda_{p[0]}_{p[1]}", "clase": clase,
                    "que": "colocarse" if modelo.libre(p) or p in sitio.excavar else "girarse"}
        if tipo == "coger":
            return {"verbo": Verbo.COGER, "objetivo": f"{clase}_{p[0]}_{p[1]}", "clase": clase, "que": "cavar"}
        cerrador = modelo.cerrador_para(p)
        if cerrador is None:
            return None
        return {"verbo": Verbo.USAR, "objetivo": cerrador.objetivo, "clase": cerrador.objetivo, "que": "cerrar",
                "datos": {"receta": cerrador.objetivo}, "casilla": list(p)}

    @staticmethod
    def _confianza(ctx: Contexto, modelo: Modelo, sitio: Sitio) -> float:
        """Producto de las tasas estimadas de las acciones del plan (cavar cada clase, cerrar). Cavar una clase de la que
        solo se infiere que abre espacio pesa menos (``Modelo.confianza_cavar``)."""
        c = 1.0
        for clase in sorted({modelo.casillas[p] for p in sitio.excavar}):
            c *= modelo.confianza_cavar(clase)
        if sitio.accesos:
            cerrador = next((modelo.cerrador_para(p) for p in sorted(sitio.accesos) if modelo.cerrador_para(p) is not None), None)
            if cerrador is not None and ctx.memoria.tiene_seccion("requisitos"):
                c *= cast(Requisitos, ctx.memoria.seccion("requisitos")).tasa_estimada(Verbo.USAR, cerrador.objetivo)
        return acotar(c)

    @staticmethod
    def _explicar(sitio: Sitio, accion: Dict[str, Any]) -> str:
        donde = "+".join(f"{x},{y}" for x, y in sitio.interior)
        return (f"{accion['que']} {accion['clase'] or accion['objetivo']} · sitio {donde} · cavar {len(sitio.excavar)}, "
                f"cerrar {len(sitio.accesos)}, coste {sitio.coste:.0f}")
