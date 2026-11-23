# A6a: activaciones por registro y constantes de escala (D3, D15)

Rama `reorg/a6a-activaciones`, desde `origin/reorg/componentes` (`613d959`). Encargo: los generales que hoy se activan
con condiciones pasan a montarse porque el mundo los nombra (`Registro.opcionales`); lo propio de Crafter lo registra
Crafter con `añade`; las constantes de escala de los generales pasan a parámetros.

## Estado

| Etapa | Qué | Estado | Commit |
|---|---|---|---|
| E1 | Punto 5 (revisión) y mecanismo de opcionales con tests, sin uso | Hecha | `e9ddc83` |
| E2 | Opcionales y añadidos de Crafter, especificación | Hecha | `002c1d5` |
| E3 | Fuera las activaciones condicionales | Hecha | `6f37f49` |
| E4 | Constantes de escala | Hecha | ver `git log` |
| E5 | Herramienta, documentación y tests restantes | Pendiente | |

### Últimas comprobaciones (E4, 23/11/2026)

```
ruff check .          All checks passed!
mypy ida              Success: no issues found in 50 source files
pytest -q             334 passed, 1 warning
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

## Opcionales y añadidos de Crafter (E2)

- `opcional = True` en `Apetencia` (`ida/sistemas/s1.py`), `Amenaza` (`ida/sistemas/amenaza.py`), `Afrontar`
  (`ida/sistemas/s1.py`) y `Proteger` (`ida/sistemas/proteger.py`), en su sitio de hoy del montaje general.
- `Recinto` sale de `crear_s1` y `SalirDelRecinto` de `estrategias_s1`; Crafter los añade con `añade` y nombra los
  cuatro opcionales (`ida/mundos/crafter.py`, `registro`). Los importa de `ida/sistemas/proteger.py` hasta A6b.
- Especificación: los seis, `hoy_en = ["crafter"]`; sin `paso` (la herramienta exige quitarlo cuando `hoy` = `destino`).
  En `Recinto` y `SalirDelRecinto` la nota dice que su fichero pasa a Crafter en A6b. Mapa regenerado.
- Mundos de prueba que contaban con la activación condicional, ahora registran lo que tenían activo:
  `MundoErizos` (`tests/test_defensa.py`: Amenaza y Afrontar si no da su `peligro`), `MundoCueva`
  (`tests/test_proteger.py`: Recinto, SalirDelRecinto, Amenaza, Afrontar y Proteger) y `MundoDosNecesidades`
  (`tests/test_paso0.py`: Apetencia; su `Perfil.aliestesia` es True).
- Tests cuyo contenido era el montaje anterior, reescritos con la especificación (no relajados):
  `test_crafter_no_escribe_conducta` y `test_crafter_no_tiene_refugio_propio` comprobaban que Crafter no registra
  estrategias; ahora, que registra exactamente `SalirDelRecinto` en S1, sin `sustituye` (D16), y sigue la comprobación
  de que `ida/mundos/crafter.py` no define estrategias. `test_amenaza_va_antes_que_saliencia`: el mínimo ya no tiene
  Amenaza, y un mundo que la registra la tiene antes que Saliencia. `test_estrategia_sustituida_conserva_posicion...`:
  la referencia es el catálogo general sin los opcionales que el mínimo no registra.

## Activaciones condicionales retiradas (E3)

- `Perfil.aliestesia` (propiedad calculada: dos o más necesidades con el mismo rasgo) ya no existe. Antes de quitarla:
  True en Crafter y False en minimo, archivos, snake y ajedrez (salida del script del punto 5).
- La consultaban: `Apetencia.reactiva` (quitada la comprobación), `Alimentarse.elegible`, `paso` y `actuar` (ahora
  `ctx.registrado("Apetencia")`) y `Organismo._aprender` en `ida/core/latido.py`, que llama a `_aprender_satisface`
  (ahora `"Apetencia" in self.registrados`). Este último no estaba en el encargo; es la misma condición y sin él la
  propiedad no podía desaparecer.
- `Amenaza` ya no comprueba si alguna pieza trae `peligro`; siguen las condiciones de ubicación y entidades con posición
  y la marca `ctx.extra["peligro_aprendido"]`.
- Sin cambios: la comprobación de `Proteger` del impulso `cobijo`.
- Tests: `test_aliestesia_solo_con_un_rasgo_compartido...` pasa a `test_aliestesia_solo_donde_se_registra_apetencia`
  (Perfil sin la propiedad; el mínimo no monta Apetencia; el mundo de dos necesidades con el mismo rasgo, sí);
  `_ctx_juguete` pone `registrados = {"Apetencia"}` con las necesidades que comparten rasgo; el de Crafter comprueba
  `"Apetencia" in registro().opcionales`. Mapa: notas de `Alimentarse` y `Apetencia`.

## Constantes de escala (E4)

**Mecanismo (uno solo): `Perfil.escala`**, una `Escala` congelada (`ida/core/mundo.py`) con los valores de antes por
defecto. Crafter la fija explícitamente con los mismos valores (`ida/mundos/crafter.py`, su `perfil`; la salud son 9
puntos). Por qué el Perfil y no el registro: los opcionales se construyen en el montaje general sin argumentos (su
sitio no cambia), así que el registro no puede pasarles parámetros sin `sustituye`; y `Peligros`, que usa tres de ellas,
no es un Componente (vive en `Memoria`). `Peligros.escalar(e)` copia las de Amenaza; la llaman `Amenaza.reactiva` y
`Afrontar.evaluar` cada latido (sin depender de que la otra esté registrada). `Afrontar` lee `reserva` y la alostasis de
`Impulso`, `coste_sin_sitio`, de `ctx.perfil.escala`. Los nombres de módulo (`DANO_PREVIO`...) quedan como valores por
defecto. Test: `test_la_escala_del_perfil_llega_a_peligros` y `test_crafter_fija_la_escala_de_antes`
(`tests/test_defensa.py`).

Clasificación de las constantes de R0, sección E, de esos ficheros (las de `ida/core/peligro.py` están hoy en
`ida/sistemas/amenaza.py`):

| Fichero | Constante | Clase | Motivo |
|---|---|---|---|
| amenaza.py | `DANO_PREVIO` | de escala → `Escala.dano_previo` | fracción de la vida (2 de 9 puntos de salud de Crafter) |
| amenaza.py | `GOLPES_PREVIO` | de escala → `Escala.golpes_previo` | número de golpes |
| amenaza.py | `MARGEN_LUGAR` | de escala → `Escala.margen_lugar` | distancia en casillas |
| amenaza.py | `ESCALA` | de escala (derivada) | sale de `dano_previo`: `Peligros.c_escala`, con `constante_escala` |
| amenaza.py | `VITALIDAD_MAXIMA` | de diseño | escala interna del soma (0-100), igual en todos los mundos |
| amenaza.py | `PESO_PREVIO`, `PESO_TASA` | de diseño | pesos de los previos |
| amenaza.py | `VENTANA`, `MAX_RECORRIDOS`, `MAX_DERRIBOS` | de diseño | tamaños de búfer |
| amenaza.py | `EMISION_MINIMA`, `MARGEN_REDUCTOR`, `PELIGRO_PREVIO` | de diseño | proporciones internas |
| amenaza.py | `JUNTO_MINIMO`, `MINIMO_LEGADO` | de diseño | observaciones mínimas para decidir |
| amenaza.py | `TASA_PREVIA` (0,5) | **DUDA** | daños por latido de exposición sin datos. A favor de escala: depende del ritmo de ataque del mundo por latido. En contra: es un previo pesimista en [0, 1], como una probabilidad, que la experiencia corrige con peso 2. Se queda |
| s1.py | `RESERVA` | de escala → `Escala.reserva` | fracción de la vida (3 de 9) |
| s1.py | `ENCUENTROS_HABITUACION` | de diseño | velocidad de habituación (cuenta de experiencias) |
| s1.py | `HABITUACION_MAX`, `SENSIBILIZACION_MAX`, `SATISFACE_MIN`, `UMBRAL_MIEDO_REFERENCIA` | de diseño | proporciones internas |
| s1.py | `SEGURIDAD` | de diseño | nombre del impulso |
| s1.py | `VENTANA_TENDENCIA` (50) | **DUDA** | latidos de la media móvil de la tendencia. A favor de escala: con otro ritmo del mundo (latidos por día) 50 latidos son otra cosa. En contra: es una ventana de memoria del propio organismo, como `VENTANA`. Se queda |
| proteger.py | `COSTE_SIN_SITIO` | de escala → `Escala.coste_sin_sitio` | pasos; la usa la alostasis general (`Impulso`). Crafter la fija como `3 * ALCANCE_SITIO` |
| proteger.py | `MAX_INTERIOR`, `ALCANCE_SITIO`, `PROFUNDIDAD_PLAN`, `CANDIDATOS_EXACTOS`, `CADA_EVALUACION`, `MARGEN_SITIO`, `MARGEN_SITIO_MIN`, `BONO_HOGAR` | de Crafter | solo las usan `Recinto` y sus funciones (`planificar`, `recinto_actual`, `rutas`, `candidatos`, `completar`) |
| proteger.py | `MAX_ESTADOS`, `MAX_PASOS_POSTURA` | de Crafter | del buscador (`_bfs`, `buscar_postura`), que D16 lleva al cuerpo cuadrícula en A6b |
| proteger.py | `COBIJO` | de diseño | nombre de la necesidad que sirve `Proteger` |

Resumen: 6 de escala (5 parámetros de `Escala` y `ESCALA`, derivada), 18 de diseño, 10 de Crafter, 2 DUDAS
(`TASA_PREVIA`, `VENTANA_TENDENCIA`). `Proteger` y `SalirDelRecinto` no usan ninguna constante de módulo de escala.
D15 cita `ALCANCE_SITIO`, `MAX_INTERIOR`, `CANDIDATOS_EXACTOS` y `MAX_ESTADOS` entre las que pasan al Perfil; como son
de `Recinto` (de Crafter por D16), se quedan en su fichero, que pasa a Crafter en A6b.

Fuera de esta clasificación: las constantes de `ida/sistemas/comun.py`, `s2.py` y `s3.py` (p. ej. `MAX_RUTA_MAPA` y
`COSTE_RECORDADO` de `s3.py`, en pasos). El encargo pide las de «esos ficheros»; quedan para A6b o para la DUDA de
`PerseguirMetas`.

## Decisiones y desviaciones

- **`Recinto` no es el último de S1.Interpretar en Crafter hoy:** el cuerpo cuadrícula añade `MapaLocal` después
  (`ida/cuerpos/cuadricula/__init__.py:35`), y el cuerpo se monta antes que lo del mundo. Con `añade`, `Recinto` pasa
  de estar antes a estar después de `MapaLocal`. Sí es el último del montaje general (`crear_s1`). Se sigue porque
  `MapaLocal.activo` devuelve siempre False (`ida/cuerpos/cuadricula/mapa_local.py:26`: no corre en los barridos, no
  cuenta operaciones) y su `aprender` lo llama el Core aparte (`Organismo._aprender`, sin depender del orden del
  módulo; `_plasticidad` salta los del cuerpo). La equivalencia de E2 lo confirma (crafter: OK).
- `SalirDelRecinto` es la última de `estrategias_s1()` y Crafter no registra estrategias de S1: su posición no cambia.

## Pendientes

E5 (herramienta `conocimiento_mundo.py`, documentación). Las constantes de `comun.py`, `s2.py` y `s3.py` sin clasificar.
