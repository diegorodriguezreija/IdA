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

## 4. Registro del latido v1 (esbozo)

```jsonc
{
  "v": 1, "latido": 1234, "vida": 3, "generacion": 2, "individuo": "ida-7f3a", "mundo": "crafter",
  // nivel vital
  "cuerpo":   {"vitalidad": 72, "energia": 55, "descanso": 80, "dormido": false},
  "afecto":   {"valencia": 0.3, "activacion": 0.6, "animo": "curioso"},
  "quimica":  {"dopamina": 0.4, "cortisol": 0.2, "...": 0},
  "necesidades": [{"nombre": "hambre", "deficit": 0.4}, {"nombre": "sed", "deficit": 0.1}],
  "accion":   {"verbo": "hacer", "objetivo": "mesa", "exito": true, "sistema": "S3"},
  "score":    {"valor": 15.9, "logros": ["collect_wood", "place_table"]},
  "hechos":   [{"tipo": "aprende", "verbo": "hacer", "clase": "mesa", "requiere": {"madera": 1}, "fuente": "experiencia"}],
  "escena":   { /* sección 6; solo si cambia */ },
  // nivel cognitivo
  "onda": {
    "canales": {"Exterocepcion": 9, "Imagen": 4, "Accion": 3},
    "flujo":   [{"pieza": "Imagen:arbol", "de": "S1.Sentir.Imagen", "a": "S2.Interpretar.Valor"}],
    "consumo": {"S1": {"amplitud": 31, "potencia": 2.6}, "S2": {"...": 0}, "S3": {"...": 0}},
    "guillotina": false
  },
  "tribunal":    {"ganador": "S3", "candidatos": [{"sistema": "S1", "verbo": "comer", "puntuacion": 0.41}]},
  "estrategias": {"S1": "alimentarse", "S3": "progresar"},
  // nivel completo
  "tiempos_ms": {"S1.Sentir.Imagen": 0.12, "...": 0},
  "fases":      [["sentir", 0, 1.2], ["preatencion", 1.2, 1.9]],
  "piezas":     [{"id": "...", "tipo": "...", "arousal": 0.7, "origen": "S1.Imagen", "registro": []}]
}
```

Los nombres exactos se fijan en T1 a partir de lo que exponen `Onda`, `Soma`, `Memoria` y `Mundo`. Cada versión nueva
del esquema solo puede **añadir** campos; quitar o renombrar exige `v: 2` y un conversor para las grabaciones antiguas.

## 5. Catálogo inicial de hechos

| Tipo | Parámetros | Ejemplo de frase (es) |
|---|---|---|
| `nace` | individuo, generación, heredados | «Nace Ida-7f3a, generación 2, con 14 recuerdos heredados» |
| `primera_vez` | verbo, clase | «Por primera vez: come una vaca» |
| `aprende` | verbo, clase, efecto o requisito, fuente, confianza | «Ha aprendido que la mesa necesita madera» |
| `duda` / `refuta` | proposición | «Ya no cree que el agua quite el hambre» |
| `sorpresa` | esperado, obtenido | «Esperaba ganar y perdió: sorpresa» |
| `logro` | nombre (del mundo) | «Logro: colocar una mesa» |
| `peligro` | clase, daño estimado | «Ha aprendido a temer al zombi» |
| `estrategia` | sistema, nombre, inicio o abandono | «Cambia de plan: buscar refugio» |
| `duerme` / `despierta` | | «Se duerme agotada» |
| `muere` | causa, latidos, Score | «Muere de hambre tras 812 latidos» |

## 6. Contrato de `escena()` (esbozo)

```jsonc
{
  "tipo": "rejilla",                  // rejilla | arbol (archivos) | tablero (ajedrez)
  "ancho": 9, "alto": 7,               // la parte visible
  "celdas": [["hierba", "arbol", "..."]],   // clase del fondo por celda
  "entidades": [{"clase": "zombi", "x": 3, "y": 1}],
  "yo": {"x": 4, "y": 3, "orientacion": "norte"},
  "inventario": {"madera": 2, "piedra": 0},
  "extra": {}                          // lo propio del mundo (FEN en ajedrez, carpeta actual en archivos)
}
```

Sprites por mundo en `web/sprites/<mundo>/`. En Crafter se usan sus texturas (licencia MIT). En el resto, sprites
propios sencillos. La escena viaja en el registro solo cuando cambia.

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
| Crafter | Tamaño del mapa; semilla del mapa independiente de la del organismo; vista oficial o ampliada |
| Snake | Velocidad del juego; tamaño del tablero (si la web lo permite) |
| Mínimo | Tamaño de la rejilla; número de depredadores; abundancia de comida |
| Archivos | Número de biomas; frecuencia de brotes; agresividad del depredador |
| Ajedrez | Ya tiene color, Stockfish y Elo; añadir «apertura aleatoria» |

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
