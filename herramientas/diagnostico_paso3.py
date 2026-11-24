"""Diagnóstico del paso 3 en Crafter: la primera noche de cada episodio, lo que pasa después y la cadena de herramientas.

Ejecuta ``evaluar_crafter.evaluar`` (vista oficial, sin herencia) con un gancho en cada latido. No cambia la conducta.
Con ``--salida`` guarda un JSON por semilla; con ``--resumir`` junta varios JSON en las tablas de ``docs/DIAGNOSTICO_PASO3.md``.

**a) Primera noche** de cada episodio: una sola causa. La ventana va del ocaso (primera luz < 0,5) al final de lo
oscuro (luz < 0,3). «Dentro» es estar en un recinto **real** del mundo (``diagnostico_proteger.recinto_real``), no en lo
que cree IdA.
- ``muere antes de anochecer``: el episodio acaba antes de la primera luz < 0,3;
- ``no encuentra sitio``: nunca entra, y en el primer latido oscuro ``Recinto`` no tiene sitio ni requisitos;
- ``no lo completa a tiempo``: nunca entra, y en el primer latido oscuro ``Recinto`` tiene sitio. El motivo: falta
  herramienta (pide un objeto que no se consume al cerrar), falta material (pide lo que consume el cierre), falta
  tiempo (tenía un sitio completable con lo que llevaba) o cree estar dentro (``Recinto`` dice dentro y no lo es);
- ``entra un peligro, se rompe o muere dentro``: estaba dentro y deja de estarlo sin moverse ni abrir, o muere dentro;
- ``sale antes del amanecer``: estaba dentro y sale con su propia acción (moverse o abrir); el motivo es esa acción;
- ``pasa la noche dentro``: dentro en el último latido oscuro.

**b)** Episodios que pasan la noche dentro: causa de muerte, latidos vividos desde el final de lo oscuro, y comida y
bebida (0-9) en el primer latido fuera del recinto.

**c) Cadena de herramientas:** en los episodios que colocan la mesa, fracción que fabrica después el pico y la espada
de madera y latidos desde la mesa. Cuando no se fabrica: estrategias y motivos que ganan desde la mesa hasta el final,
la mejor propuesta de ``PerseguirMetas`` en cada latido (sus metas y las peticiones que atiende) (gane o no), en qué se gasta la madera (acciones USAR con
éxito) y cuántos latidos tenía madera y una mesa en el cuadrado 3 × 3.

    python herramientas/diagnostico_paso3.py --pasos 10000 --semilla 31 --salida d31.json
    python herramientas/diagnostico_paso3.py --resumir d31.json d32.json d33.json

Es un diagnóstico, no una medición. Hay que lanzar las semillas **una tras otra**: el Core corta un latido que pasa de
``Perfil.frecuencia_ms`` en tiempo de reloj (guillotina), y con varios procesos a la vez se cortan latidos que solos no
se cortarían, y la vida cambia. El resumen cuenta los latidos cortados.
"""

import argparse
import json
import os
import statistics
import sys
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))

from diagnostico_proteger import recinto_real  # noqa: E402

OCASO, OSCURO = 0.5, 0.3
CONSUMEN_MADERA = ("place_table", "make_wood_pickaxe", "make_wood_sword", "make_stone_pickaxe", "make_stone_sword",
                   "make_iron_pickaxe", "make_iron_sword")
CAUSAS = ("muere antes de anochecer", "no encuentra sitio", "no lo completa a tiempo",
          "entra un peligro, se rompe o muere dentro", "sale antes del amanecer", "pasa la noche dentro")


def _motivo(texto: str) -> str:
    """La primera parte de un motivo (antes de «·» y de «←»), sin las cifras de coste."""
    return texto.split("·")[0].split("←")[0].strip()[:60]


def _estrategia(carga: Dict[str, Any]) -> str:
    e = str(carga.get("origen", {}).get("estrategia", ""))
    return e.split(":")[1] if e.count(":") >= 1 else (e or str(carga.get("sistema", "")) or "ninguna")


def _de_metas(evaluado: Dict[str, Any]) -> bool:
    """Propuesta de ``PerseguirMetas`` (S3): sus metas («metas: …») y las peticiones que atiende («<origen>: pide …»)."""
    motivo = str(evaluado.get("motivo", ""))
    return evaluado.get("sistema") == "S3" and (motivo.startswith("metas:") or ": pide " in motivo)


VITALES = ("health", "food", "drink", "energy")


def cavable(mem: Any, aqui: Tuple[int, int], inv: Dict[str, float]) -> Dict[str, Any]:
    """La casilla conocida más cercana (Manhattan) de una clase que cavar abre (``Modelo.abre``: observado o inducido), y si
    entra en la búsqueda de sitio: ``nunca vista`` (ninguna en el mapa local), ``lejos`` (fuera de lo que ``candidatos``
    considera: alcanzable en ≤ ``ALCANCE_SITIO`` pasos más 2 casillas cavables) o ``dentro`` con el motivo de descarte."""
    from ida.cuerpos.cuadricula.geometria import _vecinas
    from ida.mundos.crafter.s1.interpretar.recinto import ALCANCE_SITIO, Modelo, candidatos, rutas
    modelo = Modelo(mem, inv, set())
    clases = sorted(c for c in set(modelo.casillas.values()) if modelo.abre(c))
    celdas = [p for p, c in modelo.casillas.items() if c in clases]
    if not celdas:
        return {"caso": "nunca vista", "clases": clases, "distancia": None, "motivo": ""}
    cerca = min(celdas, key=lambda p: (abs(p[0] - aqui[0]) + abs(p[1] - aqui[1]), p))
    d = abs(cerca[0] - aqui[0]) + abs(cerca[1] - aqui[1])
    dist, _ = rutas(modelo, aqui)
    alcance = set(dist)
    for _ in range(2):
        alcance |= {v for p in list(alcance) for v in _vecinas(p) if modelo.casillas.get(v) in clases}
    dentro = [p for p in celdas if p in alcance]
    if not dentro:
        return {"caso": "lejos", "clases": clases, "distancia": d, "motivo": f"más allá de {ALCANCE_SITIO} pasos"}
    falta = {k: v for c in sorted({modelo.casillas[p] for p in dentro}) for k, v in (modelo.falta_para_cavar(c) or {}).items()}
    formas = _formas(modelo, dist)
    if falta:
        motivo = "falta para cavar: " + ", ".join(sorted(falta))
    elif not candidatos(modelo, aqui, dist, None):
        motivo = "sin forma válida: " + max(("vecina sin ver", "acceso que no se sabe cerrar", "peligro al lado", "falta material"),
                                            key=lambda k: formas.get(k, 0))
    else:
        motivo = "hay candidatos y ninguno completable"
    cerradores = {c.objetivo: c.unidades for c in modelo.cerradores}
    return {"caso": "dentro del alcance", "clases": clases, "distancia": d, "motivo": motivo, "formas": formas, "cerradores": cerradores}


def _formas(modelo: Any, dist: Dict[Tuple[int, int], int]) -> Dict[str, int]:
    """Por qué se descartan las formas de 1-3 casillas al alcance (el mismo filtro que ``candidatos``), la primera razón de cada una."""
    from ida.cuerpos.cuadricula.geometria import _manhattan, _suma, _vecinas
    from ida.mundos.crafter.s1.interpretar.recinto import accesos_de
    celdas = set(dist)
    for _ in range(2):
        celdas |= {v for p in list(celdas) for v in _vecinas(p) if modelo.rinde(v) is not None}
    razones: Counter = Counter()
    for a in sorted(celdas):
        for forma in ((a,), (a, _suma(a, (1, 0))), (a, _suma(a, (0, 1)))):
            if not all(p in celdas for p in forma):
                continue
            excavar = [p for p in forma if p not in dist]
            if any(modelo.rinde(p) is None for p in excavar):
                razones["no se puede cavar"] += 1
                continue
            if any(_manhattan(p, q) <= 1 for p in forma for q in modelo.peligros):
                razones["peligro al lado"] += 1
                continue
            accesos = accesos_de(modelo, forma)
            if accesos is None:
                razones["vecina sin ver"] += 1
            elif any(not modelo.cerrable(v) for v in accesos):
                razones["acceso que no se sabe cerrar"] += 1
            elif len(accesos) > modelo.unidades(frozenset(excavar)):
                razones["falta material"] += 1
            else:
                razones["válida"] += 1
    return dict(razones)


def _mesa_cerca(world: Any, pos: Tuple[int, int]) -> bool:
    mats, _ = world.nearby(pos, 1)
    return "table" in mats


class Episodio:
    def __init__(self, indice: int) -> None:
        self.indice = indice
        self.n = 0
        self.fase = "dia"                 # dia → ocaso → oscuro → despues
        self.t_ocaso: Optional[int] = None
        self.t_oscuro: Optional[int] = None
        self.t_fin_noche: Optional[int] = None
        self.estado_oscuro: Optional[Dict[str, Any]] = None
        self.entro = False
        self.dentro = False
        self.salidas: List[Dict[str, Any]] = []
        self.latidos_oscuro_fuera_antes_de_entrar = 0
        self.dentro_al_final_oscuro = False
        self.salida_tras_noche: Optional[Dict[str, Any]] = None
        self.pos: Optional[Tuple[int, int]] = None
        self.logros: Dict[str, int] = {}
        self.gana: Dict[str, Counter] = {"sin_pico": Counter(), "sin_espada": Counter()}
        self.metas: Dict[str, Counter] = {"sin_pico": Counter(), "sin_espada": Counter()}
        self.usar: Counter = Counter()
        self.oportunidad: Counter = Counter()
        self.latidos_tras_mesa = 0
        self.inv_previo: Dict[str, int] = {}
        self.colocadas: Counter = Counter()      # USAR que cambian el inventario, en todo el episodio, por objetivo
        self.usar_sin_efecto: Counter = Counter()
        self.cavable: Optional[Dict[str, Any]] = None
        self.retencion: Counter = Counter()
        self.aperturas: List[Dict[str, Any]] = []       # cada vez que se pasa de dentro a fuera: quién lo hace
        self.retencion_proteger: Counter = Counter()
        self.retencion_impulsos: List[Dict[str, float]] = []
        self.causa: Optional[str] = None
        self.vivo = False
        self.guillotinas = 0

    def latido(self, org: Any, onda: Any) -> None:
        self.n += 1
        n = self.n
        w, jug = org.mundo.env._world, org.mundo.jugador
        luz = float(w.daylight)
        pos = (int(jug.pos[0]), int(jug.pos[1]))
        dentro = recinto_real(w, pos)
        accion = onda.reactiva.ef.get("Accion", {}).get("Accion")
        carga = dict(accion.carga) if accion is not None else {}
        inv = {k: int(v) for k, v in jug.inventory.items()}
        for logro in org.mundo.logros():
            self.logros.setdefault(logro, n)
        # Un USAR de Crafter es «éxito» si la receta existe aunque no haga nada: solo cuenta si cambia el inventario.
        usar = getattr(carga.get("verbo"), "value", "") == "USAR"
        efectivo = usar and any(inv.get(k, 0) != self.inv_previo.get(k, 0) for k in inv if k not in VITALES)
        if usar:
            (self.colocadas if efectivo else self.usar_sin_efecto)[str(carga.get("objetivo"))] += 1
        self.inv_previo = inv

        # a) y b): primera noche
        if self.fase == "dia" and luz < OCASO:
            self.fase, self.t_ocaso = "ocaso", n
        if self.fase in ("ocaso", "dia") and luz < OSCURO:
            self.fase, self.t_oscuro = "oscuro", n
            r = onda.reactiva.ef.get("Recinto", {}).get("recinto")
            self.estado_oscuro = None if r is None else {
                "dentro": bool(r.carga.get("dentro")), "coste": r.carga.get("coste"), "accion": r.carga.get("accion") is not None,
                "requiere": dict(r.carga.get("requiere") or {}), "explicacion": str(r.carga.get("explicacion", ""))[:120]}
            self.cavable = cavable(org.memoria, pos, {k: float(v) for k, v in inv.items()})
        if self.fase in ("ocaso", "oscuro"):
            if self.dentro and not dentro:
                propia = pos != self.pos or carga.get("verbo") is not None and carga["verbo"].value in ("COGER", "MOVER")
                self.salidas.append({"latido": n, "luz": round(luz, 2), "propia": bool(propia), "verbo": str(getattr(carga.get("verbo"), "value", "")),
                                     "estrategia": _estrategia(carga), "motivo": _motivo(str(carga.get("motivo", "")))})
            if dentro:
                self.entro = True
            elif self.fase == "oscuro" and not self.entro:
                self.latidos_oscuro_fuera_antes_de_entrar += 1
            if self.fase == "oscuro":
                self.dentro_al_final_oscuro = dentro
        if self.fase == "oscuro" and luz >= OSCURO:
            self.fase, self.t_fin_noche = "despues", n
        if self.fase == "despues" and self.salida_tras_noche is None and dentro and self.dentro_al_final_oscuro:
            self.retencion[f"{_estrategia(carga)} · {_motivo(str(carga.get('motivo', '')))}"] += 1
            imp = {k: float(p.arousal) for k, p in onda.reactiva.ef.get("Impulso", {}).items()}
            alarma = onda.ef("Supervivencia").get("alarma")
            r = onda.reactiva.ef.get("Recinto", {}).get("recinto")
            prot = next((e for e in onda.notas.get("evaluados") or [] if str(e.get("motivo", "")).startswith("proteger:")), None)
            hostiles = [abs(o.pos[0] - pos[0]) + abs(o.pos[1] - pos[1]) for o in w.objects
                        if type(o).__name__ in ("Zombie", "Skeleton") and abs(o.pos[0] - pos[0]) + abs(o.pos[1] - pos[1]) <= 9]
            self.retencion_impulsos.append({**{k: round(v, 3) for k, v in imp.items()},
                                            "peligro_alarma": round(float(alarma.carga["peligro"]), 3) if alarma is not None else 0.0,
                                            "hostil_d": float(min(hostiles)) if hostiles else 99.0,
                                            "puede_abrir": float(bool(r is not None and r.carga.get("abrir"))),
                                            "luz": round(luz, 3), "gana": _estrategia(carga),
                                            "proteger_total": round(float(prot["total"]), 3) if prot else 0.0,
                                            "primero_total": round(float((onda.notas.get("evaluados") or [{}])[0].get("total", 0.0)), 3)})
            self.retencion_proteger[_motivo(str(prot["motivo"])) if prot else "Proteger no propone"] += 1
        if self.fase == "despues" and self.salida_tras_noche is None and not dentro and self.dentro_al_final_oscuro:
            self.salida_tras_noche = {"latido": n, "comida": inv.get("food", 0), "bebida": inv.get("drink", 0),
                                      "energia": inv.get("energy", 0), "tras_fin_noche": n - (self.t_fin_noche or n)}
        if self.dentro and not dentro:
            fase = {"dia": "antes del ocaso", "ocaso": "ocaso", "oscuro": "noche", "despues": "tras la noche"}[self.fase]
            self.aperturas.append({"latido": n, "fase": fase, "estrategia": _estrategia(carga), "verbo": str(getattr(carga.get("verbo"), "value", "")),
                                   "motivo": _motivo(str(carga.get("motivo", ""))), "se_mueve": pos != self.pos,
                                   "primera_noche": self.dentro_al_final_oscuro and self.fase == "despues"})
        self.dentro, self.pos = dentro, pos

        # c) cadena de herramientas
        if "place_table" in self.logros:
            self.latidos_tras_mesa += 1
            if efectivo:
                self.usar[f"{carga.get('objetivo')} · {_motivo(str(carga.get('motivo', '')))}"] += 1
            mesa = _mesa_cerca(w, pos)
            self.oportunidad["madera"] += int(inv.get("wood", 0) >= 1)
            self.oportunidad["madera_y_mesa"] += int(inv.get("wood", 0) >= 1 and mesa)
            mejor_metas = next((e for e in onda.notas.get("evaluados") or [] if _de_metas(e)), None)
            for herramienta, clave in (("make_wood_pickaxe", "sin_pico"), ("make_wood_sword", "sin_espada")):
                if herramienta in self.logros:
                    continue
                self.gana[clave][f"{_estrategia(carga)} · {_motivo(str(carga.get('motivo', '')))}"] += 1
                if mejor_metas is not None:
                    self.metas[clave][_motivo(str(mejor_metas.get("motivo", "")))] += 1

    def causa_noche(self) -> Tuple[str, str]:
        if self.t_oscuro is None:
            return ("muere antes de anochecer" if not self.vivo else "cortado por presupuesto"), str(self.causa)
        if self.dentro_al_final_oscuro and self.t_fin_noche is not None:
            return "pasa la noche dentro", ""
        if self.dentro_al_final_oscuro:            # murió de noche, dentro
            return "entra un peligro, se rompe o muere dentro", f"muere dentro: {self.causa}"
        if self.entro and self.salidas:
            s = self.salidas[-1]
            if s["propia"]:
                return "sale antes del amanecer", f"{s['estrategia']} · {s['motivo']}"
            return "entra un peligro, se rompe o muere dentro", "se rompe o entra un peligro sin moverse"
        e = self.estado_oscuro
        if e is None:
            return "no encuentra sitio", "sin pieza recinto"
        if e["dentro"]:
            return "no lo completa a tiempo", "cree estar dentro"
        if e["accion"]:
            return "no lo completa a tiempo", "falta tiempo"
        if e["requiere"]:
            herramienta = any(not k.endswith(("wood", "stone", "coal", "iron", "diamond", "sapling")) for k in e["requiere"])
            return "no lo completa a tiempo", "falta herramienta" if herramienta else "falta material"
        return "no encuentra sitio", ""

    def resumen(self) -> Dict[str, Any]:
        causa, motivo = self.causa_noche()
        return {"indice": self.indice, "latidos": self.n, "causa_muerte": self.causa, "vivo": self.vivo, "noche": causa,
                "motivo_noche": motivo, "t_ocaso": self.t_ocaso, "t_oscuro": self.t_oscuro, "t_fin_noche": self.t_fin_noche,
                "salidas": self.salidas, "estado_oscuro": self.estado_oscuro,
                "oscuro_fuera_antes_de_entrar": self.latidos_oscuro_fuera_antes_de_entrar if self.entro else None,
                "salida_tras_noche": self.salida_tras_noche, "logros": self.logros, "gana": {k: dict(v) for k, v in self.gana.items()},
                "metas": {k: dict(v) for k, v in self.metas.items()}, "usar": dict(self.usar), "oportunidad": dict(self.oportunidad),
                "latidos_tras_mesa": self.latidos_tras_mesa, "colocadas": dict(self.colocadas),
                "usar_sin_efecto": dict(self.usar_sin_efecto), "cavable": self.cavable, "retencion": dict(self.retencion),
                "retencion_proteger": dict(self.retencion_proteger),
                "retencion_impulsos": self.retencion_impulsos, "guillotinas": self.guillotinas,
                "aperturas": self.aperturas}


def ejecutar(args: argparse.Namespace) -> int:
    import evaluar_crafter as ev
    from ida.core import latido

    eps: List[Episodio] = []
    vivir_original = latido.Organismo.vivir

    def vivir(self: Any, max_latidos: int, al_latir_externo: Any = None) -> int:
        eps.append(Episodio(len(eps)))
        r = vivir_original(self, max_latidos, al_latir=eps[-1].latido)
        eps[-1].vivo = bool(self.soma.esta_vivo)
        eps[-1].causa = self.causa_muerte if not self.soma.esta_vivo else None
        eps[-1].guillotinas = int(self.contadores.get("guillotinas", 0))
        return r

    latido.Organismo.vivir = vivir   # type: ignore[method-assign,assignment]
    res = ev.evaluar(args.pasos, args.semilla, vista="oficial", sin_herencia=True, quiet=True, manual=args.manual,
                     sin_estrategias_propias=args.sin_estrategias_propias,
                     **({"plazo_logico": args.plazo_logico} if args.plazo_logico else {}))
    datos = {"semilla": args.semilla, "pasos": args.pasos, "score": res["score"], "episodios": [e.resumen() for e in eps]}
    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)
    print(f"semilla {args.semilla}: {len(eps)} episodios, score {res['score']} → {args.salida}")
    return 0


def _pct(a: int, b: int) -> str:
    return f"{a} ({100 * a / b:.1f} %)".replace(".", ",") if b else "0"


def _med(xs: List[float]) -> str:
    return f"{statistics.median(xs):.0f}" if xs else "—"


def resumir(rutas: List[str]) -> int:
    corridas = [json.load(open(r, encoding="utf-8")) for r in rutas]
    eps = [e for c in corridas for e in c["episodios"]]
    sem = [c["semilla"] for c in corridas]
    print(f"Semillas {', '.join(map(str, sem))} · {', '.join(str(c['pasos']) for c in corridas)} pasos · "
          f"{len(eps)} episodios · score {', '.join(str(c['score']) for c in corridas)} · "
          f"latidos cortados por la guillotina: {sum(e.get('guillotinas', 0) for e in eps)}\n")

    # a)
    print("### a) Primera noche de cada episodio\n")
    print("| Causa | " + " | ".join(f"Semilla {s}" for s in sem) + " | Total |")
    print("|---|" + "---|" * (len(sem) + 1))
    filas = list(CAUSAS) + ["cortado por presupuesto"]
    for causa in filas:
        por = [sum(1 for e in c["episodios"] if e["noche"] == causa) for c in corridas]
        if causa == "cortado por presupuesto" and not sum(por):
            continue
        print(f"| {causa} | " + " | ".join(_pct(x, len(c["episodios"])) for x, c in zip(por, corridas, strict=True)) + f" | {_pct(sum(por), len(eps))} |")
    print("\nMotivos dentro de cada causa (total de las semillas):\n")
    print("| Causa | Motivo | Episodios |")
    print("|---|---|---|")
    for causa in filas:
        for motivo, k in Counter(e["motivo_noche"] for e in eps if e["noche"] == causa).most_common(8):
            print(f"| {causa} | {motivo or '—'} | {k} |")
    entran = [e["oscuro_fuera_antes_de_entrar"] for e in eps if e["oscuro_fuera_antes_de_entrar"] is not None]
    print(f"\nLatidos oscuros fuera antes de entrar (episodios que entran): mediana {_med(entran)}, "
          f"máximo {max(entran) if entran else '—'}, n = {len(entran)}.")

    # b)
    pasan = [e for e in eps if e["noche"] == "pasa la noche dentro"]
    print("\n### b) Episodios que pasan la primera noche dentro\n")
    print(f"Episodios: {len(pasan)}.\n")
    print("| Causa de muerte | Episodios |")
    print("|---|---|")
    for causa, k in Counter(str(e["causa_muerte"]) if not e["vivo"] else "vivo al acabar" for e in pasan).most_common():
        print(f"| {causa} | {k} |")
    tras = [e["latidos"] - e["t_fin_noche"] for e in pasan]
    sal = [e["salida_tras_noche"] for e in pasan if e["salida_tras_noche"]]
    print(f"\n- Latidos vividos desde el final de lo oscuro: mediana {_med(tras)}, mínimo {min(tras) if tras else '—'}, "
          f"máximo {max(tras) if tras else '—'}.")
    print(f"- Salen del recinto tras la noche: {len(sal)} de {len(pasan)}; latidos desde el final de lo oscuro hasta salir: "
          f"mediana {_med([s['tras_fin_noche'] for s in sal])}.")
    print(f"- Al salir (0-9): comida mediana {_med([s['comida'] for s in sal])}, bebida mediana {_med([s['bebida'] for s in sal])}; "
          f"con comida ≤ 3: {sum(s['comida'] <= 3 for s in sal)}; con bebida ≤ 3: {sum(s['bebida'] <= 3 for s in sal)}.")
    print(f"- Con `wake_up`: {sum('wake_up' in e['logros'] for e in pasan)} de {len(pasan)}.")
    ret: Counter = Counter()
    for e in pasan:
        ret.update(e.get("retencion") or {})
    if ret:
        tr = sum(ret.values())
        print(f"\nQué gana desde el final de lo oscuro hasta salir ({tr} latidos):\n")
        print("| Estrategia · motivo | Latidos |\n|---|---|")
        for m, k in ret.most_common(8):
            print(f"| {m} | {_pct(k, tr)} |")
        imp: Dict[str, List[float]] = {}
        for e in pasan:
            for x in e.get("retencion_impulsos") or []:
                for k, v in x.items():
                    if isinstance(v, (int, float)):
                        imp.setdefault(k, []).append(float(v))
        tramos: Counter = Counter()
        for e in pasan:
            for x in e.get("retencion_impulsos") or []:
                if "gana" in x:
                    tramo = "peligro < 0,5" if x["peligro_alarma"] < 0.5 else ("0,5-0,8" if x["peligro_alarma"] < 0.8 else "≥ 0,8")
                    hostil = "hostil a ≤ 4" if x["hostil_d"] <= 4 else "sin hostil a ≤ 4"
                    tramos[(tramo, hostil, x["gana"])] += 1
        if tramos:
            print("\n| Peligro de la alarma | Hostil real | Gana | Latidos |\n|---|---|---|---|")
            for (tramo, hostil, gana), k in sorted(tramos.items(), key=lambda kv: -kv[1])[:12]:
                print(f"| {tramo} | {hostil} | {gana} | {_pct(k, tr)} |")
        rp: Counter = Counter()
        for e in pasan:
            rp.update(e.get("retencion_proteger") or {})
        print("\n| Propuesta de Proteger en esos latidos | Latidos |\n|---|---|")
        for m, k in rp.most_common(6):
            print(f"| {m} | {_pct(k, tr)} |")
        print("\n| Impulso en esos latidos | Mediana | p75 |\n|---|---|---|")
        for k in sorted(imp):
            q = statistics.quantiles(imp[k], n=4) if len(imp[k]) >= 4 else [0.0, 0.0, 0.0]
            print(f"| {k} | {statistics.median(imp[k]):.2f} | {q[2]:.2f} |")

    # b2) quién abre el recinto
    ap = [x for e in eps for x in e.get("aperturas") or []]
    if ap:
        print("\n### b2) Quién saca del recinto (cada paso de dentro a fuera)\n")
        print("| Fase | Estrategia · motivo | Verbo | Veces |\n|---|---|---|---|")
        for (fase, quien, verbo), k in Counter((x["fase"], f"{x['estrategia']} · {x['motivo']}", x["verbo"]) for x in ap).most_common(14):
            print(f"| {fase} | {quien} | {verbo} | {k} |")
        tras = [x for x in ap if x.get("primera_noche")]
        if tras:
            print(f"\nAl salir tras pasar dentro la primera noche ({len(tras)}): "
                  + "; ".join(f"{q}: {k}" for q, k in Counter(f"{x['estrategia']} · {x['motivo']}" for x in tras).most_common(6)) + ".")

    # a2) dónde está lo cavable en los que no encuentran sitio
    ns = [e for e in eps if e["noche"] == "no encuentra sitio" and e.get("cavable")]
    if ns:
        print("\n### a2) «No encuentra sitio»: casilla conocida más cercana de una clase que se puede cavar\n")
        print("| Caso | Episodios | Distancia Manhattan (mediana) |\n|---|---|---|")
        for caso in ("nunca vista", "lejos", "dentro del alcance"):
            g = [e for e in ns if e["cavable"]["caso"] == caso]
            print(f"| {caso} | {_pct(len(g), len(ns))} | {_med([e['cavable']['distancia'] for e in g if e['cavable']['distancia'] is not None])} |")
        mot = Counter(e["cavable"]["motivo"] for e in ns if e["cavable"]["caso"] == "dentro del alcance")
        for m, k in mot.most_common():
            print(f"- dentro del alcance, descartada: {m}: {k}")
        print(f"- clases que se pueden cavar según el modelo: {dict(Counter(c for e in ns for c in e['cavable']['clases']))}")
        formas: Counter = Counter()
        for e in ns:
            formas.update(e["cavable"].get("formas") or {})
        if formas:
            print(f"- formas de 1-3 casillas al alcance, por la primera razón de descarte (suma de episodios): {dict(formas.most_common())}")
            cerr = Counter(f"{k} ({'con' if n > 0 else 'sin'} material)" for e in ns for k, n in (e["cavable"].get("cerradores") or {}).items())
            print(f"- acciones que el modelo sabe que cierran (episodios): {dict(cerr.most_common())}; "
                  f"sin ninguna: {sum(1 for e in ns if e['cavable']['caso'] == 'dentro del alcance' and not e['cavable'].get('cerradores'))}")

    # c)
    mesa = [e for e in eps if "place_table" in e["logros"]]
    print("\n### c) Cadena de herramientas\n")
    print(f"Episodios con mesa: {_pct(len(mesa), len(eps))}.\n")
    if all("colocadas" in e for e in eps):
        mesas = [e["colocadas"].get("place_table", 0) for e in eps]
        print(f"Mesas colocadas por episodio (USAR que cambia el inventario): media {statistics.mean(mesas):.2f}, "
              f"mediana {_med(mesas)}, máximo {max(mesas)}; episodios con 2 o más: {sum(m >= 2 for m in mesas)}.\n")
        sin_ef: Counter = Counter()
        con_ef: Counter = Counter()
        for e in eps:
            sin_ef.update(e["usar_sin_efecto"])
            con_ef.update(e["colocadas"])
        print(f"USAR con efecto: {dict(con_ef.most_common())}; sin efecto: {dict(sin_ef.most_common())}.\n")
    print("| Herramienta | Fabricada tras la mesa | Latidos desde la mesa (mediana) | (p25-p75) |")
    print("|---|---|---|---|")
    for h in ("make_wood_pickaxe", "make_wood_sword"):
        d = sorted(e["logros"][h] - e["logros"]["place_table"] for e in mesa if h in e["logros"])
        q = statistics.quantiles(d, n=4) if len(d) >= 4 else None
        print(f"| {h} | {_pct(len(d), len(mesa))} | {_med(d)} | {f'{q[0]:.0f}-{q[2]:.0f}' if q else '—'} |")
    for clave, h, nombre in (("sin_pico", "make_wood_pickaxe", "pico"), ("sin_espada", "make_wood_sword", "espada")):
        sin = [e for e in mesa if h not in e["logros"]]
        lat = sum(sum(e["gana"][clave].values()) for e in sin)
        print(f"\n**Episodios con mesa y sin {nombre}: {len(sin)}** ({lat} latidos desde la mesa).\n")
        madera = sum(e["oportunidad"].get("madera", 0) for e in sin)
        ambas = sum(e["oportunidad"].get("madera_y_mesa", 0) for e in sin)
        total = sum(e["latidos_tras_mesa"] for e in sin)
        print(f"- Latidos con madera ≥ 1: {_pct(madera, total)}; con madera ≥ 1 y una mesa en el 3 × 3: {_pct(ambas, total)}.")
        gana: Counter = Counter()
        metas: Counter = Counter()
        usar: Counter = Counter()
        for e in sin:
            gana.update(e["gana"][clave])
            metas.update(e["metas"][clave])
            usar.update(e["usar"])
        print("\n| Estrategia · motivo que gana | Latidos |\n|---|---|")
        for m, k in gana.most_common(10):
            print(f"| {m} | {_pct(k, lat)} |")
        tm = sum(metas.values())
        print("\n| Mejor propuesta de PerseguirMetas (gane o no) | Latidos |\n|---|---|")
        for m, k in metas.most_common(8):
            print(f"| {m} | {_pct(k, tm)} |")
        print("\n| USAR con éxito tras la mesa (objetivo · motivo) | Veces |\n|---|---|")
        for m, k in usar.most_common(8):
            print(f"| {m} | {k} |")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--pasos", type=int, default=10000)
    p.add_argument("--semilla", type=int, default=31)
    p.add_argument("--manual", default="estricto")
    p.add_argument("--con-estrategias-propias", dest="sin_estrategias_propias", action="store_false")
    p.add_argument("--salida", default="diagnostico_paso3.json")
    p.add_argument("--plazo-logico", type=float, default=None, metavar="OPS",
                   help="guillotina lógica (operaciones por ms de plazo), como en evaluar_crafter.py")
    p.add_argument("--resumir", nargs="*", default=None, help="JSON de varias semillas: imprime las tablas")
    args = p.parse_args()
    if args.resumir:
        return resumir(args.resumir)
    return ejecutar(args)


if __name__ == "__main__":
    raise SystemExit(main())
