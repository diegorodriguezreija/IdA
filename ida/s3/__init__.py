"""S3 · Verdad: comunicación, razonamiento y lenguaje formal interno. Trabaja con lo que le sobra a S2."""

from typing import List

from ida.nucleo.arquitectura import Modulo, Sistema
from ida.nucleo.estrategia import Catalogo, Definicion
from ida.s3.actuar.accion import Accion
from ida.s3.interpretar.agente import Agente
from ida.s3.interpretar.creencia import Creencia
from ida.s3.interpretar.logica import Logica
from ida.s3.interpretar.predicado import Predicado
from ida.s3.interpretar.proposicion import Proposicion
from ida.s3.interpretar.requisito import Requisito
from ida.s3.interpretar.sentencia import Sentencia
from ida.s3.reaccionar.estrategia import Estrategia
from ida.s3.reaccionar.estrategias import (
    CogerLoUtil,
    ComerLoNutritivo,
    Estudio,
    EvitarLoPeligroso,
    PerseguirMetas,
)
from ida.s3.reaccionar.feedback import Feedback
from ida.s3.reaccionar.impulso import Impulso
from ida.s3.reaccionar.intencion import Intencion
from ida.s3.sentir.comunicacion import Comunicacion


def estrategias_s3() -> List[Definicion]:
    return [EvitarLoPeligroso(), ComerLoNutritivo(), CogerLoUtil(), Estudio(), PerseguirMetas()]


def crear_s3() -> Sistema:
    catalogo = Catalogo(estrategias_s3())
    return Sistema("S3", "Verdad", [
        Modulo("Sentir", [Comunicacion()]),
        Modulo("Interpretar", [Agente(), Predicado(), Proposicion(), Sentencia(), Logica(), Creencia(), Requisito()]),
        Modulo("Reaccionar", [Intencion(), Impulso(), Feedback(), Estrategia(catalogo)]),
        Modulo("Actuar", [Accion(catalogo)]),
    ])


__all__ = ["crear_s3", "estrategias_s3"]
