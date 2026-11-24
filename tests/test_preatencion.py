"""Pasos del latido de A3 (D1): preatención (D5), plasticidad (D6) y regulación (D12)."""

from typing import Any, Callable, Dict, List, Tuple

import pytest

from ida.nucleo.arquitectura import Componente, Contexto, Modulo, Preatencion, Sistema
from ida.nucleo.azar import Azar
from ida.core.latido import Organismo
from ida.nucleo.linaje import Arquetipo
from ida.nucleo.memoria import Memoria
from ida.nucleo.onda import PiezaAjena
from ida.nucleo.pieza import Pieza, acotar
from ida.nucleo.vocabulario import Verbo
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


# --- Amenaza (D5, D7) -------------------------------------------------------------------------------
def test_amenaza_va_antes_que_saliencia() -> None:
    """Amenaza es opcional (D3): el mínimo no la registra; quien la registra la tiene antes que Saliencia."""
    from ida.nucleo.mundo import Registro
    from ida.mundos.minimo import MundoMinimo

    class MundoConAmenaza(MundoMinimo):
        def registro(self) -> Registro:
            reg = super().registro()
            reg.opcionales = ["Amenaza"]
            return reg

    assert [type(c).__name__ for c in _organismo().preatencion.componentes] == ["Saliencia"]
    org = _organismo(MundoConAmenaza())
    assert [type(c).__name__ for c in org.preatencion.componentes] == ["Amenaza", "Saliencia"]


def test_amenaza_escribe_el_peligro_en_la_pieza_y_no_en_la_observacion() -> None:
    """En un mundo con posiciones y sin peligro propio (Crafter): el peligro va al final de los rasgos de cada pieza
    ``Exterocepcion`` con posición, con el valor que daba ``estimar`` sobre la Observación, y la Observación queda sin
    él. Se comprueba varios latidos, también tras aprender."""
    pytest.importorskip("crafter")
    import copy

    from ida.mundos.crafter import MundoCrafter
    from ida.sistemas import amenaza as pel
    from ida.sistemas.amenaza import Amenaza

    mundo = MundoCrafter()
    mundo.reiniciar(31)
    org = _organismo(mundo)
    obs_vista: List[Any] = []
    observar = mundo.observar

    def capturar() -> Any:
        obs = observar()
        obs_vista.append(obs)
        return obs

    mundo.observar = capturar  # type: ignore[method-assign]
    amenaza = next(c for c in org.preatencion.componentes if isinstance(c, Amenaza))
    esperados: List[Dict[str, float]] = []
    reactiva = amenaza.reactiva

    def comprobar(ctx: Contexto) -> None:
        reactiva(ctx)
        assert ctx.extra.get("peligro_aprendido") is True
        # Lo que habría escrito la versión anterior en la Observación, con la memoria ya actualizada
        assert ctx.observacion is None             # D4: tras Core · Sentir nadie la lee; se usa la capturada
        entidades = copy.deepcopy(obs_vista[-1].entidades)
        aqui = pel.pos_de(obs_vista[-1].ubicacion)
        assert aqui is not None
        pel.estimar(entidades, aqui, ctx.memoria.seccion("peligros"), ctx.soma.vitalidad, ctx.memoria.peligrosa, dormido=bool(ctx.soma.dormido))
        esperados.append({e.id: e.rasgos["peligro"] for e in entidades if "peligro" in e.rasgos})

    amenaza.reactiva = comprobar  # type: ignore[method-assign]
    for _ in range(30):
        onda = org.latir()
        obs = obs_vista[-1]
        piezas = onda.ev("Exterocepcion")
        assert all("peligro" not in e.rasgos for e in obs.entidades)
        con_peligro = {i: p for i, p in piezas.items() if "peligro" in p.carga["rasgos"]}
        assert con_peligro and set(con_peligro) == set(esperados[-1])
        for i, p in con_peligro.items():
            assert list(p.carga["rasgos"])[-1] == "peligro"
            assert p.carga["rasgos"]["peligro"] == esperados[-1][i]
        if mundo.terminado():
            break
