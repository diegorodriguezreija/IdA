"""S2 · Valor: motivación, sentimiento y relación social. Trabaja con lo que le sobra a S1."""

from typing import List

from ida.nucleo.arquitectura import Modulo, Sistema
from ida.nucleo.estrategia import Catalogo, Definicion
from ida.s2.actuar.accion import Accion
from ida.s2.actuar.anticipacion import Anticipacion
from ida.s2.interpretar.sujeto import Sujeto
from ida.s2.interpretar.valor import Valor
from ida.s2.reaccionar.estrategia import Estrategia
from ida.s2.reaccionar.estrategias import Explorar, RecordarComida, Refugiarse
from ida.s2.reaccionar.exteriorizacion import Exteriorizacion
from ida.s2.reaccionar.feedback import Feedback
from ida.s2.reaccionar.impulso import Impulso
from ida.s2.reaccionar.peticion import Peticion
from ida.s2.sentir.emocion import Emocion
from ida.s2.sentir.patron import Patron
from ida.s2.sentir.recuerdo import Recuerdo


def estrategias_s2() -> List[Definicion]:
    return [Explorar(), Refugiarse(), RecordarComida()]


def crear_s2() -> Sistema:
    catalogo = Catalogo(estrategias_s2())
    return Sistema("S2", "Valor", [
        Modulo("Sentir", [Patron(), Emocion(), Recuerdo()]),
        Modulo("Interpretar", [Sujeto(), Valor()]),
        Modulo("Reaccionar", [Exteriorizacion(), Impulso(), Feedback(), Estrategia(catalogo), Peticion(catalogo)]),
        Modulo("Actuar", [Accion(catalogo), Anticipacion(("placer", "estres"))]),
    ])


__all__ = ["crear_s2", "estrategias_s2"]
