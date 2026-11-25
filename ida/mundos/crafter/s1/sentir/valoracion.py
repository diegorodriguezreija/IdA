"""ValoracionCrafter (D4, D5): preatención de Crafter en S1 · Sentir.

El adaptador de Crafter entrega la percepción en bruto (``proximidad``, ``agente`` y ``lugar``, más ``datos["madura"]``
de las plantas, ``cuerpo["casillas"]`` y ``cuerpo["vista"]``). La interpretación es del organismo: este Componente
escribe, en los rasgos de cada pieza ``Exterocepcion``, ``nutritivo`` y ``recurso`` (cosas) y ``nutritivo`` y ``novedad``
(lugares), con las fórmulas que antes tenía ``MundoCrafter.observar``:

- cosa: ``nutritivo`` = ``valor_nutritivo`` si el manual declara su clase NUTRITIVO y no se ve sin madurar
  (``datos["madura"]`` False); ``recurso`` = ``valor_recurso`` si la declara UTIL;
- lugar: ``nutritivo`` = el máximo, entre lo nutritivo a la vista (``casillas`` y ``vista``) del que el lugar acerca,
  de ``valor_nutritivo · (1 − distancia / alcance_gradiente)``; ``novedad`` = 1 si nunca se ha llegado a ese lugar
  moviéndose, o ``min(1, (cuenta − visita) / olvido_novedad)``.

Lo que sabe del mundo lo recibe en el constructor (conocimiento declarado del manual: clases nutritivas y útiles; y las
escalas). La memoria de visitas es suya: tras un MOVER que ejecutó primitivas, apunta la posición propia actual con la
cuenta de primitivas ejecutadas del Motor del cuerpo (copia eferente, ``Motor.ejecutadas``), que coincide con los pasos
del entorno. Coste lineal en lo percibido y en lo que hay a la vista.
"""

from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Tuple

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.mundo import Cuerpo
from ida.nucleo.vocabulario import Verbo
from ida.cuerpos.cuadricula.geometria import Pos, pos_de

ORDEN_COSA = ("proximidad", "nutritivo", "recurso", "agente")
ORDEN_LUGAR = ("lugar", "proximidad", "nutritivo", "novedad")


def _par(v: Any) -> Optional[Pos]:
    return (int(v[0]), int(v[1])) if isinstance(v, (list, tuple)) and len(v) == 2 else None


def _dist(a: Pos, b: Pos) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _ordenados(rasgos: Dict[str, float], nuevos: Dict[str, float], orden: Tuple[str, ...]) -> Dict[str, float]:
    """Los rasgos con los nuevos, en ``orden`` y después los demás (p. ej. ``peligro``) en el orden en que estaban."""
    salida = {k: nuevos[k] if k in nuevos else rasgos[k] for k in orden if k in nuevos or k in rasgos}
    salida.update({k: v for k, v in rasgos.items() if k not in salida})
    return salida


class ValoracionCrafter(Componente):
    tipo = "Exterocepcion"
    preatentivo = True

    def __init__(self, nutritivas: Iterable[str], utiles: Iterable[str], cuerpo: Optional[Cuerpo] = None,
                 valor_nutritivo: float = 0.6, valor_recurso: float = 0.6, alcance_gradiente: float = 16.0,
                 olvido_novedad: float = 50.0):
        super().__init__()
        self.nutritivas: FrozenSet[str] = frozenset(nutritivas)
        self.utiles: FrozenSet[str] = frozenset(utiles)
        self.cuerpo = cuerpo
        self.valor_nutritivo = float(valor_nutritivo)
        self.valor_recurso = float(valor_recurso)
        self.alcance_gradiente = alcance_gradiente
        self.olvido_novedad = float(olvido_novedad)
        self.visitas: Dict[Pos, int] = {}

    def conocimiento_declarado(self) -> Dict[str, List[str]]:
        """Lo que el mundo le declara (su manual), para ``herramientas/conocimiento_mundo.py``."""
        return {"NUTRITIVO": sorted(self.nutritivas), "UTIL": sorted(self.utiles)}

    def cuenta(self) -> int:
        """Primitivas ejecutadas en esta vida (copia eferente del Motor del cuerpo)."""
        motor = self.cuerpo.motor() if self.cuerpo is not None else None
        return sum(motor.ejecutadas.values()) if motor is not None else 0

    def _nutritivo(self, clase: str, madura: Any) -> float:
        return self.valor_nutritivo if clase in self.nutritivas and madura is not False else 0.0

    def _deseables(self, cuerpo: Dict[str, Any]) -> List[Tuple[Pos, float]]:
        """Lo nutritivo a la vista: materiales (``casillas``) y objetos (``vista``)."""
        salida: List[Tuple[Pos, float]] = []
        casillas = cuerpo.get("casillas")
        if isinstance(casillas, dict):
            for k, clase in casillas.items():
                q = _par(k)
                valor = self._nutritivo(str(clase), None)
                if q is not None and valor > 0.1:
                    salida.append((q, valor))
        vista = cuerpo.get("vista")
        if isinstance(vista, dict):
            for v in vista.values():
                if not isinstance(v, dict):
                    continue
                q = _par(v.get("pos"))
                valor = self._nutritivo(str(v.get("clase", "")), v.get("madura"))
                if q is not None and valor > 0.1:
                    salida.append((q, valor))
        return salida

    def reactiva(self, ctx: Contexto) -> None:
        yo = ctx.onda.ev("Propiocepcion").get("yo")
        aqui = pos_de(yo.carga.get("ubicacion")) if yo is not None else None
        t = self.cuenta()
        previa = ctx.onda.ei("Accion").get("Accion")
        if previa is not None and aqui is not None and previa.carga.get("verbo") == Verbo.MOVER and previa.carga.get("primitivas"):
            self.visitas[aqui] = t
        cuerpo = dict((yo.carga.get("cuerpo") or {}) if yo is not None else {})
        deseables: Optional[List[Tuple[Pos, float]]] = None
        for p in list(ctx.onda.ev("Exterocepcion").values()):
            rasgos = p.carga.get("rasgos", {})
            datos = p.carga.get("datos", {})
            if rasgos.get("lugar", 0.0) >= 0.5:
                c = _par(datos.get("pos"))
                if c is None or aqui is None:
                    continue
                if deseables is None:
                    deseables = self._deseables(cuerpo)
                nutritivo = 0.0
                for dpos, valor in deseables:
                    if _dist(c, dpos) < _dist(aqui, dpos):
                        nutritivo = max(nutritivo, valor * (1.0 - _dist(c, dpos) / self.alcance_gradiente))
                ultima = self.visitas.get(c)
                novedad = 1.0 if ultima is None else min(1.0, (t - ultima) / self.olvido_novedad)
                nuevos, orden = {"nutritivo": nutritivo, "novedad": novedad}, ORDEN_LUGAR
            else:
                clase = str(p.carga.get("clase", ""))
                nuevos = {"nutritivo": self._nutritivo(clase, datos.get("madura")),
                          "recurso": self.valor_recurso if clase in self.utiles else 0.0}
                orden = ORDEN_COSA
            self.modificar(ctx, p, carga={"rasgos": _ordenados(rasgos, nuevos, orden)})
