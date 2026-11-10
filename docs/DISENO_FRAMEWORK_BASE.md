# Diseño del framework base de IdA

Este documento describe de qué se compone el framework base de IdA, qué contrato cumple un mundo y cómo se mantienen el latido y la guillotina.

## 1. Principios

1. **El framework base no sabe en qué mundo está.** Ni importaciones, ni palabras, ni significados de un mundo concreto: nada de «archivo», «brote», «tablero» o «zombi» en el Core ni en los sistemas base. `tests/test_pureza.py` lo vigila.
2. **Componentes, Módulos y Sistemas.** Componentes con tres barridos, agrupados en Módulos, que forman Sistemas. El Core tiene sus propios módulos Sentir y Actuar. Todo pasa por la Onda.
3. **El latido manda.** Cada latido tiene su presupuesto de amplitud y de tiempo, y la guillotina se respeta (sección 4).
4. **Alcance acotado.** Quedan fuera, por ahora: teoría de la mente, medidas de integración de la información, autopoiesis, deontología, modelos de lenguaje y memoria colectiva. Se pueden añadir después como módulos opcionales sin tocar el núcleo.
5. **Visible.** Todo lo que el individuo siente, propone, decide y aprende se ve en la consola y en el panel de telemetría.
6. **Repetible.** Toda la aleatoriedad sale de un generador con semilla.
7. **El mundo percibe; IdA piensa.** El sensor de un mundo traduce lo que hay *ahora* a rasgos (lo que se ve, lo que está al alcance, lo que amenaza de inmediato). No calcula por el individuo. Si el sensor calcula mucho, quien juega bien es el mundo, no IdA. Ejemplo: el sensor de ajedrez mira una sola respuesta del rival; hacerle buscar combinaciones más largas subiría los resultados, pero mediría el motor del sensor y no la mente. Lo mismo vale para cualquier oráculo externo (un motor o un modelo de lenguaje) que eligiera la acción. Mejorar un mundo es mejorar su percepción, no sustituir el juicio del individuo.

## 2. De qué se compone el framework base

```
ida/
├── core/                       El organismo, sin mundo
│   ├── vocabulario.py          Verbos, rasgos, relaciones, estados del saber y afectos
│   ├── pieza.py                Pieza (unidad de información) y Episodio
│   ├── arquitectura.py         Componente, Módulo, Sistema y Contexto
│   ├── onda.py                 Onda (ei, ev, acc, ef), presupuesto, guillotina y registro de fases
│   ├── latido.py               Organismo: orden del latido, aprendizaje, sueño, marcapasos
│   ├── soma.py                 Cuerpo: vitalidad, alimentación, energía, descanso, química e indicadores
│   ├── sentidos.py             Sentir del Core (interocepción, propiocepción, escena), Tribunal y actuadores
│   ├── memoria.py              Registros, expectativas, episodios, proposiciones, sueño y olvido
│   ├── persistencia.py         SQLite en modo WAL, escrita al dormir y al morir
│   ├── linaje.py               Arquetipo, mutación y herencia dentro del linaje
│   ├── azar.py                 Generador con semilla y derivación por generación
│   └── mundo.py                Contrato que implementa cada mundo (sección 3)
├── sistemas/                   Componentes base de S1, S2 y S3 (sección 5)
├── telemetria/                 Panel en vivo (SSE, biblioteca estándar) y OpenTelemetry opcional
├── mundos/                     minimo, archivos, snake, crafter, ajedrez/
└── __main__.py                 python -m ida --mundo X [opciones]
```

| Pieza | Responsabilidad |
|---|---|
| **Pieza** | Unidad individual: id, tipo, arousal, confianza, carga, entradas causales, marcas de creación y actualización |
| **Componente** | Produce un tipo de Pieza. Tres barridos (`reactiva`, `activa`, `proactiva`) y una lista de `entradas` que lo activan |
| **Módulo** | Grupo de componentes de una etapa (Sentir, Interpretar, Reaccionar, Actuar). Se ejecuta por barridos: primero todos los reactivos; después, si sobra presupuesto, los activos; después, los proactivos |
| **Sistema** | S1, S2 o S3: una meta (supervivencia, valor, verdad) y sus módulos |
| **Onda** | Paquete de un latido: `ei` (solo lectura) → `ev` → `acc` → `ef`, con su presupuesto de amplitud y de tiempo |
| **Core · Sentir** | Módulo exento de peaje: interocepción (del soma), propiocepción y escena (de la observación del mundo) |
| **Core · Actuar** | Módulo exento de peaje: el Tribunal más un actuador por verbo del mundo |
| **Tribunal** | Arbitra candidatos con `arousal·estrés + confianza·(1 − estrés)`, más el sesgo de la experiencia con un peso pequeño, acecho y desempate |
| **Soma** | Estado vital, metabolismo por latido, química, afecto y los tres indicadores (peligro, tensión, calma) |
| **Memoria** | Activa (recuerdos por verbo y clase), proactiva (expectativas que se validan), episodios, proposiciones, sueño y olvido. Escribe el Core, no los componentes |
| **Linaje** | Arquetipo por individuo, mutación y herencia de lo demostrado como hipótesis |
| **Telemetría** | Servidor HTTP con SSE en un hilo aparte y un panel HTML/JS; OpenTelemetry como extra opcional |

## 3. Contrato entre el framework y un mundo

El mundo traduce su realidad a un vocabulario común con significado, y los componentes base razonan solo con ese vocabulario (`ida/core/mundo.py`).

**Un mundo implementa:**

| Método o atributo | Qué es |
|---|---|
| `perfil` | Las pocas perillas del mundo: tiempo real o por turnos, plazo base del latido, amplitud, memoria, si duerme, si usa hogar, peso de la experiencia y si el mundo marca las constantes del cuerpo |
| `reiniciar(semilla)` | Prepara una vida nueva |
| `observar()` | Devuelve una `Observacion`: ubicación, entidades con rasgos, constantes propias (si las tiene) y si está dormido (si el mundo lo decide) |
| `verbos()` | Los verbos que sabe ejecutar |
| `ejecutar(verbo, objetivo, datos)` | Devuelve un `Efecto`: éxito, cambios en el soma, causa de un daño, lo obtenido y si hubo muerte |
| `terminado()`, `puntuacion()`, `vista()`, `cerrar()` | Fin de la vida, resultado, vista de texto y liberación de recursos |
| `componentes_propios()` | Componentes adicionales para S1, S2 o S3, declarados como propios del mundo. Deberían ser pocos |

**Escena con significado.** Cada entidad tiene un `id` estable entre latidos, una `clase` (etiqueta libre del mundo, como `"zombi"` o `"brote"`, que la memoria usa para generalizar) y `rasgos` en [0, 1]:

| Rasgo | Significado |
|---|---|
| `proximidad` | Lo cerca que está (1 = al alcance) |
| `nutritivo` | Lo que promete para el soma |
| `peligro` | Lo que amenaza al soma |
| `novedad` | Cuánto se desconoce o hace cuánto que no se ve |
| `recurso` | Utilidad instrumental: sirve para algo, aunque no se coma |
| `lugar` | Es un sitio al que se puede ir |
| `agente` | Actúa por sí mismo |

En el mundo de archivos, por ejemplo, el sensor calcula estos rasgos a partir de los bytes (masa, entropía, periodicidad…). La mente no sabe qué es un archivo. Lo mismo para Snake (comida, cuerpo, pared), Crafter (vaca, zombi, árbol) y Ajedrez (jugadas legales).

**Verbos comunes:** `MOVER`, `COMER`, `ATACAR`, `COGER`, `SOLTAR`, `USAR` (fabricar o colocar), `DORMIR`, `ESPERAR`, más `ACECHAR`, interno del Tribunal. Cada mundo declara cuáles admite.

## 4. El latido y la guillotina

**La guillotina es síncrona y cooperativa.** En Python, ni `asyncio` ni los hilos pueden interrumpir un cálculo que no cede el control, y en Windows no hay señales de temporizador. La única interrupción de verdad sería ejecutar la cognición en otro proceso y matarlo, copiando la Onda en cada latido, lo que es caro y complica todo. Por eso cada emisión llama a `onda.control_vital()`, que cobra amplitud y mira el reloj. Si se pasa, salta `LatidoAgotado`, se cortan los componentes restantes y **el Tribunal actúa igualmente con lo que haya en `acc`**. Como el orden es S1 → S2 → S3, S1 casi siempre ha propuesto algo; si nadie propone nada, el Core espera o propone el mal menor.

**Reglas que hacen fiable la guillotina:**

1. **Puntos de control.** Toda emisión pasa por `control_vital()`, y el gestor comprueba el reloj antes de cada componente.
2. **Lo lento, fuera del latido.** Persistir y consolidar se hace al dormir o al morir. Los resultados vuelven por la dimensión proactiva en latidos siguientes.
3. **El tiempo del mundo no cuenta.** El plazo mide desde que empieza Sentir hasta que decide el Tribunal. La jugada del rival o la latencia de una web no se cobran al organismo.
4. **Medir los excesos.** Cada latido registra cuánto tardó cada componente, y la telemetría lo muestra. La Onda apunta además cuándo empieza y acaba cada fase (`Onda.fases`); con `--otel` cada latido se convierte en una traza de OpenTelemetry fuera del plazo, sin que el núcleo llame a nada.
5. **Marcapasos.** En mundos de tiempo real (Snake), el latido dura al menos su periodo; el mundo avanza aunque IdA no haya terminado. En mundos por turnos (archivos, Crafter, ajedrez), el mundo espera a IdA, pero cada latido conserva su presupuesto.
6. **Frecuencia y amplitud variables.** Se calculan en cada latido a partir del soma: la energía escala la amplitud, el sueño la reduce y el agotamiento de la amplitud acelera el latido siguiente. El plazo base es el que declara cada mundo.

**Orden de un latido:**

```
1. Soma: metabolismo. Observación del mundo. Presupuesto del latido (frecuencia, amplitud)
2. Onda nueva: ei ← ef anterior (solo lectura)
3. Core · Sentir      (exento de peaje)  → ev
4. Aprender del efecto de la acción anterior (ei → ef)
5. S1 → S2 → S3       (cada uno, sus módulos por barridos; guillotina cooperativa)
   Dormido: solo sueño y vigilancia de alarmas
6. Core · Actuar      (exento de peaje)  Tribunal → actuador del mundo → ef["Ejecucion"]
7. Indicadores, memoria rápida (las K piezas de mayor arousal) y episodio
```

Si en el paso 5 salta la guillotina, se va directamente al paso 6.

## 5. Componentes base

| Sistema · etapa | Componentes |
|---|---|
| S1 · Sentir | **Imagen** |
| S1 · Interpretar | **Supervivencia** (peligro graduado por distancia y número) |
| S1 · Reaccionar | **Reflejo** (huir o defenderse), **ImpulsoS1** (comer, acercarse a la comida) |
| S2 · Sentir | **Patrón** (la clase del mundo más los rasgos) |
| S2 · Interpretar | **Sujeto**, **Valor** |
| S2 · Reaccionar | **Exteriorización**, **ImpulsoS2**, **Curiosidad**, **Hogar** |
| S3 · Sentir | **Comunicación** (solo si el mundo emite mensajes) |
| S3 · Interpretar | **Agente**, **PredicadoProposicion**, **Sentencia**, **Lógica** |
| S3 · Reaccionar | **Comportamiento** (solo se apoya en proposiciones demostradas), **ImpulsoS3** |
| Core · Actuar | **Tribunal** y un **Actuador** por verbo: cada sistema entrega candidatos; solo el Tribunal ejecuta |

Cada mundo puede añadir componentes propios (por ejemplo, `Prudencia` en el mundo de archivos o `PlanTecnologico` en Crafter), y se declaran como tales.
