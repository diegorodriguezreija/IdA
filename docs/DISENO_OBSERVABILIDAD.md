# Diseño de la observabilidad y la experiencia de usuario de IdA

> Estado: **aprobado por el autor** (26/11/2026). Base: `main` en `crafter-general-v5.1`.
> Este documento manda sobre la telemetría, la antesala, el Vivero, el Laboratorio y la grabación.
> El diseño del organismo sigue mandado por [`DISENO_COMPONENTES.md`](DISENO_COMPONENTES.md): nada de lo que aquí se
> decide puede cambiar la conducta de IdA.

## 1. Objetivos

1. **Entender IdA.** Que el autor y quien se interese por el proyecto vean cómo funciona: el flujo de la Onda por el
   latido, los sistemas, los Componentes, qué sabe IdA y de dónde lo sabe. Cinco miradas: analítica, de ingeniería,
   epistemológica, neurocientífica y biológica.
2. **Probar IdA sin esfuerzo.** Que un usuario casual con Python configure y vea vivir a IdA en cualquier mundo, en su PC,
   con una interfaz moderna y atractiva («tamagotchi»): sus indicadores, sus aprendizajes y cómo evoluciona su estirpe.
3. **Reutilizar lo que ya funciona** y evolucionarlo.

## 2. Lo que hay y qué se hace con ello

| Hoy | Qué se hace |
|---|---|
| `python -m ida` abre la antesala; servidor de la biblioteca estándar (`ida/telemetria/servidor.py`), sin dependencias | **Se mantiene** la forma de arrancar y la ausencia de dependencias. El servidor se reorganiza con una API versionada (O14) |
| Antesala (`antesala.html`): mundo, opciones, arquetipo con presets y deslizadores, semilla, generaciones, tabula rasa, OTel | **Se reutiliza su contenido**; las opciones de cada mundo dejan de estar escritas a mano (O8) |
| Panel (`panel.html`): carácter, Onda, cuerpo y química, latido y rendimiento, tribunal, memoria, linaje, ficha de individuo con descarga y restauración | **Se reparte**: lo vital va al Vivero; lo cognitivo y lo técnico, al Laboratorio. La ficha de individuo es la base de la colección (O10) |
| Resumen del latido montado a mano en `consola.py` y ampliado en `ejecutor.py` | **Se sustituye** por el registro del latido v1 (O2). La consola lo usa también |
| OTel (`ida/telemetria/otel.py`) y la pila de `infra/` (Grafana, Jaeger, Prometheus) | **Se mantiene** para ingeniería; se alimenta del registro (O15) |
| `vista()` de texto en cada mundo; Snake y Crafter solo se ven en su propia ventana | **Se añade** `escena()` estructurada (O6); `vista()` queda para la consola |
| `componentes.toml` con destino, decisión, preatentivo y plasticidad de cada Componente | **Se amplía** con su análogo biológico y una descripción en los dos idiomas (O13) |
| La Onda ya registra autoría de cada pieza (`origen`, `registro`), tiempos por Componente, fases, notas y consumo por sistema | **Se aprovecha**: es la materia prima del Laboratorio |

## 3. Decisiones

| Id | Decisión |
|---|---|
| **O1** | **Tres superficies y una para ingeniería.** **Antesala / Lobby**: configurar y lanzar. **Vivero / Nursery**: la vista casual y la colección. **Laboratorio / Lab**: la vista experta. Grafana y Jaeger siguen para ingeniería. Se pasa de una a otra sin salir de la aplicación |
| **O2** | **Una sola fuente de datos: el registro del latido.** Un *observador* lee el organismo al final de cada latido y produce un registro con esquema versionado (sección 4). Ninguna vista lee el organismo directamente. La consola, el directo, la grabación y OTel consumen el mismo registro |
| **O3** | **El observador no cambia la conducta.** Solo lee. `herramientas/invariancia.py` debe dar lo mismo con el observador encendido y apagado, y la equivalencia sigue en OK. El ritmo visible (pausa, ×1, ×4, máximo) se aplica *entre* latidos y fuera del organismo; en los mundos de tiempo real (Snake) lo marca el mundo |
| **O4** | **Tres niveles de detalle.** *Vital* (cuerpo, ánimo, necesidades, acción, Score, logros, hechos), *cognitivo* (piezas por canal con su autoría, flujo entre sistemas, tribunal y candidatos, consumo de amplitud y potencia, estrategias) y *completo* (tiempos por Componente, fases, todas las piezas con su registro). Cada nivel incluye al anterior |
| **O5** | **Hechos estructurados, no frases.** Lo que pasa en la vida se registra como hechos con tipo y parámetros (sección 5), y la interfaz forma la frase en el idioma elegido. El observador deduce los hechos comparando el estado entre latidos (proposiciones nuevas o que cambian de estado, logros, muerte...): **no se toca el motor**. Las frases de la consola actual se mantienen |
| **O6** | **`escena()`: el mundo se describe, la interfaz lo dibuja.** Contrato nuevo de `Mundo`: una descripción estructurada de lo que se ve (sección 6). La implementan los cinco mundos. Por defecto devuelve `None` y la interfaz enseña `vista()` |
| **O7** | **Grabación.** Cada vida se puede grabar en `.jsonl.gz`: una cabecera (versión del esquema, commit, mundo, opciones, semilla, arquetipo, plazo, nivel) y un registro por línea. Por defecto, nivel *cognitivo*; *completo* a petición. El Laboratorio reproduce, rebobina y compara grabaciones |
| **O8** | **Cada mundo declara sus opciones.** Nombre, tipo, rango o valores, valor por defecto y etiqueta y ayuda en es/en. La antesala construye el formulario. Las opciones actuales se conservan y se añaden las de la sección 8. **El valor por defecto de cada opción es el que da más Score de base**: el de la medición oficial donde la hay (en Crafter, la de D17) o, si no, el comportamiento de hoy. Así lo que el usuario lanza sin tocar nada es lo mejor que IdA sabe hacer, y coincide con lo medido. Una opción nueva solo cambia ese valor si una medición demuestra que da más Score |
| **O9** | **Vivero: un compañero por mundo y una colección.** En cada mundo, un individuo es *tu compañero*: el Vivero se abre con él, su estado, su diario y su estirpe. El resto de individuos guardados forma la *colección*, con un ranking por mundo (mejor Score) y la opción de hacer compañero a cualquiera. Se ajustará cuando el autor lo vea funcionando |
| **O10** | **Ficha de individuo v1.** JSON con arquetipo, legado, historial de vidas, mejor Score, logros, mundo y fecha. Compatible con la descarga de hoy (se pueden importar las fichas antiguas). Guardar crea la ficha en `datos/vivero/`; *adoptar* (cargar una ficha propia o recibida) empieza una vida nueva con su legado |
| **O11** | **Vidas reproducibles por defecto.** Lo que se lanza desde la antesala usa plazo lógico (`ops_por_ms` = 40, como D17), salvo en los mundos de tiempo real. Con la misma ficha, opciones y semilla, la vida es la misma, y una grabación puede regenerarse |
| **O12** | **Frontal sin compilación.** JavaScript moderno con módulos ES, Web Components y SVG o Canvas. Sin Node ni npm. Las bibliotecas copiadas van en `ida/telemetria/web/vendor/`, solo con licencia MIT, BSD o Apache, cada una en `NOTICE` con su versión. Funciona sin conexión |
| **O13** | **El Laboratorio se alimenta del diseño.** `componentes.toml` gana dos campos opcionales: `analogo` (correspondencia biológica: interocepción, saliencia, aliestesia, traza de elegibilidad...) y `descripcion` en es/en. El Laboratorio los lee; el mapa de Componentes del Laboratorio sale de la misma fuente que los diagramas 06 y 07 |
| **O14** | **Servidor.** Solo biblioteca estándar, escucha solo en `127.0.0.1`. API REST versionada (`/api/v1/...`) y SSE para el directo. Sirve los ficheros estáticos de `ida/telemetria/web/` |
| **O15** | **OTel se alimenta del registro.** Las mismas métricas y trazas de hoy, sacadas del registro del latido. Sigue siendo un extra (`[observabilidad]`) |
| **O16** | **Idiomas.** Español e inglés desde el principio. Por defecto el del navegador (`navigator.language`; si no es español, inglés), con selector siempre visible y la elección recordada. Textos en `web/i18n/es.json` y `en.json`; un test comprueba que los dos tienen las mismas claves |
| **O17** | **Mundos instalables desde la antesala.** La antesala muestra el estado de cada mundo (listo / no instalado). «Instalar» ejecuta `pip install -e ".[<extra>]"` con el Python del propio entorno de IdA (y `playwright install chromium` para Snake), con la salida en pantalla. Solo extras conocidos de `pyproject.toml`, nunca texto libre. Nuevo extra `[todos]` para instalarlo todo |
| **O18** | **Pruebas.** Validación del esquema del registro (biblioteca estándar), invariancia con observador, paridad de claves de idioma, que cada mundo declare opciones válidas y que `escena()` cumpla su contrato. Las vistas se revisan a mano con una lista de comprobación por fase |

## 4. Registro del latido v1

Fijado en T1 (26/11/2026). Lo produce `Observador(nivel).registrar(org, onda)` (`ida/telemetria/observador.py`) al
final de cada latido; el esquema y su validador, con la biblioteca estándar, están en `ida/telemetria/esquema.py`
(`ESQUEMA`, `HECHOS`, `validar`). Cada nivel incluye al anterior. Las versiones futuras solo **añaden** campos (el
validador de v1 acepta campos que no conoce); quitar o renombrar exige `v: 2` y un conversor de las grabaciones antiguas.

**Siempre.** `v` (1), `nivel`, `latido`, `vida` (número de vida en la ejecución, desde 1), `generacion`, `individuo`,
`mundo`, `con_experiencia`.

**Nivel vital.**

| Campo | Contenido | De dónde sale |
|---|---|---|
| `ritmo` | `ms`, `ms_total` (lógicos con plazo lógico, de reloj sin él), `plazo_ms`, `amplitud` [consumida, máxima], `potencia` [consumida, máxima], `guillotina` (motivo o vacío), `logico` | `Onda`, `onda.notas` |
| `cuerpo` | `vitalidad`, `alimentacion`, `energia`, `descanso`, `dormido`, `cargando`, `vivo` | `Soma.valores()` |
| `quimica` | `dopamina`, `placer`, `estres` | `Soma.valores()` |
| `afecto` | `estado` (CALMA, CURIOSIDAD, ALERTA...), `valencia`, `indicadores` (peligro, tensión, calma) | `Soma` |
| `necesidades` | `[{nombre, deficit}]` de cada necesidad declarada | `Perfil.necesidades`, `Necesidad.deficit` |
| `accion` | `verbo`, `objetivo`, `clase`, `sistema`, `exito`, `mensaje`, `motivo` y, si viene de una, `estrategia`; `null` si no hubo | `ef["Accion"]` |
| `score` | `puntuacion` (el diccionario del mundo) y `logros` (su lista `logros`, si la tiene) | `Mundo.puntuacion()` |
| `hechos` | lista de hechos del latido (sección 5) | deducidos |
| `experiencia` | `aprendizaje`, `expectativa`, `cambio_decision`, `episodio`: las frases de la consola de siempre (O5) | `onda.notas` |
| `memoria` | `aciertos`, `sorpresas`, `episodios`, `demostradas`, `hipotesis`, `refutadas`, `recuerdos`, `heredados` | `Memoria` |
| `contadores` | los del organismo (miedo, calma, hambre, guillotinas, dormido...) | `Organismo.contadores` |
| `arquetipo` | los cinco rasgos | `Arquetipo` |
| `vista` | la vista de texto del mundo | `Mundo.vista()` |
| `escena` | la escena estructurada (sección 6), **solo cuando cambia** respecto a la del latido anterior de la misma vida; falta si el mundo no la da o no ha cambiado | `Mundo.escena()` |

**Nivel cognitivo.**

| Campo | Contenido |
|---|---|
| `onda.canales` | por canal, cuántas piezas hay en `ev`, `acc` y `ef` |
| `onda.piezas` | las piezas de `ev` y `acc`: `id`, `canal`, `fase`, `tipo`, `arousal`, `confianza`, `origen` (autoría, `Pieza.origen`), `sistema` |
| `onda.flujo` | `[{pieza, de, a, op}]`: cada pieza que otro Componente modificó en este latido (de su autor a quien la tocó, según `Pieza.registro`) y cada pieza formada a partir de otra (`entradas`, `op: "entrada"`) |
| `onda.consumo`, `onda.restante` | gasto, rechazos y recortes de amplitud y potencia por sistema; lo que quedaba al entrar en cada sistema |
| `onda.operaciones`, `onda.guillotina`, `onda.excepciones` | operaciones del plazo lógico, si saltó la guillotina, usos de excepciones a la propiedad |
| `tribunal` | `ganador` (`id` del candidato y `sistema`), `candidatos` (los 8 primeros, con `base`, `activa`, `proactiva`, `plus` y `total`), `cambio_experiencia`, `plus_decide` |
| `estrategias` | `activas` (`id`, `sistema`, `nombre`) y `por_sistema` (lo que anota cada sistema: activas, ejecutada, abandonos, reflejo...) |
| `saber` | las 20 proposiciones de más confianza: `sujeto`, `relacion`, `estado` (`hipotesis`, `demostrada`, `refutada`), `confianza`, `heredada`, `autoridad` |

**Nivel completo.** `tiempos_ms` (cada Componente), `fases` (`[nombre, inicio_ms, fin_ms]` desde el inicio del latido),
`piezas` (todas las de `ef`, con `creada`, `actualizada`, `entradas`, `carga` y su `registro`) y `saber` entero.

**Campos de tiempo** (`esquema.CAMPOS_TIEMPO`): `ritmo.ms`, `ritmo.ms_total`, `tiempos_ms` y `fases`. Son los únicos que
pueden cambiar entre dos grabaciones de la misma vida con plazo lógico (con plazo de reloj, `ritmo.ms` y
`ritmo.ms_total` también son de reloj).

**Lectura sin efectos.** El observador solo lee atributos y métodos de consulta. Una excepción, revisada con el autor
en T1: en Crafter `vista()` llama a `_cosas()`, que asigna un id a cada criatura vista por primera vez. Entre el final
del latido y el `observar()` siguiente (que también empieza por `_cosas()`) el entorno no avanza, así que asigna los
mismos ids en el mismo orden. `herramientas/invariancia.py --observador completo` da OK en los cuatro mundos.

**Grabación** (O7, `ida/telemetria/grabacion.py`). `.jsonl.gz`: una cabecera (`formato`, `esquema`, `commit` de
`git rev-parse HEAD` con `+cambios` si los hay, `mundo`, `opciones`, `semilla`, `arquetipo`, `latidos`,
`generaciones`, `plazo_logico`, `nivel`, `sin_experiencia`, `creada`) y un registro por línea. Se graba con
`python -m ida --mundo M --grabar RUTA [--nivel vital|cognitivo|completo] [--plazo-logico OPS]`; por defecto, nivel
cognitivo. El lector (`leer`, `iterar`) rehace la secuencia y `comparar` compara dos grabaciones sin los campos de tiempo.

**Consumidores.** La consola forma su línea desde el registro (`ida/consola.py`, la misma salida byte a byte). El panel,
la antesala y OTel reciben, hasta T6, la forma de antes por la capa `ida/telemetria/compat.py` (`a_panel`). Lo lanzado
desde la antesala usa plazo lógico 40 (O11) salvo en los mundos cuyo `Perfil.tiempo_real` es verdadero (Snake), y nivel
completo (el panel enseña los tiempos por Componente).

## 5. Catálogo de hechos v1

Los deduce `ida/telemetria/hechos.py` comparando el estado al final de cada latido con el del anterior; no se toca el
motor. Lo que el individuo ya trae al nacer (manual, herencia) es la línea de partida y no cuenta como aprendido.

| Tipo | Parámetros | Cuándo | Ejemplo de frase (es) |
|---|---|---|---|
| `nace` | `individuo`, `generacion`, `heredados` | primer latido de un organismo | «Nace Crafter_G2, generación 2, con 14 recuerdos heredados» |
| `primera_vez` | `verbo`, `clase` | primera acción con éxito de ese verbo sobre esa clase en la vida | «Por primera vez: come una vaca» |
| `aprende` | `saber: "proposicion"`, `clase`, `relacion`, `estado`, `fuente`, `confianza` | una proposición nueva, que pasa a demostrada o que vuelve de refutada | «Ha aprendido que el agua nutre» |
| `aprende` | `saber: "requisito"`, `verbo`, `clase`, `requiere`, `cerca`, `efecto`, `confirmado`, `fuente`, `confianza` | un requisito nuevo, que cambia lo que pide o produce, o que se cumple por primera vez (sección «requisitos») | «Ha aprendido que la mesa necesita madera» |
| `duda` | `clase`, `relacion`, `confianza` | una proposición demostrada vuelve a hipótesis | «Ya no está segura de que la seta nutra» |
| `refuta` | `clase`, `relacion`, `confianza` | una proposición pasa a refutada | «Ya no cree que el agua quite el hambre» |
| `sorpresa` | `origen: "expectativa"`, `verbo`, `clase`, `esperado`, `obtenido`, `rpe` | pieza `Sorpresa` de la expectativa (lo esperado es la expectativa que quedó al final del latido anterior) | «Esperaba ganar y perdió: sorpresa» |
| `sorpresa` | `origen: "modelo"`, `sistema`, `clase`, `error` | pieza `Sorpresa` del modelo de transiciones (F1) | «Lo de la vaca no salió como preveía» |
| `logro` | `nombre` (del mundo) | logro nuevo en `score.logros` | «Logro: colocar una mesa» |
| `peligro` | `clase`, `estado`, `dano`, `confianza` | con cada `aprende` de «hace daño»; `dano` es el daño esperado de un encuentro según la sección «peligros», si la hay | «Ha aprendido a temer al zombi» |
| `estrategia` | `sistema`, `nombre`, `cambio` (`inicio` o `fin`) y, al terminar, `estado` | una estrategia entra en las activas o sale | «Cambia de plan: buscar refugio» |
| `duerme` | — | el cuerpo pasa a dormido | «Se duerme» |
| `despierta` | `motivo` (`alarma`, `descansado` o vacío) | el cuerpo deja de estar dormido | «Despierta por una alarma» |
| `muere` | `causa`, `latidos`, `puntuacion` | la vitalidad llega a cero (la causa es la del Core) | «Muere de hambre tras 812 latidos» |

**Fuera de v1** (no se deducen sin tocar el motor, o se dejan para más adelante):

- Lo que se aprende de la acción que mató (`Organismo._aprender_de_la_muerte`) ocurre después del último latido
  observado: no da hechos (tampoco sale hoy en la consola).
- Las proposiciones olvidadas al dormir (olvido, reducción nocturna) no dan hecho: el catálogo no tiene `olvida`.
- Los recuerdos agregados verbo × clase (`Memoria.registros`) cambian casi en cada acción: no dan `aprende`.
- `duerme` no lleva la causa (sueño elegido o forzado por agotamiento): el Core no la deja en la Onda de forma
  estructurada.

## 6. Contratos de `escena()` y de las opciones (v1)

Fijados en T2a (26/11/2026). El código de cada contrato: `Mundo.escena()` y `Mundo.opciones()` en
`ida/nucleo/mundo.py`; el esquema y el validador de la escena en `ida/telemetria/esquema.py` (`ESCENAS`,
`validar_escena`); el formato y la validación de las opciones en `ida/mundos/opciones.py`.

### 6.1 `escena()` (O6)

`Mundo.escena()` devuelve un diccionario o `None` (por defecto, `None`: la interfaz enseña `vista()`). Solo lee (O3):
no cambia el estado del mundo ni el del azar. Lo describe el mundo tal como lo percibe el individuo (la misma ventana
que `vista()`); no añade valoraciones (regla 3 de `AGENTS.md`).

**Campos comunes a los tres tipos:** `tipo`, `inventario` (`{clase: número}`, vacío si no hay) y `extra` (objeto libre
con lo propio del mundo). **Coordenadas:** enteras desde 0, `x` hacia la derecha e `y` hacia abajo (la fila 0 es la
de arriba). Las clases son las del mundo (las mismas que entrega en la `Observacion`). Un campo con `?` es opcional.

```jsonc
// rejilla (Crafter, mínimo, Snake)
{
  "tipo": "rejilla",
  "ancho": 9, "alto": 7,                       // la parte visible, en casillas
  "celdas": [["hierba", "arbol", null]],       // alto filas de ancho clases del fondo; null: nada que dibujar (fuera del mapa)
  "entidades": [{"clase": "zombi", "x": 3, "y": 1, "?id": "zombi_2", "?estado": "madura"}],
  "yo": {"x": 4, "y": 3, "?orientacion": "norte", "?estado": "dormido"},   // o null; orientacion: norte, sur, este, oeste o null
  "?origen": [27, 30],                         // [x, y] en el mundo de la celda (0, 0), si el mundo tiene coordenadas
  "inventario": {"madera": 2},
  "extra": {"luz": 0.8}
}

// arbol (archivos)
{
  "tipo": "arbol",
  "nodos": [{"ruta": "", "clase": "raiz", "padre": null},              // los padres van antes que los hijos
            {"ruta": "pradera", "clase": "carpeta", "padre": "", "?id": "...", "?estado": "..."}],
  "entidades": [{"clase": "comida", "ruta": "pradera", "?id": "...", "?nombre": "a.brote", "?estado": "..."}],   // ruta: un nodo
  "yo": {"ruta": "pradera"},                   // o null
  "inventario": {}, "extra": {}
}

// tablero (ajedrez)
{
  "tipo": "tablero",
  "ancho": 8, "alto": 8,                       // x = columna (0 = a), y = fila desde arriba (0 = la 8.ª vista por las blancas)
  "piezas": [{"clase": "rey", "color": "blanco", "x": 4, "y": 7}],
  "yo": {"color": "blanco"},                   // o null
  "turno": "negro",                            // o null
  "?marcas": [{"clase": "ultima", "x": 4, "y": 6}],   // última jugada, jaque...
  "inventario": {}, "extra": {"fen": "..."}
}
```

`validar_escena` comprueba los campos y sus tipos y la coherencia: dimensiones de `celdas`, coordenadas dentro de la
rejilla o del tablero, orientación conocida, padres y rutas que existen en el árbol.

**En el registro.** La escena va en el nivel vital (campo `escena`, sección 4) solo cuando cambia: la primera completa
y después completa cada vez que cambia (comparación de igualdad con la anterior de la misma vida). Para reproducir, la
escena de un latido es la última que llegó en su vida (`ida.telemetria.grabacion.escenas`). Es un campo añadido: el
registro sigue siendo v1 y el validador la valida cuando está.

**Sprites.** En `ida/telemetria/web/sprites/<mundo>/`, con un `indice.json` cuyo `mapa_sprites` da el fichero de cada
clave: la clase del fondo o de la entidad; `clase.estado` si la entidad lleva estado; `yo.<orientacion>` o
`yo.<estado>`; las clases del inventario; y `?` para lo que no tiene sprite. Crafter usa sus texturas (crafter 1.8.3,
licencia MIT, en `NOTICE`); el resto, sprites propios sencillos. Sin índice, el visor dibuja colores y letras.

**Crafter (T2a).** Rejilla con la ventana que se ve (9×7 con la vista oficial; de noche, 5×5; con la cuadrada,
(2·radio+1)²), el fondo de cada casilla (`hierba`, `arena`, `camino`, `agua`, `piedra`, `arbol`, `carbon`, `hierro`,
`diamante`, `mesa`, `horno`, `lava`), las criaturas y plantas con su id (`vaca`, `zombi`, `esqueleto`, `planta` con
estado `madura`, `flecha` con estado su dirección), `yo` en el centro con su orientación y `estado: "dormido"`, el
inventario completo (con `salud`, `comida`, `bebida` y `energia`) y, en `extra`, `luz` (la del día, con dos decimales)
y `logros`. Las criaturas se leen con `_cosas()`, la misma vía que `observar()` y `vista()`: asigna un id a la criatura
vista por primera vez, pero el observador llama a `vista()` y `escena()` al final del latido y el entorno no avanza
antes del `observar()` siguiente, así que los ids y su orden son los mismos (la excepción de lectura de la sección 4).

**Visor de comprobación** (no es el Vivero). `ida/telemetria/web/escena.html` y `escena.js`, servidos en `/escena`:
cargan una grabación `.jsonl.gz` (con `DecompressionStream`) o `.jsonl`, o un registro `.json`, y dibujan en Canvas
las escenas de rejilla; las de árbol y tablero se enseñan en JSON. El servidor sirve `web/` en `/web/` (solo esa
carpeta y tipos conocidos).

![Visor de escena con una grabación de Crafter](img/t2a_escena_crafter.png)

*Grabación `python -m ida --mundo crafter --latidos 300 --semilla 31 --plazo-logico 40 --opcion vista=oficial --opcion
longitud=10000 --opcion manual=estricto --grabar F:\tmp\t2a\crafter.jsonl.gz` (commit `2041fd0`, 26/11/2026; 208
latidos, todos válidos, escena en 190), latido 137.*

### 6.2 Opciones declaradas (O8)

`Mundo.opciones()` es un método de clase (se lee sin crear el mundo ni cargar sus dependencias) que devuelve una lista
de declaraciones; por defecto, vacía. Cada declaración:

| Campo | Contenido |
|---|---|
| `nombre` | clave de `--opcion nombre=valor` y argumento del constructor del mundo (identificador) |
| `tipo` | `entero`, `real`, `opcion` o `booleano` |
| `min`, `max` | entero y real: el rango, ambos obligatorios |
| `valores` | opción: lista no vacía de textos |
| `defecto` | el valor que da más Score de base (O8); pasa su propia validación |
| `etiqueta`, `ayuda` | `{"es": ..., "en": ...}` |
| `vacia` | opcional: la opción admite no tener valor (`None`, el campo vacío); solo entonces `defecto` puede ser `None` |

`ida/mundos/opciones.py` da `opcion(...)` (crea una declaración y la valida), `validar_declaracion`, `convertir`
(comprueba y convierte los valores de `--opcion`, que llegan como texto, y los de la antesala, que llegan como JSON;
un nombre no declarado es un error; un mundo sin declaraciones recibe los valores tal cual), `con_defectos` y
`defectos`. Los errores son `OpcionInvalida` con el mundo, la opción y el motivo, p. ej. «crafter: opción 'mapa': 500
fuera del rango [32, 128]».

**Dónde se aplican.** El ejecutor convierte siempre las opciones que recibe; la CLI da el error antes de crear nada.
Lo que no se da toma el valor por defecto **del constructor**, que no cambia: la invariancia y las herramientas de
medición lo usan. La antesala lanza con los **declarados** (`servidor.opciones_por_defecto`, con `con_defectos`), y el
Vivero hará lo mismo. Así, lo que se lanza desde la interfaz sin tocar nada coincide con la medición oficial.

## 7. Fases

Cada fase sale de `main` en su rama (`vista/<fase>`) y vuelve con autorización del autor.

| Fase | Contenido | Criterio | Agente |
|---|---|---|---|
| **T0** | Este documento, aprobado | Aprobación del autor | — |
| **T1** | Observador, registro v1 (tres niveles), hechos deducidos, grabación `.jsonl.gz`, consola sobre el registro, vidas reproducibles (O11) | Equivalencia OK; invariancia igual con observador encendido y apagado; validación del esquema; coste ≤ 5 % por latido con nivel cognitivo | Opus |
| **T2** | `escena()` en los cinco mundos; opciones declaradas por mundo (O8) con las de hoy y las nuevas aprobadas | Equivalencia OK; tests de contrato de escena y opciones | Opus diseña el contrato, Flash lo extiende a los mundos |
| **T3** | Servidor v1 (API y SSE); estructura `web/` con i18n; antesala nueva (mundos instalables, formulario automático, presets de carácter, idioma) | Paridad de idiomas; lista de comprobación de la antesala | Opus |
| **T4** | Vivero: escena viva con sprites, ánimo y necesidades, diario de hechos, logros, compañero y colección, ranking, guardar y adoptar | Lista de comprobación del Vivero; el autor lo prueba en los cinco mundos | Opus |
| **T5** | Laboratorio: latido animado (Onda por las 8 fases), mapa de Componentes, epistemología, biología y química, análisis y comparación de vidas, reproductor de grabaciones | Lista de comprobación del Laboratorio | Opus |
| **T6** | Cierre: OTel sobre el registro, README («Pruébalo en 1 minuto» con `[todos]`), capturas, `CHANGELOG`; retirar `panel.html` y `antesala.html` | Todo en verde; el autor revisa | Flash |

El orden pone el Vivero antes que el Laboratorio, como pidió el autor. T1 y T2 son la base de los dos.

## 8. Opciones nuevas por mundo (aprobadas; sus valores por defecto siguen O8)

| Mundo | Opciones que se proponen |
|---|---|
| Crafter | Tamaño del mapa; semilla del mapa independiente de la del organismo; vista oficial o ampliada (**hecho en T2a**, abajo) |
| Snake | Velocidad del juego; tamaño del tablero (si la web lo permite) |
| Mínimo | Tamaño de la rejilla; número de depredadores; abundancia de comida |
| Archivos | Número de biomas; frecuencia de brotes; agresividad del depredador |
| Ajedrez | Ya tiene color, Stockfish y Elo; añadir «apertura aleatoria» |

**Crafter (T2a).** Defecto declarado frente al del constructor (el que usan la CLI sin `--opcion`, la invariancia y la
equivalencia):

| Opción | Tipo y rango | Declarado (O8) | Constructor | De dónde sale el declarado |
|---|---|---|---|---|
| `vista` | opción: `oficial`, `cuadrada` | `oficial` | `cuadrada` | `evaluar_crafter.py` (D17) |
| `radio` | entero, 2–8 | 4 | 4 | la evaluación no lo toca |
| `manual` | opción: `estricto`, `ampliado` | `estricto` | `estricto` | `evaluar_crafter.py` |
| `longitud` | entero, 100–1 000 000 | 10 000 | 100 000 | `evaluar_crafter.py` (longitud oficial del episodio) |
| `mapa` | entero, 32–128 (lado en casillas) | 64 | 64 | nueva; reproduce lo de hoy (`crafter.Env(area=(64, 64))`) |
| `semilla_mapa` | entero, 0–2 147 483 646, admite vacía | vacía | vacía | nueva; vacía = la semilla del organismo, como hoy |
| `ventana` | booleano | no | no (`0`) | la evaluación no la abre |

`mapa` y `semilla_mapa` existen en el paquete: `crafter.Env(area=(64, 64), ..., seed=None)` (crafter 1.8.3); con lados
16, 32, 48, 96 y 128 el mapa se genera y avanza 50 pasos sin error (prueba del 26/11/2026). Pasarlas con su valor por
defecto da las mismas acciones que sin ellas (`tests/test_escena_crafter.py`, 40 latidos, semilla 31, plazo lógico 40).
No quedó fuera ninguna de las aprobadas.

## 9. Qué no entra (por ahora)

- **Intervenir en la vida.** El usuario solo observa. La intervención podrá llegar como modo aparte, con las vidas
  intervenidas marcadas y fuera de cualquier medición.
- Un ejecutable descargable y una demo web sin instalar nada.
- Cuentas, nube o compartir en línea: compartir es enviar una ficha o una grabación.

## 10. Registro de cambios

| Fecha | Decisión | Cambio | Motivo |
|---|---|---|---|
| 25/11/2026 | O1–O18 | Propuesta inicial | Conversación con el autor sobre la evolución de la telemetría y la experiencia de usuario |
| 26/11/2026 | O1–O18, sección 8 | Aprobadas por el autor. O8: el valor por defecto de cada opción es el que da más Score de base | Aprobación del autor |
| 26/11/2026 | O2–O5, O7, O11, secciones 4 y 5 | T1: el registro del latido pasa de esbozo a v1 (esquema y catálogo de hechos finales, con lo que queda fuera); grabación `.jsonl.gz`; consola sobre el registro; plazo lógico 40 desde la antesala salvo en tiempo real. Excepción de lectura de `vista()` en Crafter (caché de ids), aprobada por el autor. Equivalencia OK; invariancia OK con el observador en los tres niveles; coste con nivel cognitivo, +4,6 % por latido (Crafter, 3000 latidos, plazo lógico 40, semilla 31, 2 repeticiones) | Rama `vista/t1-registro` |
| 26/11/2026 | O6, O8, O18, secciones 4, 6 y 8 | T2a: contratos `escena()` v1 (rejilla, árbol, tablero) y opciones declaradas (formato, validación, defecto = el de la medición oficial; los del constructor no cambian), con su implementación completa en Crafter (escena, siete opciones con `mapa` y `semilla_mapa`, sprites MIT) y un visor de comprobación en `/escena`. La escena va en el registro solo cuando cambia (sigue siendo v1). Único cambio en la base: los dos métodos de `Mundo`. Equivalencia OK; invariancia OK con el observador completo en los cuatro mundos; 1208 tests | Rama `vista/t2a-escena` |
