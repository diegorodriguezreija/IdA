"""Estrategia PerseguirMetas para S3."""

from typing import Any, Dict, List, Optional, Tuple, cast

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.estrategia import ConPropuestas
from ida.nucleo.pieza import Pieza
from ida.nucleo.vocabulario import Verbo
from ida.s3.comun import (
    Paso,
    _cantidad,
    _cosas,
    acercarse_a_clase,
    delante,
    desplazamientos_a_clase,
    inventario,
    ir_por_el_mapa,
)
from ida.s3.interpretar.requisito import Requisitos
from ida.sistemas_comun import al_alcance, lugares, mejor


class PerseguirMetas(ConPropuestas):
    """Estrategia general de S3 para la intención «progresar» (paso 5): encadena requisitos hacia atrás desde
    las metas que declara el manual del mundo. No sabe qué es nada: trabaja con (verbo, objetivo) →
    requisitos → efecto. Con ``memoria.metas`` vacía (un mundo sin manual) no es elegible.

    - Para cada meta pendiente busca la primera acción ejecutable que la acerca (``_resolver``) y propone la
      de menor coste: submetas pendientes más distancia a la instancia objetivo, más los fallos esperados de
      la acción, 1 / tasa − 1 (``Memoria.tasa_estimada``). Una acción cuyo efecto puede salir (manual o
      experiencia) no se bloquea por fallos seguidos: su coste crece con ellos.
    - No persigue metas de ATACAR (lo arbitra Seguridad) ni de DORMIR (no decide cuándo dormir): son metas
      del manual, pero se cumplen por otras vías.
    - Sin plan, con calma y con poca frecuencia, prueba COGER sobre lo que tiene delante si aún no lo ha
      probado en esta vida (exploración de efectos, 5.2 c).
    """

    nombre = "perseguir_metas"
    impulsos = ("progresar",)
    prioridad = 10
    agotable = False
    PROFUNDIDAD = 5
    AROUSAL = 0.5
    CADA_EXPLORACION = 5          # latidos entre pruebas de efectos
    VERBOS_PLAN = (Verbo.USAR, Verbo.COGER, Verbo.COMER)
    SIN_ACERCARSE = 8             # propuestas seguidas de MOVER al mismo destino sin que baje la distancia...
    APARCAR = 30                  # ...que lo dejan aparcado durante estos latidos

    def __init__(self) -> None:
        super().__init__()
        self._aparcados: Dict[str, int] = {}          # destino -> latido hasta el que no se elige
        self._seguimiento: Tuple[str, Optional[int], int] = ("", None, 0)   # destino, mejor distancia, propuestas sin bajar
        self._costes_unidad: Dict[Tuple[int, str], float] = {}           # (latido, objeto) -> pasos para una unidad
        self._lote_en_curso: Optional[Tuple[str, frozenset]] = None       # 14.2: (estación, metas) del lote elegido
        self._rutas_mapa: Dict[Tuple[int, str, frozenset], Optional[Paso]] = {}   # (latido, clase, aparcados) -> paso por el mapa

    def _excluir(self, ctx: Contexto) -> frozenset:
        return frozenset(d for d, hasta in self._aparcados.items() if ctx.latido < hasta)

    def _vigilar(self, ctx: Contexto, paso: Paso) -> None:
        """Antibloqueo general: si las últimas ``SIN_ACERCARSE`` propuestas fueron MOVER hacia el mismo destino y la
        distancia no ha bajado, ese destino queda aparcado ``APARCAR`` latidos."""
        if paso.verbo != Verbo.MOVER or not paso.destino:
            self._seguimiento = ("", None, 0)
            return
        destino, mejor_d, n = self._seguimiento
        if destino != paso.destino:
            self._seguimiento = (paso.destino, paso.distancia, 0)
            return
        if paso.distancia is not None and (mejor_d is None or paso.distancia < mejor_d):
            self._seguimiento = (destino, paso.distancia, 0)
            return
        n += 1
        if n >= self.SIN_ACERCARSE:
            self._aparcados[destino] = ctx.latido + self.APARCAR
            self._seguimiento = ("", None, 0)
        else:
            self._seguimiento = (destino, mejor_d, n)

    @staticmethod
    def _requisitos(ctx: Contexto) -> Optional[Requisitos]:
        if ctx.memoria.tiene_seccion("requisitos"):
            return cast(Requisitos, ctx.memoria.seccion("requisitos"))
        return None

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        req = self._requisitos(ctx)
        metas = req.metas if req is not None else {}
        return bool(ctx.con_experiencia) and (any(not m.conseguida and m.verbo in self.VERBOS_PLAN for m in metas.values())
                                              or bool(self._peticiones(ctx, inventario(ctx))))

    @staticmethod
    def _peticiones(ctx: Contexto, inv: Dict[str, float]) -> List[Pieza]:
        """Metas instrumentales pendientes (piezas ``Peticion`` de este latido): lo pedido que aún no se tiene."""
        return [p for _, p in sorted(ctx.onda.ef("Peticion").items()) if inv.get(str(p.carga["objeto"]), 0.0) < float(p.carga["cantidad"])]

    def conseguir(self, ctx: Contexto, objeto: str, inv: Dict[str, float]) -> Optional[Paso]:
        """Primer paso del plan más barato para tener una unidad más de ``objeto``: la mejor de las acciones cuyo efecto
        lo da (requisitos), resuelta hacia atrás como cualquier carencia de inventario. None si nada lo da."""
        req = self._requisitos(ctx)
        reqs = req.requisitos if req is not None else {}
        productoras = sorted((k for k, q in reqs.items() if q.efecto.get(objeto, 0) > 0),
                             key=lambda k: (k[0].value, k[1]))
        pasos = [p for p in (self._resolver(ctx, k, inv, frozenset(), 0) for k in productoras) if p is not None]
        return min(pasos, key=lambda q: q.coste) if pasos else None

    def decidir(self, ctx: Contexto, estrategia: Optional[Pieza] = None) -> None:
        inv = inventario(ctx)
        mejor_paso: Optional[Paso] = None
        meta_mejor = ""
        resueltas: List[Tuple[Verbo, str]] = []
        req = self._requisitos(ctx)
        metas = req.metas if req is not None else {}
        for meta in metas.values():
            if meta.conseguida or meta.verbo not in self.VERBOS_PLAN:
                continue
            paso = self._resolver(ctx, (meta.verbo, meta.objetivo), inv, frozenset(), 0)
            if paso is None:
                continue
            resueltas.append((meta.verbo, meta.objetivo))
            if mejor_paso is None or paso.coste < mejor_paso.coste:
                mejor_paso, meta_mejor = paso, meta.objetivo
        if mejor_paso is not None:
            # Deuda 14.2: un lote en curso sigue hasta tener todo su material junto a la estación (o hasta dejar de valer);
            # uno nuevo se elige si su coste por meta es menor que el de la meta suelta más barata.
            lote = self._mejor_lote(ctx, resueltas, inv, self._lote_en_curso) if self._lote_en_curso else None
            if lote is None:
                self._lote_en_curso = None
                lote = self._mejor_lote(ctx, resueltas, inv)
                if lote is not None and lote[1] >= mejor_paso.coste:
                    lote = None
            if lote is not None:
                mejor_paso, meta_mejor = lote[0], lote[2]
                self._lote_en_curso = lote[3]
        if mejor_paso is not None:
            self._vigilar(ctx, mejor_paso)
            motivo = "metas: " + meta_mejor + "".join(f" ← {m}" for m in mejor_paso.motivo)
            self.proponer(ctx, mejor_paso.verbo, mejor_paso.objetivo, self.AROUSAL, mejor_paso.confianza, motivo,
                          clase=mejor_paso.clase, **mejor_paso.datos)
        else:
            self._explorar_efectos(ctx)
        self._atender_peticiones(ctx, inv)

    def _atender_peticiones(self, ctx: Contexto, inv: Dict[str, float]) -> None:
        """Metas instrumentales (``Peticion``): para cada objeto pedido que falta, el primer paso para conseguirlo, con el
        arousal de quien lo pide (la urgencia de su impulso). Compite en el Tribunal con lo demás."""
        for p in self._peticiones(ctx, inv):
            objeto = str(p.carga["objeto"])
            sin = {**inv, objeto: 0.0}        # una unidad más, aunque ya se tenga alguna
            paso = self.conseguir(ctx, objeto, sin)
            if paso is None:
                continue
            motivo = f"{p.carga['origen']}: pide {objeto}" + "".join(f" ← {m}" for m in paso.motivo)
            if p.carga.get("motivo"):
                motivo += f" · {p.carga['motivo']}"
            self.proponer(ctx, paso.verbo, paso.objetivo, float(p.carga["urgencia"]), paso.confianza, motivo,
                          clase=paso.clase, **paso.datos)

    def _resolver(self, ctx: Contexto, accion: Tuple[Verbo, str], inv: Dict[str, float], visitado: frozenset,
                  prof: int) -> Optional[Paso]:
        req = self._requisitos(ctx)
        bloqueada = req.bloqueada(*accion) if req is not None else False
        if prof > self.PROFUNDIDAD or accion in visitado or bloqueada:
            return None
        visitado = visitado | {accion}
        r = req.requisitos.get(accion) if req is not None else None
        faltan_inv = {k: (n or 1) - inv.get(k, 0.0) for k, n in (r.requiere_inventario if r else {}).items()
                      if inv.get(k, 0.0) < (n or 1)}
        faltan_cerca = []
        for c in sorted(r.requiere_cerca if r else ()):
            if r is None or not any(r.cerca_basta(c, d, ctx.espacio) for d in desplazamientos_a_clase(ctx, c)):
                faltan_cerca.append(c)
        if not faltan_inv and not faltan_cerca:
            return self._ejecutar(ctx, accion, r)
        # Cada carencia necesita su propio plan; si alguna no lo tiene, la acción no es alcanzable. Se ejecuta
        # primero la carencia más barata y el coste es la suma de todas.
        planes: List[Paso] = []

        def mejor_de(opciones: List[Optional[Paso]], texto: str) -> Optional[Paso]:
            validas = [p for p in opciones if p is not None]
            if not validas:
                return None
            p = min(validas, key=lambda q: q.coste)
            p.coste += 1.0
            p.motivo.insert(0, texto)
            return p

        for item in sorted(faltan_inv):
            productoras = sorted((k for k, q in (req.requisitos if req else {}).items() if q.efecto.get(item, 0) > 0), key=lambda k: (k[0].value, k[1]))
            p = mejor_de([self._resolver(ctx, k, inv, visitado, prof + 1) for k in productoras], f"falta {item}")
            if p is None:
                return None
            planes.append(p)
        for clase in faltan_cerca:
            # Ir a una que se ve o se recuerda (mapa local, con el coste de la ruta) frente a producir otra, con el coste de
            # reponer lo que consume. Así no se coloca una nueva mientras ir a la conocida cueste menos.
            colocadoras = sorted((k for k, q in (req.requisitos if req else {}).items() if clase in q.aparece), key=lambda k: (k[0].value, k[1]))
            confianza = r.confianza if r else 0.5
            opciones = [acercarse_a_clase(ctx, clase, confianza, self._excluir(ctx)), self._por_el_mapa(ctx, clase, confianza)]
            opciones += [self._con_consumo(ctx, k, self._resolver(ctx, k, inv, visitado, prof + 1), inv, visitado, prof)
                         for k in colocadoras]
            p = mejor_de(opciones, f"falta cerca {clase}")
            if p is None:
                return None
            planes.append(p)
        # Primero lo que se lleva (inventario) y después el sitio: ir junto a algo antes de tener lo que se usa allí obliga a
        # volver. El coste cuenta todas las carencias.
        primero = min(planes[:len(faltan_inv)] or planes, key=lambda q: q.coste)
        primero.coste = sum(q.coste for q in planes)
        return primero

    def _con_consumo(self, ctx: Contexto, accion: Tuple[Verbo, str], paso: Optional[Paso], inv: Dict[str, float],
                     visitado: frozenset, prof: int) -> Optional[Paso]:
        """Producir algo cuesta también reponer lo que consume: lo que su efecto aprendido resta del inventario
        (``Requisito.efecto`` negativo), por el coste de conseguir cada unidad. Sin experiencia de su efecto, nada."""
        req = self._requisitos(ctx)
        r = req.requisitos.get(accion) if req is not None else None
        if paso is None or r is None:
            return paso
        for k, d in sorted(r.efecto.items()):
            if d < 0:
                paso.coste += -d * self._coste_unidad(ctx, k, inv, visitado | {accion}, prof + 1)
        return paso

    def _coste_unidad(self, ctx: Contexto, objeto: str, inv: Dict[str, float], visitado: frozenset, prof: int) -> float:
        """Pasos estimados para conseguir una unidad de ``objeto`` desde cero (el plan más barato de sus productoras)."""
        clave = (ctx.latido, objeto)
        if clave not in self._costes_unidad:
            if len(self._costes_unidad) > 200:
                self._costes_unidad.clear()
            sin = {**inv, objeto: 0.0}
            req = self._requisitos(ctx)
            reqs = req.requisitos if req is not None else {}
            productoras = sorted((k for k, q in reqs.items() if q.efecto.get(objeto, 0) > 0),
                                 key=lambda k: (k[0].value, k[1]))
            pasos = [q for q in (self._resolver(ctx, k, sin, visitado, prof) for k in productoras) if q is not None]
            self._costes_unidad[clave] = min(q.coste for q in pasos) + 1.0 if pasos else ctx.perfil.escala.coste_sin_productor
        return self._costes_unidad[clave]

    # --- deuda 14.2: metas que comparten una estación, planificadas en lote ---------------------------------------
    def _mejor_lote(self, ctx: Contexto, resueltas: List[Tuple[Verbo, str]], inv: Dict[str, float],
                    solo: Optional[Tuple[str, frozenset]] = None) -> Optional[Tuple[Paso, float, str, Tuple[str, frozenset]]]:
        """El lote más barato por meta (paso, coste por meta, nombre, (estación, metas)). Un lote son las metas resueltas
        que piden estar cerca de una misma clase X y de ninguna otra, y cuyo material se consigue sin estar cerca de nada.
        Su coste es conseguir todo el material del lote, más ir a X (o colocarla, con su material), más una acción por
        meta; se reparte entre las metas. El primer paso es el material («primero lo que se lleva»); con todo, ir a X o
        colocarla; con todo y junto a X, ninguno (lo hacen las metas sueltas). ``solo``: el lote en curso (su estación
        y, de sus metas, las que siguen valiendo)."""
        req = self._requisitos(ctx)
        reqs = req.requisitos if req is not None else {}
        estaciones = sorted({c for k in resueltas if (r := reqs.get(k)) is not None for c in r.requiere_cerca})
        if solo is not None:
            estaciones = [x for x in estaciones if x == solo[0]]
        mejor_lote: Optional[Tuple[Paso, float, str, Tuple[str, frozenset]]] = None
        for x in estaciones:
            lote = [k for k in resueltas if (r := reqs.get(k)) is not None and r.requiere_cerca == {x}
                    and (solo is None or k in solo[1])
                    and all(inv.get(i, 0.0) >= _cantidad(r, i) or self._de_campo(ctx, i, inv, 0) for i in r.requiere_inventario)]
            if len(lote) < 2:
                continue
            material: Dict[str, float] = {}
            for k in lote:
                r = reqs[k]
                for i in r.requiere_inventario:
                    material[i] = material.get(i, 0.0) + _cantidad(r, i)
            r0 = reqs[lote[0]]
            cerca_ya = any(r0.cerca_basta(x, d, ctx.espacio) for d in desplazamientos_a_clase(ctx, x))
            # Opciones para la estación: (paso si ya se tiene el material, coste, material propio).
            opciones: List[Tuple[Optional[Paso], float, Dict[str, float]]] = []
            if cerca_ya:
                opciones.append((None, 0.0, {}))
            else:
                excluir = self._excluir(ctx)
                for ir in (acercarse_a_clase(ctx, x, r0.confianza, excluir), ir_por_el_mapa(ctx, x, r0.confianza, excluir)):
                    if ir is not None:
                        opciones.append((ir, ir.coste, {}))
                for k in sorted((k for k, q in reqs.items() if x in q.aparece), key=lambda k: (k[0].value, k[1])):
                    rk = reqs[k]
                    if rk.requiere_cerca or (req.bloqueada(*k) if req else False):
                        continue
                    propio = {i: _cantidad(rk, i) for i in rk.requiere_inventario}
                    tasa = req.tasa_estimada(*k) if req else 1.0
                    opciones.append((self._colocar(ctx, k, inv, propio, material), 1.0 / max(tasa, 1e-6), propio))
            for paso_est, coste_est, propio in opciones:
                total = dict(material)
                for i, n in propio.items():
                    total[i] = total.get(i, 0.0) + n
                conseguir = self._coste_material(ctx, total, inv)
                if conseguir is None:
                    continue
                coste_mat, primero = conseguir
                paso = primero if primero is not None else paso_est
                if paso is None:              # todo a mano y junto a X: lo hace la meta suelta, que es más barata
                    continue
                por_meta = (coste_mat + coste_est + len(lote)) / len(lote)
                if mejor_lote is None or por_meta < mejor_lote[1]:
                    nombre = f"lote {x} ({', '.join(k[1] for k in lote)})"
                    mejor_lote = (Paso(paso.verbo, paso.objetivo, paso.clase, por_meta, paso.confianza, list(paso.motivo),
                                       dict(paso.datos), paso.destino, paso.distancia), por_meta, nombre, (x, frozenset(lote)))
        return mejor_lote

    def _colocar(self, ctx: Contexto, accion: Tuple[Verbo, str], inv: Dict[str, float], propio: Dict[str, float],
                 material: Dict[str, float]) -> Optional[Paso]:
        """El paso de colocar la estación, solo si ya se lleva su material y el del lote (si no, primero el material)."""
        if any(inv.get(i, 0.0) < propio.get(i, 0.0) + material.get(i, 0.0) for i in set(propio) | set(material)):
            return None
        return self._resolver(ctx, accion, inv, frozenset(), 0)

    def _coste_material(self, ctx: Contexto, total: Dict[str, float],
                        inv: Dict[str, float]) -> Optional[Tuple[float, Optional[Paso]]]:
        """Coste de reunir ``total`` (la primera unidad que falta de cada objeto por su mejor plan, el resto por el coste
        de una unidad) y el primer paso: el plan más barato de lo que falta. None si algo no se sabe conseguir."""
        coste, primero = 0.0, None
        for i in sorted(total):
            falta = total[i] - inv.get(i, 0.0)
            if falta <= 0:
                continue
            plan = self.conseguir(ctx, i, inv)
            if plan is None:
                return None
            coste += plan.coste + 1.0 + (falta - 1.0) * self._coste_unidad(ctx, i, inv, frozenset(), 0)
            if primero is None or plan.coste < primero.coste:
                primero = plan
                primero.motivo.insert(0, f"falta {i}")
        return coste, primero

    def _de_campo(self, ctx: Contexto, objeto: str, inv: Dict[str, float], prof: int) -> bool:
        """Si ``objeto`` se consigue sin estar cerca de nada: alguna acción que lo da no pide cercanía y lo que pide se lleva
        o es también de campo (hasta 3 niveles)."""
        if prof > 3:
            return False
        req = self._requisitos(ctx)
        if req is not None:
            for q in req.requisitos.values():
                if q.efecto.get(objeto, 0) > 0 and not q.requiere_cerca and not req.bloqueada(q.verbo, q.objetivo):
                    if all(inv.get(i, 0.0) >= _cantidad(q, i) or (i != objeto and self._de_campo(ctx, i, inv, prof + 1))
                           for i in q.requiere_inventario):
                        return True
        return False

    def _por_el_mapa(self, ctx: Contexto, clase: str, confianza: float) -> Optional[Paso]:
        """``ir_por_el_mapa`` con caché por latido (el planificador la pide muchas veces por latido). Devuelve una copia."""
        clave = (ctx.latido, clase, self._excluir(ctx))
        if clave not in self._rutas_mapa:
            if len(self._rutas_mapa) > 200:
                self._rutas_mapa.clear()
            self._rutas_mapa[clave] = ir_por_el_mapa(ctx, clase, 0.5, clave[2])
        q = self._rutas_mapa[clave]
        return None if q is None else Paso(q.verbo, q.objetivo, q.clase, q.coste, confianza, list(q.motivo), dict(q.datos), q.destino, q.distancia)

    def _ejecutar(self, ctx: Contexto, accion: Tuple[Verbo, str], r: Any) -> Optional[Paso]:
        verbo, objetivo = accion
        confianza = float(r.confianza) if r is not None else 0.5
        # Coste en intentos: 1 / tasa estimada. El primer intento ya cuenta como el paso (coste 0, como cualquier
        # acción que siempre funciona); se suman los fallos esperados antes del éxito, 1 / tasa − 1.
        req = self._requisitos(ctx)
        tasa = req.tasa_estimada(verbo, objetivo) if req is not None else 1.0
        penal = 1.0 / max(tasa, 1e-6) - 1.0
        texto = f"{verbo.value} {objetivo}"
        if verbo == Verbo.USAR:
            d = delante(ctx)
            if r is not None and d is not None and d["clase"] in r.delante_fallido and r.requiere_delante:
                sitio = mejor([lugar for lugar in lugares(ctx) if lugar.rasgo("peligro") < 0.5], lambda lugar: lugar.rasgo("novedad"))
                if sitio is None:
                    return None
                return Paso(Verbo.MOVER, sitio.id, sitio.clase, 2.0 + penal, confianza, [texto, f"no sirve delante {d['clase']}"])
            return Paso(Verbo.USAR, objetivo, objetivo, penal, confianza, [texto], {"receta": objetivo})
        d = delante(ctx)
        if d is not None and d["clase"] == objetivo:
            return Paso(verbo, str(d["id"]), objetivo, penal, confianza, [texto])
        instancias = [p for p in _cosas(ctx) if p.clase == objetivo]
        cerca = [p for p in instancias if al_alcance(p)]
        if cerca:
            p = max(cerca, key=lambda q: q.rasgo("proximidad"))
            return Paso(verbo, p.id, objetivo, penal, confianza, [texto])
        # Deuda 11c: ir a por ello a lo visible, a lo que recuerda la memoria topológica o a un sitio recordado del mapa del cuerpo
        # local de la que sale (p. ej. el material de un cierre o de un lote), la de menor coste.
        opciones = [q for q in (acercarse_a_clase(ctx, objetivo, confianza, self._excluir(ctx)),
                                self._por_el_mapa(ctx, objetivo, confianza)) if q is not None]
        ir = min(opciones, key=lambda q: q.coste) if opciones else None
        if ir is not None:
            ir.coste += penal
            ir.motivo.insert(0, texto)
        return ir

    def _explorar_efectos(self, ctx: Contexto) -> None:
        """5.2 c: balbuceo motor. Con calma (nada peligroso a la vista) y cada ``CADA_EXPLORACION`` latidos,
        COGER sobre lo que hay delante si en esta vida aún no se ha probado."""
        if ctx.latido % self.CADA_EXPLORACION or any(p.rasgo("peligro") > 0.0 for p in _cosas(ctx)):
            return
        d = delante(ctx)
        if d is None:
            return
        clave = (Verbo.COGER, str(d["clase"]))
        req = self._requisitos(ctx)
        reqs = req.requisitos if req is not None else {}
        intentos = req.intentos if req is not None else {}
        if clave in reqs or clave in intentos:
            return
        self.proponer(ctx, Verbo.COGER, str(d["id"]), 0.3, 0.5, f"metas: probar a coger {d['clase']} (sin plan)", clase=str(d["clase"]))
