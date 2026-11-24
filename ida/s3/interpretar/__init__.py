"""Componentes de Interpretar para S3."""

from ida.s3.interpretar.agente import Agente
from ida.s3.interpretar.creencia import Creencia, creencia
from ida.s3.interpretar.logica import Logica
from ida.s3.interpretar.predicado import Predicado
from ida.s3.interpretar.proposicion import Proposicion
from ida.s3.interpretar.requisito import Requisito, Requisitos, desplazamiento
from ida.s3.interpretar.sentencia import Sentencia

__all__ = [
    "Agente",
    "Creencia",
    "Logica",
    "Predicado",
    "Proposicion",
    "Requisito",
    "Requisitos",
    "Sentencia",
    "creencia",
    "desplazamiento",
]
