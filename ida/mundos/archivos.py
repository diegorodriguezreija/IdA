"""Mundo de archivos: el mundo original de IdA. Las carpetas son biomas y los archivos, lo que hay en ellos.

El tensor de bytes (masa, entropía de Shannon, periodicidad, firma cinética) es **el sensor de
este mundo**. La mente no sabe qué es un archivo: recibe entidades con rasgos.

- Especies comestibles (``Boletus_edulis``, ``brote``...) y tóxicas (``Amanita_phalloides``...)
  tienen **la misma apariencia** (biomasa periódica). Solo comiéndolas se sabe cuál alimenta.
- Depredadores (``depredador_N.exe``, ``escarabajo_N.exe``): firma cinética; muerden si están en
  la misma carpeta y a veces cambian de carpeta.
- Elementos ambientales (``.env``) y mensajes (``.txt``): no se comen; los mensajes se leen.

**Seguridad:** todas las operaciones de disco se comprueban contra la raíz del bioma, un
directorio propio dentro de ``datos/archivos``. Nada fuera de ella se lee, escribe ni borra.
"""

import math
import os
import shutil
from collections import Counter
from typing import Any, Dict, List, Optional, Set

from ida.core.arquitectura import Componente, Contexto
from ida.core.azar import Azar
from ida.core.mundo import Efecto, Entidad, Mundo, Observacion, Perfil
from ida.core.pieza import acotar
from ida.core.vocabulario import Relacion, Verbo

COMESTIBLES = ["Boletus_edulis.brote", "Taraxacum_officinale.brote", "Vaccinium_myrtillus.fruto"]
TOXICOS = ["Amanita_phalloides.brote", "Atropa_belladonna.brote", "Conium_maculatum.brote"]
AMBIENTE = {
    "arroyo_cristalino.env": "ARMONIA FRESCURA FLUJO",
    "musgo_suave.env": "ARMONIA REFUGIO TEXTURA",
    "cristal_resonante.env": "MISTERIO VIBRACION ECO",
    "fango_putrefacto.env": "DISONANCIA HEDOR HUMEDAD",
}
MENSAJES = ["{b} es buen sitio para descansar", "en {b} hay comida", "cuidado: en {b} hay depredadores", "la Amanita parece comida y no lo es"]
BIOMAS = {"Llanura": ["Valle"], "Bosque": ["Cueva"], "Montaña": ["Glaciar"], "Pantano": [], "Ruinas": []}
NUTRIENTE = "NUTRIENTE_PURO_1024_BYTES"
ALCALOIDE = "ALCALOIDE_TOXICO_1024_BYTES"
MORDISCO = 256


def tensor_bytes(nombre: str, datos: bytes) -> Dict[str, float]:
    """La «retina» de este mundo: masa, entropía, periodicidad y firma cinética de los bytes."""
    n = len(datos)
    masa = min(1.0, math.log1p(n) / math.log1p(2048))
    entropia = 0.0
    if n:
        cuenta = Counter(datos)
        entropia = min(1.0, -sum((c / n) * math.log2(c / n) for c in cuenta.values()) / 5.5)
    periodicidad = 0.0
    if n >= 8:
        for p in (4, 8, 16, 25, 26, 27, 28):
            if n >= 2 * p:
                total = min(n - p, 128)
                periodicidad = max(periodicidad, sum(1 for i in range(total) if datos[i] == datos[i + p]) / total)
    cinetico = 0.9 if nombre.endswith(".exe") else 0.0
    return {"masa": masa, "entropia": entropia, "periodicidad": periodicidad, "cinetico": cinetico}


def clase_de(nombre: str) -> str:
    """Etiqueta de clase: el nombre sin extensión ni número final (``depredador_2.exe`` → ``depredador``)."""
    base = nombre.rsplit(".", 1)[0]
    partes = base.split("_")
    if partes[-1].isdigit():
        partes = partes[:-1]
    return "_".join(partes) or base


class MundoArchivos(Mundo):
    nombre = "archivos"
    perfil = Perfil(frecuencia_ms=100.0, amplitud=100, memoria="completa", duerme=True, hogar=True, peso_experiencia=0.2)

    def __init__(self, datos: str = "datos/archivos", **_):
        self.raiz = os.path.abspath(os.path.join(datos, "bioma"))
        self.azar = Azar(0)
        self.actual = self.raiz
        self.visitas: Dict[str, int] = {}
        self.vistos: Dict[str, int] = {}
        self.t = 0
        self.mochila: Optional[Dict[str, Any]] = None
        self.comido: Dict[str, int] = {}
        self.nutritivos = 0
        self.toxicos = 0

    # --- seguridad -----------------------------------------------------------
    def _seguro(self, ruta: str) -> str:
        ruta = os.path.abspath(ruta)
        if os.path.commonpath([ruta, self.raiz]) != self.raiz:
            raise PermissionError(f"Operación fuera del bioma bloqueada: {ruta}")
        return ruta

    def _rel(self, ruta: str) -> str:
        rel = os.path.relpath(ruta, self.raiz).replace("\\", "/")
        return "raiz" if rel == "." else rel

    def _abs(self, rel: str) -> str:
        return self._seguro(self.raiz if rel == "raiz" else os.path.join(self.raiz, rel))

    def _escribir(self, carpeta: str, nombre: str, contenido: str) -> None:
        with open(self._seguro(os.path.join(carpeta, nombre)), "w", encoding="utf-8") as f:
            f.write(contenido)

    # --- ciclo de vida -------------------------------------------------------
    def reiniciar(self, semilla: Optional[int]) -> None:
        self.azar = Azar(semilla)
        if os.path.isdir(self.raiz):
            shutil.rmtree(self._seguro(self.raiz))
        os.makedirs(self.raiz)
        for bioma, hijos in BIOMAS.items():
            ruta = os.path.join(self.raiz, bioma)
            os.makedirs(ruta)
            self._poblar(ruta, bioma)
            for h in hijos:
                sub = os.path.join(ruta, h)
                os.makedirs(sub)
                self._poblar(sub, h)
        self._escribir(self.raiz, "musgo_suave.env", AMBIENTE["musgo_suave.env"])
        self.actual = self.raiz
        self.visitas, self.vistos, self.t, self.mochila, self.comido = {"raiz": 0}, {}, 0, None, {}
        self.nutritivos = 0
        self.toxicos = 0

    def _poblar(self, carpeta: str, bioma: str) -> None:
        az = self.azar
        for j in range(az.eleccion([1, 2, 3])):
            if az.probabilidad(0.3):
                self._escribir(carpeta, az.eleccion(TOXICOS), ALCALOIDE * 32)
            elif az.probabilidad(0.5):
                self._escribir(carpeta, az.eleccion(COMESTIBLES), NUTRIENTE * 32)
            else:
                self._escribir(carpeta, f"brote_{j}.txt", "0101" * 64)
        if az.probabilidad(0.35):
            self._escribir(carpeta, f"depredador_{az.eleccion(range(100))}.exe", "X")
        if az.probabilidad(0.5):
            nombre = az.eleccion(list(AMBIENTE))
            self._escribir(carpeta, nombre, AMBIENTE[nombre])
        if az.probabilidad(0.3):
            self._escribir(carpeta, f"mensaje_{az.eleccion(range(100))}.txt", az.eleccion(MENSAJES).format(b=az.eleccion(list(BIOMAS))))

    # --- percepción ----------------------------------------------------------
    def _archivos(self, carpeta: str) -> List[str]:
        try:
            return sorted(f for f in os.listdir(carpeta) if os.path.isfile(os.path.join(carpeta, f)))
        except OSError:
            return []

    def _leer(self, ruta: str, limite: int = 512) -> bytes:
        with open(self._seguro(ruta), "rb") as f:
            return f.read(limite)

    def _rasgos_archivo(self, ruta: str, nombre: str) -> Dict[str, float]:
        datos = self._leer(ruta)
        t = tensor_bytes(nombre, datos)
        organico = t["periodicidad"] >= 0.55 and t["cinetico"] == 0.0
        simbolico = not organico and t["cinetico"] == 0.0 and nombre.endswith((".txt", ".env"))
        return {
            "proximidad": 1.0,
            "nutritivo": round(t["periodicidad"] * (0.5 + 0.5 * t["masa"]), 3) if organico else 0.0,
            "peligro": t["cinetico"],
            "recurso": 0.5 if simbolico else 0.0,
            "agente": 1.0 if t["cinetico"] else 0.0,
        }

    def _olor(self, carpeta: str) -> Dict[str, float]:
        """Lo que se intuye de una carpeta vecina: cuánta biomasa y cuánta amenaza hay dentro."""
        nombres = self._archivos(carpeta)
        comida = sum(1 for n in nombres if n.endswith((".brote", ".fruto")) or n.startswith("brote_"))
        amenaza = sum(1 for n in nombres if n.endswith(".exe"))
        return {"nutritivo": min(1.0, 0.3 * comida), "peligro": min(1.0, 0.5 * amenaza)}

    def observar(self) -> Observacion:
        entidades: List[Entidad] = []
        for nombre in self._archivos(self.actual):
            ruta = os.path.join(self.actual, nombre)
            eid = self._rel(ruta)
            rasgos = self._rasgos_archivo(ruta, nombre)
            rasgos["novedad"] = 1.0 if eid not in self.vistos else 0.0
            datos: Dict[str, Any] = {}
            if nombre.startswith("mensaje_"):
                datos["mensaje"] = self._leer(ruta, 200).decode("utf-8", "replace")
            entidades.append(Entidad(eid, clase_de(nombre), rasgos, datos))
            self.vistos.setdefault(eid, self.t)
        destinos = [os.path.join(self.actual, d) for d in sorted(os.listdir(self.actual)) if os.path.isdir(os.path.join(self.actual, d))]
        if self.actual != self.raiz:
            destinos.append(os.path.dirname(self.actual))
        for d in destinos:
            rel = self._rel(d)
            olor = self._olor(d)
            ultima = self.visitas.get(rel)
            novedad = 1.0 if ultima is None else min(1.0, (self.t - ultima) / 30.0)
            entidades.append(Entidad(rel, "carpeta", {"lugar": 1.0, "proximidad": 1.0, "novedad": novedad, **olor}))
        return Observacion(ubicacion=self._rel(self.actual), entidades=entidades)

    # --- acción --------------------------------------------------------------
    def verbos(self) -> Set[Verbo]:
        return {Verbo.MOVER, Verbo.COMER, Verbo.ATACAR, Verbo.COGER, Verbo.SOLTAR, Verbo.DORMIR, Verbo.ESPERAR}

    def ejecutar(self, verbo: Verbo, objetivo: str, datos: Dict[str, Any]) -> Efecto:
        self.t += 1
        try:
            ef = self._accion(verbo, objetivo)
        except (OSError, PermissionError) as exc:
            ef = Efecto(exito=False, mensaje=str(exc))
        self._dinamica(ef)
        return ef

    def _accion(self, verbo: Verbo, objetivo: str) -> Efecto:
        if verbo == Verbo.MOVER:
            destino = self._abs(objetivo)
            if os.path.isdir(destino) and os.path.dirname(destino) in (self.actual,) or destino == os.path.dirname(self.actual):
                self.actual = destino
                self.visitas[objetivo] = self.t
                return Efecto(True, {"energia": -0.5})
            return Efecto(False, mensaje="no hay paso")
        if verbo in (Verbo.SOLTAR, Verbo.DORMIR, Verbo.ESPERAR):
            if verbo == Verbo.SOLTAR and self.mochila:
                self._escribir(self.actual, self.mochila["nombre"], self.mochila["contenido"])
                self.mochila = None
            return Efecto(True)
        ruta = self._abs(objetivo)
        if not os.path.isfile(ruta) or os.path.dirname(ruta) != self.actual:
            return Efecto(False, mensaje="no está aquí")
        nombre = os.path.basename(ruta)
        if verbo == Verbo.COMER:
            return self._comer(ruta, nombre)
        if verbo == Verbo.ATACAR:
            if nombre.endswith(".exe") and self.azar.probabilidad(0.6):
                os.remove(self._seguro(ruta))
                return Efecto(True, {"energia": -2.0}, mensaje="amenaza eliminada")
            return Efecto(True, {"energia": -2.0})
        if verbo == Verbo.COGER and self.mochila is None and not nombre.endswith(".exe"):
            with open(ruta, "r", encoding="utf-8", errors="replace") as f:
                self.mochila = {"nombre": nombre, "contenido": f.read()}
            os.remove(self._seguro(ruta))
            return Efecto(True, obtenido=clase_de(nombre))
        return Efecto(False)

    def _comer(self, ruta: str, nombre: str) -> Efecto:
        """Mordisco destructivo de bytes."""
        with open(ruta, "r", encoding="utf-8", errors="replace") as f:
            contenido = f.read()
        bocado, resto = contenido[:MORDISCO], contenido[MORDISCO:]
        if resto:
            self._escribir(os.path.dirname(ruta), nombre, resto)
        else:
            os.remove(self._seguro(ruta))
        clase = clase_de(nombre)
        self.comido[clase] = self.comido.get(clase, 0) + 1
        if ALCALOIDE[:8] in bocado:
            self.toxicos += 1
            return Efecto(True, {"vitalidad": -10.0, "alimentacion": -4.0}, obtenido=clase, mensaje="alcaloide tóxico")
        if NUTRIENTE[:8] in bocado or bocado.startswith("0101"):
            self.nutritivos += 1
            return Efecto(True, {"alimentacion": 8.0}, obtenido=clase)
        return Efecto(True, obtenido=clase, mensaje="no alimenta")

    def _dinamica(self, ef: Efecto) -> None:
        """El mundo sigue: los depredadores muerden y se mueven, y la biomasa rebrota."""
        for nombre in self._archivos(self.actual):
            if nombre.endswith(".exe") and self.azar.probabilidad(0.35):
                ef.delta["vitalidad"] = ef.delta.get("vitalidad", 0.0) - 6.0
                ef.causa = clase_de(nombre)
        if self.azar.probabilidad(0.08):
            carpetas = [d for d, _, _ in os.walk(self.raiz)]
            origen = self.azar.eleccion(carpetas)
            presas = [n for n in self._archivos(origen) if n.endswith(".exe")]
            if presas:
                n = self.azar.eleccion(presas)
                shutil.move(self._seguro(os.path.join(origen, n)), self._seguro(os.path.join(self.azar.eleccion(carpetas), n)))
        if self.t % 25 == 0:
            carpeta = self.azar.eleccion([d for d, _, _ in os.walk(self.raiz)])
            self._escribir(carpeta, f"brote_{self.t}.txt", "0101" * 64)

    def componentes_propios(self) -> Dict[str, list]:
        return {"S1.Reaccionar": [Defensa()], "S3.Reaccionar": [Prudencia()]}

    # --- resultados y vista --------------------------------------------------
    def puntuacion(self) -> Dict[str, Any]:
        return {"comido": dict(self.comido), "nutritivos": self.nutritivos, "toxicos": self.toxicos}

    def vista(self) -> str:
        lineas = []
        for carpeta, subdirs, archivos in os.walk(self.raiz):
            subdirs.sort()
            nivel = 0 if carpeta == self.raiz else self._rel(carpeta).count("/") + 1
            marca = " @" if carpeta == self.actual else ""
            comida = sum(1 for a in archivos if a.endswith((".brote", ".fruto")) or a.startswith("brote_"))
            amenazas = sum(1 for a in archivos if a.endswith(".exe"))
            lineas.append(f"{'  ' * nivel}{os.path.basename(carpeta) if carpeta != self.raiz else 'bioma'}/{marca}  "
                          f"comida:{comida} amenazas:{amenazas} otros:{len(archivos) - comida - amenazas}")
        if self.mochila:
            lineas.append(f"mochila: {self.mochila['nombre']}")
        return "\n".join(lineas)


class Defensa(Componente):
    """Componente propio del mundo de archivos (S1 · Reaccionar).

    Un depredador de la carpeta muerde mientras se esté en ella, y a veces cambia de carpeta:
    huir solo aplaza el problema. Si hay uno al alcance y queda vitalidad, atacarlo (lo elimina
    con un 60 % de probabilidad).
    """

    tipo = "Reflejo"

    def reactiva(self, ctx: Contexto) -> None:
        if ctx.soma.vitalidad < 30.0:
            return
        for p in ctx.onda.ev("Escena").values():
            if p.rasgo("agente") >= 0.5 and p.rasgo("peligro") >= 0.5 and p.rasgo("proximidad") >= 0.9:
                self.proponer(ctx, Verbo.ATACAR, p.id, 1.0, 0.97, f"defensa: atacar al {p.clase}", clase=p.clase)
                return


class Prudencia(Componente):
    """Componente propio del mundo de archivos (S3 · Reaccionar): prudencia alimentaria.

    Aquí comestibles y tóxicos tienen la misma apariencia y cada mordisco tóxico cuesta 10 de
    vitalidad, así que esperar a que el daño esté demostrado sale caro. Además, el «olor» de una
    carpeta no distingue lo comestible de lo tóxico, lo que puede atrapar al individuo yendo y
    viniendo a una carpeta donde solo hay veneno. Por eso:
    - comer algo con indicios de daño (aunque sea una hipótesis) se frena con fuerza;
    - una especie desconocida se frena si a la vista hay otra que ya se sabe que nutre (neofobia);
    - si aquí solo hay comida dañina, se recuerda la carpeta como «mala» durante un tiempo, se
      frena volver a ella y se propone buscar comida en otra parte.
    """

    tipo = "Impulso"
    RECUERDO = 80   # latidos que se evita una carpeta con solo comida dañina

    def __init__(self):
        super().__init__("Prudencia")
        self.malas: Dict[str, int] = {}

    def reactiva(self, ctx: Contexto) -> None:
        mem, ahora = ctx.memoria, ctx.latido
        aqui = ctx.observacion.ubicacion if ctx.observacion else ""
        malas = {c for c, t in self.malas.items() if ahora - t < self.RECUERDO}
        acc = list(ctx.onda.acc("Ejecucion").values())
        frenados = 0
        for c in acc:
            if c.carga["verbo"] == Verbo.MOVER and c.carga["objetivo"] in malas:
                c.arousal, c.confianza = acotar(c.arousal * 0.3), acotar(c.confianza * 0.5)
                c.entradas.append("MUNDO:prudencia (carpeta con solo comida dañina)")
                frenados += 1
        if frenados and frenados == sum(1 for c in acc if c.carga["verbo"] == Verbo.MOVER):
            self._buscar_en_otra_parte(ctx, malas)   # sin alternativa, el freno no basta: proponer otra carpeta
        candidatos = [c for c in acc if c.carga["verbo"] == Verbo.COMER]
        if not candidatos:
            return
        conocidas = {p.clase for p in ctx.onda.ev("Escena").values() if mem.demostrada(p.clase, Relacion.NUTRITIVO, ahora)}
        for c in candidatos:
            clase = c.carga.get("clase", "")
            dano = mem.proposicion(clase, Relacion.PELIGROSO)
            nutre = mem.proposicion(clase, Relacion.NUTRITIVO)
            if dano is not None and dano.confianza >= 0.35:
                c.arousal, c.confianza = acotar(c.arousal * 0.2), acotar(c.confianza * 0.3)
                c.entradas.append("MUNDO:prudencia (indicios de daño)")
            elif nutre is None and conocidas - {clase}:
                c.arousal, c.confianza = acotar(c.arousal * 0.5), acotar(c.confianza * 0.6)
                c.entradas.append("MUNDO:prudencia (desconocida)")
        if all(any("indicios de daño" in e for e in c.entradas) for c in candidatos):
            self.malas[aqui] = ahora
            self._buscar_en_otra_parte(ctx, malas | {aqui})

    def _buscar_en_otra_parte(self, ctx: Contexto, malas) -> None:
        carpetas = [p for p in ctx.onda.ev("Escena").values()
                    if p.rasgo("lugar") >= 0.5 and p.rasgo("peligro") < 0.5 and p.id not in malas]
        if carpetas:
            destino = max(carpetas, key=lambda p: p.rasgo("nutritivo") + 0.5 * p.rasgo("novedad"))
            self.proponer(ctx, Verbo.MOVER, destino.id, 0.6, 0.7, "prudencia: buscar comida en otra parte", clase=destino.clase)
