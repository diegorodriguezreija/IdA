"""Pasos del latido de A3 (D1): preatención (D5), plasticidad (D6) y regulación (D12)."""

from typing import Any, Callable, Dict, List, Tuple

import pytest

from ida.core.arquitectura import Componente, Contexto, Modulo, Preatencion, Sistema
from ida.core.azar import Azar
from ida.core.latido import Organismo
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.onda import PiezaAjena
from ida.core.pieza import Pieza, acotar
from ida.core.vocabulario import Verbo
from ida.sistemas import crear_sistemas
from ida.sistemas.saliencia import Saliencia


def _organismo(mundo: Any = None) -> Organismo:
    if mundo is None:
        from ida.mundos.minimo import MundoMinimo
        mundo = MundoMinimo()
    azar = Azar(7)
    return Organismo(mundo, crear_sistemas(), Arquetipo.nuevo(azar), Memoria(mundo.perfil.memoria), azar)


def _dormido(observar: Any) -> Any:
    def f() -> Any:
        obs = observar()
        obs.dormido = True
        return obs
    return f


# --- Plasticidad (D6) -------------------------------------------------------------------------------
class _Espia(Componente):
    """Apunta cuándo se le llama a ``aprender`` y en qué fase del latido está la Onda."""

    def __init__(self, nombre: str, diario: List[Any]):
        super().__init__(nombre)
        self.diario = diario

    def aprender(self, ctx: Contexto) -> None:
        self.diario.append((self.nombre, [f[0] for f in ctx.onda.fases]))


class _EspiaPreatentivo(_Espia):
    tipo = "Exterocepcion"
    preatentivo = True


def test_gancho_aprender_en_la_fase_aprender_y_en_orden() -> None:
    org = _organismo()
    diario: List[Any] = []
    previo = org._aprender

    def aprender_core(ctx: Contexto) -> None:
        diario.append(("_aprender", []))
        previo(ctx)

    org._aprender = aprender_core  # type: ignore[method-assign]
    org.sentir.componentes.append(_Espia("core", diario))
    org.preatencion.componentes.append(_EspiaPreatentivo("preatencion", diario))
    for s in org.sistemas:
        for m in s.modulos:
            m.componentes.append(_Espia(f"{s.nombre}.{m.nombre}", diario))
    org.latir()
    nombres = [n for n, _ in diario]
    esperado = ["_aprender", "core", "preatencion"] + [f"{s.nombre}.{m.nombre}" for s in org.sistemas for m in s.modulos]
    assert nombres == esperado
    for _, fases in diario[1:]:
        # Ya terminaron Sentir y la preatención, aún no ha empezado la cognición: estamos en la fase «aprender».
        assert "sentir" in fases and "preatencion" in fases and "aprender" not in fases and "S1" not in fases


def test_gancho_aprender_corre_dormido() -> None:
    org = _organismo()
    diario: List[Any] = []
    org.sentir.componentes.append(_Espia("core", diario))
    org.mundo.observar = _dormido(org.mundo.observar)  # type: ignore[method-assign]
    org.latir()
    assert org.soma.dormido and [n for n, _ in diario] == ["core"]


# --- Preatención (D5) -------------------------------------------------------------------------------
class _Preatentivo(Componente):
    """Preatentivo de prueba: ejecuta ``accion(self, ctx)`` en su barrido reactivo y apunta la Onda que ve."""

    tipo = "Exterocepcion"
    preatentivo = True

    def __init__(self, accion: Callable[["_Preatentivo", Contexto], Any]):
        super().__init__("Prueba")
        self.accion = accion
        self.vistos: List[Dict[str, Any]] = []

    def reactiva(self, ctx: Contexto) -> None:
        o = ctx.onda
        self.vistos.append({"exento": o.exento, "preatencion": o.preatencion, "amplitud": o.amplitud_consumida,
                            "potencia": o.potencia_consumida, "operaciones": o.operaciones, "dormido": ctx.soma.dormido})
        self.accion(self, ctx)
        self.vistos[-1]["despues"] = (o.amplitud_consumida, o.potencia_consumida, o.operaciones)


def _con_preatentivo(accion: Callable[[_Preatentivo, Contexto], Any]) -> Tuple[Organismo, _Preatentivo]:
    org = _organismo()
    p = _Preatentivo(accion)
    p.sistema = "S1"
    org.preatencion.componentes.append(p)
    return org, p


def _subir_todo(comp: _Preatentivo, ctx: Contexto) -> None:
    for canal in ("Exterocepcion", "Interocepcion"):
        for pieza in ctx.onda.ev(canal).values():
            comp.modificar(ctx, pieza, arousal=1.0 - pieza.arousal)


def test_la_preatencion_no_consume_amplitud_ni_potencia() -> None:
    org, p = _con_preatentivo(_subir_todo)
    org.ops_por_ms = 1.0   # plazo lógico: tampoco cuenta operaciones
    onda = org.latir()
    visto = p.vistos[0]
    assert visto["exento"] and visto["preatencion"]
    assert (visto["amplitud"], visto["potencia"], visto["operaciones"]) == (0, 0.0, 0)
    assert visto["despues"] == (0, 0.0, 0)
    assert "preatencion" in [f[0] for f in onda.fases]
    assert any(k.startswith("preatencion:S1.") for k in onda.tiempos_ms)
    assert not onda.preatencion and not onda.exento


def test_la_preatencion_no_vuelve_a_correr_en_la_cognicion() -> None:
    org, p = _con_preatentivo(lambda comp, ctx: None)
    org.latir()
    assert len(p.vistos) == 1
    assert all(not c.preatentivo for s in org.sistemas for m in s.modulos for c in m.componentes)


def test_la_preatencion_corre_dormido() -> None:
    org, p = _con_preatentivo(lambda comp, ctx: None)
    org.mundo.observar = _dormido(org.mundo.observar)  # type: ignore[method-assign]
    org.latir()
    assert len(p.vistos) == 1 and p.vistos[0]["dormido"]


def _pieza(tipo: str, id: str = "x") -> Pieza:
    return Pieza(id=id, tipo=tipo, arousal=0.5, carga={"rasgos": {}}, sistema="S1")


def _una_exterocepcion(ctx: Contexto) -> Pieza:
    return next(iter(ctx.onda.ev("Exterocepcion").values()))


@pytest.mark.parametrize("accion", [
    pytest.param(lambda c, ctx: c.percibir(ctx, _pieza("Exterocepcion", "nueva")), id="percibir"),
    pytest.param(lambda c, ctx: c.registrar(ctx, _pieza("Exterocepcion", "nueva")), id="registrar"),
    pytest.param(lambda c, ctx: c.proponer(ctx, Verbo.ESPERAR, "", 1.0, 1.0, "prueba"), id="proponer"),
    pytest.param(lambda c, ctx: c.modificar(ctx, _pieza("Objeto"), arousal=0.9), id="modificar-no-sensora"),
    pytest.param(lambda c, ctx: c.modificar(ctx, _una_exterocepcion(ctx), confianza=0.1), id="modificar-confianza"),
    pytest.param(lambda c, ctx: c.modificar(ctx, _una_exterocepcion(ctx), carga={"clase": "otra"}), id="modificar-carga"),
])
def test_un_preatentivo_solo_modifica_sensores(accion: Callable[[_Preatentivo, Contexto], Any]) -> None:
    org, _ = _con_preatentivo(accion)
    with pytest.raises(PiezaAjena):
        org.latir()


def test_solo_preatentivos_en_la_preatencion() -> None:
    with pytest.raises(ValueError):
        Preatencion([_Espia("no", [])])
    with pytest.raises(ValueError):
        Sistema("S1", "x", [Modulo("Sentir", [Saliencia()])])
    with pytest.raises(ValueError):
        Sistema("S2", "x", [], preatencion=[Saliencia()])


def test_exterocepcion_en_bruto_y_saliencia_de_antes() -> None:
    """Exterocepcion emite con arousal 0; tras la preatención, cada pieza tiene la saliencia que calculaba antes el
    sensor (``sentidos.py:57`` en eaeadaa)."""
    org = _organismo()
    obs_vista: List[Any] = []
    observar = org.mundo.observar

    def capturar() -> Any:
        obs = observar()
        obs_vista.append(obs)
        return obs

    org.mundo.observar = capturar  # type: ignore[method-assign]
    en_bruto: List[float] = []
    original = org.preatencion.ejecutar

    def antes_de_la_preatencion(ctx: Contexto) -> None:
        en_bruto.extend(p.arousal for p in ctx.onda.ev("Exterocepcion").values())
        original(ctx)

    org.preatencion.ejecutar = antes_de_la_preatencion  # type: ignore[method-assign]
    onda = org.latir()
    piezas = onda.ev("Exterocepcion")
    assert piezas and en_bruto and all(a == 0.0 for a in en_bruto)
    assert any(p.arousal > 0.0 for p in piezas.values())
    for e in obs_vista[0].entidades:
        r = e.rasgos
        cerca = r.get("proximidad", 0.0)
        esperado = acotar(max(r.get("peligro", 0.0) * max(cerca, 0.3), r.get("nutritivo", 0.0) * cerca, 0.4 * r.get("novedad", 0.0)))
        assert piezas[e.id].arousal == esperado
