# Encargo C: Crafter, llegar a la primera noche y salir de ella con vida

> Rama: `feature/crafter-fase-c` (ya contiene `docs/DIAGNOSTICO_CRAFTER_C.md`).
> Referencia: `main` con el tag `crafter-refugio-v1`.
> Lee antes: este documento, `docs/DIAGNOSTICO_CRAFTER_C.md` (completo), las secciones 3 (mecánica) y 7 (lecciones) de `ENCARGO_CRAFTER_NOCHE.md`, `docs/INFORME_B2.md` y `AGENTS.md` («Fase de mejora de los mundos»).

---

## 1. Objetivo

El refugio funciona: quien se sella duerme a salvo y se despierta de forma natural en el 90 % de los sueños. Las muertes ocurren **antes** de entrar y **después** de salir.

| Problema | Vidas afectadas (semillas 11–30) | Dato clave |
|---|---|---|
| No llega a sellarse la primera noche | **10/20** (7 mueren, 3 duermen al raso) | Las 10 se quedan atascadas en `elegir_mina` entre 74 y 186 pasos. Algunas tenían piedra visible a 2–3 casillas (21, 26, 27) y otras no veían ninguna (12, 24). |
| Hambre o sed | **6 muertes**, la misma cifra que los zombis | La comida baja de 5,2 de media al sellar a 0,8 al salir. La semilla 14 muere de sed **dentro**, ya de día. La 18 muere de sed 132 pasos después de salir, en `abastecer`, **con agua a 2 casillas de la mina**. |

Los esqueletos (4 muertes reales, todos en camino natural), el horno, las herramientas de piedra y el huerto **quedan fuera** de este encargo (véase la sección 7).

---

## 2. Mecánica nueva que hay que tener en cuenta

Está verificada en el código de Crafter 1.8.3 y se suma a la sección 3 de `ENCARGO_CRAFTER_NOCHE.md`:

- **Consumo de comida y agua** (`objects.py`, `_update_life_stats`):
  - La comida baja 1 cada 26 pasos despierto o cada 52 dormido.
  - El agua baja 1 cada 21 pasos despierto o cada 42 dormido.
- **Despertar** (`objects.py`, líneas 103–108):
  - El jugador se despierta en cuanto la energía llega a 9.
  - Por eso, dentro del refugio, **pasa la mayor parte de la noche despierto**: sueños de unos 11 pasos y vigilias de unos 30.
  - Entre el sellado (≈ paso 135) y la salida (≈ paso 300) consume **unas 5–6 de comida y 6–7 de agua**.
  - Para salir con margen hay que sellarse con comida ≥ 7 y agua ≥ 8, **o** con agua pegada a la galería (la semilla 30 bebió desde dentro y salió con 9).
- **Luz:** baja de 0,5 en el paso 148.
  - Los sellados que funcionaron se hicieron entre los pasos 123 y 152, y uno en el 181.
  - Con la luz baja, los zombis aparecen en chunks con ≥ 50 de hierba (`env.py`, línea 147).
- **Actualización por distancia:** los objetos solo se actualizan a menos de 18 casillas del jugador (`env.py:88`).
- **Hipótesis descartada:** «minas en chunks con mucha hierba». 6 de las 10 minas que funcionaron estaban en chunks con ≥ 50 de hierba. No hace falta tocar ese criterio.

---

## 3. Pasos

Cada paso lleva:
- **hipótesis**, una sola, y la métrica que la confirma;
- **cambio mínimo** en `ida/mundos/crafter.py` (y tests);
- **medición** con `herramientas/arnes_refugio_crafter.py --real` en las semillas 11–30 (≈ 80 s);
- **commit** y una entrada en `docs/INFORME_C.md`, con la hipótesis, el antes y el después y la decisión tomada.

Si la métrica no confirma la hipótesis, **se revierte el paso**, aunque «no empeore». Como mucho **3 intentos por paso**; si no se confirma, se para y se informa.

### C.0: atribución de causas de muerte (mecánico; puede hacerlo Flash)

**Problema:** `crafter.py` (líneas ~336–341):
- etiqueta como «esqueleto» muertes que en realidad son de hambre o sed;
- etiqueta como «desgaste» muertes por flecha disparada a 5 casillas.

**Cambio:**
1. Si la comida o el agua estaban a 0 en el paso de la muerte, la causa es «hambre» o «sed».
2. El radio de esqueleto pasa a ser ≤ 5 (el alcance de la flecha).
3. Detectar el impacto de una `Arrow` si se puede.

**Comprobación:** en las semillas 11–30, las causas deben coincidir con la reclasificación del diagnóstico (zombi 6, esqueleto 4, sed 3, hambre 3). No cambia el comportamiento.

**Tras C.0:** Flash ejecuta un **benchmark completo de referencia** (4 grupos) sobre este commit y lo guarda en `datos/benchmarks/ref_c0.json`. Es la referencia de este encargo, para que las causas se puedan comparar.

### C.1: elegir mina a tiempo

**Hipótesis:** el atasco en `elegir_mina` se debe a que el criterio de elección no se relaja a medida que se acerca la noche y a que, cuando no hay piedra visible, se busca demasiado tarde.

**Dirección** (la concreción es tuya):
- **La exigencia de la mina baja con la luz.** A primera hora puede ser exigente (agua cerca, sin túnel natural pegado); al caer la tarde, cualquier piedra alcanzable sirve. Debe ser continua, sin interruptores.
- **Si no hay piedra conocida a media tarde, explorar para encontrarla** antes de que oscurezca, en lugar de seguir con otras fases. Esto aprovecha el «vaivén» diurno que ya existe: Diego observó que el individuo deambula de día, y ese tiempo podría dedicarse a localizar la mina.
- **Revisar por qué la fase `madera` dura hasta 116 pasos** en algunas vidas (15, 27, 16, 19), si con 3 maderas basta. Mídelo antes de cambiarlo.

**Métrica de confirmación** (semillas 11–30):
- vidas selladas la primera noche: de 10/20 a **≥ 15/20**;
- muertes antes de dormir: de 7 a **≤ 3**.

### C.2: entrar con reservas y salir a tiempo

**Hipótesis:** las muertes por hambre o sed alrededor del refugio se deben a que el individuo se sella con reservas insuficientes para unos 165 pasos y a que no sale cuando una vital llega al límite.

**Dirección:**
- **Antes de sellarse**, la motivación de abastecerse crece si la comida o el agua no cubren la noche (véase la sección 2). La prioridad la decide el Tribunal, no una secuencia cableada.
- **Preferir minas cuya galería toque agua**, para poder beber desde dentro. Es un criterio de calidad de la mina, compatible con C.1: pesa por la mañana y se relaja por la tarde.
- **Salir del refugio** cuando, con luz suficiente, la comida o el agua llegan a un umbral crítico. No seguir durmiendo con el agua a 0 (semilla 14).

**Métrica de confirmación** (semillas 11–30):
- muertes por hambre o sed: de 6 a **≤ 2**;
- media de comida y agua al salir: **≥ 3**.

### C.3: `abastecer` después de salir

**Hipótesis:** `abastecer` no lleva al individuo a beber o comer aunque tenga los recursos cerca. Seed 18: agua a 2 casillas y muerte de sed 132 pasos después de salir, con `abastecer` ganando 84 de 104 latidos.

**Primero, diagnosticar:** en las semillas 18 y 30, qué objetivo persigue `abastecer` y por qué no lo alcanza (¿orientación?, ¿la memoria de agua apunta a otra parte?, ¿la galería le impide salir?).

**Después**, corregir la causa encontrada.

**Métrica de confirmación:** las semillas 18 y 30 no mueren de hambre ni de sed en los 150 pasos siguientes a la salida, y no aparecen casos nuevos en el resto de semillas.

> Si C.2 ya resuelve 18 y 30, C.3 se documenta como «resuelto por C.2» y no se toca.

---

## 4. Validación y benchmark final

1. **Validación de sobreajuste:** una sola pasada del arnés en las semillas **31–50**. Los porcentajes de sellado y de muertes por hambre o sed no deben quedar más de 10 puntos peor que en las semillas 11–30.
2. **Benchmark completo** (4 grupos, semillas 1–10, 3 generaciones × 600 latidos) frente a `ref_c0.json`. Criterios:
   - latidos con mejora significativa en **≥ 2 grupos**;
   - límite inferior de Δ logros **≥ −1,0** en todos los grupos;
   - **ningún grupo** significativamente peor en latidos o fitness;
   - las muertes por zombi y por hambre o sed bajan en el total.
3. **Nunca ajustar con las semillas 1–10.**

---

## 5. Reglas

- **No tocar `ida/core` ni `ida/sistemas`.** Todo va en `ida/mundos/crafter.py`, los tests y las herramientas.
- **Regla 3:** el sensor no piensa por el individuo. **Regla 4:** nada de secuencias cableadas. Las prioridades son motivaciones continuas que compiten en el Tribunal.
- **Mantener el antivaivén** del encargo anterior. En las vidas fallidas, el Tribunal alternaba `refugio_nocturno` con `huir` y `sobresalto`. Es razonable mientras haya zombis; el objetivo es no estar fuera cuando oscurece, no suprimir la huida.
- **Cuidado con el coste:**
  - el arnés tarda unos 80 s;
  - nada de barridos de parámetros;
  - un benchmark completo solo tras C.0 (lo hace Flash) y al final.
  - Informa al terminar cada paso.
- **Ruff, mypy y tests** en verde en cada commit. **Sin push.**

---

## 6. Entrega

- Commits C.0, C.1, C.2 y C.3 (o sus reversiones documentadas), y `docs/INFORME_C.md` con una tabla antes/después por paso.
- **Respuesta final:**
  - qué hipótesis se confirmaron;
  - el resultado de la validación 31–50;
  - el `comparar` del benchmark frente a `ref_c0.json`.

---

## 7. Fuera de alcance (para una fase posterior)

- **Horno y herramientas de piedra** (`PlanTecnologico`, S3):
  - el horno necesita 4 de piedra; las herramientas, 1 de madera + 1 de piedra con mesa a ≤ 1;
  - ojo: picar más piedra suma camino, y con ≥ 6 de camino en un chunk aparecen esqueletos.
- **Huerto:** plantar a menos de 18 casillas del refugio, porque si no la planta no crece, y protegerla de las vacas. Encaja con el hambre de la mañana: madura en unos 300 pasos.
- **Esqueletos:** evitar minas a distancia 0 de un túnel natural (2 de 4 casos). C.1 puede incluirlo como preferencia matinal, pero no es un objetivo.
- **Fase S2:** valorar los lugares por la experiencia vivida.
