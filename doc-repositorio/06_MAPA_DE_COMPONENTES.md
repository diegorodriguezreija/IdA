# Mapa de Componentes

> **Generado** por `herramientas/mapa_componentes.py --escribir` desde [`componentes.toml`](componentes.toml). No se edita a mano.
> Diseño y decisiones: [`docs/DISENO_COMPONENTES.md`](../docs/DISENO_COMPONENTES.md).

Cada fila es un Componente, una estrategia o una biblioteca de un cuerpo, en el orden del latido. **Destino** es dónde debe vivir; **Hoy**, dónde está en el código (lo comprueba `tests/test_mapa_componentes.py`). Si no coinciden, **Paso** dice qué paso del plan lo lleva a su destino.

**Total:** 74 · **en su destino:** 74 · **pendientes:** 0

**Clase:** general (todos los mundos) · opcional (general, pero solo lo monta quien lo registra) · cuerpo (familia de cuerpos) · mundo (propio de un mundo).

## 2 · Core · Sentir (en bruto)

| Componente | Tipo | Clase | Hoy | Paso | Decisión | Nota |
|---|---|---|---|---|---|---|
| `Interocepcion` | componente | general | ✓ |  | previo |  |
| `Propiocepcion` | componente | general | ✓ |  | previo |  |
| `Ambiente` | componente | general | ✓ |  | previo |  |
| `Exterocepcion` | componente | general | ✓ |  | previo | En bruto: emite con arousal 0; la saliencia la pone Saliencia en la preatención (D5) |

## 3 · Preatención (S1 · Sentir, no paga atención, también dormido)

| Componente | Tipo | Clase | Hoy | Paso | Decisión | Nota |
|---|---|---|---|---|---|---|
| `Saliencia` | componente | general | ✓ |  | D5 | ida/sistemas/saliencia.py; antes dentro de Exterocepcion, que ahora emite con arousal 0 |
| `Amenaza` ✱ | componente | opcional (crafter) | ✓ |  | D5 | ida/sistemas/amenaza.py: aprende y estima el peligro en las piezas Exterocepcion (sustituyó a ida/core/peligro.py y a _peligro_aprendido); se monta en todos con la condición de antes (posiciones y sin peligro del mundo): su activación por registro es A6 |
| `ValoracionCrafter` | componente | mundo: crafter | ✓ |  | D4 | ida/mundos/crafter/s1/sentir/valoracion.py: nutritivo y recurso (cosas), nutritivo y novedad (lugares), con las fórmulas que tenía el adaptador; lleva su memoria de visitas con la cuenta de primitivas del Motor. Recibe del registro de Crafter las clases NUTRITIVO y UTIL del manual |

## 5 · Regulación de la Onda (Core)

| Componente | Tipo | Clase | Hoy | Paso | Decisión | Nota |
|---|---|---|---|---|---|---|
| `Regulacion` | componente | general | ✓ |  | D12 | Reglas instantáneas de la Onda (ida/core/regulacion.py), antes Marcapasos.ritmo; en la fase A se calcula al crear la Onda, tras la preatención es B2 |

## S1 · Sentir

| Componente | Tipo | Clase | Hoy | Paso | Decisión | Nota |
|---|---|---|---|---|---|---|
| `Imagen` | componente | general | ✓ |  | previo |  |

## S1 · Interpretar

| Componente | Tipo | Clase | Hoy | Paso | Decisión | Nota |
|---|---|---|---|---|---|---|
| `Objeto` | componente | general | ✓ |  | previo |  |
| `Supervivencia` | componente | general | ✓ |  | previo |  |
| `Apetencia` ✱ | componente | opcional (crafter) | ✓ |  | D15 | Aliestesia; sustituye a Perfil.aliestesia, que desapareció en A6a |
| `Recinto` | componente | mundo: crafter | ✓ |  | D16 | ida/mundos/crafter/s1/interpretar/recinto.py: emite la afordancia de protección. Lo registra Crafter (A6a, A6b) |
| `MapaLocal` ✱ | componente | cuerpo: cuadricula | ✓ |  | D10 | ida/cuerpos/cuadricula/mapa_local.py: mapa métrico, transformaciones y cierres (salió de _aprender_mapa); datos en Memoria (casillas, cierres, yo_previo) hasta A7. Las visitas (novedad) no son suyas: las lleva ValoracionCrafter |

## S1 · Reaccionar

| Componente | Tipo | Clase | Hoy | Paso | Decisión | Nota |
|---|---|---|---|---|---|---|
| `Reflejo` | componente | general | ✓ |  | previo |  |
| `Impulso` | componente | general | ✓ |  | previo |  |
| `Feedback` | componente | general | ✓ |  | previo |  |
| `Estrategia` | componente | general | ✓ |  | previo |  |
| `Peticion` | componente | general | ✓ |  | D11 |  |
| `Huir` | estrategia | general | ✓ |  | previo |  |
| `Defenderse` | estrategia | general | ✓ |  | previo |  |
| `Sobresalto` | estrategia | general | ✓ |  | previo |  |
| `QuietoOHuir` | estrategia | general | ✓ |  | previo |  |
| `Alimentarse` | estrategia | general | ✓ |  | previo | Por necesidad si Apetencia está registrada (ctx.registrado, D15); Perfil.aliestesia ya no existe (A6a) |
| `SeguirEnMovimiento` | estrategia | general | ✓ |  | previo |  |
| `Afrontar` | estrategia | opcional (crafter) | ✓ |  | D15 |  |
| `Proteger` | estrategia | opcional (crafter) | ✓ |  | D16 |  |
| `SalirDelRecinto` | estrategia | mundo: crafter | ✓ |  | D16 | ida/mundos/crafter/s1/reaccionar/estrategias/salir_del_recinto.py: la registra Crafter (A6a, A6b) |
| `Defensa` | estrategia | mundo: minimo | ✓ |  | previo | plantar_cara |
| `Defensa` | estrategia | mundo: archivos | ✓ |  | previo | plantar_cara |
| `AlimentarseConPrudencia` | estrategia | mundo: archivos | ✓ |  | previo |  Sustituye a `Alimentarse`. |

## S1 · Actuar

| Componente | Tipo | Clase | Hoy | Paso | Decisión | Nota |
|---|---|---|---|---|---|---|
| `Accion` | componente | general | ✓ |  | previo |  |
| `Anticipacion` | componente | general | ✓ |  | D11 | Copia eferente |

## S2 · Sentir

| Componente | Tipo | Clase | Hoy | Paso | Decisión | Nota |
|---|---|---|---|---|---|---|
| `Patron` | componente | general | ✓ |  | previo |  |
| `Emocion` | componente | general | ✓ |  | previo |  |
| `Recuerdo` | componente | general | ✓ |  | previo |  |

## S2 · Interpretar

| Componente | Tipo | Clase | Hoy | Paso | Decisión | Nota |
|---|---|---|---|---|---|---|
| `Sujeto` | componente | general | ✓ |  | previo |  |
| `Valor` | componente | general | ✓ |  | previo |  |

## S2 · Reaccionar

| Componente | Tipo | Clase | Hoy | Paso | Decisión | Nota |
|---|---|---|---|---|---|---|
| `Exteriorizacion` | componente | general | ✓ |  | previo |  |
| `Impulso` | componente | general | ✓ |  | previo |  |
| `Feedback` | componente | general | ✓ |  | previo |  |
| `Estrategia` | componente | general | ✓ |  | previo |  |
| `Peticion` | componente | general | ✓ |  | D11 |  |
| `Explorar` | estrategia | general | ✓ |  | previo |  |
| `Refugiarse` | estrategia | general | ✓ |  | previo |  |
| `RecordarComida` | estrategia | general | ✓ |  | previo |  |

## S2 · Actuar

| Componente | Tipo | Clase | Hoy | Paso | Decisión | Nota |
|---|---|---|---|---|---|---|
| `Accion` | componente | general | ✓ |  | previo |  |
| `Anticipacion` | componente | general | ✓ |  | D11 | Copia eferente |

## S3 · Sentir

| Componente | Tipo | Clase | Hoy | Paso | Decisión | Nota |
|---|---|---|---|---|---|---|
| `Comunicacion` | componente | general | ✓ |  | previo |  |

## S3 · Interpretar

| Componente | Tipo | Clase | Hoy | Paso | Decisión | Nota |
|---|---|---|---|---|---|---|
| `Agente` | componente | general | ✓ |  | previo |  |
| `Predicado` | componente | general | ✓ |  | previo |  |
| `Proposicion` | componente | general | ✓ |  | previo |  |
| `Sentencia` | componente | general | ✓ |  | previo |  |
| `Logica` | componente | general | ✓ |  | previo |  |
| `Creencia` | componente | general | ✓ |  | previo |  |
| `Requisito` ✱ | componente | general | ✓ |  | D7 | Requisitos, transformaciones y metas; hoy latido.py _aprender, _aprender_mapa y _situacion_inventario. «delante» y «cerca» los da el cuerpo |

## S3 · Reaccionar

| Componente | Tipo | Clase | Hoy | Paso | Decisión | Nota |
|---|---|---|---|---|---|---|
| `Intencion` | componente | general | ✓ |  | previo |  |
| `Impulso` | componente | general | ✓ |  | previo |  |
| `Feedback` | componente | general | ✓ |  | previo |  |
| `Estrategia` | componente | general | ✓ |  | previo |  |
| `Prudencia` | componente | mundo: archivos | ✓ |  | previo |  |
| `EvitarLoPeligroso` | estrategia | general | ✓ |  | previo |  |
| `ComerLoNutritivo` | estrategia | general | ✓ |  | previo |  |
| `CogerLoUtil` | estrategia | general | ✓ |  | previo |  |
| `Estudio` | estrategia | general | ✓ |  | previo |  |
| `PerseguirMetas` | estrategia | general | ✓ |  | previo | General; resuelto en A6b: la búsqueda de material en el mapa es geometría de cuadrícula (ida/cuerpos/cuadricula/mapa.py) y la ofrece el cuerpo (Contexto.cuerpo); sin cuerpo no la hay |
| `BuscarEnOtraCarpeta` | estrategia | mundo: archivos | ✓ |  | previo |  |

## S3 · Actuar

| Componente | Tipo | Clase | Hoy | Paso | Decisión | Nota |
|---|---|---|---|---|---|---|
| `Accion` | componente | general | ✓ |  | previo |  |

## 7 · Core · Actuar

| Componente | Tipo | Clase | Hoy | Paso | Decisión | Nota |
|---|---|---|---|---|---|---|
| `Tribunal` | componente | general | ✓ |  | previo |  |
| `Actuador` | componente | general | ✓ |  | previo | Ejecuta primitivas del mundo (A5, D9) |
| `ModeloDirecto` ✱ | componente | cuerpo: cuadricula | ✓ |  | D10 | ida/cuerpos/cuadricula/modelo_directo.py: qué hace cada acción con el cuerpo (salió de _aprender_mapa); datos en Memoria.cuerpo hasta A7 |

## Bibliotecas de los cuerpos

| Componente | Tipo | Clase | Hoy | Paso | Decisión | Nota |
|---|---|---|---|---|---|---|
| `Geometria` | biblioteca | cuerpo: cuadricula | ✓ |  | D10 | ida/cuerpos/cuadricula/geometria.py: vecinos, distancia, entorno, búsqueda en anchura |
| `BuscadorPosturas` | biblioteca | cuerpo: cuadricula | ✓ |  | D10 | ida/cuerpos/cuadricula/buscador.py: qué secuencia de MOVER deja en A mirando a C |
| `Motor` | biblioteca | cuerpo: cuadricula | ✓ |  | D9 | ida/cuerpos/cuadricula/motor.py: intención → primitivas, con sinergias (máx. 2 en la fase A); juzga el éxito; cuenta las primitivas ejecutadas (copia eferente) |

✱ Tiene plasticidad: aprende en el paso 4 del latido (D6).
