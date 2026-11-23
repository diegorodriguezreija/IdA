"""La Onda: el paquete de un latido, con su presupuesto y la guillotina.

Dimensión reactiva (el cuarteto de la experiencia):
- ``ei``: estado inicial. Es el ``ef`` del latido anterior, de solo lectura.
- ``ev``: lo que se percibe e interpreta ahora. Cobra amplitud.
- ``acc``: candidatos de Acción propuestos por los sistemas. Cobra amplitud.
- ``ef``: estado final. Registro de todo a coste cero; contiene la ``Accion``.

Atención (decisiones 15 y 18): la Onda tiene frecuencia (plazo), amplitud (cuántas piezas nuevas
caben en ``ev`` y ``acc``: cada una cuesta 1) y potencia (cuánto arousal se puede otorgar o cambiar:
cuesta |Δ arousal|, al subir y al bajar). Lo máximo que un componente cambia una pieza en un latido
es potencia / amplitud. Escribir solo en ``ef`` (``registrar``) no cuesta. El Core (sus módulos
exentos o lo que firma con ``AutorCore``) no paga amplitud ni potencia y tampoco está sujeto a la
fuerza máxima por pieza: sus piezas (sensores, sorpresa, sueño forzado) llevan el arousal que dicta
el cuerpo, no lo que la atención permite cambiar en un latido. Aceptado por el autor en la revisión
de C1 (decisión 5).

Agotar amplitud o potencia no corta el latido: sin amplitud, la pieza nueva se rechaza; sin potencia
suficiente, el cambio de arousal se recorta a lo que queda (a cero si no queda nada); lo demás sigue.
Los recursos son un único fondo que los sistemas gastan en orden (S1, S2, S3): S1 usa lo que
necesite y los demás, lo que sobre. Cada rechazo o recorte se cuenta por sistema en ``consumo``.

La guillotina es cooperativa y solo mira el plazo: cada operación pasa por ``control_vital``, que
mira el reloj. Si se supera, salta ``LatidoAgotado``; el latido corta los componentes que faltan y el
Tribunal decide con lo que ya haya en ``acc``.

Plazo lógico (opcional, para evaluaciones reproducibles): con ``ops_por_ms`` el plazo deja de medirse en reloj de
pared y se mide en operaciones. Una operación es una llamada a ``control_vital`` fuera del Core exento:
la entrada a cada sistema, el turno de cada componente y cada pieza que se cobra. Es la unidad natural
porque son exactamente los puntos donde la guillotina cooperativa puede cortar. El plazo del latido
pasa a ser ``frecuencia_ms × ops_por_ms`` operaciones, así que la regulación lo sigue acortando con
peligro. Con plazo lógico, la misma semilla da la misma vida aunque la máquina esté cargada. Por defecto
(``None``) todo sigue igual: plazo de reloj.

``fases`` apunta cuándo empieza y termina cada fase del latido (reloj de pared, en ns). Es un
registro pasivo: el núcleo no llama a nadie; la observabilidad externa lo lee después.

Propiedad de las piezas (decisión 14): un componente solo emite o modifica piezas de su tipo, y
solo a través de la Onda (``percibir``, ``registrar``, ``proponer``, ``modificar``), que lo
comprueba y deja constancia en el registro de la pieza. El Core escribe con ``AutorCore`` (o desde
un módulo exento) y no paga atención. Sin excepciones desde C3.5 (``EXCEPCIONES_TRANSITORIAS`` vacío).
"""

import time
from contextlib import contextmanager
from types import MappingProxyType
from typing import Any, Callable, Dict, Iterator, List, Optional, Protocol, Tuple

from ida.core.pieza import MAX_REGISTRO, Pieza, acotar

Canales = Dict[str, Dict[str, Pieza]]

# Excepciones transitorias a la propiedad por tipo. Las dos del bloque B (cualquier componente
# proponía Accion; un Impulso modulaba Accion) se quitaron en C3.5: solo los componentes Accion
# proponen acciones y nadie modifica piezas Accion ajenas. Si se añade alguna, cada uso queda en el
# registro de la pieza y se cuenta en ``Onda.excepciones``.
EXCEPCIONES_TRANSITORIAS: Dict[str, str] = {}


class LatidoAgotado(Exception):
    """La guillotina: se agotó el plazo o la amplitud del latido."""


class PiezaAjena(Exception):
    """Un componente intentó emitir o modificar una pieza de un tipo que no es el suyo."""


class Autor(Protocol):
    """Lo que la Onda necesita saber de quien emite o modifica: el componente."""

    nombre: str
    sistema: str
    tipo: str


class AutorCore:
    """El propio Core como autor de una pieza que escribe fuera de sus módulos (sueño forzado,
    sorpresa). Queda en el registro; no paga atención ni se recorta."""

    nombre = "Organismo"
    sistema = "CORE"

    def __init__(self, tipo: str):
        self.tipo = tipo


def _exento(onda_exenta: bool, autor: Optional[Autor]) -> bool:
    return onda_exenta or (autor is not None and autor.sistema == "CORE")


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
        potencia_max: Optional[float] = None,
        estrategias: Optional[Dict[str, Pieza]] = None,
        ops_por_ms: Optional[float] = None,
        reloj: Callable[[], float] = time.perf_counter,
    ):
        self.ciclo = ciclo
        self.amplitud_max = int(amplitud_max)
        self.frecuencia_ms = float(frecuencia_ms)
        self.potencia_max = float(amplitud_max if potencia_max is None else potencia_max)
        self.amplitud_consumida = 0
        self.potencia_consumida = 0.0
        self.consumo: Dict[str, Dict[str, float]] = {}   # por sistema: gasto, rechazos y recortes
        self.amplitud_agotada = False                     # algún sistema se quedó sin amplitud
        # Estrategias activas de todos los sistemas. El Core pasa el mismo diccionario en cada latido,
        # así que se conservan entre latidos (decisión 4); solo ``activar`` y ``cerrar`` las cambian.
        self.estrategias: Dict[str, Pieza] = estrategias if estrategias is not None else {}
        self.reactiva = DimensionReactiva(ef_anterior)
        self._reloj = reloj
        self._t0 = reloj()
        self.ops_por_ms = ops_por_ms     # plazo lógico: None = reloj de pared
        self.operaciones = 0             # llamadas a ``control_vital`` fuera del Core exento
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
        """Milisegundos del latido: de reloj, o lógicos (operaciones / ``ops_por_ms``) con plazo lógico."""
        if self.ops_por_ms:
            return self.operaciones / self.ops_por_ms
        return (self._reloj() - self._t0) * 1000.0

    def ms_restantes(self) -> float:
        return max(0.0, self.frecuencia_ms - self.ms_transcurridos())

    def amplitud_restante(self) -> int:
        return max(0, self.amplitud_max - self.amplitud_consumida)

    def potencia_restante(self) -> float:
        return max(0.0, self.potencia_max - self.potencia_consumida)

    @property
    def fuerza_max(self) -> float:
        """Lo máximo que un componente puede cambiar el arousal de una pieza en este latido."""
        return self.potencia_max / self.amplitud_max if self.amplitud_max > 0 else 0.0

    def control_vital(self, coste: int = 0, donde: str = "") -> None:
        """Cobra amplitud y comprueba el plazo. Lanza ``LatidoAgotado`` si se supera algo."""
        if self.exento:
            return
        self.operaciones += 1
        if self.ms_transcurridos() > self.frecuencia_ms:
            raise LatidoAgotado(f"plazo de {self.frecuencia_ms:.0f} ms superado en {donde or '?'}")
        if coste > 0:
            if self.amplitud_consumida + coste > self.amplitud_max:
                self.amplitud_consumida = self.amplitud_max
                raise LatidoAgotado(f"amplitud {self.amplitud_max} agotada en {donde or '?'}")
            self.amplitud_consumida += coste

    def _cuenta(self, autor: Optional[Autor]) -> Dict[str, float]:
        return self.consumo.setdefault(autor.sistema if autor else "?", {
            "amplitud": 0.0, "potencia": 0.0, "rechazos_amplitud": 0.0, "recortes_potencia": 0.0})

    def _cobrar(self, autor: Optional[Autor], amplitud: int, antes: float, despues: float, donde: str) -> Optional[float]:
        """Cobra la amplitud y la potencia de llevar un arousal de ``antes`` a ``despues``.

        Devuelve el arousal resultante, recortado a la potencia que quede, o ``None`` si no queda
        amplitud para una pieza nueva. Solo el plazo lanza ``LatidoAgotado``. El Core no paga."""
        if _exento(self.exento, autor):
            return despues
        self.control_vital(0, donde=donde)
        c = self._cuenta(autor)
        if self.amplitud_consumida + amplitud > self.amplitud_max:
            c["rechazos_amplitud"] += 1
            self.amplitud_agotada = True
            return None
        restante = self.potencia_restante()
        if abs(despues - antes) > restante + 1e-9:
            c["recortes_potencia"] += 1
            despues = antes + restante if despues > antes else antes - restante
        gasto = abs(despues - antes)
        self.amplitud_consumida += amplitud
        self.potencia_consumida += gasto
        c["amplitud"] += amplitud
        c["potencia"] += gasto
        return despues

    def _limitar(self, antes: float, despues: float, autor: Optional[Autor] = None) -> float:
        """Recorta un cambio de arousal a la fuerza máxima por pieza (el Core, sin límite)."""
        if _exento(self.exento, autor):
            return despues
        f = self.fuerza_max
        return max(antes - f, min(antes + f, despues))

    # --- propiedad ---------------------------------------------------------
    def _propiedad(self, autor: Optional[Autor], pieza: Pieza, op: str, campos: Tuple[str, ...] = ()) -> Optional[str]:
        """Comprueba que ``autor`` puede emitir o modificar ``pieza``. Devuelve la excepción transitoria
        usada, si alguna. El Core (sin autor o en un módulo exento) no se comprueba."""
        if autor is None or self.exento or autor.tipo == pieza.tipo:
            return None
        raise PiezaAjena(f"{autor.sistema}.{autor.nombre} (tipo {autor.tipo}) no puede {op} una pieza {pieza.tipo} ({pieza.id})")

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

    def _emitir(self, fase: Canales, canal: str, pieza: Pieza, autor: Optional[Autor], op: str, excepcion: Optional[str]) -> bool:
        """Cobra una pieza nueva (1 de amplitud) o sustituida (0), y |Δ arousal| de potencia, con el
        cambio recortado a la fuerza máxima por pieza y a la potencia que quede. ``False`` si se rechaza."""
        existente = fase.get(canal, {}).get(pieza.id)
        antes = existente.arousal if existente is not None else 0.0
        resultado = self._cobrar(autor, 0 if existente is not None else 1, antes, self._limitar(antes, pieza.arousal, autor), canal)
        if resultado is None:
            return False
        cambios = None
        if resultado != pieza.arousal:
            cambios = {"arousal_limitado": (pieza.arousal, resultado)}
            pieza.arousal = resultado
        self._anotar(pieza, autor, op, excepcion, cambios)
        return True

    def percibir(self, canal: str, pieza: Pieza, autor: Optional[Autor] = None) -> bool:
        """Proyecta la pieza a ``ev`` (atención consciente) cobrando amplitud y potencia.
        Devuelve ``False`` si no queda amplitud y la pieza no entra."""
        excepcion = self._propiedad(autor, pieza, "percibir")
        if not self._emitir(self.reactiva.ev, canal, pieza, autor, "percibir", excepcion):
            return False
        pieza.actualizada = self.ciclo
        self.reactiva.ef.setdefault(canal, {})[pieza.id] = pieza
        self.reactiva.ev.setdefault(canal, {})[pieza.id] = pieza
        return True

    def proponer(self, canal: str, pieza: Pieza, autor: Optional[Autor] = None) -> Optional[Pieza]:
        """Deposita un candidato en ``acc``. Si ya existe uno con el mismo id, conserva el más urgente.
        Devuelve ``None`` si no queda amplitud para un candidato nuevo."""
        excepcion = self._propiedad(autor, pieza, "proponer")
        existente = self.reactiva.acc.get(canal, {}).get(pieza.id)
        if existente is not None and existente.arousal >= pieza.arousal:
            return existente
        if not self._emitir(self.reactiva.acc, canal, pieza, autor, "proponer", excepcion):
            return existente
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
            nuevo = self._cobrar(autor, 0, pieza.arousal, self._limitar(pieza.arousal, acotar(arousal), autor), pieza.tipo)
            if nuevo is not None and nuevo != pieza.arousal:
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

    # --- estrategias ------------------------------------------------------
    def activar(self, pieza: Pieza, autor: Optional[Autor] = None) -> Pieza:
        """Pone una estrategia entre las activas (se conserva entre latidos) y la registra en ``ef``."""
        excepcion = self._propiedad(autor, pieza, "activar")
        self._anotar(pieza, autor, "activar", excepcion)
        self.estrategias[pieza.id] = pieza
        self.reactiva.ef.setdefault(pieza.tipo, {})[pieza.id] = pieza
        return pieza

    def cerrar(self, pieza: Pieza, estado: str, autor: Optional[Autor] = None) -> Pieza:
        """Saca una estrategia de las activas con su estado final."""
        self.modificar(pieza, autor, carga={"estado": estado})
        self.estrategias.pop(pieza.id, None)
        self.reactiva.ef.setdefault(pieza.tipo, {})[pieza.id] = pieza
        return pieza

    # --- lectura -----------------------------------------------------------
    def ef(self, canal: str) -> Dict[str, Pieza]:
        """Estado final de un canal en este latido (lo registrado, con o sin atención)."""
        return self.reactiva.ef.get(canal, {})

    def ev(self, canal: str) -> Dict[str, Pieza]:
        return self.reactiva.ev.get(canal, {})

    def acc(self, canal: str) -> Dict[str, Pieza]:
        return self.reactiva.acc.get(canal, {})

    def ei(self, canal: str):
        return self.reactiva.ei.get(canal, {})
