"""El mapa de Componentes (doc-repositorio/componentes.toml) es la especificación del diseño por Componentes.

- La especificación es válida y cada decisión citada existe en docs/DISENO_COMPONENTES.md.
- El documento generado (doc-repositorio/06_MAPA_DE_COMPONENTES.md) está al día.
- El código montado coincide con «hoy» en cada mundo: ni falta nada de lo que la especificación dice que
  está, ni hay nada montado que la especificación no declare.

Si este test falla tras mover un Componente, actualiza «hoy» en la especificación en el mismo PR.
Cambiar «destino» exige una decisión del autor (AGENTS.md); nunca para que pase el test.
"""

import os
import sys
from typing import Any, Callable, Dict, List, Set, Tuple

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "herramientas"))

import mapa_componentes as mc  # noqa: E402

from ida.nucleo.azar import Azar  # noqa: E402
from ida.core.latido import Organismo  # noqa: E402
from ida.nucleo.linaje import Arquetipo  # noqa: E402
from ida.nucleo.memoria import Memoria  # noqa: E402
from ida.sistemas_comun import crear_sistemas  # noqa: E402
from ida.sistemas_comun import Estrategia  # noqa: E402

Montado = Set[Tuple[str, str, str]]   # (tipo, ubicación, nombre)


def _minimo() -> Any:
    from ida.mundos.minimo import MundoMinimo
    return MundoMinimo()


def _archivos() -> Any:
    from ida.mundos.archivos import MundoArchivos
    return MundoArchivos()


def _crafter() -> Any:
    pytest.importorskip("crafter")
    from ida.mundos.crafter import MundoCrafter
    return MundoCrafter()


MUNDOS: Dict[str, Callable[[], Any]] = {"minimo": _minimo, "archivos": _archivos, "crafter": _crafter}


def _montado(mundo: Any) -> Montado:
    azar = Azar(1)
    org = Organismo(mundo, crear_sistemas(), Arquetipo.nuevo(azar), Memoria(mundo.perfil.memoria), azar)
    hay: Montado = set()
    for modulo, ubicacion in ((org.sentir, "CORE.Sentir"), (org.actuar, "CORE.Actuar")):
        hay |= {("componente", ubicacion, type(c).__name__) for c in modulo.componentes}
    hay.add(("componente", "CORE.Regulacion", type(org.regulacion).__name__))
    hay |= {("componente", "S1.Sentir", type(c).__name__) for c in org.preatencion.componentes}
    for sistema in org.sistemas:
        for modulo in sistema.modulos:
            ubicacion = f"{sistema.nombre}.{modulo.nombre}"
            for c in modulo.componentes:
                hay.add(("componente", ubicacion, type(c).__name__))
                if isinstance(c, Estrategia):
                    hay |= {("estrategia", ubicacion, type(d).__name__) for d in c.catalogo.todas()}
    return hay


def _esperado(espec: List[Dict[str, Any]], mundo: str) -> Montado:
    sustituidas = {c["sustituye"] for c in espec if c.get("sustituye") and c.get("dueno") == mundo}
    esperado: Montado = set()
    for c in espec:
        if c["tipo"] == "biblioteca" or c["hoy"] not in mc.UBICACIONES:
            continue
        en = mc.hoy_en(c)
        if en != "todos" and mundo not in en:
            continue
        if c["clase"] != "mundo" and c["nombre"] in sustituidas:
            continue
        esperado.add((c["tipo"], c["hoy"], c["nombre"]))
    return esperado


def test_especificacion_valida() -> None:
    errores = mc.validar(mc.cargar(), mc.decisiones_existentes())
    assert not errores, "\n".join(errores)


def test_documento_al_dia() -> None:
    with open(mc.DOC, encoding="utf-8") as f:
        actual = f.read()
    assert actual == mc.generar(mc.cargar()), "Ejecuta: python herramientas/mapa_componentes.py --escribir"


@pytest.mark.parametrize("mundo", sorted(MUNDOS))
def test_el_codigo_coincide_con_hoy(mundo: str) -> None:
    hay = _montado(MUNDOS[mundo]())
    esperado = _esperado(mc.cargar(), mundo)
    sin_declarar = sorted(hay - esperado)
    faltan = sorted(esperado - hay)
    assert not sin_declarar, f"Montado en {mundo} y no declarado (o con otro «hoy») en componentes.toml: {sin_declarar}"
    assert not faltan, f"Declarado en componentes.toml y no montado en {mundo}: {faltan}"
