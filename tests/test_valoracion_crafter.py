"""ValoracionCrafter (A4, D4 y D5): la valoración de Crafter, del organismo y no del adaptador.

- Latido a latido, en vidas con semilla, da los mismos ``nutritivo``, ``recurso`` y ``novedad`` que calculaba el
  adaptador (``_valoracion_antigua``: copia literal de ``MundoCrafter.observar`` y de sus visitas antes de A4), con las
  claves de los rasgos en el mismo orden.
- La cuenta de primitivas del Motor (copia eferente) coincide en cada latido con los pasos del entorno (``self.t``).
- ``Saliencia`` corre la última de la preatención, aunque el mundo registre después otro preatentivo.
"""

from typing import Any, Dict, List, Tuple

import pytest

from ida.core.azar import Azar
from ida.core.latido import Organismo
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.mundo import Observacion
from ida.core.vocabulario import Verbo
from ida.sistemas import crear_sistemas

ORDEN_COSA = ["proximidad", "nutritivo", "recurso", "agente"]
ORDEN_LUGAR = ["lugar", "proximidad", "nutritivo", "novedad"]


def _organismo(semilla: int, preparar: Any = None) -> Any:
    pytest.importorskip("crafter")
    from ida.mundos.crafter import MundoCrafter
    mundo = MundoCrafter(vista="oficial")
    mundo.reiniciar(semilla)
    if preparar is not None:
        preparar(mundo)       # antes de montar: los Actuadores guardan ``ejecutar_primitivas`` al construirse
    azar = Azar(semilla)
    org = Organismo(mundo, crear_sistemas(), Arquetipo.nuevo(azar), Memoria(mundo.perfil.memoria), azar)
    org.memoria.aplicar_manual(mundo.manual())
    return org


def _valoracion_antigua(m: Any, visitas: Dict[Tuple[int, int], int]) -> Dict[str, Dict[str, float]]:
    """Copia literal de la valoración que hacía ``MundoCrafter.observar`` antes de A4: id -> rasgos."""
    from ida.mundos.crafter import MOVIMIENTOS, NUTRITIVO_MANUAL, RECURSO_MANUAL, _dist

    def nutritivo_de(clase: str, obj: Any) -> float:
        if clase not in m.nutritivos or (clase == "planta" and not (obj is not None and getattr(obj, "ripe", False))):
            return 0.0
        return NUTRITIVO_MANUAL
    p = m.jugador
    pos = tuple(p.pos)
    cosas = m._cosas()
    cosas.sort(key=lambda c: (c[1] not in m.peligrosos, _dist(pos, c[2])))
    salida: Dict[str, Dict[str, float]] = {}
    for cid, clase, cpos, obj in cosas[:14]:
        d = _dist(pos, cpos)
        salida[cid] = {
            "proximidad": 1.0 if d <= 1 else max(0.0, 1.0 - d / (2 * m.radio + 1)),
            "nutritivo": nutritivo_de(clase, obj),
            "recurso": RECURSO_MANUAL if clase in m.utiles else 0.0,
            "agente": 1.0 if obj is not None and clase != "planta" else 0.0,
        }
    deseables = [(c, nutritivo_de(c[1], c[3])) for c in cosas if nutritivo_de(c[1], c[3]) > 0.1]
    w = m.env._world
    for (dx, dy), _ in MOVIMIENTOS.items():
        c = (pos[0] + dx, pos[1] + dy)
        if not (0 <= c[0] < w.area[0] and 0 <= c[1] < w.area[1]):
            continue
        mat, obj = w[c]
        if mat not in m.constantes.walkable or obj is not None:
            continue
        nutritivo = 0.0
        for (_, _, dpos, _), valor in deseables:
            if _dist(c, dpos) < _dist(pos, dpos):
                nutritivo = max(nutritivo, valor * (1.0 - _dist(c, dpos) / (4 * m.radio)))
        ultima = visitas.get(c)
        novedad = 1.0 if ultima is None else min(1.0, (m.t - ultima) / 50.0)
        salida[f"celda_{c[0]}_{c[1]}"] = {"lugar": 1.0, "proximidad": 1.0, "nutritivo": nutritivo, "novedad": novedad}
    return salida


def _motor(org: Organismo) -> Any:
    return next(c._motor for c in org.actuar.componentes if getattr(c, "_motor", None) is not None)


@pytest.mark.parametrize("semilla", [3, 31])
def test_misma_valoracion_que_el_adaptador(semilla: int) -> None:
    vistas: List[Tuple[Observacion, Dict[str, Dict[str, float]]]] = []
    visitas: Dict[Tuple[int, int], int] = {}

    def espiar(mundo: Any) -> None:
        observar, ejecutar = mundo.observar, mundo.ejecutar_primitivas

        def observar_y_valorar() -> Observacion:
            obs = observar()
            vistas.append((obs, _valoracion_antigua(mundo, visitas)))
            return obs

        def ejecutar_y_visitar(primitivas: List[str], intencion: Any = None) -> Any:
            ef = ejecutar(primitivas, intencion)
            if intencion == Verbo.MOVER and primitivas:      # las visitas del adaptador antes de A4
                visitas[tuple(mundo.jugador.pos)] = mundo.t
            return ef
        mundo.observar = observar_y_valorar
        mundo.ejecutar_primitivas = ejecutar_y_visitar
    org = _organismo(semilla, espiar)
    mundo = org.mundo
    motor = _motor(org)
    comparadas = {"cosa": 0, "lugar": 0, "novedad<1": 0, "gradiente>0": 0, "nutritiva": 0, "recurso": 0}
    for _ in range(500):
        onda = org.latir()
        obs, antigua = vistas[-1]
        assert sum(motor.ejecutadas.values()) == mundo.t      # copia eferente = pasos del entorno
        piezas = onda.ev("Exterocepcion")
        assert [e.id for e in obs.entidades] == list(piezas)
        assert list(antigua) == list(piezas)
        for e in obs.entidades:
            assert set(e.rasgos) <= {"proximidad", "agente", "lugar"}     # el adaptador no valora
            r, a = piezas[e.id].carga["rasgos"], antigua[e.id]
            if e.rasgos.get("lugar", 0.0) >= 0.5:
                assert list(r)[:4] == ORDEN_LUGAR
                assert (r["nutritivo"], r["novedad"]) == (a["nutritivo"], a["novedad"]), e.id
                comparadas["lugar"] += 1
                comparadas["novedad<1"] += r["novedad"] < 1.0
                comparadas["gradiente>0"] += r["nutritivo"] > 0.0
            else:
                assert list(r)[:4] == ORDEN_COSA
                assert (r["nutritivo"], r["recurso"]) == (a["nutritivo"], a["recurso"]), e.id
                comparadas["cosa"] += 1
                comparadas["nutritiva"] += r["nutritivo"] > 0.0
                comparadas["recurso"] += r["recurso"] > 0.0
            assert list(r)[4:] in ([], ["peligro"])
        if not org.soma.esta_vivo or mundo.terminado():
            break
    assert all(v > 0 for v in comparadas.values()), comparadas


def test_saliencia_la_ultima_de_la_preatencion() -> None:
    org = _organismo(1)
    nombres = [c.__class__.__name__ for c in org.preatencion.componentes]
    assert nombres[-1] == "Saliencia"
    assert "ValoracionCrafter" in nombres and nombres.index("ValoracionCrafter") < nombres.index("Saliencia")


def test_orden_de_las_claves_reconstruido() -> None:
    from ida.mundos.crafter_valoracion import ORDEN_COSA as COSA, ORDEN_LUGAR as LUGAR, _ordenados
    r: Dict[str, float] = {"proximidad": 1.0, "agente": 0.0, "peligro": 0.2}
    assert list(_ordenados(r, {"nutritivo": 0.6, "recurso": 0.0}, COSA)) == ORDEN_COSA + ["peligro"]
    assert list(_ordenados({"lugar": 1.0, "proximidad": 1.0}, {"nutritivo": 0.0, "novedad": 1.0}, LUGAR)) == ORDEN_LUGAR


def test_conocimiento_declarado_por_el_registro() -> None:
    """Crafter registra ``ValoracionCrafter`` en S1.Sentir con lo que su manual declara NUTRITIVO y UTIL, y el informe de
    conocimiento del mundo (D3) lo muestra."""
    pytest.importorskip("crafter")
    import importlib.util
    import pathlib

    from ida.mundos.crafter import MundoCrafter
    from ida.mundos.crafter_valoracion import ValoracionCrafter
    m = MundoCrafter()
    reg = m.registro()
    (v,) = reg.componentes["S1.Sentir"].añade
    assert isinstance(v, ValoracionCrafter) and v.preatentivo
    assert v.conocimiento_declarado() == {"NUTRITIVO": sorted(m.nutritivos), "UTIL": sorted(m.utiles)}
    assert v.cuerpo is reg.cuerpo           # la cuenta de primitivas es la del Motor que usan los Actuadores
    ruta = pathlib.Path(__file__).resolve().parent.parent / "herramientas" / "conocimiento_mundo.py"
    spec = importlib.util.spec_from_file_location("conocimiento_mundo", ruta)
    assert spec is not None and spec.loader is not None
    herramienta = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(herramienta)
    informe = herramienta.informe_mundo("crafter")
    assert "ValoracionCrafter (preatentivo) {NUTRITIVO: agua, planta, vaca;" in informe
    assert "`ida/mundos/crafter_valoracion.py`" in informe
    # A6a (D3, D15): los generales opcionales que registra Crafter; el mínimo, ninguno
    assert "- **Opcionales:** `Apetencia`, `Amenaza`, `Afrontar`, `Proteger`" in informe
    assert "- **Opcionales:** *(ninguno)*" in herramienta.informe_mundo("minimo")
