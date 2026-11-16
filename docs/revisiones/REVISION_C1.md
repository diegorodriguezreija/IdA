# Revisión C1 — Infraestructura del bucle y S1

Fecha: 16 de noviembre de 2026  
Rama: `feature/bloque-c`  
Carácter: Solo lectura (sin modificaciones de código ni commits)

---

## 1. Coherencia de nombres

Búsqueda de nombres antiguos (`Escena`, `Ejecucion`, `ImpulsoS1/S2/S3`, `PredicadoProposicion`, `Soma.presupuesto`) en código, tests, comentarios y documentación vigente (excluidos `docs/DISENO_FRAMEWORK_BASE.md` y `docs/PLAN_EVOLUCION_NUCLEO.md` por estar marcados expresamente como históricos).

| Fichero | Línea | Descripción |
|---|---|---|
| `ida/core/marcapasos.py` | 8 | Comentario en docstring: referencia histórica a `Soma.presupuesto` como origen de la fórmula. |
| `tests/test_core.py` | 315 | Nombre de función de test: `def test_presupuesto_varia_con_el_estado():` (prueba la clase `Marcapasos`). |
| `docs/MEDICIONES_BLOQUE_B.md` | 38 | Documentación vigente: mención retrospectiva `Soma.presupuesto, ahora Marcapasos.ritmo`. |
| `docs/PLAN_IMPLEMENTACION.md` | 41 | Tabla del bloque A: registro del paso A1 (`Escena pasa a Exterocepcion`). |
| `docs/PLAN_IMPLEMENTACION.md` | 42 | Tabla del bloque A: registro del paso A2 (`Ejecucion pasan a Accion`). |
| `docs/PLAN_IMPLEMENTACION.md` | 43 | Tabla del bloque A: registro del paso A3 (`ImpulsoS1/S2/S3 pasan a Impulso`). |
| `docs/PLAN_IMPLEMENTACION.md` | 46 | Tabla del bloque A: registro del paso A6 (`PredicadoProposicion se divide en Predicado y Proposicion`). |
| `docs/PLAN_IMPLEMENTACION.md` | 47 | Tabla del bloque A: registro del paso A7 (`La lógica de Soma.presupuesto pasa a Marcapasos`). |
| `docs/PLAN_IMPLEMENTACION.md` | 187 | Nota del bloque A: referencia a registros antiguos en `memoria.db` con tipo `Escena`. |
| `docs/REDISENO_BASE.md` | 13, 17, 18 | Decisión 1: título, motivo y alcance del renombre de `Escena` a `Exterocepcion`. |
| `docs/REDISENO_BASE.md` | 22 | Decisión 2: descripción del problema previo con `ImpulsoS1`. |
| `docs/REDISENO_BASE.md` | 38 | Decisión 3: especificación de que `Ejecucion` pasa a llamarse `Accion`. |
| `docs/REDISENO_BASE.md` | 129, 132 | Decisión 10: referencias a `ImpulsoS1` e `ImpulsoS2`. |
| `docs/REDISENO_BASE.md` | 140, 141, 145 | Decisión 10: tabla y texto con `ImpulsoS1` e `ImpulsoS2`. |
| `docs/REDISENO_BASE.md` | 150 | Decisión 12: mención de la división de `PredicadoProposicion`. |
| `docs/REDISENO_BASE.md` | 167 | Decisión 13: referencia a `ImpulsoS3`. |
| `docs/REDISENO_BASE.md` | 175, 177 | Decisión 14: referencias a `ImpulsoS2`, `Ejecucion` y renombres de `ImpulsoS1/S2/S3`. |
| `docs/REDISENO_BASE.md` | 191 | Decisión 15: referencia a la lógica previa en `Soma.presupuesto`. |
| `docs/REDISENO_BASE.md` | 301, 302, 307, 309 | Historial de cambios del borrador con menciones a `Escena`, `Ejecucion`, `ImpulsoS2` e `ImpulsoS3`. |

*Nota:* En el código ejecutable (`ida/`) y en las aserciones de los tests (`tests/`), la sustitución de los nombres antiguos es total; solo subsisten menciones documentales o explicativas del cambio.

---

## 2. Regla 3 de AGENTS.md

Accesos a `env._world` o al estado interno del mundo que permanecen en `ida/mundos/`.

| Fichero | Línea | ¿Es componente de decisión? | Descripción |
|---|---|---|---|
| `ida/mundos/crafter.py` | 109 | No | `MundoCrafter.iniciar`: inicializa el simulador y obtiene referencia interna. |
| `ida/mundos/crafter.py` | 176 | No | `MundoCrafter._entidades`: sensor exteroceptivo que lee celdas para emitir entidades. |
| `ida/mundos/crafter.py` | 223 | No | `MundoCrafter._construir_lugares`: sensor que lee celdas para construir entidades tipo lugar. |
| `ida/mundos/crafter.py` | 353 | No | `MundoCrafter.ver`: visualización de depuración en consola que lee `daylight`. |
| `ida/mundos/crafter.py` | 457 | Sí (`PlanTecnologico`) | Almacena referencia directa `self.mundo` en el componente. |
| `ida/mundos/crafter.py` | 467-469 | Sí (`PlanTecnologico`) | Lee `self.mundo.env._world` y `jugador.pos` para comprobar adyacencia de materiales en el grid. |
| `ida/mundos/crafter.py` | 472 | Sí (`PlanTecnologico`) | Lee `self.mundo.constantes` para consultar requerimientos de recetas. |
| `ida/mundos/crafter.py` | 488-490 | Sí (`PlanTecnologico`) | Lee `self.mundo.env._world`, `jugador.pos` y `jugador.facing` como oráculo de hierba para plantar. |
| `ida/mundos/crafter.py` | 494 | Sí (`PlanTecnologico`) | Lee `self.mundo.env._world.daylight` directamente para decidir si duerme de día. |
| `ida/mundos/crafter.py` | 499-503 | Sí (`PlanTecnologico`) | Lee `self.mundo.env._world` y `jugador.pos` para detectar retoños en celdas vecinas. |
| `ida/mundos/crafter.py` | 510 | Sí (`PlanTecnologico`) | Llama a `self.mundo.inventario()` para consultar inventario real del juego fuera de la percepción. |
| `ida/mundos/crafter.py` | 511 | Sí (`PlanTecnologico`) | Llama a `self.mundo.logros()` para consultar logros desbloqueados del simulador. |
| `ida/mundos/crafter.py` | 520 | Sí (`PlanTecnologico`) | Lee recetas en `self.mundo.constantes.make`. |
| `ida/mundos/crafter.py` | 546 | Sí (`PlanTecnologico`) | Lee `self.mundo.jugador.pos` para calcular distancias a estructuras de taller. |
| `ida/mundos/crafter.py` | 577 | Sí (`PlanTecnologico`) | Lee `self.mundo.jugador.pos` para calcular distancias al recurso objetivo. |

*Nota:* Las defensas de Crafter (`DefensaArmada` y `CerrarDistancia`) fueron desacopladas en C1.5 y ya no acceden al mundo interno; `PlanTecnologico` quedó aplazado para C3 según la decisión 5 de `docs/C0_CORRESPONDENCIA.md`.

---

## 3. Fuera de alcance

Comparación de `git diff main...feature/bloque-c` frente al encargo estricto de C1 (`docs/PLAN_IMPLEMENTACION.md:142-164`).

| Fichero | Línea | Descripción |
|---|---|---|
| `ida/sistemas/comun.py` | 59-69 | Lógica de «el mal menor» implementada directamente dentro de `Accion` (emite acción sin pieza de estrategia previa). En C0 correspondía a una estrategia genérica de S1 (`seguir_en_movimiento`). |
| `ida/core/onda.py` | 197-202 | Exención en `Onda._limitar`: el Core (`autor.sistema == "CORE"`) queda exento del recorte de fuerza máxima por pieza, ampliando la exención de coste prevista en C1.6. |
| `ida/core/onda.py` | 322-324 | Nuevo método helper `ef(canal)` en `Onda`, no listado en los pasos C1.1 a C1.6. |
| `herramientas/benchmark.py` | 13, 56-78, 128-146 | Instrumentación del benchmark para telemetría de C1 (estrategias activas, abandonos, sustituciones, reflejos, plus decisivo). |
| `docs/MEDICIONES_C1.md` | 1-174 | Documento de resultados y análisis empírico de la pérdida de rendimiento frente a `main`. |

---

## 4. Excepciones transitorias

Usos actuales de las excepciones declaradas en `EXCEPCIONES_TRANSITORIAS` (`ida/core/onda.py:44-47`).

### 4.1. `proponer_accion` (componente cuyo `tipo != "Accion"` emite a `acc["Accion"]`)

| Fichero | Línea | Componente | Descripción |
|---|---|---|---|
| `ida/mundos/archivos.py` | 385 | `Prudencia` (tipo `Impulso`) | Propone `MOVER` para buscar comida en otra carpeta. |
| `ida/mundos/crafter.py` | 485 | `PlanTecnologico` (tipo `Comportamiento`) | Propone `COGER` minerales con herramienta adecuada. |
| `ida/mundos/crafter.py` | 491 | `PlanTecnologico` (tipo `Comportamiento`) | Propone `USAR` retoño en casilla de hierba. |
| `ida/mundos/crafter.py` | 496 | `PlanTecnologico` (tipo `Comportamiento`) | Propone `DORMIR` de día para afrontar la noche. |
| `ida/mundos/crafter.py` | 504 | `PlanTecnologico` (tipo `Comportamiento`) | Propone `COGER` retoño adyacente. |
| `ida/mundos/crafter.py` | 528, 532 | `PlanTecnologico` (tipo `Comportamiento`) | Propone `USAR` mesa de trabajo o receta tecnológica. |
| `ida/mundos/crafter.py` | 550, 561 | `PlanTecnologico` (tipo `Comportamiento`) | Propone `MOVER` hacia estación de trabajo o por ruta hipocampal. |
| `ida/mundos/crafter.py` | 574, 581 | `PlanTecnologico` (tipo `Comportamiento`) | Propone `COGER` o `MOVER` hacia recurso necesario. |
| `ida/sistemas/s2.py` | 141, 146 | `Curiosidad` (tipo `Curiosidad`) | Propone `MOVER` al lugar más nuevo o `COGER` objeto útil. |
| `ida/sistemas/s2.py` | 176, 180 | `Hogar` (tipo `Hogar`) | Propone `MOVER` al hogar o `DORMIR` en él. |
| `ida/sistemas/s2.py` | 226 | `Orientacion` (tipo `Orientacion`) | Propone `MOVER` por ruta hipocampal hacia alimento recordado. |
| `ida/sistemas/s3.py` | 146, 149, 153, 155 | `Comportamiento` (tipo `Comportamiento`) | Propone `MOVER`, `COMER` o `COGER` según deducción lógica. |
| `ida/sistemas/s3.py` | 277, 306, 349 | `Estudio` (tipo `Estudio`) | Propone `LEER` en la biblioteca para reducir incertidumbre. |
| `tests/test_propiedad.py` | 65 | `_Valor` (tipo `Valor`) | Test específico de validación de la excepción transitoria. |

### 4.2. `impulso_modula_accion` (componente `tipo == "Impulso"` modula `Accion`)

| Fichero | Línea | Componente | Descripción |
|---|---|---|---|
| `ida/mundos/archivos.py` | 360 | `Prudencia` (tipo `Impulso`) | Modula arousal (×0,3) y confianza (×0,5) al moverse hacia carpetas con solo veneno. |
| `ida/mundos/archivos.py` | 373 | `Prudencia` (tipo `Impulso`) | Modula arousal (×0,2) y confianza (×0,3) al comer con indicios de daño. |
| `ida/mundos/archivos.py` | 375 | `Prudencia` (tipo `Impulso`) | Modula arousal (×0,5) y confianza (×0,6) por neofobia (especie desconocida). |
| `ida/sistemas/s2.py` | 115 | `Impulso` (tipo `Impulso`) | Modula arousal de acciones según la valencia afectiva de su objetivo (±0,15 × valencia). |
| `ida/sistemas/s3.py` | 178 | `Impulso` (tipo `Impulso`) | Freno prefrontal: modula arousal (×0,4) y confianza (×0,5) de acciones contrarias a lo demostrado. |
| `tests/test_propiedad.py` | 67 | `_Impulso` (tipo `Impulso`) | Test específico de modulación autorizada sobre pieza `Accion`. |

---

## 5. Tests

Cobertura de tests unitarios para `Estrategia`, `Accion`, `Marcapasos` y propiedad de piezas en la `Onda`.

### 5.1. `Estrategia`

| Comportamiento | ¿Tiene test? | Fichero y línea | Frase descriptiva |
|---|---|---|---|
| Creación de pieza y carga inicial | Sí | `tests/test_estrategia.py:39` | Verifica campos `valor_inicial`, `inicio`, estado inicial y estructura de ID. |
| Cálculo de progreso sobre intensidad cruda | Sí | `tests/test_estrategia.py:39` | Comprueba progreso relativo al tramo entre valor inicial y objetivo. |
| Agotamiento: latidos de gracia | Sí | `tests/test_estrategia.py:47` | Verifica que el agotamiento no aumenta durante el periodo de gracia. |
| Agotamiento: subida por falta de progreso | Sí | `tests/test_estrategia.py:47` | Comprueba incremento acumulado de agotamiento si el ritmo es menor al esperado. |
| Agotamiento: bajada con progreso efectivo | Sí | `tests/test_estrategia.py:47` | Verifica reducción de agotamiento al progresar por encima del ritmo esperado. |
| Conservación en `Onda.estrategias` | Sí | `tests/test_estrategia.py:59` | Verifica que las estrategias activas persisten a través de instancias de Onda sucesivas. |
| Cierre de estrategia (`onda.cerrar`) | Sí | `tests/test_estrategia.py:69` | Comprueba que la estrategia se deslista de activas y registra estado `agotada`. |
| Encadenamiento y último recurso en seguridad | Sí | `tests/test_estrategia.py:191` | Verifica transición secuencial ante agotamiento: estrategia A → B → último recurso. |
| Sustitución por estrategia más específica | Sí | `tests/test_estrategia.py:206` | Comprueba reemplazo de estrategia activa por otra de mayor prioridad elegible. |
| Reflejo como estrategia innata corta | Sí | `tests/test_estrategia.py:219` | Verifica activación del reflejo por salto brusco de peligro y no por nivel estático. |
| Elegibilidad y actuación según percepción | Sí | `tests/test_estrategia.py:235` | Comprueba que `DefensaArmada` evalúa salud percibida e inventario de armas. |
| Aprendizaje de valor por feedback | No | — | No hay test de actualización de mérito y tasa de aprendizaje (`_recompensar`). |
| Modulación por apertura de arquetipo | No | — | No se evalúa el peso del rasgo apertura en la exploración de estrategias (`_elegir`). |
| Transición a estado `completada` | No | — | Sin test para el cierre automático cuando la intensidad cruda alcanza el objetivo. |
| Transición a estado `sin_objeto` | No | — | Sin test para el abandono cuando la estrategia deja de ser elegible en el entorno. |
| Cooldown tras abandono de estrategia | No | — | Sin test unitario aislado para el enfriamiento (`enfriamiento_estrategia`). |
| Apagado gradual de prioridad con progreso | No | — | Sin test para la atenuación de arousal en función del avance hacia la meta. |
| Desempate por azar | No | — | Sin test para la resolución aleatoria de empates entre estrategias concurrentes. |

### 5.2. `Accion`

| Comportamiento | ¿Tiene test? | Fichero y línea | Frase descriptiva |
|---|---|---|---|
| Traducción de estrategia activa a propuesta | Sí | `tests/test_estrategia.py:74` | Verifica que `Accion` llama a `actuar()` de la definición y propone a `acc["Accion"]`. |
| Propagación de metadato `origen` | Sí | `tests/test_estrategia.py:74` | Comprueba que `impulso` y `estrategia` viajan desde la propuesta hasta `ef["Accion"]`. |
| Fallback de `mal_menor` en mundos sin espera | No | — | Sin test para la propuesta de `MOVER` cuando no hay acciones y falta `Verbo.ESPERAR`. |
| Omisión de propuesta ante retorno `None` | No | — | Sin test que confirme que si `actuar()` devuelve `None`, no se emite acción. |
| Filtrado por sistema (`p.sistema == self.sistema`) | No | — | Sin test que verifique el aislamiento de estrategias activas pertenecientes a otro sistema. |
| Concurrencia de múltiples estrategias activas | No | — | Sin test para la traducción simultánea de múltiples estrategias del mismo sistema. |

### 5.3. `Marcapasos`

| Comportamiento | ¿Tiene test? | Fichero y línea | Frase descriptiva |
|---|---|---|---|
| Escala de amplitud según energía | Sí | `tests/test_core.py:315` | Comprueba que baja la amplitud cuando desciende la energía corporal. |
| Reducción de amplitud al dormir | Sí | `tests/test_core.py:325` | Verifica fijación de amplitud en 20 unidades durante el sueño. |
| Acortamiento del plazo de frecuencia ante peligro | Sí | `tests/test_core.py:321` | Comprueba reducción de hasta un 30 % del periodo ante señal de peligro. |
| Potencia proporcional a la amplitud | Sí | `tests/test_core.py:323` | Verifica relación `potencia == amplitud * FUERZA_POR_PIEZA`. |
| Incremento por taquicardia (`agotado_previo`) | No | — | Sin test para el aumento al 150 % tras agotamiento de amplitud en el latido previo. |
| Suelo mínimo de amplitud (`max(5, ...)`) | No | — | Sin test para la cota inferior ante combinaciones extremas de fatiga. |
| Sustitución de componente en `Organismo` | No | — | Sin test para la inyección de una implementación alternativa de marcapasos. |

### 5.4. Propiedad de piezas en la Onda

| Comportamiento | ¿Tiene test? | Fichero y línea | Frase descriptiva |
|---|---|---|---|
| Rechazo de emisión de tipo ajeno (`PiezaAjena`) | Sí | `tests/test_propiedad.py:39` | Verifica excepción al percibir o registrar piezas no pertenecientes al tipo del autor. |
| Modificación reservada al tipo dueño | Sí | `tests/test_propiedad.py:49` | Comprueba edición válida por el propietario y rechazo con `PiezaAjena` a terceros. |
| Registro de auditoría de modificaciones | Sí | `tests/test_propiedad.py:49` | Verifica que cada cambio de arousal y carga se anota en el historial de la pieza. |
| Excepciones transitorias acotadas | Sí | `tests/test_propiedad.py:62` | Valida permisos transitorios (`proponer_accion` e `impulso_modula_accion`). |
| Rechazo de modificaciones no cubiertas por excepción | Sí | `tests/test_propiedad.py:72` | Comprueba que `Impulso` no puede mutar campos no autorizados de una `Accion`. |
| Exención del Core en módulo exento | Sí | `tests/test_propiedad.py:78` | Verifica escritura sin peaje cuando `onda.exento == True`. |
| Exención del Core con `AutorCore` | Sí | `tests/test_atencion.py:99` | Comprueba escritura sin coste ni recorte de fuerza firmada como `CORE.Organismo`. |
| Control de propiedad en `onda.activar` | Sí | `tests/test_estrategia.py:59` | Verifica que solo un componente de tipo `Estrategia` puede activar estrategias. |
| Acotación de registro (`MAX_REGISTRO`) y metadatos | Sí | `tests/test_propiedad.py:88` | Comprueba límite de tamaño del historial y conservación de metadatos (`audit`). |
| Ausencia de mutaciones y escrituras directas | Sí | `tests/test_propiedad.py:110` | Inspección estática de código que prohíbe escrituras directas en `sistemas` y `mundos`. |
| Control de propiedad en `onda.cerrar` | No | — | Sin test que fuerce `PiezaAjena` intentando cerrar una estrategia desde un autor ajeno. |
| Rechazo en `proponer` para tipos ajenos distintos de `Accion` | No | — | Sin test que compruebe fallo al intentar proponer piezas que no sean `Accion`. |
| Auditoría específica de la operación `activar` | No | — | Sin aserción directa de la presencia de `op == "activar"` en `pieza.registro`. |
