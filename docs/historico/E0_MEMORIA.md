# E0 — Inventario de la memoria y correspondencia con el bloque E

Paso E0 del encargo del bloque E ([`PLAN_IMPLEMENTACION.md`](PLAN_IMPLEMENTACION.md)); decisiones 7 y 19 a 22 de [`REDISENO_BASE.md`](REDISENO_BASE.md). Base: `base-v2.0`. Rutas de `ida/core/memoria.py` salvo que se indique otra.

## Qué hay hoy

| Parte | Dónde | Qué guarda | Cuándo se escribe | Cuándo se olvida |
|---|---|---|---|---|
| Proposiciones (`saber`) | `Proposicion`, `Memoria.saber` | Relación de una clase (nutre, hace daño, útil…) con confianza por fuentes (`c_exp`, `c_aut`), confirmaciones y refutaciones | Al aprender del efecto de cada acción (`aprender`, Core paso 4 del latido) | `consolidar`: hipótesis sin actualizar > 150 latidos y confianza < 0,4 |
| Registros | `Registro`, `Memoria.registros` | Balance medio de un verbo sobre una clase | En `aprender` | `consolidar`: un solo uso, \|media\| < 0,5 y > 200 latidos |
| Lugares (hogar) | `Memoria.lugares` | Bienestar recordado por lugar | Al cerrar cada episodio (`latido._episodio`) | No se olvidan |
| Mapa espacial | `Memoria.mapa`, `Arista`, `mapa_valores` | Grafo de transiciones entre lugares y su valor por *replay* | Cada cambio de ubicación (`registrar_transicion`); *replay* al dormir | Aristas de un uso con más de 300 latidos; poda LRU a 200 nodos; los valores decaen ×0,9 por noche |
| Dónde está cada clase | `Memoria.donde`, `RecuerdoLugar` | Última ubicación en que se vio una clase al alcance | `_aprender` del Core | > 300 latidos, o al llegar y no encontrarla (`olvidar_donde`) |
| Familiaridad | `Memoria.clases_vistas` | Veces que se ha visto cada clase | Exterocepción | No se olvida |
| Búfer rápido | `Memoria.buffer`, `guardar_rapido` | K piezas de mayor arousal por latido (K = 5 completa, 2 ligera) | Cierre de cada latido | Se vuelca a `memoria.db` al dormir; en `consolidar` solo sobrevive lo de arousal ≥ 0,85 |
| Episodios | `Episodio`, `Memoria.episodios` | Tramos de latidos con su balance y trayectoria | Se abren y cierran en `latido._episodio` | No se olvidan; el *replay* recorre los nuevos |
| Consolidación | `Memoria.consolidar(ahora)` | Olvido de lo anterior y *replay* inverso de trayectorias | Al dormirse (`Organismo.vivir`), con experiencia | — |
| Persistencia | `ida/core/persistencia.py` | Tablas `piezas`, `episodios`, `saber`, `lecturas` en `memoria.db` | `volcar` al dormir y al final de la vida | Nadie la lee de vuelta |
| Herencia | `legado` / `heredar`, `ida/core/linaje.py` | Proposiciones demostradas (como hipótesis fuertes, ×0,8) y registros con n ≥ 2 (n / 2) | Al morir / al nacer | — |
| Creencias (bloque D) | `S3.Creencia` | Una pieza por proposición, cada latido, en `ef` | Cada latido | — |

## En qué se convierte

| Mecanismo (paso) | Interruptor del `Perfil` | Qué cambia | Con el interruptor apagado |
|---|---|---|---|
| E1 Búfer diurno | `mecanismos.buffer` | Nuevo búfer de tamaño fijo (`Memoria.diurno`) con las piezas mejor puntuadas (arousal + feedback) y el episodio del día (secuencia de ondas) | No existe |
| E2 Consolidación | `mecanismos.consolidacion` | Al dormir (o al final de la vida en mundos sin sueño) lo mejor del búfer pasa a un grafo semántico (`Memoria.grafo`: nodos y relaciones con fuerza) y al almacén de días (`Memoria.dias`); el búfer se vacía | No existe; `consolidar` sigue igual |
| E3 Instancias y conceptos | `mecanismos.conceptos` | `Objeto` mantiene en `Memoria.conceptos` un prototipo promediado por clase, con id estable sin significado y la etiqueta legible como metadato | No existe |
| E4 Reducción nocturna | `mecanismos.reduccion` | Cada noche, las fuerzas del grafo y la confianza de las hipótesis se reducen en proporción y se poda lo que cae bajo un umbral; sustituye al olvido de hipótesis de `consolidar` | Regla de olvido actual |
| E5 Recuperación evocada y reconsolidación | `mecanismos.evocacion` | Un componente de S2 (`Recuerdo`) trae a la dimensión activa lo que la memoria asocia a los impulsos y objetos presentes, con la potencia que sobre; `Valor` y `recordar_comida` leen esas piezas en lugar de la memoria; lo recuperado se refresca y pasa al búfer | `Valor` y `recordar_comida` leen la memoria |
| E6 Repaso en calma | `mecanismos.repaso` | En calma, con potencia de sobra y sin recuerdos evocados, se refuerzan los recuerdos recientes de más puntuación | No existe |
| E7 Herencia configurable | `mecanismos.tasa_herencia` | Fracción (0 a 1) de lo aprendido que se hereda, ordenado por trust | 1,0: todo lo demostrado y los registros con n ≥ 2, como hoy |

Partes que no cambian en el bloque E: lugares y hogar, mapa espacial y *replay*, `donde`, familiaridad, persistencia (sigue sin leerse de vuelta), expectativas y lecturas de la biblioteca.
