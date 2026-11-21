# Método de medición: guillotina lógica y comparación pareada

Rama `feature/metodo`, sobre `f26c243` (`crafter-general-v2`). Fecha: 21/11/2026. Resuelve la deuda 13 (`docs/DEUDA_TECNICA_CRAFTER.md`).

## 1. Guillotina lógica

### Qué cambia

- `Onda` acepta `ops_por_ms` (`ida/core/onda.py`). Con él, `ms_transcurridos()` devuelve `operaciones / ops_por_ms` en lugar del reloj de pared, y `control_vital` corta cuando las operaciones superan `frecuencia_ms × ops_por_ms`.
- `Organismo.ops_por_ms` (`ida/core/latido.py`, por defecto `None`) se pasa a cada Onda.
- `evaluar_crafter.py --plazo-logico OPS` lo enciende. También lo aceptan `diagnostico_logros.py`, `diagnostico_paso3.py`, `diagnostico_proteger.py` y `diagnostico_sitio.py`, que llaman a `evaluar`. El JSON guarda `plazo_logico` (`null` con reloj).
- Sin la opción, la guillotina sigue cortando por reloj. El único cambio en ese camino es que `control_vital` suma 1 a un contador.

### Unidad: la operación

Una operación es una llamada a `Onda.control_vital` fuera del Core exento. Ocurre al entrar en cada sistema (`latido.py`), en el turno de cada componente (`Modulo.ejecutar`, `arquitectura.py`) y al cobrar cada pieza (`Onda._cobrar`). Es la unidad natural del núcleo porque la guillotina es cooperativa y esos son los únicos puntos donde puede cortar. No depende del mundo: cuenta lo mismo en mínimo, archivos, Crafter y ajedrez. El plazo sigue escalando con la frecuencia que fija el marcapasos (con peligro, hasta un 30 % menos).

**Límite:** la operación no ve el trabajo dentro de un componente (por ejemplo, una búsqueda del planificador). Por eso el plazo lógico no reproduce *qué* latidos cortaría el reloj, solo que con la máquina libre casi no se corta ninguno.

### Calibración

Script de calibración (fuera del repositorio) que registra en cada latido las operaciones, el plazo y los ms de cognición. 3000 pasos, semilla 31, vista oficial, sin herencia, manual estricto, sin estrategias propias, reloj:

| Medida | Valor |
|---|---|
| Latidos (despiertos) | 3000 (2754) |
| Latidos cortados por reloj | 0 |
| Operaciones por latido: mediana, p99, máximo | 157, 170, 172 |
| Operaciones por ms de plazo: máximo | 2,40 |
| ms de cognición por latido: media, máximo | 3,6, 31,95 |
| Operaciones por ms de reloj (total) | 40,54 |

Los cinco latidos más lentos (22-32 ms) tienen entre 141 y 169 operaciones, como uno normal.

**Valor elegido: 40 operaciones por ms**, la velocidad de esta máquina. Un plazo de 100 ms son 4000 operaciones y uno de 70 ms (peligro máximo), 2800, frente a un máximo observado de 172. Con la máquina libre no corta, igual que el reloj (D1, D2 y D3: 0 latidos cortados; F1, F2 y D4: 4, 6 y 1 de unos 100 000, `docs/MEDICION_PASO6.md`).

### Comprobaciones

Comando base: `.venv\Scripts\python.exe herramientas\evaluar_crafter.py --pasos 3000 --semilla 31 --sin-herencia --sin-estrategias-propias --quiet`. Datos en `datos/evaluacion/metodo_*.json`. La comparación ignora `tiempo_segundos`, `ms_por_paso` y `plazo_logico`.

| Prueba | Ficheros | Latidos cortados | Score (%) | Campos distintos |
|---|---|---|---|---|
| Reloj frente a lógico (40), máquina libre, una a una | `metodo_reloj`, `metodo_logico40` | 0 y 0 | 16,91 y 16,91 | ninguno |
| Lógico (40), cuatro ejecuciones a la vez | `metodo_carga40_a`, `metodo_carga40_b` | 0 y 0 | 16,91 y 16,91 | ninguno (y ninguno frente a `metodo_reloj`) |
| Lógico (2, plazo estrecho que corta), las mismas cuatro a la vez | `metodo_carga2_a`, `metodo_carga2_b` | 581 y 581 (11 episodios) | 9,80 y 9,80 | ninguno |

En la prueba de carga corrieron cuatro evaluaciones a la vez (las dos de 40 y las dos de 2): 11,77-12,47 ms por paso, frente a 10,55 y 10,60 una a una. El plazo de 2 op/ms sirve para comprobar que, cuando el plazo lógico corta, corta los mismos latidos en las dos ejecuciones.

Invariancia (`herramientas/invariancia.py`): OK en mínimo, archivos, Crafter y ajedrez.

## 2. Comparación pareada

`resumen_evaluacion.py --pareada A.json B.json` (función `comparar_pareado`):

- Exige la misma `semilla_base`. El episodio i se juega en el mismo mundo en las dos evaluaciones, porque su semilla solo depende de i (`azar.derivar(i)` en `evaluar_crafter.py`).
- Empareja los primeros min(n1, n2) episodios.
- Da la diferencia A − B de la Score y de cada logro, en puntos, con su IC 95 % por bootstrap pareado: 2000 réplicas que remuestrean índices de episodio con reemplazo y usan el mismo índice en A y en B (semilla del bootstrap 42).

**Qué guardaban los JSON.** Ninguno de los medidos hasta ahora guarda los logros por episodio. Guardan `pasos`, `episodios`, `tiempo_segundos`, `ms_por_paso`, `score`, `score_ci_95`, `tasas_logros` (agregadas), `causas_muerte` (agregadas), la configuración y `latidos_cortados_por_episodio`. Desde esta rama `evaluar_crafter.py` añade `por_episodio`: pasos, causa de muerte, si sigue vivo y los logros de cada episodio.

**Reanálisis pedido (D2 frente a F1, D3 frente a F2, F1 frente a C1, C1 frente a G1): no se puede hacer** con los JSON actuales (`paso6_D2`, `paso3_F1`, `paso6_D3`, `paso3_F2`, `cierre0_C1`, `paso5_G1`: ninguno tiene `por_episodio`). La herramienta lo rechaza y lista lo que guarda el fichero. Para hacerlo hay que volver a medir cada condición en su commit con `por_episodio`, mejor con `--plazo-logico 40`.

## 3. Referencia

Medición de la referencia oficial de Crafter (100 000 pasos, vista oficial, sin herencia, manual estricto) con guillotina lógica (`--plazo-logico 40`) para fijar la línea base reproducible con `por_episodio`:

| ID | Semilla | Fichero | Episodios | Score (%) | IC 95 % (%) | Latidos cortados |
|---|---|---|---|---|---|---|
| B31 | 31 | `datos/evaluacion/base_v2_31.json` | 383 | 14,04 | [12,92, 15,06] | 0 |
| B32 | 32 | `datos/evaluacion/base_v2_32.json` | 365 | 15,45 | [14,18, 16,53] | 0 |

**Comparación con D2 y D3 (reloj, paso 6):**
- B31 frente a D2 (`datos/evaluacion/paso6_D2.json`): todos los campos son idénticos, ignorando `tiempo_segundos`, `ms_por_paso`, `plazo_logico`, `mecanismos`, `sin_estrategias_propias` y `por_episodio`.
- B32 frente a D3 (`datos/evaluacion/paso6_D3.json`): todos los campos son idénticos, ignorando los mismos campos.

