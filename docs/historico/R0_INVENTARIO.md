# R0: Inventario inicial de la reorganización por Componentes

> Este documento contiene el inventario mecánico previo a las transformaciones de la reorganización.
> Todas las entradas provienen directamente de la ejecución de comandos sobre el árbol en `reorg/componentes`.

## A. Añadido por la fase de generalización

**Comando:** `git diff crafter-procedimental-v1..eaeadaa -- ida/core ida/sistemas`

| fichero:línea | tipo | nombre | línea literal |
|---|---|---|---|
| `ida/core/estrategia.py:91` | función | `pedir` | `def pedir(self, ctx: Any, estrategia: Pieza) -> List[Dict[str, Any]]:` |
| `ida/core/latido.py:243` | función | `_peligro_aprendido` | `def _peligro_aprendido(self, ctx: Contexto) -> None:` |
| `ida/core/latido.py:275` | función | `_aprender_satisface` | `def _aprender_satisface(self, ctx: Contexto, c: Dict[str, Any]) -> None:` |
| `ida/core/latido.py:286` | función | `_aprender_mapa` | `def _aprender_mapa(self, ctx: Contexto, c: Optional[Dict[str, Any]]) -> None:` |
| `ida/core/latido.py:350` | función | `_situacion_inventario` | `def _situacion_inventario(ctx: Contexto) -> Optional[Tuple[Dict[str, float], Set[str], Optional[str], Dict[str, Desplazamiento]]]:` |
| `ida/core/latido.py:362` | función | `_distancias` | `def _distancias(obs: Any) -> Dict[str, Desplazamiento]:` |
| `ida/core/memoria.py:195` | constante | `RADIO_PRUEBA` | `RADIO_PRUEBA = 2   # paso 5: hasta esta distancia se prueba una acción con requisito de cercanía antes de caminar` |
| `ida/core/memoria.py:199` | función | `desplazamiento` | `def desplazamiento(dx: int, dy: int) -> Desplazamiento:` |
| `ida/core/memoria.py:205` | constante | `DIRECCIONES` | `DIRECCIONES: Tuple[Pos, ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))` |
| `ida/core/memoria.py:208` | función | `pos_de` | `def pos_de(texto: Any) -> Optional[Pos]:` |
| `ida/core/memoria.py:217` | clase | `Requisito` | `class Requisito:` |
| `ida/core/memoria.py:243` | función | `cerca_basta` | `def cerca_basta(self, clase: str, desp: Desplazamiento) -> bool:` |
| `ida/core/memoria.py:254` | función | `tasa` | `def tasa(self) -> float:` |
| `ida/core/memoria.py:259` | función | `cumple_inventario` | `def cumple_inventario(self, inventario: Dict[str, float]) -> bool:` |
| `ida/core/memoria.py:262` | función | `cumple` | `def cumple(self, inventario: Dict[str, float], cerca: Set[str]) -> bool:` |
| `ida/core/memoria.py:267` | función | `a_dict` | `def a_dict(self) -> Dict[str, Any]:` |
| `ida/core/memoria.py:275` | clase | `Meta` | `class Meta:` |
| `ida/core/memoria.py:285` | clase | `Satisface` | `class Satisface:` |
| `ida/core/memoria.py:309` | constante | `PREVIO` | `PREVIO = 3.0   # peso (en comidas) del previo que no viene del manual` |
| `ida/core/memoria.py:311` | función | `contingencia` | `def contingencia(self) -> float:` |
| `ida/core/memoria.py:315` | función | `estimacion` | `def estimacion(self, previo: float, peso: float) -> float:` |
| `ida/core/memoria.py:321` | función | `fuente` | `def fuente(self) -> str:` |
| `ida/core/memoria.py:983` | constante | `CONFIANZA_MANUAL` | `CONFIANZA_MANUAL = 0.8      # c_aut de lo que declara el manual (y confianza inicial de sus requisitos)` |
| `ida/core/memoria.py:984` | constante | `PESO_MANUAL` | `PESO_MANUAL = 1.0           # w_aut del manual: pesa como una experiencia propia` |
| `ida/core/memoria.py:985` | constante | `PASO_CONFIANZA_REQUISITO` | `PASO_CONFIANZA_REQUISITO = 0.1` |
| `ida/core/memoria.py:986` | constante | `MAX_INTENTOS` | `MAX_INTENTOS = 50           # intentos fallidos recordados por (verbo, objetivo); se olvidan los más antiguos` |
| `ida/core/memoria.py:987` | constante | `FALLOS_BLOQUEO` | `FALLOS_BLOQUEO = 3          # paso 5: fallos seguidos sin ningún éxito que bloquean una acción` |
| `ida/core/memoria.py:989` | función | `aplicar_manual` | `def aplicar_manual(self, manual: Dict[str, Any]) -> int:` |
| `ida/core/memoria.py:1035` | función | `satisfaccion` | `def satisfaccion(self, clase: str, previos: Optional[Dict[str, float]] = None) -> Optional[Dict[str, float]]:` |
| `ida/core/memoria.py:1057` | función | `estimacion_satisface` | `def estimacion_satisface(self, clase: str, necesidad: str, previos: Optional[Dict[str, float]] = None) -> float:` |
| `ida/core/memoria.py:1060` | función | `aprender_satisface` | `def aprender_satisface(self, clase: str, subidas: Dict[str, bool]) -> None:` |
| `ida/core/memoria.py:1070` | constante | `VENTANA_BASE` | `VENTANA_BASE = 10   # latidos de la media móvil de la línea base (media exacta mientras haya menos): lo reciente` |
| `ida/core/memoria.py:1072` | función | `actualizar_linea_base` | `def actualizar_linea_base(self, subidas: Dict[str, bool]) -> None:` |
| `ida/core/memoria.py:1082` | función | `_objetos` | `def _objetos(self, inventario: Dict[str, float]) -> Dict[str, float]:` |
| `ida/core/memoria.py:1089` | función | `transitable` | `def transitable(self, clase: Optional[str]) -> Optional[bool]:` |
| `ida/core/memoria.py:1100` | función | `transitable_peligro` | `def transitable_peligro(self, clase: Optional[str]) -> bool:` |
| `ida/core/memoria.py:1105` | función | `ver_casillas` | `def ver_casillas(self, aqui: Pos, casillas: Dict[Pos, str], libres: Set[Pos], ocupadas: Set[Pos], peligros: Set[Pos]) -> None:` |
| `ida/core/memoria.py:1125` | función | `aprender_transformacion` | `def aprender_transformacion(self, verbo: Verbo, objetivo: str, antes: str, despues: str) -> None:` |
| `ida/core/memoria.py:1130` | función | `resultado` | `def resultado(self, verbo: Verbo, objetivo: str, antes: Optional[str] = None) -> Optional[str]:` |
| `ida/core/memoria.py:1135` | función | `aprender_cuerpo` | `def aprender_cuerpo(self, accion: str, libre: bool, avanza: bool, mira: bool) -> None:` |
| `ida/core/memoria.py:1142` | función | `modelo_cuerpo` | `def modelo_cuerpo(self, accion: str, libre: bool) -> Optional[Tuple[bool, bool]]:` |
| `ida/core/memoria.py:1149` | función | `bloqueada` | `def bloqueada(self, verbo: Verbo, objetivo: str) -> bool:` |
| `ida/core/memoria.py:1158` | función | `declarada` | `def declarada(self, verbo: Verbo, objetivo: str) -> bool:` |
| `ida/core/memoria.py:1163` | función | `puede_salir` | `def puede_salir(self, verbo: Verbo, objetivo: str) -> bool:` |
| `ida/core/memoria.py:1169` | función | `tasa_estimada` | `def tasa_estimada(self, verbo: Verbo, objetivo: str) -> float:` |
| `ida/core/memoria.py:1182` | función | `aprender_requisito` | `def aprender_requisito(` |
| `ida/core/memoria.py:1277` | función | `registrar_meta` | `def registrar_meta(` |
| `ida/core/memoria.py:1327` | función | `peligrosa` | `def peligrosa(self, clase: str) -> bool:` |
| `ida/core/mundo.py:139` | función | `aliestesia` | `def aliestesia(self) -> bool:` |
| `ida/core/mundo.py:180` | función | `manual` | `def manual(self) -> Dict[str, Any]:` |
| `ida/core/peligro.py:52` | constante | `VITALIDAD_MAXIMA` | `VITALIDAD_MAXIMA = 100.0` |
| `ida/core/peligro.py:53` | constante | `DANO_PREVIO` | `DANO_PREVIO = VITALIDAD_MAXIMA * 2.0 / 9.0   # daño desconocido de lo peligroso: 2 de 9 unidades de vitalidad (declarado)` |
| `ida/core/peligro.py:54` | constante | `PESO_PREVIO` | `PESO_PREVIO = 2.0                            # peso (en daños) del previo` |
| `ida/core/peligro.py:55` | constante | `VENTANA` | `VENTANA = 20                                 # media móvil: los últimos ~20 daños de cada clase` |
| `ida/core/peligro.py:56` | constante | `TASA_PREVIA` | `TASA_PREVIA = 0.5                            # daños por latido de exposición, sin datos (pesimista)` |
| `ida/core/peligro.py:57` | constante | `PESO_TASA` | `PESO_TASA = 2.0                              # peso (en latidos) del previo de la tasa` |
| `ida/core/peligro.py:58` | constante | `GOLPES_PREVIO` | `GOLPES_PREVIO = 10.0                         # golpes para derribar algo sin datos (pesimista: así no se lucha)` |
| `ida/core/peligro.py:59` | constante | `EMISION_MINIMA` | `EMISION_MINIMA = 0.6                         # ΔP a partir del cual X emite Y` |
| `ida/core/peligro.py:60` | constante | `JUNTO_MINIMO` | `JUNTO_MINIMO = 3                             # apariciones de Y junto a una X mínimas para decidirlo` |
| `ida/core/peligro.py:61` | constante | `MAX_RECORRIDOS` | `MAX_RECORRIDOS = 10` |
| `ida/core/peligro.py:62` | constante | `MAX_DERRIBOS` | `MAX_DERRIBOS = 30` |
| `ida/core/peligro.py:63` | constante | `MARGEN_REDUCTOR` | `MARGEN_REDUCTOR = 0.15                       # razón de golpes con / sin el objeto por debajo de 1 − margen: reduce` |
| `ida/core/peligro.py:64` | constante | `MINIMO_LEGADO` | `MINIMO_LEGADO = 2                            # observaciones mínimas para pasar al legado` |
| `ida/core/peligro.py:65` | constante | `PELIGRO_PREVIO` | `PELIGRO_PREVIO = 0.8                         # peligro del previo del manual a salud completa (fija la escala)` |
| `ida/core/peligro.py:66` | constante | `MARGEN_LUGAR` | `MARGEN_LUGAR = 3                             # el peligro de un lugar se anula a alcance + 3 casillas` |
| `ida/core/peligro.py:67` | constante | `ESCALA` | `ESCALA = (DANO_PREVIO / VITALIDAD_MAXIMA) * (1.0 / PELIGRO_PREVIO - 1.0)   # C de g(x) = x / (x + C)` |
| `ida/core/peligro.py:70` | función | `escala` | `def escala(x: float) -> float:` |
| `ida/core/peligro.py:75` | función | `manhattan` | `def manhattan(a: Pos, b: Pos) -> int:` |
| `ida/core/peligro.py:79` | función | `f_alcance` | `def f_alcance(d: int, alcance: int) -> float:` |
| `ida/core/peligro.py:85` | clase | `Media` | `class Media:` |
| `ida/core/peligro.py:91` | función | `anotar` | `def anotar(self, x: float) -> None:` |
| `ida/core/peligro.py:95` | función | `estimar` | `def estimar(self, previo: float, peso: float) -> float:` |
| `ida/core/peligro.py:101` | clase | `Emision` | `class Emision:` |
| `ida/core/peligro.py:109` | función | `contingencia` | `def contingencia(self) -> float:` |
| `ida/core/peligro.py:114` | clase | `Peligros` | `class Peligros:` |
| `ida/core/peligro.py:135` | función | `emitidas` | `def emitidas(self, x: str) -> List[str]:` |
| `ida/core/peligro.py:139` | función | `alcance_emision` | `def alcance_emision(self, x: str) -> int:` |
| `ida/core/peligro.py:143` | función | `dano_propio` | `def dano_propio(self, clase: str, peligrosa: bool) -> float:` |
| `ida/core/peligro.py:152` | función | `dano_por_golpe` | `def dano_por_golpe(self, clase: str, peligrosa) -> float:` |
| `ida/core/peligro.py:156` | función | `golpe` | `def golpe(self, clase: str, peligrosa: bool, dormido: bool = False) -> float:` |
| `ida/core/peligro.py:166` | función | `perdida` | `def perdida(self, clase: str, peligrosa: bool, dormido: bool = False) -> float:` |
| `ida/core/peligro.py:172` | función | `componentes` | `def componentes(self, clase: str, peligrosa, dormido: bool = False) -> List[Tuple[float, int]]:` |
| `ida/core/peligro.py:181` | función | `dano_esperado` | `def dano_esperado(self, clase: str, peligrosa) -> float:` |
| `ida/core/peligro.py:184` | función | `alcance` | `def alcance(self, clase: str, peligrosa) -> int:` |
| `ida/core/peligro.py:188` | función | `peligro_a` | `def peligro_a(comps: List[Tuple[float, int]], d: int, salud: float) -> float:` |
| `ida/core/peligro.py:194` | función | `peligro_lugar` | `def peligro_lugar(comps: List[Tuple[float, int]], d: int, salud: float) -> float:` |
| `ida/core/peligro.py:198` | función | `tasa` | `def tasa(self, clase: str) -> Tuple[float, int]:` |
| `ida/core/peligro.py:203` | función | `reductores` | `def reductores(self) -> Dict[str, float]:` |
| `ida/core/peligro.py:220` | función | `distinguibles` | `def distinguibles(self) -> Set[str]:` |
| `ida/core/peligro.py:230` | función | `golpes` | `def golpes(self, clase: str, objetos: Iterable[str], reductores: Optional[Dict[str, float]] = None) -> Tuple[float, int]:` |
| `ida/core/peligro.py:243` | función | `factor` | `def factor(kit: FrozenSet[str]) -> float:` |
| `ida/core/peligro.py:249` | función | `aprender` | `def aprender(self, aqui: Pos, agentes: Dict[str, Tuple[str, Pos]], visibles: Set[Pos], objetos: FrozenSet[str],` |
| `ida/core/peligro.py:333` | función | `volcado` | `def volcado(self, peligrosa) -> Dict[str, Any]:` |
| `ida/core/peligro.py:352` | función | `legado` | `def legado(self) -> Dict[str, Any]:` |
| `ida/core/peligro.py:379` | función | `heredar` | `def heredar(self, legado: Dict[str, Any]) -> int:` |
| `ida/core/peligro.py:407` | función | `estimar` | `def estimar(entidades: List[Any], aqui: Pos, peligros: Peligros, salud: float, peligrosa, dormido: bool = False) -> None:` |
| `ida/sistemas/comun.py:115` | clase | `Peticion` | `class Peticion(Componente):` |
| `ida/sistemas/comun.py:123` | función | `__init__` | `def __init__(self, catalogo: Catalogo):` |
| `ida/sistemas/comun.py:127` | función | `reactiva` | `def reactiva(self, ctx: Contexto) -> None:` |
| `ida/sistemas/proteger.py:41` | constante | `COBIJO` | `COBIJO = "cobijo"` |
| `ida/sistemas/proteger.py:42` | constante | `MAX_INTERIOR` | `MAX_INTERIOR = 3          # un recinto tiene 1-3 casillas (encargo, sección 2)` |
| `ida/sistemas/proteger.py:43` | constante | `ALCANCE_SITIO` | `ALCANCE_SITIO = 15        # pasos máximos hasta un sitio candidato (3.3)` |
| `ida/sistemas/proteger.py:44` | constante | `MAX_PASOS_POSTURA` | `MAX_PASOS_POSTURA = 12    # buscador de 3.1: «qué secuencia de MOVER me deja en A mirando a C»` |
| `ida/sistemas/proteger.py:45` | constante | `PROFUNDIDAD_PLAN` | `PROFUNDIDAD_PLAN = 30     # acciones máximas del plan local de un sitio (cavar, moverse, cerrar)` |
| `ida/sistemas/proteger.py:46` | constante | `MAX_ESTADOS` | `MAX_ESTADOS = 6000        # coste de cálculo: estados máximos por búsqueda` |
| `ida/sistemas/proteger.py:47` | constante | `CANDIDATOS_EXACTOS` | `CANDIDATOS_EXACTOS = 6    # sitios más baratos por la estimación rápida que se planifican del todo` |
| `ida/sistemas/proteger.py:48` | constante | `CADA_EVALUACION` | `CADA_EVALUACION = 5       # latidos entre evaluaciones completas de sitios (entretanto se replanifica el actual)` |
| `ida/sistemas/proteger.py:49` | constante | `MARGEN_SITIO` | `MARGEN_SITIO = 0.25       # histéresis: otro sitio sustituye al actual si cuesta al menos un 25 % menos...` |
| `ida/sistemas/proteger.py:50` | constante | `MARGEN_SITIO_MIN` | `MARGEN_SITIO_MIN = 3.0    # ...y al menos 3 pasos menos` |
| `ida/sistemas/proteger.py:51` | constante | `BONO_HOGAR` | `BONO_HOGAR = 5.0          # preferencia por el recinto recordado (hogar), en pasos` |
| `ida/sistemas/proteger.py:52` | constante | `COSTE_SIN_SITIO` | `COSTE_SIN_SITIO = 3 * ALCANCE_SITIO   # horizonte del cobijo sin ningún sitio posible: estimación alta (ir y volver al` |
| `ida/sistemas/proteger.py:57` | función | `_yo` | `def _yo(ctx: Contexto) -> Dict[str, Any]:` |
| `ida/sistemas/proteger.py:62` | función | `posicion` | `def posicion(ctx: Contexto) -> Optional[Pos]:` |
| `ida/sistemas/proteger.py:66` | función | `orientacion` | `def orientacion(ctx: Contexto) -> Optional[Pos]:` |
| `ida/sistemas/proteger.py:71` | función | `inventario` | `def inventario(ctx: Contexto) -> Dict[str, float]:` |
| `ida/sistemas/proteger.py:75` | función | `_peligros` | `def _peligros(ctx: Contexto) -> Set[Pos]:` |
| `ida/sistemas/proteger.py:86` | función | `_suma` | `def _suma(a: Pos, b: Pos) -> Pos:` |
| `ida/sistemas/proteger.py:90` | función | `_vecinas` | `def _vecinas(p: Pos) -> List[Pos]:` |
| `ida/sistemas/proteger.py:95` | función | `_manhattan` | `def _manhattan(a: Pos, b: Pos) -> int:` |
| `ida/sistemas/proteger.py:101` | clase | `Cerrador` | `class Cerrador:` |
| `ida/sistemas/proteger.py:110` | clase | `Modelo` | `class Modelo:` |
| `ida/sistemas/proteger.py:113` | función | `__init__` | `def __init__(self, mem: Memoria, inv: Dict[str, float], peligros: Set[Pos]):` |
| `ida/sistemas/proteger.py:139` | función | `libre` | `def libre(self, p: Pos) -> bool:` |
| `ida/sistemas/proteger.py:146` | función | `conocida` | `def conocida(self, p: Pos) -> bool:` |
| `ida/sistemas/proteger.py:149` | función | `acceso` | `def acceso(self, p: Pos) -> bool:` |
| `ida/sistemas/proteger.py:156` | función | `rinde` | `def rinde(self, p: Pos) -> Optional[Dict[str, float]]:` |
| `ida/sistemas/proteger.py:165` | función | `abre` | `def abre(self, clase: str) -> Optional[bool]:` |
| `ida/sistemas/proteger.py:177` | función | `inferida` | `def inferida(self, clase: str) -> bool:` |
| `ida/sistemas/proteger.py:181` | función | `confianza_cavar` | `def confianza_cavar(self, clase: str) -> float:` |
| `ida/sistemas/proteger.py:187` | función | `falta_para_cavar` | `def falta_para_cavar(self, clase: str) -> Optional[Dict[str, float]]:` |
| `ida/sistemas/proteger.py:197` | función | `_rinde_clase` | `def _rinde_clase(self, clase: str) -> Optional[Dict[str, float]]:` |
| `ida/sistemas/proteger.py:205` | función | `_cerradores` | `def _cerradores(self) -> List[Cerrador]:` |
| `ida/sistemas/proteger.py:222` | función | `unidades` | `def unidades(self, cavadas: Iterable[Pos] = ()) -> int:` |
| `ida/sistemas/proteger.py:229` | función | `_contar_unidades` | `def _contar_unidades(self, cavadas: FrozenSet[Pos]) -> int:` |
| `ida/sistemas/proteger.py:236` | función | `cerrable` | `def cerrable(self, p: Pos) -> bool:` |
| `ida/sistemas/proteger.py:243` | función | `cerrador_para` | `def cerrador_para(self, p: Pos) -> Optional[Cerrador]:` |
| `ida/sistemas/proteger.py:253` | función | `_bfs` | `def _bfs(inicio: Hashable, sucesores: Callable[[Any], Iterable[Tuple[Accion, Any]]], meta: Callable[[Any], bool],` |
| `ida/sistemas/proteger.py:282` | función | `mover` | `def mover(modelo: Modelo, pos: Pos, cara: Optional[Pos], d: Pos, pasable: bool) -> Optional[Tuple[Pos, Optional[Pos]]]:` |
| `ida/sistemas/proteger.py:291` | función | `buscar_postura` | `def buscar_postura(modelo: Modelo, pos: Pos, cara: Optional[Pos], destino: Pos, mirando: Pos,` |
| `ida/sistemas/proteger.py:296` | función | `sucesores` | `def sucesores(e: Tuple[Pos, Optional[Pos]]) -> Iterable[Tuple[Accion, Any]]:` |
| `ida/sistemas/proteger.py:310` | clase | `EstadoPlan` | `class EstadoPlan:` |
| `ida/sistemas/proteger.py:317` | función | `entorno` | `def entorno(interior: Tuple[Pos, ...]) -> Set[Pos]:` |
| `ida/sistemas/proteger.py:322` | función | `planificar` | `def planificar(modelo: Modelo, pos: Pos, cara: Optional[Pos], interior: Tuple[Pos, ...], excavar: FrozenSet[Pos],` |
| `ida/sistemas/proteger.py:333` | función | `sucesores` | `def sucesores(e: EstadoPlan) -> Iterable[Tuple[Accion, EstadoPlan]]:` |
| `ida/sistemas/proteger.py:352` | función | `meta` | `def meta(e: EstadoPlan) -> bool:` |
| `ida/sistemas/proteger.py:359` | función | `accesos_de` | `def accesos_de(modelo: Modelo, interior: Iterable[Pos]) -> Optional[FrozenSet[Pos]]:` |
| `ida/sistemas/proteger.py:374` | función | `recinto_actual` | `def recinto_actual(modelo: Modelo, aqui: Pos) -> Optional[Tuple[Pos, ...]]:` |
| `ida/sistemas/proteger.py:391` | función | `rutas` | `def rutas(modelo: Modelo, aqui: Pos, alcance: int = ALCANCE_SITIO) -> Tuple[Dict[Pos, int], Dict[Pos, Pos]]:` |
| `ida/sistemas/proteger.py:408` | clase | `Sitio` | `class Sitio:` |
| `ida/sistemas/proteger.py:420` | función | `candidatos` | `def candidatos(modelo: Modelo, aqui: Pos, dist: Dict[Pos, int], hogar: Optional[Pos],` |
| `ida/sistemas/proteger.py:466` | función | `completar` | `def completar(modelo: Modelo, sitio: Sitio, aqui: Pos, cara: Optional[Pos], dist: Dict[Pos, int],` |
| `ida/sistemas/proteger.py:494` | función | `_abrir` | `def _abrir(modelo: Modelo, interior: Tuple[Pos, ...], aqui: Pos) -> List[Dict[str, Any]]:` |
| `ida/sistemas/proteger.py:510` | clase | `Recinto` | `class Recinto(Componente):` |
| `ida/sistemas/proteger.py:521` | función | `__init__` | `def __init__(self) -> None:` |
| `ida/sistemas/proteger.py:532` | función | `reactiva` | `def reactiva(self, ctx: Contexto) -> None:` |
| `ida/sistemas/proteger.py:575` | función | `_coste_objeto` | `def _coste_objeto(self, ctx: Contexto, objeto: str, inv: Dict[str, float], cache: Dict[str, Optional[float]]) -> Optional[float]:` |
| `ida/sistemas/proteger.py:582` | función | `_requisitos` | `def _requisitos(self, ctx: Contexto, modelo: Modelo, aqui: Pos, cara: Optional[Pos], dist: Dict[Pos, int],` |
| `ida/sistemas/proteger.py:651` | función | `_elegir` | `def _elegir(self, ctx: Contexto, modelo: Modelo, aqui: Pos, cara: Optional[Pos], dist: Dict[Pos, int],` |
| `ida/sistemas/proteger.py:674` | función | `_reconstruir` | `def _reconstruir(modelo: Modelo, interior: Tuple[Pos, ...], dist: Dict[Pos, int], hogar: Optional[Pos]) -> Optional[Sitio]:` |
| `ida/sistemas/proteger.py:692` | función | `_primera` | `def _primera(modelo: Modelo, sitio: Sitio, aqui: Pos, previo: Dict[Pos, Pos]) -> Optional[Dict[str, Any]]:` |
| `ida/sistemas/proteger.py:719` | función | `_confianza` | `def _confianza(ctx: Contexto, modelo: Modelo, sitio: Sitio) -> float:` |
| `ida/sistemas/proteger.py:732` | función | `_explicar` | `def _explicar(sitio: Sitio, accion: Dict[str, Any]) -> str:` |
| `ida/sistemas/proteger.py:738` | función | `recinto` | `def recinto(ctx: Contexto) -> Optional[Pieza]:` |
| `ida/sistemas/proteger.py:743` | clase | `Proteger` | `class Proteger(ConPropuestas):` |
| `ida/sistemas/proteger.py:765` | función | `elegible` | `def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:` |
| `ida/sistemas/proteger.py:770` | función | `_cede` | `def _cede(ctx: Contexto) -> bool:` |
| `ida/sistemas/proteger.py:777` | función | `pedir` | `def pedir(self, ctx: Contexto, estrategia: Pieza) -> List[Dict[str, Any]]:` |
| `ida/sistemas/proteger.py:791` | función | `_intensidades` | `def _intensidades(ctx: Contexto) -> Tuple[float, str, float]:` |
| `ida/sistemas/proteger.py:802` | función | `decidir` | `def decidir(self, ctx: Contexto, estrategia: Optional[Pieza] = None) -> None:` |
| `ida/sistemas/proteger.py:822` | función | `riesgo_exterior` | `def riesgo_exterior(ctx: Contexto) -> float:` |
| `ida/sistemas/proteger.py:830` | función | `_proponer_abrir` | `def _proponer_abrir(estrategia: ConPropuestas, ctx: Contexto, c: Dict[str, Any], origen: str, necesidad: str, deficit: float,` |
| `ida/sistemas/proteger.py:841` | clase | `SalirDelRecinto` | `class SalirDelRecinto(ConPropuestas):` |
| `ida/sistemas/proteger.py:857` | función | `_deficit` | `def _deficit(ctx: Contexto, impulso: str) -> Optional[float]:` |
| `ida/sistemas/proteger.py:864` | función | `elegible` | `def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:` |
| `ida/sistemas/proteger.py:872` | función | `decidir` | `def decidir(self, ctx: Contexto, estrategia: Optional[Pieza] = None) -> None:` |
| `ida/sistemas/s1.py:144` | constante | `SATISFACE_MIN` | `SATISFACE_MIN = 0.3   # paso 0b: a partir de aquí algo satisface una necesidad (como ``nutritivo`` ≥ 0,3 hoy)` |
| `ida/sistemas/s1.py:147` | función | `intensidades` | `def intensidades(ctx: Contexto) -> Dict[str, float]:` |
| `ida/sistemas/s1.py:158` | función | `satisface_de` | `def satisface_de(ctx: Contexto, o: Pieza) -> Dict[str, float]:` |
| `ida/sistemas/s1.py:170` | clase | `Apetencia` | `class Apetencia(Componente):` |
| `ida/sistemas/s1.py:179` | función | `reactiva` | `def reactiva(self, ctx: Contexto) -> None:` |
| `ida/sistemas/s1.py:261` | constante | `RESERVA` | `RESERVA = 100.0 * 3.0 / 9.0   # paso 6b: vitalidad que una lucha debe dejar intacta (3 de 9, declarado)` |
| `ida/sistemas/s1.py:264` | función | `_yo` | `def _yo(ctx: Contexto) -> Optional[Tuple[int, int]]:` |
| `ida/sistemas/s1.py:273` | función | `_objetos_llevados` | `def _objetos_llevados(ctx: Contexto) -> FrozenSet[str]:` |
| `ida/sistemas/s1.py:280` | función | `objetos_peligrosos` | `def objetos_peligrosos(ctx: Contexto) -> List[Pieza]:` |
| `ida/sistemas/s1.py:288` | clase | `Afrontar` | `class Afrontar(Definicion):` |
| `ida/sistemas/s1.py:318` | función | `_valorar` | `def _valorar(ctx: Contexto, o: Pieza, aqui: Tuple[int, int], salud: float, llevados: FrozenSet[str],` |
| `ida/sistemas/s1.py:335` | función | `evaluar` | `def evaluar(self, ctx: Contexto) -> Optional[Dict[str, Any]]:` |
| `ida/sistemas/s1.py:362` | función | `elegible` | `def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:` |
| `ida/sistemas/s1.py:365` | función | `paso` | `def paso(self, ctx: Contexto, estrategia: Pieza) -> Any:` |
| `ida/sistemas/s1.py:370` | función | `_confianza` | `def _confianza(v: Dict[str, Any]) -> float:` |
| `ida/sistemas/s1.py:374` | función | `actuar` | `def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:` |
| `ida/sistemas/s1.py:411` | función | `pedir` | `def pedir(self, ctx: Contexto, estrategia: Pieza) -> List[Dict[str, Any]]:` |
| `ida/sistemas/s1.py:507` | función | `_nutritivo` | `def _nutritivo(o: Pieza) -> bool:` |
| `ida/sistemas/s1.py:511` | función | `_al_alcance` | `def _al_alcance(ctx: Contexto, rechaza: Rechazo = _rechazado, comestible: Comestible = _nutritivo) -> Tuple[List[Pieza], List[Pieza]]:` |
| `ida/sistemas/s1.py:518` | función | `_aceptables_a_la_vista` | `def _aceptables_a_la_vista(ctx: Contexto, rechaza: Rechazo = _rechazado, comestible: Comestible = _nutritivo) -> List[Pieza]:` |
| `ida/sistemas/s1.py:586` | función | `_apetencia` | `def _apetencia(ctx: Contexto, o: Pieza) -> Optional[Pieza]:` |
| `ida/sistemas/s1.py:589` | función | `_comestible` | `def _comestible(self, ctx: Contexto, impulso: str) -> Comestible:` |
| `ida/sistemas/s1.py:590` | función | `comestible` | `def comestible(o: Pieza) -> bool:` |
| `ida/sistemas/s1.py:595` | función | `_deseo` | `def _deseo(self, ctx: Contexto, o: Pieza) -> float:` |
| `ida/sistemas/s1.py:600` | función | `_olor_sin_ambiguedad` | `def _olor_sin_ambiguedad(ctx: Contexto, impulso: str) -> bool:` |
| `ida/sistemas/s1.py:607` | función | `_destino_olor` | `def _destino_olor(self, ctx: Contexto, impulso: str) -> Optional[Pieza]:` |
| `ida/sistemas/s1.py:611` | función | `_intensidad` | `def _intensidad(ctx: Contexto, impulso: str) -> float:` |
| `ida/sistemas/s1.py:615` | función | `_elegible_por_necesidad` | `def _elegible_por_necesidad(self, ctx: Contexto, impulso: str) -> bool:` |
| `ida/sistemas/s1.py:621` | función | `_paso_por_necesidad` | `def _paso_por_necesidad(self, ctx: Contexto, impulso: str) -> str:` |
| `ida/sistemas/s1.py:632` | función | `_actuar_por_necesidad` | `def _actuar_por_necesidad(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:` |
| `ida/sistemas/s1.py:743` | constante | `VENTANA_TENDENCIA` | `VENTANA_TENDENCIA = 50   # alostasis: latidos de la media móvil de la tendencia de cada déficit` |
| `ida/sistemas/s1.py:767` | función | `alostasis` | `def alostasis(ctx: Contexto, defs: Dict[str, float]) -> Dict[str, Tuple[float, float, float]]:` |
| `ida/sistemas/s3.py:474` | función | `_yo` | `def _yo(ctx: Contexto) -> Dict[str, Any]:` |
| `ida/sistemas/s3.py:479` | función | `inventario` | `def inventario(ctx: Contexto) -> Dict[str, float]:` |
| `ida/sistemas/s3.py:484` | función | `delante` | `def delante(ctx: Contexto) -> Optional[Dict[str, Any]]:` |
| `ida/sistemas/s3.py:490` | función | `_cosas` | `def _cosas(ctx: Contexto) -> List[Pieza]:` |
| `ida/sistemas/s3.py:494` | función | `_pos` | `def _pos(p: Pieza) -> Optional[Tuple[int, int]]:` |
| `ida/sistemas/s3.py:499` | función | `_dist` | `def _dist(a: Tuple[int, int], b: Tuple[int, int]) -> int:` |
| `ida/sistemas/s3.py:503` | función | `al_alcance_clase` | `def al_alcance_clase(ctx: Contexto, clase: str) -> bool:` |
| `ida/sistemas/s3.py:507` | función | `desplazamientos_a_clase` | `def desplazamientos_a_clase(ctx: Contexto, clase: str) -> List[Tuple[int, int]]:` |
| `ida/sistemas/s3.py:524` | clase | `Paso` | `class Paso:` |
| `ida/sistemas/s3.py:538` | constante | `COSTE_RECORDADO` | `COSTE_RECORDADO = 15.0     # ir adonde se recuerda algo que no se ve` |
| `ida/sistemas/s3.py:539` | constante | `COSTE_POR_PROXIMIDAD` | `COSTE_POR_PROXIMIDAD = 10.0` |
| `ida/sistemas/s3.py:540` | constante | `MAX_RUTA_MAPA` | `MAX_RUTA_MAPA = 40         # pasos máximos de una ruta por el mapa local hasta algo recordado` |
| `ida/sistemas/s3.py:541` | constante | `COSTE_SIN_PRODUCTOR` | `COSTE_SIN_PRODUCTOR = 2 * COSTE_RECORDADO   # reponer una unidad de algo que ninguna acción conocida da` |
| `ida/sistemas/s3.py:542` | constante | `VECINAS` | `VECINAS = ((1, 0), (-1, 0), (0, 1), (0, -1))` |
| `ida/sistemas/s3.py:545` | función | `ir_por_el_mapa` | `def ir_por_el_mapa(ctx: Contexto, clase: str, confianza: float = 0.5, excluir: frozenset = frozenset()) -> Optional[Paso]:` |
| `ida/sistemas/s3.py:591` | función | `acercarse_a_clase` | `def acercarse_a_clase(ctx: Contexto, clase: str, confianza: float = 0.5, excluir: frozenset = frozenset()) -> Optional[Paso]:` |
| `ida/sistemas/s3.py:623` | función | `_cantidad` | `def _cantidad(r: Any, objeto: str) -> float:` |
| `ida/sistemas/s3.py:629` | función | `_pos_propia` | `def _pos_propia(ctx: Contexto) -> Optional[Tuple[int, int]]:` |
| `ida/sistemas/s3.py:637` | clase | `PerseguirMetas` | `class PerseguirMetas(ConPropuestas):` |
| `ida/sistemas/s3.py:656` | constante | `PROFUNDIDAD` | `PROFUNDIDAD = 5` |
| `ida/sistemas/s3.py:657` | constante | `AROUSAL` | `AROUSAL = 0.5` |
| `ida/sistemas/s3.py:658` | constante | `CADA_EXPLORACION` | `CADA_EXPLORACION = 5          # latidos entre pruebas de efectos` |
| `ida/sistemas/s3.py:659` | constante | `VERBOS_PLAN` | `VERBOS_PLAN = (Verbo.USAR, Verbo.COGER, Verbo.COMER)` |
| `ida/sistemas/s3.py:660` | constante | `SIN_ACERCARSE` | `SIN_ACERCARSE = 8             # propuestas seguidas de MOVER al mismo destino sin que baje la distancia...` |
| `ida/sistemas/s3.py:661` | constante | `APARCAR` | `APARCAR = 30                  # ...que lo dejan aparcado durante estos latidos` |
| `ida/sistemas/s3.py:663` | función | `__init__` | `def __init__(self) -> None:` |
| `ida/sistemas/s3.py:671` | función | `_excluir` | `def _excluir(self, ctx: Contexto) -> frozenset:` |
| `ida/sistemas/s3.py:674` | función | `_vigilar` | `def _vigilar(self, ctx: Contexto, paso: Paso) -> None:` |
| `ida/sistemas/s3.py:694` | función | `elegible` | `def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:` |
| `ida/sistemas/s3.py:699` | función | `_peticiones` | `def _peticiones(ctx: Contexto, inv: Dict[str, float]) -> List[Pieza]:` |
| `ida/sistemas/s3.py:703` | función | `conseguir` | `def conseguir(self, ctx: Contexto, objeto: str, inv: Dict[str, float]) -> Optional[Paso]:` |
| `ida/sistemas/s3.py:711` | función | `decidir` | `def decidir(self, ctx: Contexto, estrategia: Optional[Pieza] = None) -> None:` |
| `ida/sistemas/s3.py:746` | función | `_atender_peticiones` | `def _atender_peticiones(self, ctx: Contexto, inv: Dict[str, float]) -> None:` |
| `ida/sistemas/s3.py:761` | función | `_resolver` | `def _resolver(self, ctx: Contexto, accion: Tuple[Verbo, str], inv: Dict[str, float], visitado: frozenset,` |
| `ida/sistemas/s3.py:780` | función | `mejor_de` | `def mejor_de(opciones: List[Optional[Paso]], texto: str) -> Optional[Paso]:` |
| `ida/sistemas/s3.py:813` | función | `_con_consumo` | `def _con_consumo(self, ctx: Contexto, accion: Tuple[Verbo, str], paso: Optional[Paso], inv: Dict[str, float],` |
| `ida/sistemas/s3.py:825` | función | `_coste_unidad` | `def _coste_unidad(self, ctx: Contexto, objeto: str, inv: Dict[str, float], visitado: frozenset, prof: int) -> float:` |
| `ida/sistemas/s3.py:839` | función | `_mejor_lote` | `def _mejor_lote(self, ctx: Contexto, resueltas: List[Tuple[Verbo, str]], inv: Dict[str, float],` |
| `ida/sistemas/s3.py:898` | función | `_colocar` | `def _colocar(self, ctx: Contexto, accion: Tuple[Verbo, str], inv: Dict[str, float], propio: Dict[str, float],` |
| `ida/sistemas/s3.py:905` | función | `_coste_material` | `def _coste_material(self, ctx: Contexto, total: Dict[str, float],` |
| `ida/sistemas/s3.py:923` | función | `_de_campo` | `def _de_campo(self, ctx: Contexto, objeto: str, inv: Dict[str, float], prof: int) -> bool:` |
| `ida/sistemas/s3.py:935` | función | `_por_el_mapa` | `def _por_el_mapa(self, ctx: Contexto, clase: str, confianza: float) -> Optional[Paso]:` |
| `ida/sistemas/s3.py:945` | función | `_ejecutar` | `def _ejecutar(self, ctx: Contexto, accion: Tuple[Verbo, str], r: Any) -> Optional[Paso]:` |
| `ida/sistemas/s3.py:978` | función | `_explorar_efectos` | `def _explorar_efectos(self, ctx: Contexto) -> None:` |

## B. Quién lee la Observación fuera de los sensores

**Comando:** `git grep -n -E "observacion|obs\." -- ida/core ida/sistemas ":(exclude)ida/core/sentidos.py"`

| fichero:línea | función o método | línea literal |
|---|---|---|
| `ida/core/arquitectura.py:70` | `<módulo>` | `observacion: Optional[Observacion] = None` |
| `ida/core/latido.py:114` | `latir` | `if obs.vitales:` |
| `ida/core/latido.py:115` | `latir` | `soma.sincronizar(obs.vitales)` |
| `ida/core/latido.py:116` | `latir` | `if obs.dormido is not None:` |
| `ida/core/latido.py:117` | `latir` | `soma.dormido = obs.dormido` |
| `ida/core/latido.py:202` | `_aprender` | `ubicacion = ctx.observacion.ubicacion if ctx.observacion else ""` |
| `ida/core/latido.py:207` | `_aprender` | `if ctx.observacion:` |
| `ida/core/latido.py:208` | `_aprender` | `for e in ctx.observacion.entidades:` |
| `ida/core/latido.py:248` | `_peligro_aprendido` | `obs = ctx.observacion` |
| `ida/core/latido.py:249` | `_peligro_aprendido` | `aqui = pos_de(obs.ubicacion) if obs is not None else None` |
| `ida/core/latido.py:250` | `_peligro_aprendido` | `if obs is None or aqui is None or any("peligro" in e.rasgos for e in obs.entidades):` |
| `ida/core/latido.py:252` | `_peligro_aprendido` | `con_pos = [e for e in obs.entidades if isinstance(e.datos.get("pos"), (list, tuple)) and len(e.datos["pos"]) == 2]` |
| `ida/core/latido.py:259` | `_peligro_aprendido` | `crudas = (obs.cuerpo or {}).get("casillas")` |
| `ida/core/latido.py:264` | `_peligro_aprendido` | `objetos = frozenset(k for k, v in mem._objetos(dict(obs.inventario or {})).items() if v >= 1.0)` |
| `ida/core/latido.py:272` | `_peligro_aprendido` | `pel.estimar(obs.entidades, aqui, mem.peligros, self.soma.vitalidad, mem.peligrosa, dormido=bool(self.soma.dormido))` |
| `ida/core/latido.py:297` | `_aprender_mapa` | `obs = ctx.observacion` |
| `ida/core/latido.py:300` | `_aprender_mapa` | `aqui = pos_de(obs.ubicacion)` |
| `ida/core/latido.py:301` | `_aprender_mapa` | `cuerpo = obs.cuerpo or {}` |
| `ida/core/latido.py:335` | `_aprender_mapa` | `for e in obs.entidades:` |
| `ida/core/latido.py:353` | `_situacion_inventario` | `obs = ctx.observacion` |
| `ida/core/latido.py:354` | `_situacion_inventario` | `if obs is None or obs.inventario is None:` |
| `ida/core/latido.py:356` | `_situacion_inventario` | `cerca = {e.clase for e in obs.entidades if e.rasgos.get("lugar", 0.0) < 0.5 and e.rasgos.get("proximidad", 0.0) >= 0.9}` |
| `ida/core/latido.py:357` | `_situacion_inventario` | `delante = (obs.cuerpo or {}).get("delante")` |
| `ida/core/latido.py:358` | `_situacion_inventario` | `return (dict(obs.inventario), cerca, (str(delante.get("clase")) if isinstance(delante, dict) and delante.get("clase") else None),` |
| `ida/core/latido.py:366` | `_distancias` | `partes = str(obs.ubicacion).rsplit("_", 2)` |
| `ida/core/latido.py:369` | `_distancias` | `for e in obs.entidades:` |
| `ida/core/latido.py:492` | `_episodio` | `if ctx.observacion is not None and ctx.observacion.ubicacion:` |
| `ida/core/latido.py:493` | `_episodio` | `self.episodio.trayectoria.append(ctx.observacion.ubicacion)` |
| `ida/core/latido.py:500` | `_episodio` | `if ctx.observacion is not None and ctx.observacion.ubicacion:` |
| `ida/core/latido.py:501` | `_episodio` | `if not ep.trayectoria or ep.trayectoria[-1] != ctx.observacion.ubicacion:` |
| `ida/core/latido.py:502` | `_episodio` | `ep.trayectoria.append(ctx.observacion.ubicacion)` |
| `ida/core/latido.py:513` | `_episodio` | `if self.con_experiencia and self.perfil.hogar and ctx.observacion is not None:` |
| `ida/core/latido.py:514` | `_episodio` | `self.memoria.recordar_lugar(ctx.observacion.ubicacion, 1.0 if ep.resuelto and calma else -0.5)` |
| `ida/core/peligro.py:64` | `<módulo>` | `MINIMO_LEGADO = 2                            # observaciones mínimas para pasar al legado` |
| `ida/core/peligro.py:353` | `legado` | `"""Lo aprendido con al menos ``MINIMO_LEGADO`` observaciones."""` |
| `ida/sistemas/proteger.py:63` | `posicion` | `return pos_de(ctx.observacion.ubicacion) if ctx.observacion is not None else None` |
| `ida/sistemas/proteger.py:556` | `reactiva` | `ctx.memoria.recordar_lugar(ctx.observacion.ubicacion if ctx.observacion else "", 1.0)` |
| `ida/sistemas/s2.py:272` | `_estado` | `aqui = ctx.observacion.ubicacion if ctx.observacion else ""` |
| `ida/sistemas/s2.py:330` | `_plan` | `aqui = ctx.observacion.ubicacion if ctx.observacion else ""` |
| `ida/sistemas/s2.py:371` | `construir` | `aqui = ctx.observacion.ubicacion if ctx.observacion else ""` |
| `ida/sistemas/s2.py:384` | `cumplido` | `return ctx.observacion is not None and ctx.observacion.ubicacion == paso["meta"]` |
| `ida/sistemas/s2.py:387` | `fallido` | `aqui = ctx.observacion.ubicacion if ctx.observacion else ""` |
| `ida/sistemas/s2.py:400` | `elegible` | `aqui = ctx.observacion.ubicacion if ctx.observacion else ""` |
| `ida/sistemas/s3.py:611` | `acercarse_a_clase` | `ubicacion = ctx.observacion.ubicacion if ctx.observacion else ""` |
| `ida/sistemas/s3.py:631` | `_pos_propia` | `partes = str(ctx.observacion.ubicacion if ctx.observacion else "").rsplit("_", 2)` |

## C. Quién lee rasgos valorados

**Comando:** `git grep -n -E "(rasgo\(|rasgos\.get\(|rasgos\[)" -- ida/`

| fichero:línea | función | rasgo | línea literal |
|---|---|---|---|
| `ida/core/latido.py:344` | `_aprender_mapa` | `peligro` | `if e.rasgos.get("peligro", 0.0) >= 0.5 and e.rasgos.get("agente", 0.0) >= 0.5:` |
| `ida/core/latido.py:430` | `_dormir` | `peligro` | `peligro = max((p.rasgo("peligro") * p.rasgo("proximidad") for p in ctx.onda.ev("Exterocepcion").values()), default=0.0)` |
| `ida/core/latido.py:441` | `_indicadores` | `peligro` | `peligro = max((p.rasgo("peligro") * max(p.rasgo("proximidad"), 0.3) for p in exterocepcion), default=0.0)` |
| `ida/core/latido.py:447` | `_indicadores` | `novedad` | `novedad = max((p.rasgo("novedad") for p in exterocepcion), default=0.0)` |
| `ida/core/peligro.py:424` | `estimar` | `peligro` | `e.rasgos["peligro"] = peligros.peligro_a(comps, manhattan(aqui, p), salud)` |
| `ida/core/peligro.py:428` | `estimar` | `peligro` | `e.rasgos["peligro"] = max((peligros.peligro_lugar(comps, manhattan(p, q), salud) for q, comps in fuentes), default=0.0)` |
| `ida/mundos/archivos.py:180` | `observar` | `novedad` | `rasgos["novedad"] = 1.0 if eid not in self.vistos else 0.0` |
| `ida/mundos/archivos.py:322` | `_depredador` | `peligro` | `if p.rasgo("agente") >= 0.5 and p.rasgo("peligro") >= 0.5 and p.rasgo("proximidad") >= 0.9), None)` |
| `ida/mundos/archivos.py:355` | `reactiva` | `nutritivo` | `al_alcance = [o for o in ctx.onda.ev("Objeto").values() if o.rasgo("nutritivo") >= 0.3 and o.rasgo("proximidad") >= 0.9]` |
| `ida/mundos/archivos.py:406` | `_destino` | `peligro` | `if p.rasgo("lugar") >= 0.5 and p.rasgo("peligro") < 0.5 and p.id not in malas]` |
| `ida/mundos/archivos.py:407` | `_destino` | `nutritivo` | `return max(carpetas, key=lambda p: p.rasgo("nutritivo") + 0.5 * p.rasgo("novedad")) if carpetas else None` |
| `ida/mundos/archivos.py:407` | `_destino` | `novedad` | `return max(carpetas, key=lambda p: p.rasgo("nutritivo") + 0.5 * p.rasgo("novedad")) if carpetas else None` |
| `ida/mundos/minimo.py:197` | `_depredador` | `peligro` | `if p.rasgo("agente") >= 0.5 and p.rasgo("peligro") >= 0.5 and p.rasgo("proximidad") >= 0.9), None)` |
| `ida/sistemas/proteger.py:79` | `_peligros` | `peligro` | `if p.rasgo("lugar") < 0.5 and p.rasgo("peligro") >= 0.5:` |
| `ida/sistemas/s1.py:119` | `reactiva` | `peligro` | `amenaza = acotar(o.rasgo("peligro") * (0.3 + 0.7 * o.rasgo("proximidad")) * sensibilidad)` |
| `ida/sistemas/s1.py:120` | `reactiva` | `nutritivo` | `atractivo = o.rasgo("nutritivo") * (0.4 + 0.6 * o.rasgo("proximidad"))` |
| `ida/sistemas/s1.py:203` | `_salida` | `peligro` | `salida = mejor(lugares(ctx), lambda lugar: -lugar.rasgo("peligro"))` |
| `ida/sistemas/s1.py:204` | `_salida` | `peligro` | `return salida if salida is not None and salida.rasgo("peligro") < peligro else None` |
| `ida/sistemas/s1.py:284` | `objetos_peligrosos` | `peligro` | `return sorted((o for o in objetos(ctx) if o.rasgo("peligro") > 0.0` |
| `ida/sistemas/s1.py:331` | `_valorar` | `peligro` | `beneficio = o.rasgo("peligro") + (1.0 if meta is not None and not meta.conseguida else 0.0)` |
| `ida/sistemas/s1.py:351` | `evaluar` | `peligro` | `principal = max(valoradas, key=lambda v: (v["pieza"].rasgo("peligro"), v["pieza"].id))` |
| `ida/sistemas/s1.py:402` | `actuar` | `peligro` | `pasos = [(abs(meta[0] - pos[0]) + abs(meta[1] - pos[1]), lugar.rasgo("peligro"), lugar.id, lugar)` |
| `ida/sistemas/s1.py:466` | `_destino` | `peligro` | `return mejor(lugares(ctx), lambda lugar: lugar.rasgo("nutritivo") - 1.5 * lugar.rasgo("peligro"))` |
| `ida/sistemas/s1.py:466` | `_destino` | `nutritivo` | `return mejor(lugares(ctx), lambda lugar: lugar.rasgo("nutritivo") - 1.5 * lugar.rasgo("peligro"))` |
| `ida/sistemas/s1.py:508` | `_nutritivo` | `nutritivo` | `return o.rasgo("nutritivo") >= 0.3` |
| `ida/sistemas/s1.py:535` | `_hacia` | `peligro` | `candidatos = [(lugar, _posicion(ctx, lugar.id)) for lugar in _lugares_permitidos(ctx) if lugar.rasgo("peligro") < 0.8]` |
| `ida/sistemas/s1.py:549` | `_destino_comida` | `peligro` | `destino = mejor(_lugares_permitidos(ctx), lambda lugar: lugar.rasgo("nutritivo") - 1.5 * lugar.rasgo("peligro"))` |
| `ida/sistemas/s1.py:549` | `_destino_comida` | `nutritivo` | `destino = mejor(_lugares_permitidos(ctx), lambda lugar: lugar.rasgo("nutritivo") - 1.5 * lugar.rasgo("peligro"))` |
| `ida/sistemas/s1.py:550` | `_destino_comida` | `peligro` | `return destino if destino is not None and destino.rasgo("nutritivo") > 0.0 and destino.rasgo("peligro") < 0.8 else None` |
| `ida/sistemas/s1.py:550` | `_destino_comida` | `nutritivo` | `return destino if destino is not None and destino.rasgo("nutritivo") > 0.0 and destino.rasgo("peligro") < 0.8 else None` |
| `ida/sistemas/s1.py:639` | `_actuar_por_necesidad` | `peligro` | `cerca = mejor(aceptables, lambda o: self._deseo(ctx, o) - o.rasgo("peligro"))` |
| `ida/sistemas/s1.py:644` | `_actuar_por_necesidad` | `peligro` | `lambda o: self._deseo(ctx, o) * o.rasgo("proximidad") - o.rasgo("peligro"))` |
| `ida/sistemas/s1.py:653` | `_actuar_por_necesidad` | `nutritivo` | `ar = acotar(0.25 + 0.6 * ganas * destino.rasgo("nutritivo"))` |
| `ida/sistemas/s1.py:656` | `_actuar_por_necesidad` | `peligro` | `otro = mejor([lugar for lugar in _lugares_permitidos(ctx) if lugar.rasgo("peligro") < 0.5],` |
| `ida/sistemas/s1.py:657` | `_actuar_por_necesidad` | `peligro` | `lambda lugar: lugar.rasgo("novedad") - lugar.rasgo("peligro"))` |
| `ida/sistemas/s1.py:657` | `_actuar_por_necesidad` | `novedad` | `lambda lugar: lugar.rasgo("novedad") - lugar.rasgo("peligro"))` |
| `ida/sistemas/s1.py:685` | `actuar` | `peligro` | `cerca = mejor(aceptables, lambda o: o.rasgo("nutritivo") - o.rasgo("peligro"))` |
| `ida/sistemas/s1.py:685` | `actuar` | `nutritivo` | `cerca = mejor(aceptables, lambda o: o.rasgo("nutritivo") - o.rasgo("peligro"))` |
| `ida/sistemas/s1.py:690` | `actuar` | `peligro` | `vista = mejor(_aceptables_a_la_vista(ctx, self.rechaza), lambda o: o.rasgo("nutritivo") * o.rasgo("proximidad") - o.rasgo("peligro"))` |
| `ida/sistemas/s1.py:690` | `actuar` | `nutritivo` | `vista = mejor(_aceptables_a_la_vista(ctx, self.rechaza), lambda o: o.rasgo("nutritivo") * o.rasgo("proximidad") - o.rasgo("peligro"))` |
| `ida/sistemas/s1.py:694` | `actuar` | `nutritivo` | `ar = acotar(0.25 + 0.6 * apetito(ctx) * vista.rasgo("nutritivo"))` |
| `ida/sistemas/s1.py:698` | `actuar` | `nutritivo` | `ar = acotar(0.25 + 0.6 * apetito(ctx) * destino.rasgo("nutritivo"))` |
| `ida/sistemas/s1.py:701` | `actuar` | `peligro` | `otro = mejor([lugar for lugar in _lugares_permitidos(ctx) if lugar.rasgo("peligro") < 0.5],` |
| `ida/sistemas/s1.py:702` | `actuar` | `peligro` | `lambda lugar: lugar.rasgo("novedad") - lugar.rasgo("peligro"))` |
| `ida/sistemas/s1.py:702` | `actuar` | `novedad` | `lambda lugar: lugar.rasgo("novedad") - lugar.rasgo("peligro"))` |
| `ida/sistemas/s2.py:161` | `reactiva` | `nutritivo` | `motivacional = o.rasgo("nutritivo") * apetito(ctx) + 0.5 * o.rasgo("recurso") * arq.apertura` |
| `ida/sistemas/s2.py:161` | `reactiva` | `recurso` | `motivacional = o.rasgo("nutritivo") * apetito(ctx) + 0.5 * o.rasgo("recurso") * arq.apertura` |
| `ida/sistemas/s2.py:162` | `reactiva` | `peligro` | `potencia = o.rasgo("peligro")` |
| `ida/sistemas/s2.py:196` | `reactiva` | `novedad` | `novedad = max([lugar.rasgo("novedad") for lugar in lugares(ctx)] + [o.rasgo("novedad") for o in objetos(ctx)] + [0.0])` |
| `ida/sistemas/s2.py:227` | `puntuar` | `peligro` | `s = lugar.rasgo("novedad") - lugar.rasgo("peligro")` |
| `ida/sistemas/s2.py:227` | `puntuar` | `novedad` | `s = lugar.rasgo("novedad") - lugar.rasgo("peligro")` |
| `ida/sistemas/s2.py:234` | `_nuevo` | `peligro` | `return nuevo if nuevo is not None and nuevo.rasgo("novedad") > 0.0 and nuevo.rasgo("peligro") < 0.5 else None` |
| `ida/sistemas/s2.py:234` | `_nuevo` | `novedad` | `return nuevo if nuevo is not None and nuevo.rasgo("novedad") > 0.0 and nuevo.rasgo("peligro") < 0.5 else None` |
| `ida/sistemas/s2.py:240` | `_util` | `peligro` | `return mejor([o for o in objetos(ctx) if al_alcance(o) and o.rasgo("recurso") >= 0.4 and o.rasgo("peligro") < 0.3],` |
| `ida/sistemas/s2.py:240` | `_util` | `recurso` | `return mejor([o for o in objetos(ctx) if al_alcance(o) and o.rasgo("recurso") >= 0.4 and o.rasgo("peligro") < 0.3],` |
| `ida/sistemas/s2.py:241` | `_util` | `recurso` | `lambda o: o.rasgo("recurso") + o.rasgo("novedad"))` |
| `ida/sistemas/s2.py:241` | `_util` | `novedad` | `lambda o: o.rasgo("recurso") + o.rasgo("novedad"))` |
| `ida/sistemas/s2.py:251` | `actuar` | `novedad` | `propuestas.append(Propuesta(Verbo.MOVER, nuevo.id, acotar(0.15 + 0.25 * apertura * nuevo.rasgo("novedad")), 0.5,` |
| `ida/sistemas/s2.py:255` | `actuar` | `recurso` | `propuestas.append(Propuesta(Verbo.COGER, util.id, acotar(0.2 + 0.3 * apertura * util.rasgo("recurso")), 0.5,` |
| `ida/sistemas/s2.py:285` | `_puerta` | `peligro` | `puerta = next((lugar for lugar in lugares(ctx) if lugar.id == salto and lugar.rasgo("peligro") < umbral_p), None)` |
| `ida/sistemas/s2.py:328` | `_plan` | `nutritivo` | `if _peligro(ctx) >= 0.4 or hambre < 0.35 or any(o.rasgo("nutritivo") >= 0.3 for o in objetos(ctx)):` |
| `ida/sistemas/s2.py:348` | `_plan` | `peligro` | `puerta = next((lugar for lugar in lugares(ctx) if lugar.id == salto and lugar.rasgo("peligro") < 0.6), None) if salto else None` |
| `ida/sistemas/s2.py:359` | `_candidatos_plan` | `nutritivo` | `if _peligro(ctx) >= 0.4 or hambre < 0.35 or any(o.rasgo("nutritivo") >= 0.3 for o in objetos(ctx)):` |
| `ida/sistemas/s2.py:395` | `fallido` | `peligro` | `return not any(lugar.id == paso["meta"] and lugar.rasgo("peligro") < 0.6 for lugar in lugares(ctx))` |
| `ida/sistemas/s2.py:410` | `actuar` | `peligro` | `puerta = next((lugar for lugar in lugares(ctx) if lugar.id == paso["meta"] and lugar.rasgo("peligro") < 0.6), None)` |
| `ida/sistemas/s3.py:69` | `reactiva` | `novedad` | `if o.rasgo("novedad") >= 0.6:` |
| `ida/sistemas/s3.py:203` | `actuar` | `peligro` | `salida = mejor(lugares(ctx), lambda lugar: -lugar.rasgo("peligro"))` |
| `ida/sistemas/s3.py:227` | `actuar` | `peligro` | `destino = mejor(lugares(ctx), lambda lugar: lugar.rasgo("nutritivo") - 1.5 * lugar.rasgo("peligro"))` |
| `ida/sistemas/s3.py:227` | `actuar` | `nutritivo` | `destino = mejor(lugares(ctx), lambda lugar: lugar.rasgo("nutritivo") - 1.5 * lugar.rasgo("peligro"))` |
| `ida/sistemas/s3.py:228` | `actuar` | `nutritivo` | `if destino is not None and destino.rasgo("nutritivo") > 0:` |
| `ida/sistemas/s3.py:276` | `reactiva` | `nutritivo` | `comestibles = [o for o in objetos(ctx) if o.rasgo("nutritivo") >= 0.3]` |
| `ida/sistemas/s3.py:583` | `ir_por_el_mapa` | `peligro` | `puerta = next((lugar for lugar in lugares(ctx) if _pos(lugar) == primero and lugar.rasgo("peligro") < 0.5), None)` |
| `ida/sistemas/s3.py:597` | `acercarse_a_clase` | `peligro` | `sitios = [lugar for lugar in lugares(ctx) if lugar.rasgo("peligro") < 0.5]` |
| `ida/sistemas/s3.py:955` | `_ejecutar` | `peligro` | `sitio = mejor([lugar for lugar in lugares(ctx) if lugar.rasgo("peligro") < 0.5], lambda lugar: lugar.rasgo("novedad"))` |
| `ida/sistemas/s3.py:955` | `_ejecutar` | `novedad` | `sitio = mejor([lugar for lugar in lugares(ctx) if lugar.rasgo("peligro") < 0.5], lambda lugar: lugar.rasgo("novedad"))` |
| `ida/sistemas/s3.py:981` | `_explorar_efectos` | `peligro` | `if ctx.latido % self.CADA_EXPLORACION or any(p.rasgo("peligro") > 0.0 for p in _cosas(ctx)):` |

## D. Activaciones condicionales e interruptores

**Comando:** `git grep -n -E "(aliestesia|cobijo|mecanismos\.|peligro_aprendido|if\s+.*perfil\.|if\s+.*(obs|observacion).*is\s+None|if\s+.*is\s+None.*(obs|observacion))" -- ida/core ida/sistemas`

| fichero:línea | función | línea literal |
|---|---|---|
| `ida/core/estrategia.py:100` | `<módulo>` | `Con ``Perfil.mecanismos.plan``, la cadena se construye al activarse (``construir``) y se guarda en` |
| `ida/core/estrategia.py:122` | `paso` | `if not ctx.perfil.mecanismos.plan:` |
| `ida/core/latido.py:53` | `__init__` | `self.soma = Soma(vitales_propios=tuple(VITALES) if self.perfil.vitales_propios else ())` |
| `ida/core/latido.py:134` | `latir` | `self._peligro_aprendido(ctx)` |
| `ida/core/latido.py:142` | `latir` | `if self.con_experiencia and self.perfil.mecanismos.expectativa:` |
| `ida/core/latido.py:160` | `latir` | `if Verbo.DORMIR in self.verbos and self.perfil.duerme and min(soma.energia, soma.descanso) <= 5.0:` |
| `ida/core/latido.py:186` | `latir` | `if self.perfil.mecanismos.buffer:` |
| `ida/core/latido.py:228` | `_aprender` | `if self.perfil.aliestesia:` |
| `ida/core/latido.py:243` | `_peligro_aprendido` | `def _peligro_aprendido(self, ctx: Contexto) -> None:` |
| `ida/core/latido.py:247` | `_peligro_aprendido` | `Deja ``ctx.extra["peligro_aprendido"]`` para las estrategias que usan lo aprendido (``Afrontar``)."""` |
| `ida/core/latido.py:250` | `_peligro_aprendido` | `if obs is None or aqui is None or any("peligro" in e.rasgos for e in obs.entidades):` |
| `ida/core/latido.py:273` | `_peligro_aprendido` | `ctx.extra["peligro_aprendido"] = True` |
| `ida/core/latido.py:276` | `_aprender_satisface` | `"""Paso 0b (aliestesia), aprendizaje por contingencia: qué necesidades subieron respecto al latido anterior` |
| `ida/core/latido.py:298` | `_aprender_mapa` | `if obs is None:` |
| `ida/core/latido.py:354` | `_situacion_inventario` | `if obs is None or obs.inventario is None:` |
| `ida/core/latido.py:490` | `_episodio` | `if maximo >= self.perfil.umbral_apertura_episodio or sorpresa or d_vit >= 2.0:` |
| `ida/core/latido.py:507` | `_episodio` | `if longitud >= self.perfil.latidos_por_episodio or calma or soma.dormido or not soma.esta_vivo:` |
| `ida/core/latido.py:513` | `_episodio` | `if self.con_experiencia and self.perfil.hogar and ctx.observacion is not None:` |
| `ida/core/latido.py:528` | `vivir` | `self.memoria.consolidar(self.ciclo, reduccion=self.perfil.mecanismos.reduccion)` |
| `ida/core/latido.py:529` | `vivir` | `if self.perfil.mecanismos.consolidacion:` |
| `ida/core/latido.py:543` | `vivir` | `if self.memoria.lectura_activa and not self.perfil.tiempo_real:` |
| `ida/core/latido.py:548` | `vivir` | `if self.perfil.tiempo_real:          # marcapasos: el mundo no espera` |
| `ida/core/latido.py:552` | `vivir` | `if self.con_experiencia and self.perfil.mecanismos.consolidacion and not self.perfil.duerme:` |
| `ida/core/memoria.py:286` | `<módulo>` | `"""Paso 0b (aliestesia): cuánto satisface comer algo de ``clase`` la ``necesidad``, en [0, 1].` |
| `ida/core/memoria.py:380` | `__init__` | `# Paso 0b (aliestesia): qué necesidad satisface comer cada clase, del manual y de la experiencia.` |
| `ida/core/memoria.py:1034` | `<módulo>` | `# --- aliestesia: qué necesidad satisface cada clase (paso 0b) ---------------` |
| `ida/core/mundo.py:139` | `aliestesia` | `def aliestesia(self) -> bool:` |
| `ida/core/peligro.py:3` | `<módulo>` | `Con ``Perfil.mecanismos.peligro_aprendido``, y solo en un mundo que da posiciones (ubicación ``<nombre>_x_y`` y` |
| `ida/core/sentidos.py:52` | `reactiva` | `if ctx.observacion is None:` |
| `ida/sistemas/comun.py:74` | `proactiva` | `if not (ctx.perfil.mecanismos.expectativa and ctx.con_experiencia and ctx.memoria.activa):` |
| `ida/sistemas/comun.py:195` | `reactiva` | `if ctx.latido - c["inicio"] >= perfil.duracion_reflejo:` |
| `ida/sistemas/comun.py:204` | `reactiva` | `plan = est.estado_plan(p) if perfil.mecanismos.plan and isinstance(definicion, est.Plan) else None` |
| `ida/sistemas/proteger.py:4` | `<módulo>` | ```cobijo``, nada de esto actúa.` |
| `ida/sistemas/proteger.py:10` | `<módulo>` | `\| Actuar      \| Proteger   \| (estrategia del impulso ``cobijo``) la acción del plan, quedarse dentro o abrir \|` |
| `ida/sistemas/proteger.py:41` | `<módulo>` | `COBIJO = "cobijo"` |
| `ida/sistemas/proteger.py:52` | `<módulo>` | `COSTE_SIN_SITIO = 3 * ALCANCE_SITIO   # horizonte del cobijo sin ningún sitio posible: estimación alta (ir y volver al` |
| `ida/sistemas/proteger.py:513` | `<módulo>` | `alostasis del cobijo) y su confianza (tasas estimadas de las acciones de cavar y cerrar), y las paredes que se pueden` |
| `ida/sistemas/proteger.py:550` | `reactiva` | `hogar = pos_de(ctx.memoria.hogar()) if ctx.perfil.hogar else None` |
| `ida/sistemas/proteger.py:555` | `reactiva` | `if ctx.perfil.hogar:` |
| `ida/sistemas/proteger.py:744` | `<módulo>` | `"""Estrategia general del impulso ``cobijo``: protegerse en un recinto.` |
| `ida/sistemas/proteger.py:746` | `<módulo>` | `- **Fuera:** si el cobijo pesa al menos tanto como el déficit de las necesidades que se satisfacen fuera, propone la` |
| `ida/sistemas/proteger.py:748` | `<módulo>` | `cobijo (anticipada por la alostasis); confianza = confianza del sitio × esa intensidad: la confianza de que protegerse` |
| `ida/sistemas/proteger.py:753` | `<módulo>` | `- **Dentro:** si el cobijo (o el riesgo de fuera, ``riesgo_exterior``) pesa al menos tanto como el déficit de cualquier` |
| `ida/sistemas/proteger.py:756` | `<módulo>` | `que además devuelve el material). Cuando el cobijo ya no pide nada (de día), Proteger se cierra y la salida la` |
| `ida/sistemas/proteger.py:763` | `<módulo>` | `agotable = False         # protegerse no baja el déficit del cobijo (la noche sigue): no se agota por falta de progreso` |
| `ida/sistemas/proteger.py:779` | `pedir` | `planificador con urgencia = intensidad anticipada del cobijo. No se pide si otra necesidad de fuera pesa más, ni si` |
| `ida/sistemas/proteger.py:784` | `pedir` | `cobijo, _, otras = self._intensidades(ctx)` |
| `ida/sistemas/proteger.py:785` | `pedir` | `if otras > cobijo or self._cede(ctx):` |
| `ida/sistemas/proteger.py:787` | `pedir` | `return [{"objeto": k, "cantidad": n, "urgencia": cobijo, "motivo": f"proteger: {r.carga['explicacion']}"}` |
| `ida/sistemas/proteger.py:792` | `_intensidades` | `"""Intensidad (anticipada) del cobijo y, de las necesidades «de fuera», la de mayor déficit actual (nombre y déficit).` |
| `ida/sistemas/proteger.py:796` | `_intensidades` | `cobijo = float(imp[COBIJO].carga["intensidad"]) if COBIJO in imp else 0.0` |
| `ida/sistemas/proteger.py:800` | `_intensidades` | `return cobijo, nombre, deficit` |
| `ida/sistemas/proteger.py:807` | `decidir` | `cobijo, otra, otras = self._intensidades(ctx)` |
| `ida/sistemas/proteger.py:809` | `decidir` | `if max(cobijo, riesgo_exterior(ctx)) >= otras or not c["abrir"]:` |
| `ida/sistemas/proteger.py:811` | `decidir` | `self.proponer(ctx, verbo, "", cobijo, acotar(cobijo), f"proteger: dentro, {verbo.value.lower()}")` |
| `ida/sistemas/proteger.py:813` | `decidir` | `_proponer_abrir(self, ctx, c, "proteger", otra, otras, cobijo)` |
| `ida/sistemas/proteger.py:816` | `decidir` | `if accion is None or otras > cobijo:` |
| `ida/sistemas/proteger.py:818` | `decidir` | `self.proponer(ctx, accion["verbo"], accion["objetivo"], cobijo, acotar(float(c["confianza"]) * cobijo),` |
| `ida/sistemas/proteger.py:831` | `_proponer_abrir` | `cobijo: float) -> None:` |
| `ida/sistemas/proteger.py:838` | `_proponer_abrir` | `f"{origen}: {que} ({necesidad} {deficit:.2f} > cobijo {cobijo:.2f})", clase=pared["clase"])` |
| `ida/sistemas/proteger.py:845` | `<módulo>` | `Quedarse pesa lo que el cobijo y lo que el riesgo de salir (``riesgo_exterior``: el peligro percibido, si llega al umbral` |
| `ida/sistemas/proteger.py:846` | `<módulo>` | `de miedo). Es la misma regla con la que ``Proteger`` abre de noche, pero desde la necesidad. De día el cobijo no pide` |
| `ida/sistemas/proteger.py:869` | `elegible` | `cobijo, _, _ = Proteger._intensidades(ctx)` |
| `ida/sistemas/proteger.py:870` | `elegible` | `return deficit > max(cobijo, riesgo_exterior(ctx))` |
| `ida/sistemas/proteger.py:878` | `decidir` | `cobijo, _, _ = Proteger._intensidades(ctx)` |
| `ida/sistemas/proteger.py:879` | `decidir` | `_proponer_abrir(self, ctx, r.carga, "salir del recinto", impulso, deficit, cobijo)` |
| `ida/sistemas/s1.py:10` | `<módulo>` | `\| Reaccionar  \| Impulso        \| Impulso: uno por necesidad que declara el mundo, más Seguridad (intensidad cruda; la del cobijo, anticipada: alostasis) \|` |
| `ida/sistemas/s1.py:68` | `reactiva` | `conceptos = ctx.perfil.mecanismos.conceptos and ctx.con_experiencia and ctx.memoria.activa` |
| `ida/sistemas/s1.py:163` | `satisface_de` | `previos = {n.nombre: (o.rasgo(n.rasgo) if n.rasgo else 0.0) for n in ctx.perfil.necesidades}` |
| `ida/sistemas/s1.py:171` | `<módulo>` | `"""Aliestesia (Cabanac, 1971; paso 0b, con ``Perfil.aliestesia``: un rasgo que satisface varias necesidades): el valor de algo` |
| `ida/sistemas/s1.py:173` | `<módulo>` | `necesidad ≥ ``SATISFACE_MIN``, el mismo filtro que sin aliestesia) y satisface alguna necesidad,` |
| `ida/sistemas/s1.py:174` | `<módulo>` | `deseo = Σ_n intensidad(n) · satisface(clase, n). Sin ``Perfil.aliestesia`` no produce nada."""` |
| `ida/sistemas/s1.py:180` | `reactiva` | `if not ctx.perfil.aliestesia:` |
| `ida/sistemas/s1.py:221` | `<módulo>` | `nada. Si salir o quedarse lo deciden el cobijo, el riesgo de fuera y las necesidades (``Proteger``, ``SalirDelRecinto``)."""` |
| `ida/sistemas/s1.py:307` | `<módulo>` | `salida). Solo con el peligro calculado por la base (``ctx.extra["peligro_aprendido"]``).` |
| `ida/sistemas/s1.py:341` | `evaluar` | `if ctx.extra.get("peligro_aprendido") and aqui is not None and Verbo.ATACAR in ctx.verbos:` |
| `ida/sistemas/s1.py:569` | `<módulo>` | `**Por necesidad** (paso 0b, con ``Perfil.aliestesia``): cada impulso al que sirve solo` |
| `ida/sistemas/s1.py:571` | `<módulo>` | `elige entre ello por el deseo (aliestesia) y su arousal sale de la intensidad del impulso de origen,` |
| `ida/sistemas/s1.py:664` | `elegible` | `if ctx.perfil.aliestesia:` |
| `ida/sistemas/s1.py:670` | `paso` | `if ctx.perfil.aliestesia:` |
| `ida/sistemas/s1.py:680` | `actuar` | `if ctx.perfil.aliestesia:` |
| `ida/sistemas/s1.py:750` | `<módulo>` | `**Alostasis** (paso 3, ``docs/ENCARGO_PASO3_PROTEGER.md``, 3.2): regulación por anticipación. Solo para el cobijo,` |
| `ida/sistemas/s1.py:822` | `reactiva` | `e = expectativa_ejecutada(ctx.onda, self.sistema) if ctx.perfil.mecanismos.expectativa else None` |
| `ida/sistemas/s2.py:87` | `activa` | `if ctx.perfil.mecanismos.evocacion:` |
| `ida/sistemas/s2.py:89` | `activa` | `if ctx.perfil.mecanismos.repaso:` |
| `ida/sistemas/s2.py:166` | `reactiva` | `if ctx.perfil.mecanismos.evocacion:   # bloque E, E5: lo recuperado, no la memoria` |
| `ida/sistemas/s2.py:271` | `_estado` | `hogar = ctx.memoria.hogar() if ctx.perfil.hogar else None` |
| `ida/sistemas/s2.py:333` | `_plan` | `if ctx.perfil.mecanismos.evocacion:   # bloque E, E5: lo recuperado (piezas Recuerdo), no la memoria` |
| `ida/sistemas/s2.py:361` | `_candidatos_plan` | `if ctx.perfil.mecanismos.evocacion:` |
| `ida/sistemas/s2.py:399` | `elegible` | `if ctx.perfil.mecanismos.plan:` |
| `ida/sistemas/s2.py:405` | `actuar` | `if ctx.perfil.mecanismos.plan:` |
| `ida/sistemas/s2.py:434` | `reactiva` | `e = expectativa_ejecutada(ctx.onda, self.sistema) if ctx.perfil.mecanismos.expectativa else None` |
| `ida/sistemas/s3.py:378` | `decidir` | `elif ctx.perfil.tiempo_real:` |

## E. Constantes en mayúsculas a nivel de módulo o de clase

**Comando:** `herramientas/inventario.py (AST sobre ida/core/*.py e ida/sistemas/*.py para constantes en mayúsculas a nivel módulo y clase)`

| fichero:línea | clase | nombre | valor literal |
|---|---|---|---|
| `ida/core/arquitectura.py:26` | `-` | `ETAPAS` | `("Sentir", "Interpretar", "Reaccionar", "Actuar")` |
| `ida/core/arquitectura.py:27` | `-` | `BARRIDOS` | `("reactiva", "activa", "proactiva")` |
| `ida/core/arquitectura.py:30` | `-` | `SIN_EXPECTATIVA` | `(Verbo.ACECHAR, Verbo.ESPERAR, Verbo.LEER)   # acciones sin efecto propio que predecir` |
| `ida/core/azar.py:6` | `-` | `T` | `TypeVar("T")` |
| `ida/core/biblioteca.py:12` | `Veredicto` | `AFIRMA` | `"afirma"` |
| `ida/core/biblioteca.py:13` | `Veredicto` | `NIEGA` | `"niega"` |
| `ida/core/biblioteca.py:14` | `Veredicto` | `NO_SABE` | `"no_sabe"` |
| `ida/core/biblioteca.py:15` | `Veredicto` | `INVALIDO` | `"invalido"` |
| `ida/core/biblioteca.py:19` | `EstadoLectura` | `PENDIENTE` | `"pendiente"` |
| `ida/core/biblioteca.py:20` | `EstadoLectura` | `DISPONIBLE` | `"disponible"` |
| `ida/core/biblioteca.py:21` | `EstadoLectura` | `LEIDO` | `"leido"` |
| `ida/core/biblioteca.py:22` | `EstadoLectura` | `INTERRUMPIDO` | `"interrumpido"` |
| `ida/core/biblioteca.py:23` | `EstadoLectura` | `SIN_RESPUESTA` | `"sin_respuesta"` |
| `ida/core/biblioteca.py:24` | `EstadoLectura` | `INVALIDO` | `"invalido"` |
| `ida/core/estrategia.py:30` | `-` | `ACTIVA` | `"activa"` |
| `ida/core/estrategia.py:31` | `-` | `COMPLETADA` | `"completada"        # la necesidad bajó del objetivo` |
| `ida/core/estrategia.py:32` | `-` | `SIN_OBJETO` | `"sin_objeto"        # dejó de ser elegible (no hay a qué aplicarla)` |
| `ida/core/estrategia.py:33` | `-` | `AGOTADA` | `"agotada"              # se abandona por esfuerzo sin progreso` |
| `ida/core/estrategia.py:34` | `-` | `TERMINADA` | `"terminada"          # un reflejo cumplió su duración fija` |
| `ida/core/estrategia.py:35` | `-` | `SUSTITUIDA` | `"sustituida"        # apareció una estrategia elegible más específica o mejor valorada` |
| `ida/core/estrategia.py:37` | `-` | `SUBIDA_AGOTAMIENTO` | `0.05        # por latido con progreso menor que el esperado, pasada la gracia` |
| `ida/core/estrategia.py:38` | `-` | `BAJADA_AGOTAMIENTO` | `0.10        # por latido con progreso igual o mayor que el esperado` |
| `ida/core/estrategia.py:107` | `Plan` | `REHACER` | `1` |
| `ida/core/latido.py:31` | `-` | `CANALES_SENSORES` | `{"Interocepcion", "Propiocepcion", "Exterocepcion", "Ambiente"}` |
| `ida/core/linaje.py:15` | `-` | `RASGOS_CARACTER` | `("apertura", "responsabilidad", "neuroticismo", "extraversion", "umbral_miedo")` |
| `ida/core/marcapasos.py:24` | `Marcapasos` | `FUERZA_POR_PIEZA` | `1.0   # potencia / amplitud` |
| `ida/core/marcapasos.py:25` | `Marcapasos` | `FACTOR_AMPLITUD` | `0.45   # amplitud = factor × amplitud base del perfil (escasez de atención)` |
| `ida/core/memoria.py:20` | `-` | `PERFILES_MEMORIA` | `{"apagada": 0, "ligera": 2, "completa": 5}   # K piezas guardadas por latido` |
| `ida/core/memoria.py:29` | `Proposicion` | `CONFIRMACIONES_MINIMAS` | `3` |
| `ida/core/memoria.py:30` | `Proposicion` | `CONFIANZA_DEMOSTRADA` | `0.7` |
| `ida/core/memoria.py:31` | `Proposicion` | `LATIDOS_SIN_REFUTAR` | `30` |
| `ida/core/memoria.py:32` | `Proposicion` | `DECAY` | `0.05             # bloque E, E4: caducidad por noche de c_exp (reducción nocturna ×0,95)` |
| `ida/core/memoria.py:33` | `Proposicion` | `DANO_SATURA` | `10.0       # pérdida de vitalidad con la que el arousal de daño llega a 1 (el doble de un envenenamiento grave)` |
| `ida/core/memoria.py:195` | `-` | `RADIO_PRUEBA` | `2   # paso 5: hasta esta distancia se prueba una acción con requisito de cercanía antes de caminar` |
| `ida/core/memoria.py:205` | `-` | `DIRECCIONES` | `((1, 0), (-1, 0), (0, 1), (0, -1))` |
| `ida/core/memoria.py:309` | `Satisface` | `PREVIO` | `3.0   # peso (en comidas) del previo que no viene del manual` |
| `ida/core/memoria.py:331` | `Memoria` | `MAX_NODOS_MAPA` | `200` |
| `ida/core/memoria.py:332` | `Memoria` | `EDAD_OLVIDO_MAPA` | `300` |
| `ida/core/memoria.py:542` | `Memoria` | `CAPACIDAD_DIURNO` | `256      # piezas que caben en el búfer diurno` |
| `ida/core/memoria.py:543` | `Memoria` | `CAPACIDAD_DIA` | `1000        # latidos que caben en el episodio del día` |
| `ida/core/memoria.py:560` | `Memoria` | `DIAS_GUARDADOS` | `30         # días que conserva el almacén de episodios del día` |
| `ida/core/memoria.py:561` | `Memoria` | `NODOS_POR_LATIDO` | `5        # piezas de un mismo latido que se relacionan entre sí al consolidar` |
| `ida/core/memoria.py:598` | `Memoria` | `MAX_INSTANCIAS` | `500        # instancias recordadas (se olvidan las vistas hace más tiempo)` |
| `ida/core/memoria.py:623` | `Memoria` | `MAX_MODELO` | `1000            # entradas (sistema, verbo, clase); se olvida la usada hace más tiempo` |
| `ida/core/memoria.py:624` | `Memoria` | `N_MAX_MODELO` | `10            # la media del modelo pesa como mucho 10 experiencias (sigue los cambios)` |
| `ida/core/memoria.py:625` | `Memoria` | `UMBRAL_SORPRESA` | `0.1        # error de predicción a partir del cual hay sorpresa` |
| `ida/core/memoria.py:626` | `Memoria` | `PARECIDO_CONCEPTO` | `0.2      # distancia máxima entre prototipos para generalizar de un concepto a otro` |
| `ida/core/memoria.py:692` | `Memoria` | `REPASO_FUERZA` | `1.1            # E6: refuerzo de un nodo repasado` |
| `ida/core/memoria.py:693` | `Memoria` | `REPASO_CONFIANZA` | `0.02        # E6: refuerzo de las hipótesis de la clase repasada` |
| `ida/core/memoria.py:694` | `Memoria` | `REPASO_VENTANA` | `100           # E6: latidos hacia atrás que cuentan como «reciente»` |
| `ida/core/memoria.py:871` | `Memoria` | `REDUCCION_GRAFO` | `0.9          # E4: factor nocturno sobre las fuerzas del grafo semántico` |
| `ida/core/memoria.py:872` | `Memoria` | `PODA_GRAFO` | `0.05              # E4: fuerza por debajo de la cual se poda un nodo o relación` |
| `ida/core/memoria.py:873` | `Memoria` | `REDUCCION_HIPOTESIS` | `0.95     # E4: factor nocturno de referencia (= 1 − Proposicion.DECAY); cada hipótesis usa su decay` |
| `ida/core/memoria.py:874` | `Memoria` | `PODA_HIPOTESIS` | `0.15          # E4: confianza por debajo de la cual se poda una hipótesis` |
| `ida/core/memoria.py:983` | `Memoria` | `CONFIANZA_MANUAL` | `0.8      # c_aut de lo que declara el manual (y confianza inicial de sus requisitos)` |
| `ida/core/memoria.py:984` | `Memoria` | `PESO_MANUAL` | `1.0           # w_aut del manual: pesa como una experiencia propia` |
| `ida/core/memoria.py:985` | `Memoria` | `PASO_CONFIANZA_REQUISITO` | `0.1` |
| `ida/core/memoria.py:986` | `Memoria` | `MAX_INTENTOS` | `50           # intentos fallidos recordados por (verbo, objetivo); se olvidan los más antiguos` |
| `ida/core/memoria.py:987` | `Memoria` | `FALLOS_BLOQUEO` | `3          # paso 5: fallos seguidos sin ningún éxito que bloquean una acción` |
| `ida/core/memoria.py:1070` | `Memoria` | `VENTANA_BASE` | `10   # latidos de la media móvil de la línea base (media exacta mientras haya menos): lo reciente` |
| `ida/core/mundo.py:83` | `-` | `NECESIDADES_BASE` | `(` |
| `ida/core/mundo.py:108` | `-` | `MEMORIA_E` | `MecanismosMemoria(buffer=True, consolidacion=True, conceptos=True, reduccion=True, evocacion=True, repaso=True)` |
| `ida/core/mundo.py:110` | `-` | `MEMORIA_EF` | `MecanismosMemoria(buffer=True, consolidacion=True, conceptos=True, reduccion=True, evocacion=True, repaso=True,` |
| `ida/core/onda.py:57` | `-` | `EXCEPCIONES_TRANSITORIAS` | `{}` |
| `ida/core/peligro.py:52` | `-` | `VITALIDAD_MAXIMA` | `100.0` |
| `ida/core/peligro.py:53` | `-` | `DANO_PREVIO` | `VITALIDAD_MAXIMA * 2.0 / 9.0   # daño desconocido de lo peligroso: 2 de 9 unidades de vitalidad (declarado)` |
| `ida/core/peligro.py:54` | `-` | `PESO_PREVIO` | `2.0                            # peso (en daños) del previo` |
| `ida/core/peligro.py:55` | `-` | `VENTANA` | `20                                 # media móvil: los últimos ~20 daños de cada clase` |
| `ida/core/peligro.py:56` | `-` | `TASA_PREVIA` | `0.5                            # daños por latido de exposición, sin datos (pesimista)` |
| `ida/core/peligro.py:57` | `-` | `PESO_TASA` | `2.0                              # peso (en latidos) del previo de la tasa` |
| `ida/core/peligro.py:58` | `-` | `GOLPES_PREVIO` | `10.0                         # golpes para derribar algo sin datos (pesimista: así no se lucha)` |
| `ida/core/peligro.py:59` | `-` | `EMISION_MINIMA` | `0.6                         # ΔP a partir del cual X emite Y` |
| `ida/core/peligro.py:60` | `-` | `JUNTO_MINIMO` | `3                             # apariciones de Y junto a una X mínimas para decidirlo` |
| `ida/core/peligro.py:61` | `-` | `MAX_RECORRIDOS` | `10` |
| `ida/core/peligro.py:62` | `-` | `MAX_DERRIBOS` | `30` |
| `ida/core/peligro.py:63` | `-` | `MARGEN_REDUCTOR` | `0.15                       # razón de golpes con / sin el objeto por debajo de 1 − margen: reduce` |
| `ida/core/peligro.py:64` | `-` | `MINIMO_LEGADO` | `2                            # observaciones mínimas para pasar al legado` |
| `ida/core/peligro.py:65` | `-` | `PELIGRO_PREVIO` | `0.8                         # peligro del previo del manual a salud completa (fija la escala)` |
| `ida/core/peligro.py:66` | `-` | `MARGEN_LUGAR` | `3                             # el peligro de un lugar se anula a alcance + 3 casillas` |
| `ida/core/peligro.py:67` | `-` | `ESCALA` | `(DANO_PREVIO / VITALIDAD_MAXIMA) * (1.0 / PELIGRO_PREVIO - 1.0)   # C de g(x) = x / (x + C)` |
| `ida/core/persistencia.py:10` | `-` | `ESQUEMA` | `"""` |
| `ida/core/pieza.py:6` | `-` | `MAX_REGISTRO` | `16   # entradas del registro de cambios que se conservan por pieza (las más recientes)` |
| `ida/core/sentidos.py:91` | `Tribunal` | `EMPATE` | `0.02` |
| `ida/core/sentidos.py:92` | `Tribunal` | `PLUS_ACTIVA` | `0.1     # plus a la acción de la estrategia en curso, × (1 − agotamiento) × (1 − progreso)` |
| `ida/core/sentidos.py:93` | `Tribunal` | `UMBRAL_ACECHO` | `0.35` |
| `ida/core/soma.py:9` | `-` | `VITALES` | `("vitalidad", "alimentacion", "energia", "descanso")` |
| `ida/core/soma.py:28` | `Soma` | `DOPAMINA_BASAL` | `35.0` |
| `ida/core/soma.py:29` | `Soma` | `HAMBRE_CRITICA` | `15.0` |
| `ida/core/vocabulario.py:18` | `Verbo` | `MOVER` | `"MOVER"        # ir a un lugar` |
| `ida/core/vocabulario.py:19` | `Verbo` | `COMER` | `"COMER"        # ingerir algo (comida, bebida, bytes...)` |
| `ida/core/vocabulario.py:20` | `Verbo` | `ATACAR` | `"ATACAR"      # dañar una entidad` |
| `ida/core/vocabulario.py:21` | `Verbo` | `COGER` | `"COGER"        # recoger o recolectar algo` |
| `ida/core/vocabulario.py:22` | `Verbo` | `SOLTAR` | `"SOLTAR"      # dejar lo que se lleva` |
| `ida/core/vocabulario.py:23` | `Verbo` | `USAR` | `"USAR"          # fabricar, colocar o usar algo (la carga dice qué)` |
| `ida/core/vocabulario.py:24` | `Verbo` | `DORMIR` | `"DORMIR"      # dormir` |
| `ida/core/vocabulario.py:25` | `Verbo` | `ESPERAR` | `"ESPERAR"    # no hacer nada este latido` |
| `ida/core/vocabulario.py:26` | `Verbo` | `ACECHAR` | `"ACECHAR"    # interno: el Tribunal aún no se decide` |
| `ida/core/vocabulario.py:27` | `Verbo` | `LEER` | `"LEER"          # interno: atención sostenida en consulta a biblioteca` |
| `ida/core/vocabulario.py:31` | `-` | `RASGOS` | `(` |
| `ida/core/vocabulario.py:45` | `Relacion` | `NUTRITIVO` | `"nutre"` |
| `ida/core/vocabulario.py:46` | `Relacion` | `PELIGROSO` | `"hace daño"` |
| `ida/core/vocabulario.py:47` | `Relacion` | `UTIL` | `"sirve"` |
| `ida/core/vocabulario.py:51` | `EstadoSaber` | `HIPOTESIS` | `"hipótesis"` |
| `ida/core/vocabulario.py:52` | `EstadoSaber` | `DEMOSTRADA` | `"demostrada"` |
| `ida/core/vocabulario.py:53` | `EstadoSaber` | `REFUTADA` | `"refutada"` |
| `ida/core/vocabulario.py:57` | `Afecto` | `CALMA` | `"CALMA"` |
| `ida/core/vocabulario.py:58` | `Afecto` | `CURIOSIDAD` | `"CURIOSIDAD"` |
| `ida/core/vocabulario.py:59` | `Afecto` | `ALERTA` | `"ALERTA"` |
| `ida/core/vocabulario.py:60` | `Afecto` | `MIEDO` | `"MIEDO"` |
| `ida/core/vocabulario.py:61` | `Afecto` | `PANICO` | `"PANICO"` |
| `ida/core/vocabulario.py:62` | `Afecto` | `CANSANCIO` | `"CANSANCIO"` |
| `ida/core/vocabulario.py:63` | `Afecto` | `DORMIDO` | `"DORMIDO"` |
| `ida/sistemas/comun.py:10` | `-` | `ALCANCE` | `0.9          # proximidad a partir de la cual algo está al alcance` |
| `ida/sistemas/comun.py:11` | `-` | `MAX_OBJETOS` | `7        # atención limitada: 7 ± 2 objetos por latido` |
| `ida/sistemas/comun.py:56` | `-` | `PESO_PREDICCION` | `0.5   # bloque F, F1: peso del error de predicción con signo en el feedback de S1 y S2` |
| `ida/sistemas/comun.py:67` | `Anticipacion` | `POTENCIA_MINIMA` | `0.25` |
| `ida/sistemas/comun.py:169` | `Estrategia` | `VALOR_INICIAL` | `0.5` |
| `ida/sistemas/comun.py:170` | `Estrategia` | `TASA` | `0.5` |
| `ida/sistemas/comun.py:171` | `Estrategia` | `EXPLORACION` | `0.2` |
| `ida/sistemas/comun.py:172` | `Estrategia` | `MARGEN_SUSTITUCION` | `0.2` |
| `ida/sistemas/proteger.py:41` | `-` | `COBIJO` | `"cobijo"` |
| `ida/sistemas/proteger.py:42` | `-` | `MAX_INTERIOR` | `3          # un recinto tiene 1-3 casillas (encargo, sección 2)` |
| `ida/sistemas/proteger.py:43` | `-` | `ALCANCE_SITIO` | `15        # pasos máximos hasta un sitio candidato (3.3)` |
| `ida/sistemas/proteger.py:44` | `-` | `MAX_PASOS_POSTURA` | `12    # buscador de 3.1: «qué secuencia de MOVER me deja en A mirando a C»` |
| `ida/sistemas/proteger.py:45` | `-` | `PROFUNDIDAD_PLAN` | `30     # acciones máximas del plan local de un sitio (cavar, moverse, cerrar)` |
| `ida/sistemas/proteger.py:46` | `-` | `MAX_ESTADOS` | `6000        # coste de cálculo: estados máximos por búsqueda` |
| `ida/sistemas/proteger.py:47` | `-` | `CANDIDATOS_EXACTOS` | `6    # sitios más baratos por la estimación rápida que se planifican del todo` |
| `ida/sistemas/proteger.py:48` | `-` | `CADA_EVALUACION` | `5       # latidos entre evaluaciones completas de sitios (entretanto se replanifica el actual)` |
| `ida/sistemas/proteger.py:49` | `-` | `MARGEN_SITIO` | `0.25       # histéresis: otro sitio sustituye al actual si cuesta al menos un 25 % menos...` |
| `ida/sistemas/proteger.py:50` | `-` | `MARGEN_SITIO_MIN` | `3.0    # ...y al menos 3 pasos menos` |
| `ida/sistemas/proteger.py:51` | `-` | `BONO_HOGAR` | `5.0          # preferencia por el recinto recordado (hogar), en pasos` |
| `ida/sistemas/proteger.py:52` | `-` | `COSTE_SIN_SITIO` | `3 * ALCANCE_SITIO   # horizonte del cobijo sin ningún sitio posible: estimación alta (ir y volver al` |
| `ida/sistemas/s1.py:78` | `-` | `ENCUENTROS_HABITUACION` | `20      # avistamientos sin daño para la familiaridad completa (como en Patron)` |
| `ida/sistemas/s1.py:79` | `-` | `HABITUACION_MAX` | `0.4            # la amenaza aparente baja hasta un 40 % con la familiaridad` |
| `ida/sistemas/s1.py:80` | `-` | `SENSIBILIZACION_MAX` | `0.5        # tras un daño, la amenaza sube hasta un 50 % con su confianza` |
| `ida/sistemas/s1.py:144` | `-` | `SATISFACE_MIN` | `0.3   # paso 0b: a partir de aquí algo satisface una necesidad (como ``nutritivo`` ≥ 0,3 hoy)` |
| `ida/sistemas/s1.py:198` | `-` | `SEGURIDAD` | `"seguridad"` |
| `ida/sistemas/s1.py:261` | `-` | `RESERVA` | `100.0 * 3.0 / 9.0   # paso 6b: vitalidad que una lucha debe dejar intacta (3 de 9, declarado)` |
| `ida/sistemas/s1.py:726` | `Reflejo` | `UMBRAL_MIEDO_REFERENCIA` | `0.6` |
| `ida/sistemas/s1.py:743` | `-` | `VENTANA_TENDENCIA` | `50   # alostasis: latidos de la media móvil de la tendencia de cada déficit` |
| `ida/sistemas/s2.py:28` | `-` | `EXPLORACION` | `"exploracion"` |
| `ida/sistemas/s2.py:29` | `-` | `SEGURIDAD` | `"seguridad"      # impulso de S1 al que también sirve refugiarse` |
| `ida/sistemas/s2.py:81` | `Recuerdo` | `POTENCIA_MINIMA` | `0.25     # fracción de potencia que debe sobrar para recordar` |
| `ida/sistemas/s2.py:82` | `Recuerdo` | `POTENCIA_REPASO` | `0.5      # E6: fracción de potencia que debe sobrar para repasar` |
| `ida/sistemas/s2.py:202` | `-` | `CANSANCIO` | `"cansancio"` |
| `ida/sistemas/s3.py:128` | `Logica` | `PRIORIDAD` | `{"EVITAR": 0, "COMER": 1, "COGER": 2}` |
| `ida/sistemas/s3.py:137` | `-` | `PESO_AFECTIVO` | `0.1    # peso de la fuente afectiva frente a la confianza por experiencia y autoridad` |
| `ida/sistemas/s3.py:152` | `Creencia` | `MAX_CREENCIAS` | `64   # bloque E: la emisión queda acotada aunque la memoria crezca` |
| `ida/sistemas/s3.py:262` | `Impulso` | `FUERZA` | `0.2` |
| `ida/sistemas/s3.py:296` | `Estudio` | `COOLDOWN_LECTURA` | `15` |
| `ida/sistemas/s3.py:297` | `Estudio` | `MAX_HIPOTESIS_POR_LECTURA` | `2` |
| `ida/sistemas/s3.py:298` | `Estudio` | `L0` | `4` |
| `ida/sistemas/s3.py:299` | `Estudio` | `L1` | `2` |
| `ida/sistemas/s3.py:300` | `Estudio` | `MAX_LATIDOS_ESPERA_TR` | `10` |
| `ida/sistemas/s3.py:538` | `-` | `COSTE_RECORDADO` | `15.0     # ir adonde se recuerda algo que no se ve` |
| `ida/sistemas/s3.py:539` | `-` | `COSTE_POR_PROXIMIDAD` | `10.0` |
| `ida/sistemas/s3.py:540` | `-` | `MAX_RUTA_MAPA` | `40         # pasos máximos de una ruta por el mapa local hasta algo recordado` |
| `ida/sistemas/s3.py:541` | `-` | `COSTE_SIN_PRODUCTOR` | `2 * COSTE_RECORDADO   # reponer una unidad de algo que ninguna acción conocida da` |
| `ida/sistemas/s3.py:542` | `-` | `VECINAS` | `((1, 0), (-1, 0), (0, 1), (0, -1))` |
| `ida/sistemas/s3.py:656` | `PerseguirMetas` | `PROFUNDIDAD` | `5` |
| `ida/sistemas/s3.py:657` | `PerseguirMetas` | `AROUSAL` | `0.5` |
| `ida/sistemas/s3.py:658` | `PerseguirMetas` | `CADA_EXPLORACION` | `5          # latidos entre pruebas de efectos` |
| `ida/sistemas/s3.py:659` | `PerseguirMetas` | `VERBOS_PLAN` | `(Verbo.USAR, Verbo.COGER, Verbo.COMER)` |
| `ida/sistemas/s3.py:660` | `PerseguirMetas` | `SIN_ACERCARSE` | `8             # propuestas seguidas de MOVER al mismo destino sin que baje la distancia...` |
| `ida/sistemas/s3.py:661` | `PerseguirMetas` | `APARCAR` | `30                  # ...que lo dejan aparcado durante estos latidos` |
| `ida/sistemas/s3.py:992` | `-` | `SABER` | `"saber"` |
| `ida/sistemas/s3.py:993` | `-` | `INTENSIDAD_INTENCION_DEL_MUNDO` | `0.5` |

## F. Escrituras en la Memoria fuera de ida/core/memoria.py

**Comando:** `git grep -n -E "\.(aprender_|ver_|registrar_|guardar|aplicar_|olvidar|cierres\.add|cierres\.discard|lectura_activa\s*=|ultimo_fin_lectura\s*=|yo_previo\s*=)" -- ida/core ida/sistemas ":(exclude)ida/core/memoria.py"`

| fichero:línea | función que llama | método | línea literal |
|---|---|---|---|
| `ida/core/latido.py:205` | `_aprender` | `registrar_transicion` | `self.memoria.registrar_transicion(self._ubicacion_previa, ubicacion, ctx.latido)` |
| `ida/core/latido.py:210` | `_aprender` | `registrar_donde` | `self.memoria.registrar_donde(e.clase, ubicacion, ctx.latido)` |
| `ida/core/latido.py:220` | `_aprender` | `registrar_donde` | `self.memoria.registrar_donde(clase_obj, ubicacion, ctx.latido)` |
| `ida/core/latido.py:225` | `_aprender` | `aprender_requisito` | `self.memoria.aprender_requisito(c["verbo"], objetivo, self._antes_accion[0], ahora_inv[0], self._antes_accion[1],` |
| `ida/core/latido.py:231` | `_aprender` | `registrar_meta` | `self.memoria.registrar_meta(c["verbo"], objetivo, bool(c.get("exito")),` |
| `ida/core/latido.py:282` | `_aprender_satisface` | `aprender_satisface` | `self.memoria.aprender_satisface(str(c["clase"]), subidas)` |
| `ida/core/latido.py:322` | `_aprender_mapa` | `aprender_cuerpo` | `mem.aprender_cuerpo("mover", libre, aqui == destino, cara == direccion)` |
| `ida/core/latido.py:324` | `_aprender_mapa` | `aprender_cuerpo` | `mem.aprender_cuerpo("interactuar", True, aqui != p0, cara == direccion)` |
| `ida/core/latido.py:329` | `_aprender_mapa` | `aprender_transformacion` | `mem.aprender_transformacion(verbo, objetivo, antes, despues)   # también «no cambió», si la acción salió` |
| `ida/core/latido.py:331` | `_aprender_mapa` | `cierres.add` | `mem.cierres.add(destino)` |
| `ida/core/latido.py:333` | `_aprender_mapa` | `cierres.discard` | `mem.cierres.discard(destino)` |
| `ida/core/latido.py:346` | `_aprender_mapa` | `ver_casillas` | `mem.ver_casillas(aqui, casillas, libres, ocupadas, peligros)` |
| `ida/core/latido.py:347` | `_aprender_mapa` | `yo_previo` | `mem.yo_previo = (aqui, cara)` |
| `ida/core/latido.py:464` | `_memoria_rapida` | `guardar_rapido` | `self.memoria.guardar_rapido(piezas)` |
| `ida/core/sentidos.py:61` | `reactiva` | `ver_clase` | `ctx.memoria.ver_clase(e.clase)` |
| `ida/sistemas/s2.py:344` | `_plan` | `olvidar_donde` | `ctx.memoria.olvidar_donde(clase)` |
| `ida/sistemas/s2.py:390` | `fallido` | `olvidar_donde` | `ctx.memoria.olvidar_donde(paso["clase"])    # llegó y no está` |
| `ida/sistemas/s3.py:316` | `decidir` | `lectura_activa` | `mem.lectura_activa = None` |
| `ida/sistemas/s3.py:317` | `decidir` | `ultimo_fin_lectura` | `mem.ultimo_fin_lectura = ctx.latido` |
| `ida/sistemas/s3.py:330` | `decidir` | `lectura_activa` | `mem.lectura_activa = None` |
| `ida/sistemas/s3.py:331` | `decidir` | `ultimo_fin_lectura` | `mem.ultimo_fin_lectura = ctx.latido` |
| `ida/sistemas/s3.py:339` | `decidir` | `lectura_activa` | `mem.lectura_activa = None` |
| `ida/sistemas/s3.py:340` | `decidir` | `ultimo_fin_lectura` | `mem.ultimo_fin_lectura = ctx.latido` |
| `ida/sistemas/s3.py:360` | `decidir` | `aplicar_autoridad` | `prop.aplicar_autoridad(` |
| `ida/sistemas/s3.py:375` | `decidir` | `lectura_activa` | `mem.lectura_activa = None` |
| `ida/sistemas/s3.py:376` | `decidir` | `ultimo_fin_lectura` | `mem.ultimo_fin_lectura = ctx.latido` |
| `ida/sistemas/s3.py:381` | `decidir` | `lectura_activa` | `mem.lectura_activa = None` |
| `ida/sistemas/s3.py:382` | `decidir` | `ultimo_fin_lectura` | `mem.ultimo_fin_lectura = ctx.latido` |
| `ida/sistemas/s3.py:416` | `decidir` | `lectura_activa` | `mem.lectura_activa = reg_prev` |
| `ida/sistemas/s3.py:459` | `decidir` | `lectura_activa` | `mem.lectura_activa = reg_nuevo` |

## G. Tiempo del mundo en estrategias y Componentes

**Comando:** `git grep -n -E "(ctx\.latido|\.t |\.t\)|\bpaso\b|\breloj\b|\bhora\b|\bdia\b)" -- ida/sistemas`

| fichero:línea | función | línea literal |
|---|---|---|
| `ida/sistemas/comun.py:116` | `<módulo>` | `"""Metas instrumentales (paso 3 de la fase de generalización): lo que piden al planificador las estrategias activas del` |
| `ida/sistemas/comun.py:154` | `<módulo>` | `sustituciones: las fija ``Definicion.paso`` en cada latido.` |
| `ida/sistemas/comun.py:195` | `reactiva` | `if ctx.latido - c["inicio"] >= perfil.duracion_reflejo:` |
| `ida/sistemas/comun.py:200` | `reactiva` | `cambios = est.avanzar(c, intensidad, p.id == ejecutada, ctx.latido, perfil.gracia_estrategia, perfil.ritmo_esperado_estrategia)` |
| `ida/sistemas/comun.py:212` | `reactiva` | `self.enfriando[(c["impulso"], c["nombre"])] = ctx.latido + perfil.enfriamiento_estrategia` |
| `ida/sistemas/comun.py:216` | `reactiva` | `self.enfriando[(c["impulso"], c["nombre"])] = ctx.latido + perfil.enfriamiento_estrategia` |
| `ida/sistemas/comun.py:224` | `reactiva` | `paso = definicion.paso(ctx, p)` |
| `ida/sistemas/comun.py:225` | `reactiva` | `if paso != c.get("paso"):` |
| `ida/sistemas/comun.py:226` | `reactiva` | `self.modificar(ctx, p, carga={"paso": paso})` |
| `ida/sistemas/comun.py:271` | `_disponibles` | `return elegibles, [d for d in elegibles if self.enfriando.get((impulso, d.nombre), -1) <= ctx.latido]` |
| `ida/sistemas/comun.py:291` | `_activar` | `p = est.nueva(self.sistema, definicion, impulso, intensidad, objetivo, ctx.latido)` |
| `ida/sistemas/comun.py:293` | `_activar` | `p = est.nueva(self.sistema, definicion, impulso, intensidad, objetivo, ctx.latido, paso=definicion.paso(ctx, p))` |
| `ida/sistemas/proteger.py:1` | `<módulo>` | `"""S1 · «Proteger X» con X = uno mismo: el refugio general (fase de generalización, paso 3).` |
| `ida/sistemas/proteger.py:9` | `<módulo>` | `\|             \|            \| (sin material, el primer paso para conseguirlo, del planificador de S3)                                 \|` |
| `ida/sistemas/proteger.py:570` | `reactiva` | `if ctx.latido - self._ultimo_requisitos >= CADA_EVALUACION:     # sin elección, tampoco se rehace antes` |
| `ida/sistemas/proteger.py:576` | `_coste_objeto` | `"""Pasos estimados por el planificador del paso 5 para tener una unidad más de ``objeto`` (None si nada lo da)."""` |
| `ida/sistemas/proteger.py:578` | `_coste_objeto` | `paso = self._planificador.conseguir(ctx, objeto, {**inv, objeto: 0.0})` |
| `ida/sistemas/proteger.py:579` | `_coste_objeto` | `cache[objeto] = None if paso is None else paso.coste + 1.0` |
| `ida/sistemas/proteger.py:587` | `_requisitos` | `unidad lo da el planificador del paso 5 (``PerseguirMetas.conseguir``). El plan del sitio se comprueba con el` |
| `ida/sistemas/proteger.py:590` | `_requisitos` | `self._ultimo_requisitos = ctx.latido` |
| `ida/sistemas/proteger.py:659` | `_elegir` | `if ctx.latido - self._ultima < CADA_EVALUACION and not perdido:` |
| `ida/sistemas/proteger.py:661` | `_elegir` | `self._ultima = ctx.latido` |
| `ida/sistemas/proteger.py:693` | `_primera` | `"""La acción de este latido: el primer paso de la ruta hasta la entrada o la primera acción del plan local."""` |
| `ida/sistemas/s1.py:53` | `reactiva` | `ctx, f"imagen_{ctx.latido}", arousal=foco.arousal if foco else 0.1,` |
| `ida/sistemas/s1.py:74` | `reactiva` | `ctx.memoria.instancia(p.id, p.clase, p.carga["rasgos"], ctx.latido)` |
| `ida/sistemas/s1.py:96` | `relacion_supervivencia` | `if dano is not None and dano.estado(ctx.latido) != EstadoSaber.REFUTADA:` |
| `ida/sistemas/s1.py:99` | `relacion_supervivencia` | `if (nutre is not None and nutre.confianza >= 0.5 and nutre.estado(ctx.latido) != EstadoSaber.REFUTADA) or atractivo > 0.05:` |
| `ida/sistemas/s1.py:144` | `<módulo>` | `SATISFACE_MIN = 0.3   # paso 0b: a partir de aquí algo satisface una necesidad (como ``nutritivo`` ≥ 0,3 hoy)` |
| `ida/sistemas/s1.py:171` | `<módulo>` | `"""Aliestesia (Cabanac, 1971; paso 0b, con ``Perfil.aliestesia``: un rasgo que satisface varias necesidades): el valor de algo` |
| `ida/sistemas/s1.py:261` | `<módulo>` | `RESERVA = 100.0 * 3.0 / 9.0   # paso 6b: vitalidad que una lucha debe dejar intacta (3 de 9, declarado)` |
| `ida/sistemas/s1.py:289` | `<módulo>` | `"""Seguridad (paso 6b): luchar o huir por evaluación, con lo aprendido en 6a` |
| `ida/sistemas/s1.py:302` | `<módulo>` | `falta un paso para el contacto y, más lejos, no se propone nada.` |
| `ida/sistemas/s1.py:365` | `paso` | `def paso(self, ctx: Contexto, estrategia: Pieza) -> Any:` |
| `ida/sistemas/s1.py:367` | `paso` | `return e["fase"] if e is not None else estrategia.carga.get("paso", 0)` |
| `ida/sistemas/s1.py:394` | `actuar` | `if v["d"] == 2 and Verbo.ESPERAR in ctx.verbos:     # le falta un paso para el contacto: esperarla, no irse` |
| `ida/sistemas/s1.py:569` | `<módulo>` | `**Por necesidad** (paso 0b, con ``Perfil.aliestesia``): cada impulso al que sirve solo` |
| `ida/sistemas/s1.py:584` | `<módulo>` | `# --- paso 0b: por necesidad ---------------------------------------------------------------` |
| `ida/sistemas/s1.py:636` | `_actuar_por_necesidad` | `paso = estrategia.carga.get("paso")` |
| `ida/sistemas/s1.py:637` | `_actuar_por_necesidad` | `if paso == COMER:` |
| `ida/sistemas/s1.py:642` | `_actuar_por_necesidad` | `if paso == ACERCARSE:` |
| `ida/sistemas/s1.py:655` | `_actuar_por_necesidad` | `if paso in (BUSCAR, ACERCARSE):` |
| `ida/sistemas/s1.py:669` | `paso` | `def paso(self, ctx: Contexto, estrategia: Pieza) -> str:` |
| `ida/sistemas/s1.py:682` | `actuar` | `paso = estrategia.carga.get("paso")` |
| `ida/sistemas/s1.py:683` | `actuar` | `if paso == COMER:` |
| `ida/sistemas/s1.py:688` | `actuar` | `if paso == ACERCARSE:` |
| `ida/sistemas/s1.py:700` | `actuar` | `if paso == BUSCAR:` |
| `ida/sistemas/s1.py:750` | `<módulo>` | `**Alostasis** (paso 3, ``docs/ENCARGO_PASO3_PROTEGER.md``, 3.2): regulación por anticipación. Solo para el cobijo,` |
| `ida/sistemas/s1.py:768` | `alostasis` | `"""Intensidad anticipada, tendencia y horizonte de cada necesidad (3.2 del encargo del paso 3).` |
| `ida/sistemas/s2.py:101` | `_repasar` | `for nodo, clase in ctx.memoria.recientes_para_repaso(ctx.latido):` |
| `ida/sistemas/s2.py:104` | `_repasar` | `ctx.memoria.repasar(nodo, clase, ctx.latido)` |
| `ida/sistemas/s2.py:107` | `_evocar` | `onda, mem, ahora = ctx.onda, ctx.memoria, ctx.latido` |
| `ida/sistemas/s2.py:125` | `_traer` | `carga={"clase": clase, "relacion": rel, "demostrada": prop.estado(ctx.latido) == EstadoSaber.DEMOSTRADA,` |
| `ida/sistemas/s2.py:127` | `_traer` | `ctx.memoria.reconsolidar((clase, rel), ctx.latido, arousal)` |
| `ida/sistemas/s2.py:169` | `reactiva` | `peligrosa = mem.demostrada(o.clase, Relacion.PELIGROSO, ctx.latido)` |
| `ida/sistemas/s2.py:295` | `paso` | `def paso(self, ctx: Contexto, estrategia: Pieza) -> str:` |
| `ida/sistemas/s2.py:300` | `actuar` | `if estrategia.carga.get("paso") == "descansar":` |
| `ida/sistemas/s2.py:315` | `<módulo>` | `a igualdad, fuerza del nodo en el grafo semántico) y fija la ruta completa del mapa más un paso` |
| `ida/sistemas/s2.py:316` | `<módulo>` | `final, encontrar la clase. Sorpresa (el paso falla): estar fuera de la ruta, no ver la puerta` |
| `ida/sistemas/s2.py:339` | `_plan` | `if rel == Relacion.NUTRITIVO and prop.confianza >= 0.55 and not ctx.memoria.demostrada(clase, Relacion.PELIGROSO, ctx.latido)),` |
| `ida/sistemas/s2.py:366` | `_candidatos_plan` | `if rel == Relacion.NUTRITIVO and prop.confianza >= 0.55 and not ctx.memoria.demostrada(clase, Relacion.PELIGROSO, ctx.latido)]` |
| `ida/sistemas/s2.py:381` | `cumplido` | `def cumplido(self, ctx: Contexto, paso: Dict[str, Any], estado: Dict[str, Any]) -> bool:` |
| `ida/sistemas/s2.py:382` | `cumplido` | `if paso["meta"] == "encontrar":` |
| `ida/sistemas/s2.py:383` | `cumplido` | `return any(o.clase == paso["clase"] for o in objetos(ctx))` |
| `ida/sistemas/s2.py:384` | `cumplido` | `return ctx.observacion is not None and ctx.observacion.ubicacion == paso["meta"]` |
| `ida/sistemas/s2.py:386` | `fallido` | `def fallido(self, ctx: Contexto, paso: Dict[str, Any], estado: Dict[str, Any]) -> bool:` |
| `ida/sistemas/s2.py:388` | `fallido` | `if paso["meta"] == "encontrar":` |
| `ida/sistemas/s2.py:389` | `fallido` | `if aqui == paso["en"]:` |
| `ida/sistemas/s2.py:390` | `fallido` | `ctx.memoria.olvidar_donde(paso["clase"])    # llegó y no está` |
| `ida/sistemas/s2.py:395` | `fallido` | `return not any(lugar.id == paso["meta"] and lugar.rasgo("peligro") < 0.6 for lugar in lugares(ctx))` |
| `ida/sistemas/s2.py:406` | `actuar` | `paso = paso_actual(estrategia)` |
| `ida/sistemas/s2.py:407` | `actuar` | `if paso is None or paso["meta"] == "encontrar":` |
| `ida/sistemas/s2.py:410` | `actuar` | `puerta = next((lugar for lugar in lugares(ctx) if lugar.id == paso["meta"] and lugar.rasgo("peligro") < 0.6), None)` |
| `ida/sistemas/s3.py:94` | `activa` | `estado = p.estado(ctx.latido)` |
| `ida/sistemas/s3.py:96` | `activa` | `carga={"clase": o.clase, "relacion": rel, "estado": estado, "texto": p.texto(ctx.latido)}))` |
| `ida/sistemas/s3.py:171` | `reactiva` | `estado = p.estado(ctx.latido)` |
| `ida/sistemas/s3.py:317` | `decidir` | `mem.ultimo_fin_lectura = ctx.latido` |
| `ida/sistemas/s3.py:326` | `decidir` | `if ctx.latido > reg.inicio:` |
| `ida/sistemas/s3.py:331` | `decidir` | `mem.ultimo_fin_lectura = ctx.latido` |
| `ida/sistemas/s3.py:340` | `decidir` | `mem.ultimo_fin_lectura = ctx.latido` |
| `ida/sistemas/s3.py:364` | `decidir` | `ctx.latido,` |
| `ida/sistemas/s3.py:376` | `decidir` | `mem.ultimo_fin_lectura = ctx.latido` |
| `ida/sistemas/s3.py:382` | `decidir` | `mem.ultimo_fin_lectura = ctx.latido` |
| `ida/sistemas/s3.py:408` | `decidir` | `if ctx.latido - mem.ultimo_fin_lectura < self.COOLDOWN_LECTURA:` |
| `ida/sistemas/s3.py:438` | `decidir` | `if p.estado(ctx.latido) == EstadoSaber.HIPOTESIS` |
| `ida/sistemas/s3.py:451` | `decidir` | `id=f"lec_{ctx.latido}",` |
| `ida/sistemas/s3.py:452` | `decidir` | `inicio=ctx.latido,` |
| `ida/sistemas/s3.py:546` | `ir_por_el_mapa` | `"""Un paso hacia la casilla recordada de ``clase`` más cercana por el mapa local de la memoria (paso 3), con el coste en` |
| `ida/sistemas/s3.py:549` | `ir_por_el_mapa` | ```MAX_RUTA_MAPA`` pasos, si ya está al lado o si el primer paso no es un lugar percibido sin peligro."""` |
| `ida/sistemas/s3.py:592` | `acercarse_a_clase` | `"""Un paso hacia la instancia visible más cercana de ``clase`` o, si no se ve, hacia donde se recuerda` |
| `ida/sistemas/s3.py:638` | `<módulo>` | `"""Estrategia general de S3 para la intención «progresar» (paso 5): encadena requisitos hacia atrás desde` |
| `ida/sistemas/s3.py:669` | `__init__` | `self._rutas_mapa: Dict[Tuple[int, str, frozenset], Optional[Paso]] = {}   # (latido, clase, aparcados) -> paso por el mapa` |
| `ida/sistemas/s3.py:672` | `_excluir` | `return frozenset(d for d, hasta in self._aparcados.items() if ctx.latido < hasta)` |
| `ida/sistemas/s3.py:674` | `_vigilar` | `def _vigilar(self, ctx: Contexto, paso: Paso) -> None:` |
| `ida/sistemas/s3.py:677` | `_vigilar` | `if paso.verbo != Verbo.MOVER or not paso.destino:` |
| `ida/sistemas/s3.py:681` | `_vigilar` | `if destino != paso.destino:` |
| `ida/sistemas/s3.py:682` | `_vigilar` | `self._seguimiento = (paso.destino, paso.distancia, 0)` |
| `ida/sistemas/s3.py:684` | `_vigilar` | `if paso.distancia is not None and (mejor_d is None or paso.distancia < mejor_d):` |
| `ida/sistemas/s3.py:685` | `_vigilar` | `self._seguimiento = (destino, paso.distancia, 0)` |
| `ida/sistemas/s3.py:689` | `_vigilar` | `self._aparcados[destino] = ctx.latido + self.APARCAR` |
| `ida/sistemas/s3.py:704` | `conseguir` | `"""Primer paso del plan más barato para tener una unidad más de ``objeto``: la mejor de las acciones cuyo efecto` |
| `ida/sistemas/s3.py:719` | `decidir` | `paso = self._resolver(ctx, (meta.verbo, meta.objetivo), inv, frozenset(), 0)` |
| `ida/sistemas/s3.py:720` | `decidir` | `if paso is None:` |
| `ida/sistemas/s3.py:723` | `decidir` | `if mejor_paso is None or paso.coste < mejor_paso.coste:` |
| `ida/sistemas/s3.py:724` | `decidir` | `mejor_paso, meta_mejor = paso, meta.objetivo` |
| `ida/sistemas/s3.py:747` | `_atender_peticiones` | `"""Metas instrumentales (``Peticion``): para cada objeto pedido que falta, el primer paso para conseguirlo, con el` |
| `ida/sistemas/s3.py:752` | `_atender_peticiones` | `paso = self.conseguir(ctx, objeto, sin)` |
| `ida/sistemas/s3.py:753` | `_atender_peticiones` | `if paso is None:` |
| `ida/sistemas/s3.py:755` | `_atender_peticiones` | `motivo = f"{p.carga['origen']}: pide {objeto}" + "".join(f" ← {m}" for m in paso.motivo)` |
| `ida/sistemas/s3.py:758` | `_atender_peticiones` | `self.proponer(ctx, paso.verbo, paso.objetivo, float(p.carga["urgencia"]), paso.confianza, motivo,` |
| `ida/sistemas/s3.py:759` | `_atender_peticiones` | `clase=paso.clase, **paso.datos)` |
| `ida/sistemas/s3.py:813` | `_con_consumo` | `def _con_consumo(self, ctx: Contexto, accion: Tuple[Verbo, str], paso: Optional[Paso], inv: Dict[str, float],` |
| `ida/sistemas/s3.py:818` | `_con_consumo` | `if paso is None or r is None:` |
| `ida/sistemas/s3.py:819` | `_con_consumo` | `return paso` |
| `ida/sistemas/s3.py:822` | `_con_consumo` | `paso.coste += -d * self._coste_unidad(ctx, k, inv, visitado \| {accion}, prof + 1)` |
| `ida/sistemas/s3.py:823` | `_con_consumo` | `return paso` |
| `ida/sistemas/s3.py:827` | `_coste_unidad` | `clave = (ctx.latido, objeto)` |
| `ida/sistemas/s3.py:841` | `_mejor_lote` | `"""El lote más barato por meta (paso, coste por meta, nombre, (estación, metas)). Un lote son las metas resueltas` |
| `ida/sistemas/s3.py:844` | `_mejor_lote` | `meta; se reparte entre las metas. El primer paso es el material («primero lo que se lleva»); con todo, ir a X o` |
| `ida/sistemas/s3.py:865` | `_mejor_lote` | `# Opciones para la estación: (paso si ya se tiene el material, coste, material propio).` |
| `ida/sistemas/s3.py:888` | `_mejor_lote` | `paso = primero if primero is not None else paso_est` |
| `ida/sistemas/s3.py:889` | `_mejor_lote` | `if paso is None:              # todo a mano y junto a X: lo hace la meta suelta, que es más barata` |
| `ida/sistemas/s3.py:894` | `_mejor_lote` | `mejor_lote = (Paso(paso.verbo, paso.objetivo, paso.clase, por_meta, paso.confianza, list(paso.motivo),` |
| `ida/sistemas/s3.py:895` | `_mejor_lote` | `dict(paso.datos), paso.destino, paso.distancia), por_meta, nombre, (x, frozenset(lote)))` |
| `ida/sistemas/s3.py:900` | `_colocar` | `"""El paso de colocar la estación, solo si ya se lleva su material y el del lote (si no, primero el material)."""` |
| `ida/sistemas/s3.py:908` | `_coste_material` | `de una unidad) y el primer paso: el plan más barato de lo que falta. None si algo no se sabe conseguir."""` |
| `ida/sistemas/s3.py:937` | `_por_el_mapa` | `clave = (ctx.latido, clase, self._excluir(ctx))` |
| `ida/sistemas/s3.py:948` | `_ejecutar` | `# Coste en intentos: 1 / tasa estimada. El primer intento ya cuenta como el paso (coste 0, como cualquier` |
| `ida/sistemas/s3.py:981` | `_explorar_efectos` | `if ctx.latido % self.CADA_EXPLORACION or any(p.rasgo("peligro") > 0.0 for p in _cosas(ctx)):` |
| `ida/sistemas/s3.py:1009` | `reactiva` | `saber = sum(1 for p in props if p.estado(ctx.latido) == EstadoSaber.HIPOTESIS) / len(props) if props else 0.0` |

## H. Adaptador de Crafter: cálculo de rasgos de Entidad

**Comando:** `inspección de ida/mundos/crafter.py en funciones que calculan rasgos de Entidad`

| fichero:línea | función | rasgo | atributos internos | línea literal |
|---|---|---|---|---|
| `ida/mundos/crafter.py:322` | `observar` | `proximidad` | self.radio, d (_dist con jugador.pos) | `"proximidad": 1.0 if d <= 1 else max(0.0, 1.0 - d / (2 * self.radio + 1)),` |
| `ida/mundos/crafter.py:323` | `observar` | `nutritivo` | self._nutritivo, self.nutritivos, obj.ripe | `"nutritivo": self._nutritivo(clase, obj),` |
| `ida/mundos/crafter.py:324` | `observar` | `recurso` | self.utiles, RECURSO_MANUAL | `"recurso": RECURSO_MANUAL if clase in self.utiles else 0.0,` |
| `ida/mundos/crafter.py:325` | `observar` | `agente` | obj (objeto del motor) | `"agente": 1.0 if obj is not None and clase != "planta" else 0.0,` |
| `ida/mundos/crafter.py:343` | `observar` | `lugar` | constante 1.0 | `celda = {"lugar": 1.0, "proximidad": 1.0, "nutritivo": nutritivo, "novedad": novedad}` |
| `ida/mundos/crafter.py:343` | `observar` | `proximidad` | constante 1.0 | `celda = {"lugar": 1.0, "proximidad": 1.0, "nutritivo": nutritivo, "novedad": novedad}` |
| `ida/mundos/crafter.py:343` | `observar` | `nutritivo` | deseables, self.radio, self._nutritivo, _dist | `celda = {"lugar": 1.0, "proximidad": 1.0, "nutritivo": nutritivo, "novedad": novedad}` |
| `ida/mundos/crafter.py:343` | `observar` | `novedad` | self.visitas, self.t | `celda = {"lugar": 1.0, "proximidad": 1.0, "nutritivo": nutritivo, "novedad": novedad}` |
| `ida/mundos/crafter.py:296` | `_nutritivo` | `nutritivo` | self.nutritivos, obj (getattr obj ripe) | `return NUTRITIVO_MANUAL` |

## I. Las 17 entradas pendientes del Mapa de Componentes

**Comando:** `análisis de doc-repositorio/06_MAPA_DE_COMPONENTES.md (17 entradas pendientes) y localización de código correspondiente`

| entrada | paso | fichero:rango | qué hay ahí |
|---|---|---|---|
| `Saliencia` | A3 | `ida/core/sentidos.py:54-62` | En Exterocepcion.reactiva: cálculo de saliencia (max entre peligro, nutritivo y novedad) asignado a arousal de la pieza |
| `Amenaza` | A3 | `ida/core/peligro.py:1-428; ida/core/latido.py:243-273` | Clases Encuentro, ClasePeligrosa, Peligros, PeligroAprendido y método Organismo._peligro_aprendido |
| `ValoracionCrafter` | A4 | `ida/mundos/crafter.py:290-296, 321-326, 337-344` | Método _nutritivo y asignación de rasgos nutritivo, recurso y novedad a entidades y celdas en observar() |
| `Regulacion` | A3 | `ida/core/marcapasos.py:23-44` | Clase Marcapasos y método Marcapasos.ritmo (frecuencia, amplitud y potencia según soma) |
| `Apetencia` | A6 | `ida/sistemas/s1.py:170-193, 837` | Clase Apetencia(Componente) en S1.Interpretar; montada en Modulo('Interpretar', ...) en s1.py:837 para todos los mundos |
| `Recinto` | A6 | `ida/sistemas/s1.py:195-200, 837` | Clase Recinto(Componente) en S1.Interpretar; montada en Modulo('Interpretar', ...) en s1.py:837 para todos los mundos |
| `MapaLocal` | A5 | `ida/core/memoria.py:1085-1135` | Métodos Memoria.ver_casillas, transitable, transitable_peligro y atributos de casillas/mapa |
| `Peticion (S1)` | A7 | `ida/sistemas/comun.py:115-141; ida/sistemas/s1.py:839` | Clase Peticion(Componente); montada hoy en Modulo('Actuar', ...) en s1.py:839 en vez de S1.Reaccionar |
| `Afrontar` | A6 | `ida/sistemas/s1.py:288-433, 709` | Clase Afrontar(Definicion); montada en _estrategias_base() en s1.py:709 para todos los mundos |
| `Proteger` | A6 | `ida/sistemas/proteger.py:488-601; ida/sistemas/s1.py:709` | Clase Proteger(Definicion); montada en _estrategias_base() en s1.py:709 para todos los mundos |
| `SalirDelRecinto` | A6 | `ida/sistemas/proteger.py:841-874; ida/sistemas/s1.py:710` | Clase SalirDelRecinto(ConPropuestas); montada en _estrategias_base() en s1.py:710 para todos los mundos |
| `Peticion (S2)` | A7 | `ida/sistemas/comun.py:115-141; ida/sistemas/s2.py:456` | Clase Peticion(Componente); montada hoy en Modulo('Actuar', ...) en s2.py:456 en vez de S2.Reaccionar |
| `Requisito` | A7 | `ida/core/memoria.py:216-273, 1011-1033, 1145-1180` | Clase Requisito y métodos Memoria.aprender_requisito, aprender_transformacion, transformacion |
| `ModeloDirecto` | A5 | `ida/core/memoria.py:1135-1144` | Método Memoria.aprender_cuerpo y modelo_cuerpo sobre propiocepción y dirección/avance de acciones |
| `Geometria` | A5 | `ida/sistemas/proteger.py:86-97, 317-320` | Funciones geométricas _suma, _vecinas, _manhattan y entorno (cálculos espaciales de cuadrícula) |
| `BuscadorPosturas` | A5 | `ida/sistemas/proteger.py:282-306` | Funciones mover y buscar_postura (búsqueda BFS de secuencia de MOVER para quedar en postura) |
| `Motor` | A5 | `ida/mundos/crafter.py:355-364, 404-413, 414-446` | Métodos Crafter._paso, _interactuar y ejecutar (traducción de verbos/intenciones a primitivas del motor y sinergias) |

## Resumen de conteos

| Sección | Descripción | Total filas |
|---|---|---|
| A | Añadido por la fase de generalización | 251 |
| B | Lecturas de Observación fuera de sensores | 45 |
| C | Lecturas de rasgos valorados | 76 |
| D | Activaciones condicionales e interruptores | 93 |
| E | Constantes en mayúsculas (módulo y clase) | 167 |
| F | Escrituras en Memoria fuera de memoria.py | 30 |
| G | Tiempo del mundo en ida/sistemas | 129 |
| H | Adaptador de Crafter (rasgos y atributos) | 9 |
| I | 17 entradas pendientes del Mapa | 17 |
