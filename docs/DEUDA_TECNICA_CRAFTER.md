# Deuda técnica de Crafter

Registro de compromisos de diseño, limitaciones heurísticas y puntos pendientes acumulados en la adaptación de Crafter (`ida/mundos/crafter.py`), identificados durante las fases de diagnóstico y los encargos C.0 a C.4.

---

## 1. Vaivén episódico en campo abierto (arbitraje S1 vs S2)
- **Fichero / Contexto:** [`ida/mundos/crafter.py`](file:///f:/code/IdA/ida/mundos/crafter.py), [`ida/sistemas/s1.py`](file:///f:/code/IdA/ida/sistemas/s1.py), [`docs/INFORME_C.md:345`](file:///f:/code/IdA/docs/INFORME_C.md#L345).
- **Descripción:** En campo abierto, 12 de las 20 vidas del arnés (semillas 11–30) presentan episodios de vaivén (> 20 latidos consecutivos alternando entre 2 casillas transitables).
- **Causa:** Conflicto de arbitraje en el Tribunal entre reflejos defensivos de Sistema 1 (`huir`, `sobresalto`) y metas utilitarias de Sistema 2 (`alimentarse`, `refugio_nocturno`). Al huir de un hostil, el individuo da un paso atrás; al salir del radio de amenaza inmediata, la meta de hambre o aprovisionamiento recupera el control y ordena avanzar de nuevo hacia el recurso, cayendo en oscilaciones hasta el agotamiento de vitales o la intercepción por monstruos.
- **Pendiente:** Mecanismo de inercia o histéresis espacial en la retirada y resolución de colisiones en campo abierto sin atajos cableados.

---

## 2. Detección y alcance de recursos inalcanzables tras paredes macizas
- **Fichero / Contexto:** [`ida/mundos/crafter.py:1120-1170`](file:///f:/code/IdA/ida/mundos/crafter.py#L1120-L1170) (`_paso_hacia`, `self.inalcanzables`).
- **Descripción:** La búsqueda heurística de aproximación hacia recursos detectados (agua, hierba, plantas) evalúa la distancia Manhattan hacia la casilla objetivo. Cuando el recurso está separado por una pared continua de roca maciza (como en la semilla 18 en `e3 = (43, 25)` con agua en `(45, 25)`), retroceder para rodear aumenta la distancia Manhattan, por lo que el algoritmo se bloquea o cae en bucles locales.
- **Mitigación actual:** En C.0c-2 se introdujo un enfriamiento de 50 latidos para destinos inalcanzables en el refugio.
- **Pendiente:** Navegación topológica mediante el hipocampo del Core (`ctx.memoria.ruta`) para cualquier recurso fuera de línea visual directa, evitando la aproximación por Manhattan pura en entornos rocosos.

---

## 3. Firmeza del reposo nocturno frente a reflejos externos
- **Fichero / Contexto:** [`ida/mundos/crafter.py:1435-1445`](file:///f:/code/IdA/ida/mundos/crafter.py#L1435-L1445) (`RefugioNocturno.paso`, fase `dormir`).
- **Descripción:** Cuando el individuo duerme dentro de un recinto sellado con piedra, los zombis o esqueletos que deambulan por el exterior a distancia $\le 3$ generan percepciones sensoriales de peligro que activan `S1:sobresalto`. Si `ESPERAR` en la fase `dormir` no retiene la máxima prioridad (`arousal = 1,0`, `confianza = 1,0`), los sobresaltos de S1 despiertan o agitan al individuo, impidiendo la recuperación somática completa de energía y consumiendo vitales inútilmente toda la noche (semilla 11 en C.0c-1).
- **Mitigación actual:** C.0c-fix fijó `ESPERAR` en 1,0/1,0 durante `dormir`.
- **Pendiente:** Atenuación somática y sensorial del arousal durante el sueño biológico profundo en el Core/Soma, de forma que un individuo seguro en cobijo no reaccione a estímulos tenues al otro lado de barreras infranqueables.

---

## 4. Rigidez geométrica en la evaluación de recintos y madrigueras
- **Fichero / Contexto:** [`ida/mundos/crafter.py:1010-1080`](file:///f:/code/IdA/ida/mundos/crafter.py#L1010-L1080) (`_evaluar_recinto`, `_buscar_mejor_mina`).
- **Descripción:** El diseño inicial exigía galerías rectas de 3 casillas con laterales herméticos, descartando entre el 95 % y el 99 % de los afloramientos de piedra en el paso 0 (semillas 21, 26 y 27). Aunque C.1 flexibilizó el recinto a 2 casillas (`e0`, `e1`) y añadió la fase `tapar`, la búsqueda sigue basada en plantillas direccionales discretas (4 orientaciones cardinales) que no reconocen cavidades naturales en L o nichos irregulares cerrables con un solo bloque.
- **Pendiente:** Detección topológica de componentes conexos y cuellos de botella en el mapa local mediante análisis de grafos, en lugar de plantillas rígidas de coordenadas relativas.

---

## 5. Abastecimiento forzado previo al sellado y riesgo al anochecer
- **Fichero / Contexto:** [`ida/mundos/crafter.py:1360-1410`](file:///f:/code/IdA/ida/mundos/crafter.py#L1360-L1410) (`RefugioNocturno._abastecer`, fase `provisiones`).
- **Descripción:** El intento en C.2 de forzar la acumulación de reservas de comida ($\ge 6$) antes de permitir el sellado provocó retrasos letales: individuos con mina localizada retrasaron la entrada para cazar vacas lejanas, siendo sorprendidos por la noche al aire libre sin margen de luz (semilla 20, muerte en L168 en C.2 frente a supervivencia hasta el final en C.1).
- **Mitigación actual:** C.2 fue revertida, manteniendo el sellado prioritario en cuanto el margen de luz lo exige.
- **Pendiente:** Regulación homeostática continua de la ingesta durante todo el día para llegar al atardecer naturalmente saciado, sin forzar fases exclusivas de aprovisionamiento de última hora.

---

## 6. Dispersión fuera del área de campeo y forrajeo diurno
- **Fichero / Contexto:** [`ida/mundos/crafter.py:1260-1320`](file:///f:/code/IdA/ida/mundos/crafter.py#L1260-L1320) (`_explorar_con_rumbo`, radio $\le 17$).
- **Descripción:** Cuando el individuo sale del refugio al amanecer, la tendencia a explorar rumbos abiertos lo aleja progresivamente del refugio inicial. Al superar la distancia de 17 casillas, las plantas sembradas o las fuentes seguras de agua quedan fuera del radio de simulación/atención y se pierde la inversión de hábitat.
- **Mitigación actual:** C.3 acotó la exploración a un radio de Manhattan $\le 17$ respecto al recinto recordado y C.3d introdujo forrajeo oportunista de vacas en el camino diurno.
- **Pendiente:** Concepto de área de campeo (*home range*) integrado en el hipocampo del Core, con gradientes de familiaridad y fidelidad al sitio de anidación.

---

## 7. Acoplamiento sensorial y accesos directos al entorno (`env._world`)
- **Fichero / Contexto:** [`ida/mundos/crafter.py`](file:///f:/code/IdA/ida/mundos/crafter.py) (`_transitable`, `_cobijo`, `observar`, `vista`, `PlanTecnologico`).
- **Descripción:** En diversos puntos auxiliares de Crafter aún subsisten consultas directas a arrays internos del simulador o comprobaciones que trascienden la percepción visual estricta del individuo (deuda técnica arrastrada desde la Fase 5, registrada en commit `5eebee8`).
- **Pendiente:** Encapsulación estricta en el sensor del mundo, garantizando que el individuo solo razone a partir de piezas depositadas en la Onda (`Exterocepcion`, `Propiocepcion`, `Soma`) conforme a la Regla 3 de `AGENTS.md`.

---

## 8. Rediseño del huerto
- **Fichero / Contexto:** [`ida/mundos/crafter.py`](file:///f:/code/IdA/ida/mundos/crafter.py) (antigua rama `huerto` en `RefugioNocturno`), [`docs/MEDICION_WIP_C4.md`](file:///f:/code/IdA/docs/MEDICION_WIP_C4.md), [`docs/INFORME_C.md`](file:///f:/code/IdA/docs/INFORME_C.md) (apartado 8).
- **Lecciones aprendidas de C.4:**
  1. Plantar el día 1 compite frontalmente con el sellado nocturno por escasez de tiempo y recursos (redujo el sellado de 32 a 25/29 vidas).
  2. Abrir una pared exterior para cosechar expone el cultivo: si un hostil aparece durante la recolección, el Sistema 1 aborta el recierre para huir y la celda queda permanentemente transitable como `path`, permitiendo que monstruos posteriores destruyan la plantación (como en la semilla 11 en L821).
  3. Acoplar la lógica de cultivo dentro de la máquina de estados de `RefugioNocturno` sobrecarga el componente y deteriora la conducta global incluso en las vidas donde no se llega a plantar.
- **Líneas del rediseño:**
  - **Nichos orientados al interior:** El hueco del cultivo debe abrirse hacia el interior del refugio o la madriguera, protegido por la envoltura exterior de roca natural o colocada, de modo que nunca exista una celda transitable conectada al exterior del bioma.
  - **Cosecha sin apertura exterior:** El individuo debe poder interactuar y cosechar (`eat_plant` / `collect`) directamente desde el espacio seguro interno sin necesidad de minar ni reponer bloques de cierre.
  - **Plantación a partir del día 2:** El día 1 se consagra exclusivamente a la supervivencia básica (herramientas, refugio, agua y sellado nocturno). La agricultura se inicia en los días sucesivos, una vez asegurado el cobijo estable y con excedente de retoños y tiempo diurno.
  - **Componente separado:** Desacoplar la agricultura de `RefugioNocturno`. Debe estructurarse como un componente propio independiente (p. ej. `Horticultura` o meta de S3), preservando la simplicidad y robustez de la máquina de estados del refugio.
