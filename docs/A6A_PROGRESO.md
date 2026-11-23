# A6a: activaciones por registro y constantes de escala (D3, D15)

Rama `reorg/a6a-activaciones`, desde `origin/reorg/componentes` (`613d959`). Encargo: los generales que hoy se activan
con condiciones pasan a montarse porque el mundo los nombra (`Registro.opcionales`); lo propio de Crafter lo registra
Crafter con `añade`; las constantes de escala de los generales pasan a parámetros.

## Estado

| Etapa | Qué | Estado | Commit |
|---|---|---|---|
| E1 | Punto 5 (revisión) y mecanismo de opcionales con tests, sin uso | Hecha | ver `git log` |
| E2 | Opcionales y añadidos de Crafter, especificación | Pendiente | |
| E3 | Fuera las activaciones condicionales | Pendiente | |
| E4 | Constantes de escala | Pendiente | |
| E5 | Herramienta, documentación y tests restantes | Pendiente | |

### Últimas comprobaciones (E1, 23/11/2026)

```
ruff check .          All checks passed!
mypy ida              Success: no issues found in 50 source files
pytest -q             332 passed, 1 warning
equivalencia.py       minimo: OK · archivos: OK · crafter: OK · ajedrez: OK · EQUIVALENCIA: OK
```

## Punto 5: ¿lo que deja de montarse en los demás mundos hace algo?

Método: una vida instrumentada por mundo y semilla (1, 2 y 3; 400 latidos; `ejecutor.ejecutar`, `tabula_rasa`, reloj
de la Onda congelado como en `invariancia.py`), sin tocar `ida/`. Se envuelven `Amenaza.reactiva`,
`Apetencia.reactiva`, `Recinto.reactiva` y los métodos de `Afrontar`, `Proteger` y `SalirDelRecinto` (`elegible`,
`evaluar`, `paso`, `actuar`, `pedir`, `decidir`), y todos los métodos de `Azar` (`uniforme`, `ruido`, `eleccion`,
`probabilidad`, `derivar`) para contar los números pedidos mientras se ejecuta alguno de ellos. Script fuera del
repositorio (scratchpad, `punto5.py`); se reproduce con lo descrito.

| Mundo | Llamadas (semillas 1-3) | Pasan sus condiciones / producen algo | Números del Azar |
|---|---|---|---|
| minimo | Amenaza 400/400/400, Apetencia y Recinto ~380, Afrontar.elegible 233/195/138, SalirDelRecinto.elegible ~1000 | 0 | 0 |
| archivos | Amenaza 400/240/218, Apetencia y Recinto 380/232/216, Afrontar.elegible 4/6/1 | 0 | 0 |
| snake | Amenaza, Apetencia y Recinto 400/49/169, SalirDelRecinto.elegible 660/49/238 | 0 | 0 |
| ajedrez | Amenaza, Apetencia y Recinto 65/36/64, Afrontar.elegible 23/24/11 | 0 | 0 |
| crafter (control) | | Amenaza 216/400/197, Apetencia 203/153/7, Proteger.elegible 65/428/304, Afrontar.actuar 51 (s. 2) | — |

Por qué no hacen nada fuera de Crafter (código):
- `Apetencia` sale en su primera línea: `Perfil.aliestesia` es False en minimo, archivos, snake y ajedrez y True en
  Crafter (salida de la misma ejecución).
- `Amenaza` sale antes de escribir nada (no llega a `mem.peligros.aprender` ni a `peligro_aprendido`): ninguna vida
  la marcó.
- `Recinto` sale antes de escribir nada si `memoria.casillas` está vacía, y solo la llena `MapaLocal` (cuerpo
  cuadrícula, solo Crafter).
- `Afrontar.evaluar` deja `ctx.extra["afrontar"] = None`; `ctx` es nuevo en cada latido y solo lo lee `Afrontar`.
- `Proteger` y `SalirDelRecinto` no son elegibles sin la pieza `recinto`. Ninguna es `reflejo` ni `ultimo_recurso`,
  así que no entran en los otros caminos de `Estrategia._elegir`; la exploración (`azar.probabilidad`) solo corre con
  más de una disponible (`ida/sistemas/comun.py:285`), y estas nunca lo fueron.
- Estado compartido que sí cambia: `Onda.operaciones` (una por Componente activo en S1.Interpretar: `Apetencia` y
  `Recinto`). Solo cuenta con plazo lógico (`Onda.ms_transcurridos`, `ida/core/onda.py:160`), que solo usa
  `evaluar_crafter.py`; `invariancia.py` congela el reloj y no lo usa. No cobra amplitud (`control_vital(0)`).
  Los tiempos por Componente (`Onda.tiempos_ms`) pierden esas claves: telemetría, no conducta.

Conclusión: nada consume Azar ni escribe estado del que dependa la conducta. Se sigue.

## Mecanismo de opcionales (E1)

- `Componente.opcional` (`ida/core/arquitectura.py`) y `Definicion.opcional` (`ida/core/estrategia.py`), False por
  defecto. `Registro.opcionales: List[str]` (nombres de clase, `ida/core/mundo.py`). `Catalogo.quitar(nombre)`.
- `Organismo._montar_opcionales` (`ida/core/latido.py`): antes del cuerpo y del mundo, quita de cada módulo, de la
  preatención y de cada catálogo los opcionales cuya clase no está en `opcionales`, con el orden relativo de lo demás.
  Un nombre que no es un opcional del montaje general → `ValueError`.
- Tests: `tests/test_registro.py` (no nombrado se quita y deja el montaje igual al de base; nombrado queda en su sitio
  en módulo, preatención y catálogo compartido; nombre desconocido o no opcional → `ValueError`).

## Decisiones y desviaciones

- **`Recinto` no es el último de S1.Interpretar en Crafter hoy:** el cuerpo cuadrícula añade `MapaLocal` después
  (`ida/cuerpos/cuadricula/__init__.py:35`), y el cuerpo se monta antes que lo del mundo. Con `añade`, `Recinto` pasa
  de estar antes a estar después de `MapaLocal`. Sí es el último del montaje general (`crear_s1`). Se sigue porque
  `MapaLocal.activo` devuelve siempre False (`ida/cuerpos/cuadricula/mapa_local.py:26`: no corre en los barridos, no
  cuenta operaciones) y su `aprender` lo llama el Core aparte (`Organismo._aprender`, sin depender del orden del
  módulo; `_plasticidad` salta los del cuerpo). La equivalencia lo confirma (E2).
- `SalirDelRecinto` es la última de `estrategias_s1()` y Crafter no registra estrategias de S1: su posición no cambia.

## Pendientes

E2 a E5 (ver la tabla de estado).
