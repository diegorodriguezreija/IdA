"""Ejecuta vidas y generaciones de un linaje en un mundo."""

import os
import shutil
import sys
from typing import Any, Callable, Dict, List, Optional

from ida.consola import imprimir_latido, linea
from ida.nucleo.azar import Azar
from ida.core.latido import Organismo
from ida.nucleo.linaje import Arquetipo, Linaje
from ida.nucleo.memoria import Memoria
from ida.nucleo.persistencia import Persistencia
from ida.telemetria.grabacion import Grabacion, cabecera, commit_actual
from ida.telemetria.observador import Observador
from ida.telemetria.ritmo import Regulador
from ida.historico import calcular_fitness, guardar_linaje_con_retencion
from ida.mundos import cargar
from ida.mundos.opciones import convertir
from ida.sistemas import crear_sistemas

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _carpeta_datos(raiz: str) -> str:
    """Devuelve la carpeta de datos: local en el repositorio o del usuario si está instalado."""
    if os.path.isfile(os.path.join(raiz, "pyproject.toml")):
        return os.path.join(raiz, "datos")
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, "IdA", "datos")
    if sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "IdA", "datos")
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, "ida", "datos")


DATOS = _carpeta_datos(RAIZ)


class InterrupcionSimulacion(Exception):
    """Lanzada para detener limpiamente la simulación desde la antesala web."""
    pass


def ejecutar(
    mundo: str,
    latidos: int = 300,
    semilla: int = 1,
    generaciones: int = 1,
    sin_experiencia: bool = False,
    tabula_rasa: bool = False,
    consola: bool = True,
    cada: int = 1,
    datos: Optional[str] = None,
    opciones_mundo: Optional[Dict[str, Any]] = None,
    al_latir: Optional[Callable] = None,
    otel: bool = False,
    telemetria_instancia: Optional[Any] = None,
    evento_parada: Optional[Any] = None,
    arquetipo_inicial: Optional[Dict[str, float]] = None,
    legado_inicial: Optional[Dict[str, Any]] = None,
    biblioteca: Optional[Any] = None,
    nivel: Optional[str] = None,
    grabar: Optional[str] = None,
    plazo_logico: Optional[float] = None,
    ritmo: Optional[Regulador] = None,
) -> List[Dict[str, Any]]:
    """Vive ``generaciones`` vidas de un linaje en ``mundo``.

    - ``nivel``: nivel del registro del latido (``vital``, ``cognitivo`` o ``completo``, O4). Con un nivel, el observador
      corre siempre; sin él (``None``), corre al nivel cognitivo solo si alguien consume el registro (consola,
      telemetría, OTel o grabación). ``al_latir(org, onda, registro)`` recibe el registro, o ``None`` si no corre.
    - ``grabar``: ruta de la grabación ``.jsonl.gz`` de la vida (O7).
    - ``opciones_mundo``: opciones del mundo, comprobadas y convertidas con sus declaraciones (``Mundo.opciones()``,
      O8). Las que no se dan toman el valor por defecto del constructor (la antesala añade antes los declarados).
    - ``plazo_logico``: operaciones por ms de plazo de la guillotina (``Onda.ops_por_ms``, O11). ``None``: plazo de reloj,
      como siempre.
    - ``ritmo``: el regulador del ritmo visible (O3), aplicado entre latidos cuando hay telemetría y el mundo no es de
      tiempo real. Sin él, ×1: cada latido dura al menos ``frecuencia_ms`` del ``Perfil``, como siempre.
    """
    datos = datos or os.path.join(DATOS, mundo)
    if tabula_rasa and os.path.isdir(datos):
        shutil.rmtree(datos)
    os.makedirs(datos, exist_ok=True)
    clase_mundo = cargar(mundo)
    opciones_mundo = convertir(clase_mundo.opciones(), opciones_mundo or {}, mundo)   # O8: error claro si no valen
    m = clase_mundo(datos=datos, **opciones_mundo)
    azar = Azar(semilla)
    linaje = Linaje(os.path.join(datos, "linaje.json"))
    persistencia = Persistencia(os.path.join(datos, "memoria.db") if m.perfil.memoria != "apagada" else None)
    telemetria = telemetria_instancia   # el servidor de la aplicación (T6a: también el de ``python -m ida --ver``)
    if telemetria is not None:
        telemetria.mundo = mundo
    observabilidad = None
    if otel:
        from ida.telemetria.otel import Observabilidad   # requiere el extra [observabilidad]
        observabilidad = Observabilidad(mundo)
    regulador = ritmo if ritmo is not None else (Regulador("x1") if telemetria is not None else None)
    observador: Optional[Observador] = None
    if nivel is not None or grabar or consola or telemetria is not None or observabilidad is not None:
        # O2: la consola, el directo, la grabación y OTel leen el registro. OTel (O15) saca sus tramos por fase de los
        # campos del nivel completo (``fases``, ``tiempos_ms``): sin nivel pedido, con OTel se observa a ese nivel.
        observador = Observador(nivel or ("completo" if observabilidad is not None else "cognitivo"))
    grabacion: Optional[Grabacion] = None
    if grabar and observador is not None:
        grabacion = Grabacion(grabar, cabecera(mundo, observador.nivel, semilla, latidos, generaciones, opciones_mundo,
                                               arquetipo_inicial, plazo_logico, sin_experiencia, commit_actual()))
    resumenes = []
    vivencia = None
    try:
        for g in range(generaciones):
            azar_g = azar.derivar(g + 1 + len(linaje.generaciones))
            padre = linaje.ultimo_arquetipo()
            if padre:
                arq = padre.mutar(azar_g, vivencia)
            elif arquetipo_inicial:
                arq = Arquetipo(
                    linaje=mundo.capitalize(),
                    apertura=float(arquetipo_inicial.get("apertura", 0.5)),
                    responsabilidad=float(arquetipo_inicial.get("responsabilidad", 0.5)),
                    neuroticismo=float(arquetipo_inicial.get("neuroticismo", 0.5)),
                    extraversion=float(arquetipo_inicial.get("extraversion", 0.5)),
                    umbral_miedo=float(arquetipo_inicial.get("umbral_miedo", 0.6)),
                )
            else:
                arq = Arquetipo.nuevo(azar_g, linaje=mundo.capitalize())
            memoria = Memoria(m.perfil.memoria)
            memoria.aplicar_manual(m.manual())       # paso 2: el manual del mundo, antes de heredar
            legado_a_heredar = linaje.legado() or legado_inicial or {}
            heredados = memoria.heredar(legado_a_heredar, m.perfil.mecanismos.tasa_herencia)
            m.reiniciar(azar_g.semilla)
            org_biblioteca: Optional[Any] = None
            if isinstance(biblioteca, str):
                if biblioteca == "nula":
                    from ida.bibliotecas.nula import BibliotecaNula
                    org_biblioteca = BibliotecaNula()
                elif biblioteca == "fija":
                    from ida.bibliotecas.fija import BibliotecaFija
                    org_biblioteca = BibliotecaFija()
                elif biblioteca == "erronea":
                    from ida.bibliotecas.erronea import BibliotecaErronea
                    semilla_bib = azar_g.semilla if azar_g.semilla is not None else 42
                    org_biblioteca = BibliotecaErronea(semilla=semilla_bib)
            elif biblioteca is not None:
                org_biblioteca = biblioteca
            org = Organismo(m, crear_sistemas(), arq, memoria, azar_g, con_experiencia=not sin_experiencia, biblioteca=org_biblioteca)
            if plazo_logico is not None:
                org.ops_por_ms = plazo_logico   # O11: plazo lógico (la misma semilla da la misma vida)
            heredados = memoria.heredados   # D7: con lo que tomaron las secciones al montarse sus dueños
            persistencia.nueva_vida()
            org.al_dormir = lambda o: persistencia.volcar(o.memoria, o.arquetipo.id, o.ciclo)
            if consola:
                print(f"\n=== {arq.id} · {mundo} · generación {arq.generacion} · {arq.texto()} · heredados: {heredados}")

            ultima: Dict[str, Any] = {"onda": None}   # la Onda del último latido (para el registro de cierre)

            def latir(o: Organismo, onda, ultima: Dict[str, Any] = ultima) -> None:
                ultima["onda"] = onda
                registro = observador.registrar(o, onda) if observador is not None else None
                if grabacion is not None and registro is not None:
                    grabacion.escribir(registro)
                if consola and registro is not None and imprimir_latido(registro, cada):
                    print(linea(registro))
                if observabilidad is not None and registro is not None:
                    observabilidad.latido(registro)   # O15: OTel se alimenta del registro
                if telemetria is not None and registro is not None:
                    telemetria.publicar(registro)
                    if regulador is not None and not o.perfil.tiempo_real:   # O3: ritmo visible, entre latidos
                        regulador.esperar(o.perfil.frecuencia_ms, evento_parada)
                if al_latir:
                    al_latir(o, onda, registro)
                if evento_parada is not None and evento_parada.is_set():
                    raise InterrupcionSimulacion()

            try:
                vividos = org.vivir(latidos, al_latir=latir)
            except InterrupcionSimulacion:
                vividos = org.ciclo
                if consola:
                    print(f"\n[simulación interrumpida por el usuario tras {vividos} latidos]")
                break
            if observador is not None and ultima["onda"] is not None and not org.soma.esta_vivo:
                # T4b: lo aprendido al morir (``_aprender_de_la_muerte`` corre después del último latido observado). El
                # observador solo lee; el registro de cierre va a la grabación y al directo, no a la consola ni a al_latir.
                cierre = observador.cierre(org, ultima["onda"])
                if cierre is not None:
                    if grabacion is not None:
                        grabacion.escribir(cierre)
                    if telemetria is not None:
                        telemetria.publicar(cierre)
            persistencia.volcar(memoria, arq.id, org.ciclo)
            total = max(1, vividos)
            vivencia = {
                "fraccion_miedo": org.contadores["miedo"] / total,
                "fraccion_calma": org.contadores["calma"] / total,
                "fraccion_hambre": org.contadores["hambre"] / total,
            }
            resumen = {
                "latidos": vividos,
                "vivo": org.soma.esta_vivo,
                "causa_muerte": org.causa_muerte,
                "vitalidad": round(org.soma.vitalidad, 1),
                "puntuacion": m.puntuacion(),
                "guillotinas": org.contadores["guillotinas"],
                "aciertos": memoria.aciertos,
                "fallos": memoria.fallos,
                "episodios": len(memoria.episodios),
                "conocimiento": memoria.conocimiento(org.ciclo),
                "sin_experiencia": sin_experiencia,
                "fitness": round(calcular_fitness(mundo, {"puntuacion": m.puntuacion(), "latidos": vividos}), 2),
                "fijado": False,
            }
            linaje.registrar(arq, resumen, memoria.legado(org.ciclo))
            guardar_linaje_con_retencion(mundo, linaje.datos, datos_dir=datos)
            if observabilidad is not None:
                observabilidad.vida(vividos, org.soma.esta_vivo)
            resumenes.append(resumen)
            if consola:
                _imprimir_resumen(arq, resumen)
    finally:
        if grabacion is not None:
            grabacion.cerrar()
        m.cerrar()
        persistencia.cerrar()
        if observabilidad is not None:
            observabilidad.cerrar()
    return resumenes


def _imprimir_resumen(arq: Arquetipo, r: Dict[str, Any]) -> None:
    estado = "vive" if r["vivo"] else "muere"
    print(f"--- {arq.id}: {r['latidos']} latidos, {estado} (vitalidad {r['vitalidad']}) · {r['puntuacion']} · "
          f"expectativas: {r['aciertos']} aciertos, {r['fallos']} sorpresas · guillotinas: {r['guillotinas']}")
    if r["conocimiento"]:
        print("    Lo que sabe:")
        for t in r["conocimiento"][:12]:
            print(f"      {t}")
