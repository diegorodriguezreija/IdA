"""Arquetipo (carácter de cada individuo), mutación entre generaciones y legado del linaje.

La herencia respeta una barrera: al linaje solo pasa lo demostrado y la memoria colectiva
agregada de S1, nunca los episodios vividos. No hay transmisión entre linajes distintos.
"""

import json
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from ida.core.azar import Azar
from ida.core.pieza import acotar

RASGOS_CARACTER = ("apertura", "responsabilidad", "neuroticismo", "extraversion", "umbral_miedo")


@dataclass
class Arquetipo:
    nombre: str = "IdA"
    linaje: str = "Alfa"
    generacion: int = 1
    padre: Optional[str] = None
    apertura: float = 0.5         # curiosidad, atracción por lo nuevo
    responsabilidad: float = 0.5  # prudencia, peso de lo aprendido
    neuroticismo: float = 0.5     # sensibilidad al peligro
    extraversion: float = 0.5     # atracción por otros agentes
    umbral_miedo: float = 0.6     # peligro a partir del cual S1 reacciona con reflejos

    @property
    def id(self) -> str:
        return f"{self.linaje}_G{self.generacion}"

    @classmethod
    def nuevo(cls, azar: Azar, linaje: str = "Alfa", nombre: str = "IdA") -> "Arquetipo":
        valores: Dict[str, Any] = {r: round(azar.uniforme(0.3, 0.7), 3) for r in RASGOS_CARACTER}
        valores["umbral_miedo"] = round(azar.uniforme(0.45, 0.75), 3)
        return cls(nombre=nombre, linaje=linaje, **valores)

    def mutar(self, azar: Azar, vivencia: Optional[Dict[str, float]] = None) -> "Arquetipo":
        """Hijo con rasgos propios: los del padre más ruido, y una pequeña marca de lo que vivió el padre."""
        viv = vivencia or {}
        marcas = {
            "neuroticismo": 0.04 * viv.get("fraccion_miedo", 0.0) - 0.02 * viv.get("fraccion_calma", 0.0),
            "apertura": 0.03 * viv.get("fraccion_calma", 0.0) - 0.02 * viv.get("fraccion_miedo", 0.0),
            "responsabilidad": 0.03 * viv.get("fraccion_hambre", 0.0),
        }
        hijo = {}
        for r in RASGOS_CARACTER:
            valor = getattr(self, r) + azar.ruido(0.08) + marcas.get(r, 0.0)
            hijo[r] = round(acotar(valor, 0.15, 0.85), 3)
        return Arquetipo(nombre=self.nombre, linaje=self.linaje, generacion=self.generacion + 1, padre=self.id, **hijo)

    def texto(self) -> str:
        return " ".join(f"{r[:4]}={getattr(self, r):.2f}" for r in RASGOS_CARACTER)


class Linaje:
    """Persistencia del linaje en un JSON: historial de generaciones, último arquetipo y legado."""

    def __init__(self, ruta: str):
        self.ruta = ruta
        self.datos: Dict[str, Any] = {"generaciones": [], "arquetipo": None, "legado": {}}
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                self.datos = json.load(f)

    @property
    def generaciones(self) -> List[Dict[str, Any]]:
        return self.datos["generaciones"]

    def ultimo_arquetipo(self) -> Optional[Arquetipo]:
        a = self.datos.get("arquetipo")
        return Arquetipo(**a) if a else None

    def legado(self) -> Dict[str, Any]:
        return self.datos.get("legado", {})

    def registrar(self, arquetipo: Arquetipo, resumen: Dict[str, Any], legado: Dict[str, Any]) -> None:
        self.datos["generaciones"].append({"individuo": arquetipo.id, "arquetipo": asdict(arquetipo), **resumen})
        self.datos["arquetipo"] = asdict(arquetipo)
        self.datos["legado"] = legado
        os.makedirs(os.path.dirname(self.ruta) or ".", exist_ok=True)
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump(self.datos, f, ensure_ascii=False, indent=2)
