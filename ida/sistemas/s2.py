"""S2 · Valor: motivación, sentimiento y relación social. Trabaja con lo que le sobra a S1.

| Etapa       | Componente       | Produce |
|-------------|------------------|---------|
| Sentir      | Patron           | Patrón: qué clase de cosa es y qué recuerda de ella |
| Sentir      | Recuerdo         | Recuerdo: lo que la memoria asocia a objetos e impulsos (con el interruptor de evocación) |
| Sentir      | Emocion          | Emoción: el estado afectivo sentido (en ``ef``, sin coste; aún no lo consume nadie) |
| Interpretar | Sujeto           | Sujeto (mismo id que el Objeto) |
| Interpretar | Valor            | Valor: motivacional, potencia, sentimental y social de cada sujeto; valencia |
| Reaccionar  | Exteriorizacion  | Exteriorización del estado afectivo (en ``ef``, sin coste) |
| Reaccionar  | Impulso          | Impulso propio: Exploración (apertura × novedad) |
| Reaccionar  | Feedback         | Feedback de S2: mejora del placer y bajada del estrés |
| Reaccionar  | Estrategia       | Estrategias de valor: explorar, refugiarse (hogar valorado), recordar_comida |
| Actuar      | Accion           | Acción de cada estrategia activa de S2, con su origen |
| Actuar      | Anticipacion     | Expectativa: valencia esperada si se ejecuta su propuesta (con el interruptor de expectativa) |
"""

import math
from typing import Any, Dict, List, Optional, Tuple

from ida.core.arquitectura import Componente, Contexto, Modulo, Sistema, expectativa_ejecutada
from ida.core.estrategia import Catalogo, Definicion, Plan, Propuesta, estado_plan, paso_actual
from ida.core.pieza import Pieza, acotar
from ida.core.vocabulario import Afecto, EstadoSaber, Relacion, Verbo
from ida.sistemas.comun import PESO_PREDICCION, Accion, Anticipacion, Estrategia, Peticion, cautela, al_alcance, alarma, apetito, lugares, mejor, objetos


EXPLORACION = "exploracion"
SEGURIDAD = "seguridad"      # impulso de S1 al que también sirve refugiarse


class Patron(Componente):
    tipo = "Patron"
    entradas = ("Objeto",)

    def reactiva(self, ctx: Contexto) -> None:
        for o in objetos(ctx):
            vistos = ctx.memoria.clases_vistas.get(o.clase, 0)
            self.percibir(ctx, self.pieza(ctx, o.id, arousal=o.arousal * 0.8,
                                          carga={"clase": o.clase, "familiaridad": round(min(1.0, vistos / 20.0), 3)},
                                          entradas=[o.id]))

    def activa(self, ctx: Contexto) -> None:
        """Dimensión activa: recupera lo que la experiencia dice de cada clase."""
        if not ctx.con_experiencia:
            return
        for pid, p in ctx.onda.ev("Patron").items():
            recuerdos = {v.value: round(ctx.memoria.recordar(v, p.clase)[0], 2)
                         for v in (Verbo.COMER, Verbo.MOVER, Verbo.ATACAR, Verbo.COGER) if ctx.memoria.recordar(v, p.clase)[1]}
            if recuerdos:
                self.modificar(ctx, p, carga={"recuerdos": recuerdos})


class Emocion(Componente):
    """Estado afectivo interno sentido por el individuo, tal como lo calcula ``Soma``.

    Se registra en ``ef`` a coste cero: no entra en ``ev``, así que no cambia la tensión ni la
    apertura de episodios, que leen todos los canales de ``ev``.
    """

    tipo = "Emocion"
    entradas = ("Interocepcion", "Patron")

    def reactiva(self, ctx: Contexto) -> None:
        self.registrar(ctx, self.pieza(ctx, "emocion", arousal=ctx.soma.estres,
                                       carga={"valencia": round(ctx.soma.valencia, 3), "afecto": ctx.soma.afecto.value,
                                              "placer": round(ctx.soma.placer, 1)},
                                       entradas=["Interocepcion", "Patron"]))


class Recuerdo(Componente):
    """Recuperación evocada (bloque E, E5; decisión 22): con la potencia que sobra tras la pasada reactiva,
    las piezas evocadoras traen a la atención lo que la memoria les asocia, como piezas ``Recuerdo``:
    - cada objeto a la vista: si se sabe que su clase hace daño (demostrado);
    - cada impulso que satisface lo nutritivo, con hambre (≥ 0,35): las clases que se creen nutritivas
      (confianza ≥ 0,55) y no se saben peligrosas, con dónde se vieron por última vez.
    Lo recuperado se reconsolida: se refresca y, con búfer diurno, se persiste de noche. ``Valor`` y la
    estrategia ``recordar_comida`` leen estas piezas en lugar de la memoria."""

    tipo = "Recuerdo"
    POTENCIA_MINIMA = 0.25     # fracción de potencia que debe sobrar para recordar
    POTENCIA_REPASO = 0.5      # E6: fracción de potencia que debe sobrar para repasar

    def activa(self, ctx: Contexto) -> None:
        if not (ctx.con_experiencia and ctx.memoria.activa):
            return
        if ctx.perfil.mecanismos.evocacion:
            self._evocar(ctx)
        if ctx.perfil.mecanismos.repaso:
            self._repasar(ctx)

    def _repasar(self, ctx: Contexto) -> None:
        """Repaso en calma (bloque E, E6; decisión 21): en calma, con potencia de sobra y sin recuerdos
        evocados en este latido, trae lo reciente de más fuerza y lo refuerza. Solo en calma, para que
        repasar lo negativo no se convierta en rumiación."""
        onda = ctx.onda
        if ctx.soma.afecto != Afecto.CALMA or onda.ev("Recuerdo"):
            return
        if onda.potencia_max <= 0 or onda.potencia_restante() < self.POTENCIA_REPASO * onda.potencia_max:
            return
        for nodo, clase in ctx.memoria.recientes_para_repaso(ctx.latido):
            if self.percibir(ctx, self.pieza(ctx, f"repaso:{nodo}", arousal=0.2, carga={"clase": clase, "relacion": None,
                                                                                    "demostrada": False, "donde": None, "repaso": True})) is not None:
                ctx.memoria.repasar(nodo, clase, ctx.latido)

    def _evocar(self, ctx: Contexto) -> None:
        onda, mem, ahora = ctx.onda, ctx.memoria, ctx.latido
        if onda.potencia_max <= 0 or onda.potencia_restante() < self.POTENCIA_MINIMA * onda.potencia_max:
            return
        for clase in sorted({o.clase for o in objetos(ctx)}):
            if mem.demostrada(clase, Relacion.PELIGROSO, ahora):
                self._traer(ctx, clase, Relacion.PELIGROSO, None)
        hambre = any(i.carga.get("rasgo") == "nutritivo" and float(i.carga.get("intensidad", 0.0)) > 0.0 for i in onda.ef("Impulso").values())
        if hambre and ctx.soma.hambre() >= 0.35:
            for (clase, rel), prop in list(mem.saber.items()):
                if rel == Relacion.NUTRITIVO and prop.confianza >= 0.55 and not mem.demostrada(clase, Relacion.PELIGROSO, ahora):
                    self._traer(ctx, clase, rel, mem.donde_esta(clase))

    def _traer(self, ctx: Contexto, clase: str, rel: Relacion, donde: Optional[str]) -> None:
        prop = ctx.memoria.proposicion(clase, rel)
        if prop is None:
            return
        arousal = acotar(0.5 * prop.confianza)
        if self.percibir(ctx, self.pieza(ctx, f"{clase}|{rel.name}", arousal=arousal, confianza=prop.confianza,
                                         carga={"clase": clase, "relacion": rel, "demostrada": prop.estado(ctx.latido) == EstadoSaber.DEMOSTRADA,
                                                "donde": donde})) is not None:
            ctx.memoria.reconsolidar((clase, rel), ctx.latido, arousal)


def _recordado(ctx: Contexto, clase: str, rel: Relacion) -> Optional[Pieza]:
    return ctx.onda.ev("Recuerdo").get(f"{clase}|{rel.name}")


class Sujeto(Componente):
    tipo = "Sujeto"
    entradas = ("Patron",)

    def reactiva(self, ctx: Contexto) -> None:
        for o in objetos(ctx):
            self.percibir(ctx, self.pieza(ctx, o.id, arousal=o.arousal * 0.5, carga={"clase": o.clase}, entradas=[o.id]))


class Valor(Componente):
    """Lo que vale cada sujeto para mí (decisión 9), en cuatro dimensiones:
    - **motivacional**: lo que satisface una necesidad actual (nutritivo × apetito, y lo útil según la
      apertura);
    - **potencia**: la fuerza percibida del sujeto (su rasgo de peligro; el cansancio del sujeto no se
      percibe todavía);
    - **sentimental**: la valencia que la memoria asocia a la clase (recuerdos de sus efectos; −0,5 si
      se sabe peligrosa);
    - **social**: 0 mientras no haya varios individuos.
    La valencia se mantiene como combinación de las dimensiones (0,5 · motivacional + 0,5 · sentimental
    + social − potencia · neuroticismo), para las estrategias que ya la leen."""

    tipo = "Valor"
    entradas = ("Sujeto",)

    def reactiva(self, ctx: Contexto) -> None:
        arq, mem = ctx.arquetipo, ctx.memoria
        for o in objetos(ctx):
            motivacional = o.rasgo("nutritivo") * apetito(ctx) + 0.5 * o.rasgo("recurso") * arq.apertura
            potencia = o.rasgo("peligro")
            patron = ctx.onda.ev("Patron").get(o.id)
            recuerdos = patron.carga.get("recuerdos", {}) if patron else {}
            sentimental = math.tanh(sum(recuerdos.values()) / 5.0) if recuerdos else 0.0
            if ctx.perfil.mecanismos.evocacion:   # bloque E, E5: lo recuperado, no la memoria
                peligrosa = (r := _recordado(ctx, o.clase, Relacion.PELIGROSO)) is not None and bool(r.carga.get("demostrada"))
            else:
                peligrosa = mem.demostrada(o.clase, Relacion.PELIGROSO, ctx.latido)
            if peligrosa:
                sentimental -= 0.5
            social = 0.0
            valencia = acotar(0.5 * motivacional + 0.5 * sentimental + social - potencia * arq.neuroticismo, -1.0, 1.0)
            self.percibir(ctx, self.pieza(ctx, o.id, arousal=abs(valencia),
                                          carga={"clase": o.clase, "valencia": round(valencia, 3), "motivacional": round(motivacional, 3),
                                                 "potencia": round(potencia, 3), "sentimental": round(sentimental, 3), "social": social},
                                          entradas=[o.id, "Patron"]))


class Exteriorizacion(Componente):
    tipo = "Exteriorizacion"

    def reactiva(self, ctx: Contexto) -> None:
        self.registrar(ctx, self.pieza(ctx, "exteriorizacion", arousal=ctx.soma.estres,
                                       carga={"afecto": ctx.soma.afecto.value, "placer": round(ctx.soma.placer, 1)}))


class Impulso(Componente):
    """Impulsos propios de S2 (decisión 10): Exploración, con intensidad cruda = apertura × la novedad
    máxima a la vista (lugares y objetos). Ya no modula acciones: el «no comas esto» lo resuelve la
    elección del objeto de las estrategias (C1)."""

    tipo = "Impulso"

    def reactiva(self, ctx: Contexto) -> None:
        novedad = max([lugar.rasgo("novedad") for lugar in lugares(ctx)] + [o.rasgo("novedad") for o in objetos(ctx)] + [0.0])
        intensidad = acotar(ctx.arquetipo.apertura * novedad)
        self.registrar(ctx, self.pieza(ctx, EXPLORACION, arousal=intensidad,
                                       carga={"intensidad": round(intensidad, 4), "objetivo": 0.0, "rasgo": None}))


CANSANCIO = "cansancio"


def _peligro(ctx: Contexto) -> float:
    a = alarma(ctx)
    return float(a.carga["peligro"]) if a else 0.0


# --- Estrategias de valor de S2 (decisión 10; tabla del C0) ---------------------------------------
class Explorar(Definicion):
    """Exploración (antes ``Curiosidad``): sin peligro (< 0,3) ni mucha hambre (< 0,6), recorrer el
    lugar más nuevo (ponderado por lo que se recuerda de él) y coger lo útil al alcance. Son dos
    acciones de la misma fase: las propone las dos y decide el Tribunal, como antes."""

    nombre = "explorar"
    impulsos = (EXPLORACION,)
    prioridad = 10

    @staticmethod
    def _calma(ctx: Contexto) -> bool:
        return _peligro(ctx) < 0.3 and ctx.soma.hambre() < 0.6

    @staticmethod
    def _nuevo(ctx: Contexto) -> Optional[Pieza]:
        def puntuar(lugar: Pieza) -> float:
            s = lugar.rasgo("novedad") - lugar.rasgo("peligro")
            if ctx.con_experiencia and ctx.memoria.activa:
                s += max(-0.4, min(0.3, ctx.memoria.valor_lugar(lugar.id) * 0.15))
            return s

        evitar = cautela(ctx)[1]
        nuevo = mejor([lugar for lugar in lugares(ctx) if lugar.id not in evitar], puntuar)
        return nuevo if nuevo is not None and nuevo.rasgo("novedad") > 0.0 and nuevo.rasgo("peligro") < 0.5 else None

    @staticmethod
    def _util(ctx: Contexto) -> Optional[Pieza]:
        if ctx.soma.cargando is not None:
            return None
        return mejor([o for o in objetos(ctx) if al_alcance(o) and o.rasgo("recurso") >= 0.4 and o.rasgo("peligro") < 0.3],
                     lambda o: o.rasgo("recurso") + o.rasgo("novedad"))

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return self._calma(ctx) and (self._util(ctx) is not None or self._nuevo(ctx) is not None)

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> List[Propuesta]:
        apertura = ctx.arquetipo.apertura
        propuestas = []
        nuevo = self._nuevo(ctx)
        if nuevo is not None:
            propuestas.append(Propuesta(Verbo.MOVER, nuevo.id, acotar(0.15 + 0.25 * apertura * nuevo.rasgo("novedad")), 0.5,
                                        "curiosidad: explorar", clase=nuevo.clase))
        util = self._util(ctx)
        if util is not None:
            propuestas.append(Propuesta(Verbo.COGER, util.id, acotar(0.2 + 0.3 * apertura * util.rasgo("recurso")), 0.5,
                                        f"curiosidad: coger {util.clase}", clase=util.clase))
        return propuestas


class Refugiarse(Definicion):
    """Cansancio y Seguridad (antes ``Hogar``): el refugio que se valora, el hogar recordado. Volver a
    él con cansancio o peligro (≥ 0,4), por la vista o por la ruta del hipocampo, y descansar allí;
    con mucho cansancio y en calma también se descansa sin hogar (decisión 10)."""

    nombre = "refugiarse"
    impulsos = (CANSANCIO, SEGURIDAD)
    prioridad = 10

    @staticmethod
    def _estado(ctx: Contexto) -> Tuple[float, float, Optional[str], str]:
        hogar = ctx.memoria.hogar() if ctx.perfil.hogar else None
        aqui = ctx.observacion.ubicacion if ctx.observacion else ""
        return _peligro(ctx), ctx.soma.cansancio(), hogar, aqui

    def _puerta(self, ctx: Contexto) -> Optional[Pieza]:
        peligro, cansancio, hogar, aqui = self._estado(ctx)
        if not (hogar and hogar != aqui and (cansancio >= 0.4 or peligro >= 0.4)):
            return None
        puerta = next((lugar for lugar in lugares(ctx) if lugar.id == hogar), None)
        if puerta is None and ctx.con_experiencia:
            salto = ctx.memoria.ruta(aqui, hogar)
            if salto:
                # El retorno por memoria espacial no debe pisar la huida si la casilla implica peligro
                umbral_p = 0.2 if peligro >= 0.4 else 0.8
                puerta = next((lugar for lugar in lugares(ctx) if lugar.id == salto and lugar.rasgo("peligro") < umbral_p), None)
        return puerta

    def _descansar(self, ctx: Contexto, impulso: str) -> bool:
        peligro, cansancio, hogar, aqui = self._estado(ctx)
        return impulso == CANSANCIO and cansancio >= 0.6 and peligro < 0.3 and (hogar is None or hogar == aqui or cansancio >= 0.85)

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return ctx.perfil.duerme and (self._descansar(ctx, impulso) or self._puerta(ctx) is not None)

    def paso(self, ctx: Contexto, estrategia: Pieza) -> str:
        return "descansar" if self._descansar(ctx, estrategia.carga["impulso"]) else "volver"

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        peligro, cansancio, hogar, aqui = self._estado(ctx)
        if estrategia.carga.get("paso") == "descansar":
            return Propuesta(Verbo.DORMIR, aqui, acotar(0.4 + 0.5 * cansancio), 0.8,
                             "cansancio: dormir" + (" en el hogar" if hogar == aqui else ""))
        puerta = self._puerta(ctx)
        if puerta is None:
            return None
        return Propuesta(Verbo.MOVER, puerta.id, acotar(0.3 + 0.5 * max(cansancio, peligro * 0.7)), 0.7, "volver al hogar", clase=puerta.clase)


class RecordarComida(Plan):
    """Necesidades que satisface lo nutritivo (antes ``Orientacion``): con hambre (≥ 0,35), sin peligro
    (< 0,4) y sin comida a la vista, ir por la ruta del hipocampo hacia donde se vio una clase que se
    cree nutritiva (confianza ≥ 0,55) y no se sabe peligrosa. Si llega y no está, la olvida.

    Con el interruptor de plan (bloque F, F2) es un ``Plan``: al activarse elige destino (confianza y,
    a igualdad, fuerza del nodo en el grafo semántico) y fija la ruta completa del mapa más un paso
    final, encontrar la clase. Sorpresa (el paso falla): estar fuera de la ruta, no ver la puerta
    esperada o llegar y no encontrar la comida (entonces la olvida)."""

    nombre = "recordar_comida"
    rasgo = "nutritivo"
    prioridad = 10

    @staticmethod
    def _plan(ctx: Contexto) -> Optional[Tuple[Pieza, float, str]]:
        if not ctx.con_experiencia or not ctx.memoria.activa:
            return None
        hambre = ctx.soma.hambre()
        if _peligro(ctx) >= 0.4 or hambre < 0.35 or any(o.rasgo("nutritivo") >= 0.3 for o in objetos(ctx)):
            return None
        aqui = ctx.observacion.ubicacion if ctx.observacion else ""
        if not aqui:
            return None
        if ctx.perfil.mecanismos.evocacion:   # bloque E, E5: lo recuperado (piezas Recuerdo), no la memoria
            candidatos = sorted(((r.carga["clase"], r.confianza, r.carga["donde"]) for r in ctx.onda.ev("Recuerdo").values()
                                 if r.carga.get("relacion") == Relacion.NUTRITIVO), key=lambda item: -item[1])
        else:
            candidatos = sorted(
                ((clase, prop.confianza, ctx.memoria.donde_esta(clase)) for (clase, rel), prop in ctx.memoria.saber.items()
                 if rel == Relacion.NUTRITIVO and prop.confianza >= 0.55 and not ctx.memoria.demostrada(clase, Relacion.PELIGROSO, ctx.latido)),
                key=lambda item: -item[1],
            )
        for clase, confianza, destino in candidatos:
            if destino == aqui and not any(o.clase == clase for o in objetos(ctx)):
                ctx.memoria.olvidar_donde(clase)
                continue
            if destino and destino != aqui:
                salto = ctx.memoria.ruta(aqui, destino)
                puerta = next((lugar for lugar in lugares(ctx) if lugar.id == salto and lugar.rasgo("peligro") < 0.6), None) if salto else None
                if puerta is not None:
                    return puerta, acotar(0.25 + 0.45 * hambre * confianza), clase
        return None

    @staticmethod
    def _candidatos_plan(ctx: Contexto) -> List[Tuple[str, float, Optional[str]]]:
        """Con plan: los mismos candidatos, con la fuerza del nodo del grafo como desempate."""
        if not ctx.con_experiencia or not ctx.memoria.activa:
            return []
        hambre = ctx.soma.hambre()
        if _peligro(ctx) >= 0.4 or hambre < 0.35 or any(o.rasgo("nutritivo") >= 0.3 for o in objetos(ctx)):
            return []
        if ctx.perfil.mecanismos.evocacion:
            crudos = [(r.carga["clase"], r.confianza, r.carga["donde"]) for r in ctx.onda.ev("Recuerdo").values()
                      if r.carga.get("relacion") == Relacion.NUTRITIVO]
        else:
            crudos = [(clase, prop.confianza, ctx.memoria.donde_esta(clase)) for (clase, rel), prop in ctx.memoria.saber.items()
                      if rel == Relacion.NUTRITIVO and prop.confianza >= 0.55 and not ctx.memoria.demostrada(clase, Relacion.PELIGROSO, ctx.latido)]
        grafo = ctx.memoria.grafo
        return sorted(crudos, key=lambda c: (-c[1], -float(grafo.get(f"Objeto:{c[0]}", {}).get("fuerza", 0.0)), c[0]))

    def construir(self, ctx: Contexto, estrategia: Pieza) -> Optional[List[Dict[str, Any]]]:
        aqui = ctx.observacion.ubicacion if ctx.observacion else ""
        if not aqui:
            return None
        for clase, confianza, destino in self._candidatos_plan(ctx):
            if destino and destino != aqui:
                camino = ctx.memoria.camino(aqui, destino)
                if camino:
                    return [{"meta": n} for n in camino] + [{"meta": "encontrar", "clase": clase, "en": destino, "confianza": confianza}]
        return None

    def cumplido(self, ctx: Contexto, paso: Dict[str, Any], estado: Dict[str, Any]) -> bool:
        if paso["meta"] == "encontrar":
            return any(o.clase == paso["clase"] for o in objetos(ctx))
        return ctx.observacion is not None and ctx.observacion.ubicacion == paso["meta"]

    def fallido(self, ctx: Contexto, paso: Dict[str, Any], estado: Dict[str, Any]) -> bool:
        aqui = ctx.observacion.ubicacion if ctx.observacion else ""
        if paso["meta"] == "encontrar":
            if aqui == paso["en"]:
                ctx.memoria.olvidar_donde(paso["clase"])    # llegó y no está
            return True                                     # llegó y no está, o se alejó del destino
        i = int(estado["i"])
        previo = estado["pasos"][i - 1]["meta"] if i > 0 else None
        if aqui == previo:   # donde esperaba estar: ¿está la puerta esperada?
            return not any(lugar.id == paso["meta"] and lugar.rasgo("peligro") < 0.6 for lugar in lugares(ctx))
        return True          # fuera de la ruta

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        if ctx.perfil.mecanismos.plan:
            aqui = ctx.observacion.ubicacion if ctx.observacion else ""
            return bool(aqui) and any(d and d != aqui for _, _, d in self._candidatos_plan(ctx))
        return self._plan(ctx) is not None

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        if ctx.perfil.mecanismos.plan:
            paso = paso_actual(estrategia)
            if paso is None or paso["meta"] == "encontrar":
                return None
            final = estado_plan(estrategia)["pasos"][-1]   # type: ignore[index]
            puerta = next((lugar for lugar in lugares(ctx) if lugar.id == paso["meta"] and lugar.rasgo("peligro") < 0.6), None)
            if puerta is None:
                return None
            ar = acotar(0.25 + 0.45 * ctx.soma.hambre() * float(final.get("confianza", 0.55)))
            return Propuesta(Verbo.MOVER, puerta.id, ar, 0.65, f"plan: recordar {final.get('clase', '')}", clase=puerta.clase)
        plan = self._plan(ctx)
        if plan is None:
            return None
        puerta, ar, clase = plan
        return Propuesta(Verbo.MOVER, puerta.id, ar, 0.65, f"orientación: recordar {clase}", clase=puerta.clase)


class Feedback(Componente):
    """Feedback de S2 (decisión 5): mejora del placer y bajada del estrés respecto al latido anterior,
    (Δ placer) / 100 − Δ estrés. Positivo = mejora. Es el mérito de las estrategias de S2, sea cual
    sea el impulso al que sirven (S2 juzga con su criterio, el valor)."""

    tipo = "Feedback"

    def reactiva(self, ctx: Contexto) -> None:
        placer, estres = float(ctx.soma.placer), float(ctx.soma.estres)
        previo = ctx.onda.ei("Feedback").get(f"feedback:{self.sistema}")
        antes = previo.carga["estado"] if previo is not None else {"placer": placer, "estres": estres}
        valor = round((placer - antes["placer"]) / 100.0 - (estres - antes["estres"]), 4)
        e = expectativa_ejecutada(ctx.onda, self.sistema) if ctx.perfil.mecanismos.expectativa else None
        if e is not None and "valencia" in e.carga["esperado"]:
            # Bloque F, F1: error de predicción con signo sobre la valencia esperada.
            b = e.carga["base"]
            obtenida = (placer / 100.0 - float(b.get("placer", placer / 100.0))) - (estres - float(b.get("estres", estres)))
            valor = round(valor + PESO_PREDICCION * (obtenida - float(e.carga["esperado"]["valencia"])), 4)
        impulsos = {**ctx.onda.ef("Impulso"), **ctx.onda.ef("Intencion")}
        self.registrar(ctx, self.pieza(ctx, f"feedback:{self.sistema}", arousal=0.0,
                                       carga={"valor": valor, "por_impulso": dict.fromkeys(impulsos, valor),
                                              "estado": {"placer": placer, "estres": estres}}))


def estrategias_s2() -> List[Definicion]:
    return [Explorar(), Refugiarse(), RecordarComida()]


def crear_s2() -> Sistema:
    catalogo = Catalogo(estrategias_s2())
    return Sistema("S2", "Valor", [
        Modulo("Sentir", [Patron(), Emocion(), Recuerdo()]),
        Modulo("Interpretar", [Sujeto(), Valor()]),
        Modulo("Reaccionar", [Exteriorizacion(), Impulso(), Feedback(), Estrategia(catalogo)]),
        Modulo("Actuar", [Accion(catalogo), Peticion(catalogo), Anticipacion(("placer", "estres"))]),
    ])
