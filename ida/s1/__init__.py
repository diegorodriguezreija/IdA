"""S1 · Supervivencia: cuerpo, peligro, reflejos e impulsos básicos. Rápido, simple y siempre primero."""

from typing import List

from ida.nucleo.arquitectura import Modulo, Sistema
from ida.nucleo.estrategia import Catalogo, Definicion
from ida.s1.actuar import Accion, Anticipacion
from ida.s1.comun import SEGURIDAD
from ida.s1.interpretar.apetencia import Apetencia
from ida.s1.interpretar.objeto import Objeto
from ida.s1.interpretar.supervivencia import Supervivencia
from ida.s1.reaccionar.estrategia import Estrategia
from ida.s1.reaccionar.estrategias import (
    Afrontar,
    Alimentarse,
    Defenderse,
    Huir,
    Proteger,
    QuietoOHuir,
    SeguirEnMovimiento,
    Sobresalto,
)
from ida.s1.reaccionar.feedback import Feedback
from ida.s1.reaccionar.impulso import Impulso
from ida.s1.reaccionar.peticion import Peticion
from ida.s1.reaccionar.reflejo import Reflejo
from ida.s1.sentir.amenaza import Amenaza
from ida.s1.sentir.imagen import Imagen
from ida.s1.sentir.saliencia import Saliencia


def estrategias_s1() -> List[Definicion]:
    """Catálogo general de S1. ``Afrontar`` y ``Proteger`` son opcionales (D3): solo quedan si el mundo los registra.
    ``SalirDelRecinto`` la añade con su registro el mundo que la usa (D16)."""
    return [Huir(), Defenderse(), Afrontar(), Sobresalto(), QuietoOHuir(), Alimentarse(), SeguirEnMovimiento(), Proteger()]


def crear_s1() -> Sistema:
    catalogo = Catalogo(estrategias_s1())
    return Sistema("S1", "Supervivencia", [
        Modulo("Sentir", [Imagen()]),
        Modulo("Interpretar", [Objeto(), Supervivencia(), Apetencia()]),   # Recinto: lo añade el mundo que lo usa (D16)
        Modulo("Reaccionar", [Reflejo(), Impulso(), Feedback(), Estrategia(catalogo, impulso_critico=SEGURIDAD), Peticion(catalogo)]),
        Modulo("Actuar", [Accion(catalogo), Anticipacion()]),
    ], preatencion=[Amenaza(), Saliencia()])


__all__ = ["crear_s1", "estrategias_s1"]
