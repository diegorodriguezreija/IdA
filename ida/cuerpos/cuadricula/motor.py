"""Motor del cuerpo cuadrícula (D9): capa motora, una biblioteca (no un Componente).

Traduce la intención decidida a las primitivas del mundo leyendo piezas:
- posición y orientación propias, de la ``Propiocepcion`` «yo» (``ubicacion`` y ``cuerpo["orientacion"]``);
- posición del objetivo, en este orden: las coordenadas de su id (``<clase>_<x>_<y>``); la pieza ``Exterocepcion`` con
  ese id (``datos["pos"]``); ``cuerpo["vista"][id]["pos"]`` de la Propiocepcion (B5: transitorio, mientras el mundo corte
  lo que entrega). Si no está en ninguno, no hay primitivas.

MOVER a una vecina → [mover hacia ella]; COMER, ATACAR o COGER a una vecina → [girar hacia ella si no la mira] + [do]
(girar contra lo que ocupa la casilla no mueve); USAR → [receta] si está disponible; DORMIR → [sleep]; el resto →
[noop]. Sin precondición (no es vecina, receta no disponible) → [] y el mundo no se toca.

Sinergias: como mucho ``max_sinergia`` primitivas por Actuación (parámetro del cuerpo); lo que no cabe se deja para
otra Actuación.

El éxito se juzga comparando lo pretendido con lo medido en bruto (``Efecto.medidas``): sin primitivas, fracaso; COMER
solo es éxito si sube la comida o la bebida (un golpe que aún no abate a la presa es un intento en curso); COGER, si algo
nuevo entra en el inventario (de las claves que el mundo mide como ``objetos``); el resto, éxito. Que alimente se mide con
``delta["alimentacion"]`` (constante del Soma).
"""

from typing import Any, Dict, List, Optional

from ida.core.arquitectura import Contexto
from ida.core.memoria import Pos, pos_de
from ida.core.mundo import Efecto, Motor
from ida.core.pieza import Pieza
from ida.core.vocabulario import Verbo

MOVIMIENTOS: Dict[Pos, str] = {(-1, 0): "move_left", (1, 0): "move_right", (0, -1): "move_up", (0, 1): "move_down"}
INTERACTUAR = "do"
DORMIR = "sleep"
NADA = "noop"


def _par(v: Any) -> Optional[Pos]:
    return (int(v[0]), int(v[1])) if isinstance(v, (list, tuple)) and len(v) == 2 else None


class MotorCuadricula(Motor):
    def __init__(self, max_sinergia: int = 2) -> None:
        super().__init__()
        self.max_sinergia = int(max_sinergia)

    @staticmethod
    def posicion(objetivo: str, ctx: Contexto) -> Optional[Pos]:
        """Posición del objetivo: coordenadas del id, pieza Exterocepcion o ``vista`` de la Propiocepcion «yo»."""
        p = pos_de(objetivo)
        if p is not None:
            return p
        e = ctx.onda.ev("Exterocepcion").get(objetivo)
        if e is not None:
            p = _par((e.carga.get("datos") or {}).get("pos"))
            if p is not None:
                return p
        yo = ctx.onda.ev("Propiocepcion").get("yo")
        vista = ((yo.carga.get("cuerpo") or {}).get("vista") or {}) if yo is not None else {}
        visto = vista.get(objetivo) if isinstance(vista, dict) else None
        return _par(visto.get("pos")) if isinstance(visto, dict) else None

    def primitivas(self, intencion: Pieza, ctx: Contexto, disponibles: List[str]) -> List[str]:
        verbo, objetivo = intencion.carga["verbo"], str(intencion.carga.get("objetivo", ""))
        if verbo in (Verbo.MOVER, Verbo.COMER, Verbo.ATACAR, Verbo.COGER):
            yo = ctx.onda.ev("Propiocepcion").get("yo")
            aqui = pos_de(yo.carga.get("ubicacion")) if yo is not None else None
            destino = self.posicion(objetivo, ctx)
            if aqui is None or destino is None or abs(destino[0] - aqui[0]) + abs(destino[1] - aqui[1]) != 1:
                return []
            direccion = (destino[0] - aqui[0], destino[1] - aqui[1])
            if verbo == Verbo.MOVER:
                secuencia = [MOVIMIENTOS[direccion]]
            else:
                cara = _par(((yo.carga.get("cuerpo") or {}) if yo is not None else {}).get("orientacion"))
                secuencia = ([] if cara == direccion else [MOVIMIENTOS[direccion]]) + [INTERACTUAR]
        elif verbo == Verbo.USAR:
            receta = (intencion.carga.get("datos") or {}).get("receta") or objetivo
            secuencia = [receta] if receta in disponibles else []
        elif verbo == Verbo.DORMIR:
            secuencia = [DORMIR]
        else:
            secuencia = [NADA]
        return secuencia[: self.max_sinergia]

    def juzgar(self, intencion: Pieza, primitivas: List[str], efecto: Efecto) -> bool:
        if not primitivas:
            return False
        verbo = intencion.carga["verbo"]
        if verbo == Verbo.COMER and not efecto.delta.get("alimentacion", 0.0) > 0.0:
            return False
        antes = efecto.medidas.get("inventario_antes") or {}
        despues = efecto.medidas.get("inventario_despues") or {}
        if verbo == Verbo.COGER and not any(despues.get(k, 0) > antes.get(k, 0) for k in efecto.medidas.get("objetos") or ()):
            return False
        return True
