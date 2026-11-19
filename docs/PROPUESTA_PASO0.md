# Propuesta de diseño del paso 0: la intensidad del impulso llega al Tribunal

Fase de generalización (`docs/FASE_GENERALIZACION_CRAFTER.md`, «Paso 0»). Fecha: 19/11/2026. Base: `feature/planificador` (5738e45). **Propuesta: no hay nada implementado.**

Las cifras de este documento salen de diagnósticos de una vida por condición. Sirven para orientar el diseño, no son mediciones. Scripts (fuera del repositorio): `diag_intensidad.py` y `diag_tribunal.py` en el scratchpad de la sesión. Si se aprueba la propuesta, se pueden pasar a `herramientas/`.

---

## a) Cómo decide hoy el Tribunal

### Fórmula

Para cada candidato `c` de Acción (`ida/core/sentidos.py`, `Tribunal.reactiva`):

```
modulación_c = A_imp − I_imp                                   # sentidos.py:112
arousal_c'   = acotar(arousal_c + modulación_c, 0, 1)          # sentidos.py:113
base_c       = arousal_c' · estrés + confianza_c · (1 − estrés) # sentidos.py:114
plus_c       = 0,1 · (1 − agotamiento) · (1 − progreso)          # sentidos.py:118 (solo la estrategia en curso)
total_c      = base_c + peso_exp · (activa + proactiva) + plus_c # sentidos.py:119-120
```

- `A_imp` es el arousal de la pieza del impulso (o intención) de origen e `I_imp` su intensidad.
- Gana el mayor `total`. Si los dos primeros quedan a ≤ 0,02, decide el azar.
- Con confianza < 0,35 y sin urgencia, el candidato acecha antes de ejecutarse.

El estrés es global, del cuerpo (`ida/core/soma.py:97-98`):

```
urgencia = max(peligro, hambre() si alimentación ≤ HAMBRE_CRITICA (15) si no 0)
estrés   = 0,7 · estrés + 0,3 · urgencia
```

### Dónde se pierde la intensidad

1. **Impulso (S1).** `ida/sistemas/s1.py:434-437` crea una pieza por necesidad, con `intensidad = déficit` y `arousal = intensidad`. Hasta aquí la intensidad existe.
2. **Estrategia.** `ida/sistemas/comun.py` (`Estrategia.reactiva`) usa la intensidad para elegir, mantener y cerrar estrategias, pero no para puntuar sus propuestas.
3. **Cada estrategia pone su propio arousal y su propia confianza.** Son constantes de su autor, a veces con algo de estado:
   - `Huir`: 0,75 + 0,25 · peligro (`s1.py:178`);
   - `Alimentarse`: 0,35 + 0,6 · apetito (`s1.py:371`). El apetito usa `soma.hambre()`, que sale de la alimentación global (en Crafter, `min(comida, bebida)`), no de la necesidad concreta;
   - `Refugiarse`: 0,4 + 0,5 · cansancio (`s2.py:301`);
   - `PerseguirMetas`: 0,5 fijo;
   - `RefugioNocturno`: entre 0,72 y 0,98 (`crafter.py`, `_motivacion`).
4. **Tribunal.**
   - La modulación resta la intensidad (`A_imp − I_imp`): solo pasa lo que S2 o S3 subieron o bajaron el impulso, no la intensidad misma.
   - El arousal pesa en proporción al estrés. Con poco estrés, el Tribunal decide por confianza, que es una constante de cada estrategia.
5. **El estrés solo mira el peligro y el hambre crítica.** La sed, el cansancio o el cobijo apurados no suben el estrés. En Crafter, la sed solo cuenta a través de `min(comida, bebida)`.

### Datos: gana un impulso menos apurado

**Inversión:** en un latido con más de un candidato, un candidato pierde aunque su impulso de origen tiene intensidad ≥ 0,5 y al menos 0,2 más que la del impulso del ganador.

| Mundo y condición | Latidos | Latidos con competencia | Inversiones | % | Estrés medio | Pares más frecuentes (ganador → apurado que pierde) |
|---|---|---|---|---|---|---|
| Crafter, suelo (semilla 31) | 275 | 111 | 6 | 5,4 % | 0,382 | hambre → seguridad (4) |
| Crafter, con estrategias (semilla 31) | 395 | 323 | 80 | 24,8 % | 0,600 | cobijo → progresar (57), cobijo → seguridad (19) |
| mínimo (semilla 1) | 400 | 142 | 9 | 6,3 % | 0,416 | hambre → cansancio (4), seguridad → cansancio (2) |
| archivos (semilla 1) | 400 | 116 | 1 | 0,9 % | 0,320 | cansancio → hambre (1) |
| ajedrez (semilla 1) | 65 | 9 | 0 | 0 % | 0,482 | — |

Lectura:
- **«progresar» no es una necesidad.** Es una intención con intensidad fija 0,5. Sin ella, las inversiones de Crafter con estrategias son 23 (7,1 %): 19 de cobijo contra seguridad, 3 del Core contra seguridad y 1 de seguridad contra cobijo.
- **Las 57 restantes son `RefugioNocturno` ganando con cobijo a 0,03-0,2.** Ocurren desde el latido 1, con estrés de 0,001 a 0,035, en la fase de «ir a por madera». Decide su confianza inflada (0,86 + 0,12 · empuje), no una necesidad. Es la deuda 2 de `DEUDA_TECNICA_CRAFTER.md`.
- **Desde el lado de `PerseguirMetas`** (diagnóstico del paso 5, mismas vidas):
  - con estrategias gana el 9,1 % de sus propuestas. Pierde el 76 % de las veces contra el refugio (total medio 0,865 frente a 0,549) y en el 57 % de los latidos ni siquiera entra entre los 8 mejores;
  - en el suelo gana el 53 %.
- **Ejemplo de aliestesia en la base** (Crafter, suelo, latidos 188-190): el impulso que propone «comer agua» es **hambre**, con intensidad 0,65. Hambre y sed comparten estrategia (`Alimentarse`, rasgo `nutritivo`). Lo que decide que el agua apetezca es el `_deseo` del adaptador.

## b) Aliestesia en la base

**Hoy:**
- Crafter ya declara hambre (`comida`) y sed (`agua`) como dos necesidades (`crafter.py`, `Perfil.necesidades`), pero las dos tienen el rasgo `nutritivo`.
- Las sirve la misma estrategia (`Alimentarse`), que elige el objeto por `nutritivo − peligro`.
- El `nutritivo` de cada objeto lo calcula el adaptador según lo que falta (`_deseo`): el mundo piensa por el individuo.

**Propuesta, en tres piezas generales:**

1. **Qué satisface cada necesidad** (memoria): `Memoria.satisface[(clase, necesidad)]`, una estimación en [0, 1] con su fuente.
   - **Del manual:** una proposición NUTRITIVO puede llevar `necesidad`. Por ejemplo: `{"sujeto": "agua", "relacion": "NUTRITIVO", "necesidad": "sed", "cita": "restored by drinking from a lake"}`. Entra como autoridad (`c_aut`), como en el paso 2.
   - **De la experiencia:** tras COMER sobre una clase, se mira qué constante vital subió, comparando la interocepción de antes y de después, igual que el inventario en `aprender_requisito`. La constante identifica la necesidad, porque cada `Necesidad` declara sus constantes. Es aprendizaje de contingencias.
2. **Apetencia** (S1): un componente nuevo de Interpretar calcula, para cada objeto a la vista, `deseo(o) = Σ_n intensidad(n) · satisface(clase(o), n)`. Es la aliestesia de Cabanac: el valor hedónico depende del estado interno. Produce su propio tipo de pieza, y el rasgo `nutritivo` del mundo deja de modularse.
3. **Alimentarse por necesidad**:
   - la estrategia sirve al impulso cuya necesidad satisface el objeto mejor valorado por `deseo`;
   - su arousal sale de la intensidad del impulso de origen, no de `soma.hambre()`;
   - `apetito` deja de usar la alimentación global.

**En el adaptador:** `_deseo` desaparece. El `nutritivo` del mundo pasa a ser un rasgo perceptivo constante, 0,6 si el manual declara la clase NUTRITIVO. La planta, solo madura: su textura se ve.

**Sin nombres de Crafter en el núcleo:** la base solo conoce «clase», «necesidad» y «constante».

**Compatibilidad:**
- en mínimo y archivos hay una sola necesidad con rasgo `nutritivo` (hambre). Mientras no haya manual ni experiencia, `satisface(clase, hambre)` vale lo mismo que el rasgo `nutritivo`, y el deseo coincide con el de hoy;
- la regla de reparación de `_deseo` (×1,3 con salud < 7) no pasa a la base. Si hace falta, debe salir de la necesidad de salud (paso 0b o posterior).

## c) Alternativas

### A. Intensidad como estrés local del candidato (recomendada)

Cada candidato usa como estrés el mayor entre el global y la urgencia de su propio impulso:

```
u(I)   = max(0, (I − U) / (1 − U))          # U = 0,5: por debajo del umbral, nada cambia
e_c    = max(estrés, u(I_origen_c))
base_c = arousal_c' · e_c + confianza_c · (1 − e_c)
```

- **A favor:**
  - un solo cambio, en `Tribunal.reactiva`;
  - mientras ningún impulso pase de U, la puntuación es idéntica a la de hoy (invariancia por construcción en calma);
  - es monótono: a más apuro, más pesa la urgencia de esa propuesta;
  - las intenciones (intensidad fija 0,5) quedan por debajo de U y no cambian.
- **En contra:**
  - el arousal sigue siendo una constante de cada estrategia: dos estrategias del mismo impulso apurado siguen compitiendo por sus constantes;
  - no arregla `RefugioNocturno` en calma (confianza inflada, cobijo bajo): eso es del paso 3;
  - U es un umbral nuevo y hay que justificarlo. Propuesta: 0,5, el mismo que ya usa la base para «apurado» en este diagnóstico, y medir 0,4 y 0,6.

### B. El arousal de la propuesta es la intensidad del impulso de origen

`Accion` (`comun.py`) fija `arousal_c = I_origen · a_c`, donde `a_c` es la urgencia relativa que declara la estrategia (en [0, 1]).

- **A favor:**
  - es la separación conceptual limpia: el impulso dice cuánto importa; la estrategia, qué hacer y con qué confianza;
  - quita constantes de todas las estrategias.
- **En contra:**
  - cambia la conducta en todos los mundos siempre que haya estrés, y el estrés medio medido va de 0,32 a 0,60: no hay invariancia en ningún sitio;
  - hay que recalibrar todas las estrategias (S1, S2, S3 y las del mundo);
  - es mucho más difícil atribuir cualquier mejora o pérdida.

### Recomendación

**A, en dos subpasos medidos por separado:**
- **0a:** el término de urgencia local en el Tribunal;
- **0b:** la aliestesia (la b anterior), con `_deseo` borrado.

B puede venir más tarde, si A deja demostrado que el arbitraje por intensidad funciona.

## d) Qué cambia en cada mundo

| Mundo | Necesidades | Qué cambia con 0a | Qué cambia con 0b | Invariancia |
|---|---|---|---|---|
| mínimo | las de la base: hambre (rasgo `nutritivo`), cansancio y salud | Solo en los latidos con alguna necesidad ≥ U. Hubo 9 inversiones en 400 latidos (hambre → cansancio, seguridad → cansancio), así que algo cambiará | Nada: una sola necesidad nutritiva; `satisface` = `nutritivo` | **No exacta.** Benchmark completo, no peor |
| archivos | las de la base | Casi nada: 1 inversión en 400 latidos | Nada, por la misma razón | No exacta (esperable casi igual). Benchmark completo, no peor |
| ajedrez | las de la base, sobre las constantes que marca el mundo (`vitales_propios`) | Se espera nada: 0 inversiones en 65 latidos. **No verificado** que ninguna necesidad pase de U en las 3 semillas de `invariancia.py` | Nada | **Exigida** (`invariancia.py`) |
| Crafter | hambre, sed, cansancio, salud y cobijo; intención «progresar» | Las propuestas de una necesidad apurada pesan por urgencia; sed y cansancio apurados por fin compiten | Hambre y sed eligen su objeto; `_deseo` desaparece | No: cambia por diseño. Medición abreviada |

## e) Riesgos y criterios de aceptación (propuestos antes de medir)

**Riesgos:**
- **Vaivén entre dos necesidades apuradas parecidas.** Lo amortiguan el plus de continuidad y la histéresis de `Estrategia`. Se mide con las sustituciones por vida.
- **Seguridad aún más dominante.** El peligro ya entra en el estrés, y A lo refuerza en sus propias propuestas. Se vigilan las muertes por hambre y sed en vidas con peligro frecuente.
- **En Crafter el estrés ya es alto** (0,38-0,60 de media), así que A puede cambiar menos de lo esperado. Si el efecto es nulo, la causa está en las constantes de las estrategias, no en el Tribunal.
- **0b puede empeorar Crafter si la experiencia no separa bien hambre y sed** (comer y beber a la vez, o cambios simultáneos de constantes). Se mitiga con la `necesidad` declarada en el manual.

**Criterios (a fijar antes de medir):**
1. **ajedrez:** `invariancia.py` OK.
2. **mínimo y archivos:**
   - benchmark completo (4 grupos, N = 10, pareado por semilla, IC 95 %) sin diferencia significativa en contra en latidos y fitness, ni en muertes por hambre en archivos;
   - coste por latido como mucho un 10 % mayor.
3. **Crafter** (protocolo abreviado: 100 000 pasos, semilla 31, vista 9×7, Equilibrado, sin herencia):
   - Score no peor de forma significativa que la referencia del paso 5 (G1 y G3 de 5.4), en suelo y con estrategias;
   - inversiones de necesidades (sin contar intenciones) reducidas al menos a la mitad, con el diagnóstico de este documento sobre las semillas de validación 31-35;
   - con 0b: al menos el 80 % de los COMER sobre agua ocurren con la sed más apurada que el hambre, y las muertes por sed más hambre no aumentan de forma significativa.
4. **Un apaño de urgencia del mundo se borra sin pérdida significativa:** la urgencia por salud de C.0c, o los valores fijos 0,98 y 0,92 de `RefugioNocturno._motivacion` para sed crítica y salud.

## f) Dormir de día

**Qué hacía `PlanTecnologico`:** dormía con energía ≤ 4/9 (≤ 44 %), de día (luz ≥ 0,5) y sin hostiles a la vista.

**Qué hace hoy la base:**
- la necesidad de cansancio en Crafter tiene `confort` 60, así que déficit = (60 − energía %) / 60;
- `Refugiarse` descansa con cansancio ≥ 0,6 (`s2.py`, `_descansar`): energía ≤ 24 %, unos 2/9;
- el Core fuerza el sueño con energía ≤ 5 % (`latido.py:156-157`).

**Con 0a y U = 0,5:** el cansancio empieza a pesar con energía ≤ 30 % (unos 2,7/9). Sigue siendo bastante más tarde que 4/9.

**Conclusión:** la intensidad cubre «dormir cuando se está cansado», pero no la anticipación de dormir de día *porque* luego viene la noche y ahora es seguro. Eso es circadiano y de protección: no es una urgencia, es prevenir una.

**Recomendación:**
- no meter una regla en el paso 0;
- medir `wake_up` y las muertes nocturnas con 0a. Referencia: `wake_up` está en 6,73 % en el suelo y 51,44 % en `main` sin herencia (`docs/MEDICION_OFICIAL.md:108`);
- incluir en el paso 3 («proteger X», con X = uno mismo) una pauta general: descansar cuando es seguro si se anticipa la oscuridad, según la tendencia de la luz percibida;
- el umbral 0,6 de `_descansar` es candidato a desaparecer en 0b o en el paso 3, cuando la competencia por intensidad haga su papel.
