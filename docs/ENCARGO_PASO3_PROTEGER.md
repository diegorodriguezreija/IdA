# Encargo del paso 3: proteger X (el refugio general)

Fase de generalización (`docs/FASE_GENERALIZACION_CRAFTER.md`), paso 3. Rama `feature/proteger` desde `feature/cierre-paso0`.

**Modelos:** diseño, este documento; implementación, Opus 5.5; mediciones, Flash.

---

## 1. Por qué y qué se espera

**Datos** (`docs/MEDICION_PASO5_PASO0.md` y `docs/DIAGNOSTICO_G3.md`):
- **Línea general** (sin estrategias de Crafter, G1 y P2):
  - el 76-78 % de los episodios acaban por zombis;
  - los episodios duran unos 244 pasos, así que el individuo muere en su primera noche;
  - `wake_up` está al 5 %.
- **Con estrategias** (G3), `wake_up` llega al 39 %. Su refugio es `RefugioNocturno`: una máquina de estados de Crafter de unas 900 líneas que lo decide casi todo (deuda 1). Además gana en el Tribunal por una confianza inflada (diagnóstico del paso 0).

**Hipótesis:** una capacidad general de la base, «proteger X» con X = uno mismo, que **anticipa** la necesidad de cobijo (alostasis) y **elige y completa** un recinto cerrando accesos o cavando, hace que la línea general sobreviva a la noche. Con eso:
- sube `wake_up`;
- se alargan los episodios, lo que da tiempo a los logros de piedra, carbón y hierro;
- `RefugioNocturno` se puede borrar.

**Expectativa, escrita antes de medir:**
- línea general (G1 con este paso frente a G1 actual): `wake_up` del 5 % a ≥ 25 %, la proporción de muertes por zombi baja de forma clara y la Score sube de forma significativa;
- con las demás estrategias de Crafter y `RefugioNocturno` borrado: no peor que G3 en más de 2 puntos (margen declarado).

## 2. Conceptos generales (sin nombres de Crafter)

| Concepto | Definición | De dónde sale |
|---|---|---|
| **Casilla transitable** | Una casilla con rasgo `lugar` (el adaptador ya la da como `celda_x_y`) | Percepción |
| **Transitable para un peligro** | Clases de casilla sobre las que se ha visto un peligro (hostil) | Experiencia, más el manual («zombies in grasslands») como previo |
| **Accesos de una casilla** | Sus vecinas transitables para algún peligro | Calculado |
| **Recinto** | Un conjunto de 1-3 casillas transitables, conectado, con 0 accesos hacia fuera | Calculado |
| **Cerrar un acceso** | Una acción USAR cuyo efecto aprendido es que la casilla de delante deja de ser transitable (`Requisito.aparece`, del paso 5) | Requisitos |
| **Abrir espacio** | Una acción COGER sobre una casilla no transitable que, por el efecto aprendido, pasa a serlo (cavar) | Requisitos y experiencia |
| **Modelo del cuerpo** | Cómo cambian la posición y la orientación tras un MOVER, según la casilla destino sea transitable o no | Aprendido por propiocepción (sección 3.1) |

## 3. Diseño

### 3.1 Modelo del cuerpo aprendido (memoria, general)

Tras cada MOVER, la memoria registra la terna (destino transitable sí o no, cambió la posición, cambió la orientación). En pocos latidos aprende la regla de Crafter: hacia una casilla libre se avanza y se gira; hacia una bloqueada solo se gira. **No se escribe**: se aprende, y otro mundo podría tener otra regla.

Con ese modelo, un **buscador sobre estados (posición, orientación)** (BFS, máximo 12 pasos) responde a la pregunta «qué secuencia de MOVER me deja en A mirando a C». Es la generalización de `_plan_mirar` de la fase C.

**Comprobar** que la propiocepción da la orientación. `PlanTecnologico` la leía con `_orientacion(ctx)`.

### 3.2 Alostasis: anticipar el cobijo (S1, general)

Hoy la necesidad de cobijo sube cuando ya ha bajado la luz. Lo general es anticipar el déficit:

```
deficit_previsto(n, T) = deficit(n) + tendencia(n) · T     # tendencia: media móvil del cambio por latido
T = coste_estimado_de_protegerse                            # pasos del mejor plan de recinto (3.3)
intensidad_anticipada(n) = max(deficit(n), deficit_previsto(n, T))
```

- Es **alostasis** (regulación por anticipación), aplicada a cualquier necesidad con tendencia.
- **Para el cobijo:** si la luz baja y el recinto está a 20 pasos, la intensidad sube unos 20 pasos antes de que oscurezca.
- **Para el hambre y la sed (3b):** con una noche protegida por delante, el déficit previsto incluye el consumo durante ese periodo. Así se come y se bebe antes de encerrarse, sin ninguna fase de «provisiones».

**Comprobar** cómo se calcula hoy la intensidad de cada impulso (`s1.py`, `Impulso`) y aplicar esto ahí, tras un interruptor `alostasis`. **Invariancia:** las necesidades sin tendencia sostenida, o en mundos sin recintos posibles, no cambian. Se verifica con `invariancia.py`.

### 3.3 Proteger (S1, estrategia general)

Estrategia `Proteger(ConPropuestas)` para el impulso de cobijo, y opcionalmente el de seguridad cuando hay peligro anticipado. Cada latido:

```python
def decidir(self, ctx):
    mapa = mapa_local(ctx)                      # casillas percibidas y recordadas: transitable o no, clase
    if dentro_de_recinto(ctx, mapa):            # 0 accesos abiertos alrededor de la posición propia
        return self._dentro(ctx)                # quedarse; DORMIR si hay cansancio o noche; abrir al bajar el cobijo
    sitio = self._mantener_o_elegir(ctx, mapa)  # histéresis: se cambia solo si el nuevo es mucho más barato
    if sitio is None:
        return None                             # sin plan: que decidan otras estrategias (huir, explorar)
    accion = primera_accion(sitio.plan)         # cavar, ir hasta A mirando a C, cerrar el acceso...
    self.proponer(ctx, accion, arousal=intensidad_anticipada(cobijo), confianza=sitio.confianza,
                  motivo=f"proteger: {sitio.explicacion}")
```

**Elegir sitio.** Para cada casilla candidata `s` del mapa local, al alcance en ≤ 15 pasos:

```
excavar(s)   = nº de casillas no transitables a abrir para tener al menos 2 casillas interiores
               (2 interiores: hacen falta para sellarse desde dentro mirando al acceso; esto sale
                del buscador de 3.1, no se escribe)
cerrar(s)    = nº de accesos que quedarían abiertos
material     = cerrar(s) ≤ unidades disponibles de algo que cierra (aprendido) + lo que dé excavar
coste(s)     = pasos_hasta(s) + excavar(s) · coste_coger + cerrar(s) · coste_colocar + pasos_de_orientación
preferencia  = − coste(s) + bono_si_es_un_recinto_recordado (hogar)
```

- Es **anticipación corta**, no voracidad: el coste incluye la orientación (3.1), así que un recinto que se bloquea a sí mismo cuesta más o resulta imposible.
- Se descartan los sitios con un peligro dentro o junto a ellos (rasgo `peligro`).
- **El hogar** (`memoria.hogar`) pasa a ser el recinto recordado. Volver a él cuesta solo los pasos de llegar y de cerrar, y así surge la fidelidad al refugio sin escribirla.

**Dentro del recinto:**
- **Quedarse:** las demás estrategias no lo sacan mientras la intensidad del cobijo sea alta, porque su propuesta usa esa intensidad como arousal (`quedarse` = NOOP o DORMIR).
- **DORMIR:** si hay cansancio o la necesidad de cobijo es alta. Así llega `wake_up`.
- **Abrir:** cuando la intensidad del cobijo baja (amanece), COGER sobre el cierre, que además recupera el material. Lo aprendido en la fase C (salida al amanecer) aparece aquí como efecto de la necesidad, no como una fase.

### 3.4 Lo que **no** se escribe (pilar 2)

Ninguna secuencia «madera → herramientas → provisiones → mina → cavar → cerrarse». Lo que antes eran fases sale de:
- tener pico: el planificador del paso 5 lo resuelve si cavar lo requiere (requisito aprendido o del manual);
- la madera o la piedra para cerrar: el planificador, porque el material de cierre es un requisito de USAR;
- las provisiones: la alostasis de hambre y sed (3.2);
- cavar o cerrar: el coste del sitio (3.3).

## 4. Regla de traslado

- `RefugioNocturno` se borra en este paso, con su apaño de motivación (0,92 y 0,98), su mapa propio y sus constantes (`LUZ_PLENO_DIA`, `MEMORIA_VACA`…). La memoria del mapa pasa al mapa local de la base (3.3), que es el «mapa cognitivo compartido» de la deuda 1, en su versión mínima.
- **Durante la implementación**, las dos versiones pueden convivir tras el interruptor `proteger` para medirlas una contra otra. El paso **no se cierra** hasta borrar `RefugioNocturno`.
- `DefensaArmada` y `CerrarDistancia` siguen (paso 6).

## 5. Subpasos y medición

| Subpaso | Qué | Interruptor |
|---|---|---|
| 3a | Modelo del cuerpo (3.1) y Proteger (3.3), con la alostasis solo para el cobijo | `proteger` |
| 3b | Alostasis también para hambre y sed (provisiones) | `alostasis` |
| 3c | Borrar `RefugioNocturno` y su código; quitar los interruptores | — |

**Mediciones (Flash).** Protocolo abreviado: 100 000 pasos, semilla 31, vista 9×7, Equilibrado, sin herencia y manual estricto:
- **L1 (línea general):** `--sin-estrategias-propias`, con 3a y con 3a+3b, frente a G1 con los arreglos del paso 0;
- **L2 (con las demás estrategias):** con 3a+3b y `RefugioNocturno` apagado, frente a G3 con los arreglos;
- además: `wake_up`, causas de muerte, pasos por episodio y la fracción de noches que acaban dentro de un recinto (el diagnóstico de `docs/DIAGNOSTICO_G3.md` sirve).

## 6. Criterios de aceptación

1. **L1:** la Score sube de forma significativa frente a G1 con los arreglos, y `wake_up` ≥ 25 %.
2. **L2:** no peor que G3 con los arreglos en más de 2 puntos.
3. **Pilar 1:** `RefugioNocturno` borrado. Ni `ida/core` ni `ida/sistemas` tienen nombres de Crafter.
4. **Otros mundos:** `invariancia.py` OK en mínimo, archivos y ajedrez. Si 3.2 cambia algo en mínimo o archivos, benchmark completo de esos mundos, no peor.
5. Tests con un mundo de juguete en cuadrícula:
   - el modelo del cuerpo se aprende;
   - el buscador encuentra cómo quedar mirando a una casilla libre;
   - Proteger elige el sitio más barato y lo completa;
   - la alostasis adelanta la intensidad.

## 7. Riesgos

- **Coste de cálculo:** evaluar sitios cada latido puede ser caro. Se recalcula solo cuando cambia el mapa local o cada N latidos, con histéresis.
- **Quedarse dentro con hambre o sed:** la alostasis (3b) y la intensidad de cada necesidad deben poder sacarlo. Hay que vigilar las muertes por hambre y sed (en G3 ya son el 33 %).
- **Que las propuestas pierdan en el Tribunal:** con la confianza en su sitio, debería ganar por la intensidad anticipada como arousal cuando el estrés es alto. Si no gana, se diagnostica antes de tocar constantes.

## Resultado

Mediciones oficiales en [`docs/MEDICION_PASO3.md`](MEDICION_PASO3.md) (rama `feature/proteger`, código `c0fd4e3`; 100 000 pasos, vista oficial, sin herencia, manual estricto; datos en `datos/evaluacion/`).

### 3b (alostasis de las demás necesidades): retirada

| Condición | Score (%) | IC 95 % | `wake_up` (%) | Muertes por hambre | Muertes por sed |
|---|---|---|---|---|---|
| L1a: 3a, semilla 31 | 11,95 | [11,01, 12,76] | 18,49 | 31 (8,1 %) | 39 (10,2 %) |
| L1b: 3a + 3b, semilla 31 | 11,70 | [10,86, 12,41] | 18,75 | 31 (8,1 %) | 38 (9,9 %) |

L1b frente a L1a: −0,25 puntos, con los intervalos solapados. Las muertes por hambre y sed no bajan, que era lo que 3b buscaba (riesgo 2 de la sección 7). Sin efecto medido, se retira: el código (rama `mecanismos.alostasis` de `alostasis` en `ida/sistemas/s1.py`), el interruptor y su test. La alostasis del cobijo (3a) se queda.

### 3c: `RefugioNocturno` borrado, `proteger` siempre activo

Se borran `RefugioNocturno` y lo que solo usaba él (detalle en [`docs/INVENTARIO_CONOCIMIENTO_CRAFTER.md`](INVENTARIO_CONOCIMIENTO_CRAFTER.md), sección 7), y se quita el interruptor `proteger`.

La invariancia sigue OK en mínimo, archivos y ajedrez, porque esos mundos no dan casillas ni la necesidad `cobijo`. En Crafter, la conducta cambia desde el primer latido.

**Pérdida aceptada en la línea con estrategias (L2, semilla 31):**

| Métrica | C2 (con `RefugioNocturno`) | L2 (con `Proteger`) |
|---|---|---|
| Score (%) | 15,29 [14,00, 16,30] | 13,12 [11,96, 14,12] |
| `make_wood_pickaxe` (%) | 91,89 | 60,98 |
| `make_wood_sword` (%) | 84,80 | 37,67 |
| `defeat_zombie` (%) | 69,93 | 49,86 |
| `wake_up` (%) | 37,16 | 22,49 |
| Muertes por zombi | 164 (55,4 %) | 242 (65,6 %) |
| Pasos por episodio | 337,8 | 271,0 |

L2 queda 2,17 puntos por debajo de C2, en el límite del criterio 2 de la sección 6 («no peor en más de 2 puntos»).

**Causa:** `RefugioNocturno` hacía también lo que no es protegerse. En su fase «herramientas» fabricaba el pico y la espada de madera con urgencias fijas de 0,92 a 0,98. Con la espada, `DefensaArmada` lucha en vez de huir. Sin él, la cadena de herramientas depende solo de `PerseguirMetas`: el pico cae del 92 % al 61 % y la espada del 85 % al 38 %, en las mismas cifras que en la línea sin estrategias propias (C1: 62 % y 40 %). Con menos espadas hay menos zombis abatidos y más muertes por zombi.

Se acepta porque aquella conducta era conocimiento de Crafter cableado en el mundo. El diagnóstico de la cadena de herramientas está en [`docs/DIAGNOSTICO_PASO3.md`](DIAGNOSTICO_PASO3.md).
