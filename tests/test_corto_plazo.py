"""Tests para la memoria a corto plazo del organismo (decisión D13)."""

import pytest
from dataclasses import replace

from ida.core.azar import Azar
from ida.core.latido import Organismo
from ida.core.linaje import Arquetipo
from ida.core.memoria import Memoria
from ida.core.mundo import Perfil
from ida.mundos.minimo import MundoMinimo
from ida.sistemas import crear_sistemas


def test_perfil_defecto_corto_plazo():
    p = Perfil()
    assert p.corto_plazo == 8


def test_corto_plazo_en_contexto():
    from ida.core.arquitectura import Componente, Contexto

    vistos_en_ctx = []

    class LectorCortoPlazo(Componente):
        tipo = "Lector"

        def reactiva(self, ctx: Contexto) -> None:
            vistos_en_ctx.append((ctx.latido, len(ctx.corto_plazo), ctx.corto_plazo))

    mundo = MundoMinimo()
    mundo.reiniciar(1)
    mundo.perfil = replace(mundo.perfil, corto_plazo=3)

    azar = Azar(1)
    sistemas = crear_sistemas()
    # Inyectamos el componente lector en S1.Sentir
    sistemas[0].modulo("Sentir").componentes.append(LectorCortoPlazo())

    org = Organismo(mundo, sistemas, Arquetipo.nuevo(azar), Memoria(mundo.perfil.memoria), azar)
    org.vivir(5)

    assert len(vistos_en_ctx) == 5
    # En latido 1, aún no hay ninguna onda cerrada previa
    assert vistos_en_ctx[0][1] == 0
    # En latido 2, hay 1 onda cerrada previa (la del latido 1)
    assert vistos_en_ctx[1][1] == 1
    # En latido 3, hay 2 ondas
    assert vistos_en_ctx[2][1] == 2
    # En latido 4, hay 3 ondas (tamaño máximo N=3)
    assert vistos_en_ctx[3][1] == 3
    # En latido 5, sigue habiendo 3 ondas
    assert vistos_en_ctx[4][1] == 3
    # Comprobar inmutabilidad en Contexto
    assert isinstance(vistos_en_ctx[4][2], tuple)

    p = Perfil()
    assert p.corto_plazo == 8


def test_corto_plazo_tamano_y_orden():
    mundo = MundoMinimo()
    mundo.reiniciar(42)
    # Fijamos N = 4 para probar el desbordamiento de la cola rápidamente
    mundo.perfil = replace(mundo.perfil, corto_plazo=4)

    azar = Azar(42)
    org = Organismo(mundo, crear_sistemas(), Arquetipo.nuevo(azar), Memoria(mundo.perfil.memoria), azar)

    assert org.corto_plazo == ()

    latidos_vistos = []

    def anotar(o, onda):
        # En el momento de ejecutar la onda, ctx.corto_plazo contiene las ondas cerradas previas
        # Obtenemos el ciclo de cada onda cerrada en corto_plazo a través de su pieza de acción
        ciclos_cp = [
            ef["Accion"]["Accion"].actualizada
            for ef in o.corto_plazo
            if "Accion" in ef and "Accion" in ef["Accion"]
        ]
        latidos_vistos.append((o.ciclo, tuple(ciclos_cp)))

    org.vivir(10, al_latir=anotar)

    # 1. Comprobar longitud y orden latido a latido
    for ciclo, cp in latidos_vistos:
        esperado_len = min(ciclo, 4)
        assert len(cp) == esperado_len
        if esperado_len > 0:
            # Orden estricto de la más antigua a la más reciente
            esperados_ciclos = tuple(range(max(1, ciclo - 4 + 1), ciclo + 1))
            assert cp == esperados_ciclos

    # 2. Tamaño máximo alcanzado
    assert len(org.corto_plazo) == 4

    # 3. Inmutabilidad de la secuencia y de los mapeos
    with pytest.raises(TypeError):
        org.corto_plazo[0] = {}  # type: ignore[index]

    ef0 = org.corto_plazo[0]
    with pytest.raises(TypeError):
        ef0["Accion"] = {}  # type: ignore[index]

    # 4. Cada pieza contiene lo mínimo que la identifica: tipo, id, arousal y carga
    for ef in org.corto_plazo:
        for _canal, piezas in ef.items():
            for p_id, pieza in piezas.items():
                assert hasattr(pieza, "tipo")
                assert hasattr(pieza, "id")
                assert hasattr(pieza, "arousal")
                assert hasattr(pieza, "carga")
                assert pieza.id == p_id
