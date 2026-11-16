"""Ejecuta vidas y generaciones de un linaje en un mundo."""

import os
import shutil
import time
from typing import Any, Callable, Dict, List, Optional

from ida.consola import linea, resumen_latido
from ida.core.azar import Azar
from ida.core.latido import Organismo
from ida.core.linaje import Arquetipo, Linaje
from ida.core.memoria import Memoria
from ida.core.persistencia import Persistencia
from ida.historico import calcular_fitness, guardar_linaje_con_retencion
from ida.mundos import cargar
from ida.sistemas import crear_sistemas

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(RAIZ, "datos")


class InterrupcionSimulacion(Exception):
    """Lanzada para detener limpiamente la simulación desde la antesala web."""
    pass


def ejecutar(
    mundo: str,
    latidos: int = 300,
    semilla: int = 1,
    generaciones: int = 1,
    ver: bool = False,
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
) -> List[Dict[str, Any]]:
    datos = datos or os.path.join(DATOS, mundo)
    if tabula_rasa and os.path.isdir(datos):
        shutil.rmtree(datos)
    os.makedirs(datos, exist_ok=True)
    m = cargar(mundo)(datos=datos, **(opciones_mundo or {}))
    azar = Azar(semilla)
    linaje = Linaje(os.path.join(datos, "linaje.json"))
    persistencia = Persistencia(os.path.join(datos, "memoria.db") if m.perfil.memoria != "apagada" else None)
    telemetria = telemetria_instancia
    telemetria_propia = False
    if ver and telemetria is None:
        from ida.telemetria.servidor import Telemetria
        telemetria = Telemetria(mundo=mundo)
        telemetria_propia = True
    elif telemetria is not None:
        telemetria.mundo = mundo
    observabilidad = None
    if otel:
        from ida.telemetria.otel import Observabilidad   # requiere el extra [observabilidad]
        observabilidad = Observabilidad(mundo)
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
            legado_a_heredar = linaje.legado() or legado_inicial or {}
            heredados = memoria.heredar(legado_a_heredar)
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
            persistencia.nueva_vida()
            org.al_dormir = lambda o: persistencia.volcar(o.memoria, o.arquetipo.id, o.ciclo)
            if consola:
                print(f"\n=== {arq.id} · {mundo} · generación {arq.generacion} · {arq.texto()} · heredados: {heredados}")

            def latir(o: Organismo, onda) -> None:
                r = resumen_latido(o, onda)
                if consola and (onda.ciclo % cada == 0 or r["experiencia"]["aprendizaje"] or r["guillotina"]):
                    print(linea(r))
                if telemetria is not None or observabilidad is not None:
                    mem = o.memoria
                    estados = [p.estado(onda.ciclo).value for p in mem.saber.values()]
                    r["vista"] = o.mundo.vista()
                    r["conocimiento"] = mem.conocimiento(onda.ciclo)[:20]
                    r["individuo"] = o.arquetipo.id
                    r["generacion"] = o.arquetipo.generacion
                    r["arquetipo"] = {k: getattr(o.arquetipo, k) for k in ("apertura", "responsabilidad", "neuroticismo", "extraversion", "umbral_miedo")}
                    r["memoria"] = {"aciertos": mem.aciertos, "sorpresas": mem.fallos, "episodios": len(mem.episodios),
                                    "demostradas": estados.count("demostrada"), "hipotesis": estados.count("hipótesis"),
                                    "refutadas": estados.count("refutada"), "recuerdos": len(mem.registros), "heredados": heredados}  # noqa: B023 (se usa en la misma iteración)
                    r["contadores"] = dict(o.contadores)
                    r["puntuacion"] = o.mundo.puntuacion()
                    r["sin_experiencia"] = sin_experiencia
                if observabilidad is not None:
                    observabilidad.latido(onda, r)
                if telemetria is not None:
                    telemetria.publicar(r)
                    if not o.perfil.tiempo_real:      # a ritmo visible: cada latido dura al menos su plazo
                        time.sleep(o.perfil.frecuencia_ms / 1000.0)
                if al_latir:
                    al_latir(o, onda, r)
                if evento_parada is not None and evento_parada.is_set():
                    raise InterrupcionSimulacion()

            try:
                vividos = org.vivir(latidos, al_latir=latir)
            except InterrupcionSimulacion:
                vividos = org.ciclo
                if consola:
                    print(f"\n[simulación interrumpida por el usuario tras {vividos} latidos]")
                break
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
        m.cerrar()
        persistencia.cerrar()
        if telemetria is not None and telemetria_propia:
            telemetria.detener()
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
