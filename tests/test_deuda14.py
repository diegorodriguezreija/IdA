"""Deuda 14 (docs/ENCARGO_DEUDA14_HERRAMIENTAS.md): metas que comparten una estación, en un mundo de juguete.

Dos metas, «hacer_a» y «hacer_b», piden una unidad de «m» cada una y estar cerca de un «taller»; «m» se consigue cogiendo
«c», sin estar cerca de nada. El individuo está en (0, 0), «c» al lado y el taller a 10 casillas.
"""

from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from ida.core.memoria import Memoria
from ida.core.mundo import Perfil
from ida.core.pieza import Pieza
from ida.core.vocabulario import Verbo
from ida.sistemas.s3 import PerseguirMetas

MANUAL = {
    "inventario": ["m"],
    "hechos": [
        {"tipo": "meta", "verbo": "USAR", "objetivo": "hacer_a"},
        {"tipo": "meta", "verbo": "USAR", "objetivo": "hacer_b"},
        {"tipo": "requisito", "verbo": "USAR", "objetivo": "hacer_a", "requiere_inventario": {"m": None}, "requiere_cerca": ["taller"]},
        {"tipo": "requisito", "verbo": "USAR", "objetivo": "hacer_b", "requiere_inventario": {"m": None}, "requiere_cerca": ["taller"]},
        {"tipo": "requisito", "verbo": "COGER", "objetivo": "c", "requiere_inventario": {}, "efecto": {"m": 1}},
    ],
}


class _Onda:
    def __init__(self, canales: Dict[str, Dict[str, Pieza]]):
        self.canales = canales

    def ev(self, canal: str) -> Dict[str, Pieza]:
        return self.canales.get(canal, {})

    def ef(self, canal: str) -> Dict[str, Pieza]:
        return {}


def _entidad(id_: str, clase: str, proximidad: float, pos: tuple, lugar: float = 0.0) -> Pieza:
    return Pieza(id=id_, tipo="Exterocepcion", carga={"clase": clase, "rasgos": {"proximidad": proximidad, "lugar": lugar},
                                                       "datos": {"pos": pos}})


def _ctx(inventario: Dict[str, float], taller: tuple = (10, 0), latido: int = 1, manual: Optional[Dict[str, Any]] = None) -> Any:
    m = Memoria()
    m.aplicar_manual(manual or MANUAL)
    entidades: List[Pieza] = [
        _entidad("c_1", "c", 1.0, (0, -1)),
        _entidad("taller_1", "taller", 1.0 if max(abs(taller[0]), abs(taller[1])) <= 1 else 0.2, taller),
        _entidad("suelo_1_0", "suelo", 1.0, (1, 0), lugar=1.0),
        _entidad("suelo_m1_0", "suelo", 1.0, (-1, 0), lugar=1.0),
    ]
    yo = Pieza(id="yo", tipo="Propiocepcion", carga={"inventario": inventario, "cuerpo": {}})
    onda = _Onda({"Exterocepcion": {e.id: e for e in entidades}, "Propiocepcion": {"yo": yo}})
    return SimpleNamespace(memoria=m, onda=onda, con_experiencia=True, latido=latido,
                           observacion=SimpleNamespace(ubicacion="aqui_0_0"), verbos=set(Verbo), perfil=Perfil())


def _propuesta(ctx: Any) -> Optional[Any]:
    propuestas = PerseguirMetas().actuar(ctx, None)
    return propuestas[0] if propuestas else None


def test_se_elige_un_lote_cuando_comparte_estacion():
    p = _propuesta(_ctx({}))
    assert p is not None and p.motivo.startswith("metas: lote taller (hacer_a, hacer_b)")
    assert (p.verbo, p.objetivo) == (Verbo.COGER, "c_1")


def test_se_reune_el_material_antes_de_ir():
    """Con una unidad basta para una meta suelta, que va ya al taller (mundo con una sola meta); el lote coge antes la segunda."""
    una = {"inventario": ["m"], "hechos": [h for h in MANUAL["hechos"] if h.get("objetivo") != "hacer_b"]}
    sin = _propuesta(_ctx({"m": 1.0}, manual=una))
    assert sin is not None and sin.verbo == Verbo.MOVER and "lote" not in sin.motivo
    con = _propuesta(_ctx({"m": 1.0}))
    assert con is not None and (con.verbo, con.objetivo) == (Verbo.COGER, "c_1") and "lote taller" in con.motivo


def test_con_todo_el_material_el_lote_va_a_la_estacion():
    p = _propuesta(_ctx({"m": 2.0}))
    assert p is not None and p.verbo == Verbo.MOVER and p.objetivo == "suelo_1_0"


def test_junto_a_la_estacion_con_material_hace_la_meta_suelta():
    p = _propuesta(_ctx({"m": 2.0}, taller=(1, 1)))
    assert p is not None and p.verbo == Verbo.USAR and "lote" not in p.motivo


def test_el_lote_en_curso_sigue_hasta_tener_el_material():
    """Junto al taller con una unidad, la meta suelta es más barata (la gastaría); si el lote ya está en curso, sigue
    reuniendo el material de las dos."""
    suelta = _propuesta(_ctx({"m": 1.0}, taller=(1, 1)))
    assert suelta is not None and suelta.verbo == Verbo.USAR and "lote" not in suelta.motivo
    plan = PerseguirMetas()
    primero = plan.actuar(_ctx({}, latido=1), None)[0]
    assert "lote taller" in primero.motivo
    sigue = plan.actuar(_ctx({"m": 1.0}, taller=(1, 1), latido=2), None)[0]
    assert (sigue.verbo, sigue.objetivo) == (Verbo.COGER, "c_1") and "lote taller" in sigue.motivo
    hecho = plan.actuar(_ctx({"m": 2.0}, taller=(1, 1), latido=3), None)[0]
    assert hecho.verbo == Verbo.USAR and "lote" not in hecho.motivo

