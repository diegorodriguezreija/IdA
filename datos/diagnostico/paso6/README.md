# Humo del paso 6 (no es medición)

Fecha: 21/11/2026. Rama `feature/defensa`, commit `cacaf27` (código; los datos van en el commit siguiente).
Ejecutados en serie, sin otros procesos de IdA. 3000 pasos por semilla: 9-13 episodios, intervalos muy anchos.

```
python herramientas/evaluar_crafter.py --pasos 3000 --semilla S --vista oficial --sin-herencia --manual estricto \
    --sin-estrategias-propias [--mecanismos ...] --salida datos/diagnostico/paso6/<condición>_S.json
```

| Fichero | `--mecanismos` |
|---|---|
| `apagados_S` | (ninguno) |
| `6a_S` | `peligro_aprendido` |
| `6abc_S` | `peligro_aprendido afrontar arma_instrumental` |

`.json`: salida de `evaluar_crafter.py`; `.txt`: lo que imprime.

La causa de muerte no se cuenta igual en las dos versiones del adaptador: apagado, el daño se atribuye por geometría
(esqueleto a ≤ 4 casillas, el resto a ≤ 1, al final de la acción); con `peligro_aprendido`, por contacto en cada paso
del entorno. En la semilla 32, el episodio 8 muere en el mismo paso (163) en las dos condiciones: apagado consta como
«desgaste» y con 6a como «zombi».

## Equivalencia del 6d (punto 3 de la ronda del 21/11/2026)

Comprueba que borrar `DefensaArmada` y `CerrarDistancia` y quitar los interruptores no cambia la conducta.

| Fichero | Código | Comando |
|---|---|---|
| `equivalencia_027062e_31` | `027062e` | `... --mecanismos peligro_aprendido afrontar arma_instrumental --sin-estrategias-propias` |
| `equivalencia_6d_31` | `2085f87` (6d) | sin opciones |

Las dos con `evaluar_crafter.py --pasos 3000 --semilla 31 --vista oficial --sin-herencia --manual estricto`, en serie. Los
JSON coinciden campo a campo salvo `tiempo_segundos` (34,56 y 34,76), `ms_por_paso` (11,52 y 11,59) y los campos que
registran las opciones: `mecanismos` (los tres frente a ninguno) y `sin_estrategias_propias` (true frente a false).
Score 16,91 % [8,86, 20,97] en las dos; 0 latidos cortados.
