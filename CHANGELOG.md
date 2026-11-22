# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Unreleased]

### Deuda 14: cadena de herramientas (cumplida en parte)
- **Lote por estación (14.2, `PerseguirMetas`, S3):** las metas que piden la misma estación de trabajo se planifican juntas. Primero se reúne todo su material (también el de colocar la estación) y después se va a la estación; el lote sigue en curso hasta tener el material. Siempre activo.
- **Retirado 14.3** («aprovechar la estación mientras está al alcance»): en el diagnóstico no añadía nada sobre 14.2.
- **Crafter declara su ritmo** por turnos, con un plazo base de 1000 ms (14.0); el JSON de 3000 pasos no cambia.
- **`resumen_evaluacion.py --pareada-conjunta`:** comparación pareada que junta varias semillas, con bootstrap estratificado por semilla. Desde ahora los criterios se fijan sobre ella antes de medir.
- **Cifras** (100 000 pasos, semillas 31 y 32, frente a `base_v2`): Score 14,83 % y 15,98 % (antes, 14,04 % y 15,45 %); diferencia pareada +0,76 y +0,57 puntos, sin que ningún IC excluya el 0; conjunta, +0,64 [0,04; 1,29] (no prevista de antemano). `make_wood_sword` +5,50 y +7,12, y el pico y la espada de piedra suben, todos con IC que excluyen el 0. Coste: `collect_drink` −3,40 en la semilla 31 y `eat_cow` −2,28 en el conjunto. El pico de madera baja −0,27 en la semilla 32 (criterio 2 sin cumplir).
- **Diagnósticos:** `herramientas/diagnostico_deuda14.py` y `herramientas/diagnostico_sin_meta.py` (`docs/DIAGNOSTICO_DEUDA14.md`).

### Método de medición
- Guillotina lógica (--plazo-logico): plazo en operaciones en lugar de milisegundos; evaluaciones idénticas aunque la máquina esté cargada.
- Comparación pareada episodio a episodio (resumen_evaluacion.py --pareada), con IC 95 % por bootstrap pareado.
- evaluar_crafter.py guarda plazo_logico y por_episodio (pasos, causa de muerte, vivo y logros).

### Fase de generalización en Crafter: paso 6 (defensa general) y pilar 1
- **Peligro aprendido** (`ida/core/peligro.py`):
  - daño por contacto y daño dormido;
  - alcance;
  - emisores por contingencia (el individuo descubre que las flechas vienen de los esqueletos).

  La base calcula el peligro solo cuando el mundo no da el suyo.
- **`Afrontar`** (S1): decide si luchar o huir según la salud y la eficacia aprendida. Además, puede pedir un arma al planificador como meta instrumental.
- **Borradas de Crafter** `DefensaArmada`, `CerrarDistancia`, `PELIGRO_MANUAL` y la atribución del daño por geometría. `estrategias_propias()` de Crafter queda vacío: **pilar 1 cumplido**.
- **Línea general:** 14,0–15,5 % de Crafter Score (antes, 12,8–13,6 %); `defeat_skeleton` del 0-0,5 % al 5-8 %.

### Fase de generalización en Crafter (pasos 2, 5, 0 y 3)
- **Manual declarativo** (`ida/mundos/crafter_manual.json`, estricto y ampliado) con citas verificadas por `herramientas/verificar_manual.py`.
- **Requisitos de acción y planificador general** (`PerseguirMetas`, S3), con inducción de requisitos, metas instrumentales y reutilización de lo construido.
- **Aliestesia aprendida por contingencia** (`Memoria.satisface`).
- **Modelo del cuerpo, mapa local y refugio general** (`Proteger`, S1).
- **Borradas de Crafter** `PlanTecnologico`, `RefugioNocturno`, `HOSTILES` y `_deseo`.
- **Retirados por resultado nulo:** urgencia local en el Tribunal (0a) y alostasis de hambre y sed (3b).
- **Línea general:** 12,8–13,6 % de Crafter Score (antes, 1,45 %). La línea procedimental (19,2 %) queda en la etiqueta `crafter-procedimental-v1`.
- **`evaluar_crafter.py` registra los latidos cortados** y tiene la opción `--verificar-determinismo`.

### Corregido: métricas públicas de Crafter
- **Logros por vida en Crafter: 9,30 ± 1,09, no 10,9.** `README.md`, `README.en.md` y `doc-repositorio/05_METRICAS_E_HITOS.md` publicaban 10,9 logros y 263,8 latidos (medido el 11/11/2026 con `python -m ida --mundo crafter --latidos 600 --semilla S`, S = 1..10). Ese comando no lleva `--tabula-rasa` y el directorio de datos se reutilizó entre semillas, así que cada vida heredaba arquetipo y legado de la anterior: no eran 10 vidas independientes.
- **Nueva cifra:** protocolo aislado de [`docs/BENCHMARK_PERFILES_MUNDOS.md`](docs/BENCHMARK_PERFILES_MUNDOS.md) (12/11/2026, Python 3.15): semillas 1..10, directorio limpio por semilla, 3 generaciones por linaje (30 vidas), 600 latidos máximos, perfil inicial Equilibrado, IC 95 % con t de Student sobre los 10 linajes. En `5c8ae1e` da 9,30 ± 1,09 logros y 233,7 latidos de media. En `25e1303` (mismo árbol que `main` tras el PR #4) da 9,13 ± 1,42; la diferencia pareada, −0,17 ± 1,42, incluye el 0.
- Se retiran los porcentajes de mejora publicados con la cifra antigua (+26,5 % de vida, +19,8 % de logros): la versión base no se ha medido con el protocolo aislado. La tabla del 11/11 se conserva en `05_METRICAS_E_HITOS.md` como registro.
- Límite: el script de la batería no está en el repositorio; la ejecución usa `ida.ejecutor.ejecutar(..., tabula_rasa=True, arquetipo_inicial=...)`.

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
