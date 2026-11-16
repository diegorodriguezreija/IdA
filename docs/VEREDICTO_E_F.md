# Veredicto de los bloques E y F

**Pregunta:** ¿aporta la memoria, con su uso proactivo?

**Respuesta: no, con lo medido.** Con E (memoria) y F (Expectativa y Plan) activados, ningún mundo ni perfil mejora de forma significativa frente a `base-v2.0`. Hay un empeoramiento significativo y cuesta entre un 7 y un 14 % más de tiempo por latido.

## Datos

Crafter, mínimo y archivos; Equilibrado, Valiente, Reactivo y sin experiencia; N = 10 linajes; pareado por semilla, IC 95 %; 16/11/2026. Detalle, comandos y muertes por causa en [`MEDICIONES_F.md`](MEDICIONES_F.md) y [`MEDICIONES_E.md`](MEDICIONES_E.md).

| | Solo E − base | E + F − base | F sobre E |
|---|---|---|---|
| Mejoras significativas | 0 | 0 | 0 |
| Empeoramientos significativos | 0 | 1: Crafter Valiente, logros −0,77 ± 0,73 | 0 |
| Crafter, logros (Equilibrado / Valiente / Reactivo) | −0,27 / −0,57 / −0,10 | −0,37 / −0,77 / −0,33 | −0,10 / −0,20 / −0,23 |
| Archivos, muertes por hambre (de 40 vidas por perfil) | 12 → 13 / 16 / 13 | 12 → 15 / 15 / 15 | — |
| ms por latido, Equilibrado (apagado → con mecanismos) | +0,15 a +0,16 | +0,16 a +0,24 | +0,01 a +0,08 |

Mínimo: todas las diferencias dentro del ruido (latidos de −5,4 a +9,1; setas de 0,00 a +0,05).

## Por qué no aporta (causas probables, no verificadas una a una)

1. **La base ya tenía la memoria que usan las decisiones:** saber con confianza, registros por (verbo, clase), mapa con rutas y `donde`. E reorganiza esa memoria (búfer, grafo, conceptos, reducción) pero ninguna estrategia decide con algo que antes no estuviera.
2. **La evocación (E5) cobra atención por lo que antes se leía gratis:** la potencia de S2 sube (archivos, de 1,42 a 1,91 por latido) y S3 se queda más veces sin amplitud o potencia (archivos, Equilibrado: de 223 latidos a 406 con solo E y a 346 con E + F).
3. **F2 reproduce decisiones que ya se tomaban:** la ruta completa del plan coincide con el siguiente salto que `recordar_comida` recalculaba en cada latido, y la cadena de recetas es el orden que `PlanTecnologico` ya seguía. El resultado es idéntico en mínimo y casi idéntico en Crafter.
4. **F1 solo cambia señales secundarias:** el error de predicción entra en el feedback y en el arousal, sin umbrales calibrados. En Crafter, los tres Δ de logros de F sobre E son negativos.

## Recomendación: fusionar solo una parte

- **Fusionar, sin cambio de conducta:**
  - **Tope de 64 Creencias por latido:** protege el rendimiento si crece la memoria; invariante.
  - **Herencia configurable (E7):** por defecto 1,0, igual que antes.
  - **Interruptores de `MecanismosMemoria`:** apagados en todos los mundos. Con esto, el código de E y F entra en `main` sin activarse, y la invariancia con `base-v2.0` se mantiene.
- **No activar** E1 a E6 ni F1 y F2 en ningún mundo (`MEMORIA_E` y `MEMORIA_EF` fuera de los perfiles). No mejoran nada, cuestan tiempo y en Crafter tienden a empeorar.
- **Alternativa más estricta:** no fusionar nada y dejar E y F en sus ramas. La fusión parcial solo merece la pena si el siguiente trabajo (Prospectiva, o estrategias que decidan con el grafo o con la valencia de los recuerdos) va a partir de este código. Si no, conviene no fusionar.

Para que la memoria aporte, alguna decisión tendría que depender de lo que solo E y F saben (relaciones del grafo, conceptos de clases no vistas, sorpresa de un plan). Así hay que diseñar y medir el siguiente bloque.
