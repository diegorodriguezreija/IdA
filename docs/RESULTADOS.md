# Resultados del framework base

> **Este documento recoge la línea base**: los mundos recién conectados. Después se optimizó el código de cada mundo (sin tocar el framework base); la comparación entre la base y la versión optimizada, en varias semillas, está en [`doc-repositorio/05_METRICAS_E_HITOS.md`](../doc-repositorio/05_METRICAS_E_HITOS.md).

Ejecuciones del 9 de noviembre de 2026, en Windows 10 y Python 3.15.1. Se cuentan tal como salieron. **No es un estudio:** son pocas vidas, casi siempre con una sola semilla, y sirven para ver que cada mundo funciona y cómo se comporta.

## Comprobaciones

- **Tests:** `python -m pytest tests/` → 56 correctos en unos 10 s en esta línea base; 58 tras la optimización y 64 con la observabilidad y el test de licencias (core, extremo a extremo con el mundo mínimo, repetibilidad con semilla, pureza de capas, y los cuatro mundos; los de Snake no usan la red).
- **Repetibilidad:** con la misma semilla, el mundo mínimo produce exactamente la misma vida (`tests/test_organismo.py`). Snake no es repetible: juega en una web en tiempo real. En esta línea base Crafter tampoco lo era entre procesos (se corrigió después; ver [`doc-repositorio/04`](../doc-repositorio/04_GUIA_TECNICA_Y_PATRONES.md)), así que sus cifras de abajo no se reproducen exactamente.
- **Guillotina:** con plazo 0 ms la cognición se corta y el Tribunal sigue decidiendo cada latido (test). En las ejecuciones de abajo no saltó ninguna guillotina: la cognición tarda alrededor de 1 ms por latido frente a plazos de 70 a 100 ms.

## Mundo mínimo: con y sin experiencia

```powershell
python -m ida --mundo minimo --latidos 400 --generaciones 4 --semilla 3 --tabula-rasa [--sin-experiencia]
```

| | G1 | G2 | G3 | G4 | Media de latidos | Setas tóxicas comidas |
|---|---|---|---|---|---|---|
| Con experiencia | 257 | 154 | 157 | 387 | **239** | 9 |
| Sin experiencia | 132 | 197 | 109 | 118 | **139** | 29 |

Con experiencia el individuo aprende pronto que la seta no nutre y que hace daño, deja de comerla y vive más. Es un **indicio** (una semilla, 4 vidas por grupo), no una demostración. Todos mueren antes de 400 latidos por el lobo, que está mal calibrado (demasiado letal).

## Archivos

```powershell
python -m ida --mundo archivos --latidos 400 --generaciones 4 --semilla 2 --tabula-rasa
```

Vidas de 167, 325, 307 y 289 latidos. Aprende qué especies nutren (`brote`, `Vaccinium_myrtillus`, `Taraxacum_officinale`…) y cuáles hacen daño (`Amanita_phalloides`, `Atropa_belladonna`, `Conium_maculatum`), duerme y vuelve al hogar. **Problema:** todavía da varios mordiscos a especies tóxicas a lo largo de la vida (hasta 7 de *Amanita* en G2); el freno de S3 no basta cuando aprieta el hambre. Pendiente de ajuste.

## Snake (playsnake.org, nivel pitón)

```powershell
python -m ida --mundo snake --latidos 1000 --generaciones 5 --tabula-rasa --opcion dificultad=piton
```

| Gen | Latidos | Puntos | Causa de muerte |
|---|---|---|---|
| 1 | 82 | 385 | pared |
| 2 | 25 | 40 | desconocida |
| 3 | 122 | 220 | desconocida |
| 4 | 100 | 310 | desconocida |
| 5 | 42 | 30 | cuerpo |

En una prueba anterior del mismo día, la mejor vida llegó a 620 puntos en 191 latidos. Aprende y hereda que la pared hace daño y que la comida nutre. **Problemas:** la causa sale «desconocida» cuando la serpiente avanza más de una casilla entre dos lecturas; y el afecto está casi siempre en PANICO porque paredes y cuerpo adyacentes cuentan como amenazas.

## Crafter

```powershell
python -m ida --mundo crafter --latidos 600 --generaciones 6 --semilla 42 --tabula-rasa
```

Vidas de 66 a 220 latidos (todas mueren por zombis, esqueletos o desgaste). Logros por vida: 3, 7, 5, 2, 10 y 9. En la población: `collect_wood` y `place_table` 100 %, `collect_drink` 83 %, `make_wood_pickaxe` y `eat_cow` 67 %, `collect_stone` y `place_stone` 50 %, `make_wood_sword` y `place_furnace` 33 %, `defeat_zombie` 17 %. Crafter Score de estas 6 vidas: **5,1 %**.

**No es comparable** con los resultados publicados del benchmark: IdA lee el estado simbólico del juego y no la imagen, el árbol tecnológico es un componente propio escrito a mano (`PlanTecnologico`), y son 6 episodios cortos frente a los episodios de hasta 10 000 pasos tras un millón de pasos de entrenamiento de los agentes de referencia.

## Ajedrez (rival local corregido, 5 partidas por dificultad)

```powershell
python -m ida --mundo ajedrez --latidos 200 --generaciones 5 --semilla 1 --tabula-rasa --opcion dificultad=N
```

| Rival | Victorias | Tablas | Derrotas |
|---|---|---|---|
| Dificultad 1 (1 ply) | 3 | 2 | 0 |
| Dificultad 2 (alfa-beta 2 ply) | 0 | 5 | 0 |
| Dificultad 3 (alfa-beta 3 ply) | 0 | 1 | 4 |

El sensor del mundo solo mira una respuesta del rival, así que IdA no ve combinaciones más largas. Contra la dificultad 1 empata dos partidas con una ventaja de material aplastante porque no sabe dar mate (solo lo ve cuando es mate en 1). Las tablas contra la dificultad 2 son por repetición.

## Pendiente para la fase de ajustes

Recogido en [`ESTADO_IMPLEMENTACION.md`](ESTADO_IMPLEMENTACION.md): letalidad del lobo, aversión insuficiente a las especies tóxicas en el mundo de archivos, causa «desconocida» y pánico constante en Snake, muertes tempranas en Crafter y finales de ajedrez.
