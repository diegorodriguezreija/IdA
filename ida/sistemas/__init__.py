"""El circuito común de los sistemas (D2): los Componentes que comparten S1, S2 y S3 (``Accion``, ``Anticipacion``,
``Peticion`` y ``Estrategia``) y las lecturas comunes de la Onda (``piezas``, ``motivacion``). Va entre el Core y los
sistemas: importa ``ida.nucleo`` y nada de ``ida.s1``-``ida.s3``, salvo ``crear_sistemas``, que los importa al llamarla."""

from typing import List

from ida.nucleo.arquitectura import Sistema


def crear_sistemas() -> List[Sistema]:
    """S1, S2 y S3 en su orden fijo: S1 siempre primero; S2 y S3 con lo que sobra."""
    from ida.s1 import crear_s1
    from ida.s2 import crear_s2
    from ida.s3 import crear_s3
    return [crear_s1(), crear_s2(), crear_s3()]
