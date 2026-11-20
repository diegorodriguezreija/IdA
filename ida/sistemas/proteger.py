"""S1 · «Proteger X» con X = uno mismo: el refugio general (fase de generalización, paso 3).

Diseño: ``docs/ENCARGO_PASO3_PROTEGER.md``. Todo está tras ``Perfil.mecanismos.proteger``; apagado, nada de esto actúa.

| Etapa       | Componente | Produce |
|-------------|------------|---------|
| Interpretar | Recinto    | Recinto: si se está dentro de uno, el mejor sitio para protegerse, el plan para completarlo y su coste |
|             |            | (sin material, el primer paso para conseguirlo, del planificador de S3)                                 |
| Actuar      | Proteger   | (estrategia del impulso ``cobijo``) la acción del plan, quedarse dentro o abrir |

Conceptos (sección 2 del encargo), todos desde la percepción y el mapa local de la memoria, sin nombres de ningún mundo:
- **casilla transitable:** su clase ha sido un lugar (``Memoria.transitable``);
- **transitable para un peligro:** lo es para uno mismo, es desconocida o se ha visto un peligro encima
  (``Memoria.transitable_peligro``);
- **accesos** de un conjunto de casillas: sus vecinas transitables para un peligro;
- **recinto:** 1-3 casillas transitables, conectadas, sin accesos;
- **cerrar un acceso:** un USAR cuyo efecto aprendido deja delante una clase no transitable (sin experiencia, la clase
  que el manual dice que aparece, ``Requisito.aparece``, si ya se sabe que no es transitable);
- **abrir espacio (cavar):** un COGER sobre una clase que, por la transformación aprendida, pasa a ser transitable (sin
  experiencia de esa clase, por inducción desde otras clases recogibles que sí la dejaron transitable);
- **modelo del cuerpo:** cómo cambian posición y orientación tras un MOVER hacia una casilla libre o bloqueada, aprendido
  (``Memoria.modelo_cuerpo``). Con él, un buscador sobre estados (posición, orientación) planifica.

Lo que **no** se escribe: ninguna secuencia de fases. Que hacen falta 2 casillas interiores para sellarse desde dentro
sale del buscador: con una sola, entrar deja de espaldas al acceso y no hay forma de girarse hacia él sin salir.
"""

from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Deque, Dict, FrozenSet, Hashable, Iterable, List, Optional, Set, Tuple

from ida.core.arquitectura import Componente, Contexto
from ida.core.estrategia import ConPropuestas
from ida.core.memoria import DIRECCIONES, Memoria, Pos, pos_de
from ida.core.pieza import Pieza, acotar
from ida.core.vocabulario import Verbo
from ida.sistemas.s3 import PerseguirMetas

COBIJO = "cobijo"
MAX_INTERIOR = 3          # un recinto tiene 1-3 casillas (encargo, sección 2)
ALCANCE_SITIO = 15        # pasos máximos hasta un sitio candidato (3.3)
MAX_PASOS_POSTURA = 12    # buscador de 3.1: «qué secuencia de MOVER me deja en A mirando a C»
PROFUNDIDAD_PLAN = 30     # acciones máximas del plan local de un sitio (cavar, moverse, cerrar)
MAX_ESTADOS = 6000        # coste de cálculo: estados máximos por búsqueda
CANDIDATOS_EXACTOS = 6    # sitios más baratos por la estimación rápida que se planifican del todo
CADA_EVALUACION = 5       # latidos entre evaluaciones completas de sitios (entretanto se replanifica el actual)
MARGEN_SITIO = 0.25       # histéresis: otro sitio sustituye al actual si cuesta al menos un 25 % menos...
MARGEN_SITIO_MIN = 3.0    # ...y al menos 3 pasos menos
BONO_HOGAR = 5.0          # preferencia por el recinto recordado (hogar), en pasos
COSTE_SIN_SITIO = 3 * ALCANCE_SITIO   # horizonte del cobijo sin ningún sitio posible: estimación alta (ir y volver al
                                      # alcance de búsqueda y otro tanto para conseguir material, cavar y cerrar)


# --- percepción ----------------------------------------------------------------------------------
def _yo(ctx: Contexto) -> Dict[str, Any]:
    yo = ctx.onda.ev("Propiocepcion").get("yo")
    return dict(yo.carga) if yo is not None else {}


def posicion(ctx: Contexto) -> Optional[Pos]:
    return pos_de(ctx.observacion.ubicacion) if ctx.observacion is not None else None


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


def _suma(a: Pos, b: Pos) -> Pos:
    return a[0] + b[0], a[1] + b[1]


def _vecinas(p: Pos) -> List[Pos]:
    return [_suma(p, d) for d in DIRECCIONES]


def _manhattan(a: Pos, b: Pos) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


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
        self.casillas = mem.casillas
        self.inv = inv
        self.peligros = peligros
        self.mover_libre = mem.modelo_cuerpo("mover", True)
        self.mover_bloqueado = mem.modelo_cuerpo("mover", False)
        self.interactuar = mem.modelo_cuerpo("interactuar", True)
        self.cerradores = self._cerradores()
        self._cavables: Dict[str, Optional[Dict[str, float]]] = {}
        # Clases no transitables cuyo resultado al cogerlas se ha observado, y cuántas quedaron transitables (inducción).
        observadas = {a for (v, _), t in self.mem.transformaciones.items() if v == Verbo.COGER for (a, _d) in t
                      if self.mem.transitable(a) is False}
        abren = {a for a in observadas if self.mem.transitable(self.mem.resultado(Verbo.COGER, a, a)) is True}
        self._abre_alguna = bool(abren)
        self.induccion = (len(abren) + 1.0) / (len(observadas) + 2.0)    # regla de sucesión de Laplace

    # Casillas
    def libre(self, p: Pos) -> bool:
        return self.mem.transitable(self.casillas.get(p)) is True and p not in self.peligros

    def conocida(self, p: Pos) -> bool:
        return p in self.casillas

    def acceso(self, p: Pos) -> bool:
        return self.mem.transitable_peligro(self.casillas.get(p))

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
        if self.mem.transitable(clase) is not False:
            return None
        despues = self.mem.resultado(Verbo.COGER, clase, clase)
        if despues is not None:
            return self.mem.transitable(despues) is True
        r = self.mem.requisitos.get((Verbo.COGER, clase))
        return True if self._abre_alguna and r is not None and any(n > 0 for n in r.efecto.values()) else None

    def inferida(self, clase: str) -> bool:
        """Que cavar ``clase`` abre espacio se infiere (inducción), no se ha observado."""
        return self.mem.resultado(Verbo.COGER, clase, clase) is None and self.abre(clase) is True

    def confianza_cavar(self, clase: str) -> float:
        """Tasa estimada de cavar la clase; si que abre espacio es inferido, por la confianza de la inducción
        (``induccion``, menor que 1): lo inferido pesa menos que lo observado."""
        c = self.mem.tasa_estimada(Verbo.COGER, clase)
        return c * self.induccion if self.inferida(clase) else c

    def falta_para_cavar(self, clase: str) -> Optional[Dict[str, float]]:
        """Lo que falta en el inventario para cavar ``clase`` (vacío si nada); None si cavarla no abre espacio."""
        if not self.abre(clase):
            return None
        r = self.mem.requisitos.get((Verbo.COGER, clase))
        if r is None:
            return {}
        return {k: float(max(1, n or 1)) - self.inv.get(k, 0.0) for k, n in r.requiere_inventario.items()
                if self.inv.get(k, 0.0) < max(1, n or 1)}

    def _rinde_clase(self, clase: str) -> Optional[Dict[str, float]]:
        """Cavar ``clase`` ahora: abre espacio (``abre``) y se cumple su requisito. Devuelve lo que da al inventario."""
        if self.falta_para_cavar(clase) != {}:
            return None
        r = self.mem.requisitos.get((Verbo.COGER, clase))
        return {k: float(n) for k, n in (r.efecto if r is not None else {}).items() if n > 0}

    # Cierre
    def _cerradores(self) -> List[Cerrador]:
        salida: List[Cerrador] = []
        for (verbo, objetivo), r in sorted(self.mem.requisitos.items(), key=lambda kv: (kv[0][0].value, kv[0][1])):
            if verbo != Verbo.USAR or r.requiere_cerca or not r.requiere_inventario:
                continue
            aprendidas = {d for (_, d) in self.mem.transformaciones.get((verbo, objetivo), {})}
            if aprendidas:
                cierra = any(not self.mem.transitable_peligro(d) for d in aprendidas)
            else:
                cierra = any(self.mem.transitable(a) is False and a not in self.mem.peligro_sobre for a in r.aparece)
            if not cierra:
                continue
            requiere = {k: max(1, n or 1) for k, n in r.requiere_inventario.items()}
            unidades = min(int(self.inv.get(k, 0.0) // n) for k, n in requiere.items())
            salida.append(Cerrador(objetivo, unidades, frozenset(requiere.items()), frozenset(r.delante_fallido)))
        return salida

    def unidades(self, cavadas: Iterable[Pos] = ()) -> int:
        """Cierres posibles con el inventario de ahora más lo que den las casillas ``cavadas``."""
        extra: Dict[str, float] = {}
        for p in cavadas:
            for k, n in (self.rinde(p) or {}).items():
                extra[k] = extra.get(k, 0.0) + n
        return sum(min(int((self.inv.get(k, 0.0) + extra.get(k, 0.0)) // n) for k, n in c.requiere) for c in self.cerradores)

    def cerrable(self, p: Pos) -> bool:
        clase = self.casillas.get(p)
        return any(clase not in c.no_sirve for c in self.cerradores)

    def cerrador_para(self, p: Pos) -> Optional[Cerrador]:
        clase = self.casillas.get(p)
        validos = [c for c in self.cerradores if c.unidades > 0 and clase not in c.no_sirve]
        return max(validos, key=lambda c: (c.unidades, c.objetivo)) if validos else None


# --- buscador sobre estados (3.1) ------------------------------------------------------------------
Accion = Tuple[str, Pos]          # ("mover", destino) | ("coger", casilla) | ("usar", casilla)


def _bfs(inicio: Hashable, sucesores: Callable[[Any], Iterable[Tuple[Accion, Any]]], meta: Callable[[Any], bool],
         profundidad: int, max_estados: int = MAX_ESTADOS) -> Optional[List[Accion]]:
    """Búsqueda en anchura: la secuencia más corta de acciones hasta un estado meta (None si no la hay en el límite)."""
    if meta(inicio):
        return []
    padres: Dict[Any, Tuple[Any, Accion]] = {}
    vistos = {inicio}
    cola: Deque[Tuple[Any, int]] = deque([(inicio, 0)])
    while cola:
        estado, prof = cola.popleft()
        if prof >= profundidad:
            continue
        for accion, nuevo in sucesores(estado):
            if nuevo in vistos:
                continue
            vistos.add(nuevo)
            padres[nuevo] = (estado, accion)
            if meta(nuevo):
                plan: List[Accion] = []
                while nuevo != inicio:
                    nuevo, a = padres[nuevo]
                    plan.append(a)
                return plan[::-1]
            if len(vistos) >= max_estados:
                return None
            cola.append((nuevo, prof + 1))
    return None


def mover(modelo: Modelo, pos: Pos, cara: Optional[Pos], d: Pos, pasable: bool) -> Optional[Tuple[Pos, Optional[Pos]]]:
    """Efecto previsto de MOVER en la dirección ``d`` según el modelo del cuerpo aprendido (None si no se sabe)."""
    m = modelo.mover_libre if pasable else modelo.mover_bloqueado
    if m is None:
        return None
    avanza, mira = m
    return (_suma(pos, d) if avanza else pos), (d if mira else cara)


def buscar_postura(modelo: Modelo, pos: Pos, cara: Optional[Pos], destino: Pos, mirando: Pos,
                   max_pasos: int = MAX_PASOS_POSTURA) -> Optional[List[Accion]]:
    """Secuencia de MOVER que deja en ``destino`` mirando a la casilla ``mirando`` (vecina), o None."""
    cara_meta = (mirando[0] - destino[0], mirando[1] - destino[1])

    def sucesores(e: Tuple[Pos, Optional[Pos]]) -> Iterable[Tuple[Accion, Any]]:
        p, c = e
        for d in DIRECCIONES:
            t = _suma(p, d)
            if _manhattan(t, pos) > max_pasos:
                continue
            r = mover(modelo, p, c, d, modelo.libre(t))
            if r is not None and r != (p, c):
                yield ("mover", t), r

    return _bfs((pos, cara), sucesores, lambda e: e == (destino, cara_meta), max_pasos)


@dataclass(frozen=True)
class EstadoPlan:
    pos: Pos
    cara: Optional[Pos]
    cavadas: FrozenSet[Pos]
    cerradas: FrozenSet[Pos]


def entorno(interior: Tuple[Pos, ...]) -> Set[Pos]:
    """Casillas a 2 o menos (en cada eje) del sitio: la ventana del plan local."""
    return {(x, y) for (cx, cy) in interior for x in range(cx - 2, cx + 3) for y in range(cy - 2, cy + 3)}


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
        for d in DIRECCIONES:
            t = _suma(e.pos, d)
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
    if modelo.mem.transitable(modelo.casillas.get(aqui)) is not True:
        return None
    comp, frontera = {aqui}, [aqui]
    while frontera:
        p = frontera.pop()
        for v in _vecinas(p):
            if v not in comp and modelo.mem.transitable(modelo.casillas.get(v)) is True:
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
            accesos = accesos_de(modelo, interior)
            if accesos is None or not all(modelo.cerrable(p) for p in accesos):
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
              previo: Dict[Pos, Pos], hogar: Optional[Pos]) -> bool:
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
    plan = planificar(modelo, inicio, cara0, sitio.interior, sitio.excavar, sitio.accesos)
    if plan is None:
        return False
    sitio.plan, sitio.desde_aqui = plan, cerca
    sitio.coste = offset + len(plan) - (BONO_HOGAR if hogar is not None and hogar in sitio.interior else 0.0)
    return True


def _abribles(modelo: Modelo, interior: Tuple[Pos, ...]) -> List[Pos]:
    """Paredes del recinto que se pueden cavar para salir; primero las que cerró el propio individuo."""
    paredes = {v for p in interior for v in _vecinas(p) if v not in interior and modelo.rinde(v) is not None}
    return sorted(paredes, key=lambda p: (p not in modelo.mem.cierres, p))

# --- componente de Interpretar ---------------------------------------------------------------------
class Recinto(Componente):
    """Interpreta el espacio para protegerse (con ``mecanismos.proteger``): una pieza ``recinto`` con
    ``dentro`` (y las casillas del recinto), el sitio elegido, la primera acción de su plan, su coste en pasos (lo usa la
    alostasis del cobijo) y su confianza (tasas estimadas de las acciones de cavar y cerrar), y las paredes que se pueden
    abrir. Evalúa todos los candidatos cada ``CADA_EVALUACION`` latidos o cuando cambia el inventario; entretanto, replanifica
    solo el sitio actual.
    Histéresis: otro sitio sustituye al actual solo si es claramente más barato."""

    tipo = "Recinto"
    entradas = ("Propiocepcion",)

    def __init__(self) -> None:
        super().__init__("Recinto")
        self._memoria: Optional[int] = None
        self._sitio: Optional[Tuple[Pos, ...]] = None
        self._ultima = -10**9
        self._ultimo_requisitos = -10**9
        self._sel_requisitos: Optional[Dict[str, Any]] = None
        self._inventario: Dict[str, float] = {}
        self._planificador = PerseguirMetas()

    def reactiva(self, ctx: Contexto) -> None:
        if not ctx.perfil.mecanismos.proteger or not ctx.con_experiencia or not ctx.memoria.activa:
            return
        aqui = posicion(ctx)
        if aqui is None or not ctx.memoria.casillas:
            return
        if self._memoria != id(ctx.memoria):          # vida nueva
            self._memoria, self._sitio, self._ultima = id(ctx.memoria), None, -10**9
            self._ultimo_requisitos, self._sel_requisitos, self._planificador = -10**9, None, PerseguirMetas()
        cara = orientacion(ctx)
        inv = inventario(ctx)
        if inv != self._inventario:       # lo que se tiene cambia qué sitios son completables: se reevalúa ya
            self._inventario, self._ultima, self._ultimo_requisitos = inv, -10**9, -10**9
        modelo = Modelo(ctx.memoria, inv, _peligros(ctx))
        hogar = pos_de(ctx.memoria.hogar()) if ctx.perfil.hogar else None
        dentro = recinto_actual(modelo, aqui)
        carga: Dict[str, Any] = {"dentro": dentro is not None, "interior": list(dentro or ()), "coste": None, "confianza": 0.0,
                                 "accion": None, "explicacion": "", "abrir": [], "requiere": {}}
        if dentro is not None:
            if ctx.perfil.hogar:
                ctx.memoria.recordar_lugar(ctx.observacion.ubicacion if ctx.observacion else "", 1.0)
            carga.update(coste=0.0, confianza=1.0, explicacion="dentro del recinto",
                         abrir=[{"objetivo": f"{modelo.casillas[p]}_{p[0]}_{p[1]}", "clase": modelo.casillas[p]}
                                for p in _abribles(modelo, dentro)])
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
        con_herramientas = Modelo(modelo.mem, {**inv, **herramientas}, modelo.peligros)
        extra = {k: con_herramientas.inv.get(k, 0.0) + n * 2 * len(DIRECCIONES) for k, n in cierre[1].requiere} if cierre else {}
        previsto = Modelo(modelo.mem, {**con_herramientas.inv, **extra}, modelo.peligros)
        previa = self._sel_requisitos
        elegido: Optional[Tuple[Sitio, Dict[str, float]]] = None
        anterior: Optional[Tuple[Sitio, Dict[str, float]]] = None
        for s in candidatos(con_herramientas, aqui, dist, hogar, cierre[0] if cierre else None)[:CANDIDATOS_EXACTOS]:
            clases = sorted({modelo.casillas[p] for p in s.excavar if modelo.casillas.get(p) in coste_cavar})
            if (s.falta == 0 and not clases) or not completar(previsto, s, aqui, cara, dist, previo, hogar):
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
            if actual is not None and not completar(modelo, actual, aqui, cara, dist, previo, hogar):
                actual = None
        perdido = self._sitio is not None and actual is None
        if ctx.latido - self._ultima < CADA_EVALUACION and not perdido:
            return actual          # sin sitio, tampoco se busca otro hasta la próxima evaluación
        self._ultima = ctx.latido
        mejor: Optional[Sitio] = None
        for s in candidatos(modelo, aqui, dist, hogar)[:CANDIDATOS_EXACTOS]:
            if actual is not None and s.interior == actual.interior:
                continue
            if completar(modelo, s, aqui, cara, dist, previo, hogar) and (mejor is None or s.coste < mejor.coste):
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
            if cerrador is not None:
                c *= ctx.memoria.tasa_estimada(Verbo.USAR, cerrador.objetivo)
        return acotar(c)

    @staticmethod
    def _explicar(sitio: Sitio, accion: Dict[str, Any]) -> str:
        donde = "+".join(f"{x},{y}" for x, y in sitio.interior)
        return (f"{accion['que']} {accion['clase'] or accion['objetivo']} · sitio {donde} · cavar {len(sitio.excavar)}, "
                f"cerrar {len(sitio.accesos)}, coste {sitio.coste:.0f}")


def recinto(ctx: Contexto) -> Optional[Pieza]:
    return ctx.onda.ef("Recinto").get("recinto")


# --- estrategia ------------------------------------------------------------------------------------
class Proteger(ConPropuestas):
    """Estrategia general del impulso ``cobijo`` (con ``mecanismos.proteger``): protegerse en un recinto.

    - **Fuera:** si el cobijo pesa al menos tanto como el déficit de las necesidades que se satisfacen fuera, propone la
      primera acción del plan del sitio que interpreta ``Recinto`` (ir, cavar, girarse, cerrar). Arousal = intensidad del
      cobijo (anticipada por la alostasis); confianza = confianza del sitio × esa intensidad: la confianza de que protegerse
      ahora sirve a la necesidad. Sin sitio, o si otra necesidad de fuera pesa más, no propone (deciden otras estrategias).
      La alostasis de 3b no entra aquí: sube la intensidad del hambre y la sed, y con ella el arousal de sus estrategias.
    - **Sin sitio completable:** pide al planificador lo que falta (``pedir``, metas instrumentales) y no propone; ante
      un peligro por encima del umbral de miedo, cede (``_cede``).
    - **Dentro:** si el cobijo (o el peligro de fuera) pesa al menos tanto como el déficit de cualquier necesidad que se
      satisface fuera (las que declaran un ``rasgo``), quedarse: DORMIR (o ESPERAR si el mundo no deja dormir). Si una de
      ellas pesa más, abrir: COGER sobre una pared que se pueda cavar (primero la que cerró uno mismo, que además devuelve
      el material).
    """

    nombre = "proteger"
    impulsos = (COBIJO,)
    prioridad = 10
    agotable = False         # protegerse no baja el déficit del cobijo (la noche sigue): no se agota por falta de progreso

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        r = recinto(ctx)
        return r is not None and (bool(r.carga["dentro"]) or r.carga["accion"] is not None or bool(r.carga.get("requiere")))

    @staticmethod
    def _cede(ctx: Contexto) -> bool:
        """Con un peligro percibido por encima del umbral de miedo (el mismo que hace elegible huir), un sitio que aún no se
        puede completar no se persigue: conseguir lo que falta (material, herramientas) junto a un hostil es exponerse, y
        se deja que respondan las estrategias de Seguridad. Un sitio completable sí se sigue (llegar a él también aleja)."""
        a = ctx.onda.ev("Supervivencia").get("alarma")
        return a is not None and float(a.carga["peligro"]) >= ctx.arquetipo.umbral_miedo

    def pedir(self, ctx: Contexto, estrategia: Pieza) -> List[Dict[str, Any]]:
        """Metas instrumentales: si el mejor sitio necesita algo que no se tiene (``requiere`` del recinto), se pide al
        planificador con urgencia = intensidad anticipada del cobijo. No se pide si otra necesidad de fuera pesa más, ni si
        hay que ceder ante un peligro (``_cede``)."""
        r = recinto(ctx)
        if r is None or r.carga["dentro"] or not r.carga.get("requiere"):
            return []
        cobijo, _, otras = self._intensidades(ctx)
        if otras > cobijo or self._cede(ctx):
            return []
        return [{"objeto": k, "cantidad": n, "urgencia": cobijo, "motivo": f"proteger: {r.carga['explicacion']}"}
                for k, n in sorted(r.carga["requiere"].items())]

    @staticmethod
    def _intensidades(ctx: Contexto) -> Tuple[float, str, float]:
        """Intensidad (anticipada) del cobijo y, de las necesidades «de fuera», la de mayor déficit actual (nombre y déficit).
        «De fuera»: las que se satisfacen con algo del mundo (declaran un ``rasgo``); las del propio cuerpo (descanso, salud)
        se recuperan dentro y no compiten con protegerse."""
        imp = ctx.onda.ef("Impulso")
        cobijo = float(imp[COBIJO].carga["intensidad"]) if COBIJO in imp else 0.0
        fuera = {n.nombre for n in ctx.perfil.necesidades if n.rasgo} - {COBIJO}
        deficits = [(float(p.carga.get("deficit", p.carga["intensidad"])), n) for n, p in imp.items() if n in fuera]
        deficit, nombre = max(deficits, default=(0.0, ""))
        return cobijo, nombre, deficit

    def decidir(self, ctx: Contexto, estrategia: Optional[Pieza] = None) -> None:
        r = recinto(ctx)
        if r is None:
            return
        c = r.carga
        cobijo, otra, otras = self._intensidades(ctx)
        if c["dentro"]:
            a = ctx.onda.ev("Supervivencia").get("alarma")
            peligro = float(a.carga["peligro"]) if a is not None else 0.0
            if max(cobijo, peligro) >= otras or not c["abrir"]:
                verbo = Verbo.DORMIR if Verbo.DORMIR in ctx.verbos else Verbo.ESPERAR
                self.proponer(ctx, verbo, "", cobijo, acotar(cobijo), f"proteger: dentro, {verbo.value.lower()}")
                return
            pared = c["abrir"][0]
            self.proponer(ctx, Verbo.COGER, pared["objetivo"], otras, ctx.memoria.tasa_estimada(Verbo.COGER, pared["clase"]),
                          f"proteger: abrir {pared['clase']} ({otra} {otras:.2f} > cobijo {cobijo:.2f})", clase=pared["clase"])
            return
        accion = c["accion"]
        if accion is None or otras > cobijo:
            return      # otra necesidad de fuera pesa más: que actúen sus estrategias
        self.proponer(ctx, accion["verbo"], accion["objetivo"], cobijo, acotar(float(c["confianza"]) * cobijo),
                      f"proteger: {c['explicacion']}", clase=accion.get("clase", ""), **(accion.get("datos") or {}))
