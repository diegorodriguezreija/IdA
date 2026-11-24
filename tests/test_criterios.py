"""Tests de los criterios de diseño D8 y D5 (Paso A8).

- D8: Ninguna estrategia (en reaccionar/estrategias/ de ida/s1-s3 y de ida/mundos/*)
  ni ningún Componente fuera de ida/core/sentir lee ``observacion``, el mundo (``mundo``,
  ``.env``, ``_world``) ni un reloj del mundo (``.t`` de un mundo, reloj/paso del mundo,
  ``hora``, ``reloj``). ``ctx.latido`` y ``ciclo`` (tiempo interno del organismo) están permitidos.
- D5: Los Componentes preatentivos tienen ``preatentivo = True`` y viven en ``sentir/``.
- Sustituye a ``test_crafter_no_escribe_conducta`` conservando la verificación de que el adaptador
  no define estrategias y que Crafter solo registra ``SalirDelRecinto``.
"""

import ast
import inspect
import pathlib
from typing import List

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
IDA = RAIZ / "ida"


def _ficheros_estrategias() -> List[pathlib.Path]:
    ficheros = []
    for p in IDA.rglob("*.py"):
        if "__pycache__" in p.parts or p.name == "__init__.py":
            continue
        parts = p.parts
        if "reaccionar" in parts and "estrategias" in parts:
            ficheros.append(p)
    return sorted(ficheros)


def _ficheros_componentes_fuera_de_sentir() -> List[pathlib.Path]:
    ficheros = []
    for p in IDA.rglob("*.py"):
        if "__pycache__" in p.parts or p.name == "__init__.py":
            continue
        rel = p.relative_to(IDA).as_posix()
        # Excluir mecánica de núcleo
        if rel.startswith("nucleo/"):
            continue
        # Excluir sensores del core (donde sí se lee observacion)
        if rel.startswith("core/sentir/"):
            continue
        # Excluir adaptadores de mundo, perfiles y manuales
        if "adaptador" in p.name or "perfil" in p.name or "manual" in p.name or "registro" in p.name:
            continue
        # Excluir orquestación de latido y ejecutor/CLI/telemetría
        if p.name in ("latido.py", "ejecutor.py", "historico.py", "__main__.py"):
            continue
        if "telemetria" in p.parts:
            continue
        # Excluir estrategias (ya se comprueban por separado)
        if "reaccionar" in p.parts and "estrategias" in p.parts:
            continue
        # Comprobar si define al menos una clase
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        if any(isinstance(n, ast.ClassDef) for n in ast.walk(tree)):
            ficheros.append(p)
    return sorted(ficheros)


ATTRS_PROHIBIDOS = {"observacion", "mundo", "env", "_world", "reloj", "hora", "t"}
NAMES_PROHIBIDOS = {"observacion", "mundo", "reloj", "hora"}


def _comprobar_ast(ruta: pathlib.Path) -> List[str]:
    """Detecta accesos prohibidos a observacion, mundo o reloj del mundo."""
    tree = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
    violaciones = []
    for node in ast.walk(tree):
        # Lectura de atributo prohibido
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            if node.attr in ATTRS_PROHIBIDOS:
                violaciones.append(f"{ruta.name}:{node.lineno} lee atributo '.{node.attr}'")
            elif node.attr == "paso":
                # .paso solo es reloj del mundo si se lee de ctx, mundo, env o similar
                if isinstance(node.value, ast.Name) and node.value.id in ("ctx", "mundo", "env", "obs", "_world"):
                    violaciones.append(f"{ruta.name}:{node.lineno} lee reloj '.paso' de {node.value.id}")
        # Lectura de variable/parámetro prohibido
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in NAMES_PROHIBIDOS:
                violaciones.append(f"{ruta.name}:{node.lineno} lee nombre '{node.id}'")
    return violaciones


@pytest.mark.parametrize("ruta", _ficheros_estrategias(), ids=lambda p: p.relative_to(IDA).as_posix())
def test_criterio_d8_estrategias_no_leen_mundo_ni_observacion_ni_reloj(ruta: pathlib.Path) -> None:
    """D8: ninguna estrategia lee observacion, el mundo ni reloj del mundo."""
    violaciones = _comprobar_ast(ruta)
    assert not violaciones, f"Violaciones en {ruta}:\n" + "\n".join(violaciones)


@pytest.mark.parametrize("ruta", _ficheros_componentes_fuera_de_sentir(), ids=lambda p: p.relative_to(IDA).as_posix())
def test_criterio_d8_componentes_no_leen_mundo_ni_observacion_ni_reloj(ruta: pathlib.Path) -> None:
    """D8: ningún Componente fuera de core/sentir lee observacion, mundo ni reloj del mundo."""
    violaciones = _comprobar_ast(ruta)
    assert not violaciones, f"Violaciones en {ruta}:\n" + "\n".join(violaciones)


def test_criterio_d5_componentes_preatentivos() -> None:
    """D5: los Componentes preatentivos tienen preatentivo = True y viven en sentir/."""
    from ida.s1.sentir.saliencia import Saliencia
    from ida.s1.sentir.amenaza import Amenaza
    clases: List[type] = [Saliencia, Amenaza]

    pytest.importorskip("crafter")
    from ida.mundos.crafter.s1.sentir.valoracion import ValoracionCrafter
    clases.append(ValoracionCrafter)

    for cls in clases:
        assert getattr(cls, "preatentivo", False) is True, f"{cls.__name__} debe tener preatentivo = True"
        mod = cls.__module__
        assert "sentir" in mod.split("."), f"{cls.__name__} (en {mod}) debe vivir en una carpeta sentir/"


def test_crafter_adaptador_no_define_conducta():
    """Conservado de test_crafter_no_escribe_conducta:

    - Ninguna clase de ida/mundos/crafter/adaptador.py es una estrategia.
    - Crafter solo registra SalirDelRecinto como estrategia en S1.
    """
    pytest.importorskip("crafter")
    from ida.nucleo.estrategia import ConPropuestas, Definicion, Plan
    from ida.mundos.crafter import MundoCrafter, adaptador

    clases = [c for _, c in inspect.getmembers(adaptador, inspect.isclass) if c.__module__ == adaptador.__name__]
    assert clases  # el adaptador existe
    assert not [c.__name__ for c in clases if issubclass(c, (Definicion, Plan, ConPropuestas))]

    estrategias = MundoCrafter().registro().estrategias
    assert list(estrategias) == ["S1"] and not estrategias["S1"].sustituye
    assert [type(d).__name__ for d in estrategias["S1"].añade] == ["SalirDelRecinto"]
