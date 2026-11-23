"""Componentes del Core: Sentir (sensores) y Actuar (Tribunal y actuadores). Exentos de peaje.

Sentir convierte la ``Observacion`` que entrega el mundo en piezas de ``ev``:
- ``Interocepcion``: una pieza por constante vital, con su variación respecto al latido anterior.
  Además de las de ``Soma``, las constantes propias que el mundo entregue en ``vitales``.
- ``Propiocepcion``: dónde está el individuo, qué lleva y su inventario (si el mundo lo tiene).
- ``Exterocepcion``: una pieza por entidad percibida (incluidos los lugares a los que puede ir), en bruto (arousal 0);
  la saliencia la pone la preatención de S1 (D5).
- ``Ambiente``: las condiciones del entorno que el mundo entregue (p. ej. la luz), si las hay.

Actuar: el ``Tribunal`` elige un candidato de ``acc["Accion"]`` y el ``Actuador`` de ese
verbo lo materializa en el mundo. Nada se ejecuta sin pasar por el Tribunal.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple

from ida.core.arquitectura import Componente, Contexto
from ida.core.mundo import Efecto, Motor
from ida.core.pieza import Pieza
from ida.core.soma import VITALES
from ida.core.vocabulario import Verbo


class Interocepcion(Componente):
    tipo = "Interocepcion"

    def reactiva(self, ctx: Contexto) -> None:
        previo = ctx.onda.ei("Interocepcion")
        valores = {nombre: float(getattr(ctx.soma, nombre)) for nombre in VITALES}
        if ctx.observacion is not None and ctx.observacion.vitales:
            valores.update({k: float(v) for k, v in ctx.observacion.vitales.items() if k not in valores})
        for nombre, valor in valores.items():
            antes = float(previo[nombre].carga["valor"]) if nombre in previo else valor
            p = self.pieza(ctx, nombre, arousal=(100.0 - valor) / 100.0, carga={"valor": round(valor, 2), "delta": round(valor - antes, 2)})
            self.percibir(ctx, p)


class Propiocepcion(Componente):
    tipo = "Propiocepcion"

    def reactiva(self, ctx: Contexto) -> None:
        obs = ctx.observacion
        p = self.pieza(ctx, "yo", arousal=0.1, carga={"ubicacion": obs.ubicacion if obs else "", "cargando": ctx.soma.cargando,
                                                     "inventario": dict(obs.inventario or {}) if obs else {},
                                                     "cuerpo": dict(obs.cuerpo or {}) if obs else {}})
        self.percibir(ctx, p)


class Exterocepcion(Componente):
    """Una pieza por entidad, en bruto: arousal 0 (sin valorar). La saliencia la pone la preatención (``Saliencia``, D5)."""

    tipo = "Exterocepcion"

    def reactiva(self, ctx: Contexto) -> None:
        if ctx.observacion is None:
            return
        for e in ctx.observacion.entidades:
            p = self.pieza(ctx, e.id, arousal=0.0, carga={"clase": e.clase, "rasgos": dict(e.rasgos), "datos": dict(e.datos)})
            self.percibir(ctx, p)
            if ctx.memoria.activa:
                ctx.memoria.ver_clase(e.clase)


class Ambiente(Componente):
    """Condiciones del entorno (``Observacion.ambiente``): una sola pieza ``ambiente``, si el mundo las da."""

    tipo = "Ambiente"

    def reactiva(self, ctx: Contexto) -> None:
        if ctx.observacion is not None and ctx.observacion.ambiente:
            self.percibir(ctx, self.pieza(ctx, "ambiente", arousal=0.0, carga=dict(ctx.observacion.ambiente)))


class Tribunal(Componente):
    """Arbitra los candidatos de Acción de S1, S2 y S3.

    Puntuación = arousal·estrés + confianza·(1 − estrés) + experiencia, con el arousal ya modulado:
    el de la acción más lo que S2 o S3 hayan subido o bajado su impulso de origen.
    - Con estrés manda la urgencia; en calma, la confianza.
    - La experiencia (activa y proactiva) sesga con un peso pequeño los candidatos que ya existen;
      no añade candidatos.
    - Continuidad: la acción de la estrategia en curso (la que se ejecutó en el latido anterior y
      sigue activa) suma un plus acotado de 0,1 × (1 − agotamiento) × (1 − progreso) (decisiones 4,
      16 y 23): se apaga de forma gradual al agotarse y al acercarse al objetivo.
    - Si los dos mejores casi empatan, decide el azar.
    - Acecho: un candidato con poca confianza y poca urgencia no se ejecuta enseguida; su
      confianza se acumula latido a latido hasta superar el umbral.
    """

    tipo = "Decision"
    EMPATE = 0.02
    PLUS_ACTIVA = 0.1     # plus a la acción de la estrategia en curso, × (1 − agotamiento) × (1 − progreso)
    UMBRAL_ACECHO = 0.35

    def __init__(self):
        super().__init__("Tribunal")
        self.acumulado: Dict[Tuple[str, str], float] = {}

    def reactiva(self, ctx: Contexto) -> None:
        candidatos: List[Pieza] = list(ctx.onda.acc("Accion").values())
        if not candidatos:
            self._decidir(ctx, Verbo.ESPERAR, "", "", "sin candidatos", None, [])
            return
        estres = ctx.soma.estres
        peso = ctx.perfil.peso_experiencia if ctx.con_experiencia else 0.0
        en_curso = self._estrategia_en_curso(ctx)
        impulsos = {**ctx.onda.ef("Impulso"), **ctx.onda.ef("Intencion")}
        evaluados: List[Dict[str, Any]] = []
        for c in candidatos:
            # Arousal ya modulado (decisión 23): lo que S2 o S3 hayan subido o bajado el impulso de origen.
            imp = impulsos.get(c.carga.get("origen", {}).get("impulso", ""))
            modulacion = float(imp.arousal) - float(imp.carga.get("intensidad", imp.arousal)) if imp is not None else 0.0
            arousal = max(0.0, min(1.0, c.arousal + modulacion))
            base = arousal * estres + c.confianza * (1.0 - estres)
            act, pro = ctx.memoria.sesgo(c.carga["verbo"], c.carga.get("clase", ""), ctx.latido) if peso else (0.0, 0.0)
            plus = 0.0
            if en_curso is not None and c.carga.get("origen", {}).get("estrategia") == en_curso.id:
                plus = self.PLUS_ACTIVA * (1.0 - float(en_curso.carga.get("agotamiento", 0.0))) * (1.0 - float(en_curso.carga.get("progreso", 0.0)))
            sin_plus = base + peso * (act + pro)
            evaluados.append({"pieza": c, "base": base, "activa": act, "proactiva": pro, "plus": plus, "sin_plus": sin_plus, "total": sin_plus + plus})
        evaluados.sort(key=lambda e: -e["total"])
        ganador = evaluados[0]
        if len(evaluados) > 1 and evaluados[0]["total"] - evaluados[1]["total"] <= self.EMPATE:
            ganador = ctx.azar.eleccion(evaluados[:2])
        sin_experiencia = max(evaluados, key=lambda e: e["base"])
        ctx.onda.notas["experiencia_cambio"] = sin_experiencia["pieza"].id != ganador["pieza"].id
        if ganador["plus"] > 0.0:
            ctx.onda.notas["plus_decide"] = max(evaluados, key=lambda e: e["sin_plus"])["pieza"].id != ganador["pieza"].id
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
                "plus": round(e["plus"], 3),
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

    @staticmethod
    def _estrategia_en_curso(ctx: Contexto) -> Optional[Pieza]:
        """La estrategia cuya acción se ejecutó en el latido anterior, si sigue activa (decisión 4)."""
        previa = ctx.onda.ei("Accion").get("Accion")
        if previa is None:
            return None
        return ctx.onda.estrategias.get(previa.carga.get("origen", {}).get("estrategia", ""))

    def _decidir(self, ctx: Contexto, verbo: Verbo, objetivo: str, clase: str, motivo: str, ganador, evaluados) -> None:
        datos = dict(ganador.carga.get("datos", {})) if ganador is not None else {}
        d = self.pieza(
            ctx,
            "decision",
            arousal=ganador.arousal if ganador is not None else 0.0,
            confianza=ganador.confianza if ganador is not None else 1.0,
            carga={"verbo": verbo, "objetivo": objetivo, "clase": clase, "motivo": motivo, "datos": datos,
                   "sistema": ganador.sistema if ganador is not None else "CORE",
                   "origen": dict(ganador.carga.get("origen", {})) if ganador is not None else {}},
            entradas=[ganador.id] if ganador is not None else [],
        )
        self.registrar(ctx, d)
        ctx.extra["decision"] = d


class Actuador(Componente):
    """Materializa en el mundo la decisión del Tribunal para un verbo concreto.

    Si el mundo tiene primitivas y el cuerpo tiene Motor (D9), el Motor traduce la decisión a primitivas al ejecutarla;
    sin primitivas (precondición no cumplida) no se toca el mundo. El éxito lo juzga el Motor con lo medido en bruto.
    Si no, el mundo ejecuta el verbo."""

    tipo = "Accion"

    def __init__(self, verbo: Verbo, ejecutar: Callable[[Verbo, str, Dict[str, Any]], Efecto], motor: Optional[Motor] = None,
                 ejecutar_primitivas: Optional[Callable[[List[str], Optional[Verbo]], Efecto]] = None,
                 disponibles: Optional[List[str]] = None):
        super().__init__(f"Actuador_{verbo.value}")
        self.verbo = verbo
        self._ejecutar = ejecutar
        self._motor = motor
        self._ejecutar_primitivas = ejecutar_primitivas
        self._disponibles = list(disponibles or [])

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
        if self._motor is None or self._ejecutar_primitivas is None:
            efecto = self._ejecutar(verbo, d.carga["objetivo"], d.carga.get("datos", {}))
            aplicar_efecto(ctx, verbo, d, efecto)
            return
        primitivas = self._motor.primitivas(d, ctx, self._disponibles)
        efecto = self._ejecutar_primitivas(primitivas, verbo) if primitivas else Efecto(exito=False)
        efecto.exito = self._motor.juzgar(d, primitivas, efecto)
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
        id="Accion",
        tipo="Accion",
        arousal=decision.arousal,
        confianza=decision.confianza,
        carga={
            "verbo": decision.carga["verbo"],
            "objetivo": decision.carga["objetivo"],
            "clase": decision.carga.get("clase", ""),
            "sistema": decision.carga.get("sistema", ""),
            "motivo": decision.carga.get("motivo", ""),
            "origen": dict(decision.carga.get("origen", {})),
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
    ctx.onda.registrar("Accion", ej)
