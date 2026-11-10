"""Snake: IdA juega en la web real playsnake.org, controlando un navegador con Playwright.

Necesita conexión a internet y Chromium (``python -m playwright install chromium``). Mundo de
tiempo real: la serpiente avanza aunque IdA no haya decidido (marcapasos del latido).

Traducción al vocabulario común:
- ``comida``: entidad nutritiva; ``proximidad`` según la distancia. COMER cuando está al lado =
  girar hacia ella.
- Lugares: las casillas vecinas libres; ``pared`` y ``cuerpo`` (peligro 1) solo si no queda otra. En las
  casillas libres, el sensor estima el peligro de encerrarse: cuenta el espacio libre al que se
  llega desde ella (relleno por inundación) y lo compara con la longitud de la serpiente.
  ``nutritivo`` indica cuánto acerca a la comida.
- Al morir, la causa (``pared`` o ``cuerpo``) se calcula con la última posición y dirección
  **antes** de que la web reinicie la partida.

Opciones: ``--opcion dificultad=0|1|2`` (babosa, gusano, pitón), ``--opcion ventana=1`` y
``--opcion ritmo=MS`` (periodo del latido, 60 por defecto: a ritmo pitón, 100 llega tarde).
"""

from collections import deque
from dataclasses import replace
from typing import Any, Dict, List, Optional, Set, Tuple

from ida.core.mundo import Efecto, Entidad, Mundo, Observacion, Perfil
from ida.core.vocabulario import Verbo

URL = "https://playsnake.org/"
ANCHO, ALTO = 21, 15
DIRECCIONES = {"N": (0, -1, "ArrowUp"), "S": (0, 1, "ArrowDown"), "E": (1, 0, "ArrowRight"), "O": (-1, 0, "ArrowLeft")}
DIFICULTADES = {"0": 0, "babosa": 0, "slug": 0, "1": 1, "gusano": 1, "worm": 1, "2": 2, "piton": 2, "pitón": 2, "python": 2}

JS_ESTADO = """() => {
  const game = document.querySelector('.game');
  const cells = Array.from(document.querySelectorAll('.game .board .cell'));
  const cuerpo = []; let comida = null;
  cells.forEach((c, i) => { const p = [i % 21, Math.floor(i / 21)];
    if (c.classList.contains('snake')) cuerpo.push(p);
    if (c.classList.contains('food')) comida = p; });
  const s = document.querySelector('.info .score');
  return {clase: game ? game.className : '', cuerpo, comida, puntos: s ? (parseInt(s.textContent, 10) || 0) : 0};
}"""

Celda = Tuple[int, int]


def espacio_libre(inicio: Celda, ocupadas: Set[Celda], limite: int = 80) -> int:
    """Casillas libres alcanzables desde ``inicio`` (relleno por inundación acotado)."""
    if inicio in ocupadas or not (0 <= inicio[0] < ANCHO and 0 <= inicio[1] < ALTO):
        return 0
    vistas, cola = {inicio}, deque([inicio])
    while cola and len(vistas) < limite:
        x, y = cola.popleft()
        for dx, dy, _ in DIRECCIONES.values():
            n = (x + dx, y + dy)
            if n not in vistas and n not in ocupadas and 0 <= n[0] < ANCHO and 0 <= n[1] < ALTO:
                vistas.add(n)
                cola.append(n)
    return len(vistas)


class MundoSnake(Mundo):
    nombre = "snake"
    perfil = Perfil(tiempo_real=True, frecuencia_ms=60.0, amplitud=80, memoria="ligera", duerme=False, hogar=False, peso_experiencia=0.15)

    def __init__(self, dificultad: Any = 0, ventana: Any = 0, ritmo: Any = 60, **_):
        self.dificultad = DIFICULTADES.get(str(dificultad).lower(), 0)
        self.perfil = replace(MundoSnake.perfil, frecuencia_ms=float(ritmo))
        self.ventana = str(ventana) in ("1", "si", "sí", "true")
        self._pw: Any = None
        self._navegador: Any = None
        self._pagina: Any = None
        self._reset_estado()

    def _reset_estado(self) -> None:
        self.cuerpo: List[Celda] = [(10, 2), (10, 1), (10, 0)]
        self.cabeza: Celda = (10, 2)
        self.comida: Optional[Celda] = None
        self.puntos = 0
        self.max_puntos = 0
        self.direccion = "S"
        self.muerta = False
        self.causa_muerte: Optional[str] = None
        self.muerte_notificada = False

    # --- navegador -----------------------------------------------------------
    def _conectar(self) -> None:
        if self._pagina is not None:
            return
        from playwright.sync_api import sync_playwright   # dependencia solo de este mundo
        self._pw = sync_playwright().start()
        self._navegador = self._pw.chromium.launch(headless=not self.ventana,
                                                   args=["--disable-background-timer-throttling", "--disable-renderer-backgrounding"])
        self._pagina = self._navegador.new_page()

    def reiniciar(self, semilla: Optional[int]) -> None:
        """La web no admite semilla: cada partida es distinta."""
        self._conectar()
        p = self._pagina
        p.goto(URL, timeout=20000)
        p.wait_for_timeout(500)
        consentimiento = p.query_selector(".fc-cta-consent")
        if consentimiento and consentimiento.is_visible():
            consentimiento.click()
            p.wait_for_timeout(300)
        selector = f".game nav .level[data-level='{self.dificultad}']"
        p.wait_for_selector(selector, timeout=8000)
        p.click(selector)
        p.wait_for_timeout(1200)
        self._reset_estado()

    def cerrar(self) -> None:
        for cosa in (self._pagina, self._navegador):
            try:
                if cosa is not None:
                    cosa.close()
            except Exception:
                pass
        if self._pw is not None:
            self._pw.stop()
        self._pw = self._navegador = self._pagina = None

    # --- percepción ----------------------------------------------------------
    def _leer(self) -> None:
        d = self._pagina.evaluate(JS_ESTADO)
        cuerpo = [tuple(c) for c in d["cuerpo"]]
        reinicio = (self.puntos > 0 and d["puntos"] == 0) or (len(self.cuerpo) > 5 and len(cuerpo) <= 3)
        if not self.muerta and ("ended" in d["clase"] or "over" in d["clase"] or reinicio):
            self.muerta = True
            self.causa_muerte = self._causa()
            return                       # no se actualiza la posición: la web ya ha reiniciado
        if cuerpo:
            nuevas = [c for c in cuerpo if c not in set(self.cuerpo)]
            if nuevas:
                nueva = nuevas[0]
                dx, dy = nueva[0] - self.cabeza[0], nueva[1] - self.cabeza[1]
                for k, (ddx, ddy, _) in DIRECCIONES.items():
                    if (ddx, ddy) == (dx, dy):
                        self.direccion = k
                self.cabeza = nueva
            elif self.cabeza not in cuerpo:
                self.cabeza = cuerpo[0]
            self.cuerpo = cuerpo
        self.comida = tuple(d["comida"]) if d["comida"] else None
        self.puntos = d["puntos"]
        self.max_puntos = max(self.max_puntos, self.puntos)

    def _causa(self) -> str:
        """Proyecta la dirección hasta 3 casillas: a ritmo alto la serpiente avanza varias entre dos lecturas."""
        dx, dy, _ = DIRECCIONES[self.direccion]
        cuerpo = set(self.cuerpo[:-1])
        for k in range(1, 4):
            sig = (self.cabeza[0] + k * dx, self.cabeza[1] + k * dy)
            if not (0 <= sig[0] < ANCHO and 0 <= sig[1] < ALTO):
                return "pared"
            if sig in cuerpo:
                return "cuerpo"
        return "desconocida"

    def observar(self) -> Observacion:
        self._leer()
        if self.muerta:
            return Observacion(ubicacion="fin", entidades=[], mensaje=f"muerte: {self.causa_muerte}")
        entidades: List[Entidad] = []
        hx, hy = self.cabeza
        if self.comida:
            d = abs(self.comida[0] - hx) + abs(self.comida[1] - hy)
            entidades.append(Entidad("comida", "comida", {"nutritivo": 1.0, "proximidad": 1.0 if d <= 1 else max(0.0, 1.0 - d / (ANCHO + ALTO))},
                                     {"pos": self.comida}))
        ocupadas = set(self.cuerpo[:-1])          # la cola se libera al avanzar
        longitud = len(self.cuerpo)
        mortales = []
        for k, (dx, dy, _) in DIRECCIONES.items():
            c = (hx + dx, hy + dy)
            fuera = not (0 <= c[0] < ANCHO and 0 <= c[1] < ALTO)
            if fuera or c in ocupadas:
                mortales.append(Entidad(f"dir_{k}", "pared" if fuera else "cuerpo", {"lugar": 1.0, "proximidad": 1.0, "peligro": 1.0}, {"dir": k}))
                continue
            libre = espacio_libre(c, ocupadas)
            peligro = max(0.0, min(0.9, 1.0 - libre / (2.0 * longitud + 4)))
            nutritivo = 0.0
            if self.comida:
                antes = abs(self.comida[0] - hx) + abs(self.comida[1] - hy)
                despues = abs(self.comida[0] - c[0]) + abs(self.comida[1] - c[1])
                nutritivo = 1.0 - despues / (ANCHO + ALTO) if despues < antes else 0.05
            entidades.append(Entidad(f"dir_{k}", "casilla", {"lugar": 1.0, "proximidad": 1.0, "peligro": peligro, "nutritivo": nutritivo}, {"dir": k}))
        if not any(e.clase == "casilla" for e in entidades):
            entidades.extend(mortales)   # las casillas mortales solo se ofrecen si no queda ninguna segura
        return Observacion(ubicacion=f"{hx}_{hy}", entidades=entidades)

    # --- acción --------------------------------------------------------------
    def verbos(self) -> Set[Verbo]:
        return {Verbo.MOVER, Verbo.COMER, Verbo.ESPERAR}

    def ejecutar(self, verbo: Verbo, objetivo: str, datos: Dict[str, Any]) -> Efecto:
        if self.muerta:
            self.muerte_notificada = True
            return Efecto(exito=False, delta={"vitalidad": -100.0}, causa=self.causa_muerte, muerte=True, mensaje=f"muerte: {self.causa_muerte}")
        direccion = None
        if verbo == Verbo.MOVER and objetivo.startswith("dir_"):
            direccion = objetivo[4:]
        elif verbo == Verbo.COMER and self.comida:
            dx, dy = self.comida[0] - self.cabeza[0], self.comida[1] - self.cabeza[1]
            direccion = next((k for k, (a, b, _) in DIRECCIONES.items() if (a, b) == (dx, dy)), None)
        antes, cabeza_antes, comida_antes = self.puntos, self.cabeza, self.comida
        if direccion:
            self._pagina.keyboard.press(DIRECCIONES[direccion][2])
            self.direccion = direccion
        self._pagina.wait_for_timeout(15)
        self._leer()
        if verbo == Verbo.COMER:
            # Tiempo real: el efecto de comer llega cuando la cabeza entra en la casilla de la comida.
            for _ in range(15):
                if self.muerta or self.puntos > antes or self.cabeza != cabeza_antes:
                    break
                self._pagina.wait_for_timeout(20)
                self._leer()
        if self.muerta:
            self.muerte_notificada = True
            return Efecto(exito=False, delta={"vitalidad": -100.0}, causa=self.causa_muerte, muerte=True, mensaje=f"muerte: {self.causa_muerte}")
        if self.puntos > antes or (verbo == Verbo.COMER and self.cabeza == comida_antes):
            return Efecto(True, {"alimentacion": 25.0}, obtenido="comida")
        if verbo == Verbo.COMER:
            return Efecto(False, mensaje="no alcanzó la comida")   # p. ej. giro de 180° imposible
        return Efecto(True)

    def terminado(self) -> bool:
        return self.muerte_notificada

    def puntuacion(self) -> Dict[str, Any]:
        return {"puntos": self.max_puntos, "longitud": len(self.cuerpo), "causa_muerte": self.causa_muerte}

    def vista(self) -> str:
        cuerpo = set(self.cuerpo)
        filas = []
        for y in range(ALTO):
            fila = ""
            for x in range(ANCHO):
                fila += "@" if (x, y) == self.cabeza else ("o" if (x, y) in cuerpo else ("*" if (x, y) == self.comida else "."))
            filas.append(fila)
        return "\n".join(filas) + f"\npuntos: {self.puntos}"
