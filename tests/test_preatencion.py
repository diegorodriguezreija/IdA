"""Pasos del latido de A3 (D1): preatención (D5), plasticidad (D6) y regulación (D12)."""

from typing import Any, List

from ida.core.arquitectura import Componente, Contexto
from ida.core.azar import Azar
from ida.core.latido import Organismo
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.sistemas import crear_sistemas


def _organismo(mundo: Any = None) -> Organismo:
    if mundo is None:
        from ida.mundos.minimo import MundoMinimo
        mundo = MundoMinimo()
    azar = Azar(7)
    return Organismo(mundo, crear_sistemas(), Arquetipo.nuevo(azar), Memoria(mundo.perfil.memoria), azar)


# --- Plasticidad (D6) -------------------------------------------------------------------------------
class _Espia(Componente):
    """Apunta cuándo se le llama a ``aprender`` y en qué fase del latido está la Onda."""

    def __init__(self, nombre: str, diario: List[Any]):
        super().__init__(nombre)
        self.diario = diario

    def aprender(self, ctx: Contexto) -> None:
        self.diario.append((self.nombre, [f[0] for f in ctx.onda.fases]))


def test_gancho_aprender_en_la_fase_aprender_y_en_orden() -> None:
    org = _organismo()
    diario: List[Any] = []
    previo = org._aprender

    def aprender_core(ctx: Contexto) -> None:
        diario.append(("_aprender", []))
        previo(ctx)

    org._aprender = aprender_core  # type: ignore[method-assign]
    org.sentir.componentes.append(_Espia("core", diario))
    for s in org.sistemas:
        for m in s.modulos:
            m.componentes.append(_Espia(f"{s.nombre}.{m.nombre}", diario))
    org.latir()
    nombres = [n for n, _ in diario]
    esperado = ["_aprender", "core"] + [f"{s.nombre}.{m.nombre}" for s in org.sistemas for m in s.modulos]
    assert nombres == esperado
    for _, fases in diario[1:]:
        # Ya terminó Sentir, aún no ha empezado la cognición: estamos dentro de la fase «aprender».
        assert "sentir" in fases and "aprender" not in fases and "S1" not in fases


def test_gancho_aprender_corre_dormido() -> None:
    org = _organismo()
    diario: List[Any] = []
    org.sentir.componentes.append(_Espia("core", diario))
    org.soma.dormido = True
    org.mundo.observar = _dormido(org.mundo.observar)  # type: ignore[method-assign]
    org.latir()
    assert org.soma.dormido and [n for n, _ in diario] == ["core"]


def _dormido(observar: Any) -> Any:
    def f() -> Any:
        obs = observar()
        obs.dormido = True
        return obs
    return f
