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
"""

from typing import Any, Dict, List, Optional, Tuple

from ida.core.arquitectura import Componente, Contexto, Modulo, Sistema
from ida.core import estrategia as est
from ida.core.estrategia import Catalogo, Definicion, Propuesta
from ida.core.pieza import Pieza, acotar
from ida.core.vocabulario import EstadoSaber, Relacion, Verbo
from ida.sistemas.comun import Accion, MAX_OBJETOS, al_alcance, alarma, apetito, exterocepcion, lugares, mejor, objetos


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
        for p in _cosas(ctx)[:MAX_OBJETOS]:
            self.percibir(ctx, self.pieza(ctx, p.id, arousal=p.arousal, confianza=p.confianza,
                                          carga={"clase": p.clase, "rasgos": dict(p.carga["rasgos"])},
                                          entradas=[p.id]))


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
        for o in objetos(ctx):
            amenaza = acotar(o.rasgo("peligro") * (0.3 + 0.7 * o.rasgo("proximidad")) * sensibilidad)
            atractivo = o.rasgo("nutritivo") * (0.4 + 0.6 * o.rasgo("proximidad"))
            seguro *= (1.0 - amenaza)
            if amenaza > max_amenaza:
                principal, max_amenaza = o, amenaza
            if atractivo > max_comida:
                comida, max_comida = o, atractivo
            if amenaza > 0.05 or atractivo > 0.05:
                self.percibir(ctx, self.pieza(ctx, o.id, arousal=max(amenaza, atractivo * apetito(ctx)),
                                              carga={"clase": o.clase, "amenaza": round(amenaza, 3), "atractivo": round(atractivo, 3)},
                                              entradas=[o.id]))
        peligro = 1.0 - seguro
        self.percibir(ctx, self.pieza(
            ctx, "alarma", arousal=max(peligro, 0.9 if ctx.soma.alimentacion <= ctx.soma.HAMBRE_CRITICA else 0.0),
            carga={"peligro": round(peligro, 3), "hambre": round(ctx.soma.hambre(), 3), "cansancio": round(ctx.soma.cansancio(), 3),
                   "amenaza": principal.id if principal else None, "clase_amenaza": principal.clase if principal else None,
                   "comida": comida.id if comida else None},
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
    porque S2 corre después de S1) y después lo demostrado (S3). Se rechaza lo que se valora mal
    (valencia negativa) y lo que se sabe peligroso o se sabe que no nutre. Un objeto que S2 no ha
    valorado (fuera de la atención) toma el valor de otro de su clase que sí lo esté: el sentimiento
    sale de los recuerdos de la clase."""
    valores = ctx.onda.ei("Valor")
    valor = valores.get(o.id)
    if valor is None:
        valor = next((v for v in valores.values() if v.carga.get("clase") == o.clase), None)
    if valor is not None and float(valor.carga.get("valencia", 0.0)) < 0.0:
        return True
    if not ctx.con_experiencia:
        return False
    if ctx.memoria.demostrada(o.clase, Relacion.PELIGROSO, ctx.latido):
        return True
    nutre = ctx.memoria.proposicion(o.clase, Relacion.NUTRITIVO)
    return nutre is not None and nutre.estado(ctx.latido) == EstadoSaber.REFUTADA


def _al_alcance(ctx: Contexto) -> Tuple[List[Pieza], List[Pieza]]:
    """Comestibles al alcance, separados en aceptables y rechazados."""
    comestibles = [o for o in objetos(ctx) if o.rasgo("nutritivo") >= 0.3 and al_alcance(o)]
    rechazados = [o for o in comestibles if _rechazado(ctx, o)]
    return [o for o in comestibles if o not in rechazados], rechazados


def _aceptables_a_la_vista(ctx: Contexto) -> List[Pieza]:
    """Comestibles a la vista pero no al alcance que no se rechazan."""
    return [o for o in objetos(ctx) if o.rasgo("nutritivo") >= 0.3 and not al_alcance(o) and not _rechazado(ctx, o)]


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
    candidatos = [(lugar, _posicion(ctx, lugar.id)) for lugar in lugares(ctx) if lugar.rasgo("peligro") < 0.8]
    con_pos = [(lugar, pos) for lugar, pos in candidatos if pos is not None and len(pos) == len(meta)]
    if not con_pos:
        return None
    return min(con_pos, key=lambda lp: sum(abs(a - b) for a, b in zip(lp[1], meta, strict=True)))[0]


def _destino_comida(ctx: Contexto) -> Optional[Pieza]:
    destino = mejor(lugares(ctx), lambda lugar: lugar.rasgo("nutritivo") - 1.5 * lugar.rasgo("peligro"))
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

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        aceptables, rechazados = _al_alcance(ctx)
        return bool(aceptables or rechazados) or _destino_comida(ctx) is not None

    def paso(self, ctx: Contexto, estrategia: Pieza) -> str:
        aceptables, rechazados = _al_alcance(ctx)
        if aceptables and Verbo.COMER in ctx.verbos and ctx.soma.alimentacion < 95.0:
            return COMER
        if rechazados and not aceptables:
            return ACERCARSE if _aceptables_a_la_vista(ctx) else BUSCAR
        return ACERCARSE if _destino_comida(ctx) is not None else BUSCAR

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        paso = estrategia.carga.get("paso")
        if paso == COMER:
            aceptables, _ = _al_alcance(ctx)
            cerca = mejor(aceptables, lambda o: o.rasgo("nutritivo") - o.rasgo("peligro"))
            if cerca is not None:
                return Propuesta(Verbo.COMER, cerca.id, acotar(0.35 + 0.6 * apetito(ctx)), 0.7, f"comer {cerca.clase}", clase=cerca.clase)
        if paso == ACERCARSE:
            _, rechazados = _al_alcance(ctx)
            vista = mejor(_aceptables_a_la_vista(ctx), lambda o: o.rasgo("nutritivo") * o.rasgo("proximidad") - o.rasgo("peligro"))
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
            otro = mejor([lugar for lugar in lugares(ctx) if lugar.rasgo("peligro") < 0.5],
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


class Estrategia(Componente):
    """Elige, mantiene y abandona las estrategias de S1 (decisiones 4, 16 y 17).

    - Una estrategia activa como mucho por impulso, más el reflejo. Continúa mientras sea elegible.
      Solo cede ante otra elegible si la supera con un margen claro (histéresis,
      ``MARGEN_SUSTITUCION``) en puntuación = valor aprendido + prioridad innata / 100 (p. ej., de
      huir a plantar cara). Las fases de una misma estrategia (buscar, acercarse, comer) no son
      sustituciones: las fija ``Definicion.paso`` en cada latido.
    - Se cierra al bajar la necesidad al objetivo (completada), al dejar de ser elegible (sin objeto)
      o al agotarse (agotada; no se vuelve a elegir durante ``Perfil.enfriamiento_estrategia``).
    - Agotar una estrategia de Seguridad cambia de estrategia, no abandona el impulso; si todas
      las elegibles están agotadas, último recurso innato (quedarse quieto o huir).
    - Si nada es elegible para un impulso en un mundo que no deja esperar, último recurso genérico
      (seguir en movimiento). Un último recurso cede en cuanto otra estrategia es elegible.
    - Elección: la de mayor puntuación; la apertura regula cuánto se prueba otra al azar. Valor
      aprendido por impulso y estrategia durante la vida, al cerrarse: el mérito es el feedback de S1
      de su impulso acumulado mientras se ejecutó, normalizado por la intensidad inicial (en [−1, 1]);
      la fuerza del aprendizaje es esa intensidad inicial (su arousal). Sin experiencia no se aprende
      ni se explora.
    """

    tipo = "Estrategia"
    VALOR_INICIAL = 0.5
    TASA = 0.5
    EXPLORACION = 0.2
    MARGEN_SUSTITUCION = 0.2

    def __init__(self, catalogo: Catalogo):
        super().__init__("Estrategia")
        self.catalogo = catalogo
        self.valor: Dict[Tuple[str, str], float] = {}
        self.enfriando: Dict[Tuple[str, str], int] = {}

    def reactiva(self, ctx: Contexto) -> None:
        onda, perfil = ctx.onda, ctx.perfil
        impulsos = onda.ef("Impulso")
        previa = onda.ei("Accion").get("Accion")
        ejecutada = previa.carga.get("origen", {}).get("estrategia") if previa is not None else None
        fb = onda.ef("Feedback").get("feedback")
        feedback = fb.carga.get("por_impulso", {}) if fb is not None else {}
        notas: Dict[str, Any] = {"activas": [], "ejecutada": None, "abandonos": [], "reflejo": False, "interrumpe": False, "sustituciones": 0}

        for p in [p for p in onda.estrategias.values() if p.sistema == self.sistema]:
            c = p.carga
            if p.id == ejecutada:
                notas["ejecutada"] = c["nombre"]
            if c["reflejo"]:
                if ctx.latido - c["inicio"] >= perfil.duracion_reflejo:
                    self._cerrar(ctx, p, est.TERMINADA)
                continue
            imp = impulsos.get(c["impulso"])
            intensidad = float(imp.carga["intensidad"]) if imp is not None else 0.0
            cambios = est.avanzar(c, intensidad, p.id == ejecutada, ctx.latido, perfil.gracia_estrategia, perfil.ritmo_esperado_estrategia)
            if p.id == ejecutada:          # el mérito se lo lleva la estrategia que se ejecutó (decisión 23)
                cambios["merito"] = float(c.get("merito", 0.0)) + float(feedback.get(c["impulso"], 0.0))
            self.modificar(ctx, p, carga=cambios)
            definicion = self.catalogo.get(c["nombre"])
            if intensidad <= c["objetivo"] + 1e-9:
                self._cerrar(ctx, p, est.COMPLETADA)
            elif c["agotamiento"] >= 1.0:
                self._cerrar(ctx, p, est.AGOTADA)
                self.enfriando[(c["impulso"], c["nombre"])] = ctx.latido + perfil.enfriamiento_estrategia
                notas["abandonos"].append(c["nombre"])
            elif definicion is None or not definicion.elegible(ctx, c["impulso"], intensidad):
                self._cerrar(ctx, p, est.SIN_OBJETO)
            elif definicion.ultimo_recurso and self._mejor(ctx, c["impulso"], imp.carga.get("rasgo") if imp is not None else None, intensidad):
                self._cerrar(ctx, p, est.SUSTITUIDA)     # un último recurso cede en cuanto hay otra opción
                notas["sustituciones"] += 1
            else:
                paso = definicion.paso(ctx, p)
                if paso != c.get("paso"):
                    self.modificar(ctx, p, carga={"paso": paso})

        sobresalto = onda.ef("Reflejo").get("sobresalto")
        reflejo_activo = any(p.sistema == self.sistema and p.carga["reflejo"] for p in onda.estrategias.values())
        if sobresalto is not None and not reflejo_activo:
            imp = impulsos.get(SEGURIDAD)
            reflejo = next((d for d in self.catalogo.todas() if d.reflejo and d.sirve(SEGURIDAD, None)), None)
            if imp is not None and reflejo is not None:
                p = self._activar(ctx, reflejo, SEGURIDAD, float(imp.carga["intensidad"]), float(imp.carga["objetivo"]))
                notas["reflejo"] = True
                notas["interrumpe"] = ejecutada is not None and ejecutada != p.id and not ejecutada.startswith("innato:")

        activa_por_impulso = {p.carga["impulso"]: p for p in onda.estrategias.values() if p.sistema == self.sistema and not p.carga["reflejo"]}
        for nombre, imp in impulsos.items():
            intensidad, objetivo = float(imp.carga["intensidad"]), float(imp.carga["objetivo"])
            if intensidad <= objetivo:
                continue
            actual = activa_por_impulso.get(nombre)
            if actual is not None:
                # Continuidad, salvo que otra elegible la supere con margen claro (histéresis).
                mejor_def = self._mejor(ctx, nombre, imp.carga.get("rasgo"), intensidad)
                if mejor_def is None or mejor_def.nombre == actual.carga["nombre"] or \
                        self._puntuacion(nombre, mejor_def) < self._puntuacion(nombre, self.catalogo.get(actual.carga["nombre"])) + self.MARGEN_SUSTITUCION:
                    continue
                self._cerrar(ctx, actual, est.SUSTITUIDA)
                notas["sustituciones"] += 1
                self._activar(ctx, mejor_def, nombre, intensidad, objetivo, ctx_paso=True)
                continue
            definicion = self._elegir(ctx, nombre, imp.carga.get("rasgo"), intensidad)
            if definicion is not None:
                self._activar(ctx, definicion, nombre, intensidad, objetivo, ctx_paso=True)

        notas["activas"] = [p.carga["nombre"] for p in onda.estrategias.values() if p.sistema == self.sistema]
        onda.notas[f"estrategias_{self.sistema}"] = notas

    def _puntuacion(self, impulso: str, d: Optional[Definicion]) -> float:
        """Valor aprendido + prioridad innata / 100."""
        if d is None:
            return -1.0
        return self.valor.get((impulso, d.nombre), self.VALOR_INICIAL) + d.prioridad / 100.0

    def _disponibles(self, ctx: Contexto, impulso: str, rasgo: Optional[str], intensidad: float) -> Tuple[List[Definicion], List[Definicion]]:
        elegibles = [d for d in self.catalogo.todas()
                     if not d.reflejo and not d.ultimo_recurso and d.sirve(impulso, rasgo) and d.elegible(ctx, impulso, intensidad)]
        return elegibles, [d for d in elegibles if self.enfriando.get((impulso, d.nombre), -1) <= ctx.latido]

    def _mejor(self, ctx: Contexto, impulso: str, rasgo: Optional[str], intensidad: float) -> Optional[Definicion]:
        _, disponibles = self._disponibles(ctx, impulso, rasgo, intensidad)
        return max(disponibles, key=lambda d: self._puntuacion(impulso, d)) if disponibles else None

    def _elegir(self, ctx: Contexto, impulso: str, rasgo: Optional[str], intensidad: float) -> Optional[Definicion]:
        elegibles, disponibles = self._disponibles(ctx, impulso, rasgo, intensidad)
        if not disponibles:
            ultimos = [d for d in self.catalogo.todas() if d.ultimo_recurso and d.sirve(impulso, rasgo)]
            if elegibles and impulso == SEGURIDAD:     # todas agotadas: respuesta innata de último recurso
                return next((d for d in ultimos if not d.cualquier_impulso), None)
            # Nada elegible: en un mundo que no deja esperar, seguir en movimiento.
            return next((d for d in ultimos if d.cualquier_impulso and d.elegible(ctx, impulso, intensidad)), None)
        if ctx.con_experiencia and len(disponibles) > 1 and ctx.azar.probabilidad(self.EXPLORACION * ctx.arquetipo.apertura):
            return ctx.azar.eleccion(disponibles)
        return max(disponibles, key=lambda d: self._puntuacion(impulso, d))

    def _activar(self, ctx: Contexto, definicion: Definicion, impulso: str, intensidad: float, objetivo: float,
                 ctx_paso: bool = False) -> Pieza:
        p = est.nueva(self.sistema, definicion, impulso, intensidad, objetivo, ctx.latido)
        if ctx_paso:      # fase inicial de su máquina de estados
            p = est.nueva(self.sistema, definicion, impulso, intensidad, objetivo, ctx.latido, paso=definicion.paso(ctx, p))
        return ctx.onda.activar(p, self)

    def _cerrar(self, ctx: Contexto, p: Pieza, estado: str) -> None:
        c = p.carga
        if ctx.con_experiencia and not c["reflejo"]:
            clave = (c["impulso"], c["nombre"])
            v = self.valor.get(clave, self.VALOR_INICIAL)
            tramo = max(float(c["valor_inicial"]) - float(c["objetivo"]), 0.05)
            merito = max(-1.0, min(1.0, float(c.get("merito", 0.0)) / tramo))
            self.valor[clave] = v + self.TASA * float(c["valor_inicial"]) * (merito - v)
        ctx.onda.cerrar(p, estado, self)


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
        previo = ctx.onda.ei("Feedback").get("feedback")
        antes = previo.carga["deficits"] if previo is not None else ahora
        cambios = {k: round(antes.get(k, v) - v, 4) for k, v in ahora.items()}
        self.registrar(ctx, self.pieza(ctx, "feedback", arousal=0.0,
                                       carga={"valor": round(sum(cambios.values()), 4), "por_impulso": cambios, "deficits": ahora}))


def crear_s1() -> Sistema:
    catalogo = Catalogo(estrategias_s1())
    return Sistema("S1", "Supervivencia", [
        Modulo("Sentir", [Imagen()]),
        Modulo("Interpretar", [Objeto(), Supervivencia()]),
        Modulo("Reaccionar", [Reflejo(), Impulso(), Feedback(), Estrategia(catalogo)]),
        Modulo("Actuar", [Accion(catalogo)]),
    ])
