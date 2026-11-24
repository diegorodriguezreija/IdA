"""Tribunal: arbitra los candidatos de Acción de S1, S2 y S3."""

from typing import Any, Dict, List, Optional, Tuple

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.pieza import Pieza
from ida.nucleo.vocabulario import Verbo


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
