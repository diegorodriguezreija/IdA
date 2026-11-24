"""D4 (A4): la Observación solo la leen los sensores del Core.

- Tras Core · Sentir, el Organismo pone ``ctx.observacion = None``: ningún otro Componente montado (preatención, S1,
  S2, S3, Tribunal y Actuadores) la ve. Un lector olvidado falla en vez de pasar inadvertido.
- La pieza «yo» lleva ``inventario`` solo si el mundo lo tiene (``_situacion_inventario`` distingue así «sin
  inventario» de «inventario vacío», como antes con ``Observacion.inventario is None``).
"""

from typing import Any, List

import pytest

from ida.nucleo.arquitectura import Componente
from ida.nucleo.azar import Azar
from ida.core.latido import Organismo
from ida.nucleo.linaje import Arquetipo
from ida.nucleo.memoria import Memoria
from ida.sistemas import crear_sistemas


def _organismo(mundo: Any) -> Organismo:
    azar = Azar(7)
    return Organismo(mundo, crear_sistemas(), Arquetipo.nuevo(azar), Memoria(mundo.perfil.memoria), azar)


def _mundos() -> List[Any]:
    from ida.mundos.minimo import MundoMinimo
    mundos: List[Any] = [MundoMinimo()]
    try:
        from ida.mundos.crafter import MundoCrafter
    except ImportError:
        return mundos
    m = MundoCrafter()
    m.reiniciar(31)
    return mundos + [m]


@pytest.mark.parametrize("mundo", _mundos(), ids=lambda m: m.nombre)
def test_nadie_fuera_de_los_sensores_ve_la_observacion(mundo: Any) -> None:
    org = _organismo(mundo)
    sensores = set(map(id, org.sentir.componentes))
    vistos: List[str] = []
    llamados: List[str] = []

    def espiar(c: Componente) -> None:
        reactiva = c.reactiva

        def f(ctx: Any) -> None:
            llamados.append(c.nombre)
            if ctx.observacion is not None:
                vistos.append(c.nombre)
            reactiva(ctx)
        c.reactiva = f  # type: ignore[method-assign]
    for c in org.montados():
        if id(c) not in sensores:
            espiar(c)
    for _ in range(40):
        org.latir()
        if not org.soma.esta_vivo or mundo.terminado():
            break
    assert {"Saliencia", "Tribunal"} <= set(llamados)
    assert not vistos, sorted(set(vistos))


def test_inventario_en_yo_solo_si_el_mundo_lo_tiene() -> None:
    from ida.mundos.minimo import MundoMinimo
    org = _organismo(MundoMinimo())
    assert MundoMinimo().observar().inventario is None
    yo = org.latir().ev("Propiocepcion")["yo"]
    assert "inventario" not in yo.carga
    pytest.importorskip("crafter")
    from ida.mundos.crafter import MundoCrafter
    m = MundoCrafter()
    m.reiniciar(31)
    org = _organismo(m)
    yo = org.latir().ev("Propiocepcion")["yo"]
    assert isinstance(yo.carga["inventario"], dict) and yo.carga["inventario"]
