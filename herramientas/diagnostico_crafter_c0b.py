"""Diagnóstico de supuestos S1, S2 y S3 en Crafter (Paso C.0b de ENCARGO_CRAFTER_C.md).

Analiza:
- S1: Sed de las semillas 14 y 18 (trayectoria detallada antes de la muerte,
     _presion_interna, _riesgo_exterior, _conviene_salir y abastecer).
- S2: Descarte de roca cercana en semillas 21, 26 y 27 (motivos de descarte de candidatos
     en _buscar_mejor_mina / _evaluar_candidato, victorias de Tribunal, geometría de roca visible).
- S3: Existencia del territorio del hogar en paso 0 (semillas 11 a 30).
"""

import argparse
from collections import Counter
import os
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import crafter  # noqa: E402
from herramientas.benchmark import PERFILES  # noqa: E402
from ida.core.arquitectura import Contexto  # noqa: E402
from ida.ejecutor import ejecutar as vivir  # noqa: E402
from ida.mundos.crafter import (  # noqa: E402
    MOVIMIENTOS,
    NO_TRANSITABLES_ZOMBI,
    ROCA_EXCAVABLE,
    TRANSITABLES_JUGADOR,
    RefugioNocturno,
    _dist,
)

Pos = Tuple[int, int]
PARED_NATURAL = {"water", "stone", "tree", "coal", "iron", "diamond"}
TRANSITABLES_MAPA = {"grass", "sand", "path"}


# ==============================================================================
# S1. Diagnóstico de sed en semillas 14 y 18
# ==============================================================================

def _obtener_refugio(org: Any) -> Optional[RefugioNocturno]:
    s2 = org._sistema("S2")
    elige = next((c for c in s2.componentes() if c.tipo == "Estrategia"), None)
    if elige and hasattr(elige, "catalogo"):
        inst = elige.catalogo.get("refugio_nocturno")
        if isinstance(inst, RefugioNocturno):
            return inst
    return None


class RastreadorS1:
    """Registra la evolución latido a latido para el diagnóstico S1."""

    def __init__(self, semilla: int) -> None:
        self.semilla = semilla
        self.latido_primer_sello: Optional[int] = None
        self.latido_ultimo_sello: Optional[int] = None
        self.latido_salida: Optional[int] = None
        self.muerte_latido: Optional[int] = None
        self.causa_muerte: Optional[str] = None
        self.historial: List[Dict[str, Any]] = []

    def al_latir(self, org: Any, onda: Any, r: Dict[str, Any]) -> None:
        p = org.mundo.jugador
        pos = tuple(p.pos)
        cara = tuple(p.facing)
        luz = float(org.mundo.env._world.daylight)
        inv = dict(p.inventory)
        t_paso = org.mundo.t

        refugio = _obtener_refugio(org)
        estado = refugio._estado_mem if refugio else {}
        fase = estado.get("fase", "desconocida")
        mina = estado.get("mina")
        sellado = refugio._sellado(mina) if refugio and mina else False

        if sellado:
            if self.latido_primer_sello is None:
                self.latido_primer_sello = onda.ciclo
            self.latido_ultimo_sello = onda.ciclo

        if estado.get("saliendo") or (self.latido_primer_sello is not None and not sellado and fase in ("amanecer", "abastecer")):
            if self.latido_salida is None and refugio and not refugio._en_galeria(pos, mina):
                self.latido_salida = onda.ciclo

        prop_refugio = None
        for accion_p in onda.ef("Accion").values():
            orig = accion_p.carga.get("origen", {})
            if orig.get("estrategia") == "refugio_nocturno" or orig.get("impulso") == "cobijo":
                verbo_str = accion_p.carga.get("verbo").value if hasattr(accion_p.carga.get("verbo"), "value") else str(accion_p.carga.get("verbo"))
                prop_refugio = {
                    "verbo": verbo_str,
                    "objetivo": accion_p.carga.get("objetivo"),
                    "arousal": round(accion_p.arousal, 3),
                    "confianza": round(accion_p.confianza, 3),
                    "motivo": accion_p.carga.get("motivo", ""),
                }
                break

        evaluados = onda.notas.get("evaluados", [])
        top3 = []
        for ev in evaluados[:3]:
            top3.append({
                "id": ev.get("id"),
                "verbo": ev.get("verbo"),
                "objetivo": ev.get("objetivo"),
                "total": round(ev.get("total", 0.0), 3),
                "motivo": ev.get("motivo", ""),
            })

        decision = r.get("decision", {})
        ganadora = decision.get("sistema", "")
        accion_ef = onda.ei("Accion").get("Accion")
        estrat_ganadora = accion_ef.carga.get("origen", {}).get("estrategia", ganadora) if accion_ef else ganadora

        ultimo_ef = org.ultimo_efecto
        exito = decision.get("exito")
        cambio_inv = dict(ultimo_ef.delta) if ultimo_ef and ultimo_ef.delta else {}
        cambio_pos = bool(ultimo_ef.cambio_posicion) if ultimo_ef and hasattr(ultimo_ef, "cambio_posicion") else False

        presion = RefugioNocturno._presion_interna(inv, refugio._agua_accesible_dentro(mina) is not None) if refugio else 0.0
        ctx_sim = Contexto(
            onda=onda,
            soma=org.soma,
            memoria=org.memoria,
            arquetipo=org.arquetipo,
            azar=org.azar,
            perfil=org.perfil,
            verbos=org.verbos,
            observacion=None,
            con_experiencia=org.con_experiencia,
            biblioteca=org.biblioteca,
        )
        riesgo = refugio._riesgo_exterior(ctx_sim, luz, pos) if refugio else 0.0
        conviene = refugio._conviene_salir(ctx_sim, inv, luz, mina) if refugio else False
        agua_in = refugio._agua_accesible_dentro(mina) if refugio else None

        aguas_recordadas = [pt for pt, m in refugio.mapa.items() if m == "water"] if refugio else []
        aguas_dist = [(a, _dist(pos, a)) for a in aguas_recordadas]
        aguas_dist.sort(key=lambda x: x[1])

        # Destino de abastecer si está en esa fase
        destino_abastecer = None
        if refugio and fase == "abastecer":
            # simular destino elegido en _abastecer
            deficit_agua = 9.0 - inv.get("drink", 9.0)
            deficit_comida = 9.0 - inv.get("food", 9.0)
            objetivos: List[Tuple[float, Pos, str, str]] = []
            if deficit_agua > 0:
                for a, m in refugio.mapa.items():
                    if m == "water":
                        objetivos.append((_dist(pos, a) - 3.0 * deficit_agua, a, f"agua_{a[0]}_{a[1]}", "agua"))
            if deficit_comida > 0:
                exter = [p_obj for p_obj in ctx_sim.onda.ev("Exterocepcion").values() if "pos" in p_obj.carga.get("datos", {})]
                for p_obj in exter:
                    if p_obj.clase in ("vaca", "planta") and p_obj.rasgo("nutritivo") > 0.05:
                        cp = tuple(p_obj.carga["datos"]["pos"])
                        objetivos.append((_dist(pos, cp) - 3.0 * deficit_comida, cp, p_obj.id, p_obj.clase))
            if objetivos:
                objetivo_min = min(objetivos, key=lambda o: o[0])
                destino_abastecer = {"coste": round(objetivo_min[0], 2), "pos": objetivo_min[1], "clase": objetivo_min[3]}

        self.historial.append({
            "ciclo": onda.ciclo,
            "t": t_paso,
            "luz": round(luz, 3),
            "salud": int(p.health),
            "comida": int(inv.get("food", 0)),
            "agua": int(inv.get("drink", 0)),
            "energia": int(inv.get("energy", 0)),
            "pos": pos,
            "cara": cara,
            "fase": fase,
            "mina": mina,
            "sellado": sellado,
            "propuesta_refugio": prop_refugio,
            "estrategia_ganadora": estrat_ganadora,
            "top3": top3,
            "decision": {
                "verbo": decision.get("verbo"),
                "objetivo": decision.get("objetivo"),
                "motivo": r.get("motivo", ""),
                "exito": exito,
                "delta": cambio_inv,
                "cambio_pos": cambio_pos,
            },
            "presion_interna": round(presion, 3),
            "riesgo_exterior": round(riesgo, 3),
            "conviene_salir": conviene,
            "agua_accesible_dentro": agua_in,
            "aguas_cerca": aguas_dist[:3],
            "destino_abastecer": destino_abastecer,
        })


def diagnosticar_s1(semillas: Optional[List[int]] = None, latidos: int = 600) -> Dict[int, Dict[str, Any]]:
    if semillas is None:
        semillas = [14, 18]
    resultados: Dict[int, Dict[str, Any]] = {}

    for sem in semillas:
        rastreador = RastreadorS1(sem)
        with tempfile.TemporaryDirectory(prefix=f"ida_diag_s1_{sem}_") as td:
            res = vivir("crafter", latidos=latidos, semilla=sem, generaciones=1, tabula_rasa=True,
                        consola=False, datos=td, al_latir=rastreador.al_latir, arquetipo_inicial=PERFILES["Equilibrado"])[0]

        rastreador.muerte_latido = res.get("latidos")
        rastreador.causa_muerte = res.get("causa_muerte")

        # Filtrar tramo relevante:
        # Semilla 14: desde 30 latidos antes del último sello hasta la muerte
        # Semilla 18: desde 30 latidos antes de la salida hasta la muerte
        if sem == 14:
            punto_ref = rastreador.latido_ultimo_sello or 129
            inicio = max(0, punto_ref - 30)
            registros = rastreador.historial[inicio:]
        else:
            punto_ref = rastreador.latido_salida or 281
            inicio = max(0, punto_ref - 30)
            registros = rastreador.historial[inicio:]

        resultados[sem] = {
            "latido_primer_sello": rastreador.latido_primer_sello,
            "latido_ultimo_sello": rastreador.latido_ultimo_sello,
            "latido_salida": rastreador.latido_salida,
            "muerte_latido": rastreador.muerte_latido,
            "causa_muerte": rastreador.causa_muerte,
            "registros": registros,
        }

    return resultados


# ==============================================================================
# S2. Diagnóstico de descarte de roca en semillas 21, 26 y 27
# ==============================================================================

def diagnosticar_candidato_detallado(refugio: RefugioNocturno, e0: Pos, d: Pos, pos_actual: Pos,
                                    hogar_pos: Optional[Pos]) -> Tuple[bool, Optional[float], str, str]:
    """Evalúa un candidato (e0, d) y devuelve (es_valido, score, categoria_descarte, detalle)."""
    m0 = refugio.mapa.get(e0)
    if m0 not in TRANSITABLES_JUGADOR and e0 != pos_actual:
        return False, None, "otro", f"acceso e0 {e0} ({m0}) no transitable"

    dx, dy = d
    e1 = (e0[0] + dx, e0[1] + dy)
    e2 = (e0[0] + 2 * dx, e0[1] + 2 * dy)
    e3 = (e0[0] + 3 * dx, e0[1] + 3 * dy)
    es_recordada = refugio.mina_recordada == (e0, d) or (hogar_pos is not None and hogar_pos == e2)

    for idx, ek in enumerate((e1, e2, e3), start=1):
        mk = refugio.mapa.get(ek)
        if mk is None:
            return False, None, "sin profundidad para 3 casillas", f"e{idx} {ek} no explorado (None)"
        if mk in ROCA_EXCAVABLE:
            pass
        elif mk == "path" and (es_recordada or pos_actual in (e0, e1, e2, e3)):
            pass
        else:
            return False, None, "sin profundidad para 3 casillas", f"e{idx} {ek} es {mk} (no roca)"

        laterales = [(-dy, dx), (dy, -dx)]
        if idx == 3:
            laterales.append((dx, dy))
        for ldx, ldy in laterales:
            vec = (ek[0] + ldx, ek[1] + ldy)
            mv = refugio.mapa.get(vec)
            if mv not in NO_TRANSITABLES_ZOMBI:
                if idx == 3 and (ldx, ldy) == (dx, dy):
                    return False, None, "túnel al fondo", f"fondo e3 {vec} es {mv} (transitable)"
                return False, None, f"lateral transitable (e{idx})", f"lateral {vec} de e{idx} es {mv} ({'None' if mv is None else mv})"
            if idx >= 2 and mv == "water":
                if any(refugio.mapa.get((vec[0] + k * ldx, vec[1] + k * ldy)) == "path" for k in (1, 2)):
                    return False, None, "otro", f"camino tras agua en {vec} de e{idx}"

    for x in range(min(e0[0], e3[0]) - 2, max(e0[0], e3[0]) + 3):
        for y in range(min(e0[1], e3[1]) - 2, max(e0[1], e3[1]) + 3):
            if refugio.mapa.get((x, y)) == "lava":
                return False, None, "lava cerca", f"lava en {(x, y)}"

    dist_jugador = _dist(pos_actual, e0)
    aguas = [p for p, m in refugio.mapa.items() if m == "water"]
    dist_agua = min((_dist(e0, a) for a in aguas), default=12)
    agua_pared_e2 = any(refugio.mapa.get((e2[0] + ldx, e2[1] + ldy)) == "water" for ldx, ldy in ((-dy, dx), (dy, -dx)))
    agua_pared_e3 = any(refugio.mapa.get((e3[0] + ldx, e3[1] + ldy)) == "water" for ldx, ldy in ((-dy, dx), (dy, -dx), (dx, dy)))
    rocas_a_picar = sum(1 for ek in (e1, e2, e3) if refugio.mapa.get(ek) in ROCA_EXCAVABLE)

    bono_agua_pared = 16.0 if agua_pared_e2 else (12.0 if agua_pared_e3 else 0.0)
    puntuacion = 100.0 - 3.0 * dist_jugador - 2.0 * dist_agua + bono_agua_pared
    if es_recordada:
        puntuacion += 25.0
    puntuacion += 2.0 * rocas_a_picar
    return True, puntuacion, "valido", "ok"


class RastreadorS2:
    """Registra las evaluaciones de minas y descartes para el diagnóstico S2."""

    def __init__(self, semilla: int) -> None:
        self.semilla = semilla
        self.descartes_motivo: Counter = Counter()
        self.descartes_detalle: Counter = Counter()
        self.candidatos_evaluados = 0
        self.candidatos_validos = 0
        self.victorias_tribunal: Counter = Counter()
        self.latidos_elegir_mina = 0
        self.elegido_previo: Optional[Tuple[Pos, Pos]] = None
        self.abandonos: List[Dict[str, Any]] = []
        self.geometria_piedra_cercana: List[Dict[str, Any]] = []
        self.vio_piedra_cerca = False

    def al_latir(self, org: Any, onda: Any, r: Dict[str, Any]) -> None:
        p = org.mundo.jugador
        pos = tuple(p.pos)
        inv = dict(p.inventory)
        refugio = _obtener_refugio(org)
        if not refugio:
            return
        estado = refugio._estado_mem
        fase = estado.get("fase")

        if fase == "elegir_mina" and not self.vio_piedra_cerca:
            rocas_visibles = [pt for pt, m in refugio.mapa.items() if m == "stone" and 2 <= _dist(pos, pt) <= 3]
            if rocas_visibles:
                self.vio_piedra_cerca = True
                for r_pos in rocas_visibles:
                    piedras_cruz = 0
                    transitables_alrededor = 0
                    for dx, dy in MOVIMIENTOS:
                        v = (r_pos[0] + dx, r_pos[1] + dy)
                        mat_v = refugio.mapa.get(v)
                        if mat_v in ROCA_EXCAVABLE or mat_v in ("stone", "coal", "iron"):
                            piedras_cruz += 1
                        elif mat_v in TRANSITABLES_JUGADOR:
                            transitables_alrededor += 1
                    self.geometria_piedra_cercana.append({
                        "latido": onda.ciclo,
                        "pos_jugador": pos,
                        "pos_roca": r_pos,
                        "dist": _dist(pos, r_pos),
                        "piedras_en_cruz": piedras_cruz,
                        "transitables_alrededor": transitables_alrededor,
                    })

        if fase == "elegir_mina":
            self.latidos_elegir_mina += 1
            decision = r.get("decision", {})
            estrat = decision.get("sistema", "")
            accion_ef = onda.ei("Accion").get("Accion")
            if accion_ef:
                estrat = accion_ef.carga.get("origen", {}).get("estrategia", estrat)
            self.victorias_tribunal[estrat] += 1

            hogar_pos = None
            tiene_piedra = inv.get("stone", 0) >= 1
            mejor_val: Optional[Tuple[Pos, Pos, float]] = None

            for e0, m0 in list(refugio.mapa.items()):
                if m0 not in TRANSITABLES_JUGADOR and e0 != pos:
                    continue
                for d in MOVIMIENTOS:
                    e1 = (e0[0] + d[0], e0[1] + d[1])
                    e2 = (e0[0] + 2 * d[0], e0[1] + 2 * d[1])
                    e3 = (e0[0] + 3 * d[0], e0[1] + 3 * d[1])
                    rocas = sum(1 for ek in (e1, e2, e3) if refugio.mapa.get(ek) in ROCA_EXCAVABLE)
                    if not tiene_piedra and rocas < 1:
                        self.descartes_motivo["sin roca para obtener piedra"] += 1
                        self.descartes_detalle["sin roca excavable para obtener piedra"] += 1
                        continue

                    self.candidatos_evaluados += 1
                    valido, score, mot, det = diagnosticar_candidato_detallado(refugio, e0, d, pos, hogar_pos)
                    if valido and score is not None:
                        self.candidatos_validos += 1
                        if mejor_val is None or score > mejor_val[2]:
                            if mejor_val is not None:
                                self.descartes_motivo["puntuación menor que otro candidato"] += 1
                                self.descartes_detalle[f"puntuación {mejor_val[2]:.1f} superada por {score:.1f}"] += 1
                            mejor_val = (e0, d, score)
                        else:
                            self.descartes_motivo["puntuación menor que otro candidato"] += 1
                            self.descartes_detalle[f"puntuación {score:.1f} menor que mejor ({mejor_val[2]:.1f})"] += 1
                    else:
                        self.descartes_motivo[mot] += 1
                        self.descartes_detalle[det] += 1

            mina_actual = estado.get("mina")
            if self.elegido_previo is not None and mina_actual != self.elegido_previo:
                self.abandonos.append({
                    "latido": onda.ciclo,
                    "previo": self.elegido_previo,
                    "nuevo": mina_actual,
                    "sin_avance": estado.get("sin_avance"),
                })
            self.elegido_previo = mina_actual


def diagnosticar_s2(semillas: Optional[List[int]] = None, latidos: int = 600) -> Dict[int, Dict[str, Any]]:
    if semillas is None:
        semillas = [21, 26, 27]
    resultados: Dict[int, Dict[str, Any]] = {}

    for sem in semillas:
        rastreador = RastreadorS2(sem)
        with tempfile.TemporaryDirectory(prefix=f"ida_diag_s2_{sem}_") as td:
            res = vivir("crafter", latidos=latidos, semilla=sem, generaciones=1, tabula_rasa=True,
                        consola=False, datos=td, al_latir=rastreador.al_latir, arquetipo_inicial=PERFILES["Equilibrado"])[0]

        resultados[sem] = {
            "muerte_latido": res.get("latidos"),
            "causa_muerte": res.get("causa_muerte"),
            "candidatos_evaluados": rastreador.candidatos_evaluados,
            "candidatos_validos": rastreador.candidatos_validos,
            "descartes_por_motivo": dict(rastreador.descartes_motivo),
            "descartes_detalle_top": rastreador.descartes_detalle.most_common(10),
            "victorias_tribunal": dict(rastreador.victorias_tribunal),
            "latidos_elegir_mina": rastreador.latidos_elegir_mina,
            "abandonos": rastreador.abandonos,
            "geometria_piedra_cercana": rastreador.geometria_piedra_cercana,
        }

    return resultados


# ==============================================================================
# S3. Diagnóstico de territorio del hogar en paso 0 (semillas 11 a 30)
# ==============================================================================

def diagnosticar_s3(semillas: Optional[List[int]] = None) -> Dict[str, Any]:
    if semillas is None:
        semillas = list(range(11, 31))
    resultados_semillas: Dict[int, Dict[str, Any]] = {}

    for sem in semillas:
        env = crafter.Env(seed=sem)
        env.reset()
        start_pos = tuple(env._player.pos)
        w = env._world

        sitios_candidatos: List[Dict[str, Any]] = []

        for x in range(64):
            for y in range(64):
                X = (x, y)
                dist_salida = abs(x - start_pos[0]) + abs(y - start_pos[1])
                if dist_salida > 25:
                    continue
                mat_x = w[X][0]
                if mat_x not in ("grass", "sand"):
                    continue

                vecinos = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
                aguas = [v for v in vecinos if 0 <= v[0] < 64 and 0 <= v[1] < 64 and w[v][0] == "water"]
                if not aguas:
                    continue

                hierbas_man = sum(
                    1 for dx in range(-2, 3) for dy in range(-2, 3)
                    if abs(dx) + abs(dy) <= 2 and 0 <= x + dx < 64 and 0 <= y + dy < 64 and w[(x + dx, y + dy)][0] == "grass"
                )

                min_dist_piedra = min(
                    (abs(sx - x) + abs(sy - y) for sx in range(64) for sy in range(64) if w[(sx, sy)][0] in ("stone", "coal", "iron")),
                    default=999
                )

                hay_cantera = any(
                    (abs(sx - x) >= 12 or abs(sy - y) >= 12) and (abs(sx - x) + abs(sy - y) <= 17)
                    for sx in range(64) for sy in range(64) if w[(sx, sy)][0] in ("stone", "coal", "iron")
                )

                caminos_6 = sum(
                    1 for dx in range(-6, 7) for dy in range(-6, 7)
                    if abs(dx) + abs(dy) <= 6 and 0 <= x + dx < 64 and 0 <= y + dy < 64 and w[(x + dx, y + dy)][0] == "path"
                )

                mejor_e: Optional[int] = None
                orientacion_elegida: Optional[str] = None

                for d_agua in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    ax, ay = x + d_agua[0], y + d_agua[1]
                    if not (0 <= ax < 64 and 0 <= ay < 64 and w[(ax, ay)][0] == "water"):
                        continue
                    d_back = (-d_agua[0], -d_agua[1])
                    d_side1 = (-d_agua[1], d_agua[0])
                    d_side2 = (d_agua[1], -d_agua[0])

                    I = (x + d_back[0], y + d_back[1])
                    if not (0 <= I[0] < 64 and 0 <= I[1] < 64 and w[I][0] in TRANSITABLES_MAPA):
                        continue

                    P1 = (x + d_side1[0], y + d_side1[1])
                    P2 = (x + d_side2[0], y + d_side2[1])
                    P3 = (I[0] + d_side1[0], I[1] + d_side1[1])
                    P4 = (I[0] + d_side2[0], I[1] + d_side2[1])

                    if not all(0 <= p[0] < 64 and 0 <= p[1] < 64 and w[p][0] == "grass" for p in (P1, P2, P3, P4)):
                        continue

                    E = (I[0] + d_back[0], I[1] + d_back[1])
                    H1 = (E[0] + d_side1[0], E[1] + d_side1[1])
                    H2 = (E[0] + d_side2[0], E[1] + d_side2[1])

                    coste_recinto = sum(
                        1 for wall in (H1, E, H2)
                        if 0 <= wall[0] < 64 and 0 <= wall[1] < 64 and w[wall][0] not in PARED_NATURAL
                    )

                    if mejor_e is None or coste_recinto < mejor_e:
                        mejor_e = coste_recinto
                        nombre_dir = {(0, -1): "arriba", (0, 1): "abajo", (-1, 0): "izquierda", (1, 0): "derecha"}.get(d_agua, str(d_agua))
                        orientacion_elegida = f"agua {nombre_dir}"

                sitio = {
                    "pos": X,
                    "mat": mat_x,
                    "a": hierbas_man,
                    "b": min_dist_piedra,
                    "c": hay_cantera,
                    "d": caminos_6,
                    "e": mejor_e,
                    "orientacion": orientacion_elegida,
                    "f": dist_salida,
                }
                sitios_candidatos.append(sitio)

        cumplen = [s for s in sitios_candidatos if s["a"] >= 6 and s["b"] <= 17 and s["c"] and s["e"] is not None]

        if cumplen:
            cumplen.sort(key=lambda s: (s["e"] if s["e"] is not None else 99, 0 if s["b"] <= 8 else 1, s["f"], s["d"]))
            mejor = cumplen[0]
            resultados_semillas[sem] = {
                "valido": True,
                "sitio": mejor,
                "total_candidatos": len(sitios_candidatos),
                "total_cumplen": len(cumplen),
            }
        else:
            def distancia_a_cumplir(s: Dict[str, Any]) -> Tuple[int, int, int]:
                fallo_a = max(0, 6 - s["a"])
                fallo_b = max(0, s["b"] - 17)
                fallo_c = 1 if not s["c"] else 0
                fallo_e = 1 if s["e"] is None else 0
                return (fallo_a + fallo_b + fallo_c * 5 + fallo_e * 5, s["f"], s["b"])

            sitios_candidatos.sort(key=distancia_a_cumplir)
            cercano = sitios_candidatos[0] if sitios_candidatos else None
            motivo_fallo = []
            if cercano:
                if cercano["a"] < 6:
                    motivo_fallo.append(f"a={cercano['a']} < 6")
                if cercano["b"] > 17:
                    motivo_fallo.append(f"b={cercano['b']} > 17")
                if not cercano["c"]:
                    motivo_fallo.append("c=False (sin cantera a >=12 en eje y <=17 total)")
                if cercano["e"] is None:
                    motivo_fallo.append("e=None (sin orientación con 4 plantas en hierba y X,I transitables)")

            resultados_semillas[sem] = {
                "valido": False,
                "sitio": cercano,
                "motivo_fallo": ", ".join(motivo_fallo),
                "total_candidatos": len(sitios_candidatos),
                "total_cumplen": 0,
            }

    return {
        "semillas": resultados_semillas,
        "validas_total": sum(1 for r in resultados_semillas.values() if r["valido"]),
    }


# ==============================================================================
# CLI Principal
# ==============================================================================

def imprimir_detalle_s1(res_s1: Dict[int, Dict[str, Any]]) -> None:
    for sem, data in res_s1.items():
        print("\n=======================================================")
        print(f"DETALLE S1 - SEMILLA {sem} (muerte L={data['muerte_latido']}, causa={data['causa_muerte']})")
        print(f"Primer sello={data['latido_primer_sello']}, Último sello={data['latido_ultimo_sello']}, Salida={data['latido_salida']}")
        print("=======================================================")
        for r in data["registros"]:
            prop = r["propuesta_refugio"]
            prop_str = f"{prop['verbo']} {prop['objetivo']} (ar={prop['arousal']}, conf={prop['confianza']})" if prop else "None"
            top3_str = "; ".join(f"{t['id']}:{t['total']}" for t in r["top3"])
            dec = r["decision"]
            dec_str = f"{dec['verbo']} {dec['objetivo']} (ex={dec['exito']})"
            delta_str = str(dec["delta"]) if dec["delta"] else "{}"
            extra_s1 = ""
            if sem == 14:
                extra_s1 = f" pres={r['presion_interna']} ries={r['riesgo_exterior']} conv={r['conviene_salir']} agua_in={r['agua_accesible_dentro']}"
            else:
                dest = r["destino_abastecer"]
                dest_str = f"{dest['clase']}@{dest['pos']}(c={dest['coste']})" if dest else "None"
                aguas = [f"{a[0]}(d={a[1]})" for a in r["aguas_cerca"][:2]]
                extra_s1 = f" dest_abast={dest_str} aguas_cerca={aguas}"
            linea_diag = (
                f"L{r['ciclo']} t{r['t']} luz={r['luz']} sal={r['salud']} com={r['comida']} agu={r['agua']} ene={r['energia']} "
                f"pos={r['pos']} cara={r['cara']} fase={r['fase']} sell={r['sellado']}{extra_s1} | "
                f"prop=[{prop_str}] | gan={r['estrategia_ganadora']} | top3=[{top3_str}] | dec=[{dec_str} delta={delta_str} mov={dec['cambio_pos']}]"
            )
            print(linea_diag)


def imprimir_detalle_s1_fases(res_s1: Dict[int, Dict[str, Any]]) -> None:
    data_18 = res_s1.get(18)
    if not data_18:
        return
    print("\n--- TRANSICIONES DE FASE EN SEMILLA 18 TRAS LA SALIDA ---")
    fase_ant = None
    for r in data_18["registros"]:
        fase = r["fase"]
        if fase != fase_ant or r["ciclo"] in (280, 281, 282, 283, 284, 285, 290, 300, 320, 340, 360, 370):
            prop = r["propuesta_refugio"]
            prop_str = f"{prop['verbo']} {prop['objetivo']}" if prop else "None"
            mot = prop['motivo'] if prop else ""
            linea_f = (
                f"L{r['ciclo']} t{r['t']} luz={r['luz']} sal={r['salud']} agu={r['agua']} pos={r['pos']} "
                f"fase={fase} prop=[{prop_str} ({mot})] gan={r['estrategia_ganadora']}"
            )
            print(linea_f)
            fase_ant = fase


def imprimir_inspeccionar18(res_s1: Dict[int, Dict[str, Any]]) -> None:
    data_18 = res_s1.get(18)
    if not data_18:
        return
    print("\n--- DETALLE L290-L315 SEMILLA 18 ---")
    for r in data_18["registros"]:
        if 285 <= r["ciclo"] <= 315:
            prop = r["propuesta_refugio"]
            prop_str = f"{prop['verbo']} {prop['objetivo']} (motivo={prop['motivo']})" if prop else "None"
            print(f"L{r['ciclo']} pos={r['pos']} cara={r['cara']} fase={r['fase']} prop=[{prop_str}] gan={r['estrategia_ganadora']} aguas={r['aguas_cerca']}")


def imprimir_tabla_s3(res_s3: Dict[str, Any]) -> None:
    print("\n### Tabla S3: Territorio del hogar en paso 0 (semillas 11 a 30)")
    print("| Semilla | Válido | Sitio (x, y) | a (hierba ≤2) | b (dist roca) | c (cantera) | d (camino ≤6) | e (paredes) | Orientación | f (dist salida) |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    e_vals = []
    f_vals = []
    for sem in range(11, 31):
        info = res_s3["semillas"][sem]
        valido = "Sí" if info["valido"] else f"No ({info.get('motivo_fallo', '')})"
        s = info["sitio"]
        if s:
            pos_str = f"({s['pos'][0]}, {s['pos'][1]})"
            orient = s.get("orientacion") or "—"
            e_str = str(s["e"]) if s["e"] is not None else "—"
            print(f"| {sem} | {valido} | {pos_str} | {s['a']} | {s['b']} | {'Sí' if s['c'] else 'No'} | {s['d']} | {e_str} | {orient} | {s['f']} |")
            if info["valido"] and s["e"] is not None:
                e_vals.append(s["e"])
                f_vals.append(s["f"])
        else:
            print(f"| {sem} | No (sin sitios) | — | — | — | — | — | — | — | — |")

    import statistics
    print("\nResumen S3:")
    print(f"- Semillas con sitio válido: {len(e_vals)} / 20 ({len(e_vals)/20*100:.1f} %)")
    if e_vals:
        med_e = statistics.median(e_vals)
        rango_e = f"{min(e_vals)}–{max(e_vals)}"
        med_f = statistics.median(f_vals)
        rango_f = f"{min(f_vals)}–{max(f_vals)}"
        print(f"- e (piedras necesarias): mediana={med_e}, rango={rango_e}")
        print(f"- f (distancia a salida): mediana={med_f}, rango={rango_f}")


def imprimir_tabla_s2(res_s2: Dict[int, Dict[str, Any]]) -> None:
    print("\n### Tabla S2: Descarte de candidatos en elegir_mina (semillas 21, 26 y 27)")
    print("| Semilla | Muerte (latido / causa) | Latidos elegir_mina | Candidatos evaluados | Candidatos válidos | Refugio gana | Otras ganan |")
    print("|---|---|---|---|---|---|---|")
    for sem in (21, 26, 27):
        data = res_s2[sem]
        vic_ref = data["victorias_tribunal"].get("S2:refugio_nocturno:cobijo", 0)
        vic_otras = sum(v for k, v in data["victorias_tribunal"].items() if k != "S2:refugio_nocturno:cobijo")
        print(f"| {sem} | L={data['muerte_latido']} ({data['causa_muerte']}) | {data['latidos_elegir_mina']} | "
              f"{data['candidatos_evaluados']} | {data['candidatos_validos']} | {vic_ref} | {vic_otras} |")

    print("\n#### Desglose de motivos de descarte por semilla")
    print("| Motivo de descarte | Semilla 21 | Semilla 26 | Semilla 27 | Total |")
    print("|---|---|---|---|---|")
    todos_motivos = sorted(set(
        list(res_s2[21]["descartes_por_motivo"].keys()) +
        list(res_s2[26]["descartes_por_motivo"].keys()) +
        list(res_s2[27]["descartes_por_motivo"].keys())
    ))
    for m in todos_motivos:
        c21 = res_s2[21]["descartes_por_motivo"].get(m, 0)
        c26 = res_s2[26]["descartes_por_motivo"].get(m, 0)
        c27 = res_s2[27]["descartes_por_motivo"].get(m, 0)
        print(f"| {m} | {c21} | {c26} | {c27} | {c21 + c26 + c27} |")

    print("\n#### Piedra visible a 2–3 casillas al inicio de elegir_mina")
    print("| Semilla | Latido | Pos jugador | Pos roca | Dist | Piedras cruz | Transitables | Estimación recinto |")
    print("|---|---|---|---|---|---|---|---|")
    for sem in (21, 26, 27):
        geoms = res_s2[sem]["geometria_piedra_cercana"]
        if not geoms:
            print(f"| {sem} | — | — | — | — | — | — | Sin roca visible a 2–3 casillas |")
        else:
            for g in geoms[:2]:
                est_recinto = max(0, 4 - g["piedras_en_cruz"])
                print(f"| {sem} | {g['latido']} | {g['pos_jugador']} | {g['pos_roca']} | {g['dist']} | "
                      f"{g['piedras_en_cruz']} | {g['transitables_alrededor']} | ~{est_recinto} piedras a colocar |")

    print("\n#### Candidatos válidos elegidos y abandonados")
    for sem in (21, 26, 27):
        ab = res_s2[sem]["abandonos"]
        print(f"- Semilla {sem}: {len(ab)} abandonos registrados. Detalle: {ab[:3]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnóstico C.0b de supuestos S1, S2 y S3")
    parser.add_argument("--parte", choices=["s1", "s2", "s3", "todas"], default="todas",
                        help="Parte del diagnóstico a ejecutar")
    parser.add_argument("--detalle", action="store_true", help="Imprimir detalle latido a latido de S1")
    parser.add_argument("--fases18", action="store_true", help="Imprimir transiciones de fase de semilla 18")
    parser.add_argument("--inspeccionar18", action="store_true", help="Imprimir L285-L315 semilla 18")
    args = parser.parse_args()

    t0 = time.time()
    if args.parte in ("s1", "todas"):
        print("=== EJECUTANDO PARTE S1 (Semillas 14 y 18) ===")
        res_s1 = diagnosticar_s1()
        for sem, data in res_s1.items():
            print(f"\n--- SEMILLA {sem} (muerte en latido {data['muerte_latido']}, causa {data['causa_muerte']}) ---")
            print(f"Primer sello: {data['latido_primer_sello']}, Último sello: {data['latido_ultimo_sello']}, Salida: {data['latido_salida']}")
            print(f"Registros capturados: {len(data['registros'])}")
        if args.detalle:
            imprimir_detalle_s1(res_s1)
        if args.fases18:
            imprimir_detalle_s1_fases(res_s1)
        if args.inspeccionar18:
            imprimir_inspeccionar18(res_s1)

    if args.parte in ("s2", "todas"):
        print("\n=== EJECUTANDO PARTE S2 (Semillas 21, 26 y 27) ===")
        res_s2 = diagnosticar_s2()
        imprimir_tabla_s2(res_s2)

    if args.parte in ("s3", "todas"):
        print("\n=== EJECUTANDO PARTE S3 (Semillas 11 a 30) ===")
        res_s3 = diagnosticar_s3()
        imprimir_tabla_s3(res_s3)

    duracion = time.time() - t0
    print(f"\nTiempo total de ejecución: {duracion:.2f} s")


if __name__ == "__main__":
    main()
