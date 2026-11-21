# Encargo de la deuda 11: cuándo merece la pena perseguir un sitio

Deuda 11 de `docs/DEUDA_TECNICA_CRAFTER.md`. Rama `feature/deuda11` desde `main` (`e322217`). Medición pareada contra la referencia `base_v2_31.json` y `base_v2_32.json` (`docs/METODO_MEDICION.md`).

**Modelos:** diseño, este documento; implementación, Opus 5.5; mediciones, Flash.

**Principio:** cambio mínimo. No hay estrategias nuevas, ni componentes nuevos, ni fases. Todo ocurre en `Recinto` (`ida/sistemas/proteger.py`) y reutiliza lo que ya calcula la alostasis (`s1.alostasis`).

---

## 1. El problema, con datos

Diagnóstico de la primera noche (`docs/DIAGNOSTICO_PASO3.md`; 3 semillas, 10 000 pasos):

| | Sin filtro de orientación (lo que hay en `main`) | Con filtro de orientación (revertido) |
|---|---|---|
| No encuentra sitio | 54,8 % | 24,8 % |
| No lo completa a tiempo | 28,7 % | 53,6 % |
| Muere antes de anochecer | 1 | 5 |
| Pasa la noche dentro | 11 de 115 | 14 de 125 |
| Score total (3 semillas) | 35,33 | 30,92 |

El filtro de orientación **encuentra** sitios, pero muchos piden material, una herramienta o tiempo. **Perseguirlos al anochecer mata más que no perseguir nada.** Lo que falta no es encontrar más sitios, sino una pregunta: **¿llego a completarlo antes de que oscurezca?**

## 2. Lo que ya existe y se reutiliza

- `Sitio.coste`: los pasos para completar el sitio. Con `_requisitos`, incluye lo que cuesta conseguir lo que falta (el planificador del paso 5).
- `alostasis()` en `s1.py`: el **déficit** del cobijo y su **tendencia** (media móvil del cambio por latido).
- La histéresis (`MARGEN_SITIO`) y la reevaluación cada `CADA_EVALUACION` latidos.

## 3. Diseño

### 11a. Factibilidad en el tiempo (el cambio central)

**Tiempo disponible.** Son los latidos que quedan hasta que el cobijo llegue al nivel en que el peligro aparece:

```
T_disponible = (D* − deficit) / tendencia     si tendencia > 0 y deficit < D*
             = 0                              si deficit ≥ D*
             = ∞                              si tendencia ≤ 0 (amanece o es de día sin bajar)
```

**D\* se aprende, no se escribe.** Es el déficit del cobijo en el que llegan los primeros daños o los peligros a la vista, cada noche. La memoria guarda la mediana de los últimos valores. Su previo es 0,7, declarado y genérico (una necesidad «casi apurada»), con peso 2. Es contingencia como la de la aliestesia: a qué nivel de la necesidad aparece el peligro.

**Holgura de un sitio:**

```
holgura(s) = T_disponible − coste(s) · (1 + MARGEN_TIEMPO)      # MARGEN_TIEMPO = 0,2, declarado
```

**Reglas, en `Recinto._elegir` y en `Recinto._requisitos`:**
1. **Factible = holgura ≥ 0.** Solo se eligen sitios factibles, con el más barato primero, como hoy.
2. **Sitio en curso:** se mantiene mientras su holgura **restante** sea ≥ 0 (con el coste que le queda, no el inicial).
3. **Abandono:** si el sitio en curso pasa a holgura < 0 y no hay otro factible, se abandona. `Recinto` informa de que no hay sitio, `Proteger` no propone ni pide, y deciden las demás estrategias: huir, defenderse, afrontar, etc.
4. **Sin sitio factible no se pide material** (`Proteger.pedir`), porque conseguir material para un sitio inalcanzable es lo que mataba.
5. **La alostasis no cambia,** salvo un detalle: si no hay sitio factible, el horizonte es `COSTE_SIN_SITIO`, como hoy. Así la intensidad sigue subiendo pronto los días siguientes.

**Lo que el diagnóstico registra en cada primera noche:**
- `T_disponible` al elegir el sitio;
- la holgura;
- si hubo abandono, y en qué latido.

### 11b. Volver a meter el filtro de orientación

Es `git revert 70ae63e` (el revert del commit `5663772`), y también el presupuesto de planes, si hace falta para que no haya latidos lentos (`86629d3`).

Con 11a, los sitios que encuentra el filtro solo se persiguen si dan tiempo. **Hipótesis:** «no encuentra sitio» baja sin que suba «muere antes de anochecer».

### 11c. Volver a meter el material desde el mapa local

Es `git revert 803dc3b` (el revert del commit `8833f62`). Con 11a+11b, conseguir material solo se intenta para sitios factibles.

**Si vuelve el latido de más de 100 ms**, poner un presupuesto de cálculo declarado en esa búsqueda. Con `--plazo-logico` ya no cambia los resultados, pero tiene que caber en el plazo de reloj por defecto.

Cada subpaso va tras su interruptor (`factibilidad_temporal`, `filtro_orientacion` y `material_mapa`), para medirlos uno contra otro. Al cerrar la deuda, se quitan los interruptores de lo que se quede.

## 4. Lo que no se toca

- `Proteger` (salvo la regla 4), `Afrontar`, el planificador, la alostasis (salvo el horizonte sin sitio factible) y el Tribunal.
- No se añade ninguna fase, ni «refugio de emergencia» ni nada parecido. Si no hay sitio factible, se cede a lo que ya existe.

## 5. Medición (Flash)

Con el método nuevo: `--plazo-logico 40`, 100 000 pasos, vista 9×7, sin herencia y manual estricto, con las semillas 31 y 32. Cada condición se compara **de forma pareada** con su referencia (`resumen_evaluacion.py --pareada`):

| Medición | Interruptores | Frente a |
|---|---|---|
| E1 | `factibilidad_temporal` | `base_v2_31` y `base_v2_32` |
| E2 | `factibilidad_temporal`, `filtro_orientacion` | E1 y referencia |
| E3 | los tres | E2 y referencia |

Antes de medir, Opus hace el diagnóstico de la primera noche con las tres condiciones (3 semillas, 10 000 pasos, en serie), con la tabla de `DIAGNOSTICO_PASO3.md` más las columnas nuevas de 11a.

## 6. Criterios de aceptación (escritos antes de medir)

Para la combinación que se quede (la mejor de E1, E2 y E3), frente a la referencia, con la comparación pareada:

1. **Score:** diferencia > 0 en las dos semillas, y con un IC pareado que excluye el 0 en al menos una.
2. **`wake_up`:** diferencia pareada > 0 en las dos semillas.
3. **Muere antes de anochecer** (diagnóstico): no más que en la referencia.
4. **Otros mundos:** invariancia OK en mínimo, archivos y ajedrez.
5. **Tests con un mundo de juguete:**
   - un sitio no factible no se persigue;
   - un sitio en curso se abandona cuando su holgura pasa a negativa;
   - D\* se aprende de los primeros daños.

Si ninguna combinación cumple el criterio 1, se documenta como resultado negativo, se quita todo y la deuda 11 se reformula.

## 7. Riesgos

- **D\* mal aprendido con pocas noches:** el previo (0,7, con peso 2) lo protege al principio de cada vida. Sin herencia, cada episodio vuelve a empezar desde el previo, y eso se declara.
- **Abandono en falso al principio de una noche larga:** la regla 2 usa el coste restante. Hay que vigilar en la traza que no abandona un sitio casi terminado.
- **Coste de cálculo:** 11a solo añade una resta por candidato. 11b y 11c ya se midieron, con sus latidos lentos y su arreglo.
