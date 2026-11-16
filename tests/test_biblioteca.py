"""Tests de la biblioteca externa de autoridad y del componente Estudio (Fase 4a)."""

import os
import tempfile
import pytest

from ida.bibliotecas.erronea import BibliotecaErronea
from ida.bibliotecas.fija import BibliotecaFija
from ida.bibliotecas.nula import BibliotecaNula
from ida.core.arquitectura import Contexto
from ida.core.azar import Azar
from ida.core.biblioteca import (
    Consulta,
    ElementoConsulta,
    EstadoLectura,
    Veredicto,
)
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria, Proposicion
from ida.core.mundo import Perfil
from ida.core.onda import Onda
from ida.core.persistencia import Persistencia
from ida.core.pieza import Pieza
from ida.core.soma import Soma
from ida.core.vocabulario import Relacion, Verbo
from ida.sistemas.s3 import Estudio


def test_biblioteca_nula_siempre_no_sabe():
    bib = BibliotecaNula()
    consulta = Consulta([
        ElementoConsulta("baya", Relacion.NUTRITIVO),
        ElementoConsulta("lobo", Relacion.PELIGROSO),
    ])
    ticket = bib.solicitar(consulta)
    assert ticket.lista()
    resp = ticket.respuesta()
    assert resp is not None
    assert len(resp.elementos) == 2
    for el in resp.elementos:
        assert el.veredicto == Veredicto.NO_SABE
        assert el.confianza == 0.0


def test_biblioteca_fija_respuestas_deterministas():
    datos = {
        ("baya", "NUTRITIVO"): ("afirma", 0.9),
        ("seta", "NUTRITIVO"): ("niega", 0.85),
    }
    bib = BibliotecaFija(datos)
    consulta = Consulta([
        ElementoConsulta("baya", Relacion.NUTRITIVO),
        ElementoConsulta("seta", Relacion.NUTRITIVO),
        ElementoConsulta("roca", Relacion.UTIL),
    ])
    ticket = bib.solicitar(consulta)
    assert ticket.lista()
    resp = ticket.respuesta()
    assert resp is not None
    assert len(resp.elementos) == 3

    assert resp.elementos[0].veredicto == Veredicto.AFIRMA
    assert resp.elementos[0].confianza == pytest.approx(0.9)

    assert resp.elementos[1].veredicto == Veredicto.NIEGA
    assert resp.elementos[1].confianza == pytest.approx(0.85)

    assert resp.elementos[2].veredicto == Veredicto.NO_SABE
    assert resp.elementos[2].confianza == 0.0


def test_biblioteca_erronea_invierte_con_semilla():
    datos = {
        ("baya", "NUTRITIVO"): ("afirma", 0.9),
        ("seta", "NUTRITIVO"): ("afirma", 0.9),
    }
    # Tasa error 1.0 => todas las afirmaciones se invierten a negaciones
    bib = BibliotecaErronea(datos, tasa_error=1.0, semilla=123)
    ticket = bib.solicitar(Consulta([ElementoConsulta("baya", Relacion.NUTRITIVO)]))
    resp = ticket.respuesta()
    assert resp is not None
    assert resp.elementos[0].veredicto == Veredicto.NIEGA


def _crear_ctx(latido: int, mem: Memoria, bib=None, ef_anterior=None, peligro: float = 0.0, verbo_ejecutado=None):
    onda = Onda(latido, 100, 100.0, ef_anterior=ef_anterior)
    if peligro > 0:
        onda.registrar("Supervivencia", Pieza("alarma", "Supervivencia", arousal=0.8, carga={"peligro": peligro}))
        onda.percibir("Supervivencia", Pieza("alarma", "Supervivencia", arousal=0.8, carga={"peligro": peligro}))
    soma = Soma()
    arq = Arquetipo(responsabilidad=0.8, apertura=0.2)   # deferencia = 0.6*0.8 + 0.4*0.8 = 0.8
    verbos = {Verbo.MOVER, Verbo.COMER, Verbo.ESPERAR, Verbo.LEER}
    return Contexto(
        onda=onda,
        soma=soma,
        memoria=mem,
        arquetipo=arq,
        azar=Azar(1),
        perfil=Perfil(),
        verbos=verbos,
        biblioteca=bib,
    )


def test_estudio_ciclo_completo_lectura():
    mem = Memoria()
    p = Proposicion("baya", Relacion.NUTRITIVO, confianza=0.3)
    mem.saber[("baya", Relacion.NUTRITIVO)] = p
    bib = BibliotecaFija({("baya", "NUTRITIVO"): ("afirma", 0.9)})
    estudio = Estudio()

    # Latido 1: Iniciar lectura (duracion = L0 + L1*1 = 4 + 2 = 6 latidos)
    ctx1 = _crear_ctx(1, mem, bib=bib)
    estudio.reactiva(ctx1)
    assert mem.lectura_activa is not None
    reg = mem.lectura_activa
    assert reg.duracion_requerida == 6
    assert reg.latidos_dedicados == 0
    assert reg.estado == EstadoLectura.PENDIENTE
    assert any(c.carga["verbo"] == Verbo.LEER for c in ctx1.onda.acc("Ejecucion").values())

    # Simular ejecución sostenida de LEER durante 6 latidos
    ef_leer = {"Ejecucion": {"Ejecucion": Pieza("e1", "Ejecucion", 0.5, 0.5, carga={"verbo": Verbo.LEER})}}
    for lat in range(2, 8):
        ctx_lat = _crear_ctx(lat, mem, bib=bib, ef_anterior=ef_leer)
        estudio.reactiva(ctx_lat)

    # Al completar la duración de atención sostenida, la evidencia debe haberse aplicado
    assert mem.lectura_activa is None
    assert reg.estado == EstadoLectura.LEIDO
    assert reg.respuesta is not None
    # Confianza subió gracias a la autoridad
    assert p.confianza > 0.6
    assert "autoridad" in p.texto(8)


def test_estudio_interrupcion_por_alarma_no_aplica_evidencia():
    mem = Memoria()
    p = Proposicion("seta", Relacion.PELIGROSO, confianza=0.3)
    mem.saber[("seta", Relacion.PELIGROSO)] = p
    bib = BibliotecaFija({("seta", "PELIGROSO"): ("afirma", 0.95)})
    estudio = Estudio()

    # Latido 1: Inicia lectura
    ctx1 = _crear_ctx(1, mem, bib=bib)
    estudio.reactiva(ctx1)
    assert mem.lectura_activa is not None
    reg = mem.lectura_activa

    # Latido 2: Salta alarma con peligro alto
    ef_leer = {"Ejecucion": {"Ejecucion": Pieza("e1", "Ejecucion", 0.5, 0.5, carga={"verbo": Verbo.LEER})}}
    ctx2 = _crear_ctx(2, mem, bib=bib, ef_anterior=ef_leer, peligro=0.8)
    estudio.reactiva(ctx2)

    # La lectura debe quedar interrumpida y la proposición no haber recibido evidencia
    assert mem.lectura_activa is None
    assert reg.estado == EstadoLectura.INTERRUMPIDO
    assert p.confianza == 0.3
    assert "autoridad" not in p.texto(2)


def test_estudio_relectura_registro_interrumpido():
    mem = Memoria()
    p = Proposicion("baya", Relacion.NUTRITIVO, confianza=0.3)
    mem.saber[("baya", Relacion.NUTRITIVO)] = p
    bib = BibliotecaFija({("baya", "NUTRITIVO"): ("afirma", 0.9)})
    estudio = Estudio()

    # Latido 1: Inicia lectura
    ctx1 = _crear_ctx(1, mem, bib=bib)
    estudio.reactiva(ctx1)
    reg = mem.lectura_activa

    # Latido 2: Se interrumpe por acción distinta a LEER
    ef_mover = {"Ejecucion": {"Ejecucion": Pieza("e2", "Ejecucion", 0.5, 0.5, carga={"verbo": Verbo.MOVER})}}
    ctx2 = _crear_ctx(2, mem, bib=bib, ef_anterior=ef_mover)
    estudio.reactiva(ctx2)
    assert reg.estado == EstadoLectura.INTERRUMPIDO

    # Esperar que pase el cooldown (15 latidos)
    lat_reinicio = 2 + Estudio.COOLDOWN_LECTURA + 1
    ctx_reinicio = _crear_ctx(lat_reinicio, mem, bib=bib)
    estudio.reactiva(ctx_reinicio)
    assert mem.lectura_activa == reg
    assert reg.estado == EstadoLectura.PENDIENTE

    # Sostener lectura hasta el final
    ef_leer = {"Ejecucion": {"Ejecucion": Pieza("e1", "Ejecucion", 0.5, 0.5, carga={"verbo": Verbo.LEER})}}
    for lat in range(lat_reinicio + 1, lat_reinicio + reg.duracion_requerida + 2):
        ctx_lat = _crear_ctx(lat, mem, bib=bib, ef_anterior=ef_leer)
        estudio.reactiva(ctx_lat)
        if mem.lectura_activa is None:
            break

    assert reg.estado == EstadoLectura.LEIDO
    assert p.confianza > 0.6


def test_persistencia_tabla_lecturas():
    mem = Memoria()
    p = Proposicion("baya", Relacion.NUTRITIVO, confianza=0.3)
    mem.saber[("baya", Relacion.NUTRITIVO)] = p
    bib = BibliotecaFija({("baya", "NUTRITIVO"): ("afirma", 0.9)})
    estudio = Estudio()

    ctx = _crear_ctx(1, mem, bib=bib)
    estudio.reactiva(ctx)
    assert len(mem.lecturas) == 1

    with tempfile.TemporaryDirectory() as td:
        ruta_db = os.path.join(td, "memoria.db")
        pers = Persistencia(ruta_db)
        filas = pers.volcar(mem, "Individuo_1", 1)
        assert filas >= 1

        # Verificar que la tabla lecturas se escribió en sqlite
        cur = pers.conn.cursor()
        cur.execute("SELECT individuo, id, inicio, estado FROM lecturas")
        filas_lecturas = cur.fetchall()
        assert len(filas_lecturas) == 1
        assert filas_lecturas[0][0] == "Individuo_1"
        assert filas_lecturas[0][3] == "pendiente"
        pers.cerrar()
