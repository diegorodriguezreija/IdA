# Reglas para agentes de IA que contribuyan a IdA

Gran parte del código de IdA se escribió con agentes de IA bajo la dirección y la revisión del autor. Estas reglas valen para cualquier agente (y persona) que proponga cambios.

## Diseño de la base

Antes de cualquier cambio, lee:

- [`docs/DISENO_COMPONENTES.md`](docs/DISENO_COMPONENTES.md): la referencia de diseño (decisiones D1 a D17 y cómo se cambian). Manda sobre cualquier otro documento.
- [`doc-repositorio/07_DISENO_VISUAL.md`](doc-repositorio/07_DISENO_VISUAL.md): el latido y los Componentes del núcleo y de cada mundo, en diagramas.
- [`docs/PENDIENTES.md`](docs/PENDIENTES.md): qué queda por hacer y en qué orden (limpieza C, conducta B, validación V y M).

El rediseño anterior ([`docs/historico/REDISENO_BASE.md`](docs/historico/REDISENO_BASE.md), [`docs/historico/PLAN_IMPLEMENTACION.md`](docs/historico/PLAN_IMPLEMENTACION.md), bloques A a F) está terminado y solo sirve de contexto.

## Fase actual: limpieza y cambios de conducta sobre `crafter-general-v5`

La reorganización por Componentes (fase A) está en `main` con la etiqueta `crafter-general-v5`, con la misma conducta y la misma Score que `crafter-general-v4` ([`docs/COMPARACION_MUNDOS.md`](docs/COMPARACION_MUNDOS.md)). Esa es la referencia fija. Lo siguiente es la limpieza sin cambio de conducta (pasos C) y la fase B, en el orden de [`docs/PENDIENTES.md`](docs/PENDIENTES.md).

- **Proceso de cambio de diseño:** la especificación vive en [`docs/DISENO_COMPONENTES.md`](docs/DISENO_COMPONENTES.md) y [`doc-repositorio/componentes.toml`](doc-repositorio/componentes.toml). La pureza y los límites biológicos se vigilan con `tests/test_pureza.py` y `tests/test_criterios.py`. Los cambios de limpieza sin cambio de conducta se aceptan con `.venv\Scripts\python.exe herramientas/equivalencia.py` (`EQUIVALENCIA: OK`); los cambios de conducta, con el criterio de no inferioridad **D17**. La lista viva de tareas pendientes está en [`docs/PENDIENTES.md`](docs/PENDIENTES.md).
- **El mapa de Componentes es la especificación:** [`doc-repositorio/componentes.toml`](doc-repositorio/componentes.toml) dice dónde debe vivir cada Componente (`destino`) y dónde está hoy (`hoy`); `tests/test_mapa_componentes.py` comprueba que el código coincide con `hoy` en cada mundo.
  - Si mueves, añades o quitas un Componente o una estrategia, actualiza `hoy` (y `hoy_en`, `paso`) en el mismo cambio y regenera los documentos 06 (tabla) y 07 (diagramas): `.venv\Scripts\python.exe herramientas/mapa_componentes.py --escribir`. Nunca se editan a mano.
  - **No cambies `destino`, `clase`, `registran` ni `decision`** sin una decisión nueva o modificada en `docs/DISENO_COMPONENTES.md`, aprobada por el autor. Si el código no puede llegar al destino, para y explica por qué.
  - Nunca cambies la especificación para que pase un test.
- **Ramas de trabajo:** cada paso sale de `main` en su propia rama (`limpieza/<paso>` o `conducta/<paso>`). Solo se fusiona en `main` cuando cumple su criterio (equivalencia para la limpieza, D17 para la conducta) y el autor lo autoriza. No hagas push a `main`: sube solo la rama de tu paso.
- **Implementa solo el paso que te encarguen** (C1, B1...). Cada encargo dice qué partes de la base puede tocar; ese es el permiso expreso del no negociable 5.
- **Fase B: cada cambio de conducta, por separado y medido** con el criterio de no inferioridad de D17, fijado antes de medir. Comparación pareada conjunta de las semillas 31 y 32 a 100 000 pasos (`resumen_evaluacion.py --pareada-conjunta`):
  - La diferencia de Score tiene una estimación ≥ −0,3 puntos **y** el límite inferior de su IC 95 % ≥ −1,0 puntos.
  - En mínimo y archivos, `benchmark.py` pareado (N = 10) con `--plazo-logico 40`, frente a `datos/benchmark/v5_*_logico40.json`, sin empeoramiento significativo.
  - Se informa también de cada logro con un cambio significativo, aunque no decida.
  - Si no se cumple: un diagnóstico y una ronda. Si sigue sin cumplirse, el cambio queda tras un parámetro del cuerpo o del `Perfil` con el valor de la fase A, y se documenta como resultado negativo.
- **Comprobar la equivalencia antes de tocar conducta:** en pasos que no cambian conducta, `.venv\Scripts\python.exe herramientas/equivalencia.py` debe terminar en `EQUIVALENCIA: OK`.
- **Componentes de mundo:**
  - se declaran en el registro del mundo (`añade` o `sustituye`), nunca por el nombre de un fichero;
  - pueden emitir y modificar piezas de un tipo de la base si son de ese tipo (propiedad por tipo);
  - solo los Componentes `Accion` proponen acciones.
- **La Observación solo la leen los sensores del Core** y los del mundo en `core/sentir/`. Los datos en bruto no llevan valoración: `nutritivo`, `peligro`, `recurso` y `novedad` los interpreta el organismo. Si un mundo los entrega hechos, lo declara en `Perfil.rasgos_declarados`.
- **Preatención:** solo modifica las piezas de los sensores, no crea piezas, no propone acciones y su coste es lineal en lo percibido.
- **Estrategias:** se activan por piezas de la Onda (nunca por el paso, el reloj ni el estado interno del mundo), pueden omitirse, compiten en el Tribunal y sus umbrales son parámetros o se aprenden. Pueden tener fases con esas condiciones.
- **Las constantes de escala** van en el `Perfil` del mundo o en los parámetros de su cuerpo, no en los Componentes generales.
- **Lo aprendido es de cada mundo:** no pasa de un mundo a otro.
- **Mecanismos de memoria (bloques E y F, `ida/nucleo/memoria/mecanismos.py`):** siguen apagados por defecto; un mundo los activa en su `Perfil` si un benchmark pareado demuestra su valor ([`docs/historico/VEREDICTO_E_F.md`](docs/historico/VEREDICTO_E_F.md)).
- Mientras se mide, en la máquina no corre ningún otro proceso de IdA (ni tests ni pruebas rápidas). Cada medición registra sus latidos cortados.
- Los agentes no instalan paquetes sin permiso del autor.

## No negociables

1. **No debilites los tests.** No quites palabras de `PALABRAS_DE_MUNDO` ni imports de `IMPORTS_PROHIBIDOS` en `tests/test_pureza.py`, no añadas excepciones y no relajes aserciones ni umbrales para que algo pase. Si un test falla, di qué falla y por qué.
2. **No metas conocimiento de un mundo en los paquetes base (`ida/nucleo/`, `ida/core/`, `ida/sistemas/`, `ida/s1/`-`ida/s3/`)**, ni directamente ni con trucos que el test no ve (cadenas construidas en ejecución, imports dinámicos, umbrales afinados para un mundo). Va en `ida/mundos/<mundo>`.
3. **El mundo percibe; IdA piensa.** No mejores un mundo haciendo que su sensor calcule o valore por el individuo (búsquedas, planes, oráculos externos, rasgos valorados). Mejora su percepción en bruto o sus Componentes propios.
4. **Harness engineering: consistencia biológica sin atajos ni trucos rígidos.**
   - Las conductas adaptativas deben apoyarse en principios biológicos plausibles: mapas cognitivos/hipocampales, aliestesia homeostática, asimetrías lucha/huida reguladas por el estado somático y equipamiento, o aprendizaje de contingencias.
   - Prohibido parchear comportamientos mediante autómatas deterministas rígidos, "trampas" de juego, secuencias de acciones cableadas para un fin específico o saltos que ignoren el arbitraje del Tribunal.
   - Cualquier mecanismo orgánico candidato debe evaluarse empíricamente con mediciones repetibles con semilla antes y después. Si demuestra generalidad y rigor entre mundos, puede proponerse para su elevación al Core.
5. **No toques el framework base (`ida/nucleo/`, `ida/core/`, `ida/s1/`-`ida/s3/`) sin permiso expreso del autor.** Si es imprescindible, en un commit propio, explicado, y comprobando que una vida con semilla da lo mismo antes y después cuando el cambio no busca cambiar la conducta. Cuenta como permiso expreso el que concede cada encargo (un paso de [`docs/PENDIENTES.md`](docs/PENDIENTES.md)), y vale solo para ese paso y mientras dure su encargo. Ese permiso no cambia las reglas 1 a 3: la pureza de los paquetes base y sus tests se mantienen.
6. **Verifica antes de afirmar.** Cada afirmación sobre el código cita fichero y línea o la salida de un comando. Lo que no hayas comprobado, márcalo como no verificado.
7. **No inventes cifras, referencias ni mecanismos.** Toda cifra publicada lleva su comando, sus semillas, su número de vidas y su fecha, y se compara con la versión anterior en las mismas semillas. Publica también los resultados negativos.
8. **Un commit por cambio**, con mensaje descriptivo. Nada de `push` sin que el autor lo pida.
9. **Sin lenguaje enfático.** Describe con cifras y límites. **Informes y documentación, en español** (también las respuestas al autor, los mensajes de PR y los resúmenes).
10. **No importes `chess` fuera de `ida/mundos/ajedrez/`** (licencia, ver [`NOTICE`](NOTICE)).
11. **Seguridad:** el mundo de archivos solo puede tocar su bioma; no amplíes esa frontera. El panel y la pila de observabilidad escuchan solo en local.

## Antes de proponer un cambio

```bash
python -m pytest -q
ruff check ida tests
mypy ida
git diff --stat -- ida/nucleo ida/core ida/sistemas ida/s1 ida/s2 ida/s3   # ¿tocaste el framework base? justifícalo
```
