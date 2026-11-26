"""Análisis de vidas para el Laboratorio (T5b): series de una vida, historia de lo que sabe y comparación de estirpes.

Todo sale del registro del latido v1 (sección 4 del diseño) ya publicado o grabado: no se pide nada al motor y nada de
esto cambia la conducta de IdA (O3). Tres piezas:

- ``Series``: acumula, registro a registro, lo que las vistas Epistemología, Biología, Análisis y Cierre dibujan a lo
  largo del tiempo, en columnas (una lista por serie, alineada con ``n``, la posición del registro en su fuente). Las
  grabaciones la calculan al abrirse (``laboratorio._Abierta``) y el directo, con cada registro (``laboratorio.Directo``).
- La historia de cada proposición y de cada requisito: cuándo nace, cómo cambia su confianza y su estado, de qué fuente
  es y cuándo da hechos (``aprende``, ``duda``, ``refuta``). Con nivel cognitivo el registro solo trae las 20
  proposiciones de más confianza (``saber``): una que sale de esas 20 queda «fuera» (no se sabe su confianza) hasta que
  vuelve; con nivel completo el ``saber`` es entero y la que desaparece se ha olvidado. Los hechos se ven siempre.
- ``comparar_estirpes``: dos linajes (``Vivero.estirpe``) generación a generación.

La Score de cada latido es la de la colección y el linaje (``ida/historico.py``, ``calcular_fitness``, sección 13.1):
no es la Score oficial de D17, que no se puede dar por latido.
"""

import math
from collections import Counter
from typing import Any, Dict, List, Optional

from ida.historico import calcular_fitness

# Hechos que las vistas marcan sobre las series (los cambios de estrategia, muchos y técnicos, no).
HECHOS_SERIES = frozenset({"nace", "primera_vez", "aprende", "logro", "peligro", "sorpresa", "duda", "refuta", "muere",
                           "duerme", "despierta"})
VITALES = ("vitalidad", "alimentacion", "energia", "descanso")
QUIMICA = ("dopamina", "placer", "estres")
INDICADORES = ("peligro", "tension", "calma")
RESUMEN = ("proposiciones", "demostradas", "hipotesis", "refutadas", "heredadas", "requisitos", "requisitos_confirmados",
           "aciertos", "sorpresas")
DECIMALES = 4


def redondear(x: float, decimales: int = DECIMALES) -> float:
    """Redondeo con la misma aritmética que ``Math.round(x * 10^d) / 10^d`` de JS (``web/lab/series.js``): así las series
    de un fichero cargado en el navegador son idénticas a las del servidor."""
    escala = 10 ** decimales
    return math.floor(float(x) * escala + 0.5) / escala


def _num(x: Any) -> Optional[float]:
    if isinstance(x, bool):
        return float(x)
    if isinstance(x, (int, float)) and x == x:
        return redondear(x)
    return None


def fuente_saber(s: Dict[str, Any]) -> str:
    """La fuente de una proposición del campo ``saber`` (como ``hechos.fuente``): ``herencia``, ``manual`` o
    ``experiencia``. La biblioteca solo se distingue en los requisitos (sección 12, límites conocidos)."""
    if s.get("heredada"):
        return "herencia"
    if s.get("autoridad"):
        return "manual"
    return "experiencia"


def clave_proposicion(sujeto: Any, relacion: Any) -> str:
    return f"p|{sujeto}|{relacion}"


def clave_requisito(verbo: Any, clase: Any) -> str:
    return f"r|{verbo}|{clase}"


def score_de(mundo: str, registro: Dict[str, Any]) -> float:
    """La Score de la colección (``calcular_fitness``) con la puntuación y el latido de un registro."""
    punt = (registro.get("score") or {}).get("puntuacion") or {}
    return round(calcular_fitness(mundo, {"puntuacion": punt if isinstance(punt, dict) else {}, "latidos": registro.get("latido", 0)}), 2)


class Series:
    """Las series de una fuente (una grabación o el directo), registro a registro."""

    def __init__(self) -> None:
        self.columnas: Dict[str, List[Any]] = {}
        self.longitud = 0
        self.mundo: Optional[str] = None
        self.niveles: Counter = Counter()
        self.hechos: List[Dict[str, Any]] = []
        self.saber: Dict[str, Dict[str, Any]] = {}
        self.vidas: List[Dict[str, Any]] = []
        self._previo: Optional[Dict[str, Any]] = None    # el último registro (para la vitalidad que baja)

    # --- columnas ----------------------------------------------------------------------------------------------------
    def _poner(self, fila: Dict[str, Any]) -> None:
        for nombre, valor in fila.items():
            col = self.columnas.get(nombre)
            if col is None:
                col = self.columnas[nombre] = [None] * self.longitud   # una serie que aparece tarde: vacía antes
            col.append(valor)
        self.longitud += 1
        for col in self.columnas.values():
            if len(col) < self.longitud:
                col.append(None)

    # --- un registro -------------------------------------------------------------------------------------------------
    def anadir(self, r: Dict[str, Any], n: int) -> None:
        """Añade el registro ``r``, que está en la posición ``n`` de su fuente."""
        self.mundo = self.mundo or str(r.get("mundo") or "")
        nivel = str(r.get("nivel") or "")
        self.niveles[nivel] += 1
        cuerpo, quimica, afecto = r.get("cuerpo") or {}, r.get("quimica") or {}, r.get("afecto") or {}
        ritmo, score = r.get("ritmo") or {}, r.get("score") or {}
        resumen = r.get("resumen_saber") or r.get("memoria") or {}
        amplitud, potencia = list(ritmo.get("amplitud") or [None, None]), list(ritmo.get("potencia") or [None, None])
        hechos = [h for h in (r.get("hechos") or []) if isinstance(h, dict)]
        rpe = [float(h["rpe"]) for h in hechos if h.get("tipo") == "sorpresa" and isinstance(h.get("rpe"), (int, float))]
        fila: Dict[str, Any] = {
            "n": n, "vida": r.get("vida"), "generacion": r.get("generacion"), "latido": r.get("latido"),
            "cierre": bool(r.get("cierre")), "dormido": bool(cuerpo.get("dormido")),
            **{f"cuerpo/{k}": _num(cuerpo.get(k)) for k in VITALES},
            **{f"quimica/{k}": _num(quimica.get(k)) for k in QUIMICA},
            "afecto/valencia": _num(afecto.get("valencia")), "afecto/estado": afecto.get("estado"),
            **{f"indicadores/{k}": _num((afecto.get("indicadores") or {}).get(k)) for k in INDICADORES},
            **{f"saber/{k}": _num(resumen.get(k)) for k in RESUMEN if k in resumen},
            "score": score_de(self.mundo, r), "logros": len(score.get("logros") or []),
            "ritmo/amplitud": _num(amplitud[0]), "ritmo/amplitud_max": _num(amplitud[1]),
            "ritmo/potencia": _num(potencia[0]), "ritmo/potencia_max": _num(potencia[1]),
            "ritmo/guillotina": bool(ritmo.get("guillotina")), "ritmo/ms": _num(ritmo.get("ms")),
            "rpe": redondear(sum(rpe), 3) if rpe else None,
            "sistema": str((r.get("accion") or {}).get("sistema") or ""),
        }
        for nec in r.get("necesidades") or []:
            if isinstance(nec, dict) and nec.get("nombre"):
                fila[f"necesidad/{nec['nombre']}"] = _num(nec.get("deficit"))
        punt = score.get("puntuacion")
        if isinstance(punt, dict):
            for k, v in punt.items():
                valor = _num(v) if not isinstance(v, bool) else None
                if valor is not None:
                    fila[f"puntuacion/{k}"] = valor
        self._poner(fila)
        self._hechos(r, n, hechos)
        self._saber(r, n, hechos)
        self._vida(r, n, hechos)
        self._previo = r

    def _hechos(self, r: Dict[str, Any], n: int, hechos: List[Dict[str, Any]]) -> None:
        base = {"n": n, "vida": r.get("vida"), "latido": r.get("latido"), **({"cierre": True} if r.get("cierre") else {})}
        for h in hechos:
            if h.get("tipo") in HECHOS_SERIES:
                self.hechos.append({**base, **h})
        # Daño: la vitalidad baja respecto al latido anterior de la misma vida. No es un hecho del catálogo (sección 5):
        # lo deduce esta vista de la serie del cuerpo, y lo dice («baja la vitalidad»).
        previo = self._previo
        if previo is not None and previo.get("vida") == r.get("vida") and not r.get("cierre"):
            antes = _num((previo.get("cuerpo") or {}).get("vitalidad"))
            ahora = _num((r.get("cuerpo") or {}).get("vitalidad"))
            if antes is not None and ahora is not None and ahora < antes:
                self.hechos.append({**base, "tipo": "dano", "perdida": redondear(antes - ahora, 3), "vitalidad": ahora})

    def _saber(self, r: Dict[str, Any], n: int, hechos: List[Dict[str, Any]]) -> None:
        nivel = r.get("nivel")
        vistos = set()
        if isinstance(r.get("saber"), list):
            for s in r["saber"]:
                clave = clave_proposicion(s.get("sujeto"), s.get("relacion"))
                vistos.add(clave)
                p = self.saber.setdefault(clave, {"tipo": "proposicion", "sujeto": s.get("sujeto"), "relacion": s.get("relacion"),
                                                  "historia": [], "eventos": []})
                p["fuente"] = fuente_saber(s)
                self._paso(p, n, r, str(s.get("estado")), _num(s.get("confianza")), p["fuente"])
            # La que estaba y ya no está: fuera de las 20 (cognitivo) u olvidada (completo, el saber es entero).
            for clave, p in self.saber.items():
                if p["tipo"] == "proposicion" and clave not in vistos and p["historia"] and p["historia"][-1][2] not in ("fuera", "olvidada"):
                    self._paso(p, n, r, "olvidada" if nivel == "completo" else "fuera", None, p.get("fuente"))
        if isinstance(r.get("requisitos"), list):
            for q in r["requisitos"]:
                clave = clave_requisito(q.get("verbo"), q.get("clase"))
                p = self.saber.setdefault(clave, {"tipo": "requisito", "verbo": q.get("verbo"), "clase": q.get("clase"),
                                                  "historia": [], "eventos": []})
                p.update(fuente=str(q.get("fuente") or ""), requiere=q.get("requiere"), cerca=q.get("cerca"), efecto=q.get("efecto"))
                self._paso(p, n, r, "confirmado" if q.get("confirmado") else "sin_confirmar", _num(q.get("confianza")), p["fuente"])
        for h in hechos:
            tipo = h.get("tipo")
            if tipo in ("aprende", "duda", "refuta"):
                if h.get("saber") == "requisito":
                    clave = clave_requisito(h.get("verbo"), h.get("clase"))
                    nuevo: Dict[str, Any] = {"tipo": "requisito", "verbo": h.get("verbo"), "clase": h.get("clase"), "historia": [], "eventos": []}
                else:
                    clave = clave_proposicion(h.get("clase"), h.get("relacion"))
                    nuevo = {"tipo": "proposicion", "sujeto": h.get("clase"), "relacion": h.get("relacion"), "historia": [], "eventos": []}
                p = self.saber.setdefault(clave, nuevo)
                if h.get("fuente"):
                    p.setdefault("fuente", h["fuente"])
                estado = h.get("estado") or {"duda": "hipotesis", "refuta": "refutada"}.get(str(tipo))
                if h.get("saber") == "requisito":
                    estado = "confirmado" if h.get("confirmado") else "sin_confirmar"
                p["eventos"].append({"n": n, "vida": r.get("vida"), "latido": r.get("latido"), "tipo": tipo, "estado": estado,
                                     "confianza": _num(h.get("confianza")), **({"cierre": True} if r.get("cierre") else {})})
                # Sin el campo saber (nivel vital), la historia sale solo de los hechos.
                if not isinstance(r.get("saber" if h.get("saber") != "requisito" else "requisitos"), list):
                    self._paso(p, n, r, str(estado), _num(h.get("confianza")), p.get("fuente"))

    @staticmethod
    def _paso(p: Dict[str, Any], n: int, r: Dict[str, Any], estado: str, confianza: Optional[float], fuente: Optional[str]) -> None:
        """Apunta en la historia de un saber ``[n, latido, estado, confianza, fuente, vida]`` si algo cambió."""
        h = p["historia"]
        if h and h[-1][2] == estado and h[-1][3] == confianza and h[-1][4] == fuente and h[-1][5] == r.get("vida"):
            return
        h.append([n, r.get("latido"), estado, confianza, fuente, r.get("vida")])

    def _vida(self, r: Dict[str, Any], n: int, hechos: List[Dict[str, Any]]) -> None:
        vida = r.get("vida")
        if not self.vidas or self.vidas[-1]["vida"] != vida:
            self.vidas.append({"vida": vida, "individuo": r.get("individuo"), "generacion": r.get("generacion"),
                               "desde": n, "latido_inicial": r.get("latido"), "nace": None, "muere": None, "cierre": None,
                               "resumen_inicial": r.get("resumen_saber"), "aprendidas": 0, "sorpresas": 0, "danos": 0})
        v = self.vidas[-1]
        v.update(hasta=n, latido_final=r.get("latido"), resumen_final=r.get("resumen_saber"),
                 logros=list((r.get("score") or {}).get("logros") or []), puntuacion=(r.get("score") or {}).get("puntuacion"),
                 score=score_de(self.mundo or "", r), arquetipo=r.get("arquetipo"))
        for h in hechos:
            tipo = h.get("tipo")
            if tipo == "nace":
                v["nace"] = h
            elif tipo == "muere":
                v["muere"] = dict(h, n=n)
            elif tipo == "aprende" and not r.get("cierre"):
                v["aprendidas"] += 1
            elif tipo == "sorpresa":
                v["sorpresas"] += 1
        if self.hechos and self.hechos[-1].get("tipo") == "dano" and self.hechos[-1]["n"] == n:
            v["danos"] += 1
        if r.get("cierre"):
            v["cierre"] = {"n": n, "latido": r.get("latido"), "hechos": hechos,
                           "aprendizaje": list((r.get("experiencia") or {}).get("aprendizaje") or [])}

    # --- salida ------------------------------------------------------------------------------------------------------
    def podar(self, primero: int) -> None:
        """Olvida lo anterior a la posición ``primero`` (el directo guarda los últimos N registros). Cada historia
        conserva su último paso anterior, para saber en qué estado entra en lo que queda."""
        if not self.columnas or not self.columnas["n"] or self.columnas["n"][0] >= primero:
            return
        corte = next((i for i, x in enumerate(self.columnas["n"]) if x >= primero), self.longitud)
        for nombre in list(self.columnas):
            self.columnas[nombre] = self.columnas[nombre][corte:]
        self.longitud -= corte
        self.hechos = [h for h in self.hechos if h["n"] >= primero]
        for p in self.saber.values():
            h = p["historia"]
            dentro = [x for x in h if x[0] >= primero]
            antes = [x for x in h if x[0] < primero]
            p["historia"] = ([[primero, *antes[-1][1:]]] if antes and (not dentro or dentro[0][0] > primero) else []) + dentro
            p["eventos"] = [e for e in p["eventos"] if e["n"] >= primero]
        self.vidas = [v for v in self.vidas if v.get("hasta", v["desde"]) >= primero]
        if self.vidas and self.vidas[0]["desde"] < primero:
            self.vidas[0] = dict(self.vidas[0], desde=primero, recortada=True)

    def resultado(self) -> Dict[str, Any]:
        saber = [dict(p, clave=k) for k, p in self.saber.items() if p["historia"] or p["eventos"]]
        return {
            "mundo": self.mundo, "registros": self.longitud, "niveles": dict(self.niveles),
            "columnas": self.columnas, "hechos": self.hechos, "saber": saber, "vidas": self.vidas,
        }


def series_de(registros: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Las series de una secuencia de registros (en orden): ``Series`` de una vez."""
    s = Series()
    for i, r in enumerate(registros):
        s.anadir(r, i)
    return s.resultado()


def historia(series: Dict[str, Any], clave: str) -> Optional[Dict[str, Any]]:
    """La historia de un saber (``clave_proposicion`` o ``clave_requisito``) dentro de unas series."""
    return next((p for p in series["saber"] if p["clave"] == clave), None)


# --- estirpes ------------------------------------------------------------------------------------------------------------
RASGOS = ("apertura", "responsabilidad", "neuroticismo", "extraversion", "umbral_miedo")


def _resumen_estirpe(e: Dict[str, Any]) -> Dict[str, Any]:
    vidas = e.get("vidas") or []
    scores = [float(v["score"]) for v in vidas if isinstance(v.get("score"), (int, float))]
    causas = Counter(str(v.get("causa_muerte")) for v in vidas if v.get("causa_muerte"))
    return {"ref": e.get("ref"), "nombre": e.get("nombre"), "mundo": e.get("mundo"), "tipo": e.get("tipo"),
            "generaciones": len(vidas), "mejor_score": max(scores) if scores else None,
            "media_score": round(sum(scores) / len(scores), 2) if scores else None,
            "causas": dict(causas.most_common()), "arquetipo": e.get("arquetipo")}


def comparar_estirpes(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Dos estirpes (``Vivero.estirpe``) generación a generación: Score, latidos, causa de muerte, logros y los cinco
    rasgos de cada una, alineadas por número de generación (la retención del linaje puede dejar huecos: ese lado va
    vacío), y la diferencia de Score donde están las dos."""
    por_a = {int(v["generacion"]): v for v in a.get("vidas") or []}
    por_b = {int(v["generacion"]): v for v in b.get("vidas") or []}
    filas = []
    for g in sorted(set(por_a) | set(por_b)):
        va, vb = por_a.get(g), por_b.get(g)
        fila: Dict[str, Any] = {"generacion": g, "a": va, "b": vb, "diferencia": None, "rasgos": {}}
        if va and vb and isinstance(va.get("score"), (int, float)) and isinstance(vb.get("score"), (int, float)):
            fila["diferencia"] = round(float(vb["score"]) - float(va["score"]), 2)
        for r in RASGOS:
            ra = ((va or {}).get("arquetipo") or {}).get(r)
            rb = ((vb or {}).get("arquetipo") or {}).get(r)
            fila["rasgos"][r] = [ra, rb]
        filas.append(fila)
    mundos = {a.get("mundo"), b.get("mundo")}
    return {"a": _resumen_estirpe(a), "b": _resumen_estirpe(b), "mismo_mundo": len(mundos) == 1, "filas": filas,
            "rasgos": list(RASGOS)}

