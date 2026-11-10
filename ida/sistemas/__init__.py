"""Componentes base de S1, S2 y S3. Agnósticos del mundo: razonan solo con el vocabulario común."""

from typing import List

from ida.core.arquitectura import Sistema
from ida.sistemas.s1 import crear_s1
from ida.sistemas.s2 import crear_s2
from ida.sistemas.s3 import crear_s3


def crear_sistemas() -> List[Sistema]:
    """S1, S2 y S3 en su orden fijo: S1 siempre primero; S2 y S3 con lo que sobra."""
    return [crear_s1(), crear_s2(), crear_s3()]
