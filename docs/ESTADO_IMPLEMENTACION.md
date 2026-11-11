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
| 10. **Fase 2 del Plan de Evolución:** Replay inverso de trayectorias al dormir (`Memoria.consolidar()`, eliminación de bucles, `valor_replay`, desempate en `ruta()`) | hecho (74 tests) |
| 11. **Fase 3 del Plan de Evolución:** Confianza ponderada por fuente de evidencia (`c_exp` vs `c_aut`, `w_exp`, `Arquetipo.deferencia`, Weismann intacto) | hecho (77 tests) |
| 12. **Fase 4a del Plan de Evolución:** Biblioteca de autoridad con atención sostenida (`ida/core/biblioteca.py`, `ida/bibliotecas/{nula,fija,erronea}`, `Verbo.LEER`, componente `Estudio` en S3, persistencia `lecturas`, espera fuera de latido) | hecho (85 tests) |

**Cambios en `ida/core` en la fase 7**, con permiso expreso y en commits propios: anotaciones de tipos para mypy (sin cambiar la lógica; vidas con semilla idénticas antes y después) y el registro pasivo de fases de la Onda (`Onda.fases`) para la observabilidad. `ida/sistemas` no se tocó.

**Cambios en `ida/core` e `ida/sistemas` en las fases 9 a 12 (Fases 1 a 4a de evolución):** autorización expresa documentada en [`PLAN_EVOLUCION_NUCLEO.md`](PLAN_EVOLUCION_NUCLEO.md).
- **Fase 1:** `Arista`, `RecuerdoLugar`, `mapa`, `donde_esta` y `ruta` BFS en `Memoria`, navegación de `Hogar` y componente `Orientacion` en `S2`, y eliminación de `self.hitos` en Crafter.
- **Fase 2:** *Replay* inverso de trayectorias en `Memoria.consolidar(ahora)` con eliminación de bucles mediante reconstrucción sin ciclos, descuento temporal $\gamma=0.8$, modulación de `Arista.valor_replay` y desempate en `ruta()`. Invarianza 100% en mundos sin sueño (`Snake`, `Ajedrez`).
- **Fase 3:** Confianza epistémica ponderada por fuentes en `Proposicion` (`c_exp` vs `c_aut`), peso dinámico de la experiencia empírica, derivación analítica de `Arquetipo.deferencia` (sin tocar el PRNG `Azar`) y preservación estricta de la barrera de Weismann (la autoridad no verificada no se hereda).
- **Fase 4a:** Puerto hexagonal abstracto `ida/core/biblioteca.py`, adaptadores `ida/bibliotecas/{nula, fija, erronea}` (aislados por `test_pureza`), verbo interno `Verbo.LEER` ejecutado en el mundo como `ESPERAR`, componente `Estudio` en `S3.Reaccionar` con lectura dependiente de atención sostenida latido a latido, tabla `lecturas` en SQLite y espera bloqueante determinista en `Organismo.vivir()` entre latidos (fuera de la guillotina).

## Pendiente para la fase de ajustes (tras probar los mundos)

*Estado tras la fase 6. Las cifras, en [`doc-repositorio/05_METRICAS_E_HITOS.md`](../doc-repositorio/05_METRICAS_E_HITOS.md).*

- **Snake:** resuelto en buena parte. Con un latido de 60 ms y las casillas mortales ofrecidas solo como último recurso, la media pasa de unos 232 a 916 puntos (máximo 1605) y las causas de muerte se identifican. El afecto sigue pasando mucho tiempo en PANICO/ALERTA cuando el cuerpo es largo.
- **Mundo mínimo:** el lobo sigue siendo letal. Con `Defensa`, la vida media pasa de 141 a 198 latidos.
- **Archivos:** resuelto el comer tóxicos (de 7,2 a 2,2 mordiscos por vida) con `Prudencia`. La vida media pasa de 223 a 270 latidos; se muere sobre todo de hambre tardía. Visto en el panel: al final de la vida, agotado y hambriento, alterna dormir y «esperar sin candidatos» en vez de ir a por comida.
- **Crafter:** sigue muriendo pronto, sobre todo de noche. Logros por vida: de 6,6 a 8,2 (la duración de la vida no mejora). Ya es repetible con semilla. Pendiente: refugio nocturno (rodearse de piedra) y combate con espada. Un componente de defensa simple empeoró y se descartó.
- **Ajedrez:** remata mejor (d1: 7 victorias de 8; d2: 3 victorias de 8); contra 3 ply sigue perdiendo. **No se ampliará la búsqueda del sensor:** calcularía por IdA (principio 7 de [`DISENO_FRAMEWORK_BASE.md`](DISENO_FRAMEWORK_BASE.md)). Si algún día ve más lejos, será porque la mente imagine (barrido proactivo con presupuesto del latido), no porque el mundo calcule.
- **Contrato:** se añadió `Observacion.dormido` para mundos que deciden cuándo se duerme (Crafter ignora las acciones mientras el jugador duerme).
- **Regla genérica:** si el mundo no admite ESPERAR, el Tribunal no acecha y S1 propone el mal menor cuando nadie propone nada.
