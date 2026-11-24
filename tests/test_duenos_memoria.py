"""Vigilancia estática de las secciones de la Memoria (D7, A7b): en cada sección solo escribe su dueño, y las escrituras
delegadas solo las hacen los autores que el dueño admite.

Se recorre el código de ``ida/`` con ``ast`` y se buscan:
- llamadas a los métodos que escriben en cada sección (y a ``seccion_propia`` con su nombre), que solo pueden estar en
  los ficheros de su dueño;
- escrituras en los datos de una sección a través de la Memoria (``mem.casillas[p] = ...``, ``ctx.memoria.metas.pop(...)``,
  ``memoria.cierres.add(...)``...): las propiedades ``# A2:`` son de solo lectura, así que no pueden estar en ningún sitio;
- llamadas a las escrituras delegadas (``ver_clase``, ``recordar_lugar``, ``olvidar_donde``, ``fijar_lectura``), que
  solo pueden estar en los ficheros de su dueño o de sus autores admitidos.
"""

import ast
import pathlib
from typing import Dict, FrozenSet, List, Set, Tuple

import pytest

from ida.nucleo.memoria import Memoria

RAIZ = pathlib.Path(__file__).resolve().parent.parent
IDA = RAIZ / "ida"
FICHEROS = sorted(IDA.rglob("*.py"))

CUERPO = frozenset(str(p.relative_to(RAIZ).as_posix()) for p in (IDA / "cuerpos" / "cuadricula").glob("*.py"))

# Sección -> (ficheros del dueño, métodos que escriben en ella, datos de la sección)
SECCIONES: Dict[str, Tuple[FrozenSet[str], FrozenSet[str], FrozenSet[str]]] = {
    "peligros": (frozenset({"ida/s1/sentir/amenaza.py"}), frozenset({"heredar_peligros"}), frozenset({"peligros"})),
    "satisface": (frozenset({"ida/s1/interpretar/apetencia.py"}), frozenset({"aprender_satisface", "actualizar_linea_base"}),
                  frozenset({"satisface", "linea_base", "n_base"})),
    "cuadricula": (CUERPO, frozenset({"ver_casillas", "aprender_transformacion", "aprender_cuerpo"}),
                   frozenset({"casillas", "version_mapa", "paso_libre", "paso_bloqueado", "peligro_sobre",
                              "transformaciones", "cuerpo", "cierres", "yo_previo"})),
    "requisitos": (frozenset({"ida/s3/interpretar/requisito.py"}), frozenset({"aprender_requisito", "registrar_meta"}),
                   frozenset({"requisitos", "intentos", "claves_inventario", "metas", "fallos_seguidos"})),
}

# Escritura delegada -> ficheros del dueño y de los autores admitidos (D7, tabla de escrituras delegadas)
DELEGADAS: Dict[str, FrozenSet[str]] = {
    "ver_clase": frozenset({"ida/nucleo/memoria.py", "ida/core/latido.py"}),                 # Core (plasticidad)
    "recordar_lugar": frozenset({"ida/nucleo/memoria.py", "ida/core/latido.py",
                                 "ida/mundos/crafter/s1/interpretar/recinto.py"}),          # Core, autor Recinto
    "olvidar_donde": frozenset({"ida/nucleo/memoria.py", "ida/s2/reaccionar/estrategias/recordar_comida.py"}),             # Core, autor RecordarComida
    "fijar_lectura": frozenset({"ida/nucleo/memoria.py", "ida/s3/reaccionar/estrategias/estudio.py"}),             # autor Estudio
}

MUTADORES = {"add", "discard", "update", "clear", "pop", "popitem", "setdefault", "append", "extend", "remove", "insert"}
BASES_MEMORIA = {"mem", "memoria"}   # ``mem``, ``memoria``, ``ctx.memoria``, ``self.memoria``, ``o.memoria``, ``self.mem``


def _es_memoria(nodo: ast.AST) -> bool:
    return (isinstance(nodo, ast.Name) and nodo.id in BASES_MEMORIA) or (isinstance(nodo, ast.Attribute) and nodo.attr in BASES_MEMORIA)


def _dato_de_memoria(nodo: ast.AST) -> str:
    """Si ``nodo`` es ``<memoria>.<dato>`` (o un subíndice suyo), el nombre del dato; si no, ''."""
    while isinstance(nodo, ast.Subscript):
        nodo = nodo.value
    if isinstance(nodo, ast.Attribute) and _es_memoria(nodo.value):
        return nodo.attr
    return ""


def _rel(ruta: pathlib.Path) -> str:
    return ruta.relative_to(RAIZ).as_posix()


def _escrituras(ruta: pathlib.Path) -> List[Tuple[int, str, str]]:
    """(línea, tipo, nombre) de cada escritura candidata del fichero."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    out: List[Tuple[int, str, str]] = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
            nombre = nodo.func.attr
            out.append((nodo.lineno, "llamada", nombre))
            if nombre == "seccion_propia" and nodo.args and isinstance(nodo.args[0], ast.Constant):
                out.append((nodo.lineno, "seccion_propia", str(nodo.args[0].value)))
            if nombre == "aprender" and isinstance(nodo.func.value, (ast.Name, ast.Attribute)):
                base = nodo.func.value.id if isinstance(nodo.func.value, ast.Name) else nodo.func.value.attr
                if base == "peligros":
                    out.append((nodo.lineno, "llamada", "peligros.aprender"))
            if nombre in MUTADORES and (dato := _dato_de_memoria(nodo.func.value)):
                out.append((nodo.lineno, "dato", dato))
        elif isinstance(nodo, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            objetivos = nodo.targets if isinstance(nodo, ast.Assign) else [nodo.target]
            for t in objetivos:
                if dato := _dato_de_memoria(t):
                    out.append((nodo.lineno, "dato", dato))
        elif isinstance(nodo, ast.Delete):
            for t in nodo.targets:
                if dato := _dato_de_memoria(t):
                    out.append((nodo.lineno, "dato", dato))
    return out


@pytest.mark.parametrize("ruta", FICHEROS, ids=_rel)
def test_solo_el_dueño_escribe_en_su_seccion(ruta: pathlib.Path) -> None:
    rel = _rel(ruta)
    for linea, tipo, nombre in _escrituras(ruta):
        for seccion, (dueño, metodos, datos) in SECCIONES.items():
            if tipo == "llamada" and (nombre in metodos or (seccion == "peligros" and nombre == "peligros.aprender")):
                assert rel in dueño, f"{rel}:{linea} escribe en la sección «{seccion}» ({nombre}) sin ser su dueño"
            if tipo == "seccion_propia" and nombre == seccion:
                assert rel in dueño, f"{rel}:{linea} pide la sección «{seccion}» para escribir sin ser su dueño"
            if tipo == "dato" and nombre in datos:
                pytest.fail(f"{rel}:{linea} escribe en {nombre} (sección «{seccion}») a través de la Memoria (A2: solo lectura)")


@pytest.mark.parametrize("ruta", FICHEROS, ids=_rel)
def test_escrituras_delegadas_solo_de_autores_admitidos(ruta: pathlib.Path) -> None:
    rel = _rel(ruta)
    for linea, tipo, nombre in _escrituras(ruta):
        if tipo == "llamada" and nombre in DELEGADAS:
            assert rel in DELEGADAS[nombre], f"{rel}:{linea} llama a {nombre} sin ser su dueño ni un autor admitido"
        if tipo == "dato" and nombre in {"lectura_activa", "ultimo_fin_lectura", "_lectura_activa", "_ultimo_fin_lectura"}:
            pytest.fail(f"{rel}:{linea} escribe {nombre} sin pasar por Memoria.fijar_lectura")


def test_los_dueños_comprueban_el_autor() -> None:
    mem = Memoria()
    mem.recordar_lugar("casa", 1.0)                       # el Core
    mem.recordar_lugar("casa", 1.0, autor="Recinto")
    mem.olvidar_donde("baya", autor="RecordarComida")
    mem.fijar_lectura(None, "Estudio", fin=3)
    assert mem.ultimo_fin_lectura == 3
    for llamada in (lambda: mem.recordar_lugar("casa", 1.0, autor="Proteger"),
                    lambda: mem.olvidar_donde("baya", autor="Alimentarse"),
                    lambda: mem.fijar_lectura(None, "Proteger")):
        with pytest.raises(PermissionError):
            llamada()


def test_la_tabla_de_secciones_cubre_las_propiedades_a2() -> None:
    """Cada dato de sección que la Memoria expone con el nombre de antes (A2) está vigilado por este test."""
    vigilados: Set[str] = set().union(*(datos for _, _, datos in SECCIONES.values()))
    a2 = {n for n, v in vars(Memoria).items() if isinstance(v, property)} - {"activa", "lectura_activa", "ultimo_fin_lectura"}
    assert a2 <= vigilados, sorted(a2 - vigilados)
