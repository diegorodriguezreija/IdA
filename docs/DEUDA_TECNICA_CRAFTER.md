# Deuda técnica de Crafter (pendiente tras el encargo C)

Lista de asuntos detectados durante el encargo C (`docs/ENCARGO_CRAFTER_C.md`) que **no** se abordan en él, para tratarlos cuando termine. Cada punto lleva dónde se vio y una propuesta de partida, sin compromiso de diseño.

---

## 1. `RefugioNocturno` hace casi todo

- **Qué pasa:** es una estrategia de S2 para el impulso «cobijo». Pero hoy también reúne madera y herramientas, bebe y come antes de sellar, se abastece por la mañana, patrulla (C.3b) y caza vacas (C.3d). Lo ha ido absorbiendo porque guarda la memoria del mapa y de las vacas.
- **Por qué importa:**
  - Se aleja de los tres sistemas: comer y beber son de S1, y aquí se resuelven dentro de S2, puenteando a `alimentarse`.
  - El fichero crece mucho y cada sesión de un modelo cuesta más.
- **Propuesta, como refactorización medida que no cambie la conducta** (arnés y benchmark iguales dentro del ruido):
  - un mapa cognitivo compartido del mundo (lo percibido y recordado: materiales, vacas, agua, recintos), legible por varios componentes;
  - el forrajeo y el abastecimiento en un componente propio de S1;
  - la madera y las herramientas, en `PlanTecnologico`;
  - `RefugioNocturno`, limitado a elegir, construir, ocupar y abrir el refugio.

## 2. La intensidad del impulso no llega al Tribunal (base)

- **Qué pasa:** en calma, el Tribunal decide casi solo por la confianza. Las estrategias propias de Crafter lo compensan fijando su arousal y su confianza según la urgencia: `_motivacion` en `RefugioNocturno`, la urgencia de C.0c-1 y el hueco gástrico de C.3d. Es un apaño declarado.
- **Propuesta:** decidir en la base cómo modula la intensidad del impulso (déficit de S1) la puntuación, y si S2 (valor y emoción) interviene. Después, retirar los apaños del mundo y medir.

## 3. Vaivén en campo abierto

- **Qué pasa:** en 12 de 20 vidas (semillas 11–30) el individuo va y viene más de 20 latidos entre 2 casillas, sobre todo al alternar `huir`, `sobresalto` y `alimentarse` (`INFORME_C.md`, 2.11). El arreglo de C.0c-2 solo resolvió el caso de chocar contra la roca.
- **Propuesta:** un diagnóstico de qué estrategias alternan y con qué puntuaciones. Probablemente es cosa del Tribunal (continuidad o histéresis), así que se cruza con el punto 2.

## 4. Grupo Reactivo: muertes por sed

- **Qué pasa:** en los benchmarks completos (`c3b_completo`, `c3d_completo`), Reactivo tiene 10–11 de 30 muertes por sed, frente a 4–7 en los demás grupos, y es el único que no mejora en latidos frente a `ref_c0` (−23,9 ± 97,7).
- **Propuesta:** diagnosticar qué hace distinto ese perfil con el agua (¿no usa `RefugioNocturno` igual? ¿no llega a `provisiones`?).

## 5. Piezas mantenidas provisionalmente

- **C.3b (patrulla, visitadas que caducan) y C.3d (caza oportunista):** no confirmaron del todo su hipótesis. Su efecto es pequeño, en la dirección buena en evaluación, y no significativo.
- **Propuesta:** reevaluarlas cuando C.4 esté cerrado. Si no aportan nada medible junto al huerto, retirarlas para simplificar.

## 6. Casos residuales del primer día

- **Sin roca a la vista** (2 de 40 vidas; semilla 35, roca a 25 casillas).
- **Candidatos lejanos que desvían de una roca cercana** (semilla 16 en C.1).
- **Flechas al anochecer antes de cerrar** (2 de 20 en el arnés largo).

Son pocos casos; solo si siguen pesando tras C.4.

## 7. Herramientas de diagnóstico

- **Qué pasa:** hay varios scripts de diagnóstico parecidos (`diagnostico_crafter_c0b.py`, `diagnostico_vacas_c3b.py`, `diagnostico_vacas_c3c.py`, `diagnostico_c3d_d_e.py`) y el arnés ha crecido.
- **Propuesta:** unificar en el arnés un registro por latido reutilizable (fase, ganador del Tribunal, vitales, posición) y que los diagnósticos sean consultas sobre ese registro.

## 8. Rediseño del huerto (C.4 descartada)

- **Qué pasó:** C.4 (huecos cerrados junto al refugio, rama `wip/c4-argon`) activó la regla de parada: selladas el día 1, 29/40; mediana del arnés largo, 401,5 frente a 417 (`INFORME_C.md`, apartado 8). Cuando el huerto llega a funcionar, alarga mucho la vida (semillas 11 y 20: 1040 y 1168 latidos), pero el diseño falla por tres motivos:
  - plantar el día 1 compite con sellar;
  - abrir el hueco para cosechar lo deja expuesto si una huida interrumpe el cierre (semilla 11, L724–L821);
  - el código añadido a `RefugioNocturno` (~1200 líneas) empeora la conducta aunque casi no se use.
- **Propuesta para un encargo futuro:**
  - plantas en nichos que den al **interior** del refugio, que se comen desde dentro sin abrir nada;
  - plantar a partir del **día 2**;
  - un **componente separado y pequeño**, después de la refactorización del punto 1;
  - medir primero con una sola planta.
- **Aprovechable de la rama WIP:** el arreglo de salida en `amanecer` (no quedarse atascado en la galería; semilla 17) y la separación entre plantas vistas como obstáculo y plantas propias como pared. Cada uno, con su propia medición.

