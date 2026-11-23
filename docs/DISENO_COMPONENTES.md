# IdA: diseño por Componentes (decisiones)

**Fecha:** 22/11/2026. **Base:** `main` en `eaeadaa` (`crafter-general-v4`).
**Origen:** sección 0 y paso R1 de [`PLAN_COMPONENTES_Y_HOJA_DE_RUTA.md`](PLAN_COMPONENTES_Y_HOJA_DE_RUTA.md), con el flujo de alto nivel que dio el autor el 22/11/2026. El autor delegó las decisiones abiertas en el arquitecto; todas son revisables por él.
**Qué sustituye:** la sección 0.2 del plan (preguntas abiertas) y los pasos R1 a R7, que pasan a ser las fases A y B de este documento (sección 5).

**Especificación verificable:** el reparto de Componentes que deciden estas páginas está en [`doc-repositorio/componentes.toml`](../doc-repositorio/componentes.toml) (destino, dónde está hoy, paso y decisión de cada uno). Un test comprueba que el código coincide con ella, y [`doc-repositorio/06_MAPA_DE_COMPONENTES.md`](../doc-repositorio/06_MAPA_DE_COMPONENTES.md) se genera desde ella. Cambiar un destino exige modificar antes la decisión correspondiente aquí (sección 7).

Dos objetivos, en este orden de prioridad:
1. **Diseño coherente:** biológicamente plausible, y con Componentes coherentes entre sistemas y mundos.
2. **Score intacta:** la reorganización (fase A) da el mismo JSON. Los cambios de conducta (fase B) se aceptan solo si no empeoran, según el criterio fijado de antemano (D17).

---

## 1. Hechos del código que condicionan el diseño

Comprobados en `eaeadaa`:

| Hecho | Dónde | Consecuencia |
|---|---|---|
| Ya hay un registro de Componentes de mundo por destino (`"S1.Interpretar"`, `"CORE.Sentir"`...) | `ida/core/mundo.py:171`, `ida/core/latido.py:68-78`; lo usa archivos (`archivos.py:277`) | No hay que inventarlo: se amplía (D3) |
| La propiedad de las piezas se comprueba por **tipo**, no por nombre ni sistema | `ida/core/onda.py:225` | Componentes del mismo tipo en distintos sistemas o mundos ya pueden modificar sus piezas (D3) |
| La saliencia es interpretación: el arousal de cada pieza `Exterocepcion` sale de `peligro`, `nutritivo` y `novedad` | `ida/core/sentidos.py:57` | Sacar la valoración del adaptador cambia el arousal en el Core salvo que se reponga antes de que nadie lo lea (D5) |
| El adaptador de Crafter entrega rasgos valorados (`nutritivo`, `recurso` desde el manual, `novedad` por tiempo, gradientes de comida) | `ida/mundos/crafter.py:317-343` | No es un dato en bruto (D4) |
| El peligro aprendido se calcula antes de Sentir, escribiendo en la Observación, también dormido | `ida/core/latido.py:134`, `243-273` | La alarma que despierta depende de él (`latido.py:428-433`) |
| El Core lee la Observación fuera de los sensores (mapa, transformaciones, requisitos) | `ida/core/latido.py:300-360` | Hay lectores que no pasan por la Onda (D4) |
| En Crafter, `COMER`, `ATACAR` y `COGER` son `do` y, si no se mira al objetivo, primero se gira: dos pasos del entorno en un latido | `ida/mundos/crafter.py:404-412` | Una tecla por latido cambia la conducta (D9, fase B) |
| `Anticipacion` es F1 (bloque F, `827a6a5`, 16/11), anterior a la fase de generalización. `Peticion` sí es de la fase (`ef066cb`, 20/11) | `ida/sistemas/comun.py:59`, `115` | Corrige la sección 2.3 del plan (D11) |
| La decisión 18 de `REDISENO_BASE.md` ya fija la prioridad S1 > S2 > S3 y acepta que S3 se quede sin turno con estrés crónico | `docs/REDISENO_BASE.md`, decisión 18 | D14 |
| La comparación pareada conjunta (31 y 32, 100 000 pasos) tiene un IC 95 % de unos ±1 punto de Score | `docs/MEDICION_MATERIAL_MAPA.md` (1,08 [0,17; 2,10]) | Resolución del criterio de no inferioridad (D17) |

---

## 2. El latido (D1)

Ocho pasos. En negrita, lo que no existe hoy con ese nombre.

| Paso | Qué hace | Quién | Paga atención | Corre dormido |
|---|---|---|---|---|
| 1. Onda | Copia de la anterior: `ei` = `ef` anterior; la anterior pasa a la **memoria a corto plazo** (cola de ondas, tamaño fijo) | Core | — | Sí |
| 2. Sentir | Datos en bruto del cuerpo y del mundo (D4) | Core · Sentir (y sensores del mundo) | No | Sí |
| 3. **Preatención** | Anotación preatentiva de lo sentido: saliencia y valoración rápida (D5) | Componentes preatentivos de S1 · Sentir | No | Sí |
| 4. **Plasticidad** | Cada Componente que aprende lo hace del efecto de la acción anterior (D6) | El dueño de cada parte de la memoria | No | Sí |
| 5. **Regulación** | Reglas instantáneas que fijan frecuencia, amplitud y potencia de la Onda (D12) | Core | — | Sí |
| 6. Cognición | S1 → S2 → S3, cada uno Sentir, Interpretar, Reaccionar y Actuar; guillotina por plazo | Sistemas | Sí | No (parálisis) |
| 7. Actuar | El Tribunal acepta una Actuación y el Core ejecuta su primitiva (D9) | Core · Actuar | No | Solo lo que dicta el sueño |
| 8. Cierre | Marcar para guardar (arousal y feedback), episodios desde la memoria a corto plazo, indicadores | Core | — | Sí |

**Por qué así (biología):**
- Pasos 2 y 3: los receptores transducen; la saliencia ascendente y la valoración innata (colículo superior, la vía rápida de la amígdala) se calculan en paralelo y **antes** del cuello de botella de la atención. Por eso la preatención no paga amplitud.
- Paso 4: la plasticidad sináptica es local y no consume atención.
- Paso 5: los sistemas de activación del tronco encefálico (locus coeruleus, formación reticular) fijan la ganancia y el ritmo del procesamiento a partir del estado, sin pensar.
- Dormido: la corteza se desconecta, pero la vigilancia preatentiva sigue (pasos 2 a 5). Por eso un animal dormido despierta ante una amenaza.

**Equivalencia:** el orden 2 → 3 → 4 reproduce el de hoy (peligro aprendido y estimado antes de que nadie lea lo sentido; luego `_aprender`). La regulación (paso 5) lee lo mismo que lee hoy `Marcapasos.ritmo` (indicadores del latido anterior), así que da los mismos valores. Leer lo sentido en el propio latido es la fase B (B2).

---

## 3. Decisiones

### D2. Estructura de paquetes

La estructura del código es el diagrama de la arquitectura. Un Componente por fichero.

```text
ida/
  nucleo/            mecánica sin cognición: onda, pieza, arquitectura (Componente, Módulo, Sistema),
                     latido, memoria (almacén), soma, linaje, vocabulario, contrato del mundo, persistencia
  core/
    sentir/          interocepcion.py, propiocepcion.py, exterocepcion.py, ambiente.py
    actuar/          tribunal.py, actuador.py
    regulacion.py    reglas de la Onda (hoy Marcapasos)
  s1/  sentir/ interpretar/ reaccionar/ actuar/   (estrategias en reaccionar/estrategias/)
  s2/  ...
  s3/  ...
  cuerpos/
    cuadricula/      familia de cuerpos (D10), misma estructura: core/actuar/, s1/interpretar/...
  mundos/
    crafter/
      adaptador.py   observar (en bruto), ejecutar (primitivas), verbos
      perfil.py      parámetros y constantes de escala
      manual.json
      registro.py    qué Componentes añade o sustituye, y en qué módulo (D3)
      core/sentir/  s1/sentir/  s1/interpretar/  s1/reaccionar/estrategias/ ...
    minimo/ archivos/ snake/ ajedrez/   (misma forma)
```

- El paquete raíz sigue siendo `ida` (minúsculas, convención de Python). `ida/core` pasa a ser el sistema Core; la mecánica que hoy vive en `ida/core/*.py` se mueve a `ida/nucleo/`.
- **Importaciones permitidas:** `nucleo` ← `core`, `s1`-`s3` ← `cuerpos` ← `mundos`. Nada de `nucleo`, `core` ni `sN` importa `cuerpos` ni `mundos`; `cuerpos` no importa `mundos`. Lo vigila `test_pureza`.

### D3. Registro declarado de Componentes

Las carpetas organizan; **el registro declara**. Nada se activa por el nombre de un fichero.

```python
# ida/mundos/crafter/registro.py
REGISTRO = {
    "cuerpo": "cuadricula",
    "S1.Sentir":       {"añade": [ValoracionCrafter()]},            # preatentivo (D5)
    "S1.Interpretar":  {"añade": [Amenaza(), Apetencia(), Recinto()]},
    "S1.Reaccionar":   {"estrategias": {"añade": [Afrontar(), Proteger(), SalirDelRecinto()]}},
}
```

- **Dos verbos:** `añade` (se ejecuta después de los generales del módulo, en el orden declarado) y `sustituye` (ocupa el sitio del general con ese nombre; mismo tipo obligatorio).
- **Nombres únicos por módulo:** un Componente de mundo con el nombre de uno general solo se acepta si se declara `sustituye`. Así no hay sustituciones implícitas.
- **Propiedad por tipo** (como hoy, `onda.py:225`): un Componente de mundo puede emitir y modificar piezas de un tipo de la base si es de ese tipo. Es lo que el autor pedía con «mismo nombre»: un Componente de tipo `Interocepcion` de un mundo puede modificar las piezas `Interocepcion` del Core. Cada modificación queda en el registro de la pieza.
- **Orden determinista:** general antes que mundo; dentro de cada uno, el orden declarado.
- **Componentes generales opcionales:** viven en `ida/sN/`, pero solo se montan si un mundo los registra (`Amenaza`, `Apetencia`, `Afrontar`, `Proteger`). Son el sustituto de las activaciones condicionales (D15).
- **Una familia de cuerpos** (D10) se registra con la clave `cuerpo` y aporta sus propios Componentes con la misma forma.
- **Conocimiento del mundo, medido:** `herramientas/conocimiento_mundo.py` lista, por mundo, los Componentes registrados, sus líneas, qué sustituyen y cuántas veces modificaron piezas de la base en una vida (desde el registro de las piezas). Va en cada informe de medición: es lo que IdA sabe de ese mundo por diseño (columna «Uses» de Crafter).

### D4. Datos en bruto y la Observación

- **En bruto** es lo que mide un sensor sin valorar: constantes vitales, posición, orientación, inventario, qué clase de cosa hay y dónde, la luz.
- **Interpretación** es siempre del organismo: `nutritivo`, `peligro`, `recurso` y `novedad`.
- `proximidad`, `lugar` y `agente` se aceptan como bruto: son medidas (distancia, se puede pisar, se mueve sola), no juicios.
- **La Observación solo la leen los sensores del Core** (y los del mundo en `core/sentir/`). Todo lo demás lee piezas de la Onda. Como el Core no paga atención, cada entidad tiene su pieza y no se pierde nada.
- **Lo que R0 encontró en Crafter** (`docs/R0_INVENTARIO.md`, secciones B y H):
  - `nutritivo` lee `obj.ripe` del motor: el adaptador entregará `madura` en los `datos` de la entidad, que es una medida visible;
  - `novedad` lee `self.visitas` y `self.t` (el reloj del mundo): el organismo la calculará con su propia memoria de visitas (`ValoracionCrafter`, que las apunta al empezar su turno de preatención) y con su propia cuenta de primitivas ejecutadas (la copia eferente del `Motor`). Coincide con `self.t` porque cada primitiva es un paso del entorno. Por eso **A5 va antes que A4**;
  - en S2 y S3, la Observación solo se lee para la `ubicacion`, que pasa a leerse de la pieza `Propiocepcion`.
- **Transición:** mínimo, archivos, snake y ajedrez entregan hoy rasgos valorados. Se declaran en su `Perfil` (`rasgos_declarados = ("peligro", "nutritivo", ...)`) como conocimiento que el mundo da hecho, y cuentan en el informe de D3. Crafter queda con `rasgos_declarados` vacío al terminar la fase A. Quitarlos en los demás mundos es M3 y cambia su conducta.

### D5. Preatención

Componentes de S1 · Sentir marcados como **preatentivos**. Corren en el paso 3, también dormido, y no pagan amplitud ni potencia.

Con límites estrictos, vigilados por test, para que no sean una puerta trasera:
1. Solo modifican piezas de los sensores del Core (`Interocepcion`, `Propiocepcion`, `Exterocepcion`, `Ambiente`) de su mismo tipo: los rasgos de la carga y el arousal (la saliencia).
2. No emiten piezas nuevas ni proponen acciones.
3. Coste acotado: lineal en las entidades percibidas. Sin búsquedas ni planes. Su tiempo se mide (`onda.tiempos_ms`) y se informa.

Contenido:
- **General:** la saliencia de `sentidos.py:57`, que pasa a calcularse aquí. `Exterocepcion` en el Core emite cada entidad en bruto, con arousal 0 (sin valorar), y la preatención le pone la saliencia con los rasgos interpretados. Valor final idéntico al de hoy.
- **Amenaza** (S1, general, D7): estima el `peligro` de cada entidad con lo aprendido.
- **Crafter (`ValoracionCrafter`):** `nutritivo`, `recurso` y `novedad` que hoy calcula el adaptador, con la misma fórmula, a partir de las piezas, el manual y la memoria.
- **Orden:** `Saliencia` corre siempre la última de la preatención: integra los rasgos que ponen los demás preatentivos, generales o del mundo.

Así se cumplen a la vez el punto 2 del autor (el Core no procesa), la nota B (no hay piezas nuevas que cuesten atención) y la nota D (dormido se sigue estimando el peligro, y la alarma funciona igual).

### D6. Plasticidad

Un Componente que aprende implementa un cuarto método, `aprender(ctx)`, que el Core llama en el paso 4 (después de la preatención), exento de atención y también dormido. Hoy esa lógica está repartida entre `Organismo._aprender`, `_peligro_aprendido` y `Memoria`; pasa al Componente dueño de lo aprendido. El momento es el mismo que hoy, así que el resultado también.

Excepción de orden: `Amenaza` aprende (daño, emisores, eficacia) en su propio paso preatentivo, justo antes de estimar, porque hoy se aprende y se estima antes de Sentir.

### D7. Memoria

- **Un solo almacén** (decisión 22 de `REDISENO_BASE.md`) con **una sección por dueño**. Leer es libre; escribir en una sección solo puede su dueño, con una API que, como la Onda, recibe el autor y lo comprueba.
- **La Experiencia:** reactiva = la Onda y la memoria a corto plazo; activa = la Memoria (semántica y episódica); proactiva = expectativa, prospectiva, plan e imaginación (decisión 24). La Memoria es el sustrato de la dimensión activa, no un módulo.
- **Lo aprendido es de cada mundo:** el legado se guarda por mundo y linaje, y nunca pasa de un mundo a otro. Cada sección da su parte del legado (`legado()` y `heredar()`) y el almacén las junta.
- **El manual** es la dotación innata: el Core lo carga al nacer en las secciones de sus dueños.

| Sección | Dueño | Hoy |
|---|---|---|
| Proposiciones, registros (verbo × clase), expectativas | Core (aprende del efecto, paso 4) | `Memoria.saber`, `registros`, `proyectar` |
| Qué necesidad satisface cada clase (aliestesia) | `Apetencia` (S1 · Interpretar, general) | `Memoria.satisface` |
| Peligro: daño, alcance, emisores, eficacia | `Amenaza` (S1 · Interpretar, general) | `ida/core/peligro.py` |
| Requisitos, transformaciones | `Requisito` (S3 · Interpretar, general; «delante» y «cerca» los da el cuerpo) | `Memoria.aprender_requisito`, `aprender_transformacion` |
| Metas (qué verbo sobre qué objetivo cumplió un logro) | `Requisito` (S3 · Interpretar): una estrategia no tiene plasticidad (D6), así que las metas las aprende el Componente de medios y fines | `Memoria.registrar_meta` |
| Lugares, hogar y mapa topológico (lugares y rutas) | Core (como hoy) | `Memoria.lugares`, `mapa` |
| Mapa local métrico (casillas) | `MapaLocal` (cuerpo cuadrícula) | `Memoria.ver_casillas` |
| Modelo del cuerpo (si avanza, si gira) | Capa motora del cuerpo cuadrícula (modelo directo) | `Memoria.aprender_cuerpo` |

**Escrituras de quien no es el dueño** (R0, sección F). Pasan por la API del dueño con el autor, en el mismo momento que hoy, para no cambiar la conducta. Cada dueño declara qué autores admite:

| Escritura | Quién la hace hoy | Dueño |
|---|---|---|
| `ver_clase` (clases vistas, para la novedad) | `Exterocepcion`, `sentidos.py:61` | Core (plasticidad); el sensor deja de escribir |
| `recordar_lugar` (hogar) | `Proteger`, `proteger.py:556` | Core (lugares), autor `Proteger` |
| `olvidar_donde` (dónde estaba una clase) | `RecordarComida`, `s2.py:344` y `390` | Core (lugares), autor `RecordarComida` |
| `lectura_activa`, `ultimo_fin_lectura` | `Estudio`, `s3.py:316-459` | S3, autor `Estudio` |

### D8. Estrategias

- **Hay estrategias generales y del mundo.** Una general se expresa sobre **intenciones** («alejarse de X», «acercarse a Y», «tomar», «omitir», «buscar cobijo»), nunca sobre teclas ni casillas. Cómo se ejecuta cada intención lo resuelve la capa motora del cuerpo (D9). Es la lectura de la decisión 3 de `REDISENO_BASE.md` que conserva lo general: el qué y el porqué son del organismo; el cómo moverse, del cuerpo.
- **Biología:** la defensa (luchar, huir, quedarse quieto) se conserva entre especies en los circuitos del tronco encefálico (sustancia gris periacueductal), pero la ejecutan sistemas motores propios de cada cuerpo.
- **Las fases están permitidas** (decisión 17, patrón de acción como máquina de estados). Lo que separa una estrategia de un procedimiento escrito son los cuatro criterios de la sección 4.2 del plan, con esta precisión del primero:
  - **sí** puede disparar una transición: una pieza de la Onda (lo sentido, como la luz de `Ambiente`, o lo interpretado) y el tiempo interno del organismo (latidos que lleva la estrategia, para el agotamiento);
  - **no** puede: el paso del entorno, el reloj o la hora del mundo, ni el estado interno del mundo.
- **Prueba automática (fase A, A8):** las estrategias y los Componentes de mundo no leen `ctx.observacion` ni el mundo, y sus constantes están en el `Perfil`. El resto de criterios se revisa en cada PR.

### D9. Actuar: primitivas y capa motora

- **El Core · Actuar solo ejecuta primitivas del mundo:** las que declara su adaptador (en Crafter, las teclas: `move_left`, `do`, `place_table`, `sleep`, `noop`...; en snake, las flechas; en mínimo y archivos, sus verbos actuales, que ya son primitivas de ese mundo).
- **La Actuación** (la pieza `Accion`) lleva **la primitiva y la intención** (verbo semántico, objetivo, clase, origen). El aprendizaje sigue usando la intención (`COMER` sobre una vaca), así que no cambia.
- **La capa motora** del cuerpo traduce intención → primitiva. El Actuador del Core le pide las primitivas al ejecutar la Actuación decidida (entre la propuesta y la ejecución nada cambia, así que es equivalente y más simple).
- **Sinergias motoras:** la capa motora puede devolver una sinergia corta (orientarse y golpear) que el Core ejecuta entera. Es una unidad motora, como las sinergias de la médula espinal, no una conducta. Su longitud máxima es un parámetro del cuerpo (`max_sinergia`), con valor 2 en la fase A para reproducir el giro y golpe de hoy. Pasarla a 1 es B1.
- **El éxito de una intención** (`COMER` solo tiene éxito si sube la comida) lo juzga la capa motora del cuerpo, comparando lo pretendido con lo medido en bruto que devuelve el adaptador. Es un juicio general (comer es éxito si alimenta), no de un mundo. El adaptador deja de juzgar.
- **El plus a lo ejecutado** (punto 7 del autor) es la continuidad del Tribunal que ya existe: 0,1 × (1 − agotamiento) × (1 − progreso). Lleva el freno contra la perseveración. Se conserva tal cual.

### D10. Familias de cuerpos

`ida/cuerpos/cuadricula/` reúne lo que comparte cualquier mundo de cuadrícula 2D con orientación (Crafter, MiniGrid, la mayoría de mundos de rejilla):
- **geometría:** vecinos, distancia, «delante», orientación;
- **capa motora:** intención → primitivas, sinergias, buscador de posturas («qué secuencia de MOVER me deja en A mirando a C»);
- **modelo directo del cuerpo** (qué hace cada primitiva), que aprende de la copia eferente (función del cerebelo);
- **mapa local métrico.**

Lo que solo existe en Crafter (cavar, colocar piedra, recintos) va en `mundos/crafter/`. Un mundo de cuadrícula nuevo (V3) registra `cuerpo: "cuadricula"` y solo escribe su adaptador, su manual y su perfil.

### D11. Anticipación y Petición

- **`Anticipacion` se queda en Actuar** y se documenta como **copia eferente**: la predicción de las consecuencias se genera con la orden motora y viaja con ella (Sperry, von Holst). Moverla a Reaccionar le quitaría la acción sobre la que predice, porque se propone en Actuar.
- **`Peticion` pasa a Reaccionar**, al final del módulo, después de `Estrategia`. Pedir una submeta a S3 es una señal motivacional de la estrategia, no la aceptación de una acción. Solo registra (no paga atención) y nadie de Actuar la lee, así que el resultado es el mismo. Se comprueba en A7.

### D12. Regulación de la Onda

- El punto 3 del autor: un conjunto de reglas (condición → ajuste de frecuencia, amplitud o potencia), sin búsquedas ni bucles sobre la memoria. Sustituye a `Marcapasos.ritmo`.
- **Fase A:** lee lo mismo que hoy (el soma y los indicadores del latido anterior). Mismos valores.
- **Fase B (B2):** lee también lo sentido y preatendido en el propio latido. Es un cambio de conducta (se responde un latido antes).
- Un mundo puede añadir reglas (registradas como Componentes de `core`), con los mismos límites que la preatención.
- En la fase A la regulación se calcula al crear la Onda, con los mismos datos que el Marcapasos; colocarla tras la preatención, con lo sentido en el propio latido, es B2.

### D13. Memoria a corto plazo, episodios y poda

- **Memoria a corto plazo:** cola de las últimas ondas (`ef` resumido), tamaño fijo en el `Perfil`. Solo lectura para los sistemas. En la fase A, los episodios se siguen formando como hoy, y la cola es la fuente de la que leen.
- **Poda por arousal mínimo:** solo en `ev` (lo percibido), nunca en lo registrado en `ef`. `Feedback`, `Expectativa` y `Estrategia` tienen arousal 0 por construcción y se leen en el latido siguiente. Es un cambio de conducta (B3).

### D14. Amplitud

Se mantiene la decisión 18: un único fondo de atención y prioridad S1 > S2 > S3. Es la conducta del estrés agudo: la corteza prefrontal se desconecta con estrés y mandan los circuitos subcorticales (Arnsten, 2009).

M1 deja de ser «reservar amplitud para S3» y pasa a ser **la eficiencia de S1 con amenaza**: por qué gasta 23 piezas en lugar de 12. Una reserva contradiría esta decisión.

### D15. Activaciones, parámetros e interruptores

- **Las activaciones condicionales se sustituyen por el registro:**
  - `Perfil.aliestesia` desaparece: `Apetencia` solo existe donde se registra. `Alimentarse` también lo consulta (`s1.py:664`, `670` y `680`; R0, sección D): pasa a preguntar si `Apetencia` está registrada (`ctx.registrado("Apetencia")`), no si hay piezas de deseo en ese latido, que daría otra conducta los latidos sin nada deseable a la vista;
  - el peligro aprendido solo existe donde se registra `Amenaza`. Su condición actual («el mundo no da `peligro`», `latido.py:250`) y la marca `ctx.extra["peligro_aprendido"]` que lee `Afrontar` (`s1.py:341`) se sustituyen por el registro, con los mismos valores en Crafter;
  - `Afrontar` y `Proteger`, lo mismo.

  Hoy solo Crafter los activa, así que solo Crafter los registra y los demás mundos no cambian.
- **Las constantes de escala pasan al `Perfil`** del mundo o a parámetros del cuerpo, con los valores de hoy en Crafter: `ALCANCE_SITIO`, `MAX_INTERIOR`, `CANDIDATOS_EXACTOS`, `MAX_ESTADOS`, `DANO_PREVIO`, `GOLPES_PREVIO`, `MARGEN_LUGAR`... El inventario completo es parte de A6.
- **Los interruptores de los bloques E y F** (`MecanismosMemoria`) se quedan como parámetros del `Perfil`: activan mecanismos generales por mundo, que es justo lo que debe decidir el mundo.

### D16. Estrategias de Crafter, una a una

| Pieza | Destino | Por qué |
|---|---|---|
| `Proteger` | S1 · Reaccionar, general; la registra quien declare la necesidad `cobijo` | Cuándo y por qué buscar cobijo, con la intensidad anticipada, vale para cualquier organismo |
| `Recinto` | Crafter, S1 · Interpretar | Produce una pieza **afordancia de protección** (sitio, coste, confianza, requisitos y plan). Cavar y cerrar accesos solo existe en Crafter |
| Geometría y buscador de `proteger.py` | `cuerpos/cuadricula` | Valen para cualquier rejilla con orientación |
| `SalirDelRecinto` | Crafter, estrategia de S1 | Depende del recinto de Crafter |
| `Afrontar` | S1, general; la registra Crafter | Luchar o huir según el daño esperado y la salud |
| `Apetencia` | S1 · Interpretar, general; la registra Crafter | Aliestesia |
| `PerseguirMetas` | S3, general | **DUDA abierta:** el lote por estación y el material desde el mapa pueden suponer el cuerpo cuadrícula. R0 no lo resuelve (no lee ni posiciones ni la Observación, sección B); se decide en A6 leyendo su código |

### D17. Criterios de aceptación

**Fase A (reorganización):** igual que la sección 4.4 del plan, sin cambios:
- con `--plazo-logico 40`, el JSON de `evaluar_crafter.py` (3000 pasos, semillas 31 y 32) idéntico al de `main`, ignorando los campos de tiempo;
- `invariancia.py` OK en los cuatro mundos;
- ruff, mypy y pytest en verde.

Al final de la fase, la medición de 100 000 pasos repite campo a campo `mapa_31.json` y `mapa_32.json`.

**Fase B (cambios de conducta), no inferioridad fijada de antemano.** Comparación pareada conjunta de las semillas 31 y 32 a 100 000 pasos (`resumen_evaluacion.py --pareada-conjunta`):
- la diferencia de Score tiene una estimación ≥ −0,3 puntos **y** el límite inferior de su IC 95 % ≥ −1,0 puntos (la resolución de la medición, sección 1);
- en mínimo y archivos, `benchmark.py` pareado (N = 10) sin empeoramiento significativo;
- se informa también de cada logro con un cambio significativo, aunque no decida.

Si no se cumple: un diagnóstico y una ronda. Si sigue sin cumplirse, el cambio queda tras un parámetro del cuerpo o del `Perfil` con el valor de la fase A, y se documenta como resultado negativo.

Al terminar la fase B se mide con semillas nuevas (V1: 41 y 42) para descartar el sobreajuste a 31 y 32.

---

## 4. Riesgos

| Riesgo | Dónde | Mitigación |
|---|---|---|
| Orden de ejecución distinto al mover piezas (preatención, plasticidad, `Peticion`) | A3, A4, A7 | Un paso por PR con su comprobación de JSON. Si difiere, se busca la diferencia de orden antes de seguir |
| Lectores de la Observación que se olvidan al cambiarlos a piezas | A4 | Test: fuera de los sensores, ningún Componente recibe la Observación (`Contexto.observacion` deja de exponerse) |
| La preatención se usa como sitio gratis para cognición cara | Todas | Los tres límites de D5, vigilados por test, y el tiempo de la preatención en cada informe |
| Sustituciones por nombre que nadie ve | Todas | Registro declarado, nombres únicos por módulo e informe de conocimiento del mundo (D3) |
| `max_sinergia = 1` baja la Score | B1 | Criterio de D17; si falla, la sinergia de 2 se queda como parámetro del cuerpo |
| El movimiento mecánico de ficheros rompe las herramientas y los informes antiguos | A2 | Un PR solo de movimiento, sin cambios de lógica. Se actualizan rutas en documentos y herramientas |

---

## 5. Plan de trabajo

Sustituye a R1-R7 del plan. R0 (auditoría) se mantiene, con esta clasificación como criterio.

**Ramas.** `main` no recibe nada hasta que la medición confirme la Score: es la referencia fija (`eaeadaa`, `crafter-general-v4`) contra la que se compara todo.
- La reorganización vive en la rama de integración **`reorg/componentes`**.
- Cada paso sale de ella en su propia rama (`reorg/r0-inventario`, `reorg/a1-registro`…) y vuelve a ella con un PR y un commit de merge, nunca *squash*.
- Las etiquetas intermedias (`reorg-a8`, `reorg-b1`…) se ponen en `reorg/componentes`.
- Solo cuando se cumpla el criterio de D17 sobre la rama completa, `reorg/componentes` se fusiona en `main` con un único PR, y entonces se etiqueta `crafter-general-v5`.

### Fase A: reorganización, mismo JSON (etiqueta `reorg-a8` en `reorg/componentes`)

| Paso | Qué | Notas |
|---|---|---|
| R0 | Inventario (`docs/R0_INVENTARIO.md`) y correcciones a este documento | Hecho el 23/11/2026: corrigió D4, D7, D15 y el orden A5 → A4 |
| A1 | Registro declarado (D3): `añade` y `sustituye`, nombres únicos, orden, cuerpo, informe de conocimiento | Sobre el código actual; con los registros de hoy, todo idéntico |
| A3 | Pasos del latido: preatención, plasticidad y regulación (D1, D5, D6, D12); `Amenaza` sustituye a `ida/core/peligro.py` | **Hecho** (23/11/2026, `docs/A3_PROGRESO.md`). Única dependencia de `ida/core` hacia `ida/sistemas`: `Memoria` importa `Peligros` en su constructor, hasta A7 |
| A5a | Cuerpo cuadrícula (D10): el registro admite un cuerpo (`Registro(cuerpo=Cuadricula())`); `MapaLocal` y `ModeloDirecto` salen de `_aprender_mapa` a `ida/cuerpos/cuadricula/` y leen piezas, no la Observación | Su plasticidad se llama en el mismo punto del latido que hoy `_aprender_mapa`. La geometría y el buscador de posturas se mueven en A6, con `Recinto`: moverlos antes haría que `ida/sistemas` importara un cuerpo (D2) |
| A5b | Actuar con primitivas (D9): el `Motor` del cuerpo traduce la intención a primitivas, con `max_sinergia = 2`; el Core ejecuta primitivas; el éxito de cada intención lo juzga Crafter, no su adaptador | Va antes que A4 (D4): da la cuenta de primitivas |
| A4 | La Observación, solo para los sensores (D4): los rasgos de Crafter, a `ValoracionCrafter`; los requisitos leen piezas | `rasgos_declarados` vacío en Crafter |
| A6 | Crafter a su carpeta (D16), con la geometría y el buscador de posturas a `ida/cuerpos/cuadricula/`; activaciones por registro y constantes al `Perfil` (D15) | **A6a hecho** (23/11/2026, `docs/A6A_PROGRESO.md`): opcionales por registro y `Perfil.escala`. Queda A6b: mover ficheros. Decide la DUDA de `PerseguirMetas` (lee `mem.casillas`, `s3.py:552`) |
| A7 | Memoria por secciones con dueño (D7); `Peticion` a Reaccionar (D11); memoria a corto plazo (D13) | Legado por sección; misma herencia |
| A2 | Estructura de paquetes (D2) | Al final de la fase A, porque solo mueve ficheros; `test_pureza` con las nuevas reglas de importación |
| A8 | Tests de criterios (D8, D5), documentación y medición de 100 000 pasos | Etiqueta `reorg-a8`; el autor decide si se fusiona en `main` ya o tras la fase B |

### Fase B: cambios de conducta (uno por PR, criterio D17)

| Paso | Qué |
|---|---|
| B1 | `max_sinergia = 1`: una primitiva por latido |
| B2 | Regulación con lo sentido en el propio latido |
| B3 | Poda por arousal mínimo en `ev` |
| B4 | Episodios formados desde la memoria a corto plazo, si su formación cambia |
| B5 | Quitar el corte de 14 entidades de `observar` en Crafter (hoy prioriza «primero los peligrosos»): elegir a qué atender es atención y valoración del organismo, no del mundo. La percepción entrega todo lo visible y la amplitud de la Onda decide; `obs.cuerpo["vista"]` desaparece |

Después: V1 a V3 y M1 a M7 del plan, con M1 reformulado (D14).

---

## 6. Qué cambia respecto al plan anterior

- **Sección 0.2, resuelta:**
  - pregunta 1: D11;
  - pregunta 2: D7;
  - pregunta 3: D4 y D5;
  - pregunta 4: D5 y D7 (`Amenaza`);
  - pregunta 5: D14;
  - pregunta 6: queda para R0, con estas decisiones como criterio.
- **Sección 2.3:** `Anticipacion` no es de la fase (sección 1).
- **R1.1 y R2:** el registro ya existía; A1 lo amplía.
- **Nuevo:** preatención, plasticidad, regulación, capa motora con sinergias, familia de cuerpos, `rasgos_declarados` e informe de conocimiento del mundo.
- **M1 reformulado** (D14).

---

## 7. Cómo se cambia este diseño

El diseño se actualiza con los resultados, pero nunca de pasada:

1. **Un resultado lo motiva** (una medición, un diagnóstico o la auditoría R0), citado por su fichero.
2. **Se modifica la decisión aquí:** se edita la D afectada (o se añade una nueva), con una línea en el registro de cambios de abajo que diga qué cambió, por qué y con qué resultado.
3. **Se actualiza `componentes.toml`** (destino, clase, registran o decisión) y se regenera el mapa.
4. **El autor lo aprueba** en un PR propio, separado de la implementación.

Mover piezas hacia su destino (actualizar `hoy`) no es un cambio de diseño: va en el PR de cada paso.

### Registro de cambios del diseño

| Fecha | Decisión | Cambio | Motivo |
|---|---|---|---|
| 22/11/2026 | D1–D17 | Versión inicial | Sección 0 del plan; flujo de alto nivel del autor |
| 23/11/2026 | D3, D7 | Especificación en `componentes.toml` con test; reglas de cambio (esta sección) | Que el diseño no se pervierta a la ligera y se actualice con los resultados |
| 23/11/2026 | Sección 5 | Rama de integración `reorg/componentes`; nada entra en `main` hasta confirmar la Score | Decisión del autor |
| 23/11/2026 | D5, sección 5 | `Exterocepcion` emite con arousal 0; A5 se parte en A5a (cuerpo) y A5b (primitivas); A2 pasa al final de la fase A | Resultado de A3 (`docs/A3_PROGRESO.md`) |
| 23/11/2026 | D4, D7, D15, sección 5 | Novedad con la cuenta propia de primitivas (A5 antes que A4); metas a `Requisito`; escrituras delegadas; `Alimentarse` pregunta por el registro; `invariancia` no se regenera en la fase A | `docs/R0_INVENTARIO.md`, secciones B, D, F y H |
| 23/11/2026 | D4, sección 5 | `vista` en bruto para el Motor; B5 nuevo | Bloqueo de A5b E1 (`docs/A5B_PROGRESO.md`) |
| 23/11/2026 | D9 | Primitivas al ejecutar; el éxito lo juzga el cuerpo | A5b |
| 23/11/2026 | D5 | `Saliencia` corre siempre la última de la preatención | A4 (`docs/A4_PROGRESO.md`): `ValoracionCrafter` se registra después de ella |
