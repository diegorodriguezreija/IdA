# Diseño visual: el latido, el núcleo y cada mundo

> **Generado** por `herramientas/mapa_componentes.py --escribir` desde [`componentes.toml`](componentes.toml). No se edita a mano.
> Tabla completa: [`06_MAPA_DE_COMPONENTES.md`](06_MAPA_DE_COMPONENTES.md) · Decisiones: [`docs/DISENO_COMPONENTES.md`](../docs/DISENO_COMPONENTES.md).

## Cómo leerlo

Cada latido es una **Onda** que recorre ocho pasos, siempre en el mismo orden (D1). La Onda lleva el plazo (**frecuencia**; si se agota, la **guillotina** corta lo que quede), cuántas piezas caben en la atención (**amplitud**) y cuánto arousal se puede dar o cambiar (**potencia**). Cada Componente solo produce y cambia piezas de su tipo.

- **Pasos 1–5 (Core y preatención):** sentir en bruto, anotar lo saliente y lo valorado, aprender del efecto de la acción anterior y fijar la Onda. No pagan atención y corren también dormido.
- **Paso 6 (cognición):** S1 → S2 → S3, uno tras otro sobre la misma Onda. En cada sistema, Sentir → Interpretar → Reaccionar (las estrategias, cada una con su Actuación) → Actuar. Pagan atención y la guillotina puede cortarlos.
- **Pasos 7–8 (Core):** el Tribunal elige una Actuación, el Core ejecuta su primitiva, y el cierre marca qué guardar.

Un mundo no cambia este flujo: solo **registra** su cuerpo y sus Componentes propios, que se añaden a lo general o lo sustituyen en el mismo sitio.

**Leyenda.** Rectángulo: Componente · óvalo: estrategia · doble borde: biblioteca del cuerpo · ✱: aprende (paso 4). Color: gris, general · azul, opcional (general, montado solo por quien lo registra) · verde, del cuerpo · ámbar, propio del mundo · violeta, paso del latido sin Componentes declarados.

## El núcleo (lo que monta cualquier mundo)

```mermaid
flowchart TB
  P1["1 · Onda<br/>copia de la anterior; la anterior pasa a la memoria a corto plazo"]:::paso
  subgraph P2["2 · Core · Sentir (en bruto)"]
    direction TB
    CORESentir_Interocepcion["Interocepcion"]:::general
    CORESentir_Propiocepcion["Propiocepcion"]:::general
    CORESentir_Ambiente["Ambiente"]:::general
    CORESentir_Exterocepcion["Exterocepcion"]:::general
  end
  subgraph P3["3 · Preatención (S1 · Sentir; no paga atención; también dormido)"]
    direction TB
    PREATENCION_Saliencia["Saliencia"]:::general
  end
  P4["4 · Plasticidad: aprende del efecto de la acción anterior<br/>Requisito"]:::paso
  subgraph P5["5 · Regulación de la Onda (Core)"]
    direction TB
    CORERegulacion_Regulacion["Regulacion"]:::general
  end
  subgraph S1["6 · S1 · supervivencia"]
    direction LR
    subgraph S1Sentir["Sentir"]
      direction TB
      S1Sentir_Imagen["Imagen"]:::general
    end
    subgraph S1Interpretar["Interpretar"]
      direction TB
      S1Interpretar_Objeto["Objeto"]:::general
      S1Interpretar_Supervivencia["Supervivencia"]:::general
    end
    subgraph S1Reaccionar["Reaccionar"]
      direction TB
      S1Reaccionar_Reflejo["Reflejo"]:::general
      S1Reaccionar_Impulso["Impulso"]:::general
      S1Reaccionar_Feedback["Feedback"]:::general
      S1Reaccionar_Estrategia["Estrategia"]:::general
      S1Reaccionar_Peticion["Peticion"]:::general
      subgraph S1Reaccionar_est["estrategias"]
        direction TB
        S1Reaccionar_Huir(["Huir"]):::general
        S1Reaccionar_Defenderse(["Defenderse"]):::general
        S1Reaccionar_Sobresalto(["Sobresalto"]):::general
        S1Reaccionar_QuietoOHuir(["QuietoOHuir"]):::general
        S1Reaccionar_Alimentarse(["Alimentarse"]):::general
        S1Reaccionar_SeguirEnMovimiento(["SeguirEnMovimiento"]):::general
      end
    end
    subgraph S1Actuar["Actuar"]
      direction TB
      S1Actuar_Accion["Accion"]:::general
      S1Actuar_Anticipacion["Anticipacion"]:::general
    end
    S1Sentir --> S1Interpretar
    S1Interpretar --> S1Reaccionar
    S1Reaccionar --> S1Actuar
  end
  subgraph S2["6 · S2 · valor"]
    direction LR
    subgraph S2Sentir["Sentir"]
      direction TB
      S2Sentir_Patron["Patron"]:::general
      S2Sentir_Emocion["Emocion"]:::general
      S2Sentir_Recuerdo["Recuerdo"]:::general
    end
    subgraph S2Interpretar["Interpretar"]
      direction TB
      S2Interpretar_Sujeto["Sujeto"]:::general
      S2Interpretar_Valor["Valor"]:::general
    end
    subgraph S2Reaccionar["Reaccionar"]
      direction TB
      S2Reaccionar_Exteriorizacion["Exteriorizacion"]:::general
      S2Reaccionar_Impulso["Impulso"]:::general
      S2Reaccionar_Feedback["Feedback"]:::general
      S2Reaccionar_Estrategia["Estrategia"]:::general
      S2Reaccionar_Peticion["Peticion"]:::general
      subgraph S2Reaccionar_est["estrategias"]
        direction TB
        S2Reaccionar_Explorar(["Explorar"]):::general
        S2Reaccionar_Refugiarse(["Refugiarse"]):::general
        S2Reaccionar_RecordarComida(["RecordarComida"]):::general
      end
    end
    subgraph S2Actuar["Actuar"]
      direction TB
      S2Actuar_Accion["Accion"]:::general
      S2Actuar_Anticipacion["Anticipacion"]:::general
    end
    S2Sentir --> S2Interpretar
    S2Interpretar --> S2Reaccionar
    S2Reaccionar --> S2Actuar
  end
  subgraph S3["6 · S3 · verdad"]
    direction LR
    subgraph S3Sentir["Sentir"]
      direction TB
      S3Sentir_Comunicacion["Comunicacion"]:::general
    end
    subgraph S3Interpretar["Interpretar"]
      direction TB
      S3Interpretar_Agente["Agente"]:::general
      S3Interpretar_Predicado["Predicado"]:::general
      S3Interpretar_Proposicion["Proposicion"]:::general
      S3Interpretar_Sentencia["Sentencia"]:::general
      S3Interpretar_Logica["Logica"]:::general
      S3Interpretar_Creencia["Creencia"]:::general
      S3Interpretar_Requisito["Requisito ✱"]:::general
    end
    subgraph S3Reaccionar["Reaccionar"]
      direction TB
      S3Reaccionar_Intencion["Intencion"]:::general
      S3Reaccionar_Impulso["Impulso"]:::general
      S3Reaccionar_Feedback["Feedback"]:::general
      S3Reaccionar_Estrategia["Estrategia"]:::general
      subgraph S3Reaccionar_est["estrategias"]
        direction TB
        S3Reaccionar_EvitarLoPeligroso(["EvitarLoPeligroso"]):::general
        S3Reaccionar_ComerLoNutritivo(["ComerLoNutritivo"]):::general
        S3Reaccionar_CogerLoUtil(["CogerLoUtil"]):::general
        S3Reaccionar_Estudio(["Estudio"]):::general
        S3Reaccionar_PerseguirMetas(["PerseguirMetas"]):::general
      end
    end
    subgraph S3Actuar["Actuar"]
      direction TB
      S3Actuar_Accion["Accion"]:::general
    end
    S3Sentir --> S3Interpretar
    S3Interpretar --> S3Reaccionar
    S3Reaccionar --> S3Actuar
  end
  subgraph P7["7 · Core · Actuar"]
    direction TB
    COREActuar_Tribunal["Tribunal"]:::general
    COREActuar_Actuador["Actuador"]:::general
  end
  P8["8 · Cierre: marcar para guardar, episodios, indicadores<br/>→ siguiente latido (paso 1)"]:::paso
  P1 -->|"la Onda"| P2
  P2 -->|"piezas en bruto (arousal 0)"| P3
  P3 -->|"piezas anotadas: saliencia y valoración"| P4
  P4 --> P5
  P5 -->|"frecuencia · amplitud · potencia"| S1
  S1 -->|"la misma Onda, con lo que S1 añadió"| S2
  S2 --> S3
  S3 -->|"Actuaciones (guillotina si se agota el plazo)"| P7
  P7 -->|"una primitiva ejecutada"| P8
  classDef general fill:#f1f5f9,stroke:#64748b,color:#0f172a
  classDef opcional fill:#dbeafe,stroke:#2563eb,color:#0f172a
  classDef cuerpo fill:#dcfce7,stroke:#16a34a,color:#0f172a
  classDef mundo fill:#fef3c7,stroke:#d97706,color:#0f172a
  classDef paso fill:#ede9fe,stroke:#7c3aed,color:#0f172a
```

## Mínimo

Añade al núcleo:

- `Defensa` (estrategia, mundo: minimo) en S1 · Reaccionar

```mermaid
flowchart TB
  P1["1 · Onda<br/>copia de la anterior; la anterior pasa a la memoria a corto plazo"]:::paso
  subgraph P2["2 · Core · Sentir (en bruto)"]
    direction TB
    CORESentir_Interocepcion["Interocepcion"]:::general
    CORESentir_Propiocepcion["Propiocepcion"]:::general
    CORESentir_Ambiente["Ambiente"]:::general
    CORESentir_Exterocepcion["Exterocepcion"]:::general
  end
  subgraph P3["3 · Preatención (S1 · Sentir; no paga atención; también dormido)"]
    direction TB
    PREATENCION_Saliencia["Saliencia"]:::general
  end
  P4["4 · Plasticidad: aprende del efecto de la acción anterior<br/>Requisito"]:::paso
  subgraph P5["5 · Regulación de la Onda (Core)"]
    direction TB
    CORERegulacion_Regulacion["Regulacion"]:::general
  end
  subgraph S1["6 · S1 · supervivencia"]
    direction LR
    subgraph S1Sentir["Sentir"]
      direction TB
      S1Sentir_Imagen["Imagen"]:::general
    end
    subgraph S1Interpretar["Interpretar"]
      direction TB
      S1Interpretar_Objeto["Objeto"]:::general
      S1Interpretar_Supervivencia["Supervivencia"]:::general
    end
    subgraph S1Reaccionar["Reaccionar"]
      direction TB
      S1Reaccionar_Reflejo["Reflejo"]:::general
      S1Reaccionar_Impulso["Impulso"]:::general
      S1Reaccionar_Feedback["Feedback"]:::general
      S1Reaccionar_Estrategia["Estrategia"]:::general
      S1Reaccionar_Peticion["Peticion"]:::general
      subgraph S1Reaccionar_est["estrategias"]
        direction TB
        S1Reaccionar_Huir(["Huir"]):::general
        S1Reaccionar_Defenderse(["Defenderse"]):::general
        S1Reaccionar_Sobresalto(["Sobresalto"]):::general
        S1Reaccionar_QuietoOHuir(["QuietoOHuir"]):::general
        S1Reaccionar_Alimentarse(["Alimentarse"]):::general
        S1Reaccionar_SeguirEnMovimiento(["SeguirEnMovimiento"]):::general
        S1Reaccionar_Defensa(["Defensa"]):::mundo
      end
    end
    subgraph S1Actuar["Actuar"]
      direction TB
      S1Actuar_Accion["Accion"]:::general
      S1Actuar_Anticipacion["Anticipacion"]:::general
    end
    S1Sentir --> S1Interpretar
    S1Interpretar --> S1Reaccionar
    S1Reaccionar --> S1Actuar
  end
  subgraph S2["6 · S2 · valor"]
    direction LR
    subgraph S2Sentir["Sentir"]
      direction TB
      S2Sentir_Patron["Patron"]:::general
      S2Sentir_Emocion["Emocion"]:::general
      S2Sentir_Recuerdo["Recuerdo"]:::general
    end
    subgraph S2Interpretar["Interpretar"]
      direction TB
      S2Interpretar_Sujeto["Sujeto"]:::general
      S2Interpretar_Valor["Valor"]:::general
    end
    subgraph S2Reaccionar["Reaccionar"]
      direction TB
      S2Reaccionar_Exteriorizacion["Exteriorizacion"]:::general
      S2Reaccionar_Impulso["Impulso"]:::general
      S2Reaccionar_Feedback["Feedback"]:::general
      S2Reaccionar_Estrategia["Estrategia"]:::general
      S2Reaccionar_Peticion["Peticion"]:::general
      subgraph S2Reaccionar_est["estrategias"]
        direction TB
        S2Reaccionar_Explorar(["Explorar"]):::general
        S2Reaccionar_Refugiarse(["Refugiarse"]):::general
        S2Reaccionar_RecordarComida(["RecordarComida"]):::general
      end
    end
    subgraph S2Actuar["Actuar"]
      direction TB
      S2Actuar_Accion["Accion"]:::general
      S2Actuar_Anticipacion["Anticipacion"]:::general
    end
    S2Sentir --> S2Interpretar
    S2Interpretar --> S2Reaccionar
    S2Reaccionar --> S2Actuar
  end
  subgraph S3["6 · S3 · verdad"]
    direction LR
    subgraph S3Sentir["Sentir"]
      direction TB
      S3Sentir_Comunicacion["Comunicacion"]:::general
    end
    subgraph S3Interpretar["Interpretar"]
      direction TB
      S3Interpretar_Agente["Agente"]:::general
      S3Interpretar_Predicado["Predicado"]:::general
      S3Interpretar_Proposicion["Proposicion"]:::general
      S3Interpretar_Sentencia["Sentencia"]:::general
      S3Interpretar_Logica["Logica"]:::general
      S3Interpretar_Creencia["Creencia"]:::general
      S3Interpretar_Requisito["Requisito ✱"]:::general
    end
    subgraph S3Reaccionar["Reaccionar"]
      direction TB
      S3Reaccionar_Intencion["Intencion"]:::general
      S3Reaccionar_Impulso["Impulso"]:::general
      S3Reaccionar_Feedback["Feedback"]:::general
      S3Reaccionar_Estrategia["Estrategia"]:::general
      subgraph S3Reaccionar_est["estrategias"]
        direction TB
        S3Reaccionar_EvitarLoPeligroso(["EvitarLoPeligroso"]):::general
        S3Reaccionar_ComerLoNutritivo(["ComerLoNutritivo"]):::general
        S3Reaccionar_CogerLoUtil(["CogerLoUtil"]):::general
        S3Reaccionar_Estudio(["Estudio"]):::general
        S3Reaccionar_PerseguirMetas(["PerseguirMetas"]):::general
      end
    end
    subgraph S3Actuar["Actuar"]
      direction TB
      S3Actuar_Accion["Accion"]:::general
    end
    S3Sentir --> S3Interpretar
    S3Interpretar --> S3Reaccionar
    S3Reaccionar --> S3Actuar
  end
  subgraph P7["7 · Core · Actuar"]
    direction TB
    COREActuar_Tribunal["Tribunal"]:::general
    COREActuar_Actuador["Actuador"]:::general
  end
  P8["8 · Cierre: marcar para guardar, episodios, indicadores<br/>→ siguiente latido (paso 1)"]:::paso
  P1 -->|"la Onda"| P2
  P2 -->|"piezas en bruto (arousal 0)"| P3
  P3 -->|"piezas anotadas: saliencia y valoración"| P4
  P4 --> P5
  P5 -->|"frecuencia · amplitud · potencia"| S1
  S1 -->|"la misma Onda, con lo que S1 añadió"| S2
  S2 --> S3
  S3 -->|"Actuaciones (guillotina si se agota el plazo)"| P7
  P7 -->|"una primitiva ejecutada"| P8
  classDef general fill:#f1f5f9,stroke:#64748b,color:#0f172a
  classDef opcional fill:#dbeafe,stroke:#2563eb,color:#0f172a
  classDef cuerpo fill:#dcfce7,stroke:#16a34a,color:#0f172a
  classDef mundo fill:#fef3c7,stroke:#d97706,color:#0f172a
  classDef paso fill:#ede9fe,stroke:#7c3aed,color:#0f172a
```

## Archivos

Añade al núcleo:

- `Defensa` (estrategia, mundo: archivos) en S1 · Reaccionar
- `AlimentarseConPrudencia` (estrategia, mundo: archivos) en S1 · Reaccionar, sustituye a `Alimentarse`
- `Prudencia` (componente, mundo: archivos) en S3 · Reaccionar
- `BuscarEnOtraCarpeta` (estrategia, mundo: archivos) en S3 · Reaccionar

```mermaid
flowchart TB
  P1["1 · Onda<br/>copia de la anterior; la anterior pasa a la memoria a corto plazo"]:::paso
  subgraph P2["2 · Core · Sentir (en bruto)"]
    direction TB
    CORESentir_Interocepcion["Interocepcion"]:::general
    CORESentir_Propiocepcion["Propiocepcion"]:::general
    CORESentir_Ambiente["Ambiente"]:::general
    CORESentir_Exterocepcion["Exterocepcion"]:::general
  end
  subgraph P3["3 · Preatención (S1 · Sentir; no paga atención; también dormido)"]
    direction TB
    PREATENCION_Saliencia["Saliencia"]:::general
  end
  P4["4 · Plasticidad: aprende del efecto de la acción anterior<br/>Requisito"]:::paso
  subgraph P5["5 · Regulación de la Onda (Core)"]
    direction TB
    CORERegulacion_Regulacion["Regulacion"]:::general
  end
  subgraph S1["6 · S1 · supervivencia"]
    direction LR
    subgraph S1Sentir["Sentir"]
      direction TB
      S1Sentir_Imagen["Imagen"]:::general
    end
    subgraph S1Interpretar["Interpretar"]
      direction TB
      S1Interpretar_Objeto["Objeto"]:::general
      S1Interpretar_Supervivencia["Supervivencia"]:::general
    end
    subgraph S1Reaccionar["Reaccionar"]
      direction TB
      S1Reaccionar_Reflejo["Reflejo"]:::general
      S1Reaccionar_Impulso["Impulso"]:::general
      S1Reaccionar_Feedback["Feedback"]:::general
      S1Reaccionar_Estrategia["Estrategia"]:::general
      S1Reaccionar_Peticion["Peticion"]:::general
      subgraph S1Reaccionar_est["estrategias"]
        direction TB
        S1Reaccionar_Huir(["Huir"]):::general
        S1Reaccionar_Defenderse(["Defenderse"]):::general
        S1Reaccionar_Sobresalto(["Sobresalto"]):::general
        S1Reaccionar_QuietoOHuir(["QuietoOHuir"]):::general
        S1Reaccionar_SeguirEnMovimiento(["SeguirEnMovimiento"]):::general
        S1Reaccionar_Defensa(["Defensa"]):::mundo
        S1Reaccionar_AlimentarseConPrudencia(["AlimentarseConPrudencia"]):::mundo
      end
    end
    subgraph S1Actuar["Actuar"]
      direction TB
      S1Actuar_Accion["Accion"]:::general
      S1Actuar_Anticipacion["Anticipacion"]:::general
    end
    S1Sentir --> S1Interpretar
    S1Interpretar --> S1Reaccionar
    S1Reaccionar --> S1Actuar
  end
  subgraph S2["6 · S2 · valor"]
    direction LR
    subgraph S2Sentir["Sentir"]
      direction TB
      S2Sentir_Patron["Patron"]:::general
      S2Sentir_Emocion["Emocion"]:::general
      S2Sentir_Recuerdo["Recuerdo"]:::general
    end
    subgraph S2Interpretar["Interpretar"]
      direction TB
      S2Interpretar_Sujeto["Sujeto"]:::general
      S2Interpretar_Valor["Valor"]:::general
    end
    subgraph S2Reaccionar["Reaccionar"]
      direction TB
      S2Reaccionar_Exteriorizacion["Exteriorizacion"]:::general
      S2Reaccionar_Impulso["Impulso"]:::general
      S2Reaccionar_Feedback["Feedback"]:::general
      S2Reaccionar_Estrategia["Estrategia"]:::general
      S2Reaccionar_Peticion["Peticion"]:::general
      subgraph S2Reaccionar_est["estrategias"]
        direction TB
        S2Reaccionar_Explorar(["Explorar"]):::general
        S2Reaccionar_Refugiarse(["Refugiarse"]):::general
        S2Reaccionar_RecordarComida(["RecordarComida"]):::general
      end
    end
    subgraph S2Actuar["Actuar"]
      direction TB
      S2Actuar_Accion["Accion"]:::general
      S2Actuar_Anticipacion["Anticipacion"]:::general
    end
    S2Sentir --> S2Interpretar
    S2Interpretar --> S2Reaccionar
    S2Reaccionar --> S2Actuar
  end
  subgraph S3["6 · S3 · verdad"]
    direction LR
    subgraph S3Sentir["Sentir"]
      direction TB
      S3Sentir_Comunicacion["Comunicacion"]:::general
    end
    subgraph S3Interpretar["Interpretar"]
      direction TB
      S3Interpretar_Agente["Agente"]:::general
      S3Interpretar_Predicado["Predicado"]:::general
      S3Interpretar_Proposicion["Proposicion"]:::general
      S3Interpretar_Sentencia["Sentencia"]:::general
      S3Interpretar_Logica["Logica"]:::general
      S3Interpretar_Creencia["Creencia"]:::general
      S3Interpretar_Requisito["Requisito ✱"]:::general
    end
    subgraph S3Reaccionar["Reaccionar"]
      direction TB
      S3Reaccionar_Intencion["Intencion"]:::general
      S3Reaccionar_Impulso["Impulso"]:::general
      S3Reaccionar_Feedback["Feedback"]:::general
      S3Reaccionar_Estrategia["Estrategia"]:::general
      S3Reaccionar_Prudencia["Prudencia"]:::mundo
      subgraph S3Reaccionar_est["estrategias"]
        direction TB
        S3Reaccionar_EvitarLoPeligroso(["EvitarLoPeligroso"]):::general
        S3Reaccionar_ComerLoNutritivo(["ComerLoNutritivo"]):::general
        S3Reaccionar_CogerLoUtil(["CogerLoUtil"]):::general
        S3Reaccionar_Estudio(["Estudio"]):::general
        S3Reaccionar_PerseguirMetas(["PerseguirMetas"]):::general
        S3Reaccionar_BuscarEnOtraCarpeta(["BuscarEnOtraCarpeta"]):::mundo
      end
    end
    subgraph S3Actuar["Actuar"]
      direction TB
      S3Actuar_Accion["Accion"]:::general
    end
    S3Sentir --> S3Interpretar
    S3Interpretar --> S3Reaccionar
    S3Reaccionar --> S3Actuar
  end
  subgraph P7["7 · Core · Actuar"]
    direction TB
    COREActuar_Tribunal["Tribunal"]:::general
    COREActuar_Actuador["Actuador"]:::general
  end
  P8["8 · Cierre: marcar para guardar, episodios, indicadores<br/>→ siguiente latido (paso 1)"]:::paso
  P1 -->|"la Onda"| P2
  P2 -->|"piezas en bruto (arousal 0)"| P3
  P3 -->|"piezas anotadas: saliencia y valoración"| P4
  P4 --> P5
  P5 -->|"frecuencia · amplitud · potencia"| S1
  S1 -->|"la misma Onda, con lo que S1 añadió"| S2
  S2 --> S3
  S3 -->|"Actuaciones (guillotina si se agota el plazo)"| P7
  P7 -->|"una primitiva ejecutada"| P8
  classDef general fill:#f1f5f9,stroke:#64748b,color:#0f172a
  classDef opcional fill:#dbeafe,stroke:#2563eb,color:#0f172a
  classDef cuerpo fill:#dcfce7,stroke:#16a34a,color:#0f172a
  classDef mundo fill:#fef3c7,stroke:#d97706,color:#0f172a
  classDef paso fill:#ede9fe,stroke:#7c3aed,color:#0f172a
```

## Snake

Monta solo el núcleo: el diagrama es el de arriba.

## Ajedrez

Monta solo el núcleo: el diagrama es el de arriba.

## Crafter

Añade al núcleo:

- `ModeloDirecto` (componente, cuerpo: cuadricula) en 7 · Core · Actuar
- `Amenaza` (componente, opcional (crafter)) en 3 · Preatención (S1 · Sentir, no paga atención, también dormido)
- `ValoracionCrafter` (componente, mundo: crafter) en 3 · Preatención (S1 · Sentir, no paga atención, también dormido)
- `Apetencia` (componente, opcional (crafter)) en S1 · Interpretar
- `Recinto` (componente, mundo: crafter) en S1 · Interpretar
- `MapaLocal` (componente, cuerpo: cuadricula) en S1 · Interpretar
- `Afrontar` (estrategia, opcional (crafter)) en S1 · Reaccionar
- `Proteger` (estrategia, opcional (crafter)) en S1 · Reaccionar
- `SalirDelRecinto` (estrategia, mundo: crafter) en S1 · Reaccionar
- `Geometria` (biblioteca, cuerpo: cuadricula) en Bibliotecas de los cuerpos
- `BuscadorPosturas` (biblioteca, cuerpo: cuadricula) en Bibliotecas de los cuerpos
- `Motor` (biblioteca, cuerpo: cuadricula) en Bibliotecas de los cuerpos

```mermaid
flowchart TB
  P1["1 · Onda<br/>copia de la anterior; la anterior pasa a la memoria a corto plazo"]:::paso
  subgraph P2["2 · Core · Sentir (en bruto)"]
    direction TB
    CORESentir_Interocepcion["Interocepcion"]:::general
    CORESentir_Propiocepcion["Propiocepcion"]:::general
    CORESentir_Ambiente["Ambiente"]:::general
    CORESentir_Exterocepcion["Exterocepcion"]:::general
  end
  subgraph P3["3 · Preatención (S1 · Sentir; no paga atención; también dormido)"]
    direction TB
    PREATENCION_Saliencia["Saliencia"]:::general
    PREATENCION_Amenaza["Amenaza ✱"]:::opcional
    PREATENCION_ValoracionCrafter["ValoracionCrafter"]:::mundo
  end
  P4["4 · Plasticidad: aprende del efecto de la acción anterior<br/>ModeloDirecto · Amenaza · Apetencia · MapaLocal · Requisito"]:::paso
  subgraph P5["5 · Regulación de la Onda (Core)"]
    direction TB
    CORERegulacion_Regulacion["Regulacion"]:::general
  end
  subgraph S1["6 · S1 · supervivencia"]
    direction LR
    subgraph S1Sentir["Sentir"]
      direction TB
      S1Sentir_Imagen["Imagen"]:::general
    end
    subgraph S1Interpretar["Interpretar"]
      direction TB
      S1Interpretar_Objeto["Objeto"]:::general
      S1Interpretar_Supervivencia["Supervivencia"]:::general
      S1Interpretar_Apetencia["Apetencia ✱"]:::opcional
      S1Interpretar_Recinto["Recinto"]:::mundo
      S1Interpretar_MapaLocal["MapaLocal ✱"]:::cuerpo
    end
    subgraph S1Reaccionar["Reaccionar"]
      direction TB
      S1Reaccionar_Reflejo["Reflejo"]:::general
      S1Reaccionar_Impulso["Impulso"]:::general
      S1Reaccionar_Feedback["Feedback"]:::general
      S1Reaccionar_Estrategia["Estrategia"]:::general
      S1Reaccionar_Peticion["Peticion"]:::general
      subgraph S1Reaccionar_est["estrategias"]
        direction TB
        S1Reaccionar_Huir(["Huir"]):::general
        S1Reaccionar_Defenderse(["Defenderse"]):::general
        S1Reaccionar_Sobresalto(["Sobresalto"]):::general
        S1Reaccionar_QuietoOHuir(["QuietoOHuir"]):::general
        S1Reaccionar_Alimentarse(["Alimentarse"]):::general
        S1Reaccionar_SeguirEnMovimiento(["SeguirEnMovimiento"]):::general
        S1Reaccionar_Afrontar(["Afrontar"]):::opcional
        S1Reaccionar_Proteger(["Proteger"]):::opcional
        S1Reaccionar_SalirDelRecinto(["SalirDelRecinto"]):::mundo
      end
    end
    subgraph S1Actuar["Actuar"]
      direction TB
      S1Actuar_Accion["Accion"]:::general
      S1Actuar_Anticipacion["Anticipacion"]:::general
    end
    S1Sentir --> S1Interpretar
    S1Interpretar --> S1Reaccionar
    S1Reaccionar --> S1Actuar
  end
  subgraph S2["6 · S2 · valor"]
    direction LR
    subgraph S2Sentir["Sentir"]
      direction TB
      S2Sentir_Patron["Patron"]:::general
      S2Sentir_Emocion["Emocion"]:::general
      S2Sentir_Recuerdo["Recuerdo"]:::general
    end
    subgraph S2Interpretar["Interpretar"]
      direction TB
      S2Interpretar_Sujeto["Sujeto"]:::general
      S2Interpretar_Valor["Valor"]:::general
    end
    subgraph S2Reaccionar["Reaccionar"]
      direction TB
      S2Reaccionar_Exteriorizacion["Exteriorizacion"]:::general
      S2Reaccionar_Impulso["Impulso"]:::general
      S2Reaccionar_Feedback["Feedback"]:::general
      S2Reaccionar_Estrategia["Estrategia"]:::general
      S2Reaccionar_Peticion["Peticion"]:::general
      subgraph S2Reaccionar_est["estrategias"]
        direction TB
        S2Reaccionar_Explorar(["Explorar"]):::general
        S2Reaccionar_Refugiarse(["Refugiarse"]):::general
        S2Reaccionar_RecordarComida(["RecordarComida"]):::general
      end
    end
    subgraph S2Actuar["Actuar"]
      direction TB
      S2Actuar_Accion["Accion"]:::general
      S2Actuar_Anticipacion["Anticipacion"]:::general
    end
    S2Sentir --> S2Interpretar
    S2Interpretar --> S2Reaccionar
    S2Reaccionar --> S2Actuar
  end
  subgraph S3["6 · S3 · verdad"]
    direction LR
    subgraph S3Sentir["Sentir"]
      direction TB
      S3Sentir_Comunicacion["Comunicacion"]:::general
    end
    subgraph S3Interpretar["Interpretar"]
      direction TB
      S3Interpretar_Agente["Agente"]:::general
      S3Interpretar_Predicado["Predicado"]:::general
      S3Interpretar_Proposicion["Proposicion"]:::general
      S3Interpretar_Sentencia["Sentencia"]:::general
      S3Interpretar_Logica["Logica"]:::general
      S3Interpretar_Creencia["Creencia"]:::general
      S3Interpretar_Requisito["Requisito ✱"]:::general
    end
    subgraph S3Reaccionar["Reaccionar"]
      direction TB
      S3Reaccionar_Intencion["Intencion"]:::general
      S3Reaccionar_Impulso["Impulso"]:::general
      S3Reaccionar_Feedback["Feedback"]:::general
      S3Reaccionar_Estrategia["Estrategia"]:::general
      subgraph S3Reaccionar_est["estrategias"]
        direction TB
        S3Reaccionar_EvitarLoPeligroso(["EvitarLoPeligroso"]):::general
        S3Reaccionar_ComerLoNutritivo(["ComerLoNutritivo"]):::general
        S3Reaccionar_CogerLoUtil(["CogerLoUtil"]):::general
        S3Reaccionar_Estudio(["Estudio"]):::general
        S3Reaccionar_PerseguirMetas(["PerseguirMetas"]):::general
      end
    end
    subgraph S3Actuar["Actuar"]
      direction TB
      S3Actuar_Accion["Accion"]:::general
    end
    S3Sentir --> S3Interpretar
    S3Interpretar --> S3Reaccionar
    S3Reaccionar --> S3Actuar
  end
  subgraph P7["7 · Core · Actuar"]
    direction TB
    COREActuar_Tribunal["Tribunal"]:::general
    COREActuar_Actuador["Actuador"]:::general
    COREActuar_ModeloDirecto["ModeloDirecto ✱"]:::cuerpo
  end
  P8["8 · Cierre: marcar para guardar, episodios, indicadores<br/>→ siguiente latido (paso 1)"]:::paso
  P1 -->|"la Onda"| P2
  P2 -->|"piezas en bruto (arousal 0)"| P3
  P3 -->|"piezas anotadas: saliencia y valoración"| P4
  P4 --> P5
  P5 -->|"frecuencia · amplitud · potencia"| S1
  S1 -->|"la misma Onda, con lo que S1 añadió"| S2
  S2 --> S3
  S3 -->|"Actuaciones (guillotina si se agota el plazo)"| P7
  P7 -->|"una primitiva ejecutada"| P8
  subgraph CU["Cuerpo · cuadricula: bibliotecas que usan ModeloDirecto y MapaLocal"]
    direction TB
    cuerpo_Geometria[["Geometria"]]:::cuerpo
    cuerpo_BuscadorPosturas[["BuscadorPosturas"]]:::cuerpo
    cuerpo_Motor[["Motor"]]:::cuerpo
  end
  P8 ~~~ CU
  classDef general fill:#f1f5f9,stroke:#64748b,color:#0f172a
  classDef opcional fill:#dbeafe,stroke:#2563eb,color:#0f172a
  classDef cuerpo fill:#dcfce7,stroke:#16a34a,color:#0f172a
  classDef mundo fill:#fef3c7,stroke:#d97706,color:#0f172a
  classDef paso fill:#ede9fe,stroke:#7c3aed,color:#0f172a
```
