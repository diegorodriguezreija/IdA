"""Tests de Snake: detección de espacio libre, causa de muerte y aprendizaje tras morir."""

from unittest.mock import MagicMock

from ida.core.azar import Azar
from ida.core.latido import Organismo
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.vocabulario import Relacion
from ida.mundos.snake import ALTO, MundoSnake, espacio_libre
from ida.sistemas import crear_sistemas


def test_espacio_libre():
    # Desde (0, 0), encerrado por columna x=1
    encerrado = {(1, y) for y in range(ALTO)}
    libres = espacio_libre((0, 0), encerrado, limite=50)
    assert libres == ALTO

    # Fuera del tablero o sobre ocupada
    assert espacio_libre((-1, 0), set()) == 0
    assert espacio_libre((0, 0), {(0, 0)}) == 0


def test_causa_de_muerte():
    m = MundoSnake()
    # Dirección hacia el sur desde el borde inferior
    m.cabeza = (10, ALTO - 1)
    m.direccion = "S"
    assert m._causa() == "pared"

    # Dirección hacia su propio cuerpo
    m.cabeza = (5, 5)
    m.cuerpo = [(5, 5), (5, 6), (6, 6), (6, 5)]
    m.direccion = "S"
    assert m._causa() == "cuerpo"


def test_observacion_snake():
    m = MundoSnake()
    m._leer = MagicMock()
    m.cabeza = (10, 5)
    m.cuerpo = [(10, 5), (10, 4), (10, 3)]
    m.comida = (10, 7)
    m.direccion = "S"

    obs = m.observar()
    assert obs.ubicacion == "10_5"
    ent_comida = next(e for e in obs.entidades if e.clase == "comida")
    assert ent_comida.rasgos["nutritivo"] == 1.0

    # dir_N choca con su cuerpo (10, 4): como hay casillas seguras, no se ofrece como lugar
    assert not any(e.id == "dir_N" for e in obs.entidades)

    # dir_S acerca a la comida (10, 7)
    dir_s = next(e for e in obs.entidades if e.id == "dir_S")
    assert dir_s.clase == "casilla"
    assert dir_s.rasgos["nutritivo"] > 0.5


def test_aprender_de_la_muerte_snake():
    m = MundoSnake()
    m._leer = MagicMock()
    m.cabeza = (0, 0)
    m.cuerpo = [(0, 0), (1, 0), (2, 0)]
    m.direccion = "O"
    m._pagina = MagicMock()

    def choque():
        m.muerta = True
        m.causa_muerte = "pared"

    m._leer.side_effect = choque

    memoria = Memoria()
    org = Organismo(m, crear_sistemas(), Arquetipo(), memoria, Azar(1))
    vividos = org.vivir(10)

    assert vividos == 1
    assert not org.soma.esta_vivo
    # Comprobar que "pared" quedó demostrada como PELIGROSO por el trauma mortal
    prop = memoria.proposicion("pared", Relacion.PELIGROSO)
    assert prop is not None
    assert memoria.demostrada("pared", Relacion.PELIGROSO, org.ciclo)


def test_sin_salida_se_ofrecen_las_casillas_mortales():
    m = MundoSnake()
    m._leer = MagicMock()
    m.cabeza = (0, 0)
    m.cuerpo = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 2)]   # encerrada en la esquina
    m.comida = None
    lugares = [e for e in m.observar().entidades if e.rasgos.get("lugar")]
    assert lugares and all(e.rasgos["peligro"] == 1.0 for e in lugares)
    assert {e.clase for e in lugares} <= {"pared", "cuerpo"}


def test_causa_proyecta_varias_casillas():
    m = MundoSnake()
    m.cabeza = (10, ALTO - 3)
    m.cuerpo = [(10, ALTO - 3), (10, ALTO - 4), (10, ALTO - 5)]
    m.direccion = "S"
    assert m._causa() == "pared"
