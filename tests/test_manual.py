"""Paso 2 de la fase de generalización: manual declarativo, requisitos de las acciones y su herencia."""

import pytest

from ida.core.memoria import Memoria, Requisito
from ida.core.vocabulario import EstadoSaber, Relacion, Verbo
from ida.mundos.minimo import MundoMinimo

MANUAL = {
    "inventario": ["madera", "piedra", "pico"],
    "hechos": [
        {"id": "P1", "tipo": "proposicion", "sujeto": "vaca", "relacion": "NUTRITIVO", "veredicto": "afirma"},
        {"id": "R1", "tipo": "requisito", "verbo": "USAR", "objetivo": "place_table",
         "requiere_inventario": {"madera": None}, "requiere_cerca": []},
        {"id": "R2", "tipo": "requisito", "verbo": "USAR", "objetivo": "make_pico",
         "requiere_inventario": {"madera": None}, "requiere_cerca": ["mesa"]},
        {"id": "N1", "tipo": "nota", "texto": "no se carga"},
    ],
}


def test_manual_vacio_no_cambia_nada():
    m = Memoria()
    assert MundoMinimo.manual(MundoMinimo.__new__(MundoMinimo)) == {}
    assert m.aplicar_manual({}) == 0
    assert m.saber == {} and m.requisitos == {} and m.claves_inventario is None
    assert m.legado(0) == Memoria().legado(0)
    assert "requisitos" not in m.legado(0)


def test_carga_proposiciones_y_requisitos_sin_notas():
    m = Memoria()
    assert m.aplicar_manual(MANUAL) == 3
    assert set(m.requisitos) == {(Verbo.USAR, "place_table"), (Verbo.USAR, "make_pico")}
    r = m.requisitos[(Verbo.USAR, "make_pico")]
    assert r.fuente == "manual" and r.requiere_inventario == {"madera": None} and r.requiere_cerca == {"mesa"}
    assert m.claves_inventario == {"madera", "piedra", "pico"}


def test_proposicion_del_manual_es_autoridad_refutable():
    m = Memoria()
    m.aplicar_manual(MANUAL)
    p = m.saber[("vaca", Relacion.NUTRITIVO)]
    assert p.c_aut == pytest.approx(0.8) and p.w_aut == pytest.approx(1.0)
    assert p.confianza > p.c_exp                       # el manual sube la confianza de partida
    assert p.estado(0) == EstadoSaber.HIPOTESIS        # pero no la demuestra
    for t in range(1, 8):                              # comerla no alimenta: la experiencia la refuta
        m.aprender(Verbo.COMER, "vaca", {}, None, None, True, t)
    assert p.estado(8) == EstadoSaber.REFUTADA


def test_exito_fija_la_cantidad_consumida():
    m = Memoria()
    m.aplicar_manual(MANUAL)
    m.aprender_requisito(Verbo.USAR, "place_table", {"madera": 3.0}, {"madera": 1.0}, set(), True)
    r = m.requisitos[(Verbo.USAR, "place_table")]
    assert r.requiere_inventario["madera"] == 2
    assert r.exitos == 1 and r.efecto == {"madera": -2}
    assert r.confianza == pytest.approx(0.9)


def test_fallo_creyendo_que_bastaba_sube_la_cantidad():
    m = Memoria()
    m.aplicar_manual(MANUAL)
    m.aprender_requisito(Verbo.USAR, "place_table", {"madera": 1.0}, {"madera": 1.0}, set(), True)   # sin efecto
    r = m.requisitos[(Verbo.USAR, "place_table")]
    assert r.requiere_inventario["madera"] == 2
    assert r.fallos == 1 and r.confianza == pytest.approx(0.7)
    assert m.intentos[(Verbo.USAR, "place_table")] == [{"madera": 1.0}]


def test_exito_corrige_la_estimacion_por_fallos():
    m = Memoria()
    m.aplicar_manual(MANUAL)
    m.aprender_requisito(Verbo.USAR, "place_table", {"madera": 2.0}, {"madera": 2.0}, set(), True)   # fallo: sube a 3
    assert m.requisitos[(Verbo.USAR, "place_table")].requiere_inventario["madera"] == 3
    m.aprender_requisito(Verbo.USAR, "place_table", {"madera": 3.0}, {"madera": 1.0}, set(), True)   # consume 2
    assert m.requisitos[(Verbo.USAR, "place_table")].requiere_inventario["madera"] == 2


def test_fallo_sin_cumplir_lo_creido_no_toca_cantidades():
    m = Memoria()
    m.aplicar_manual(MANUAL)
    m.aprender_requisito(Verbo.USAR, "make_pico", {"madera": 1.0}, {"madera": 1.0}, set(), False)   # sin mesa cerca
    r = m.requisitos[(Verbo.USAR, "make_pico")]
    assert r.requiere_inventario == {"madera": None} and r.fallos == 0
    assert len(m.intentos[(Verbo.USAR, "make_pico")]) == 1


def test_lo_consumido_no_se_reinterpreta_tras_un_fallo():
    m = Memoria()
    m.aplicar_manual(MANUAL)
    m.aprender_requisito(Verbo.USAR, "place_table", {"madera": 3.0}, {"madera": 1.0}, set(), True)
    m.aprender_requisito(Verbo.USAR, "place_table", {"madera": 5.0}, {"madera": 5.0}, set(), True)   # p. ej. sitio no válido
    assert m.requisitos[(Verbo.USAR, "place_table")].requiere_inventario["madera"] == 2


def test_solo_cuentan_las_claves_de_objetos_del_manual():
    m = Memoria()
    m.aplicar_manual(MANUAL)
    m.aprender_requisito(Verbo.USAR, "place_table", {"madera": 3.0, "comida": 5.0}, {"madera": 1.0, "comida": 4.0}, set(), True)
    assert m.requisitos[(Verbo.USAR, "place_table")].requiere_inventario == {"madera": 2}


def test_requisito_descubierto_por_experiencia():
    m = Memoria()
    """Un éxito aislado (sin fallos previos) solo registra el efecto: ni la mesa que había cerca ni lo que
    se llevaba pasan a ser requisitos."""
    m = Memoria()
    m.aprender_requisito(Verbo.COGER, "piedra", {"pico": 1.0, "madera": 2.0}, {"pico": 1.0, "madera": 1.0, "piedra": 1.0},
                         {"piedra", "mesa"}, True)
    r = m.requisitos[(Verbo.COGER, "piedra")]
    assert r.fuente == "experiencia" and r.efecto == {"madera": -1, "piedra": 1}
    assert r.requiere_cerca == set() and r.requiere_inventario == {}


def test_desplazamientos_de_cercania_aprendidos():
    """La diagonal (1, 1) y dos casillas en línea (0, 2) no se confunden."""
    m = Memoria()
    m.aplicar_manual(MANUAL)                      # make_pico requiere mesa cerca
    r = m.requisitos[(Verbo.USAR, "make_pico")]
    assert r.cerca_basta("mesa", (0, 1)) and r.cerca_basta("mesa", (1, 1)) and r.cerca_basta("mesa", (0, 2))   # se prueba
    assert not r.cerca_basta("mesa", (1, 2))
    m.aprender_requisito(Verbo.USAR, "make_pico", {"madera": 1.0}, {"madera": 1.0}, set(), True, distancias={"mesa": (0, 2)})
    assert not r.cerca_basta("mesa", (0, 2))      # en línea falló: ya no se prueba
    assert r.cerca_basta("mesa", (1, 1))          # la diagonal sigue sin probar
    m.aprender_requisito(Verbo.USAR, "make_pico", {"madera": 1.0}, {"madera": 0.0, "pico": 1.0}, set(), True, distancias={"mesa": (1, 1)})
    assert r.cerca_ok == {"mesa": {(1, 1)}} and r.cerca_fallida == {"mesa": {(0, 2)}}


def test_induccion_descarta_fallos_explicados():
    """Los fallos por no llegar a la cantidad conocida no sirven para buscar otra causa (sin «pico» espurio)."""
    m = Memoria()
    m.aplicar_manual({"inventario": ["piedra", "pico"], "hechos": [
        {"tipo": "requisito", "verbo": "USAR", "objetivo": "place_horno", "requiere_inventario": {"piedra": None}}]})
    for n in (1.0, 2.0, 3.0):                     # falla con 1, 2 y 3 piedras, sin pico: la cantidad sube a 4
        m.aprender_requisito(Verbo.USAR, "place_horno", {"piedra": n}, {"piedra": n}, set(), True)
    m.aprender_requisito(Verbo.USAR, "place_horno", {"piedra": 4.0, "pico": 1.0}, {"pico": 1.0}, set(), True)
    assert m.requisitos[(Verbo.USAR, "place_horno")].requiere_inventario == {"piedra": 4}


def test_delante_solo_cuenta_para_usar():
    m = Memoria()
    m.aprender_requisito(Verbo.COGER, "piedra", {}, {"piedra": 1.0}, set(), True, delante="hierba")
    assert m.requisitos[(Verbo.COGER, "piedra")].requiere_delante == set()


def test_legado_solo_con_exitos_y_herencia():
    m = Memoria()
    m.aplicar_manual(MANUAL)
    m.aprender_requisito(Verbo.USAR, "place_table", {"madera": 3.0}, {"madera": 1.0}, set(), True)
    legado = m.legado(10)
    assert [d["objetivo"] for d in legado["requisitos"]] == ["place_table"]   # make_pico, sin éxitos, no pasa

    hija = Memoria()
    hija.aplicar_manual(MANUAL)            # al nacer, antes de heredar
    hija.heredar(legado)
    r = hija.requisitos[(Verbo.USAR, "place_table")]
    assert isinstance(r, Requisito) and r.heredado and r.requiere_inventario == {"madera": 2}
    assert hija.requisitos[(Verbo.USAR, "make_pico")].fuente == "manual"


def test_herencia_conserva_la_autoridad_del_manual():
    m = Memoria()
    m.aplicar_manual(MANUAL)
    m.heredar({"proposiciones": [{"sujeto": "vaca", "relacion": "NUTRITIVO", "confianza": 0.9}]})
    p = m.saber[("vaca", Relacion.NUTRITIVO)]
    assert p.heredada and p.c_aut == pytest.approx(0.8)


def test_memoria_apagada_no_carga_nada():
    m = Memoria("apagada")
    assert m.aplicar_manual(MANUAL) == 0 and m.requisitos == {}
