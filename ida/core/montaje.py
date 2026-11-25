"""Montaje del Organismo al nacer: lo que ocurre una sola vez, no en cada latido (C3).

En este orden, el mismo que tenía ``Organismo.__init__``:
1. Core: verbos del mundo, Regulación (D12), Tribunal, Sentir y Actuar con su capa motora (D9).
2. Opcionales (D3, D15): se quitan los generales con ``opcional`` que el mundo no nombra.
3. Cuerpo (D10): sus Componentes, antes que los del mundo, con las reglas de ``añade`` y la fase de plasticidad
   «cuerpo» (D6).
4. Componentes del registro del mundo (D3): ``sustituye`` y ``añade``, por destino y en el orden declarado.
5. Estrategias del registro, por sistema.
6. Preatención (D5) y nombres de todo lo montado.
7. Comprobaciones: espacio (C7a) y fases de plasticidad (D6).
8. Secciones de la Memoria de sus dueños (D7).

El montaje conoce los Componentes del Core, así que vive en ``ida/core`` y no en ``ida/nucleo`` (D2). Son funciones
sobre el Organismo que nace; no importa ``ida.core.latido`` al ejecutarse (sin ciclos).
"""

from typing import TYPE_CHECKING, Any, List, Optional, Set, Tuple

from ida.core.actuar.actuador import Actuador
from ida.core.actuar.tribunal import Tribunal
from ida.core.regulacion import Regulacion
from ida.core.sentir.ambiente import Ambiente
from ida.core.sentir.exterocepcion import Exterocepcion
from ida.core.sentir.interocepcion import Interocepcion
from ida.core.sentir.propiocepcion import Propiocepcion
from ida.nucleo.arquitectura import FASES_PLASTICIDAD, Componente, Modulo, Preatencion, Sistema
from ida.nucleo.mundo import Cuerpo
from ida.nucleo.vocabulario import Verbo

if TYPE_CHECKING:
    from ida.core.latido import Organismo

DESTINOS_VALIDOS_COMPONENTES = {"CORE.Sentir"} | {
    f"{sis}.{etapa}"
    for sis in ("S1", "S2", "S3")
    for etapa in ("Sentir", "Interpretar", "Reaccionar", "Actuar")
}
DESTINOS_VALIDOS_CUERPO = DESTINOS_VALIDOS_COMPONENTES | {"CORE.Actuar"}
SISTEMAS_VALIDOS_ESTRATEGIAS = {"S1", "S2", "S3"}


def montar(org: "Organismo") -> None:
    """Monta el Organismo que nace según el registro de su mundo (D3). Deja en ``org``: ``verbos``, ``regulacion``,
    ``tribunal``, ``sentir``, ``actuar``, ``cuerpo``, ``componentes_cuerpo``, ``preatencion`` y ``registrados``, y
    registra en ``org.memoria`` las secciones de sus dueños."""
    mundo = org.mundo
    verbos_mundo = sorted(set(mundo.verbos()), key=lambda v: v.value)
    org.verbos = set(verbos_mundo)
    if Verbo.ESPERAR in org.verbos:
        org.verbos.add(Verbo.LEER)

    org.regulacion = Regulacion()       # CORE.Regulacion (D12): fija frecuencia, amplitud y potencia de cada latido
    org.regulacion.sistema = "CORE"
    org.tribunal = Tribunal()
    org.sentir = Modulo("Sentir", [Interocepcion(), Propiocepcion(), Exterocepcion(), Ambiente()], exento=True)
    # Montaje declarado por el registro del mundo (D3)
    reg = mundo.registro()
    # Capa motora (D9): con primitivas del mundo y Motor del cuerpo, el Actuador ejecuta primitivas
    motor = reg.cuerpo.motor() if reg.cuerpo is not None else None
    disponibles = mundo.primitivas() if motor is not None else None
    if disponibles is None:
        motor = None
    actuadores: List[Componente] = [Actuador(v, mundo.ejecutar, motor, mundo.ejecutar_primitivas if motor else None, disponibles)
                                    for v in verbos_mundo]
    org.actuar = Modulo("Actuar", [org.tribunal, *actuadores], exento=True)
    for c in org.sentir.componentes + org.actuar.componentes:
        c.sistema = "CORE"

    org.cuerpo = reg.cuerpo

    # Opcionales (D3, D15): los generales con ``opcional`` que el mundo no nombra se quitan en su sitio, antes que nada
    _montar_opcionales(org, reg.opcionales)
    _montar_cuerpo(org, reg.cuerpo)
    _montar_componentes(org, reg.componentes)
    _montar_estrategias(org, reg.estrategias)

    # Preatención (D5): los preatentivos de S1 · Sentir, en un módulo exento que corre tras Core · Sentir. Los
    # integradores (``Saliencia``) corren siempre los últimos, sea cual sea el orden de registro (orden estable)
    org.preatencion = Preatencion(sorted((c for s in org.sistemas for c in s.preatencion), key=lambda c: c.integrador))

    # Conjunto de nombres de clase de todo lo montado (Componentes Core, preatención y S1-S3, y definiciones de catálogos)
    org.registrados = {
        c.__class__.__name__ for c in org.sentir.componentes + org.actuar.componentes + org.preatencion.componentes
    } | {
        c.__class__.__name__ for s in org.sistemas for m in s.modulos for c in m.componentes
    } | {
        d.__class__.__name__
        for s in org.sistemas
        for c in s.componentes()
        if c.tipo == "Estrategia" and hasattr(c, "catalogo")
        for d in c.catalogo.todas()
    }

    _comprobar_espacio(org)
    _comprobar_plasticidad(org)
    _registrar_secciones(org, reg.cuerpo)


def sistema_por_nombre(sistemas: List[Sistema], nombre: str) -> Sistema:
    for s in sistemas:
        if s.nombre == nombre:
            return s
    raise KeyError(f"Sistema desconocido: {nombre}")


def _montar_opcionales(org: "Organismo", nombres: List[str]) -> None:
    """Quita los generales opcionales (Componentes de los módulos, preatentivos y definiciones de los catálogos) cuya
    clase no está en ``nombres``, conservando el orden relativo de lo demás. Un nombre que no corresponde a ningún
    opcional del montaje general es un error (D3)."""
    pedidos = set(nombres)
    vistos: Set[str] = set()
    for s in org.sistemas:
        listas = [m.componentes for m in s.modulos] + [s.preatencion]
        for lista in listas:
            vistos |= {c.__class__.__name__ for c in lista if c.opcional}
            lista[:] = [c for c in lista if not c.opcional or c.__class__.__name__ in pedidos]
        catalogos = {id(c.catalogo): c.catalogo for c in s.componentes() if c.tipo == "Estrategia" and hasattr(c, "catalogo")}
        for catalogo in catalogos.values():
            for d in catalogo.todas():
                if d.opcional:
                    vistos.add(d.__class__.__name__)
                    if d.__class__.__name__ not in pedidos:
                        catalogo.quitar(d.nombre)
    desconocidos = sorted(pedidos - vistos)
    if desconocidos:
        raise ValueError(f"Opcionales desconocidos en el registro de {org.mundo.nombre}: {desconocidos}. "
                         f"Opcionales del montaje general: {sorted(vistos)}")


def _montar_cuerpo(org: "Organismo", cuerpo: Optional[Cuerpo]) -> None:
    """Cuerpo (D10): sus Componentes, antes que los del mundo, con las reglas de ``añade``."""
    org.componentes_cuerpo = []   # en orden de montaje; aprenden en la fase «cuerpo» (D6)
    if cuerpo is None:
        return
    for destino, comps in cuerpo.componentes().items():
        if destino not in DESTINOS_VALIDOS_CUERPO:
            raise ValueError(
                f"Destino no válido para un Componente del cuerpo '{cuerpo.nombre}': '{destino}'. "
                f"Válidos: {sorted(DESTINOS_VALIDOS_CUERPO)}"
            )
        modulo, preatencion, sistema_asignar = _destino(org, destino)
        for comp in comps:
            comp.de_cuerpo = cuerpo.nombre
            comp.fase_plasticidad = "cuerpo"   # D6: lo que aporta un cuerpo aprende en la fase del cuerpo
            _añadir(modulo, preatencion, destino, comp, sistema_asignar)
            org.componentes_cuerpo.append(comp)


def _montar_componentes(org: "Organismo", componentes: Any) -> None:
    """Componentes del registro (por destino, en el orden declarado)."""
    for destino, alta in componentes.items():
        if destino not in DESTINOS_VALIDOS_COMPONENTES:
            raise ValueError(
                f"Destino de componente no válido: '{destino}'. Válidos: {sorted(DESTINOS_VALIDOS_COMPONENTES)}"
            )
        modulo, preatencion, sistema_asignar = _destino(org, destino)

        # sustituye: busca en el módulo de destino (o en su preatención) el Componente general cuya clase se llame como la clave
        for nombre_clase, sustituto in alta.sustituye.items():
            lista = modulo.componentes
            idx = next((i for i, c in enumerate(lista) if c.__class__.__name__ == nombre_clase), None)
            if idx is None and preatencion is not None:
                lista = preatencion
                idx = next((i for i, c in enumerate(lista) if c.__class__.__name__ == nombre_clase), None)
            if idx is None:
                raise ValueError(f"No existe componente general '{nombre_clase}' en {destino} para sustituir")
            original = lista[idx]
            if sustituto.tipo != original.tipo:
                raise ValueError(
                    f"El sustituto '{sustituto.__class__.__name__}' tiene tipo '{sustituto.tipo}', "
                    f"pero '{nombre_clase}' tiene tipo '{original.tipo}'"
                )
            if sustituto.preatentivo != original.preatentivo:
                raise ValueError(f"El sustituto '{sustituto.__class__.__name__}' debe ser preatentivo como '{nombre_clase}' o no serlo")
            sustituto.propio_del_mundo = True
            sustituto.sistema = sistema_asignar
            lista[idx] = sustituto

        # añade: se añade al final del módulo (los preatentivos, al final de la preatención), en el orden declarado
        for comp in alta.añade:
            _añadir(modulo, preatencion, destino, comp, sistema_asignar)


def _montar_estrategias(org: "Organismo", estrategias: Any) -> None:
    """Estrategias del registro (por sistema)."""
    for sis, alta in estrategias.items():
        if sis not in SISTEMAS_VALIDOS_ESTRATEGIAS:
            raise ValueError(
                f"Sistema no válido para estrategias: '{sis}'. Válidos: {sorted(SISTEMAS_VALIDOS_ESTRATEGIAS)}"
            )
        elige: Any = next((c for c in sistema_por_nombre(org.sistemas, sis).componentes() if c.tipo == "Estrategia"), None)
        if elige is None:
            raise ValueError(f"{sis} no tiene componente Estrategia para las estrategias de {org.mundo.nombre}")
        catalogo = elige.catalogo

        # sustituye: clave es nombre de CLASE de la definición general; mismo atributo nombre; catalogo.añadir
        for nombre_clase, sustituto in alta.sustituye.items():
            original_def = next((d for d in catalogo.todas() if d.__class__.__name__ == nombre_clase), None)
            if original_def is None:
                raise ValueError(f"No existe estrategia general de clase '{nombre_clase}' en {sis} para sustituir")
            if sustituto.nombre != original_def.nombre:
                raise ValueError(
                    f"El sustituto '{sustituto.__class__.__name__}' tiene nombre '{sustituto.nombre}', "
                    f"pero la original '{nombre_clase}' tiene nombre '{original_def.nombre}'"
                )
            catalogo.añadir(sustituto)

        # añade: nombre o nombre de clase repetido -> ValueError; se añade con catalogo.añadir
        for d in alta.añade:
            if catalogo.get(d.nombre) is not None:
                raise ValueError(f"Ya existe una estrategia con nombre '{d.nombre}' en el catálogo de {sis}")
            if any(existente.__class__.__name__ == d.__class__.__name__ for existente in catalogo.todas()):
                raise ValueError(f"Ya existe una estrategia de clase '{d.__class__.__name__}' en el catálogo de {sis}")
            catalogo.añadir(d)


def _comprobar_espacio(org: "Organismo") -> None:
    """C7a: lo montado que necesita espacio (``requiere_espacio``) exige un cuerpo que lo dé (``Cuerpo.con_espacio``).
    Sin él no fallaría: no haría nada, en silencio. Es un error de montaje y se dice al nacer."""
    if org.cuerpo is not None and org.cuerpo.con_espacio:
        return
    definiciones = [d for s in org.sistemas for c in s.componentes() if c.tipo == "Estrategia" and hasattr(c, "catalogo")
                    for d in c.catalogo.todas()]
    faltan = sorted({x.__class__.__name__ for x in [*org.montados(), *definiciones] if getattr(x, "requiere_espacio", False)})
    if faltan:
        cuerpo = org.cuerpo.nombre if org.cuerpo is not None else "ninguno"
        raise ValueError(f"{org.mundo.nombre} monta {faltan}, que necesitan un cuerpo con espacio (cuerpo: {cuerpo})")


def _comprobar_plasticidad(org: "Organismo") -> None:
    """D6: cada Componente montado declara una fase de plasticidad conocida, y la fase «cuerpo» es solo de lo que aporta
    un cuerpo."""
    for c in org.montados():
        if c.fase_plasticidad not in FASES_PLASTICIDAD:
            raise ValueError(f"'{c.__class__.__name__}' declara la fase de plasticidad '{c.fase_plasticidad}'. "
                             f"Válidas: {list(FASES_PLASTICIDAD)}")
        if c.fase_plasticidad == "cuerpo" and not c.de_cuerpo:
            raise ValueError(f"'{c.__class__.__name__}' declara la fase de plasticidad 'cuerpo' y no es de un cuerpo")


def _registrar_secciones(org: "Organismo", cuerpo: Optional[Cuerpo]) -> None:
    """Memoria (D7): las secciones de sus dueños (el cuerpo y después los Componentes montados, en orden), que reciben
    al registrarse el manual y el legado que la Memoria guardó para ellas."""
    fuentes: List[Tuple[str, Any]] = [(cuerpo.nombre, cuerpo)] if cuerpo is not None else []
    fuentes += [(c.__class__.__name__, c) for c in org.montados() if not c.de_cuerpo]
    for dueño, fuente in fuentes:
        declarada = fuente.seccion_memoria(org.perfil)
        if declarada is not None and org.memoria.dueño(declarada[0]) != dueño:   # una memoria ya montada por el
            org.memoria.registrar_seccion(declarada[0], dueño, declarada[1])     # mismo dueño conserva su sección


def _destino(org: "Organismo", destino: str) -> Tuple[Modulo, Optional[List[Componente]], str]:
    """Módulo de un destino ya validado, su preatención (solo ``S1.Sentir``, D5) y el ``sistema`` que se asigna."""
    if destino == "CORE.Sentir":
        return org.sentir, None, "MUNDO"
    if destino == "CORE.Actuar":
        return org.actuar, None, "CORE"
    sis, etapa = destino.split(".")
    preatencion = sistema_por_nombre(org.sistemas, "S1").preatencion if destino == "S1.Sentir" else None
    return sistema_por_nombre(org.sistemas, sis).modulo(etapa), preatencion, sis


def _añadir(modulo: Modulo, preatencion: Optional[List[Componente]], destino: str, comp: Componente, sistema: str) -> None:
    """``añade`` (D3): al final del módulo (un preatentivo, al final de la preatención), con nombre de clase único."""
    if comp.preatentivo and preatencion is None:
        raise ValueError(f"'{comp.__class__.__name__}' es preatentivo: solo puede registrarse en S1.Sentir (D5)")
    lista = preatencion if comp.preatentivo and preatencion is not None else modulo.componentes
    if any(c.__class__.__name__ == comp.__class__.__name__ for c in modulo.componentes + (preatencion or [])):
        raise ValueError(f"Ya existe un componente '{comp.__class__.__name__}' en {destino}; declara sustituye")
    comp.propio_del_mundo = True
    comp.sistema = sistema
    lista.append(comp)
