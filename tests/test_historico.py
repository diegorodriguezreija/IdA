"""Tests para el módulo de gestión histórica, cálculo de fitness y política de retención."""

from ida.historico import (
    aplicar_politica_retencion,
    calcular_fitness,
    rasgo_dominante,
)


def test_calcular_fitness_mundos():
    # Snake
    f_snake = calcular_fitness("snake", {"puntuacion": {"puntos": 100, "longitud": 15}, "latidos": 50})
    assert f_snake > 1000

    # Crafter
    f_crafter = calcular_fitness("crafter", {"puntuacion": {"n_logros": 5, "pasos": 200}, "latidos": 200})
    assert f_crafter == 5200.0

    # Ajedrez
    f_ajedrez_vic = calcular_fitness("ajedrez", {"puntuacion": {"resultado": "VICTORIA", "material": [10, 5], "jugadas": 30}})
    assert f_ajedrez_vic == 2000.0 + 5.0 * 50.0 + 30.0

    # Archivos
    f_archivos = calcular_fitness("archivos", {"puntuacion": {"comido": {"txt": 3, "log": 2}}, "latidos": 100})
    assert f_archivos == 5 * 50.0 + 100.0

    # Minimo
    f_minimo = calcular_fitness("minimo", {"puntuacion": {"bayas": 4, "setas": 2}, "latidos": 80})
    assert f_minimo == 4 * 20.0 + 2 * 5.0 + 80.0


def test_rasgo_dominante():
    arq = {"apertura": 0.3, "responsabilidad": 0.85, "neuroticismo": 0.4, "extraversion": 0.2, "umbral_miedo": 0.6}
    dom = rasgo_dominante(arq)
    assert dom["rasgo"] == "responsabilidad"
    assert dom["valor"] == 0.85


def test_retencion_bajo_limite():
    gens = [{"individuo": f"G_{i}", "fitness": float(i), "latidos": 10} for i in range(15)]
    ret = aplicar_politica_retencion("minimo", gens, max_total=20, top_k=5)
    assert len(ret) == 15


def test_retencion_politica_hibrida():
    # Creamos 30 generaciones
    gens = []
    for i in range(30):
        # Asignamos fitness variado: algunos antiguos tienen fitness alto
        f = float(i)
        if i == 2:
            f = 999.0  # Top 1 muy antiguo (G_2)
        elif i == 5:
            f = 888.0  # Top 2 muy antiguo (G_5)
        gens.append({
            "individuo": f"G_{i}",
            "fitness": f,
            "latidos": 10,
            "fijado": (i == 7),  # G_7 está fijado manualmente por el usuario
        })

    ret = aplicar_politica_retencion("minimo", gens, max_total=20, top_k=5)

    assert len(ret) == 20
    ids_retenidos = {g["individuo"] for g in ret}

    # Debe contener siempre al Top 1 y Top 2 antiguos
    assert "G_2" in ids_retenidos
    assert "G_5" in ids_retenidos

    # Debe contener siempre al fijado G_7
    assert "G_7" in ids_retenidos

    # Debe contener las generaciones más recientes (ej. G_29, G_28...)
    assert "G_29" in ids_retenidos
    assert "G_28" in ids_retenidos

    # Debe mantener el orden cronológico
    indices = [int(g["individuo"].split("_")[1]) for g in ret]
    assert indices == sorted(indices)
