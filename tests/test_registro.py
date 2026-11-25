"""Tests para el registro declarado de Componentes y estrategias (decisión D3, paso A1)."""

from typing import Any
import pytest

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.azar import Azar
from ida.nucleo.estrategia import Definicion
from ida.core.latido import DESTINOS_VALIDOS_COMPONENTES, Organismo
from ida.nucleo.linaje import Arquetipo
from ida.nucleo.memoria import Memoria
from ida.nucleo.mundo import Alta, Cuerpo, Registro
from ida.mundos.minimo import MundoMinimo
from ida.sistemas_comun import crear_sistemas
from ida.s1 import crear_s1


def _crear_organismo(mundo: Any) -> Organismo:
    azar = Azar(42)
    sistemas = crear_sistemas()
    arquetipo = Arquetipo.nuevo(azar)
    memoria = Memoria(mundo.perfil.memoria)
    return Organismo(mundo, sistemas, arquetipo, memoria, azar)


# --- Clases auxiliares para tests --------------------------------------------


class DummyComp(Componente):
    def __init__(self, nombre_clase: str, tipo: str = "Pieza"):
        super().__init__()
        self.__class__.__name__ = nombre_clase
        self.tipo = tipo


def _crear_clase_comp(nombre: str, tipo_pieza: str = "Pieza"):
    return type(nombre, (Componente,), {"tipo": tipo_pieza})


class EstrategiaPrueba(Definicion):
    nombre = "estrategia_prueba"
    impulsos = ("seguridad",)


class EstrategiaSustitutaAlimentarse(Definicion):
    nombre = "alimentarse"
    impulsos = ("hambre",)


class EstrategiaMalNombre(Definicion):
    nombre = "nombre_distinto"
    impulsos = ("hambre",)


# --- Tests -------------------------------------------------------------------


def test_añade_en_los_13_destinos_al_final_y_en_orden():
    assert len(DESTINOS_VALIDOS_COMPONENTES) == 13

    componentes_registro = {}
    clases_creadas = {}
    for i, destino in enumerate(sorted(DESTINOS_VALIDOS_COMPONENTES)):
        c1 = _crear_clase_comp(f"CompA_{i}", f"TipoA_{i}")()
        c2 = _crear_clase_comp(f"CompB_{i}", f"TipoB_{i}")()
        componentes_registro[destino] = Alta(añade=[c1, c2])
        clases_creadas[destino] = (c1, c2)

    class Mundo13Destinos(MundoMinimo):
        def registro(self) -> Registro:
            return Registro(componentes=componentes_registro)

    org = _crear_organismo(Mundo13Destinos())

    for destino, (c1, c2) in clases_creadas.items():
        if destino == "CORE.Sentir":
            comps = org.sentir.componentes
            esperado_sis = "MUNDO"
        else:
            sis, etapa = destino.split(".")
            comps = org._sistema(sis).modulo(etapa).componentes
            esperado_sis = sis

        # Verificamos que están al final y en el orden declarado
        assert comps[-2] is c1
        assert comps[-1] is c2
        assert c1.propio_del_mundo is True
        assert c2.propio_del_mundo is True
        assert c1.sistema == esperado_sis
        assert c2.sistema == esperado_sis


def test_sustituye_conserva_posicion_y_exige_mismo_tipo():
    ClaseSustituto = _crear_clase_comp("ObjetoPersonalizado", tipo_pieza="Objeto")
    sustituto = ClaseSustituto()

    class MundoSustituto(MundoMinimo):
        def registro(self) -> Registro:
            return Registro(
                componentes={
                    "S1.Interpretar": Alta(sustituye={"Objeto": sustituto})
                }
            )

    org = _crear_organismo(MundoSustituto())
    modulo = org._sistema("S1").modulo("Interpretar")

    # Objeto era el primer componente de S1.Interpretar
    assert modulo.componentes[0] is sustituto
    assert sustituto.propio_del_mundo is True
    assert sustituto.sistema == "S1"
    assert type(modulo.componentes[1]).__name__ == "Supervivencia"

    # Distinto tipo debe fallar
    ClaseMalTipo = _crear_clase_comp("ObjetoMalTipo", tipo_pieza="OtroTipo")
    mal_tipo = ClaseMalTipo()

    class MundoMalTipo(MundoMinimo):
        def registro(self) -> Registro:
            return Registro(
                componentes={
                    "S1.Interpretar": Alta(sustituye={"Objeto": mal_tipo})
                }
            )

    with pytest.raises(ValueError, match="tiene tipo 'OtroTipo', pero 'Objeto' tiene tipo 'Objeto'"):
        _crear_organismo(MundoMalTipo())


def test_nombre_repetido_sin_sustituye_lanza_value_error():
    ClaseRepetida = _crear_clase_comp("Objeto", tipo_pieza="Objeto")

    class MundoRepetido(MundoMinimo):
        def registro(self) -> Registro:
            return Registro(
                componentes={
                    "S1.Interpretar": Alta(añade=[ClaseRepetida()])
                }
            )

    with pytest.raises(ValueError, match="Ya existe un componente 'Objeto' en S1.Interpretar; declara sustituye"):
        _crear_organismo(MundoRepetido())


def test_sustituye_de_algo_que_no_existe_lanza_value_error():
    ClaseComp = _crear_clase_comp("MiComponente", tipo_pieza="Pieza")

    class MundoInexistente(MundoMinimo):
        def registro(self) -> Registro:
            return Registro(
                componentes={
                    "S1.Interpretar": Alta(sustituye={"ComponenteFantasma": ClaseComp()})
                }
            )

    with pytest.raises(ValueError, match="No existe componente general 'ComponenteFantasma' en S1.Interpretar"):
        _crear_organismo(MundoInexistente())


def test_destino_invalido_lanza_value_error():
    ClaseComp = _crear_clase_comp("MiComponente", tipo_pieza="Pieza")

    class MundoDestinoInvalido(MundoMinimo):
        def registro(self) -> Registro:
            return Registro(
                componentes={
                    "CORE.Actuar": Alta(añade=[ClaseComp()])
                }
            )

    with pytest.raises(ValueError, match="Destino de componente no válido"):
        _crear_organismo(MundoDestinoInvalido())


def test_estrategia_añadida_en_catalogo_de_estrategia_y_de_accion():
    estr = EstrategiaPrueba()

    class MundoNuevaEstrategia(MundoMinimo):
        def registro(self) -> Registro:
            return Registro(estrategias={"S1": Alta(añade=[estr])})

    org = _crear_organismo(MundoNuevaEstrategia())
    s1 = org._sistema("S1")

    comp_estr = next(c for c in s1.componentes() if c.tipo == "Estrategia")
    comp_acc = next(c for c in s1.componentes() if c.tipo == "Accion")

    # Mismo objeto y presente en ambos catálogos
    assert comp_estr.catalogo.get("estrategia_prueba") is estr
    assert comp_acc.catalogo.get("estrategia_prueba") is estr
    assert comp_estr.catalogo is comp_acc.catalogo

    # Añadir estrategia con nombre ya existente debe fallar
    class EstrategiaNombreRepetido(Definicion):
        nombre = "huir"  # ya existe en S1

    class MundoEstrategiaNombreRepetido(MundoMinimo):
        def registro(self) -> Registro:
            return Registro(estrategias={"S1": Alta(añade=[EstrategiaNombreRepetido()])})

    with pytest.raises(ValueError, match="Ya existe una estrategia con nombre 'huir' en el catálogo de S1"):
        _crear_organismo(MundoEstrategiaNombreRepetido())

    # Añadir estrategia con nombre de clase ya existente debe fallar
    ClaseHuirRepetida = type("Huir", (Definicion,), {"nombre": "huir_personalizado"})

    class MundoEstrategiaClaseRepetida(MundoMinimo):
        def registro(self) -> Registro:
            return Registro(estrategias={"S1": Alta(añade=[ClaseHuirRepetida()])})

    with pytest.raises(ValueError, match="Ya existe una estrategia de clase 'Huir' en el catálogo de S1"):
        _crear_organismo(MundoEstrategiaClaseRepetida())


def test_estrategia_sustituida_conserva_posicion_y_exige_mismo_nombre():
    sustituta = EstrategiaSustitutaAlimentarse()

    class MundoSustituyeEstrategia(MundoMinimo):
        def registro(self) -> Registro:
            return Registro(
                estrategias={"S1": Alta(sustituye={"Alimentarse": sustituta})}
            )

    # Obtenemos el orden original de nombres de S1
    s1_base = crear_s1()
    cat_base = next(c for c in s1_base.componentes() if c.tipo == "Estrategia").catalogo
    nombres_originales = [d.nombre for d in cat_base.todas() if not d.opcional]   # el mínimo no registra opcionales

    org = _crear_organismo(MundoSustituyeEstrategia())
    s1 = org._sistema("S1")
    cat = next(c for c in s1.componentes() if c.tipo == "Estrategia").catalogo

    # La estrategia sustituida ocupa la misma posición que tenía Alimentarse
    nombres_nuevos = [d.nombre for d in cat.todas()]
    assert nombres_nuevos == nombres_originales
    assert cat.get("alimentarse") is sustituta

    # Exige el mismo nombre
    mal_nombre = EstrategiaMalNombre()

    class MundoMalNombre(MundoMinimo):
        def registro(self) -> Registro:
            return Registro(
                estrategias={"S1": Alta(sustituye={"Alimentarse": mal_nombre})}
            )

    with pytest.raises(ValueError, match="tiene nombre 'nombre_distinto', pero la original 'Alimentarse' tiene nombre 'alimentarse'"):
        _crear_organismo(MundoMalNombre())

    # Sustituye de clase que no existe en el catálogo debe fallar
    class MundoClaseNoExiste(MundoMinimo):
        def registro(self) -> Registro:
            return Registro(
                estrategias={"S1": Alta(sustituye={"EstrategiaFantasma": sustituta})}
            )

    with pytest.raises(ValueError, match="No existe estrategia general de clase 'EstrategiaFantasma' en S1 para sustituir"):
        _crear_organismo(MundoClaseNoExiste())


# --- Cuerpo (D10) -------------------------------------------------------------------------------------
class _CompCuerpo(Componente):
    """Componente de cuerpo de prueba: cuenta las llamadas a ``aprender``."""

    def __init__(self) -> None:
        super().__init__()
        self.llamadas = 0

    def aprender(self, ctx: Contexto) -> None:
        self.llamadas += 1


class CuerpoActuar(_CompCuerpo):
    pass


class CuerpoInterpretar(_CompCuerpo):
    pass


class CuerpoPrueba(Cuerpo):
    nombre = "prueba"

    def __init__(self, destinos: Any) -> None:
        self.destinos = destinos

    def componentes(self) -> Any:
        return self.destinos


def test_cuerpo_se_monta_antes_que_lo_del_mundo_y_admite_core_actuar():
    actuar, interpretar = CuerpoActuar(), CuerpoInterpretar()
    del_mundo = _crear_clase_comp("DelMundo")()

    class MundoConCuerpo(MundoMinimo):
        def registro(self) -> Registro:
            return Registro(componentes={"S1.Interpretar": Alta(añade=[del_mundo])},
                            cuerpo=CuerpoPrueba({"CORE.Actuar": [actuar], "S1.Interpretar": [interpretar]}))

    org = _crear_organismo(MundoConCuerpo())
    assert org.actuar.componentes[-1] is actuar and actuar.sistema == "CORE"
    modulo = org._sistema("S1").modulo("Interpretar").componentes
    assert modulo[-2:] == [interpretar, del_mundo] and interpretar.sistema == "S1"
    for c in (actuar, interpretar):
        assert c.de_cuerpo == "prueba" and c.propio_del_mundo is True
    assert del_mundo.de_cuerpo == ""
    assert org.componentes_cuerpo == [actuar, interpretar]
    assert {"CuerpoActuar", "CuerpoInterpretar"} <= org.registrados


def test_cuerpo_con_destino_no_valido_lanza_value_error():
    class MundoCuerpoMalo(MundoMinimo):
        def registro(self) -> Registro:
            return Registro(cuerpo=CuerpoPrueba({"CORE.Regulacion": [CuerpoActuar()]}))

    with pytest.raises(ValueError, match="Destino no válido para un Componente del cuerpo 'prueba'"):
        _crear_organismo(MundoCuerpoMalo())


def test_cuerpo_y_mundo_no_pueden_repetir_clase():
    class MundoRepite(MundoMinimo):
        def registro(self) -> Registro:
            return Registro(componentes={"S1.Interpretar": Alta(añade=[CuerpoInterpretar()])},
                            cuerpo=CuerpoPrueba({"S1.Interpretar": [CuerpoInterpretar()]}))

    with pytest.raises(ValueError, match="Ya existe un componente 'CuerpoInterpretar'"):
        _crear_organismo(MundoRepite())


def test_componentes_del_cuerpo_aprenden_una_sola_vez_por_latido():
    """Su ``aprender`` lo llama ``Organismo._aprender`` (donde estaba ``_aprender_mapa``), no el gancho general."""
    actuar, interpretar = CuerpoActuar(), CuerpoInterpretar()

    class MundoConCuerpo(MundoMinimo):
        def registro(self) -> Registro:
            return Registro(cuerpo=CuerpoPrueba({"CORE.Actuar": [actuar], "S1.Interpretar": [interpretar]}))

    org = _crear_organismo(MundoConCuerpo())
    assert org.con_experiencia and org.memoria.activa
    for n in (1, 2, 3):
        org.latir()
        assert (actuar.llamadas, interpretar.llamadas) == (n, n)


def test_ctx_registrado_dice_true_para_lo_montado_y_false_para_lo_que_no():
    class MundoPruebaRegistrados(MundoMinimo):
        def registro(self) -> Registro:
            estr = EstrategiaPrueba()
            return Registro(estrategias={"S1": Alta(añade=[estr])})

    org = _crear_organismo(MundoPruebaRegistrados())
    onda = org.latir()

    # Contexto construido durante latir()
    assert "Interocepcion" in org.registrados
    assert "Tribunal" in org.registrados
    assert "Objeto" in org.registrados
    assert "Huir" in org.registrados
    assert "EstrategiaPrueba" in org.registrados

    # Probamos ctx.registrado directamente
    ctx = Contexto(
        onda,
        org.soma,
        org.memoria,
        org.arquetipo,
        org.azar,
        org.perfil,
        org.verbos,
        registrados=org.registrados,
    )

    assert ctx.registrado("Interocepcion") is True
    assert ctx.registrado("Tribunal") is True
    assert ctx.registrado("Objeto") is True
    assert ctx.registrado("Huir") is True
    assert ctx.registrado("EstrategiaPrueba") is True
    assert ctx.registrado("ComponenteInexistente") is False
    assert ctx.registrado("EstrategiaFantasma") is False


# --- Opcionales (D3, D15, paso A6a) -------------------------------------------


class OpcionalInterpretar(Componente):
    opcional = True


class OpcionalPreatento(Componente):
    tipo = "Exterocepcion"
    preatentivo = True
    opcional = True


class EstrategiaOpcional(Definicion):
    nombre = "estrategia_opcional"
    impulsos = ("seguridad",)
    opcional = True


def _organismo_con_opcionales(opcionales: list) -> Organismo:
    """Un montaje general con un Componente, un preatentivo y una estrategia opcionales en medio de lo general."""

    class MundoOpcionales(MundoMinimo):
        def registro(self) -> Registro:
            reg = super().registro()      # lo que ya registra el mínimo (``Defensa``)
            reg.opcionales = list(opcionales)
            return reg

    mundo = MundoOpcionales()
    azar = Azar(42)
    sistemas = crear_sistemas()
    s1 = next(s for s in sistemas if s.nombre == "S1")
    s1.modulo("Interpretar").componentes.insert(1, OpcionalInterpretar())
    s1.preatencion.insert(0, OpcionalPreatento())
    catalogo = next(c for c in s1.componentes() if c.tipo == "Estrategia").catalogo
    defs = catalogo.todas()
    for d in defs:
        catalogo.quitar(d.nombre)
    for d in [*defs[:2], EstrategiaOpcional(), *defs[2:]]:
        catalogo.añadir(d)
    return Organismo(mundo, sistemas, Arquetipo.nuevo(azar), Memoria(mundo.perfil.memoria), azar)


def _nombres(lista: list) -> list:
    return [c.__class__.__name__ for c in lista]


def test_opcional_no_nombrado_se_quita_conservando_el_orden():
    base = _crear_organismo(MundoMinimo())
    org = _organismo_con_opcionales([])
    s1, s1_base = org._sistema("S1"), base._sistema("S1")
    assert _nombres(s1.modulo("Interpretar").componentes) == _nombres(s1_base.modulo("Interpretar").componentes)
    assert _nombres(org.preatencion.componentes) == _nombres(base.preatencion.componentes)
    cat = next(c for c in s1.componentes() if c.tipo == "Estrategia").catalogo
    cat_base = next(c for c in s1_base.componentes() if c.tipo == "Estrategia").catalogo
    assert [d.nombre for d in cat.todas()] == [d.nombre for d in cat_base.todas()]
    for nombre in ("OpcionalInterpretar", "OpcionalPreatento", "EstrategiaOpcional"):
        assert nombre not in org.registrados


def test_opcional_nombrado_se_monta_en_su_sitio():
    org = _organismo_con_opcionales(["OpcionalInterpretar", "OpcionalPreatento", "EstrategiaOpcional"])
    s1 = org._sistema("S1")
    assert _nombres(s1.modulo("Interpretar").componentes)[1] == "OpcionalInterpretar"
    assert _nombres(org.preatencion.componentes)[0] == "OpcionalPreatento"
    cat = next(c for c in s1.componentes() if c.tipo == "Estrategia").catalogo
    assert [d.nombre for d in cat.todas()][2] == "estrategia_opcional"
    accion = next(c for c in s1.componentes() if c.tipo == "Accion")
    assert accion.catalogo is cat      # el catálogo es el mismo para Estrategia y Accion
    for nombre in ("OpcionalInterpretar", "OpcionalPreatento", "EstrategiaOpcional"):
        assert nombre in org.registrados


def test_opcional_desconocido_lanza_value_error():
    with pytest.raises(ValueError, match="Opcionales desconocidos"):
        _organismo_con_opcionales(["NoExiste"])
    with pytest.raises(ValueError, match="Opcionales desconocidos"):
        _organismo_con_opcionales(["Objeto"])     # existe, pero no es opcional


# --- C7a: lo que necesita espacio exige un cuerpo con espacio ------------------


def test_requiere_espacio_sin_cuerpo_lanza_value_error():
    class MundoSinEspacio(MundoMinimo):
        def registro(self) -> Registro:
            reg = super().registro()
            reg.opcionales = ["Amenaza", "Afrontar"]
            return reg

    with pytest.raises(ValueError, match=r"necesitan un cuerpo con espacio.*cuerpo: ninguno"):
        _crear_organismo(MundoSinEspacio())


def test_requiere_espacio_con_cuadricula_se_monta():
    from ida.cuerpos.cuadricula import Cuadricula

    class MundoConEspacio(MundoMinimo):
        def registro(self) -> Registro:
            reg = super().registro()
            reg.opcionales = ["Amenaza", "Afrontar"]
            reg.cuerpo = Cuadricula()
            return reg

    org = _crear_organismo(MundoConEspacio())
    assert {"Amenaza", "Afrontar"} <= org.registrados
    assert Cuerpo().con_espacio is False and Cuadricula().con_espacio is True
