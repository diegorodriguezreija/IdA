"""Secciones de la Memoria con dueño (D7): el protocolo ``Seccion``, su registro (leer es libre; escribir, solo el
dueño) y la comprobación del autor de las escrituras delegadas."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple


class Seccion:
    """Protocolo de una sección de la Memoria con dueño (D7): lo que la sección sabe hacer con la memoria común. Todo es
    opcional: por defecto no da legado, no hereda y no lee el manual.

    - ``legado(ahora)``: su parte del legado (claves propias), que ``Memoria.legado`` junta con lo del Core;
    - ``heredar(legado, tasa)``: toma del legado entero lo suyo y devuelve cuántos hechos cargó;
    - ``aplicar_manual(manual)``: toma del manual entero lo suyo (la dotación innata).

    La Memoria fija ``activa`` al registrarla (una memoria apagada no aprende ni hereda). ``orden_legado`` da la
    posición de su parte en ``Memoria.legado`` (la forma del legado no cambia con las secciones)."""

    activa: bool = True
    orden_legado: int = 0

    def legado(self, ahora: int) -> Dict[str, Any]:
        return {}

    def heredar(self, legado: Dict[str, Any], tasa: float = 1.0) -> int:
        return 0

    def aplicar_manual(self, manual: Dict[str, Any]) -> None:
        return None


def admitir(autor: str, admitidos: frozenset, que: str) -> None:
    """Escrituras delegadas (D7): el autor de cada una debe estar entre los que admite su dueño."""
    if autor not in admitidos:
        raise PermissionError(f"'{autor}' no puede escribir {que} en la memoria (admitidos: {sorted(admitidos)})")


class Secciones:
    """Parte de la ``Memoria`` (fachada en ``almacen.py``): el registro de las secciones con dueño. No existen hasta que
    su dueño se monta (``ida/core/montaje.py``), pero el manual y el legado llegan antes: la Memoria guarda ambos, en
    orden, y se los entrega a cada sección al registrarse."""

    _secciones: Dict[str, Tuple[str, Seccion]]
    _diferido: List[Tuple[str, Dict[str, Any], float]]
    heredados: int

    if TYPE_CHECKING:
        @property
        def activa(self) -> bool: ...

    # --- secciones con dueño (D7) ------------------------------------------------
    def registrar_seccion(self, nombre: str, dueño: str, seccion: Seccion) -> None:
        """Registra la sección ``nombre`` de ``dueño`` y le entrega lo diferido: el manual y el legado recibidos antes,
        en el orden en que llegaron. Un nombre repetido es un error."""
        if nombre in self._secciones:
            raise ValueError(f"La sección de memoria '{nombre}' ya está registrada (dueño: {self._secciones[nombre][0]})")
        seccion.activa = self.activa
        self._secciones[nombre] = (dueño, seccion)
        for tipo, datos, tasa in self._diferido:
            if tipo == "manual":
                seccion.aplicar_manual(datos)
            else:
                self.heredados += seccion.heredar(datos, tasa)

    def seccion(self, nombre: str) -> Seccion:
        """Lectura libre de una sección registrada (``KeyError`` si su dueño no está montado)."""
        if nombre not in self._secciones:
            raise KeyError(f"No hay sección de memoria '{nombre}': su dueño no está montado")
        return self._secciones[nombre][1]

    def tiene_seccion(self, nombre: str) -> bool:
        return nombre in self._secciones

    def dueño(self, nombre: str) -> Optional[str]:
        d = self._secciones.get(nombre)
        return d[0] if d is not None else None

    def seccion_propia(self, nombre: str, autor: str) -> Seccion:
        """La sección ``nombre`` para escribir en ella: solo su dueño (``autor``), como en la Onda."""
        dueño, seccion = self._secciones[nombre]
        if autor != dueño:
            raise PermissionError(f"'{autor}' no puede escribir en la sección de memoria '{nombre}' (dueño: {dueño})")
        return seccion

    def _diferir(self, tipo: str, datos: Dict[str, Any], tasa: float = 1.0) -> int:
        """Guarda el manual o el legado para las secciones que aún no se han registrado y lo entrega a las que ya lo
        están. Devuelve los hechos que cargaron las secciones registradas."""
        self._diferido.append((tipo, datos, tasa))
        n = 0
        for _, seccion in self._secciones.values():
            if tipo == "manual":
                seccion.aplicar_manual(datos)
            else:
                n += seccion.heredar(datos, tasa)
        return n
