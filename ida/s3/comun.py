"""Constantes, estructuras de datos y funciones compartidas en S3."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Hashable, List, Optional, Tuple, cast

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.mundo import Escala
from ida.nucleo.pieza import Pieza
from ida.nucleo.vocabulario import Verbo
from ida.sistemas_comun import al_alcance, exterocepcion, lugares

SABER = "saber"
INTENSIDAD_INTENCION_DEL_MUNDO = 0.5

# Constantes de escala por defecto (D15): cada mundo las puede fijar en Perfil.escala
COSTE_RECORDADO = Escala().coste_recordado     # ir adonde se recuerda algo que no se ve
COSTE_POR_PROXIMIDAD = Escala().coste_por_proximidad
COSTE_SIN_PRODUCTOR = Escala().coste_sin_productor   # reponer una unidad de algo que ninguna acción conocida da


def _yo(ctx: Contexto) -> Dict[str, Any]:
    yo = ctx.onda.ev("Propiocepcion").get("yo")
    return dict(yo.carga) if yo is not None else {}


def inventario(ctx: Contexto) -> Dict[str, float]:
    """Inventario percibido (propiocepción)."""
    return {str(k): float(v) for k, v in (_yo(ctx).get("inventario") or {}).items()}


def delante(ctx: Contexto) -> Optional[Dict[str, Any]]:
    """Lo que hay delante (``cuerpo["delante"]`` = {"id", "clase"}), si el mundo lo percibe."""
    d = (_yo(ctx).get("cuerpo") or {}).get("delante")
    return dict(d) if isinstance(d, dict) and d.get("clase") else None


def _cosas(ctx: Contexto) -> List[Pieza]:
    return [p for p in exterocepcion(ctx) if p.rasgo("lugar") < 0.5]


def _pos(p: Pieza) -> Optional[Tuple[int, int]]:
    pos = p.carga.get("datos", {}).get("pos")
    return (int(pos[0]), int(pos[1])) if isinstance(pos, (list, tuple)) and len(pos) == 2 else None


def al_alcance_clase(ctx: Contexto, clase: str) -> bool:
    return any(p.clase == clase and al_alcance(p) for p in _cosas(ctx))


def desplazamientos_a_clase(ctx: Contexto, clase: str) -> List[Hashable]:
    """Posiciones relativas (``Contexto.espacio.relacion``) a cada instancia visible de ``clase``. Con posiciones las da
    el cuerpo; sin ellas, lo que está al alcance cuenta como ``espacio.junto`` y lo demás no se sabe (se omite)."""
    espacio = ctx.espacio
    aqui = espacio.posicion(ctx.ubicacion())
    salida: List[Hashable] = []
    for p in _cosas(ctx):
        if p.clase != clase:
            continue
        pos = _pos(p)
        rel = espacio.relacion(aqui, pos) if aqui is not None and pos is not None else None
        if rel is not None:
            salida.append(rel)
        elif al_alcance(p):
            salida.append(espacio.junto)
    return salida


@dataclass
class Paso:
    """La primera acción ejecutable de una cadena de requisitos, con su coste estimado."""

    verbo: Verbo
    objetivo: str
    clase: str
    coste: float
    confianza: float
    motivo: List[str]
    datos: Dict[str, Any] = field(default_factory=dict)
    destino: str = ""                  # adónde lleva un MOVER (instancia o lugar recordado)
    distancia: Optional[int] = None    # distancia a ese destino al proponerlo, si se sabe


def ir_por_el_mapa(ctx: Contexto, clase: str, confianza: float = 0.5, excluir: frozenset = frozenset()) -> Optional[Paso]:
    """Un paso hacia el sitio recordado de ``clase`` más cercano por el mapa del cuerpo registrado (D16). None sin
    cuerpo o si este no ofrece búsqueda en mapa."""
    cuerpo = getattr(ctx, "cuerpo", None)
    if cuerpo is None:
        return None
    ruta = cuerpo.ir_por_el_mapa(ctx, clase, confianza, excluir)
    if ruta is None:
        return None
    primero, d, destino = ruta
    puerta = next((lugar for lugar in lugares(ctx) if _pos(lugar) == primero and lugar.rasgo("peligro") < 0.5), None)
    if puerta is None:
        return None
    return Paso(Verbo.MOVER, puerta.id, puerta.clase, float(d), confianza, [f"volver a {clase} (mapa, {d} pasos)"],
                destino=destino, distancia=d)


def acercarse_a_clase(ctx: Contexto, clase: str, confianza: float = 0.5, excluir: frozenset = frozenset()) -> Optional[Paso]:
    """Un paso hacia la instancia visible más cercana de ``clase`` o, si no se ve, hacia donde se recuerda
    (``memoria.donde_esta`` y ``memoria.ruta``). General: con posiciones (``datos["pos"]`` y las distancias del
    cuerpo, ``Contexto.espacio``) elige el lugar vecino que más acorta la distancia; sin ellas, solo la ruta
    topológica de la memoria. ``excluir``: destinos
    aparcados (instancias o lugares) que no se eligen."""
    visibles = [p for p in _cosas(ctx) if p.clase == clase and p.id not in excluir]
    sitios = [lugar for lugar in lugares(ctx) if lugar.rasgo("peligro") < 0.5]
    if visibles:
        objetivo = max(visibles, key=lambda p: p.rasgo("proximidad"))
        destino = _pos(objetivo)
        espacio = ctx.espacio
        aqui = espacio.posicion(ctx.ubicacion())
        if destino is not None and aqui is not None:
            dist = cast(Callable[[Any, Any], int], espacio.distancia)
            con_pos = [(lugar, _pos(lugar)) for lugar in sitios]
            candidatos = [(lp, lugar) for lugar, lp in con_pos if lp is not None]
            if candidatos:
                lp, lugar = min(candidatos, key=lambda c: dist(c[0], destino))
                if dist(lp, destino) < dist(aqui, destino):
                    coste = ctx.perfil.escala.coste_por_proximidad * (1.0 - objetivo.rasgo("proximidad"))
                    return Paso(Verbo.MOVER, lugar.id, lugar.clase, coste, confianza, [f"ir a {clase}"],
                                destino=objetivo.id, distancia=dist(aqui, destino))
    ubicacion = ctx.ubicacion()
    destino_nodo = ctx.memoria.donde_esta(clase) if ctx.con_experiencia else None
    if ubicacion and destino_nodo and destino_nodo != ubicacion and destino_nodo not in excluir:
        salto = ctx.memoria.ruta(ubicacion, destino_nodo)
        puerta = next((lugar for lugar in sitios if lugar.id == salto), None)
        if puerta is not None:
            camino = ctx.memoria.camino(ubicacion, destino_nodo)
            return Paso(Verbo.MOVER, puerta.id, puerta.clase, ctx.perfil.escala.coste_recordado, confianza, [f"volver a {clase} (recordado)"],
                        destino=destino_nodo, distancia=len(camino) - 1 if camino else None)
    return None


def _cantidad(r: Any, objeto: str) -> float:
    """Unidades de ``objeto`` que gasta o pide la acción: lo que pide (``None``: 1) o lo que su efecto aprendido resta."""
    n = r.requiere_inventario.get(objeto)
    return float(max(n if n is not None else 1, -r.efecto.get(objeto, 0)))


def _conclusion(ctx: Contexto, tipo: str) -> Optional[Tuple[Pieza, Pieza]]:
    """La conclusión de ``Logica`` de ese tipo (EVITAR, COMER, COGER) y su objeto, si están a la vista."""
    c = ctx.onda.ev("Logica").get("conclusion")
    if c is None or c.carga["conclusion"] != tipo:
        return None
    objetivo = ctx.onda.ev("Objeto").get(c.carga["objetivo"])
    return (c, objetivo) if objetivo is not None else None
