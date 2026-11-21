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


## 9. Aliestesia (paso 0b) sin condición

- **Qué pasa:** la aliestesia solo actúa cuando dos o más necesidades comparten rasgo (`Perfil.aliestesia`, en `ida/core/mundo.py`). Sin esa condición cambiaba decisiones en mínimo (semillas 1-3, latidos 52, 127 y 24) y en archivos (semillas 1 y 3, latidos 4 y 5), según `invariancia.py` en la rama `feature/cierre-paso0`.
- **Lo más limpio** sería que 0b actuara siempre.
- **Requisito para quitar la condición:** benchmark pareado (N = 10) de mínimo y archivos, con el criterio de la sección e de `docs/PROPUESTA_PASO0.md`: ninguna diferencia significativa en contra en latidos ni en fitness, ni más muertes por hambre en archivos, y un coste por latido como mucho un 10 % mayor.

## 10. Peligro sin gradaciones (para el paso 6) — resuelto en el paso 6

- **Estado:** desde el paso 6 el adaptador no da `peligro`. Lo calcula la base con el daño aprendido (`ida/core/peligro.py`), y `defeat_skeleton` sube al 7,83 % y al 5,21 % (`docs/MEDICION_PASO6.md`).

- **Qué pasa:** con el manual estricto, el adaptador da el mismo peligro (`PELIGRO_MANUAL` = 0,8) a todo lo que el manual declara PELIGROSO, flecha incluida. IdA huye de las flechas y casi nunca se enfrenta al esqueleto: `defeat_skeleton` cae del 43,17 % al 7,39 % (`docs/DIAGNOSTICO_G3.md`).
- **Lo correcto:** aprender cuánto daño hace cada clase. La experiencia ya registra la causa de cada daño (`Efecto.causa`). Pertenece al paso 6 (defensa general).
- **Referencias para medirlo,** en `docs/DIAGNOSTICO_G3.md`:
  - el contrafactual con los peligros graduados de `main` (zombi 0,8, esqueleto 0,7, flecha 0,5, lava 1,0): `defeat_skeleton` pasa de 1/27 a 6/29 episodios (`main`: 7/24), con las semillas 31-33 y 3000 pasos, sin subir la Score;
  - `herramientas/diagnostico_logros.py`, que cuenta los latidos que gana «huir de flecha» y «acortar distancia a esqueleto» y los ATACAR al esqueleto, para comparar con las mismas semillas.

## 11. Cuándo perseguir un sitio para protegerse (y después, el filtro de orientación)

- **Qué pasa:** `Recinto` propone el sitio más barato que puede completar o cuyos requisitos se pueden conseguir. No compara ese coste completo (ir, conseguir material o herramienta, cavar y cerrar) con el tiempo que queda hasta la oscuridad.
- **El filtro de orientación** (`orientable`, commit `5663772`, revertido en `70ae63e`) descartaba los sitios que el modelo del cuerpo no deja cerrar, y con ello aparecían muchos más sitios posibles:
  - «no encuentra sitio» bajaba del 54,8 % al 24,8 %;
  - pero «no lo completa a tiempo» subía del 28,7 % al 53,6 %, sobre todo por falta de material;
  - la Score bajaba en las tres semillas (`docs/DIAGNOSTICO_PASO3.md`, «Tercera ronda»).
- **Lo pendiente:**
  1. Decidir cuándo perseguir un sitio comparando su coste completo con el tiempo hasta la oscuridad (la tendencia del cobijo, que ya estima la alostasis). Un sitio que no se puede completar antes de lo oscuro no se persigue.
  2. Después, reintroducir el filtro de orientación, con su presupuesto de planes por latido (commit `86629d3`, revertido en `d69d3d6`), y medirlo con el diagnóstico completo.

## 12. Afinar cuándo merece la pena luchar (defeat_zombie 40 % frente a 54 % de DefensaArmada)

- **Qué pasa:** con `Afrontar` (paso 6), `defeat_zombie` queda en el 40,21 % (D2) y el 40,27 % (D3), frente al 54,19 % de F3, que aún tenía `DefensaArmada`. El criterio del paso 6 pedía ≥ 50 % (`docs/ENCARGO_PASO6_DEFENSA.md`, «Resultado»).
- **Lectura:** `Afrontar` es más prudente. Lucha solo si el margen estimado supera la reserva de 3/9, y sin datos usa un previo pesimista de 10 golpes por derribo. `DefensaArmada` atacaba siempre que tenía espada y salud ≥ 4.
- **Pendiente:**
  - diagnosticar en qué encuentros `Afrontar` huye y la lucha habría salido bien: reserva, previo de golpes y tasa de daño por latido de exposición;
  - corregirlo en la base, sin umbrales para un mundo.
- **Cuidado:** las muertes por zombi + desgaste no han subido. Luchar más no debe subirlas (riesgo «luchar de más» del encargo).

## 13. Guillotina lógica para evaluaciones reproducibles

- **Qué pasa:** la guillotina corta por reloj, así que un solo latido cortado cambia una trayectoria; para las evaluaciones, conviene un plazo lógico (en operaciones) en lugar de en milisegundos.
- **Dónde se vio:** en la comprobación de equivalencia del 6d (`paso6_D4.json`, semilla 31), un único latido cortado en el episodio 64 cambió la causa de muerte de ese episodio de flecha a zombi (167 pasos frente a 169), aunque la Score, el IC, los episodios y los 22 logros fueron idénticos a D2.

