"""Componentes del Core: Sentir (sensores) y Actuar (Tribunal y actuadores). Exentos de peaje.

Sentir convierte la ``Observacion`` que entrega el mundo en piezas de ``ev``:
- ``Interocepcion``: una pieza por constante vital, con su variación respecto al latido anterior.
- ``Propiocepcion``: dónde está el individuo y qué lleva encima.
- ``Escena``: una pieza por entidad percibida (incluidos los lugares a los que puede ir).

Actuar: el ``Tribunal`` elige un candidato de ``acc["Ejecucion"]`` y el ``Actuador`` de ese
verbo lo materializa en el mundo. Nada se ejecuta sin pasar por el Tribunal.
"""

from typing import Any, Callable, Dict, List, Tuple

from ida.core.arquitectura import Componente, Contexto
from ida.core.mundo import Efecto
from ida.core.pieza import Pieza
from ida.core.soma import VITALES
from ida.core.vocabulario import Verbo


class Interocepcion(Componente):
    tipo = "Interocepcion"

    def reactiva(self, ctx: Contexto) -> None:
        previo = ctx.onda.ei("Interocepcion")
        for nombre in VITALES:
            valor = float(getattr(ctx.soma, nombre))
            antes = float(previo[nombre].carga["valor"]) if nombre in previo else valor
            p = self.pieza(ctx, nombre, arousal=(100.0 - valor) / 100.0, carga={"valor": round(valor, 2), "delta": round(valor - antes, 2)})
            self.percibir(ctx, p, coste=0)


class Propiocepcion(Componente):
    tipo = "Propiocepcion"

    def reactiva(self, ctx: Contexto) -> None:
        obs = ctx.observacion
        p = self.pieza(ctx, "yo", arousal=0.1, carga={"ubicacion": obs.ubicacion if obs else "", "cargando": ctx.soma.cargando})
        self.percibir(ctx, p, coste=0)


class Escena(Componente):
    tipo = "Escena"

    def reactiva(self, ctx: Contexto) -> None:
        if ctx.observacion is None:
            return
        for e in ctx.observacion.entidades:
            r = e.rasgos
            cerca = r.get("proximidad", 0.0)
            saliencia = max(r.get("peligro", 0.0) * max(cerca, 0.3), r.get("nutritivo", 0.0) * cerca, 0.4 * r.get("novedad", 0.0))
            p = self.pieza(ctx, e.id, arousal=saliencia, carga={"clase": e.clase, "rasgos": dict(r), "datos": dict(e.datos)})
            self.percibir(ctx, p, coste=0)
            if ctx.memoria.activa:
                ctx.memoria.ver_clase(e.clase)


class Tribunal(Componente):
    """Arbitra los candidatos de Ejecución de S1, S2 y S3.

    Puntuación = arousal·estrés + confianza·(1 − estrés) + experiencia.
    - Con estrés manda la urgencia; en calma, la confianza.
    - La experiencia (activa y proactiva) sesga con un peso pequeño los candidatos que ya existen;
      no añade candidatos.
    - Si los dos mejores casi empatan, decide el azar.
    - Acecho: un candidato con poca confianza y poca urgencia no se ejecuta enseguida; su
      confianza se acumula latido a latido hasta superar el umbral.
    """

    tipo = "Decision"
    EMPATE = 0.02
    UMBRAL_ACECHO = 0.35

    def __init__(self):
        super().__init__("Tribunal")
        self.acumulado: Dict[Tuple[str, str], float] = {}

    def reactiva(self, ctx: Contexto) -> None:
        candidatos: List[Pieza] = list(ctx.onda.acc("Ejecucion").values())
        if not candidatos:
            self._decidir(ctx, Verbo.ESPERAR, "", "", "sin candidatos", None, [])
            return
        estres = ctx.soma.estres
        peso = ctx.perfil.peso_experiencia if ctx.con_experiencia else 0.0
        evaluados: List[Dict[str, Any]] = []
        for c in candidatos:
            base = c.arousal * estres + c.confianza * (1.0 - estres)
            act, pro = ctx.memoria.sesgo(c.carga["verbo"], c.carga.get("clase", ""), ctx.latido) if peso else (0.0, 0.0)
            evaluados.append({"pieza": c, "base": base, "activa": act, "proactiva": pro, "total": base + peso * (act + pro)})
        evaluados.sort(key=lambda e: -e["total"])
        ganador = evaluados[0]
        if len(evaluados) > 1 and evaluados[0]["total"] - evaluados[1]["total"] <= self.EMPATE:
            ganador = ctx.azar.eleccion(evaluados[:2])
        sin_experiencia = max(evaluados, key=lambda e: e["base"])
        ctx.onda.notas["experiencia_cambio"] = sin_experiencia["pieza"].id != ganador["pieza"].id
        ctx.onda.notas["evaluados"] = [
            {
                "id": e["pieza"].id,
                "sistema": e["pieza"].sistema,
                "verbo": e["pieza"].carga["verbo"].value,
                "objetivo": e["pieza"].carga["objetivo"],
                "motivo": e["pieza"].carga.get("motivo", ""),
                "base": round(e["base"], 3),
                "activa": round(e["activa"], 3),
                "proactiva": round(e["proactiva"], 3),
                "total": round(e["total"], 3),
            }
            for e in evaluados[:8]
        ]

        g: Pieza = ganador["pieza"]
        clave = (g.carga["verbo"].value, g.carga["objetivo"])
        urgente = g.arousal >= 0.8 or ctx.soma.alimentacion <= ctx.soma.HAMBRE_CRITICA
        puede_esperar = Verbo.ESPERAR in ctx.verbos      # si el mundo no admite esperar, no se acecha
        if puede_esperar and g.confianza < self.UMBRAL_ACECHO and not urgente:
            self.acumulado[clave] = self.acumulado.get(clave, 0.0) + g.confianza
            if self.acumulado[clave] < self.UMBRAL_ACECHO:
                self._decidir(ctx, Verbo.ACECHAR, g.carga["objetivo"], g.carga.get("clase", ""), f"acecha: {g.carga.get('motivo', '')}", g, evaluados)
                return
        self.acumulado.clear()
        self._decidir(ctx, g.carga["verbo"], g.carga["objetivo"], g.carga.get("clase", ""), g.carga.get("motivo", ""), g, evaluados)

    def _decidir(self, ctx: Contexto, verbo: Verbo, objetivo: str, clase: str, motivo: str, ganador, evaluados) -> None:
        datos = dict(ganador.carga.get("datos", {})) if ganador is not None else {}
        d = self.pieza(
            ctx,
            "decision",
            arousal=ganador.arousal if ganador is not None else 0.0,
            confianza=ganador.confianza if ganador is not None else 1.0,
            carga={"verbo": verbo, "objetivo": objetivo, "clase": clase, "motivo": motivo, "datos": datos,
                   "sistema": ganador.sistema if ganador is not None else "CORE"},
            entradas=[ganador.id] if ganador is not None else [],
        )
        self.registrar(ctx, d)
        ctx.extra["decision"] = d


class Actuador(Componente):
    """Materializa en el mundo la decisión del Tribunal para un verbo concreto."""

    tipo = "Ejecucion"

    def __init__(self, verbo: Verbo, ejecutar: Callable[[Verbo, str, Dict[str, Any]], Efecto]):
        super().__init__(f"Actuador_{verbo.value}")
        self.verbo = verbo
        self._ejecutar = ejecutar

    def reactiva(self, ctx: Contexto) -> None:
        d = ctx.extra.get("decision")
        if d is None:
            return
        verbo = d.carga["verbo"]
        # ACECHAR y LEER no se ejecutan en el mundo: si el mundo admite ESPERAR, lo hace su actuador.
        if verbo in (Verbo.ACECHAR, Verbo.LEER) and self.verbo == Verbo.ESPERAR:
            verbo = Verbo.ESPERAR
        if verbo != self.verbo:
            return
        efecto = self._ejecutar(verbo, d.carga["objetivo"], d.carga.get("datos", {}))
        aplicar_efecto(ctx, verbo, d, efecto)


def aplicar_efecto(ctx: Contexto, verbo: Verbo, decision: Pieza, efecto: Efecto) -> None:
    soma = ctx.soma
    soma.aplicar(efecto.delta)
    if efecto.exito:
        if verbo == Verbo.DORMIR:
            soma.dormido = True
        elif verbo == Verbo.COGER:
            soma.cargando = efecto.obtenido or decision.carga.get("clase") or decision.carga["objetivo"]
        elif verbo == Verbo.SOLTAR:
            soma.cargando = None
    if efecto.muerte:
        soma.vitalidad = 0.0
    ctx.extra["efecto"] = efecto
    ej = Pieza(
        id="Ejecucion",
        tipo="Ejecucion",
        arousal=decision.arousal,
        confianza=decision.confianza,
        carga={
            "verbo": decision.carga["verbo"],
            "objetivo": decision.carga["objetivo"],
            "clase": decision.carga.get("clase", ""),
            "sistema": decision.carga.get("sistema", ""),
            "motivo": decision.carga.get("motivo", ""),
            "exito": efecto.exito,
            "delta": dict(efecto.delta),
            "causa": efecto.causa,
            "obtenido": efecto.obtenido,
            "mensaje": efecto.mensaje,
        },
        entradas=["decision"],
        sistema="CORE",
        creada=ctx.latido,
        actualizada=ctx.latido,
    )
    ctx.onda.registrar("Ejecucion", ej)
