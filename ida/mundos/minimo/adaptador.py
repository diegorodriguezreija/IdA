"""Mundo mínimo: una pradera de 9×9 para tests y como tutorial de cómo se escribe un mundo.

- ``baya``: parece nutritiva y lo es (+20 de alimentación).
- ``seta``: parece nutritiva, pero es tóxica (−12 de vitalidad). Solo la experiencia lo revela.
- ``piedra``: no se come; sirve para algo (se puede coger).
- ``lobo``: se acerca a veces; si está al lado, muerde (−8 de vitalidad). Se le puede atacar.

Los lugares son las cuatro casillas vecinas. Para cada una, el mundo calcula sus rasgos:
``nutritivo`` (cuánto acerca a lo que parece comida), ``peligro`` (cercanía al lobo) y ``novedad``
(si no se ha pisado hace tiempo).
"""

import copy
from typing import Any, Dict, List, Optional, Set, Tuple

from ida.nucleo.azar import Azar
from ida.nucleo.mundo import Alta, Efecto, Entidad, Mundo, Observacion, Perfil, Registro
from ida.nucleo.vocabulario import Verbo
from ida.mundos.opciones import opcion
from ida.mundos.minimo.s1.reaccionar.estrategias.defensa import Defensa

TAM = 9
VISION = 4
APARIENCIA = {"baya": 0.8, "seta": 0.7}     # lo que «promete» a la vista
VECINOS = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "O": (-1, 0)}


def _dist(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _t(es: str, en: str) -> Dict[str, str]:
    return {"es": es, "en": en}


OPCIONES = [
    opcion("tamano", "entero", 9,
           _t("Tamaño de la rejilla", "Grid size"),
           _t("Lado de la pradera en casillas (9 por defecto). IdA nace en el centro.",
              "Side of the meadow in tiles (9 by default). IdA is born at the centre."),
           min=5, max=25),
    opcion("depredadores", "entero", 1,
           _t("Número de depredadores", "Number of predators"),
           _t("Lobos que persiguen y atacan en la pradera (1 por defecto).",
              "Wolves that chase and attack in the meadow (1 by default)."),
           min=0, max=5),
    opcion("comida", "entero", 4,
           _t("Abundancia de comida", "Food abundance"),
           _t("Número de bayas nutritivas sembradas en la pradera (4 por defecto).",
              "Number of nutritious berries seeded in the meadow (4 by default)."),
           min=1, max=20),
]


class MundoMinimo(Mundo):
    nombre = "minimo"
    perfil = Perfil(
        frecuencia_ms=100.0,
        amplitud=100,
        memoria="completa",
        duerme=True,
        hogar=True,
        peso_experiencia=0.2,
        rasgos_declarados=("peligro", "nutritivo", "recurso", "novedad"),
    )

    def __init__(self, tamano: Any = 9, depredadores: Any = 1, comida: Any = 4, **_):
        self.tam = int(tamano)
        self.depredadores = int(depredadores)
        self.comida = int(comida)
        self.azar = Azar(0)
        self.reiniciar(0)

    @classmethod
    def opciones(cls) -> List[Dict[str, Any]]:
        return copy.deepcopy(OPCIONES)

    def reiniciar(self, semilla: Optional[int]) -> None:
        self.azar = Azar(semilla)
        self.pos = (self.tam // 2, self.tam // 2)
        self.cosas: Dict[str, Dict[str, Any]] = {}
        self.n = 0
        for _ in range(self.comida):
            self._sembrar("baya")
        for _ in range(3):
            self._sembrar("seta")
        for _ in range(2):
            self._sembrar("piedra")
        self.lobos: List[Dict[str, Any]] = []
        for i in range(self.depredadores):
            lid = "lobo" if self.depredadores == 1 else f"lobo_{i+1}"
            self.lobos.append({"id": lid, "pos": (0, 0), "vivo": True})
        self.lobo = self.lobos[0] if self.lobos else {"pos": (0, 0), "vivo": False}
        self.pisadas: Dict[Tuple[int, int], int] = {}
        self.t = 0
        self.comido = {"baya": 0, "seta": 0}

    def _sembrar(self, clase: str) -> None:
        libres = [(x, y) for x in range(self.tam) for y in range(self.tam) if (x, y) != self.pos and all(c["pos"] != (x, y) for c in self.cosas.values())]
        self.n += 1
        self.cosas[f"{clase}_{self.n}"] = {"clase": clase, "pos": self.azar.eleccion(libres)}

    # --- percepción ----------------------------------------------------------
    def observar(self) -> Observacion:
        entidades: List[Entidad] = []
        for cid, c in self.cosas.items():
            d = _dist(self.pos, c["pos"])
            if d <= VISION:
                entidades.append(Entidad(cid, c["clase"], {
                    "proximidad": 1.0 if d <= 1 else 1.0 - d / (VISION + 1),
                    "nutritivo": APARIENCIA.get(c["clase"], 0.0),
                    "recurso": 0.7 if c["clase"] == "piedra" else 0.0,
                }, {"pos": c["pos"]}))
        for l in self.lobos:
            if l["vivo"] and _dist(self.pos, l["pos"]) <= VISION:
                d = _dist(self.pos, l["pos"])
                entidades.append(Entidad(l["id"], "lobo", {"proximidad": 1.0 if d <= 1 else 1.0 - d / (VISION + 1), "peligro": 0.8, "agente": 1.0}))
        for nombre, (dx, dy) in VECINOS.items():
            celda = (self.pos[0] + dx, self.pos[1] + dy)
            if not (0 <= celda[0] < self.tam and 0 <= celda[1] < self.tam):
                continue
            entidades.append(Entidad(f"celda_{celda[0]}_{celda[1]}", "pradera", {
                "lugar": 1.0,
                "proximidad": 1.0,
                "nutritivo": self._promesa(celda),
                "peligro": self._peligro(celda),
                "novedad": 1.0 if celda not in self.pisadas else min(1.0, (self.t - self.pisadas[celda]) / 40.0),
            }, {"pos": celda, "direccion": nombre}))
        return Observacion(ubicacion=f"celda_{self.pos[0]}_{self.pos[1]}", entidades=entidades)

    def _promesa(self, celda: Tuple[int, int]) -> float:
        """Cuánto acerca esta casilla a lo que parece comida (sin saber si lo es)."""
        mejor = 0.0
        for c in self.cosas.values():
            ap = APARIENCIA.get(c["clase"], 0.0)
            d_ahora, d_luego = _dist(self.pos, c["pos"]), _dist(celda, c["pos"])
            if ap and d_ahora <= VISION and d_luego < d_ahora:
                mejor = max(mejor, ap * (1.0 - d_luego / (2 * VISION)))
        return mejor

    def _peligro(self, celda: Tuple[int, int]) -> float:
        peligro_max = 0.0
        for l in self.lobos:
            if not l["vivo"]:
                continue
            d = _dist(celda, l["pos"])
            p = 1.0 if d <= 1 else max(0.0, 0.8 - 0.2 * d)
            peligro_max = max(peligro_max, p)
        return peligro_max

    # --- acción --------------------------------------------------------------
    def verbos(self) -> Set[Verbo]:
        return {Verbo.MOVER, Verbo.COMER, Verbo.ATACAR, Verbo.COGER, Verbo.SOLTAR, Verbo.DORMIR, Verbo.ESPERAR}

    def ejecutar(self, verbo: Verbo, objetivo: str, datos: Dict[str, Any]) -> Efecto:
        self.t += 1
        ef = Efecto(exito=False)
        if verbo == Verbo.MOVER and objetivo.startswith("celda_"):
            x, y = (int(v) for v in objetivo.split("_")[1:])
            if _dist(self.pos, (x, y)) == 1 and 0 <= x < self.tam and 0 <= y < self.tam:
                self.pos = (x, y)
                self.pisadas[self.pos] = self.t
                ef = Efecto(exito=True)
        elif verbo in (Verbo.COMER, Verbo.COGER) and objetivo in self.cosas:
            c = self.cosas[objetivo]
            if _dist(self.pos, c["pos"]) <= 1:
                clase = c["clase"]
                if verbo == Verbo.COMER and clase in APARIENCIA:
                    del self.cosas[objetivo]
                    self.comido[clase] += 1
                    self._sembrar(clase)
                    ef = Efecto(True, {"alimentacion": 20.0} if clase == "baya" else {"vitalidad": -12.0}, obtenido=clase)
                elif verbo == Verbo.COGER and clase == "piedra":
                    del self.cosas[objetivo]
                    ef = Efecto(True, obtenido="piedra")
                else:
                    ef = Efecto(True, obtenido=None)   # comer una piedra: no pasa nada
        elif verbo == Verbo.ATACAR:
            for l in self.lobos:
                if objetivo == l["id"] and l["vivo"]:
                    if _dist(self.pos, l["pos"]) <= 1 and self.azar.probabilidad(0.5):
                        l["pos"] = (0, 0)
                        l["vivo"] = False
                        l["renace"] = self.t + 30
                    ef = Efecto(True)
                    break
        elif verbo in (Verbo.DORMIR, Verbo.ESPERAR, Verbo.SOLTAR):
            ef = Efecto(True)
        self._mover_lobo(ef)
        return ef

    def _mover_lobo(self, ef: Efecto) -> None:
        for l in self.lobos:
            if not l["vivo"]:
                if self.t >= l.get("renace", 0):
                    l["pos"] = (self.tam - 1, 0) if self.azar.probabilidad(0.5) else (0, self.tam - 1)
                    l["vivo"] = True
                continue
            lx, ly = l["pos"]
            if self.azar.probabilidad(0.5):
                dx = (self.pos[0] > lx) - (self.pos[0] < lx)
                dy = (self.pos[1] > ly) - (self.pos[1] < ly)
                nuevo = (lx + dx, ly) if dx and self.azar.probabilidad(0.5) or not dy else (lx, ly + dy)
                if nuevo != self.pos:
                    l["pos"] = nuevo
            if _dist(self.pos, l["pos"]) <= 1:
                ef.delta["vitalidad"] = ef.delta.get("vitalidad", 0.0) - 8.0
                ef.causa = "lobo"

    def registro(self) -> Registro:
        return Registro(estrategias={"S1": Alta(añade=[Defensa()])})

    def puntuacion(self) -> Dict[str, Any]:
        return {"bayas": self.comido["baya"], "setas": self.comido["seta"]}

    def vista(self) -> str:
        filas = []
        for y in range(self.tam):
            fila = ""
            for x in range(self.tam):
                ch = "."
                for c in self.cosas.values():
                    if c["pos"] == (x, y):
                        ch = {"baya": "b", "seta": "s", "piedra": "p"}[c["clase"]]
                for l in self.lobos:
                    if l["vivo"] and l["pos"] == (x, y):
                        ch = "L"
                if self.pos == (x, y):
                    ch = "@"
                fila += ch
            filas.append(fila)
        return "\n".join(filas)

    def escena(self) -> Dict[str, Any]:
        celdas = [["pradera"] * self.tam for _ in range(self.tam)]
        entidades: List[Dict[str, Any]] = []
        for cid in sorted(self.cosas):
            c = self.cosas[cid]
            entidades.append({"clase": c["clase"], "x": c["pos"][0], "y": c["pos"][1], "id": cid})
        for l in self.lobos:
            if l["vivo"]:
                entidades.append({"clase": "lobo", "x": l["pos"][0], "y": l["pos"][1], "id": l["id"]})
        return {
            "tipo": "rejilla",
            "ancho": self.tam,
            "alto": self.tam,
            "celdas": celdas,
            "entidades": entidades,
            "yo": {"x": self.pos[0], "y": self.pos[1]},
            "inventario": {},
            "extra": {"bayas": self.comido["baya"], "setas": self.comido["seta"]},
        }
