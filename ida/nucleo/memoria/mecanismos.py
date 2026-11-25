"""Mecanismos de memoria de los bloques E y F (apagados por defecto; un mundo los activa en su ``Perfil``): búfer diurno y
episodio del día (E1), grafo semántico y almacén de días (E2), conceptos e instancias (E3), reducción nocturna (E4),
repaso (E6), reconsolidación (decisión 22) y modelo de transiciones para las expectativas (F1)."""

import heapq
from typing import Any, Dict, List, Optional, Set, Tuple

from ida.nucleo.memoria.proposiciones import Proposicion
from ida.nucleo.pieza import acotar
from ida.nucleo.vocabulario import EstadoSaber, Relacion


class Mecanismos:
    """Parte de la ``Memoria`` (fachada en ``almacen.py``): bloques E y F."""

    saber: Dict[Tuple[str, Relacion], Proposicion]
    aciertos: int
    fallos: int
    diurno: List[Tuple[float, int, Dict[str, Any]]]
    _orden_diurno: int
    dia: List[Dict[str, Any]]
    grafo: Dict[str, Dict[str, Any]]
    relaciones: Dict[Tuple[str, str], float]
    dias: List[Dict[str, Any]]
    conceptos: Dict[str, Dict[str, Any]]
    _concepto_de: Dict[str, str]
    instancias: Dict[str, Dict[str, Any]]
    modelo: Dict[Tuple[str, str, str], Dict[str, Any]]
    _modelo_por: Dict[Tuple[str, str], Set[str]]

    CAPACIDAD_DIURNO = 256      # piezas que caben en el búfer diurno
    CAPACIDAD_DIA = 1000        # latidos que caben en el episodio del día

    def marcar(self, latido: int, piezas: List[Dict[str, Any]], feedback: float, resumen: Dict[str, Any]) -> None:
        """De día (decisión 19): puntúa cada pieza (arousal + feedback del latido) y guarda las mejores en
        un búfer de tamaño fijo; si está lleno, una pieza nueva solo entra si supera a la peor. Barato:
        montículo en memoria. Añade el latido al episodio del día."""
        for p in piezas:
            puntuacion = float(p["arousal"]) + feedback
            self._orden_diurno += 1
            entrada = (puntuacion, self._orden_diurno, {**p, "puntuacion": round(puntuacion, 4)})
            if len(self.diurno) < self.CAPACIDAD_DIURNO:
                heapq.heappush(self.diurno, entrada)
            elif puntuacion > self.diurno[0][0]:
                heapq.heapreplace(self.diurno, entrada)
        if len(self.dia) < self.CAPACIDAD_DIA:
            self.dia.append({"latido": latido, "feedback": round(feedback, 4), **resumen})

    DIAS_GUARDADOS = 30         # días que conserva el almacén de episodios del día
    NODOS_POR_LATIDO = 5        # piezas de un mismo latido que se relacionan entre sí al consolidar

    @staticmethod
    def nodo(pieza: Dict[str, Any]) -> str:
        """Nodo semántico de una pieza: su tipo y su clase (o su id, si no tiene clase)."""
        return f"{pieza.get('tipo', '')}:{pieza.get('clase') or pieza.get('id', '')}"

    def consolidar_dia(self, ahora: int) -> Dict[str, int]:
        """De noche (decisión 19): lo mejor puntuado del búfer diurno pasa al grafo semántico (fuerza =
        puntuación positiva; valencia = feedback acumulado) y se relaciona con lo que coincidió en el mismo
        latido; el episodio del día pasa al almacén de días. El búfer y el día se vacían."""
        por_latido: Dict[int, List[Dict[str, Any]]] = {}
        for _, _, p in sorted(self.diurno, reverse=True):
            por_latido.setdefault(int(p.get("latido", 0)), []).append(p)
            nodo = self.nodo(p)
            n = self.grafo.setdefault(nodo, {"fuerza": 0.0, "valencia": 0.0, "usos": 0, "ultimo": 0,
                                              "tipo": p.get("tipo", ""), "clase": p.get("clase", "")})
            n["fuerza"] = round(n["fuerza"] + max(0.0, float(p["puntuacion"])), 4)
            n["valencia"] = round(n["valencia"] + float(p["puntuacion"]) - float(p["arousal"]), 4)
            n["usos"] += 1
            n["ultimo"] = max(n["ultimo"], int(p.get("latido", 0)))
        relaciones = 0
        for piezas in por_latido.values():
            nodos = sorted({self.nodo(p): float(p["puntuacion"]) for p in piezas[: self.NODOS_POR_LATIDO]}.items())
            for i, (a, pa) in enumerate(nodos):
                for b, pb in nodos[i + 1:]:
                    self.relaciones[(a, b)] = round(self.relaciones.get((a, b), 0.0) + max(0.0, min(pa, pb)), 4)
                    relaciones += 1
        consolidadas = len(self.diurno)
        if self.dia:
            self.dias.append({"fin": ahora, "latidos": len(self.dia), "feedback": round(sum(d["feedback"] for d in self.dia), 4),
                              "ondas": list(self.dia)})
            del self.dias[: max(0, len(self.dias) - self.DIAS_GUARDADOS)]
        self.diurno.clear()
        self.dia.clear()
        return {"piezas_consolidadas": consolidadas, "relaciones": relaciones}

    MAX_INSTANCIAS = 500        # instancias recordadas (se olvidan las vistas hace más tiempo)

    def instancia(self, instancia: str, clase: str, rasgos: Dict[str, float], ahora: int) -> str:
        """Decisión 20: actualiza el concepto de la clase (prototipo = media de los rasgos de sus
        instancias) y recuerda la instancia. Devuelve el id estable del concepto."""
        cid = self._concepto_de.get(clase)
        if cid is None:
            cid = f"c{len(self.conceptos) + 1}"
            self._concepto_de[clase] = cid
            self.conceptos[cid] = {"etiqueta": clase, "prototipo": {}, "n": 0}
        c = self.conceptos[cid]
        c["n"] += 1
        proto = c["prototipo"]
        for k in set(proto) | set(rasgos):
            proto[k] = round(proto.get(k, 0.0) + (float(rasgos.get(k, 0.0)) - proto.get(k, 0.0)) / c["n"], 4)
        self.instancias[instancia] = {"concepto": cid, "visto": ahora}
        if len(self.instancias) > self.MAX_INSTANCIAS:
            del self.instancias[min(self.instancias, key=lambda i: self.instancias[i]["visto"])]
        return cid

    def concepto(self, clase: str) -> Optional[Dict[str, Any]]:
        cid = self._concepto_de.get(clase)
        return self.conceptos.get(cid) if cid else None

    # --- F1: expectativas (dimensión proactiva, decisión 24) ----------------------
    MAX_MODELO = 1000            # entradas (sistema, verbo, clase); se olvida la usada hace más tiempo
    N_MAX_MODELO = 10            # la media del modelo pesa como mucho 10 experiencias (sigue los cambios)
    UMBRAL_SORPRESA = 0.1        # error de predicción a partir del cual hay sorpresa
    PARECIDO_CONCEPTO = 0.2      # distancia máxima entre prototipos para generalizar de un concepto a otro

    @staticmethod
    def _distancia(a: Dict[str, float], b: Dict[str, float]) -> float:
        claves = set(a) | set(b)
        return sum(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in claves) / len(claves) if claves else 1.0

    def esperar(self, sistema: str, verbo: str, clase: str) -> Optional[Tuple[Dict[str, float], str]]:
        """Lo que se espera que cambie cada variable si ``sistema`` hace ``verbo`` sobre ``clase``, y de dónde
        sale: lo vivido con esa clase («episodios»); si no, lo vivido con la clase de concepto más parecido
        («concepto»); para S2, la valencia del nodo del grafo semántico («grafo»). None si no hay base."""
        entrada = self.modelo.get((sistema, verbo, clase))
        if entrada is not None:
            return {k: m for k, (_, m) in entrada["vars"].items()}, "episodios"
        propio = self.concepto(clase)
        if propio is not None:
            mejor: Optional[Tuple[float, str]] = None
            for otra in sorted(self._modelo_por.get((sistema, verbo), ())):
                otro = self.concepto(otra)
                if otro is None:
                    continue
                d = self._distancia(propio["prototipo"], otro["prototipo"])
                if d <= self.PARECIDO_CONCEPTO and (mejor is None or d < mejor[0]):
                    mejor = (d, otra)
            if mejor is not None:
                return {k: m for k, (_, m) in self.modelo[(sistema, verbo, mejor[1])]["vars"].items()}, "concepto"
        nodo = self.grafo.get(f"Objeto:{clase}")
        if sistema == "S2" and nodo is not None and nodo.get("usos", 0) > 0:
            return {"valencia": round(float(nodo["valencia"]) / float(nodo["usos"]), 4)}, "grafo"
        return None

    def contrastar(self, sistema: str, verbo: str, clase: str, observado: Dict[str, float], ahora: int) -> Optional[float]:
        """Compara lo observado con lo esperado (si había expectativa), cuenta acierto o fallo (los contadores
        del error de predicción que ya usa el feedback de S3) y aprende la transición. Devuelve el error."""
        esperado = self.esperar(sistema, verbo, clase)
        error: Optional[float] = None
        if esperado is not None:
            exp = esperado[0]
            if "valencia" in exp:
                obs_val = observado.get("placer", 0.0) - observado.get("estres", 0.0)
                error = abs(obs_val - exp["valencia"])
            else:
                error = sum(abs(observado.get(k, 0.0) - e) for k, e in exp.items())
            error = round(error, 4)
            if error >= self.UMBRAL_SORPRESA:
                self.fallos += 1
            else:
                self.aciertos += 1
        clave = (sistema, verbo, clase)
        entrada = self.modelo.setdefault(clave, {"vars": {}, "ultimo": ahora})
        entrada["ultimo"] = ahora
        variables = dict(observado)
        if sistema == "S2":
            variables["valencia"] = observado.get("placer", 0.0) - observado.get("estres", 0.0)
            variables = {"valencia": variables["valencia"]}
        for k, v in variables.items():
            n, m = entrada["vars"].get(k, (0, 0.0))
            n = min(n + 1, self.N_MAX_MODELO)
            entrada["vars"][k] = (n, round(m + (v - m) / n, 4))
        self._modelo_por.setdefault((sistema, verbo), set()).add(clase)
        if len(self.modelo) > self.MAX_MODELO:
            viejo = min(self.modelo, key=lambda c: self.modelo[c]["ultimo"])
            del self.modelo[viejo]
            self._modelo_por.get((viejo[0], viejo[1]), set()).discard(viejo[2])
        return error

    REPASO_FUERZA = 1.1            # E6: refuerzo de un nodo repasado
    REPASO_CONFIANZA = 0.02        # E6: refuerzo de las hipótesis de la clase repasada
    REPASO_VENTANA = 100           # E6: latidos hacia atrás que cuentan como «reciente»

    def recientes_para_repaso(self, ahora: int, n: int = 2) -> List[Tuple[str, str]]:
        """Lo reciente de más fuerza (decisión 21): nodos del grafo de los últimos ``REPASO_VENTANA``
        latidos o, si aún no hay grafo, lo mejor del búfer del día. Devuelve (nodo, clase)."""
        nodos = [(d["fuerza"], k, d.get("clase", "")) for k, d in self.grafo.items() if ahora - d.get("ultimo", 0) <= self.REPASO_VENTANA]
        if not nodos:
            nodos = [(punt, self.nodo(p), p.get("clase", "")) for punt, _, p in self.diurno]
        return [(k, c) for _, k, c in sorted(nodos, reverse=True)[:n]]

    def repasar(self, nodo: str, clase: str, ahora: int) -> None:
        """Repaso en calma: refuerza el nodo y las hipótesis de su clase, y las refresca."""
        if nodo in self.grafo:
            self.grafo[nodo]["fuerza"] = round(self.grafo[nodo]["fuerza"] * self.REPASO_FUERZA, 4)
            self.grafo[nodo]["ultimo"] = ahora
        for (c, _), p in self.saber.items():
            if c == clase and p.estado(ahora) == EstadoSaber.HIPOTESIS:
                p.c_exp = acotar(p.c_exp + self.REPASO_CONFIANZA)
                p.actualizada = max(p.actualizada, ahora)

    def reconsolidar(self, clave: Tuple[str, Relacion], ahora: int, arousal: float) -> None:
        """Decisión 22: un recuerdo recuperado vuelve a ser modificable; se refresca (no envejece) y, si
        hay búfer diurno, entra en él para persistirse de noche."""
        p = self.saber.get(clave)
        if p is not None:
            p.actualizada = max(p.actualizada, ahora)
        if self.diurno is not None:
            self._orden_diurno += 1
            pieza = {"latido": ahora, "tipo": "Recuerdo", "id": f"{clave[0]}|{clave[1].name}", "arousal": arousal, "clase": clave[0],
                     "sistema": "S2", "puntuacion": arousal}
            if len(self.diurno) < self.CAPACIDAD_DIURNO:
                heapq.heappush(self.diurno, (arousal, self._orden_diurno, pieza))
            elif arousal > self.diurno[0][0]:
                heapq.heapreplace(self.diurno, (arousal, self._orden_diurno, pieza))

    REDUCCION_GRAFO = 0.9          # E4: factor nocturno sobre las fuerzas del grafo semántico
    PODA_GRAFO = 0.05              # E4: fuerza por debajo de la cual se poda un nodo o relación
    REDUCCION_HIPOTESIS = 0.95     # E4: factor nocturno de referencia (= 1 − Proposicion.DECAY); cada hipótesis usa su decay
    PODA_HIPOTESIS = 0.15          # E4: confianza por debajo de la cual se poda una hipótesis

    def reducir(self, ahora: int) -> int:
        """Reducción nocturna (decisión 21, homeostasis sináptica): todas las fuerzas del grafo y la
        confianza de las hipótesis no demostradas se reducen en proporción (se mantienen las diferencias
        relativas) y se poda lo que cae por debajo del umbral. Devuelve lo podado."""
        podado = 0
        for nodo in list(self.grafo):
            self.grafo[nodo]["fuerza"] = round(self.grafo[nodo]["fuerza"] * self.REDUCCION_GRAFO, 4)
            if self.grafo[nodo]["fuerza"] < self.PODA_GRAFO:
                del self.grafo[nodo]
                podado += 1
        for clave in list(self.relaciones):
            self.relaciones[clave] = round(self.relaciones[clave] * self.REDUCCION_GRAFO, 4)
            if self.relaciones[clave] < self.PODA_GRAFO or clave[0] not in self.grafo or clave[1] not in self.grafo:
                del self.relaciones[clave]
                podado += 1
        for clave, p in list(self.saber.items()):
            if p.estado(ahora) == EstadoSaber.DEMOSTRADA:
                continue
            p.c_exp = acotar(p.c_exp * (1.0 - p.decay))   # metadato decay (por defecto, ×REDUCCION_HIPOTESIS)
            if p.confianza < self.PODA_HIPOTESIS:
                del self.saber[clave]
                podado += 1
        return podado
