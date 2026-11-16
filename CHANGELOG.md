# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Unreleased]

### Núcleo y Sistemas (Fases 1, 2, 3 y 4a del Plan de Evolución)
- **Hipocampo en el Core (`ida/core/memoria.py`, `ida/core/latido.py`):** grafo topológico de transiciones (`mapa: Dict[str, Dict[str, Arista]]`), células de lugar (`donde_esta(clase)`), búsqueda BFS acotada (`ruta`), poda LRU (`MAX_NODOS_MAPA = 200`) y olvido en `consolidar()` sin herencia. Validado con 100% de invariancia con semilla en infraestructura pasiva.
- **Navegación y Orientación (`ida/sistemas/s2.py`):** `Hogar` utiliza rutas topológicas cuando el refugio queda fuera de la vista inmediata; nuevo componente `Orientacion` en `S2.Reaccionar` para regresar hacia fuentes nutritivas recordadas cuando hay necesidad.
- **Migración hexagonal en Crafter (`ida/mundos/crafter.py`):** eliminada la estructura `self.hitos` del adaptador del mundo; `PlanTecnologico` ahora consulta el hipocampo del individuo traduciendo localmente los nombres de receta.
- **Replay Inverso de Trayectorias al Dormir (Fase 2):** consolidación de episodios recientes en sueño SWS con eliminación de ciclos/bucles triviales (`_eliminar_bucles_trayectoria`), descuento temporal $\gamma=0.8$, modulación de `Arista.valor_replay` y desempate heurístico determinista en `Memoria.ruta()`. Invarianza 100% en mundos sin sueño (`Snake`, `Ajedrez`).
- **Confianza Ponderada por Fuentes de Evidencia (Fase 3):** descomposición epistémica en `Proposicion` entre confianza empírica (`c_exp`, peso dinámico $w_{exp} = 1 + \text{conf} + \text{ref}$) y autoridad externa (`c_aut`, $w_{aut}$); derivación determinista de `Arquetipo.deferencia` a partir de responsabilidad y apertura; preservación intacta de la barrera de Weismann en `legado()`.
- **Biblioteca de Autoridad con Atención Sostenida (Fase 4a):** puerto hexagonal abstracto `ida/core/biblioteca.py` con adaptadores externos (`nula`, `fija`, `erronea`) protegidos por `test_pureza`; nuevo verbo interno `Verbo.LEER` ejecutado como `ESPERAR`; componente `Estudio` en `S3.Reaccionar` con lectura dependiente de atención sostenida latido a latido, cooldown y relectura; persistencia en tabla `lecturas` y espera bloqueante determinista en `Organismo.vivir()` entre latidos (fuera de la guillotina).
- **Arnés y Plan de Evolución (`AGENTS.md`, `docs/PLAN_EVOLUCION_NUCLEO.md`):** reglas de consistencia biológica sin atajos y hoja de ruta en cuatro fases.

### Telemetría y Experiencia de Usuario (UI/UX)
- **Ficha Expandible / Modal de Individuo:** visor interactivo para inspeccionar genoma, arquetipo (Big Five), logros específicos del mundo con iconografía (herramientas de Crafter, capturas de Ajedrez, etc.), reglas epistémicas demostradas, fijado 📌, descarga de JSON reproducible y restauración inmediata en la antesala con un clic.
- **Rediseño y Consolidación de Tarjetas:** reestructuración a 4 columnas compactas en fila superior (Carácter, Cuerpo, Latido, Tribunal) con altura optimizada (`max-height: 250px; overflow-y: auto;`), fila compartida de Memoria y Linaje a doble ancho, y retirada de métricas redundantes o poco visuales (mapa ASCII).
- **Evolución del Linaje por Selección Natural:** tabla ordenada por fitness descendente (mejores individuos arriba), política de retención con purga por la base (peores individuos abajo) respetando los elementos fijados 📌 y el Top 5 histórico.
- **Protección contra Pérdida Involuntaria:** `tabula_rasa` desactivado por defecto en la antesala y verificación dinámica contra sobreescrituras accidentales de linajes existentes.
- **Detección de Fin de Simulación:** indicador fidedigno `⏹️ finalizada` en el dashboard al concluir las vidas programadas.
- **Documentación Visual:** incorporación de GIF introductorio animado (`docs/img/demo.gif`) y capturas de alta definición de la antesala (`room.png`) y el dashboard (`dashboard.PNG`, `dashboard2.PNG`, `dashboard3.PNG`).

## [1.0.0]

Primera versión publicada: un framework genérico (Componentes con tres barridos, Módulos, Sistemas y la Onda) separado de los mundos.

### Framework base
- `ida/core`: Pieza, Onda (`ei`, `ev`, `acc`, `ef`), guillotina cooperativa, Soma con presupuesto adaptativo, Memoria (expectativas, episodios, proposiciones en hipótesis, demostradas o refutadas, aversión gustativa, trauma mortal), linaje con herencia como hipótesis, Azar con semilla y persistencia SQLite en dos velocidades.
- `ida/sistemas`: S1 (supervivencia), S2 (valor) y S3 (verdad), y un Tribunal que pondera urgencia y confianza según el estrés.
- Contrato `Mundo` con vocabulario común de rasgos y verbos. Si el mundo no admite esperar, S1 propone el mal menor.
- La Onda apunta cuándo empieza y termina cada fase del latido (`Onda.fases`), para la observabilidad.

### Mundos
- Mínimo, archivos (con su sandbox), Snake (playsnake.org con Playwright), Crafter (estado simbólico, repetible con semilla) y ajedrez (rival local corregido, GPL-3.0-or-later).
- Optimizaciones solo en el código de cada mundo: `Defensa` (mínimo y archivos), `Prudencia` (archivos), latido de 60 ms y causa de muerte proyectada (Snake), plan con logros baratos y sueño de día (Crafter), y remate o búsqueda de tablas (ajedrez). Cifras en [`doc-repositorio/05_METRICAS_E_HITOS.md`](doc-repositorio/05_METRICAS_E_HITOS.md).

### Telemetría y observabilidad
- Panel propio en vivo (`--ver`), sin dependencias, por Server-Sent Events.
- OpenTelemetry (`--otel`, extra `observabilidad`): cada latido es una traza con un tramo por fase; métricas del latido, decisiones, experiencia, cuerpo y conocimiento.
- `docker compose`: IdA, OpenTelemetry Collector, Jaeger, Prometheus y Grafana con el panel provisionado.

### Ingeniería
- `pyproject.toml` con extras por mundo, comando `ida`, `ruff`, `mypy` y 64 tests.
- GitHub Actions: ruff y mypy; tests en Python 3.12 y 3.15, con y sin las dependencias de los mundos.
- Dockerfile multietapa y devcontainer.
- Licencia Apache-2.0, con el mundo de ajedrez aislado bajo GPL-3.0-or-later y un test que vigila esa frontera.
