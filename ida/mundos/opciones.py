"""Opciones declaradas por los mundos (O8): formato de la declaración y validación compartida.

Cada mundo declara sus opciones con ``Mundo.opciones()`` (método de clase: se lee sin crear el mundo ni cargar sus
dependencias). Cada declaración es un diccionario, listo para JSON, con:

- ``nombre``: la clave de ``--opcion nombre=valor`` y del argumento del constructor del mundo;
- ``tipo``: ``"entero"``, ``"real"``, ``"opcion"`` (uno de ``valores``) o ``"booleano"``;
- ``min`` y ``max`` (entero y real, ambos obligatorios) o ``valores`` (opción: lista no vacía de textos);
- ``defecto``: el valor que da más Score de base (O8): el de la medición oficial donde la hay o, si no, el
  comportamiento de hoy. No tiene por qué coincidir con el valor por defecto del constructor, que no se cambia (la
  invariancia lo usa); la antesala y el Vivero lanzan con los declarados (``con_defectos``);
- ``etiqueta`` y ``ayuda``: textos ``{"es": ..., "en": ...}``;
- ``vacia`` (opcional, por defecto ``False``): la opción admite no tener valor (``None``; en la antesala, el campo
  vacío). Solo entonces ``defecto`` puede ser ``None``.

``convertir`` comprueba y convierte los valores que llegan por ``--opcion`` (texto) o por la antesala (JSON). Un mundo
sin declaraciones recibe los valores tal cual (compatibilidad con los mundos que aún no declaran).
"""

from typing import Any, Dict, List, Mapping, Optional

TIPOS = ("entero", "real", "opcion", "booleano")
IDIOMAS = ("es", "en")
CAMPOS = ("nombre", "tipo", "defecto", "etiqueta", "ayuda")
VERDADEROS = ("1", "si", "sí", "true", "yes", "on")
FALSOS = ("0", "no", "false", "off")


class OpcionInvalida(ValueError):
    """Un valor de opción que no cumple su declaración, o una declaración mal formada."""


def opcion(nombre: str, tipo: str, defecto: Any, etiqueta: Mapping[str, str], ayuda: Mapping[str, str], *,
           min: Optional[float] = None, max: Optional[float] = None, valores: Optional[List[str]] = None,
           vacia: bool = False) -> Dict[str, Any]:
    """Una declaración de opción, validada. Atajo para escribir las de cada mundo."""
    d: Dict[str, Any] = {"nombre": nombre, "tipo": tipo, "defecto": defecto, "etiqueta": dict(etiqueta), "ayuda": dict(ayuda)}
    if min is not None:
        d["min"] = min
    if max is not None:
        d["max"] = max
    if valores is not None:
        d["valores"] = list(valores)
    if vacia:
        d["vacia"] = True
    errores = validar_declaracion(d)
    if errores:
        raise OpcionInvalida(f"Declaración de la opción {nombre!r} mal formada: " + "; ".join(errores))
    return d


def _es_numero(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validar_declaracion(d: Any) -> List[str]:
    """Errores de una declaración (lista vacía: válida). Incluye que el ``defecto`` pase su propia validación."""
    if not isinstance(d, dict):
        return [f"se esperaba un objeto, hay {type(d).__name__}"]
    errores = [f"falta {c!r}" for c in CAMPOS if c not in d]
    if errores:
        return errores
    if not isinstance(d["nombre"], str) or not d["nombre"].isidentifier():
        errores.append(f"nombre {d['nombre']!r}: debe ser un identificador")
    if d["tipo"] not in TIPOS:
        return errores + [f"tipo {d['tipo']!r}: debe ser uno de {', '.join(TIPOS)}"]
    for campo in ("etiqueta", "ayuda"):
        textos = d[campo]
        if not isinstance(textos, dict) or any(not isinstance(textos.get(i), str) or not textos[i].strip() for i in IDIOMAS):
            errores.append(f"{campo}: debe tener texto en {' y '.join(IDIOMAS)}")
    if d["tipo"] in ("entero", "real"):
        lo: Any = d.get("min")
        hi: Any = d.get("max")
        if not _es_numero(lo) or not _es_numero(hi):
            errores.append("min y max: obligatorios y numéricos")
        elif d["tipo"] == "entero" and (lo != int(lo) or hi != int(hi)):
            errores.append("min y max: deben ser enteros")
        elif lo > hi:
            errores.append(f"min {lo} mayor que max {hi}")
    if d["tipo"] == "opcion":
        valores = d.get("valores")
        if not isinstance(valores, list) or not valores or not all(isinstance(v, str) for v in valores):
            errores.append("valores: lista no vacía de textos")
        elif len(set(valores)) != len(valores):
            errores.append("valores: repetidos")
    if "vacia" in d and not isinstance(d["vacia"], bool):
        errores.append("vacia: debe ser booleano")
    if not errores:
        try:
            if convertir_valor(d, d["defecto"]) != d["defecto"]:
                errores.append(f"defecto {d['defecto']!r}: no está en su forma convertida")
        except OpcionInvalida as e:
            errores.append(f"defecto: {e}")
    return errores


def convertir_valor(d: Dict[str, Any], valor: Any) -> Any:
    """El valor convertido al tipo de la declaración ``d``, o ``OpcionInvalida`` con un mensaje claro."""
    nombre, tipo = d["nombre"], d["tipo"]
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        if d.get("vacia"):
            return None
        raise OpcionInvalida(f"opción {nombre!r}: necesita un valor")
    if tipo == "booleano":
        if isinstance(valor, bool):
            return valor
        texto = str(valor).strip().lower()
        if texto in VERDADEROS:
            return True
        if texto in FALSOS:
            return False
        raise OpcionInvalida(f"opción {nombre!r}: {valor!r} no es un booleano (usa 1/0, si/no o true/false)")
    if tipo == "opcion":
        texto = str(valor).strip()
        if texto not in d["valores"]:
            raise OpcionInvalida(f"opción {nombre!r}: {valor!r} no es uno de {', '.join(d['valores'])}")
        return texto
    if isinstance(valor, bool):
        raise OpcionInvalida(f"opción {nombre!r}: se esperaba un número, hay un booleano")
    try:
        if tipo == "entero":
            if isinstance(valor, float):
                if valor != int(valor):
                    raise ValueError
                numero: float = int(valor)
            else:
                numero = int(str(valor).strip())
        else:
            numero = float(str(valor).strip()) if not _es_numero(valor) else float(valor)
    except ValueError:
        raise OpcionInvalida(f"opción {nombre!r}: {valor!r} no es un {'entero' if tipo == 'entero' else 'número real'}") from None
    if not d["min"] <= numero <= d["max"]:
        raise OpcionInvalida(f"opción {nombre!r}: {numero} fuera del rango [{d['min']}, {d['max']}]")
    return numero


def convertir(declaraciones: List[Dict[str, Any]], valores: Mapping[str, Any], mundo: str = "") -> Dict[str, Any]:
    """Los ``valores`` dados, comprobados y convertidos según las ``declaraciones``. Solo los dados: no añade los
    defectos (para eso, ``con_defectos``). Un nombre que el mundo no declara es un error; un mundo sin declaraciones
    recibe los valores tal cual."""
    if not declaraciones:
        return dict(valores)
    por_nombre = {d["nombre"]: d for d in declaraciones}
    de = f" de {mundo}" if mundo else ""
    salida: Dict[str, Any] = {}
    for nombre, valor in valores.items():
        if nombre not in por_nombre:
            raise OpcionInvalida(f"opción desconocida{de}: {nombre!r} (conocidas: {', '.join(por_nombre)})")
        try:
            salida[nombre] = convertir_valor(por_nombre[nombre], valor)
        except OpcionInvalida as e:
            raise OpcionInvalida(f"{mundo}: {e}" if mundo else str(e)) from None
    return salida


def con_defectos(declaraciones: List[Dict[str, Any]], valores: Mapping[str, Any], mundo: str = "") -> Dict[str, Any]:
    """Los defectos declarados, sustituidos por los ``valores`` dados (convertidos). Es lo que lanzan la antesala y el
    Vivero (O8): sin tocar nada, la configuración de la medición oficial."""
    salida = {d["nombre"]: d["defecto"] for d in declaraciones}
    salida.update(convertir(declaraciones, valores, mundo))
    return salida


def defectos(declaraciones: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Nombre -> defecto declarado."""
    return {d["nombre"]: d["defecto"] for d in declaraciones}
