# Paso 0 — Diagnóstico del Vaivén Diurno en Crafter

Diagnóstico empírico previo a la Fase 5, ejecutado sobre `feature/fase5-ciclo-y-refugio` (`5472bc2`) en Crafter (`semillas 1..10`, `300` latidos/semilla, perfil `Equilibrado`).

---

## 1. Cifras Observadas

- **Latidos diurnos en calma/curiosidad (`luz >= 0,5`, `afecto ∈ {CALMA, CURIOSIDAD}`):** `778` latidos en total.
- **Latidos atrapados en patrón `A → B → A → B`:** **`409` (`52,6 %`)**.
- **Empates resueltos por azar en vaivén:** **`0` (`0,0 %`)**.

### Desglose por ganador del Tribunal en los latidos de vaivén

| Ganador (`sistema:motivo`) | Latidos en vaivén | % |
|---|---:|---:|
| `CORE/S1: impulso: acercarse a la comida` | `257` | `62,8 %` |
| `CORE/S3: plan: ir a por wood` | `92` | `22,5 %` |
| `CORE/S3: plan: collect_sapling` (`COGER hierba`) | `31` | `7,6 %` |
| `CORE/S3: plan: ir a por stone` | `23` | `5,6 %` |
| `CORE/S2: curiosidad: explorar` | `6` | `1,5 %` |

---

## 2. Clasificación de la Causa

- **No es causa (a) (empate repetido):** `0` empates registrados.
- **Causa principal — (b) Dos componentes que tiran en sentidos opuestos + (c) Curiosidad demasiado débil frente al apetito basal:**
  1. Cuando el individuo está saciado y en calma (`L27–L28`, semilla 1), `S1` (`impulso: acercarse a la comida`, `arousal = 0,266`, `confianza = 0,60`, puntuación `0,213`) supera ligeramente a `S2` (`Curiosidad`, `arousal = 0,275`, `confianza = 0,50`, puntuación `0,206`). Esto mantiene al individuo pegado a la comida cercana o tirando en sentido opuesto a `S3: PlanTecnologico` (`MOVER celda_26_31` vs `MOVER celda_27_31`), generando vaivén entre dos casillas.
  2. Además, en `COGER hierba` (`L9–L13`, semilla 1), `MundoCrafter._interactuar()` intenta orientarse dando un paso hacia una casilla adyacente de hierba transitable, lo que desplaza al jugador sobre la hierba en vez de recolectarla desde su casilla, alternando entre `(31,32)` y `(32,32)`.

---

## 3. Implicación para la Fase 5

El ritmo circadiano del **Paso 2** (subiendo la ganancia diurna de `Curiosidad` y bajando la alerta basal en calma) atacará directamente la debilidad relativa de `Curiosidad` (`0,206` frente a `0,213` de `S1`). La comprobación de `H5.4` (proporción de vaivén diurno tras los cambios) medirá cuánto se reduce este `52,6 %` inicial.
