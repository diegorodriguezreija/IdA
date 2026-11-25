"""Elementos comunes y funciones auxiliares para los componentes y estrategias de S1."""

from typing import Any, Callable, Dict, FrozenSet, List, Optional, Tuple, cast

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.pieza import Pieza, acotar
from ida.nucleo.vocabulario import EstadoSaber, Relacion, Verbo
from ida.s1.sentir.amenaza import Peligros
from ida.s3.interpretar.requisito import Requisitos
from ida.sistemas_comun import (
    al_alcance,
    alarma,
    cautela,
    lugares,
    mejor,
    objetos,
)

SEGURIDAD = "seguridad"
COBIJO = "cobijo"
TIPO_RECINTO = "Recinto"
SATISFACE_MIN = 0.3
VENTANA_TENDENCIA = 50


def recinto(ctx: Contexto) -> Optional[Pieza]:
    """Pieza de afordancia de protección producida por el componente de interpretar del mundo."""
    return ctx.onda.ef(TIPO_RECINTO).get("recinto")


def _salida(ctx: Contexto, peligro: float) -> Optional[Pieza]:
    """El lugar a la vista menos peligroso, si lo es menos que el peligro actual."""
    salida = mejor(lugares(ctx), lambda lugar: -lugar.rasgo("peligro"))
    return salida if salida is not None and salida.rasgo("peligro") < peligro else None


def _amenaza(ctx: Contexto) -> Optional[Pieza]:
    a = alarma(ctx)
    return ctx.onda.ev("Objeto").get(a.carga["amenaza"]) if a is not None and a.carga["amenaza"] else None


def _peligro(ctx: Contexto) -> float:
    a = alarma(ctx)
    return float(a.carga["peligro"]) if a is not None else 0.0


def _yo(ctx: Contexto) -> Optional[Any]:
    """Posición propia, que el cuerpo da de la ubicación (``Contexto.espacio``, D10), o None."""
    yo = ctx.onda.ev("Propiocepcion").get("yo")
    return ctx.espacio.posicion(yo.carga.get("ubicacion", "")) if yo is not None else None


def _objetos_llevados(ctx: Contexto) -> FrozenSet[str]:
    """Lo que se lleva (inventario percibido), solo las claves que son objetos."""
    yo = ctx.onda.ev("Propiocepcion").get("yo")
    inv = dict(yo.carga.get("inventario", {})) if yo is not None else {}
    if ctx.memoria.tiene_seccion("requisitos"):
        req = cast(Requisitos, ctx.memoria.seccion("requisitos"))
        return frozenset(k for k, v in req.objetos(inv).items() if v >= 1.0)
    return frozenset(k for k, v in inv.items() if v >= 1.0)


def objetos_peligrosos(ctx: Contexto) -> List[Pieza]:
    """Los Objetos con peligro que se pueden afrontar (orden estable): los de una clase cuyo derribo se ha observado o que el
    manual declara meta de ATACAR. Atacar algo que nunca se ha visto caer y que nada pide derribar no es luchar."""
    mem = ctx.memoria
    pel: Optional[Peligros] = cast(Peligros, mem.seccion("peligros")) if mem.tiene_seccion("peligros") else None
    req: Optional[Requisitos] = cast(Requisitos, mem.seccion("requisitos")) if mem.tiene_seccion("requisitos") else None
    derribos = pel.derribos if pel is not None else {}
    metas = req.metas if req is not None else {}
    return sorted((o for o in objetos(ctx) if o.rasgo("peligro") > 0.0
                   and (derribos.get(o.clase) or (Verbo.ATACAR, o.clase) in metas)), key=lambda o: o.id)


def _rechazado(ctx: Contexto, o: Pieza) -> bool:
    """Elección del objeto (decisión 1 del autor sobre C1): primero el valor de S2 (del latido anterior,
    porque S2 corre después de S1) y después las creencias de S3 (lo que sostiene, bloque D). Se rechaza lo que se valora mal
    (valencia negativa) y lo que se sabe peligroso o se sabe que no nutre. Un objeto que S2 no ha
    valorado (fuera de la atención) toma el valor de otro de su clase que sí lo esté: el sentimiento
    sale de los recuerdos de la clase."""
    valores = ctx.onda.ei("Valor")
    valor = valores.get(o.id)
    if valor is None:
        valor = next((v for v in valores.values() if v.carga.get("clase") == o.clase), None)
    if valor is not None and float(valor.carga.get("valencia", 0.0)) < 0.0:
        return True
    if o.clase in cautela(ctx)[0]:            # S3 lo desaconseja (con su criterio, p. ej. indicios de daño)
        return True
    if not ctx.con_experiencia:
        return False
    # Lo que S3 sostiene (piezas Creencia del latido anterior: S3 corre después de S1).
    creencias = ctx.onda.ei("Creencia")
    dano = creencias.get(f"{o.clase}|{Relacion.PELIGROSO.name}")
    if dano is not None and dano.carga.get("sostiene"):
        return True
    nutre = creencias.get(f"{o.clase}|{Relacion.NUTRITIVO.name}")
    return nutre is not None and nutre.carga.get("estado") == EstadoSaber.REFUTADA


Rechazo = Callable[[Contexto, Pieza], bool]
Comestible = Callable[[Pieza], bool]


def _nutritivo(o: Pieza) -> bool:
    return o.rasgo("nutritivo") >= 0.3


def _al_alcance(ctx: Contexto, rechaza: Rechazo = _rechazado, comestible: Comestible = _nutritivo) -> Tuple[List[Pieza], List[Pieza]]:
    """Comestibles al alcance, separados en aceptables y rechazados."""
    comestibles = [o for o in objetos(ctx) if comestible(o) and al_alcance(o)]
    rechazados = [o for o in comestibles if rechaza(ctx, o)]
    return [o for o in comestibles if o not in rechazados], rechazados


def _aceptables_a_la_vista(ctx: Contexto, rechaza: Rechazo = _rechazado, comestible: Comestible = _nutritivo) -> List[Pieza]:
    """Comestibles a la vista pero no al alcance que no se rechazan."""
    return [o for o in objetos(ctx) if comestible(o) and not al_alcance(o) and not rechaza(ctx, o)]


def _posicion(ctx: Contexto, pid: str) -> Optional[Tuple[float, ...]]:
    """Posición percibida de una entidad, si el mundo la da (``datos["pos"]`` de la exterocepción)."""
    e = ctx.onda.ev("Exterocepcion").get(pid)
    pos = e.carga.get("datos", {}).get("pos") if e is not None else None
    return tuple(float(x) for x in pos) if isinstance(pos, (tuple, list)) else None


def _hacia(ctx: Contexto, objetivo: Pieza) -> Optional[Pieza]:
    """El lugar a la vista (no peligroso) que más acerca a ``objetivo``, si hay posiciones percibidas."""
    meta = _posicion(ctx, objetivo.id)
    if meta is None:
        return None
    candidatos = [(lugar, _posicion(ctx, lugar.id)) for lugar in _lugares_permitidos(ctx) if lugar.rasgo("peligro") < 0.8]
    con_pos = [(lugar, pos) for lugar, pos in candidatos if pos is not None and len(pos) == len(meta)]
    if not con_pos:
        return None
    return min(con_pos, key=lambda lp: sum(abs(a - b) for a, b in zip(lp[1], meta, strict=True)))[0]


def _lugares_permitidos(ctx: Contexto) -> List[Pieza]:
    """Lugares a la vista menos los que S3 desaconseja."""
    evitar = cautela(ctx)[1]
    return [lugar for lugar in lugares(ctx) if lugar.id not in evitar]


def _destino_comida(ctx: Contexto) -> Optional[Pieza]:
    destino = mejor(_lugares_permitidos(ctx), lambda lugar: lugar.rasgo("nutritivo") - 1.5 * lugar.rasgo("peligro"))
    return destino if destino is not None and destino.rasgo("nutritivo") > 0.0 and destino.rasgo("peligro") < 0.8 else None


def intensidades(ctx: Contexto) -> Dict[str, float]:
    """Déficit de cada necesidad que declara el mundo (sin Seguridad), desde la interocepción."""
    valores = {n: float(p.carga["valor"]) for n, p in ctx.onda.ev("Interocepcion").items()}
    d: Dict[str, float] = {}
    for necesidad in ctx.perfil.necesidades:
        v = necesidad.deficit(valores)
        if v is not None:
            d[necesidad.nombre] = v
    return d


def deficits(ctx: Contexto) -> Dict[str, float]:
    """Déficit de cada necesidad que declara el mundo (desde la interocepción) y peligro (Seguridad)."""
    valores = {n: float(p.carga["valor"]) for n, p in ctx.onda.ev("Interocepcion").items()}
    d: Dict[str, float] = {}
    for necesidad in ctx.perfil.necesidades:
        v = necesidad.deficit(valores)
        if v is not None:
            d[necesidad.nombre] = v
    a = alarma(ctx)
    d["seguridad"] = float(a.carga["peligro"]) if a is not None else 0.0
    return d


def alostasis(ctx: Contexto, defs: Dict[str, float]) -> Dict[str, Tuple[float, float, float]]:
    """Intensidad anticipada, tendencia y horizonte de cada necesidad (3.2 del encargo del paso 3).

    - **Tendencia:** media móvil (``VENTANA_TENDENCIA`` latidos) del cambio del déficit por latido, desde el impulso del latido
      anterior. Seguridad (el peligro) no se anticipa.
    - **Cobijo:** T = coste en pasos del mejor sitio para protegerse (``Recinto``), incluido lo que
      cuesta conseguir lo que le falta (metas instrumentales); dentro de un recinto, 0; sin ningún sitio posible, una
      estimación alta que declara el mundo (``Perfil.escala.coste_sin_sitio``, D15). Si la luz baja y el recinto está a
      20 pasos, la intensidad sube unos 20 latidos antes.
    - **Las demás:** T = 0, no se anticipan. La versión que las anticipaba (3b, provisiones antes de encerrarse) se retiró
      por no tener efecto medido (``docs/ENCARGO_PASO3_PROTEGER.md``, «Resultado»)."""
    previos = ctx.onda.ei("Impulso")
    a = 1.0 / VENTANA_TENDENCIA
    tendencias: Dict[str, float] = {}
    for nombre, d in defs.items():
        p = previos.get(nombre)
        if nombre == SEGURIDAD or p is None or "deficit" not in p.carga:
            tendencias[nombre] = 0.0
        else:
            tendencias[nombre] = (1.0 - a) * float(p.carga.get("tendencia", 0.0)) + a * (d - float(p.carga["deficit"]))
    r = recinto(ctx)
    coste = None if r is None or r.carga["coste"] is None else max(0.0, float(r.carga["coste"]))
    horizontes: Dict[str, float] = dict.fromkeys(defs, 0.0)
    if COBIJO in defs and r is not None:
        horizontes[COBIJO] = coste if coste is not None else (0.0 if r.carga["dentro"] else float(ctx.perfil.escala.coste_sin_sitio))
    salida: Dict[str, Tuple[float, float, float]] = {}
    for nombre, d in defs.items():
        t, h = tendencias[nombre], horizontes[nombre]
        salida[nombre] = (acotar(max(d, d + t * h)) if d > 0.0 and t > 0.0 and h > 0.0 else d, t, h)
    return salida
