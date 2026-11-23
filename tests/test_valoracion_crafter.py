"""ValoracionCrafter (A4, D4 y D5): la valoración de Crafter, del organismo y no del adaptador.

- Latido a latido, en vidas con semilla, da los mismos ``nutritivo``, ``recurso`` y ``novedad`` que calculaba el
  adaptador, con las claves de los rasgos en el mismo orden.
- La cuenta de primitivas del Motor (copia eferente) coincide en cada latido con los pasos del entorno (``self.t``).
- ``Saliencia`` corre la última de la preatención, aunque el mundo registre después otro preatentivo.
"""

from typing import Any, Dict, List

import pytest

from ida.core.azar import Azar
from ida.core.latido import Organismo
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.mundo import Observacion
from ida.sistemas import crear_sistemas

ORDEN_COSA = ["proximidad", "nutritivo", "recurso", "agente"]
ORDEN_LUGAR = ["lugar", "proximidad", "nutritivo", "novedad"]


def _organismo(semilla: int) -> Any:
    pytest.importorskip("crafter")
    from ida.mundos.crafter import MundoCrafter
    mundo = MundoCrafter(vista="oficial")
    mundo.reiniciar(semilla)
    azar = Azar(semilla)
    org = Organismo(mundo, crear_sistemas(), Arquetipo.nuevo(azar), Memoria(mundo.perfil.memoria), azar)
    org.memoria.aplicar_manual(mundo.manual())
    return org


def _motor(org: Organismo) -> Any:
    return next(c._motor for c in org.actuar.componentes if getattr(c, "_motor", None) is not None)


@pytest.mark.parametrize("semilla", [3, 31])
def test_misma_valoracion_que_el_adaptador(semilla: int) -> None:
    org = _organismo(semilla)
    mundo = org.mundo
    vistas: List[Observacion] = []
    observar = mundo.observar

    def espiar() -> Observacion:
        obs = observar()
        vistas.append(obs)
        return obs
    mundo.observar = espiar
    motor = _motor(org)
    comparadas = {"cosa": 0, "lugar": 0, "novedad<1": 0, "gradiente>0": 0, "nutritiva": 0, "recurso": 0}
    for _ in range(500):
        onda = org.latir()
        obs = vistas[-1]
        assert sum(motor.ejecutadas.values()) == mundo.t      # copia eferente = pasos del entorno
        piezas = onda.ev("Exterocepcion")
        assert [e.id for e in obs.entidades] == list(piezas)
        for e in obs.entidades:
            r = piezas[e.id].carga["rasgos"]
            if e.rasgos.get("lugar", 0.0) >= 0.5:
                assert list(r)[:4] == ORDEN_LUGAR
                assert (r["nutritivo"], r["novedad"]) == (e.rasgos["nutritivo"], e.rasgos["novedad"]), e.id
                comparadas["lugar"] += 1
                comparadas["novedad<1"] += r["novedad"] < 1.0
                comparadas["gradiente>0"] += r["nutritivo"] > 0.0
            else:
                assert list(r)[:4] == ORDEN_COSA
                assert (r["nutritivo"], r["recurso"]) == (e.rasgos["nutritivo"], e.rasgos["recurso"]), e.id
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
