# Estado de la implementación del framework base

Diseño: [`DISENO_FRAMEWORK_BASE.md`](DISENO_FRAMEWORK_BASE.md).

## Decisiones tomadas al implementar

- **Rasgos comunes:** `proximidad`, `nutritivo`, `peligro`, `novedad`, `recurso`, `lugar`, `agente`.
- **Verbos comunes:** `MOVER`, `COMER`, `ATACAR`, `COGER`, `SOLTAR`, `USAR`, `DORMIR`, `ESPERAR`, más `ACECHAR` (interno del Tribunal).
- **Lugares.** Los destinos posibles son entidades de la escena con el rasgo `lugar`. El mundo calcula los rasgos de cada destino; por ejemplo, el `nutritivo` de una casilla indica cuánto acerca a la comida. Así S1 puede «acercarse» o «huir» sin saber de geometría.
- **Una observación por latido.** El mundo entrega una sola `Observacion` por latido. Los componentes de Sentir del Core la convierten en piezas.
- **Actuadores.** El mundo declara sus verbos. El módulo Actuar del Core tiene el Tribunal más un actuador por verbo.
- **Snake y aprendizaje de la muerte.** Cuando el mundo notifica la muerte en el último latido, el Core aprende de inmediato de la acción terminal (`_aprender_de_la_muerte`) fijando la causa (`pared` o `cuerpo`) con trauma mortal en la memoria (`demostrada`) para que pase al linaje. El sensor evalúa el peligro de encierro mediante relleno por inundación comparado con la longitud del cuerpo.

## Fases

| Fase | Estado |
|---|---|
| 0. `ida/core`, `ida/sistemas`, mundo mínimo, tests | hecho (39 tests) |
| 1. Mundo de archivos + telemetría | hecho (43 tests) |
| 2. Snake | hecho (47 tests) |
| 3. Crafter | hecho (51 tests) |
| 4. Ajedrez | hecho (56 tests) |
| 6. Optimizar el código de cada mundo (sin tocar el framework base) y renovar la telemetría | hecho (58 tests) |
| 7. Preparar la publicación: licencia, `pyproject.toml`, ruff, mypy, CI, Crafter repetible, observabilidad (OpenTelemetry, Prometheus, Jaeger, Grafana) y Docker | hecho (64 tests) |
| 8. Evolución UI/UX (ficha modal, linaje ordenado, protección tabula rasa) y Crafter biológico (`defensa`, `hitos`) | hecho (68 tests) |
| 9. **Fase 1 del Plan de Evolución:** Hipocampo en el Core (`Memoria.mapa`, `donde_esta`, `ruta` BFS), `Hogar` con ruta y `Orientacion` en `S2`; retirada de `hitos` en Crafter | hecho (71 tests) |

**Cambios en `ida/core` en la fase 7**, con permiso expreso y en commits propios: anotaciones de tipos para mypy (sin cambiar la lógica; vidas con semilla idénticas antes y después) y el registro pasivo de fases de la Onda (`Onda.fases`) para la observabilidad. `ida/sistemas` no se tocó.

**Cambios en `ida/core` e `ida/sistemas` en la fase 9 (Fase 1 de evolución):** autorización expresa documentada en [`PLAN_EVOLUCION_NUCLEO.md`](PLAN_EVOLUCION_NUCLEO.md). Se integraron `Arista`, `RecuerdoLugar`, `registrar_transicion`, `registrar_donde`, `donde_esta` y `ruta` en `Memoria` (con poda `MAX_NODOS_MAPA = 200` y olvido al dormir en `consolidar()`, verificando **100% invariancia con semilla** antes de activar consumidores), navegación del `Hogar` y componente `Orientacion` en `S2`, y se migró Crafter eliminando `self.hitos` del adaptador.

## Pendiente para la fase de ajustes (tras probar los mundos)

*Estado tras la fase 6. Las cifras, en [`doc-repositorio/05_METRICAS_E_HITOS.md`](../doc-repositorio/05_METRICAS_E_HITOS.md).*

- **Snake:** resuelto en buena parte. Con un latido de 60 ms y las casillas mortales ofrecidas solo como último recurso, la media pasa de unos 232 a 916 puntos (máximo 1605) y las causas de muerte se identifican. El afecto sigue pasando mucho tiempo en PANICO/ALERTA cuando el cuerpo es largo.
- **Mundo mínimo:** el lobo sigue siendo letal. Con `Defensa`, la vida media pasa de 141 a 198 latidos.
- **Archivos:** resuelto el comer tóxicos (de 7,2 a 2,2 mordiscos por vida) con `Prudencia`. La vida media pasa de 223 a 270 latidos; se muere sobre todo de hambre tardía. Visto en el panel: al final de la vida, agotado y hambriento, alterna dormir y «esperar sin candidatos» en vez de ir a por comida.
- **Crafter:** sigue muriendo pronto, sobre todo de noche. Logros por vida: de 6,6 a 8,2 (la duración de la vida no mejora). Ya es repetible con semilla. Pendiente: refugio nocturno (rodearse de piedra) y combate con espada. Un componente de defensa simple empeoró y se descartó.
- **Ajedrez:** remata mejor (d1: 7 victorias de 8; d2: 3 victorias de 8); contra 3 ply sigue perdiendo. **No se ampliará la búsqueda del sensor:** calcularía por IdA (principio 7 de [`DISENO_FRAMEWORK_BASE.md`](DISENO_FRAMEWORK_BASE.md)). Si algún día ve más lejos, será porque la mente imagine (barrido proactivo con presupuesto del latido), no porque el mundo calcule.
- **Contrato:** se añadió `Observacion.dormido` para mundos que deciden cuándo se duerme (Crafter ignora las acciones mientras el jugador duerme).
- **Regla genérica:** si el mundo no admite ESPERAR, el Tribunal no acecha y S1 propone el mal menor cuando nadie propone nada.
