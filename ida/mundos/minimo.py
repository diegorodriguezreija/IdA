"""Mundo mínimo: una pradera de 9×9 para tests y como tutorial de cómo se escribe un mundo.

- ``baya``: parece nutritiva y lo es (+20 de alimentación).
- ``seta``: parece nutritiva, pero es tóxica (−12 de vitalidad). Solo la experiencia lo revela.
- ``piedra``: no se come; sirve para algo (se puede coger).
- ``lobo``: se acerca a veces; si está al lado, muerde (−8 de vitalidad). Se le puede atacar.

Los lugares son las cuatro casillas vecinas. Para cada una, el mundo calcula sus rasgos:
``nutritivo`` (cuánto acerca a lo que parece comida), ``peligro`` (cercanía al lobo) y ``novedad``
(si no se ha pisado hace tiempo).
"""

from typing import Any, Dict, List, Optional, Set, Tuple

from ida.core.arquitectura import Componente, Contexto
from ida.core.azar import Azar
from ida.core.mundo import Efecto, Entidad, Mundo, Observacion, Perfil
from ida.core.vocabulario import Verbo

TAM = 9
VISION = 4
APARIENCIA = {"baya": 0.8, "seta": 0.7}     # lo que «promete» a la vista
VECINOS = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "O": (-1, 0)}


def _dist(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class MundoMinimo(Mundo):
    nombre = "minimo"
    perfil = Perfil(frecuencia_ms=100.0, amplitud=100, memoria="completa", duerme=True, hogar=True, peso_experiencia=0.2)

    def __init__(self, **_):
        self.azar = Azar(0)
        self.reiniciar(0)

    def reiniciar(self, semilla: Optional[int]) -> None:
        self.azar = Azar(semilla)
        self.pos = (TAM // 2, TAM // 2)
        self.cosas: Dict[str, Dict[str, Any]] = {}
        self.n = 0
        for _ in range(4):
            self._sembrar("baya")
        for _ in range(3):
            self._sembrar("seta")
        for _ in range(2):
            self._sembrar("piedra")
        self.lobo: Dict[str, Any] = {"pos": (0, 0), "vivo": True}
        self.pisadas: Dict[Tuple[int, int], int] = {}
        self.t = 0
        self.comido = {"baya": 0, "seta": 0}

    def _sembrar(self, clase: str) -> None:
        libres = [(x, y) for x in range(TAM) for y in range(TAM) if (x, y) != self.pos and all(c["pos"] != (x, y) for c in self.cosas.values())]
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
        if self.lobo["vivo"] and _dist(self.pos, self.lobo["pos"]) <= VISION:
            d = _dist(self.pos, self.lobo["pos"])
            entidades.append(Entidad("lobo", "lobo", {"proximidad": 1.0 if d <= 1 else 1.0 - d / (VISION + 1), "peligro": 0.8, "agente": 1.0}))
        for nombre, (dx, dy) in VECINOS.items():
            celda = (self.pos[0] + dx, self.pos[1] + dy)
            if not (0 <= celda[0] < TAM and 0 <= celda[1] < TAM):
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
        if not self.lobo["vivo"]:
            return 0.0
        d = _dist(celda, self.lobo["pos"])
        return 1.0 if d <= 1 else max(0.0, 0.8 - 0.2 * d)

    # --- acción --------------------------------------------------------------
    def verbos(self) -> Set[Verbo]:
        return {Verbo.MOVER, Verbo.COMER, Verbo.ATACAR, Verbo.COGER, Verbo.SOLTAR, Verbo.DORMIR, Verbo.ESPERAR}

    def ejecutar(self, verbo: Verbo, objetivo: str, datos: Dict[str, Any]) -> Efecto:
        self.t += 1
        ef = Efecto(exito=False)
        if verbo == Verbo.MOVER and objetivo.startswith("celda_"):
            x, y = (int(v) for v in objetivo.split("_")[1:])
            if _dist(self.pos, (x, y)) == 1 and 0 <= x < TAM and 0 <= y < TAM:
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
        elif verbo == Verbo.ATACAR and objetivo == "lobo" and self.lobo["vivo"]:
            if _dist(self.pos, self.lobo["pos"]) <= 1 and self.azar.probabilidad(0.5):
                self.lobo = {"pos": (0, 0), "vivo": False, "renace": self.t + 30}
            ef = Efecto(True)
        elif verbo in (Verbo.DORMIR, Verbo.ESPERAR, Verbo.SOLTAR):
            ef = Efecto(True)
        self._mover_lobo(ef)
        return ef

    def _mover_lobo(self, ef: Efecto) -> None:
        if not self.lobo["vivo"]:
            if self.t >= self.lobo.get("renace", 0):
                self.lobo = {"pos": (TAM - 1, 0) if self.azar.probabilidad(0.5) else (0, TAM - 1), "vivo": True}
            return
        lx, ly = self.lobo["pos"]
        if self.azar.probabilidad(0.5):
            dx = (self.pos[0] > lx) - (self.pos[0] < lx)
            dy = (self.pos[1] > ly) - (self.pos[1] < ly)
            nuevo = (lx + dx, ly) if dx and self.azar.probabilidad(0.5) or not dy else (lx, ly + dy)
            if nuevo != self.pos:
                self.lobo["pos"] = nuevo
        if _dist(self.pos, self.lobo["pos"]) <= 1:
            ef.delta["vitalidad"] = ef.delta.get("vitalidad", 0.0) - 8.0
            ef.causa = "lobo"

    def componentes_propios(self) -> Dict[str, list]:
        return {"S1.Reaccionar": [Defensa()]}

    def puntuacion(self) -> Dict[str, Any]:
        return {"bayas": self.comido["baya"], "setas": self.comido["seta"]}

    def vista(self) -> str:
        filas = []
        for y in range(TAM):
            fila = ""
            for x in range(TAM):
                ch = "."
                for c in self.cosas.values():
                    if c["pos"] == (x, y):
                        ch = {"baya": "b", "seta": "s", "piedra": "p"}[c["clase"]]
                if self.lobo["vivo"] and self.lobo["pos"] == (x, y):
                    ch = "L"
                if self.pos == (x, y):
                    ch = "@"
                fila += ch
            filas.append(fila)
        return "\n".join(filas)


class Defensa(Componente):
    """Componente propio del mundo mínimo (S1 · Reaccionar).

    En esta pradera huir del lobo no sirve: persigue. Si está al alcance y queda vitalidad,
    plantarle cara (atacar lo ahuyenta con un 50 % de probabilidad). Con poca vitalidad se deja
    actuar al reflejo genérico de huida.
    """

    tipo = "Reflejo"

    def reactiva(self, ctx: Contexto) -> None:
        if ctx.soma.vitalidad < 30.0:
            return
        for p in ctx.onda.ev("Escena").values():
            if p.rasgo("agente") >= 0.5 and p.rasgo("peligro") >= 0.5 and p.rasgo("proximidad") >= 0.9:
                self.proponer(ctx, Verbo.ATACAR, p.id, 1.0, 0.97, f"defensa: plantar cara al {p.clase}", clase=p.clase)
                return
