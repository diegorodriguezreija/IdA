# Deuda técnica de Crafter (pendiente tras el encargo C)

Lista de asuntos detectados durante el encargo C (`docs/ENCARGO_CRAFTER_C.md`) que **no** se abordan en él, para tratarlos cuando termine. Cada punto lleva dónde se vio y una propuesta de partida, sin compromiso de diseño.

---

Las deudas 1 a 8 son del encargo C, cuando Crafter tenía estrategias propias. Desde el paso 6d `estrategias_propias()` de Crafter devuelve `{}` (`docs/FASE_GENERALIZACION_CRAFTER.md`, «Pilar 1»), y casi todas dependían de código ya borrado. Se conserva el título y el motivo del cierre; el texto original está en el historial de git (`f26c243`).

## 1. `RefugioNocturno` hace casi todo — resuelta

- **Estado:** `RefugioNocturno` se borró en el paso 3 (`docs/ENCARGO_PASO3_PROTEGER.md`, «Resultado»), y lo que absorbía pasó a la base: mapa cognitivo (paso 1), planificador sobre requisitos (paso 5) y `Proteger` (paso 3). Hoy no aparece en `ida/` ni en `herramientas/`.

## 2. La intensidad del impulso no llega al Tribunal — resuelta

- **Estado:** los apaños del mundo (`_motivacion`, urgencia de C.0c-1, hueco gástrico de C.3d) se borraron con las estrategias propias; en la base, el paso 0 probó la urgencia local (0a, retirada sin efecto) y dejó la aliestesia (0b) (`docs/PROPUESTA_PASO0.md`, «Resultado»).

## 3. Vaivén en campo abierto — obsoleta

- **Estado:** se midió con `huir`, `sobresalto` y `alimentarse` de las estrategias propias del encargo C, que ya no existen. No se ha medido en la línea general; si reaparece, irá como deuda nueva con su diagnóstico.

## 4. Grupo Reactivo: muertes por sed — obsoleta

- **Estado:** salía de los benchmarks `c3b_completo` y `c3d_completo`, con `RefugioNocturno` y `provisiones`, borrados. La línea general no se ha medido por perfiles en Crafter.

## 5. Piezas mantenidas provisionalmente (C.3b y C.3d) — resuelta

- **Estado:** la patrulla (C.3b) y la caza oportunista (C.3d) eran partes de `RefugioNocturno` y se fueron con él.

## 6. Casos residuales del primer día — obsoleta

- **Estado:** eran casos de la elección de roca de `RefugioNocturno` y de C.1; el sitio para protegerse lo elige hoy `Recinto`, cuyos problemas están en la deuda 11.

## 7. Herramientas de diagnóstico — obsoleta

- **Estado:** los scripts citados (`diagnostico_crafter_c0b.py`, `diagnostico_vacas_c3b.py`, `diagnostico_vacas_c3c.py`, `diagnostico_c3d_d_e.py`) ya no existen. Los diagnósticos actuales (`herramientas/diagnostico_*.py`) reutilizan `evaluar_crafter.evaluar`; el registro por latido unificado no se hizo.

## 8. Rediseño del huerto (C.4 descartada) — obsoleta

- **Estado:** el diseño dependía de `RefugioNocturno` (rama `wip/c4-argon`). El huerto pasa al paso 4 del plan (proteger X: forrajeo y huerto), en la base y sin ese código.

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
- 11c se vuelve a medir solo, sobre 14.2 (rama `feature/material-mapa`).

## 12. Afinar cuándo merece la pena luchar (defeat_zombie 40 % frente a 54 % de DefensaArmada)

- **Qué pasa:** con `Afrontar` (paso 6), `defeat_zombie` queda en el 40,21 % (D2) y el 40,27 % (D3), frente al 54,19 % de F3, que aún tenía `DefensaArmada`. El criterio del paso 6 pedía ≥ 50 % (`docs/ENCARGO_PASO6_DEFENSA.md`, «Resultado»).
- **Lectura:** `Afrontar` es más prudente. Lucha solo si el margen estimado supera la reserva de 3/9, y sin datos usa un previo pesimista de 10 golpes por derribo. `DefensaArmada` atacaba siempre que tenía espada y salud ≥ 4.
- **Pendiente:**
  - diagnosticar en qué encuentros `Afrontar` huye y la lucha habría salido bien: reserva, previo de golpes y tasa de daño por latido de exposición;
  - corregirlo en la base, sin umbrales para un mundo.
- **Cuidado:** las muertes por zombi + desgaste no han subido. Luchar más no debe subirlas (riesgo «luchar de más» del encargo).

## 13. Guillotina lógica para evaluaciones reproducibles — resuelta

- **Estado:** `evaluar_crafter.py --plazo-logico OPS` (y los `diagnostico_*.py` que llaman a `evaluar`) mide el plazo del latido en operaciones (llamadas a `Onda.control_vital`) en vez de en ms. Por defecto sigue el reloj. Calibración y comprobaciones en `docs/METODO_MEDICION.md`.

- **Qué pasa:** la guillotina corta por reloj, así que un solo latido cortado cambia una trayectoria; para las evaluaciones, conviene un plazo lógico (en operaciones) en lugar de en milisegundos.
- **Dónde se vio:** en la comprobación de equivalencia del 6d (`paso6_D4.json`, semilla 31), un único latido cortado en el episodio 64 cambió la causa de muerte de ese episodio de flecha a zombi (167 pasos frente a 169), aunque la Score, el IC, los episodios y los 22 logros fueron idénticos a D2.

## 14. Cadena de herramientas — cumplida en parte

- **Estado:** el planificador reúne en lote el material de las metas que comparten una estación (14.2, siempre activo; 14.3 retirado). Frente a `base_v2`, la espada sube +5,50 y +7,12 puntos (IC que excluyen el 0) y el pico y la espada de piedra suben de forma significativa en las semillas 31 y 32. La Score sube +0,76 y +0,57 sin que ningún IC excluya el 0, y el pico baja −0,27 en la 32. Cuesta `collect_drink` (−3,40 en la 31) y `eat_cow`. Detalle en `docs/ENCARGO_DEUDA14_HERRAMIENTAS.md`, «Resultado».

- **Qué pasa:** pico de madera 64-72 % y espada 43-47 % en la línea general, frente a 92-96 % en la procedimental.
- **Datos de la línea general:** `make_wood_pickaxe` 62,40 % y 71,51 %, `make_wood_sword` 42,56 % y 47,12 % (D2 y D3, `docs/MEDICION_PASO6.md`).
- **Datos de la procedimental:** `make_wood_pickaxe` 95,45 %, 96,41 % y 96,40 %, `make_wood_sword` 92,42 %, 92,43 % y 91,73 % (`techo_main.json`, `techo_c3d.json` y `main_sin_herencia.json`, semilla 31).
