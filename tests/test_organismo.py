"""Tests de extremo a extremo con el mundo mínimo: el organismo vive, decide, aprende y es repetible."""

from ida.core.azar import Azar
from ida.core.latido import Organismo
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.vocabulario import Relacion, Verbo
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
        ej = onda.reactiva.ef["Accion"]["Accion"]
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


def test_tras_probar_la_seta_una_vez_no_vuelve_a_comerla():
    """Aprende de la experiencia: tras probar la seta (no nutre), no la vuelve a comer en el resto de la
    vida (semilla 3). No se exige que la hipótesis siga en memoria: protegerla de un único suceso es del
    bloque E. Que la baya nutre queda demostrado en la mayoría de las semillas 1 a 5 (una sola vida es
    sensible a cualquier cambio de trayectoria)."""

    def vida(semilla):
        mundo = MundoMinimo()
        mundo.reiniciar(semilla)
        azar = Azar(semilla)
        org = Organismo(mundo, crear_sistemas(), Arquetipo.nuevo(azar), Memoria(mundo.perfil.memoria), azar, True)
        comidas = []

        def anotar(o, onda):
            ej = onda.reactiva.ef["Accion"]["Accion"]
            if ej.carga["verbo"] == Verbo.COMER and ej.carga.get("exito"):
                comidas.append(ej.carga.get("clase", ""))

        org.vivir(250, al_latir=anotar)
        return org, comidas

    org, comidas = vida(3)
    assert comidas.count("seta") == 1                      # la prueba una vez y no repite
    demostrada = [vida(s)[0] for s in range(1, 6)]
    assert sum(o.memoria.demostrada("baya", Relacion.NUTRITIVO, o.ciclo) for o in demostrada) >= 3


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
    assert nombres == ["percibir", "sentir", "preatencion", "aprender", "S1", "S2", "S3", "actuar", "cierre"]
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


def test_la_causa_de_muerte_queda_siempre_registrada():
    mundo = MundoMinimo()
    mundo.reiniciar(3)
    azar = Azar(3)
    org = Organismo(mundo, crear_sistemas(), Arquetipo.nuevo(azar), Memoria(mundo.perfil.memoria), azar, True)
    org.soma.alimentacion, org.soma.vitalidad = 0.0, 1.0      # sin comida: el metabolismo quita 2 de vitalidad
    org.vivir(10)
    assert not org.soma.esta_vivo and org.causa_muerte == "hambre"
