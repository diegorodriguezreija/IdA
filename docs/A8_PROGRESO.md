# A8: Cierre de la fase A (D8, D5, D3, D15, D17)

Rama `reorg/a8-cierre`, desde `origin/reorg/componentes` (`c6051a4`).
Paso A8: cerrar la fase A con tests de los criterios (D8, D5), inventario y paso a Perfil.escala de las constantes de escala,
informe de conocimiento del mundo extendido con `--latidos` y documentación al día. NO cambia la conducta.

## Estado

| Etapa | Qué | Estado | Commit |
|---|---|---|---|
| E1 | Tests de criterios D8 y D5 (`tests/test_criterios.py`) | Hecha | `00f9bd9` |
| E2 | Constantes y `Perfil.escala` | Hecha | Ver git log |
| E3 | Informe de conocimiento con `--latidos` | Pendiente | |
| E4 | Documentación al día y cierre de fase A | Pendiente | |

### Comprobaciones E2 (24/11/2026)

```
ruff check ida tests   All checks passed!
mypy ida               Success: no issues found in 159 source files
pytest -q              938 passed, 1 warning
equivalencia.py:
31: IDÉNTICO
32: IDÉNTICO
31h: IDÉNTICO
31h legado: IDÉNTICO
minimo: OK
archivos: OK
crafter: OK
ajedrez: OK
EQUIVALENCIA: OK
```

## E1 · Tests de criterios (D8, D5)

- `tests/test_criterios.py`: análisis estático (`ast`) sobre:
  - **Estrategias:** todas las clases de las carpetas `reaccionar/estrategias/` de `ida/s1`-`s3` y de `ida/mundos/*`. Ninguna lee `observacion`, el mundo (`mundo`, `.env`, `_world`) ni un reloj del mundo (`.t` de un mundo, `paso` del mundo, `reloj`, `hora`).
  - **Componentes fuera de core/sentir:** ningún Componente fuera de `ida/core/sentir` lee `observacion`, el mundo ni un reloj del mundo.
  - **Preatención (D5):** los Componentes preatentivos (`Saliencia`, `Amenaza`, `ValoracionCrafter`) tienen `preatentivo = True` y residen en módulos de una carpeta `sentir/`.
  - **Sustitución de test_crafter_no_escribe_conducta:** se retiró de `tests/test_defensa.py` y se incorporó a `tests/test_criterios.py`, conservando las aserciones de que el adaptador de Crafter no define clases de estrategia y de que Crafter solo registra `SalirDelRecinto` en S1.
- **Casos xfail:** Ninguno (0 violaciones encontradas).

## E2 · Constantes y Perfil.escala

Clasificación de las constantes de `ida/s1/comun.py`, `ida/s2/`, `ida/s3/` e `ida/sistemas_comun.py`:

| Fichero | Constante | Clase | Motivo |
|---|---|---|---|
| `ida/s1/comun.py` | `SEGURIDAD` | de diseño | nombre del impulso de seguridad en S1 |
| `ida/s1/comun.py` | `COBIJO` | de diseño | nombre de la necesidad de refugio |
| `ida/s1/comun.py` | `TIPO_RECINTO` | de diseño | nombre del tipo de pieza de afordancia |
| `ida/s1/comun.py` | `SATISFACE_MIN` (0,3) | de diseño | umbral de aliestesia para considerar satisfecha una necesidad |
| `ida/s1/comun.py` | `VENTANA_TENDENCIA` (50) | **DUDA** | latidos de media móvil de tendencia. Memoria del propio organismo; se queda como diseño |
| `ida/sistemas_comun.py` | `ALCANCE` (0,9) | de diseño | proximidad mínima [0, 1] en vocabulario común normalizado |
| `ida/sistemas_comun.py` | `MAX_OBJETOS` (7) | de diseño | capacidad del canal atencional (7 ± 2) |
| `ida/sistemas_comun.py` | `PESO_PREDICCION` (0,5) | de diseño | peso del error de predicción en el feedback |
| `ida/sistemas_comun.py` | `Anticipacion.POTENCIA_MINIMA` (0,25) | de diseño | potencia requerida de la Onda para emitir expectativa |
| `ida/sistemas_comun.py` | `Estrategia.VALOR_INICIAL` (0,5) | de diseño | prior inicial del valor de una estrategia |
| `ida/sistemas_comun.py` | `Estrategia.TASA` (0,5) | de diseño | tasa de aprendizaje del valor |
| `ida/sistemas_comun.py` | `Estrategia.EXPLORACION` (0,2) | de diseño | probabilidad de explorar estrategias alternativas |
| `ida/sistemas_comun.py` | `Estrategia.MARGEN_SUSTITUCION` (0,2) | de diseño | margen de ventaja requerido para sustituir estrategia |
| `ida/s2/comun.py` | `EXPLORACION` | de diseño | nombre del impulso exploratorio |
| `ida/s2/comun.py` | `SEGURIDAD` | de diseño | nombre del impulso en S2 |
| `ida/s2/comun.py` | `CANSANCIO` | de diseño | nombre del impulso de descanso |
| `ida/s2/sentir/recuerdo.py` | `Recuerdo.POTENCIA_MINIMA` (0,25) | de diseño | potencia mínima para evocar recuerdos |
| `ida/s2/sentir/recuerdo.py` | `Recuerdo.POTENCIA_REPASO` (0,5) | de diseño | potencia para consolidación y repaso en sueño |
| `ida/s3/comun.py` | `SABER` | de diseño | nombre de la intención deliberada |
| `ida/s3/comun.py` | `INTENSIDAD_INTENCION_DEL_MUNDO` (0,5) | de diseño | intensidad base para intenciones del mundo |
| `ida/s3/comun.py` | `COSTE_RECORDADO` (15,0) | de escala → `Escala.coste_recordado` | pasos estimados para navegar hacia un nodo topológico recordado no visible |
| `ida/s3/comun.py` | `COSTE_POR_PROXIMIDAD` (10,0) | de escala → `Escala.coste_por_proximidad` | factor de escala en pasos para cruzar la distancia visible |
| `ida/s3/comun.py` | `COSTE_SIN_PRODUCTOR` (30,0) | de escala (derivada) → `Escala.coste_sin_productor` | pasos estimados para reponer un recurso sin acción productora conocida (2 × `coste_recordado`) |
| `ida/s3/interpretar/creencia.py` | `PESO_AFECTIVO` (0,1) | de diseño | modulación afectiva en ajuste de creencias |
| `ida/s3/interpretar/creencia.py` | `Creencia.MAX_CREENCIAS` (64) | de diseño | tamaño de búfer del almacén de creencias |
| `ida/s3/interpretar/logica.py` | `Logica.PRIORIDAD` | de diseño | prioridad sintáctica de evaluación lógica |
| `ida/s3/interpretar/requisito.py` | `Requisitos.PASO_CONFIANZA_REQUISITO` (0,1) | de diseño | incremento de confianza por intento |
| `ida/s3/interpretar/requisito.py` | `Requisitos.MAX_INTENTOS` (50) | de diseño | tamaño de búfer de intentos |
| `ida/s3/interpretar/requisito.py` | `Requisitos.FALLOS_BLOQUEO` (3) | de diseño | fallos consecutivos para marcar bloqueo |
| `ida/s3/reaccionar/impulso.py` | `Impulso.FUERZA` (0,2) | de diseño | modulación motivacional deliberativa |
| `ida/s3/reaccionar/estrategias/estudio.py` | `Estudio.COOLDOWN_LECTURA` (15) | de diseño | latidos de enfriamiento entre lecturas |
| `ida/s3/reaccionar/estrategias/estudio.py` | `Estudio.MAX_HIPOTESIS_POR_LECTURA` (2) | de diseño | límite de hipótesis inducidas por turno |
| `ida/s3/reaccionar/estrategias/estudio.py` | `Estudio.L0` (4) | de diseño | coste de lectura inicial |
| `ida/s3/reaccionar/estrategias/estudio.py` | `Estudio.L1` (2) | de diseño | coste de relectura |
| `ida/s3/reaccionar/estrategias/estudio.py` | `Estudio.MAX_LATIDOS_ESPERA_TR` (10) | de diseño | latidos de espera en tiempo real |
| `ida/s3/reaccionar/estrategias/perseguir_metas.py` | `PerseguirMetas.PROFUNDIDAD` (5) | de diseño | profundidad máxima de resolución de metas |
| `ida/s3/reaccionar/estrategias/perseguir_metas.py` | `PerseguirMetas.AROUSAL` (0,5) | de diseño | arousal de propuestas de acción de metas |
| `ida/s3/reaccionar/estrategias/perseguir_metas.py` | `PerseguirMetas.CADA_EXPLORACION` (5) | de diseño | latidos entre replanificaciones |
| `ida/s3/reaccionar/estrategias/perseguir_metas.py` | `PerseguirMetas.VERBOS_PLAN` | de diseño | verbos admisibles en planificación |
| `ida/s3/reaccionar/estrategias/perseguir_metas.py` | `PerseguirMetas.SIN_ACERCARSE` (8) | **DUDA** | latidos sin acercarse antes de replanificar. Paciencia motora del organismo |
| `ida/s3/reaccionar/estrategias/perseguir_metas.py` | `PerseguirMetas.APARCAR` (30) | **DUDA** | latidos que una meta bloqueada permanece aparcada antes de reintentarse |

### Resumen del recuento
- **De escala:** 3 (`coste_recordado`, `coste_por_proximidad`, `coste_sin_productor`).
- **De diseño:** 35.
- **De Crafter:** 0 (las propias de Crafter ya se movieron a `ida/mundos/crafter/` o al cuerpo en A6a/A6b).
- **DUDAS:** 3 (`VENTANA_TENDENCIA`, `SIN_ACERCARSE`, `APARCAR`).
- **Cambios realizados:** Las 3 constantes de escala pasaron a `Escala` (`ida/nucleo/mundo.py`) con sus valores de base como valor por defecto, fijadas explícitamente en `MundoCrafter.perfil.escala`, y leídas desde `ctx.perfil.escala` en `ida/s3/comun.py` y `PerseguirMetas`.
