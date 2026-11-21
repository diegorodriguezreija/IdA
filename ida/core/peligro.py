"""Peligro aprendido (paso 6 de la fase de generalización, ``docs/ENCARGO_PASO6_DEFENSA.md``).

Con ``Perfil.mecanismos.peligro_aprendido``, y solo en un mundo que da posiciones (ubicación ``<nombre>_x_y`` y
``datos["pos"]``) y no da su propio rasgo ``peligro``, la base aprende de la experiencia:

- **daño por contacto** de cada clase: media móvil de la vitalidad perdida en cada **encuentro** con una instancia suya
  (desde que esa instancia está junto a uno, o le daña, hasta que deja de verse), con lo que el mundo atribuye a esa
  clase (``Efecto.causa``, que el mundo da por contacto; el daño va a la instancia de esa clase más cercana). Un
  encuentro sin daño cuenta 0. Mientras dura un encuentro, lo ya perdido en él es el mínimo del daño esperado.
  Previo: ``DANO_PREVIO`` con peso ``PESO_PREVIO`` para lo que la memoria tiene por peligroso (el manual o la
  experiencia: ``Relacion.PELIGROSO`` no refutada); 0 para lo demás;
- **daño por golpe** (cada daño atribuido) y **tasa** de daño de cada clase (daños por latido de exposición: latidos con
  una instancia a su alcance). Son los que usa la valoración de una lucha (``Afrontar``);
- **emisor**, por contingencia (como la de ``Satisface``): la clase X emite la clase Y si las Y que aparecen (un id
  nuevo) lo hacen junto a una X más de lo que tocaría por azar. ΔP = (junto − esperado) / n, con ``esperado`` la suma,
  en cada aparición, de la fracción de casillas a la vista que están junto a alguna X. Un emisor hereda el daño de lo
  que emite;
- **alcance**: 1 (contacto) para el daño propio; para un emisor, la mayor distancia recorrida desde él por lo que emite
  (más el contacto), de las últimas ``MAX_RECORRIDOS``;
- **eficacia de ataque**: golpes (ATACAR o COMER sobre una instancia adyacente) hasta que la instancia desaparece
  estando junto a uno (derribo), con los objetos que se llevaban. Un objeto **reduce** los golpes si, por contingencia
  entre llevarlo y los golpes por derribo, los derribos con él piden menos golpes que sin él (razón media entre clases).

La **estimación** del rasgo ``peligro`` de una entidad a distancia ``d``:
``acotar(max_componente(daño · f(d, alcance)) / salud)``, con ``f = 1`` hasta el alcance y ``1 / (1 + d − alcance)``
más allá. El de un lugar, el máximo del de lo peligroso percibido, a la distancia de ese lugar.

Ninguna cifra es de un mundo: los previos están declarados aquí y valen para cualquiera.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

from ida.core.pieza import acotar

Pos = Tuple[int, int]

VITALIDAD_MAXIMA = 100.0
DANO_PREVIO = VITALIDAD_MAXIMA * 2.0 / 9.0   # daño desconocido de lo peligroso: 2 de 9 unidades de vitalidad (declarado)
PESO_PREVIO = 2.0                            # peso (en daños) del previo
VENTANA = 20                                 # media móvil: los últimos ~20 daños de cada clase
TASA_PREVIA = 0.5                            # daños por latido de exposición, sin datos (pesimista)
PESO_TASA = 2.0                              # peso (en latidos) del previo de la tasa
GOLPES_PREVIO = 10.0                         # golpes para derribar algo sin datos (pesimista: así no se lucha)
EMISION_MINIMA = 0.5                         # ΔP a partir del cual X emite Y
N_EMISION_MINIMA = 2                         # apariciones de Y mínimas para decidirlo
MAX_RECORRIDOS = 10
MAX_DERRIBOS = 30
MARGEN_REDUCTOR = 0.15                       # razón de golpes con / sin el objeto por debajo de 1 − margen: reduce
MINIMO_LEGADO = 2                            # observaciones mínimas para pasar al legado


def manhattan(a: Pos, b: Pos) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def f_alcance(d: int, alcance: int) -> float:
    """Proximidad respecto al alcance: 1 dentro del alcance; fuera, 1 / (1 + pasos que faltan para entrar en él)."""
    return 1.0 if d <= alcance else 1.0 / (1.0 + d - alcance)


@dataclass
class Media:
    """Media móvil de una magnitud (los últimos ``VENTANA`` valores pesan por igual al principio)."""

    n: int = 0
    media: float = 0.0

    def anotar(self, x: float) -> None:
        self.n += 1
        self.media += (x - self.media) / min(self.n, VENTANA)

    def estimar(self, previo: float, peso: float) -> float:
        w = min(self.n, VENTANA)
        return (peso * previo + w * self.media) / (peso + w) if peso + w > 0 else previo


@dataclass
class Emision:
    """Contingencia «Y aparece junto a X»: ``n`` apariciones de Y con X a la vista, ``junto`` de ellas junto a una X y
    ``esperado`` las que tocarían por azar."""

    n: int = 0
    junto: int = 0
    esperado: float = 0.0

    def contingencia(self) -> float:
        return max(0.0, min(1.0, (self.junto - self.esperado) / self.n)) if self.n else 0.0


@dataclass
class Peligros:
    """Lo que la base aprende del peligro (paso 6). Vive en ``Memoria.peligros``; la escribe el Core cada latido."""

    dano: Dict[str, Media] = field(default_factory=dict)          # por encuentro
    dano_golpe: Dict[str, Media] = field(default_factory=dict)    # por daño atribuido
    expuestos: Dict[str, int] = field(default_factory=dict)       # latidos con una instancia de la clase a su alcance
    eventos: Dict[str, int] = field(default_factory=dict)         # daños de la clase (o de lo que emite) en esos latidos
    emision: Dict[Tuple[str, str], Emision] = field(default_factory=dict)
    recorridos: Dict[str, List[int]] = field(default_factory=dict)   # emisor -> distancias alcanzadas por lo que emite
    derribos: Dict[str, List[Tuple[FrozenSet[str], int]]] = field(default_factory=dict)   # clase -> (objetos llevados, golpes)
    # Estado de esta vida (no se hereda)
    vistos: Dict[str, Tuple[str, Pos]] = field(default_factory=dict)          # id -> (clase, posición) del latido anterior
    emitidos: Dict[str, Tuple[str, Pos]] = field(default_factory=dict)        # id -> (clase del emisor, su posición al aparecer)
    golpeando: Dict[str, Tuple[str, int, FrozenSet[str]]] = field(default_factory=dict)   # id -> (clase, golpes, objetos)
    encuentros: Dict[str, Tuple[str, float]] = field(default_factory=dict)   # id -> (clase, daño acumulado en el encuentro)
    aqui_previo: Optional[Pos] = None
    objetos_previos: FrozenSet[str] = frozenset()

    # --- estimaciones ---------------------------------------------------------
    def emitidas(self, x: str) -> List[str]:
        """Las clases que emite ``x``."""
        return sorted(y for (a, y), e in self.emision.items() if a == x and e.n >= N_EMISION_MINIMA and e.contingencia() >= EMISION_MINIMA)

    def alcance_emision(self, x: str) -> int:
        r = self.recorridos.get(x)
        return max(r) if r else 1

    def dano_propio(self, clase: str, peligrosa: bool) -> float:
        """Daño esperado de un contacto con ``clase``: la media aprendida con su previo, y como mínimo lo perdido en el
        contacto en curso."""
        m = self.dano.get(clase)
        previo = DANO_PREVIO if peligrosa else 0.0
        estimado = m.estimar(previo, PESO_PREVIO) if m is not None else previo
        en_curso = [d for c, d in self.encuentros.values() if c == clase]
        return max([estimado] + en_curso)

    def dano_por_golpe(self, clase: str, peligrosa) -> float:
        """Daño de cada golpe de ``clase`` o de lo que emite (el mayor), con el mismo previo."""
        def una(c: str) -> float:
            m = self.dano_golpe.get(c)
            previo = DANO_PREVIO if peligrosa(c) else 0.0
            return m.estimar(previo, PESO_PREVIO) if m is not None else previo
        return max([una(clase)] + [una(y) for y in self.emitidas(clase)])

    def componentes(self, clase: str, peligrosa) -> List[Tuple[float, int]]:
        """(daño, alcance) de cada forma en que ``clase`` puede hacer daño: el propio, por contacto, y el de lo que emite.
        ``peligrosa(c)`` dice si la memoria tiene la clase ``c`` por peligrosa (para el previo)."""
        comps = [(self.dano_propio(clase, peligrosa(clase)), 1)]
        alcance = self.alcance_emision(clase)
        for y in self.emitidas(clase):
            comps.append((self.dano_propio(y, peligrosa(y)), alcance))
        return [c for c in comps if c[0] > 0.0]

    def dano_esperado(self, clase: str, peligrosa) -> float:
        return max((d for d, _ in self.componentes(clase, peligrosa)), default=0.0)

    def alcance(self, clase: str, peligrosa) -> int:
        return max((a for _, a in self.componentes(clase, peligrosa)), default=1)

    def peligro_a(self, comps: List[Tuple[float, int]], d: int, salud: float) -> float:
        if not comps:
            return 0.0
        return acotar(max(dano * f_alcance(d, a) for dano, a in comps) / max(salud, 1.0))

    def tasa(self, clase: str) -> Tuple[float, int]:
        """Daños por latido de exposición a ``clase`` y latidos de exposición contados."""
        n = self.expuestos.get(clase, 0)
        return (self.eventos.get(clase, 0) + PESO_TASA * TASA_PREVIA) / (n + PESO_TASA), n

    def reductores(self) -> Dict[str, float]:
        """Objetos que reducen los golpes por derribo, con su razón media (golpes con él / sin él) entre las clases en que
        hay derribos con y sin el objeto."""
        razones: Dict[str, List[float]] = {}
        objetos: Set[str] = set()
        for lista in self.derribos.values():
            for kit, _ in lista:
                objetos |= kit
        for x in sorted(objetos):
            for lista in self.derribos.values():
                con = [g for kit, g in lista if x in kit]
                sin = [g for kit, g in lista if x not in kit]
                if con and sin and sum(sin) > 0:
                    razones.setdefault(x, []).append((sum(con) / len(con)) / (sum(sin) / len(sin)))
        medias = {x: sum(r) / len(r) for x, r in razones.items()}
        return {x: r for x, r in medias.items() if r < 1.0 - MARGEN_REDUCTOR}

    def golpes(self, clase: str, objetos: Iterable[str], reductores: Optional[Dict[str, float]] = None) -> Tuple[float, int]:
        """Golpes estimados para derribar una ``clase`` llevando ``objetos``, y derribos de la clase en que se basa.
        Con derribos con los mismos reductores, su media; si no, los de la clase llevados a «sin reductores» y escalados
        por el mejor reductor llevado; sin derribos de la clase, el previo pesimista."""
        lista = self.derribos.get(clase, [])
        if not lista:
            return GOLPES_PREVIO, 0
        red = self.reductores() if reductores is None else reductores
        clave = frozenset(objetos) & frozenset(red)
        iguales = [g for kit, g in lista if kit & frozenset(red) == clave]
        if iguales:
            return sum(iguales) / len(iguales), len(iguales)

        def factor(kit: FrozenSet[str]) -> float:
            return min((red[x] for x in kit if x in red), default=1.0)
        base = sum(g / factor(kit) for kit, g in lista) / len(lista)
        return base * factor(clave), len(lista)

    # --- aprendizaje (cada latido, desde lo percibido) ----------------------------
    def aprender(self, aqui: Pos, agentes: Dict[str, Tuple[str, Pos]], visibles: Set[Pos], objetos: FrozenSet[str],
                 verbo: Optional[str], objetivo: str, causa: Optional[str], perdida: float, peligrosa) -> None:
        """Un latido. ``agentes``: id -> (clase, posición) de lo que se mueve a la vista (no lugares); ``visibles``: las
        casillas a la vista; ``objetos``: lo que se lleva ahora; ``verbo`` y ``objetivo``: la acción anterior; ``causa`` y
        ``perdida``: el daño que dejó (clase y vitalidad perdida)."""
        previos = self.vistos
        por_clase: Dict[str, int] = {}     # distancia mínima a cada clase en el latido anterior (cuando se actuó)
        if self.aqui_previo is not None:
            for _, (c, p) in previos.items():
                d = manhattan(self.aqui_previo, p)
                por_clase[c] = min(d, por_clase.get(c, d))
        # Encuentros (contacto con una instancia) y daño atribuido por el mundo
        if self.aqui_previo is not None:
            for i, (c, p) in previos.items():
                if i not in self.encuentros and manhattan(self.aqui_previo, p) <= 1 and (peligrosa(c) or c in self.dano or c in self.dano_golpe):
                    self.encuentros[i] = (c, 0.0)
        if causa and perdida > 0.0:
            self.dano_golpe.setdefault(str(causa), Media()).anotar(perdida)
            ref = self.aqui_previo or aqui
            candidatas = sorted((manhattan(ref, p), i) for i, (c, p) in previos.items() if c == causa)
            i = candidatas[0][1] if candidatas else f"?{causa}"
            self.encuentros[i] = (str(causa), self.encuentros.get(i, (str(causa), 0.0))[1] + perdida)
        for i in [i for i in self.encuentros if i not in agentes]:
            c, total = self.encuentros.pop(i)
            self.dano.setdefault(c, Media()).anotar(total)
        # Exposición y tasa: latidos con la clase a su alcance (los del latido anterior, cuando se recibió el daño)
        if self.aqui_previo is not None:
            for c, d in por_clase.items():
                if d <= self.alcance(c, peligrosa) and self.dano_esperado(c, peligrosa) > 0.0:
                    self.expuestos[c] = self.expuestos.get(c, 0) + 1
                    if causa and (causa == c or causa in self.emitidas(c)):
                        self.eventos[c] = self.eventos.get(c, 0) + 1
        # Golpes dados a una instancia adyacente
        if verbo is not None and objetivo in previos and self.aqui_previo is not None and manhattan(self.aqui_previo, previos[objetivo][1]) <= 1:
            clase, n, _ = self.golpeando.get(objetivo, (previos[objetivo][0], 0, frozenset()))
            self.golpeando[objetivo] = (clase, n + 1, self.objetos_previos)
        # Lo que desaparece: derribos y recorridos de lo emitido
        for i, (_c, p) in previos.items():
            if i in agentes:
                continue
            junto = manhattan(p, aqui) <= 1 or (self.aqui_previo is not None and manhattan(p, self.aqui_previo) <= 1)
            if i in self.golpeando:
                clase, n, kit = self.golpeando.pop(i)
                if junto:
                    lista = self.derribos.setdefault(clase, [])
                    lista.append((kit, n))
                    del lista[:-MAX_DERRIBOS]
            if i in self.emitidos:
                x, origen = self.emitidos.pop(i)
                r = self.recorridos.setdefault(x, [])
                r.append(manhattan(origen, p) + 1)
                del r[:-MAX_RECORRIDOS]
        for i in [i for i in self.golpeando if i not in agentes]:
            del self.golpeando[i]
        # Apariciones: contingencia de emisión
        if previos:
            nuevos = [(i, c, p) for i, (c, p) in agentes.items() if i not in previos]
            antiguos: Dict[str, List[Pos]] = {}
            for i, (c, p) in agentes.items():
                if i in previos:
                    antiguos.setdefault(c, []).append(p)
            total = max(1, len(visibles))
            for i, y, p in nuevos:
                for x, posiciones in sorted(antiguos.items()):
                    if x == y:
                        continue
                    e = self.emision.setdefault((x, y), Emision())
                    e.n += 1
                    vecinas = {(q[0] + dx, q[1] + dy) for q in posiciones for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))}
                    e.esperado += len(vecinas & visibles) / total
                    cerca = [q for q in posiciones if manhattan(p, q) <= 1]
                    if cerca:
                        e.junto += 1
                        if i not in self.emitidos:
                            self.emitidos[i] = (x, cerca[0])
        for i in [i for i in self.emitidos if i not in agentes]:
            del self.emitidos[i]
        self.vistos = dict(agentes)
        self.aqui_previo = aqui
        self.objetos_previos = objetos

    # --- volcado y herencia ---------------------------------------------------------
    def volcado(self, peligrosa) -> Dict[str, Any]:
        clases = sorted(set(self.dano) | set(self.expuestos) | set(self.derribos) | {x for x, _ in self.emision})
        red = self.reductores()
        return {
            "dano_contacto": {c: {"n": m.n, "media": round(m.media, 2), "estimado": round(self.dano_propio(c, peligrosa(c)), 2)}
                              for c, m in sorted(self.dano.items())},
            "dano_golpe": {c: {"n": m.n, "media": round(m.media, 2)} for c, m in sorted(self.dano_golpe.items())},
            "alcance": {c: self.alcance(c, peligrosa) for c in clases if self.dano_esperado(c, peligrosa) > 0.0},
            "emisores": {f"{x}->{y}": {"n": e.n, "junto": e.junto, "esperado": round(e.esperado, 2), "dP": round(e.contingencia(), 3)}
                         for (x, y), e in sorted(self.emision.items()) if e.junto},
            "recorridos": {x: list(r) for x, r in sorted(self.recorridos.items())},
            "tasa": {c: round(self.tasa(c)[0], 3) for c in sorted(self.expuestos)},
            "expuestos": dict(sorted(self.expuestos.items())),
            "derribos": {c: [(sorted(k), g) for k, g in lista] for c, lista in sorted(self.derribos.items())},
            "reductores": {x: round(r, 3) for x, r in sorted(red.items())},
            "golpes_sin_objetos": {c: round(self.golpes(c, (), red)[0], 2) for c in sorted(self.derribos)},
        }

    def legado(self) -> Dict[str, Any]:
        """Lo aprendido con al menos ``MINIMO_LEGADO`` observaciones."""
        out: Dict[str, Any] = {}
        dano = {c: {"n": m.n, "media": round(m.media, 4)} for c, m in self.dano.items() if m.n >= MINIMO_LEGADO}
        if dano:
            out["dano"] = dano
        golpe = {c: {"n": m.n, "media": round(m.media, 4)} for c, m in self.dano_golpe.items() if m.n >= MINIMO_LEGADO}
        if golpe:
            out["dano_golpe"] = golpe
        tasa = {c: {"expuestos": n, "eventos": self.eventos.get(c, 0)} for c, n in self.expuestos.items() if n >= MINIMO_LEGADO}
        if tasa:
            out["tasa"] = tasa
        emision = [{"x": x, "y": y, "n": e.n, "junto": e.junto, "esperado": round(e.esperado, 4)}
                   for (x, y), e in self.emision.items() if e.n >= MINIMO_LEGADO]
        if emision:
            out["emision"] = emision
        recorridos = {x: list(r) for x, r in self.recorridos.items() if len(r) >= MINIMO_LEGADO}
        if recorridos:
            out["recorridos"] = recorridos
        derribos = {c: [[sorted(k), g] for k, g in lista] for c, lista in self.derribos.items() if len(lista) >= MINIMO_LEGADO}
        if derribos:
            out["derribos"] = derribos
        return out

    def heredar(self, legado: Dict[str, Any]) -> int:
        """Con la mitad de la evidencia, como el resto de lo heredado."""
        n = 0
        for c, d in legado.get("dano", {}).items():
            self.dano[str(c)] = Media(max(1, int(d["n"]) // 2), float(d["media"]))
            n += 1
        for c, d in legado.get("dano_golpe", {}).items():
            self.dano_golpe[str(c)] = Media(max(1, int(d["n"]) // 2), float(d["media"]))
            n += 1
        for c, d in legado.get("tasa", {}).items():
            self.expuestos[str(c)] = max(1, int(d["expuestos"]) // 2)
            self.eventos[str(c)] = int(d["eventos"]) // 2
            n += 1
        for d in legado.get("emision", []):
            self.emision[(str(d["x"]), str(d["y"]))] = Emision(max(1, int(d["n"]) // 2), int(d["junto"]) // 2, float(d["esperado"]) / 2)
            n += 1
        for x, r in legado.get("recorridos", {}).items():
            self.recorridos[str(x)] = [int(v) for v in r][-MAX_RECORRIDOS:]
            n += 1
        for c, lista in legado.get("derribos", {}).items():
            self.derribos[str(c)] = [(frozenset(str(o) for o in k), int(g)) for k, g in lista][-MAX_DERRIBOS:]
            n += 1
        return n


def estimar(entidades: List[Any], aqui: Pos, peligros: Peligros, salud: float, peligrosa) -> None:
    """Escribe el rasgo ``peligro`` de cada entidad con posición (paso 6a): las cosas, por su daño y alcance aprendidos a su
    distancia; los lugares, por lo peligroso percibido a la distancia de cada lugar."""
    fuentes: List[Tuple[Pos, List[Tuple[float, int]]]] = []
    lugares = []
    cache: Dict[str, List[Tuple[float, int]]] = {}
    for e in entidades:
        pos = e.datos.get("pos")
        if not isinstance(pos, (list, tuple)) or len(pos) != 2:
            continue
        p = (int(pos[0]), int(pos[1]))
        if e.rasgos.get("lugar", 0.0) >= 0.5:
            lugares.append((e, p))
            continue
        comps = cache.get(e.clase)
        if comps is None:
            comps = cache[e.clase] = peligros.componentes(e.clase, peligrosa)
        e.rasgos["peligro"] = peligros.peligro_a(comps, manhattan(aqui, p), salud)
        if comps:
            fuentes.append((p, comps))
    for e, p in lugares:
        e.rasgos["peligro"] = max((peligros.peligro_a(comps, manhattan(p, q), salud) for q, comps in fuentes), default=0.0)
