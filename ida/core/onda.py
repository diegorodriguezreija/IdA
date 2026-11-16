"""La Onda: el paquete de un latido, con su presupuesto y la guillotina.

Dimensión reactiva (el cuarteto de la experiencia):
- ``ei``: estado inicial. Es el ``ef`` del latido anterior, de solo lectura.
- ``ev``: lo que se percibe e interpreta ahora. Cobra amplitud.
- ``acc``: candidatos de Acción propuestos por los sistemas. Cobra amplitud.
- ``ef``: estado final. Registro de todo a coste cero; contiene la ``Accion``.

La guillotina es cooperativa: cada emisión pasa por ``control_vital``, que cobra amplitud y
mira el reloj. Si se agota cualquiera de los dos, salta ``LatidoAgotado``; el latido corta los
componentes que faltan y el Tribunal decide con lo que ya haya en ``acc``.

``fases`` apunta cuándo empieza y termina cada fase del latido (reloj de pared, en ns). Es un
registro pasivo: el núcleo no llama a nadie; la observabilidad externa lo lee después.

Propiedad de las piezas (decisión 14): un componente solo emite o modifica piezas de su tipo, y
solo a través de la Onda (``percibir``, ``registrar``, ``proponer``, ``modificar``), que lo
comprueba y deja constancia en el registro de la pieza. El Core queda exento (``autor=None`` o
módulo exento). Excepciones transitorias hasta el bloque C, en ``EXCEPCIONES_TRANSITORIAS``.
"""

import time
from contextlib import contextmanager
from types import MappingProxyType
from typing import Any, Callable, Dict, Iterator, List, Optional, Protocol, Tuple

from ida.core.pieza import MAX_REGISTRO, Pieza, acotar

Canales = Dict[str, Dict[str, Pieza]]

# Excepciones transitorias a la propiedad por tipo (hasta el bloque C). Cada uso queda en el
# registro de la pieza y se cuenta en ``Onda.excepciones``.
EXCEPCIONES_TRANSITORIAS = {
    "proponer_accion": "cualquier componente puede proponer piezas Accion",
    "impulso_modula_accion": "un componente Impulso puede modular arousal y confianza de piezas Accion (y anotar sus entradas)",
}


class LatidoAgotado(Exception):
    """La guillotina: se agotó el plazo o la amplitud del latido."""


class PiezaAjena(Exception):
    """Un componente intentó emitir o modificar una pieza de un tipo que no es el suyo."""


class Autor(Protocol):
    """Lo que la Onda necesita saber de quien emite o modifica: el componente."""

    nombre: str
    sistema: str
    tipo: str


class DimensionReactiva:
    def __init__(self, ef_anterior: Optional[Canales] = None):
        previo = ef_anterior or {}
        self.ei = MappingProxyType({c: MappingProxyType(dict(p)) for c, p in previo.items()})
        self.ev: Canales = {}
        self.acc: Canales = {}
        self.ef: Canales = {}

    def fase(self, nombre: str):
        return {"ei": self.ei, "ev": self.ev, "acc": self.acc, "ef": self.ef}[nombre]

    def hay(self, canal: str) -> bool:
        """¿Hay alguna pieza de ese canal en cualquier fase? (activa a los componentes)."""
        return any(canal in f and len(f[canal]) > 0 for f in (self.ei, self.ev, self.acc))


class Onda:
    def __init__(
        self,
        ciclo: int,
        amplitud_max: int,
        frecuencia_ms: float,
        ef_anterior: Optional[Canales] = None,
        reloj: Callable[[], float] = time.perf_counter,
    ):
        self.ciclo = ciclo
        self.amplitud_max = int(amplitud_max)
        self.frecuencia_ms = float(frecuencia_ms)
        self.amplitud_consumida = 0
        self.reactiva = DimensionReactiva(ef_anterior)
        self._reloj = reloj
        self._t0 = reloj()
        self.exento = False            # True mientras corren los módulos del Core (sin peaje)
        self.guillotina = False
        self.motivo_guillotina = ""
        self.tiempos_ms: Dict[str, float] = {}   # tiempo de cada componente en este latido
        self.notas: Dict[str, object] = {}       # resúmenes para consola y telemetría
        self.fases: List[Tuple[str, int, int]] = []   # (fase, inicio_ns, fin_ns) para la observabilidad
        self.excepciones: Dict[str, int] = {}         # usos de EXCEPCIONES_TRANSITORIAS en este latido

    @contextmanager
    def fase(self, nombre: str) -> Iterator[None]:
        """Apunta la duración de una fase del latido, también si la corta la guillotina."""
        inicio = time.time_ns()
        try:
            yield
        finally:
            self.fases.append((nombre, inicio, time.time_ns()))

    # --- presupuesto -------------------------------------------------------
    def ms_transcurridos(self) -> float:
        return (self._reloj() - self._t0) * 1000.0

    def ms_restantes(self) -> float:
        return max(0.0, self.frecuencia_ms - self.ms_transcurridos())

    def amplitud_restante(self) -> int:
        return max(0, self.amplitud_max - self.amplitud_consumida)

    def control_vital(self, coste: int = 0, donde: str = "") -> None:
        """Cobra amplitud y comprueba el plazo. Lanza ``LatidoAgotado`` si se supera algo."""
        if self.exento:
            return
        if self.ms_transcurridos() > self.frecuencia_ms:
            raise LatidoAgotado(f"plazo de {self.frecuencia_ms:.0f} ms superado en {donde or '?'}")
        if coste > 0:
            if self.amplitud_consumida + coste > self.amplitud_max:
                self.amplitud_consumida = self.amplitud_max
                raise LatidoAgotado(f"amplitud {self.amplitud_max} agotada en {donde or '?'}")
            self.amplitud_consumida += coste

    # --- emisiones ---------------------------------------------------------
    # --- propiedad ---------------------------------------------------------
    def _propiedad(self, autor: Optional[Autor], pieza: Pieza, op: str, campos: Tuple[str, ...] = ()) -> Optional[str]:
        """Comprueba que ``autor`` puede emitir o modificar ``pieza``. Devuelve la excepción transitoria
        usada, si alguna. El Core (sin autor o en un módulo exento) no se comprueba."""
        if autor is None or self.exento or autor.tipo == pieza.tipo:
            return None
        if pieza.tipo == "Accion" and op == "proponer":
            excepcion = "proponer_accion"
        elif pieza.tipo == "Accion" and op == "modificar" and autor.tipo == "Impulso" and set(campos) <= {"arousal", "confianza", "entrada"}:
            excepcion = "impulso_modula_accion"
        else:
            raise PiezaAjena(f"{autor.sistema}.{autor.nombre} (tipo {autor.tipo}) no puede {op} una pieza {pieza.tipo} ({pieza.id})")
        self.excepciones[excepcion] = self.excepciones.get(excepcion, 0) + 1
        return excepcion

    def _anotar(self, pieza: Pieza, autor: Optional[Autor], op: str, excepcion: Optional[str] = None,
                cambios: Optional[Dict[str, Any]] = None) -> None:
        quien = f"{autor.sistema}.{autor.nombre}" if autor else "CORE"
        if not pieza.origen:
            pieza.origen = quien
        entrada: Dict[str, Any] = {"latido": self.ciclo, "op": op, "autor": quien}
        if excepcion:
            entrada["excepcion"] = excepcion
        if cambios:
            entrada["cambios"] = cambios
        pieza.registro.append(entrada)
        if len(pieza.registro) > MAX_REGISTRO:
            del pieza.registro[: len(pieza.registro) - MAX_REGISTRO]

    # --- emisiones ---------------------------------------------------------
    def registrar(self, canal: str, pieza: Pieza, autor: Optional[Autor] = None) -> None:
        """Escribe en ``ef`` a coste cero."""
        excepcion = self._propiedad(autor, pieza, "registrar")
        self._anotar(pieza, autor, "registrar", excepcion)
        self.reactiva.ef.setdefault(canal, {})[pieza.id] = pieza

    def percibir(self, canal: str, pieza: Pieza, coste: int = 1, autor: Optional[Autor] = None) -> None:
        """Proyecta la pieza a ``ev`` (atención consciente) cobrando amplitud."""
        excepcion = self._propiedad(autor, pieza, "percibir")
        self.control_vital(coste, donde=canal)
        pieza.actualizada = self.ciclo
        self._anotar(pieza, autor, "percibir", excepcion)
        self.reactiva.ef.setdefault(canal, {})[pieza.id] = pieza
        self.reactiva.ev.setdefault(canal, {})[pieza.id] = pieza

    def proponer(self, canal: str, pieza: Pieza, coste: int = 1, autor: Optional[Autor] = None) -> Pieza:
        """Deposita un candidato en ``acc``. Si ya existe uno con el mismo id, conserva el más urgente."""
        excepcion = self._propiedad(autor, pieza, "proponer")
        existente = self.reactiva.acc.get(canal, {}).get(pieza.id)
        if existente is not None and existente.arousal >= pieza.arousal:
            return existente
        self.control_vital(coste, donde=canal)
        self._anotar(pieza, autor, "proponer", excepcion)
        self.reactiva.ef.setdefault(canal, {})[pieza.id] = pieza
        self.reactiva.acc.setdefault(canal, {})[pieza.id] = pieza
        return pieza

    def modificar(self, pieza: Pieza, autor: Optional[Autor] = None, *, arousal: Optional[float] = None,
                  confianza: Optional[float] = None, carga: Optional[Dict[str, Any]] = None, entrada: Optional[str] = None) -> Pieza:
        """Cambia una pieza ya emitida: arousal y confianza (acotados), claves de la carga y una
        anotación en ``entradas``. Solo su dueño, salvo las excepciones transitorias."""
        campos = tuple(k for k, v in (("arousal", arousal), ("confianza", confianza), ("carga", carga), ("entrada", entrada)) if v is not None)
        excepcion = self._propiedad(autor, pieza, "modificar", campos)
        cambios: Dict[str, Any] = {}
        if arousal is not None:
            nuevo = acotar(arousal)
            cambios["arousal"] = (pieza.arousal, nuevo)
            pieza.arousal = nuevo
        if confianza is not None:
            nueva = acotar(confianza)
            cambios["confianza"] = (pieza.confianza, nueva)
            pieza.confianza = nueva
        if carga is not None:
            cambios["carga"] = sorted(carga)
            pieza.carga.update(carga)
        if entrada is not None:
            cambios["entrada"] = entrada
            pieza.entradas.append(entrada)
        pieza.actualizada = self.ciclo
        self._anotar(pieza, autor, "modificar", excepcion, cambios)
        return pieza

    # --- lectura -----------------------------------------------------------
    def ev(self, canal: str) -> Dict[str, Pieza]:
        return self.reactiva.ev.get(canal, {})

    def acc(self, canal: str) -> Dict[str, Pieza]:
        return self.reactiva.acc.get(canal, {})

    def ei(self, canal: str):
        return self.reactiva.ei.get(canal, {})
