## Comparación de perfiles (cProfile; tottime agregado)

Total perfilado: base 83.18 s, nueva 86.81 s, Δ +3.62 s (+4.4 %).

### Por zona

| Clave | tottime base (s) | tottime nueva (s) | Δ (s) | llamadas base | llamadas nueva |
|---|---|---|---|---|---|
| `IdA` | 38.18 | 41.26 | +3.08 | 35820668 | 38928057 |
| `herramientas` | 0.12 | 1.86 | +1.74 | 285684 | 3091794 |
| `python` | 16.32 | 15.21 | -1.11 | 51408556 | 51580715 |
| `entorno:opensimplex` | 18.82 | 18.71 | -0.12 | 2744389 | 2744389 |
| `entorno:crafter` | 8.74 | 8.76 | +0.02 | 2970149 | 2949841 |
| `entorno:pil` | 0.73 | 0.75 | +0.01 | 580540 | 580540 |
| `entorno:numpy` | 0.10 | 0.10 | +0.00 | 201128 | 201128 |
| `entorno:imageio` | 0.10 | 0.10 | -0.00 | 36666 | 36666 |
| `entorno:__editable___laboratorio_ida_0_1_0_finder.py` | 0.00 | 0.00 | +0.00 | 2928 | 2928 |
| `entorno:ruamel` | 0.06 | 0.06 | -0.00 | 93124 | 93124 |

### Ficheros de IdA, por Δ

| Clave | tottime base (s) | tottime nueva (s) | Δ (s) | llamadas base | llamadas nueva |
|---|---|---|---|---|---|
| `ida/sistemas/proteger.py` | 13.45 | 0.00 | -13.45 | 15310679 | 0 |
| `ida/mundos/crafter/s1/interpretar/recinto.py` | 0.00 | 10.54 | +10.54 | 0 | 11515846 |
| `ida/sistemas/s3.py` | 5.35 | 0.00 | -5.35 | 1549052 | 0 |
| `ida/nucleo/pieza.py` | 0.00 | 4.40 | +4.40 | 0 | 6976562 |
| `ida/nucleo/onda.py` | 0.00 | 4.28 | +4.28 | 0 | 5537401 |
| `ida/core/pieza.py` | 4.05 | 0.00 | -4.05 | 6394291 | 0 |
| `ida/core/onda.py` | 3.54 | 0.00 | -3.54 | 4554935 | 0 |
| `ida/nucleo/arquitectura.py` | 0.00 | 3.48 | +3.48 | 0 | 3114486 |
| `ida/core/arquitectura.py` | 3.12 | 0.00 | -3.12 | 2670172 | 0 |
| `ida/s3/reaccionar/estrategias/perseguir_metas.py` | 0.00 | 2.28 | +2.28 | 0 | 978884 |
| `ida/cuerpos/cuadricula/geometria.py` | 0.00 | 2.27 | +2.27 | 0 | 2564995 |
| `ida/core/memoria.py` | 1.77 | 0.00 | -1.77 | 2448783 | 0 |
| `ida/s3/comun.py` | 0.00 | 1.60 | +1.60 | 0 | 627803 |
| `ida/sistemas/comun.py` | 1.31 | 0.00 | -1.31 | 656960 | 0 |
| `ida/sistemas_comun.py` | 0.00 | 1.30 | +1.30 | 0 | 656973 |
| `ida/mundos/crafter.py` | 1.22 | 0.00 | -1.22 | 469864 | 0 |
| `ida/cuerpos/cuadricula/mapa.py` | 0.00 | 1.21 | +1.21 | 0 | 36577 |
| `ida/mundos/crafter/adaptador.py` | 0.00 | 1.05 | +1.05 | 0 | 297503 |
| `ida/nucleo/memoria.py` | 0.00 | 1.03 | +1.03 | 0 | 1586465 |
| `ida/sistemas/s1.py` | 0.97 | 0.00 | -0.97 | 496671 | 0 |
| `<string>` | 0.00 | 0.87 | +0.87 | 0 | 2428215 |
| `<frozen importlib._bootstrap_external>` | 0.00 | 0.70 | +0.70 | 0 | 183991 |
| `ida/s1/sentir/amenaza.py` | 0.00 | 0.67 | +0.67 | 0 | 290390 |
| `ida/s3/interpretar/requisito.py` | 0.00 | 0.65 | +0.65 | 0 | 374980 |
| `ida/mundos/crafter/s1/sentir/valoracion.py` | 0.00 | 0.61 | +0.61 | 0 | 488439 |
| `ida/sistemas/s2.py` | 0.52 | 0.00 | -0.52 | 100090 | 0 |
| `ida/cuerpos/cuadricula/buscador.py` | 0.00 | 0.46 | +0.46 | 0 | 1207944 |
| `ida/cuerpos/cuadricula/memoria.py` | 0.00 | 0.42 | +0.42 | 0 | 890973 |
| `ida/core/sentidos.py` | 0.40 | 0.00 | -0.40 | 57222 | 0 |
| `ida/core/peligro.py` | 0.33 | 0.00 | -0.33 | 238024 | 0 |
| `ida/s1/interpretar/apetencia.py` | 0.00 | 0.30 | +0.30 | 0 | 137840 |
| `ida/core/latido.py` | 1.59 | 1.29 | -0.30 | 351392 | 361017 |
| `ida/s3/interpretar/creencia.py` | 0.00 | 0.29 | +0.29 | 0 | 23174 |
| `ida/s1/comun.py` | 0.00 | 0.25 | +0.25 | 0 | 104934 |
| `ida/core/mundo.py` | 0.25 | 0.00 | -0.25 | 96163 | 0 |
| `ida/cuerpos/cuadricula/situacion.py` | 0.00 | 0.22 | +0.22 | 0 | 18003 |
| `ida/nucleo/estrategia.py` | 0.00 | 0.21 | +0.21 | 0 | 345040 |
| `ida/core/estrategia.py` | 0.20 | 0.00 | -0.20 | 344936 | 0 |
| `ida/nucleo/mundo.py` | 0.00 | 0.18 | +0.18 | 0 | 86841 |
| `ida/s1/reaccionar/estrategias/alimentarse.py` | 0.00 | 0.17 | +0.17 | 0 | 204211 |

### Funciones, por Δ

| Clave | tottime base (s) | tottime nueva (s) | Δ (s) | llamadas base | llamadas nueva |
|---|---|---|---|---|---|
| `<python>:__hash__` | 0.62 | 0.00 | -0.62 | 1746099 | 323 |
| `__hash__` | 0.00 | 0.60 | +0.60 | 0 | 1745788 |
| `reactiva` | 1.93 | 2.41 | +0.48 | 134413 | 143413 |
| `<python>:_path_join` | 0.47 | 0.00 | -0.47 | 90225 | 0 |
| `_path_join` | 0.00 | 0.47 | +0.47 | 0 | 90674 |
| `modificar` | 0.11 | 0.57 | +0.46 | 46602 | 293946 |
| `rasgo` | 2.11 | 2.40 | +0.28 | 3225353 | 3644785 |
| `<python>:<method 'get' of 'dict' objects>` | 4.44 | 4.71 | +0.27 | 22302868 | 23889873 |
| `__eq__` | 0.00 | 0.23 | +0.23 | 0 | 604380 |
| `<python>:__eq__` | 0.23 | 0.00 | -0.23 | 604822 | 498 |
| `distancias` | 0.00 | 0.22 | +0.22 | 0 | 5987 |
| `aprender` | 0.05 | 0.27 | +0.22 | 5999 | 170973 |
| `situacion` | 0.00 | 0.20 | +0.20 | 0 | 6000 |
| `_requisitos` | 0.03 | 0.23 | +0.20 | 442 | 152291 |
| `_aprender_mapa` | 0.19 | 0.00 | -0.19 | 3000 | 0 |
| `_distancias` | 0.19 | 0.00 | -0.19 | 5987 | 0 |
| `_peligro_aprendido` | 0.18 | 0.00 | -0.18 | 3000 | 0 |
| `_anotar` | 0.41 | 0.56 | +0.15 | 320262 | 443934 |
| `<python>:find_spec` | 0.14 | 0.00 | -0.14 | 23437 | 0 |
| `_par` | 0.00 | 0.14 | +0.14 | 0 | 168980 |
| `find_spec` | 0.00 | 0.14 | +0.14 | 0 | 23844 |
| `_deseables` | 0.00 | 0.13 | +0.13 | 0 | 2969 |
| `estimaciones` | 0.00 | 0.13 | +0.13 | 0 | 3000 |
| `ubicacion` | 0.00 | 0.13 | +0.13 | 0 | 106213 |
| `vivir` | 0.26 | 0.39 | +0.12 | 13 | 13 |
| `estimar` | 0.12 | 0.00 | -0.12 | 4925 | 1925 |
| `ejecutar` | 1.44 | 1.53 | +0.08 | 43056 | 46056 |
| `situacion_inventario` | 0.00 | 0.08 | +0.08 | 0 | 5987 |
| `_plasticidad` | 0.00 | 0.08 | +0.08 | 0 | 3000 |
| `_propiedad` | 0.09 | 0.17 | +0.08 | 329376 | 453048 |
| `ir_por_el_mapa` | 1.18 | 1.26 | +0.08 | 18288 | 54864 |
| `<genexpr>` | 2.03 | 2.11 | +0.08 | 7112964 | 7464360 |
| `observar` | 0.25 | 0.18 | -0.07 | 3000 | 3000 |
| `_ordenados` | 0.00 | 0.07 | +0.07 | 0 | 41224 |
| `_guardar_corto_plazo` | 0.00 | 0.06 | +0.06 | 0 | 3000 |
| `_pos` | 0.13 | 0.19 | +0.06 | 77448 | 118672 |
| `__post_init__` | 0.55 | 0.49 | -0.06 | 347618 | 347631 |
| `ev` | 0.20 | 0.26 | +0.06 | 442503 | 593739 |
| `_situacion_inventario` | 0.06 | 0.00 | -0.06 | 5987 | 0 |
| `seccion` | 0.00 | 0.06 | +0.06 | 0 | 197204 |

### Funciones más caras en la nueva

| Clave | tottime base (s) | tottime nueva (s) | Δ (s) | llamadas base | llamadas nueva |
|---|---|---|---|---|---|
| `<python>:<method 'get' of 'dict' objects>` | 4.44 | 4.71 | +0.27 | 22302868 | 23889873 |
| `candidatos` | 3.65 | 3.64 | -0.01 | 920 | 920 |
| `reactiva` | 1.93 | 2.41 | +0.48 | 134413 | 143413 |
| `rasgo` | 2.11 | 2.40 | +0.28 | 3225353 | 3644785 |
| `<genexpr>` | 2.03 | 2.11 | +0.08 | 7112964 | 7464360 |
| `sucesores` | 2.11 | 2.07 | -0.03 | 1349948 | 1349948 |
| `_bfs` | 1.64 | 1.61 | -0.03 | 2441 | 2441 |
| `ejecutar` | 1.44 | 1.53 | +0.08 | 43056 | 46056 |
| `ir_por_el_mapa` | 1.18 | 1.26 | +0.08 | 18288 | 54864 |
| `libre` | 1.02 | 1.01 | -0.01 | 1726591 | 1726591 |
| `pieza` | 0.91 | 0.92 | +0.01 | 301695 | 301695 |
| `clase` | 0.82 | 0.88 | +0.06 | 1775051 | 1896666 |
| `<python>:<built-in method nt.stat>` | 0.82 | 0.83 | +0.01 | 18850 | 19283 |
| `<python>:<built-in method builtins.max>` | 0.84 | 0.83 | -0.01 | 2522718 | 2481533 |
| `acotar` | 0.74 | 0.76 | +0.02 | 1087488 | 1128712 |
| `_resolver` | 0.63 | 0.68 | +0.05 | 81436 | 81436 |
| `_cosas` | 0.68 | 0.67 | -0.01 | 113422 | 113233 |
| `__hash__` | 0.00 | 0.60 | +0.60 | 0 | 1745788 |
| `<python>:<built-in method builtins.sorted>` | 0.57 | 0.60 | +0.03 | 833697 | 919184 |
| `rutas` | 0.57 | 0.57 | +0.00 | 2818 | 2818 |
| `modificar` | 0.11 | 0.57 | +0.46 | 46602 | 293946 |
| `_anotar` | 0.41 | 0.56 | +0.15 | 320262 | 443934 |
| `<python>:<built-in method builtins.round>` | 0.52 | 0.53 | +0.00 | 686978 | 686978 |
| `accesos_de` | 0.51 | 0.51 | -0.00 | 124759 | 124759 |
| `__post_init__` | 0.55 | 0.49 | -0.06 | 347618 | 347631 |

