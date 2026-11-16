"""S1 · Supervivencia: cuerpo, peligro, reflejos e impulsos básicos. Rápido, simple y siempre primero.

| Etapa       | Componente     | Produce |
|-------------|----------------|---------|
| Sentir      | Imagen         | Imagen (gestalt del instante) |
| Interpretar | Objeto         | Objeto (cada cuerpo de la Imagen que entra en la atención) |
| Interpretar | Supervivencia  | Supervivencia por objeto (peligro graduado) y una alarma global |
| Reaccionar  | Reflejo        | Reflejo: sobresalto ante un salto brusco del peligro |
| Reaccionar  | Impulso        | Impulso: uno por necesidad que declara el mundo, más Seguridad (intensidad cruda) |
| Reaccionar  | Feedback       | Feedback de S1: cuánto bajan los déficits del cuerpo y el peligro |
| Reaccionar  | Estrategia     | Estrategia: elige, mantiene y abandona estrategias (progreso y agotamiento) |
| Actuar      | Accion         | Acción de cada estrategia activa, con su origen |
| Actuar      | Anticipacion   | Expectativa: cambio esperado de las necesidades si se ejecuta su propuesta (con el interruptor de expectativa) |
"""

from typing import Callable, Dict, List, Optional, Tuple

from ida.core.arquitectura import Componente, Contexto, Modulo, Sistema, expectativa_ejecutada
from ida.core.estrategia import Catalogo, Definicion, Propuesta
from ida.core.pieza import Pieza, acotar
from ida.core.vocabulario import EstadoSaber, Relacion, Verbo
from ida.sistemas.comun import PESO_PREDICCION, Accion, Anticipacion, Estrategia, cautela, MAX_OBJETOS, al_alcance, alarma, apetito, exterocepcion, lugares, mejor, objetos


def _cosas(ctx: Contexto) -> list:
    """Lo percibido que no es un lugar, de más a menos saliente (orden estable)."""
    cosas = [p for p in exterocepcion(ctx) if p.rasgo("lugar") < 0.5]
    cosas.sort(key=lambda p: -p.arousal)
    return cosas


class Imagen(Componente):
    """Integra Exterocepcion, Interocepción y el resultado de la acción anterior en una representación del instante."""

    tipo = "Imagen"
    entradas = ("Exterocepcion", "Interocepcion")

    def reactiva(self, ctx: Contexto) -> None:
        cosas = _cosas(ctx)
        foco = cosas[0] if cosas else None
        previa = ctx.onda.ei("Accion").get("Accion")
        agencia = ""
        if previa is not None:
            d = previa.carga.get("delta", {})
            agencia = f"{previa.carga['verbo'].value} {previa.carga.get('clase') or previa.carga['objetivo']} → " + (
                ", ".join(f"{k} {v:+.1f}" for k, v in d.items() if v) or "sin cambios"
            )
        self.percibir(ctx, self.pieza(
            ctx, f"imagen_{ctx.latido}", arousal=foco.arousal if foco else 0.1,
            carga={"foco": foco.id if foco else None, "clase_foco": foco.clase if foco else None,
                   "n_cosas": len(cosas), "n_lugares": len(lugares(ctx)), "agencia": agencia},
            entradas=["Exterocepcion", "Interocepcion", "Accion"],
        ))


class Objeto(Componente):
    """Distingue los cuerpos dentro de la Imagen: solo los más salientes (7 ± 2) pasan a la atención
    como piezas ``Objeto``, cada una con coste 1."""

    tipo = "Objeto"
    entradas = ("Imagen",)

    def reactiva(self, ctx: Contexto) -> None:
        conceptos = ctx.perfil.mecanismos.conceptos and ctx.con_experiencia and ctx.memoria.activa
        for p in _cosas(ctx)[:MAX_OBJETOS]:
            self.percibir(ctx, self.pieza(ctx, p.id, arousal=p.arousal, confianza=p.confianza,
                                          carga={"clase": p.clase, "rasgos": dict(p.carga["rasgos"])},
                                          entradas=[p.id]))
            if conceptos:   # bloque E, E3: la instancia actualiza el concepto de su clase (decisión 20)
                ctx.memoria.instancia(p.id, p.clase, p.carga["rasgos"], ctx.latido)


RECURSO, PELIGRO, NEUTRO = "recurso", "peligro", "neutro"
ENCUENTROS_HABITUACION = 20      # avistamientos sin daño para la familiaridad completa (como en Patron)
HABITUACION_MAX = 0.4            # la amenaza aparente baja hasta un 40 % con la familiaridad
SENSIBILIZACION_MAX = 0.5        # tras un daño, la amenaza sube hasta un 50 % con su confianza


def relacion_supervivencia(ctx: Contexto, o: Pieza, amenaza: float, atractivo: float) -> Tuple[str, float, float]:
    """Clase de relación de un objeto con la supervivencia, su trust y el factor sobre su amenaza
    (decisión 8): habituación y sensibilización.
    - peligro: ya hizo daño (hay hipótesis de daño): trust = su confianza; sensibilización, la amenaza
      sube hasta ``1 + SENSIBILIZACION_MAX``;
    - recurso: se sabe que nutre (confianza ≥ 0,5 y no refutado) o lo parece (atractivo > 0,05);
    - neutro: el resto. Trust = familiaridad (encuentros sin daño): bajo = desconocido, alto =
      habituado; si además parece peligroso, la amenaza baja hasta ``1 − HABITUACION_MAX``.
    Sin experiencia, solo la apariencia: peligro si amenaza > 0,05, recurso si atractivo > 0,05."""
    if not ctx.con_experiencia or not ctx.memoria.activa:
        return (PELIGRO if amenaza > 0.05 else RECURSO if atractivo > 0.05 else NEUTRO), 0.0, 1.0
    mem = ctx.memoria
    dano = mem.proposicion(o.clase, Relacion.PELIGROSO)
    if dano is not None and dano.estado(ctx.latido) != EstadoSaber.REFUTADA:
        return PELIGRO, dano.confianza, 1.0 + SENSIBILIZACION_MAX * dano.confianza
    nutre = mem.proposicion(o.clase, Relacion.NUTRITIVO)
    if (nutre is not None and nutre.confianza >= 0.5 and nutre.estado(ctx.latido) != EstadoSaber.REFUTADA) or atractivo > 0.05:
        return RECURSO, nutre.confianza if nutre is not None else 0.5, 1.0
    familiaridad = min(1.0, mem.clases_vistas.get(o.clase, 0) / ENCUENTROS_HABITUACION)
    return NEUTRO, familiaridad, 1.0 - HABITUACION_MAX * familiaridad


class Supervivencia(Componente):
    """Relación de cada Objeto con la supervivencia. El peligro es graduado por cercanía y por número,
    no un sí o no, y la sensibilidad depende del carácter (neuroticismo)."""

    tipo = "Supervivencia"
    entradas = ("Objeto", "Interocepcion")

    def reactiva(self, ctx: Contexto) -> None:
        sensibilidad = 0.8 + 0.4 * ctx.arquetipo.neuroticismo
        seguro = 1.0
        principal, max_amenaza = None, 0.0
        comida, max_comida = None, 0.0
        clases: Dict[str, Tuple[str, float]] = {}
        for o in objetos(ctx):
            amenaza = acotar(o.rasgo("peligro") * (0.3 + 0.7 * o.rasgo("proximidad")) * sensibilidad)
            atractivo = o.rasgo("nutritivo") * (0.4 + 0.6 * o.rasgo("proximidad"))
            categoria, trust, factor = relacion_supervivencia(ctx, o, amenaza, atractivo)
            amenaza = acotar(amenaza * factor)
            clases[o.clase] = (categoria, round(trust, 3))
            seguro *= (1.0 - amenaza)
            if amenaza > max_amenaza:
                principal, max_amenaza = o, amenaza
            if atractivo > max_comida:
                comida, max_comida = o, atractivo
            if amenaza > 0.05 or atractivo > 0.05:
                self.percibir(ctx, self.pieza(ctx, o.id, arousal=max(amenaza, atractivo * apetito(ctx)),
                                              carga={"clase": o.clase, "amenaza": round(amenaza, 3), "atractivo": round(atractivo, 3),
                                                     "categoria": categoria, "trust": round(trust, 3)},
                                              entradas=[o.id]))
        peligro = 1.0 - seguro
        self.percibir(ctx, self.pieza(
            ctx, "alarma", arousal=max(peligro, 0.9 if ctx.soma.alimentacion <= ctx.soma.HAMBRE_CRITICA else 0.0),
            carga={"peligro": round(peligro, 3), "hambre": round(ctx.soma.hambre(), 3), "cansancio": round(ctx.soma.cansancio(), 3),
                   "amenaza": principal.id if principal else None, "clase_amenaza": principal.clase if principal else None,
                   "comida": comida.id if comida else None, "clases": clases},
            entradas=["Objeto", "Interocepcion"],
        ))


SEGURIDAD = "seguridad"


def _salida(ctx: Contexto, peligro: float) -> Optional[Pieza]:
    """El lugar a la vista menos peligroso, si lo es menos que el peligro actual."""
    salida = mejor(lugares(ctx), lambda lugar: -lugar.rasgo("peligro"))
    return salida if salida is not None and salida.rasgo("peligro") < peligro else None


def _amenaza(ctx: Contexto) -> Optional[Pieza]:
    a = alarma(ctx)
    return ctx.onda.ev("Objeto").get(a.carga["amenaza"]) if a is not None and a.carga["amenaza"] else None


def _peligro(ctx: Contexto) -> float:
    a = alarma(ctx)
    return float(a.carga["peligro"]) if a is not None else 0.0


# --- Estrategias genéricas de S1 (decisiones 3, 6 y 17) -----------------------------------------
class Huir(Definicion):
    """Seguridad: alejarse al lugar más seguro mientras el peligro supere el umbral de miedo."""

    nombre = "huir"
    impulsos = (SEGURIDAD,)
    prioridad = 10

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return intensidad >= ctx.arquetipo.umbral_miedo and _salida(ctx, intensidad) is not None

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        peligro = _peligro(ctx)
        salida = _salida(ctx, peligro)
        if salida is None:
            return None
        a = alarma(ctx)
        de = a.carga["clase_amenaza"] if a is not None else ""
        return Propuesta(Verbo.MOVER, salida.id, acotar(0.75 + 0.25 * peligro), 0.85, f"huir de {de}", clase=salida.clase)


class Defenderse(Definicion):
    """Seguridad: sin salida y con la amenaza al alcance, defenderse."""

    nombre = "defenderse"
    impulsos = (SEGURIDAD,)
    prioridad = 5

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        amenaza = _amenaza(ctx)
        return intensidad >= ctx.arquetipo.umbral_miedo and _salida(ctx, intensidad) is None and amenaza is not None and al_alcance(amenaza)

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        amenaza = _amenaza(ctx)
        if amenaza is None or not al_alcance(amenaza):
            return None
        return Propuesta(Verbo.ATACAR, amenaza.id, acotar(0.75 + 0.25 * _peligro(ctx)), 0.7, f"defenderse de {amenaza.clase}", clase=amenaza.clase)


class Sobresalto(Definicion):
    """Reflejo (decisión 6): ante un salto brusco del peligro, empezar a huir (o defenderse si no hay
    salida y la amenaza está al alcance). Innato, corto, de duración fija y prioridad máxima."""

    nombre = "sobresalto"
    impulsos = (SEGURIDAD,)
    reflejo = True

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        peligro = _peligro(ctx)
        salida = _salida(ctx, peligro)
        if salida is not None:
            return Propuesta(Verbo.MOVER, salida.id, 1.0, 0.9, "reflejo: sobresalto, huir", clase=salida.clase)
        amenaza = _amenaza(ctx)
        if amenaza is not None and al_alcance(amenaza):
            return Propuesta(Verbo.ATACAR, amenaza.id, 1.0, 0.9, f"reflejo: sobresalto, defenderse de {amenaza.clase}", clase=amenaza.clase)
        return None


class QuietoOHuir(Definicion):
    """Último recurso de Seguridad cuando todas sus estrategias están agotadas: huir si hay un lugar
    menos peligroso; si no, quedarse quieto."""

    nombre = "quieto_o_huir"
    impulsos = (SEGURIDAD,)
    ultimo_recurso = True

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        peligro = _peligro(ctx)
        salida = _salida(ctx, peligro)
        urgencia = acotar(0.75 + 0.25 * peligro)
        if salida is not None:
            return Propuesta(Verbo.MOVER, salida.id, urgencia, 0.85, "último recurso: huir", clase=salida.clase)
        return Propuesta(Verbo.ESPERAR, "", urgencia, 0.6, "último recurso: quedarse quieto")


class SeguirEnMovimiento(Definicion):
    """Último recurso de cualquier impulso en un mundo que no deja esperar: si ninguna otra estrategia
    es elegible, moverse al lugar menos malo (el más nutritivo y menos peligroso). Cede en cuanto
    otra estrategia del impulso vuelve a ser elegible. Antes era «el mal menor» de ``Accion``."""

    nombre = "seguir_en_movimiento"
    cualquier_impulso = True
    ultimo_recurso = True

    @staticmethod
    def _destino(ctx: Contexto) -> Optional[Pieza]:
        return mejor(lugares(ctx), lambda lugar: lugar.rasgo("nutritivo") - 1.5 * lugar.rasgo("peligro"))

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return Verbo.ESPERAR not in ctx.verbos and self._destino(ctx) is not None

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        destino = self._destino(ctx)
        if destino is None:
            return None
        return Propuesta(Verbo.MOVER, destino.id, 0.3, 0.5, "sin opción mejor: seguir en movimiento", clase=destino.clase)


def _rechazado(ctx: Contexto, o: Pieza) -> bool:
    """Elección del objeto (decisión 1 del autor sobre C1): primero el valor de S2 (del latido anterior,
    porque S2 corre después de S1) y después las creencias de S3 (lo que sostiene, bloque D). Se rechaza lo que se valora mal
    (valencia negativa) y lo que se sabe peligroso o se sabe que no nutre. Un objeto que S2 no ha
    valorado (fuera de la atención) toma el valor de otro de su clase que sí lo esté: el sentimiento
    sale de los recuerdos de la clase."""
    valores = ctx.onda.ei("Valor")
    valor = valores.get(o.id)
    if valor is None:
        valor = next((v for v in valores.values() if v.carga.get("clase") == o.clase), None)
    if valor is not None and float(valor.carga.get("valencia", 0.0)) < 0.0:
        return True
    if o.clase in cautela(ctx)[0]:            # S3 lo desaconseja (con su criterio, p. ej. indicios de daño)
        return True
    if not ctx.con_experiencia:
        return False
    # Lo que S3 sostiene (piezas Creencia del latido anterior: S3 corre después de S1).
    creencias = ctx.onda.ei("Creencia")
    dano = creencias.get(f"{o.clase}|{Relacion.PELIGROSO.name}")
    if dano is not None and dano.carga.get("sostiene"):
        return True
    nutre = creencias.get(f"{o.clase}|{Relacion.NUTRITIVO.name}")
    return nutre is not None and nutre.carga.get("estado") == EstadoSaber.REFUTADA


Rechazo = Callable[[Contexto, Pieza], bool]


def _al_alcance(ctx: Contexto, rechaza: Rechazo = _rechazado) -> Tuple[List[Pieza], List[Pieza]]:
    """Comestibles al alcance, separados en aceptables y rechazados."""
    comestibles = [o for o in objetos(ctx) if o.rasgo("nutritivo") >= 0.3 and al_alcance(o)]
    rechazados = [o for o in comestibles if rechaza(ctx, o)]
    return [o for o in comestibles if o not in rechazados], rechazados


def _aceptables_a_la_vista(ctx: Contexto, rechaza: Rechazo = _rechazado) -> List[Pieza]:
    """Comestibles a la vista pero no al alcance que no se rechazan."""
    return [o for o in objetos(ctx) if o.rasgo("nutritivo") >= 0.3 and not al_alcance(o) and not rechaza(ctx, o)]


def _posicion(ctx: Contexto, pid: str) -> Optional[Tuple[float, ...]]:
    """Posición percibida de una entidad, si el mundo la da (``datos["pos"]`` de la exterocepción)."""
    e = ctx.onda.ev("Exterocepcion").get(pid)
    pos = e.carga.get("datos", {}).get("pos") if e is not None else None
    return tuple(float(x) for x in pos) if isinstance(pos, (tuple, list)) else None


def _hacia(ctx: Contexto, objetivo: Pieza) -> Optional[Pieza]:
    """El lugar a la vista (no peligroso) que más acerca a ``objetivo``, si hay posiciones percibidas."""
    meta = _posicion(ctx, objetivo.id)
    if meta is None:
        return None
    candidatos = [(lugar, _posicion(ctx, lugar.id)) for lugar in _lugares_permitidos(ctx) if lugar.rasgo("peligro") < 0.8]
    con_pos = [(lugar, pos) for lugar, pos in candidatos if pos is not None and len(pos) == len(meta)]
    if not con_pos:
        return None
    return min(con_pos, key=lambda lp: sum(abs(a - b) for a, b in zip(lp[1], meta, strict=True)))[0]


def _lugares_permitidos(ctx: Contexto) -> List[Pieza]:
    """Lugares a la vista menos los que S3 desaconseja."""
    evitar = cautela(ctx)[1]
    return [lugar for lugar in lugares(ctx) if lugar.id not in evitar]


def _destino_comida(ctx: Contexto) -> Optional[Pieza]:
    destino = mejor(_lugares_permitidos(ctx), lambda lugar: lugar.rasgo("nutritivo") - 1.5 * lugar.rasgo("peligro"))
    return destino if destino is not None and destino.rasgo("nutritivo") > 0.0 and destino.rasgo("peligro") < 0.8 else None


BUSCAR, ACERCARSE, COMER = "buscar", "acercarse", "comer"


class Alimentarse(Definicion):
    """Necesidades que satisface lo nutritivo (decisión 2 del autor sobre C1): una sola estrategia con
    tres fases, buscar → acercarse → comer.

    - **comer**: hay algo aceptable al alcance (y el mundo deja comer): el mejor por nutritivo − peligro.
    - **acercarse**: hay comida aceptable a la vista o se huele comida en un lugar a la vista: ir
      hacia el lugar más nutritivo y menos peligroso. Si lo que hay al alcance se rechaza pero hay
      comida aceptable a la vista, ir hacia esa comida (por posición percibida, si el mundo la da):
      el olor del lugar también lleva a lo rechazado.
    - **buscar**: lo único al alcance se rechaza (se valora mal o se sabe dañino) y no hay nada
      aceptable a la vista: no se come y se va a otro sitio, el lugar más nuevo y menos peligroso.
    Elegible mientras haya algo de eso; si no hay nada a la vista, se cierra y exploran otros sistemas.
    """

    nombre = "alimentarse"
    rasgo = "nutritivo"
    prioridad = 10

    def rechaza(self, ctx: Contexto, o: Pieza) -> bool:
        """Criterio de elección del objeto. Un mundo puede ampliarlo con una estrategia propia."""
        return _rechazado(ctx, o)

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        aceptables, rechazados = _al_alcance(ctx, self.rechaza)
        return bool(aceptables or rechazados) or _destino_comida(ctx) is not None

    def paso(self, ctx: Contexto, estrategia: Pieza) -> str:
        aceptables, rechazados = _al_alcance(ctx, self.rechaza)
        if aceptables and Verbo.COMER in ctx.verbos and ctx.soma.alimentacion < 95.0:
            return COMER
        if rechazados and not aceptables:
            return ACERCARSE if _aceptables_a_la_vista(ctx, self.rechaza) else BUSCAR
        return ACERCARSE if _destino_comida(ctx) is not None else BUSCAR

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        paso = estrategia.carga.get("paso")
        if paso == COMER:
            aceptables, _ = _al_alcance(ctx, self.rechaza)
            cerca = mejor(aceptables, lambda o: o.rasgo("nutritivo") - o.rasgo("peligro"))
            if cerca is not None:
                return Propuesta(Verbo.COMER, cerca.id, acotar(0.35 + 0.6 * apetito(ctx)), 0.7, f"comer {cerca.clase}", clase=cerca.clase)
        if paso == ACERCARSE:
            _, rechazados = _al_alcance(ctx, self.rechaza)
            vista = mejor(_aceptables_a_la_vista(ctx, self.rechaza), lambda o: o.rasgo("nutritivo") * o.rasgo("proximidad") - o.rasgo("peligro"))
            if rechazados and vista is not None:
                lugar = _hacia(ctx, vista)
                if lugar is not None:
                    ar = acotar(0.25 + 0.6 * apetito(ctx) * vista.rasgo("nutritivo"))
                    return Propuesta(Verbo.MOVER, lugar.id, ar, 0.6, f"acercarse a {vista.clase}", clase=lugar.clase)
            destino = _destino_comida(ctx)
            if destino is not None:
                ar = acotar(0.25 + 0.6 * apetito(ctx) * destino.rasgo("nutritivo"))
                return Propuesta(Verbo.MOVER, destino.id, ar, 0.6, "acercarse a la comida", clase=destino.clase)
        if paso == BUSCAR:
            otro = mejor([lugar for lugar in _lugares_permitidos(ctx) if lugar.rasgo("peligro") < 0.5],
                         lambda lugar: lugar.rasgo("novedad") - lugar.rasgo("peligro"))
            if otro is not None:
                return Propuesta(Verbo.MOVER, otro.id, acotar(0.2 + 0.3 * apetito(ctx)), 0.5, "buscar comida en otro sitio", clase=otro.clase)
        return None


def estrategias_s1() -> List[Definicion]:
    return [Huir(), Defenderse(), Sobresalto(), QuietoOHuir(), Alimentarse(), SeguirEnMovimiento()]


# --- Componentes de Reaccionar ------------------------------------------------------------------
class Reflejo(Componente):
    """Detecta un cambio brusco del Sentir (decisión 6): si el peligro sube de golpe respecto al latido
    anterior al menos el umbral del reflejo, registra un sobresalto. La respuesta es la estrategia
    refleja de S1, de duración fija y prioridad máxima.

    El umbral escala con el carácter: ``Perfil.umbral_reflejo`` vale para un ``umbral_miedo`` de
    referencia (0,6, el del arquetipo por defecto) y se multiplica por ``umbral_miedo / 0,6``. Un
    individuo valiente necesita un salto mayor para sobresaltarse; uno reactivo, menor.
    """

    tipo = "Reflejo"
    entradas = ("Supervivencia",)
    UMBRAL_MIEDO_REFERENCIA = 0.6

    def umbral(self, ctx: Contexto) -> float:
        return min(1.0, ctx.perfil.umbral_reflejo * ctx.arquetipo.umbral_miedo / self.UMBRAL_MIEDO_REFERENCIA)

    def reactiva(self, ctx: Contexto) -> None:
        a = alarma(ctx)
        if a is None:
            return
        previa = ctx.onda.ei("Supervivencia").get("alarma")
        antes = float(previa.carga["peligro"]) if previa is not None else 0.0
        salto = float(a.carga["peligro"]) - antes
        if salto >= self.umbral(ctx):
            self.registrar(ctx, self.pieza(ctx, "sobresalto", arousal=1.0,
                                           carga={"salto": round(salto, 3), "peligro": a.carga["peligro"], "de": a.carga["clase_amenaza"]}))


class Impulso(Componente):
    """Un impulso por necesidad que declara el mundo (su déficit es la intensidad cruda) y Seguridad
    (el peligro). No proponen acciones: lo hacen las estrategias (decisiones 2 y 3)."""

    tipo = "Impulso"
    entradas = ("Supervivencia",)

    def reactiva(self, ctx: Contexto) -> None:
        rasgos = {n.nombre: n.rasgo for n in ctx.perfil.necesidades}
        for nombre, intensidad in deficits(ctx).items():
            self.registrar(ctx, self.pieza(ctx, nombre, arousal=intensidad,
                                           carga={"intensidad": round(intensidad, 4), "objetivo": 0.0, "rasgo": rasgos.get(nombre)}))


def deficits(ctx: Contexto) -> Dict[str, float]:
    """Déficit de cada necesidad que declara el mundo (desde la interocepción) y peligro (Seguridad)."""
    valores = {n: float(p.carga["valor"]) for n, p in ctx.onda.ev("Interocepcion").items()}
    d: Dict[str, float] = {}
    for necesidad in ctx.perfil.necesidades:
        v = necesidad.deficit(valores)
        if v is not None:
            d[necesidad.nombre] = v
    a = alarma(ctx)
    d["seguridad"] = float(a.carga["peligro"]) if a is not None else 0.0
    return d


class Feedback(Componente):
    """Feedback de S1 (decisión 5): cuánto bajan los déficits del cuerpo y el peligro respecto al latido
    anterior. Positivo = mejora. Es la señal de mérito de las estrategias de S1."""

    tipo = "Feedback"

    def reactiva(self, ctx: Contexto) -> None:
        ahora = deficits(ctx)
        previo = ctx.onda.ei("Feedback").get(f"feedback:{self.sistema}")
        antes = previo.carga["deficits"] if previo is not None else ahora
        cambios = {k: round(antes.get(k, v) - v, 4) for k, v in ahora.items()}
        e = expectativa_ejecutada(ctx.onda, self.sistema) if ctx.perfil.mecanismos.expectativa else None
        if e is not None and e.carga["esperado"]:
            # Bloque F, F1: error de predicción con signo (mejor de lo esperado = positivo) por necesidad.
            for k, base in e.carga["base"].items():
                if k in ahora and k in e.carga["esperado"]:
                    rpe = float(e.carga["esperado"][k]) - (ahora[k] - float(base))
                    cambios[k] = round(cambios.get(k, 0.0) + PESO_PREDICCION * rpe, 4)
        self.registrar(ctx, self.pieza(ctx, f"feedback:{self.sistema}", arousal=0.0,
                                       carga={"valor": round(sum(cambios.values()), 4), "por_impulso": cambios, "deficits": ahora}))


def crear_s1() -> Sistema:
    catalogo = Catalogo(estrategias_s1())
    return Sistema("S1", "Supervivencia", [
        Modulo("Sentir", [Imagen()]),
        Modulo("Interpretar", [Objeto(), Supervivencia()]),
        Modulo("Reaccionar", [Reflejo(), Impulso(), Feedback(), Estrategia(catalogo, impulso_critico=SEGURIDAD)]),
        Modulo("Actuar", [Accion(catalogo), Anticipacion()]),
    ])
