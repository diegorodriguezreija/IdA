"""Tests de extremo a extremo con el mundo mínimo: el organismo vive, decide, aprende y es repetible."""

from ida.core.azar import Azar
from ida.core.latido import Organismo
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.vocabulario import Relacion
from ida.mundos.minimo import MundoMinimo
from ida.sistemas import crear_sistemas


def _vida(semilla=3, latidos=200, con_experiencia=True, frecuencia=None):
    mundo = MundoMinimo()
    mundo.reiniciar(semilla)
    if frecuencia is not None:
        from dataclasses import replace
        mundo.perfil = replace(mundo.perfil, frecuencia_ms=frecuencia)
    azar = Azar(semilla)
    org = Organismo(mundo, crear_sistemas(), Arquetipo.nuevo(azar), Memoria(mundo.perfil.memoria), azar, con_experiencia)
    decisiones, notas = [], []

    def anotar(o, onda):
        ej = onda.reactiva.ef["Ejecucion"]["Ejecucion"]
        decisiones.append((ej.carga["verbo"].value, ej.carga["objetivo"]))
        notas.append(onda.notas)

    org.vivir(latidos, al_latir=anotar)
    return org, decisiones, notas


def test_vive_y_decide_cada_latido():
    org, decisiones, _ = _vida(latidos=80)
    assert len(decisiones) == org.ciclo > 0
    assert any(v == "COMER" for v, _ in decisiones)
    assert any(v == "MOVER" for v, _ in decisiones)


def test_misma_semilla_misma_vida():
    _, d1, _ = _vida(semilla=7, latidos=150)
    _, d2, _ = _vida(semilla=7, latidos=150)
    assert d1 == d2


def test_aprende_de_la_experiencia_que_la_seta_no_nutre():
    org, _, _ = _vida(semilla=3, latidos=250)
    p = org.memoria.proposicion("seta", Relacion.NUTRITIVO)
    assert p is not None and p.refutaciones > 0
    assert org.memoria.demostrada("baya", Relacion.NUTRITIVO, org.ciclo)


def test_se_ve_actuar_cada_dimension():
    org, _, notas = _vida(semilla=3, latidos=250)
    assert any("aprendizaje" in n for n in notas)          # reactiva → aprendizaje
    assert any("expectativa" in n for n in notas)          # proactiva
    assert any(e["activa"] != 0 for n in notas for e in n.get("evaluados", []))   # activa sesga
    assert any("episodio" in n for n in notas)


def test_sin_experiencia_no_aprende():
    org, _, notas = _vida(semilla=3, latidos=120, con_experiencia=False)
    assert not org.memoria.saber
    assert not any("expectativa" in n for n in notas)


def test_con_guillotina_extrema_s1_sigue_decidiendo():
    """Con un plazo de 0 ms la cognición se corta, pero el Tribunal siempre ejecuta algo."""
    org, decisiones, notas = _vida(semilla=3, latidos=30, frecuencia=0.0)
    assert org.contadores["guillotinas"] > 0
    assert len(decisiones) == org.ciclo


def test_la_onda_apunta_sus_fases():
    """Registro pasivo para la observabilidad: cada latido apunta sus fases en orden y sin solaparse."""
    mundo = MundoMinimo()
    mundo.reiniciar(3)
    azar = Azar(3)
    org = Organismo(mundo, crear_sistemas(), Arquetipo.nuevo(azar), Memoria(mundo.perfil.memoria), azar)
    onda = org.latir()
    nombres = [f[0] for f in onda.fases]
    assert nombres == ["percibir", "sentir", "aprender", "S1", "S2", "S3", "actuar", "cierre"]
    for (_, ini, fin), (_, ini_sig, _) in zip(onda.fases, onda.fases[1:], strict=False):
        assert ini <= fin <= ini_sig


def test_la_fase_cortada_por_la_guillotina_queda_apuntada():
    """Con plazo 0 ms la cognición se corta; las fases siguen apuntadas y el Tribunal actúa."""
    mundo = MundoMinimo()
    mundo.reiniciar(3)
    from dataclasses import replace
    mundo.perfil = replace(mundo.perfil, frecuencia_ms=0.0)
    azar = Azar(3)
    org = Organismo(mundo, crear_sistemas(), Arquetipo.nuevo(azar), Memoria(mundo.perfil.memoria), azar)
    onda = org.latir()
    nombres = [f[0] for f in onda.fases]
    assert onda.guillotina
    assert nombres[-2:] == ["actuar", "cierre"]
