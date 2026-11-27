// Antesala (O1, O8, O16, O17): elegir mundo (e instalarlo si falta), carácter y los detalles de la vida, y lanzarla.
// T4b (O9, sección 13): en el paso 3, «Tu compañero»: continuar con él, adoptar de la colección o empezar de cero (la
// estirpe se archiva, no se borra). Cargar una ficha pasa a ser «Importar a la colección».
// Web Component <ida-antesala> con DOM normal (comparte la hoja de estilo de la aplicación).

import { api, escuchar } from '../api.js';
import { t, texto } from '../i18n.js';
import { conectarOpciones, esAvanzada, htmlOpciones } from '../componentes/opciones.js';
import { radar } from '../componentes/radar.js';
import { almacen, avisar, esc, ICONO_CHECK } from '../componentes/util.js';

const SPRITES = {
  crafter: 'crafter/player-down.png',
  minimo: 'minimo/yo.svg',
  archivos: 'archivos/brote.svg',
  snake: 'snake/yo_este.svg',
};
const GLIFOS = { ajedrez: '♞' };
const COLLAGE_CRAFTER = ['tree', 'grass', 'cow', 'water', 'player-down', 'stone', 'sand', 'table', 'diamond'];
// Duración y generaciones sugeridas por mundo (las de la antesala de siempre).
const SUGERIDOS = {
  minimo: { latidos: 400, generaciones: 3 },
  archivos: { latidos: 400, generaciones: 3 },
  // O8: 10 000 = un episodio de la medición oficial; la vida termina antes si IdA muere.
  crafter: { latidos: 10000, generaciones: 3 },
  ajedrez: { latidos: 150, generaciones: 2 },
  snake: { latidos: 1000, generaciones: 3 },
};
const ESTADO_CHIP = { listo: 'listo', sin_stockfish: 'listo', falta_navegador: 'aviso', no_instalado: 'falta' };
const GUARDADO = 'ida.antesala';

function spriteHtml(mundo, clase = 'sprite') {
  if (GLIFOS[mundo]) return `<div class="${clase} texto" aria-hidden="true">${GLIFOS[mundo]}</div>`;
  const s = SPRITES[mundo];
  return `<div class="${clase}" aria-hidden="true">${s ? `<img src="/web/sprites/${s}" alt="">` : ''}</div>`;
}

class IdaAntesala extends HTMLElement {
  constructor() {
    super();
    const previo = almacen.leer(GUARDADO) || {};
    this.e = {
      paso: 1, mundos: null, presets: null, rasgos: [], rangos: {}, error: '',
      mundo: previo.mundo || 'crafter', caracter: previo.caracter || 'optimo', arquetipo: null,
      companeros: {}, coleccion: {}, origen: null, adoptarId: '', fichaError: '',
      opciones: {}, semilla: 1, latidos: 300, generaciones: 1, sin_experiencia: false, grabar: false, otel: false,
      instalaciones: {}, lanzando: false, errorLanzar: '',
    };
    this._alIdioma = () => this.pintar();
  }

  connectedCallback() {
    document.addEventListener('ida:idioma', this._alIdioma);
    this.pintar();
    this.cargar();
  }

  disconnectedCallback() {
    document.removeEventListener('ida:idioma', this._alIdioma);
    for (const i of Object.values(this.e.instalaciones)) if (i.cerrar) i.cerrar();
  }

  // --- datos ---------------------------------------------------------------------------------------------------------
  async cargar() {
    this.e.error = '';
    try {
      const [m, p, c] = await Promise.all([api.mundos(), this.e.presets ? null : api.presets(), api.companeros()]);
      this.e.mundos = m.mundos;
      this.e.observabilidad = Boolean(m.observabilidad);
      this.e.companeros = Object.fromEntries(c.companeros.map((x) => [x.mundo, x]));
      if (p) { this.e.presets = p.presets; this.e.rasgos = p.rasgos; this.e.rangos = p.rangos; }
      for (const mundo of this.e.mundos) {             // una instalación que siguió mientras no se veía la página
        const inst = mundo.instalacion;
        if (inst && inst.estado === 'en_curso' && !this.e.instalaciones[mundo.nombre]) this.seguirInstalacion(mundo.nombre, inst.id);
      }
      if (!this.mundo()) this.e.mundo = 'crafter';
      this.elegirMundo(this.e.mundo, false);
      await this.cargarColeccion();
    } catch (err) {
      this.e.error = t(`error.${err.codigo || 'red'}`);
    }
    this.pintar();
  }

  /** Lo que se puede adoptar en el mundo elegido: sus fichas y estirpes archivadas, por mejor Score. */
  async cargarColeccion(mundo = this.e.mundo) {
    try {
      const r = await api.coleccion(mundo);
      this.e.coleccion[mundo] = (r.ranking[mundo] || []).filter((x) => x.tipo !== 'companero');
    } catch { this.e.coleccion[mundo] = []; }
    if (this.e.adoptarId && !this.e.coleccion[mundo].some((x) => x.id === this.e.adoptarId)) this.e.adoptarId = '';
  }

  companero(mundo = this.e.mundo) {
    const c = this.e.companeros[mundo];
    return c && c.existe ? c : null;
  }

  /** De dónde sale la estirpe de esta vida: «continuar» (por defecto si hay compañero), «adoptar» o «cero». */
  origen() {
    const e = this.e;
    if (e.origen === 'continuar' && !this.companero()) return 'cero';
    return e.origen || (this.companero() ? 'continuar' : 'cero');
  }

  mundo(nombre = this.e.mundo) {
    return (this.e.mundos || []).find((m) => m.nombre === nombre) || null;
  }

  elegirMundo(nombre, pintar = true) {
    const m = this.mundo(nombre);
    if (!m) return;
    const cambia = nombre !== this.e.mundoOpciones;
    this.e.mundo = nombre;
    if (cambia && m.opciones) {
      this.e.opciones = Object.fromEntries(m.opciones.map((d) => [d.nombre, d.defecto]));
      this.e.mundoOpciones = nombre;
      const s = SUGERIDOS[nombre] || { latidos: 300, generaciones: 1 };
      this.e.latidos = s.latidos;
      this.e.generaciones = s.generaciones;
      this.e.origen = null;
      this.e.adoptarId = '';
      this.e.fichaError = '';
      if (this.e.coleccion[nombre] === undefined && this.e.mundos) this.cargarColeccion(nombre).then(() => { if (this.e.paso === 3) this.pintar(); });
    }
    this.guardar();
    if (pintar) this.pintar();
  }

  guardar() {
    almacen.guardar(GUARDADO, { mundo: this.e.mundo, caracter: this.e.caracter });
  }

  arquetipoActual() {
    const e = this.e;
    if (e.caracter === 'personalizado') return e.arquetipo;
    const p = (e.presets || []).find((x) => x.id === e.caracter);
    if (!p) return null;
    if (p.por_mundo) return p.por_mundo[e.mundo] || null;
    return p.arquetipo;
  }

  nombreCaracter() {
    const e = this.e;
    if (e.caracter === 'personalizado') return t('caracter.personalizado');
    const p = (e.presets || []).find((x) => x.id === e.caracter);
    return p ? `${p.icono} ${texto(p.nombre)}` : '';
  }

  // --- instalación ---------------------------------------------------------------------------------------------------
  async instalar(nombre) {
    try {
      const r = await api.instalar(nombre);
      this.seguirInstalacion(nombre, r.instalacion.id);
    } catch (err) {
      avisar(t(`error.${err.codigo || 'red'}`));
    }
  }

  seguirInstalacion(nombre, id) {
    const inst = { id, lineas: [], estado: 'en_curso', codigo: null, cerrar: null };
    this.e.instalaciones[nombre] = inst;
    this.pintarInstalacion(nombre);
    inst.cerrar = escuchar(`instalaciones/${encodeURIComponent(id)}`, {
      linea: (d) => { inst.lineas.push(d.texto); this.pintarInstalacion(nombre, d.texto); },
      fin: async (d) => {
        inst.cerrar();
        inst.estado = d.estado;
        inst.codigo = d.codigo;
        const etiqueta = t(`mundo.${nombre}.nombre`);
        if (d.estado === 'ok') avisar(t('mundo.instalado', { mundo: etiqueta }));
        else avisar(t('mundo.fallo_instalar', { mundo: etiqueta, codigo: d.codigo ?? '–' }));
        try { this.e.mundos = (await api.mundos()).mundos; } catch { /* se queda lo que había */ }
        if (d.estado === 'ok') this.elegirMundo(nombre, false);
        this.pintar();
      },
    });
  }

  /** Actualiza solo la zona de instalación de una tarjeta (la salida llega línea a línea). */
  pintarInstalacion(nombre, linea) {
    const zona = this.querySelector(`[data-instalacion="${CSS.escape(nombre)}"]`);
    if (!zona) return;
    const inst = this.e.instalaciones[nombre];
    if (linea !== undefined && zona.querySelector('.salida')) {
      const pre = zona.querySelector('.salida');
      const abajo = pre.scrollTop + pre.clientHeight >= pre.scrollHeight - 8;
      pre.textContent += (pre.textContent ? '\n' : '') + linea;
      if (abajo) pre.scrollTop = pre.scrollHeight;
      zona.querySelector('[data-lineas]').textContent = t('mundo.lineas', { n: inst.lineas.length });
      return;
    }
    zona.innerHTML = this.htmlInstalacion(nombre);
  }

  htmlInstalacion(nombre) {
    const inst = this.e.instalaciones[nombre];
    if (!inst) return '';
    const clase = inst.estado === 'ok' ? 'ok' : inst.estado === 'error' ? 'error' : '';
    const abierto = inst.estado === 'error' ? 'open' : '';
    return `<div class="barra-progreso ${clase}" role="progressbar" aria-label="${esc(t('mundo.instalando'))}" ${inst.estado === 'en_curso' ? 'aria-busy="true"' : ''}><i></i></div>
      <details ${abierto}><summary>${esc(t('mundo.ver_salida'))} · <span data-lineas>${esc(t('mundo.lineas', { n: inst.lineas.length }))}</span></summary>
      <pre class="salida">${esc(inst.lineas.join('\n'))}</pre></details>`;
  }

  // --- pintado -------------------------------------------------------------------------------------------------------
  pintar() {
    const e = this.e;
    const pasos = [['paso.mundo', 1], ['paso.caracter', 2], ['paso.empezar', 3]];
    const progreso = pasos.map(([clave, n], i) => {
      const estado = n < e.paso ? 'hecho' : n === e.paso ? 'actual' : '';
      const tallo = i < pasos.length - 1 ? `<span class="tallo ${n < e.paso ? 'lleno' : ''}" aria-hidden="true"><i></i></span>` : '';
      return `<li class="${estado}"><button type="button" data-ir="${n}" ${n > e.paso ? 'disabled' : ''} ${n === e.paso ? 'aria-current="step"' : ''}>
        <span class="bola">${n < e.paso ? ICONO_CHECK : n}</span><span>${esc(t(clave))}</span></button></li>${tallo ? `<li aria-hidden="true">${tallo}</li>` : ''}`;
    }).join('');
    let cuerpo;
    if (e.error) {
      cuerpo = `<div class="aviso-caja" role="alert">${esc(t('mundos.error'))} ${esc(e.error)}
        <button type="button" class="boton pequeno" data-accion="recargar">${esc(t('mundos.reintentar'))}</button></div>`;
    } else if (!e.mundos || !e.presets) {
      cuerpo = `<p class="suave">${esc(t('mundos.cargando'))}</p>`;
    } else if (e.paso === 1) {
      cuerpo = this.htmlPaso1();
    } else if (e.paso === 2) {
      cuerpo = this.htmlPaso2();
    } else {
      cuerpo = this.htmlPaso3();
    }
    this.innerHTML = `
      <div class="antesala-cabeza">
        <div><h1>${esc(t('antesala.titulo'))}</h1><p>${esc(t('antesala.subtitulo'))}</p></div>
        <nav aria-label="${esc(t('antesala.progreso'))}"><ol class="pasos">${progreso}</ol></nav>
      </div>
      <section aria-live="polite">${cuerpo}</section>`;
    this.conectar();
  }

  htmlPaso1() {
    const e = this.e;
    const tarjetas = e.mundos.map((m) => {
      const elegido = m.nombre === e.mundo;
      const inst = e.instalaciones[m.nombre];
      const instalando = inst && inst.estado === 'en_curso';
      const chips = [
        m.estrella ? `<span class="chip estrella">★ ${esc(t('mundo.estrella'))}</span>` : '',
        `<span class="chip ${ESTADO_CHIP[m.estado] || ''}">${esc(t(`estado.${m.estado}`))}</span>`,
        m.tiempo_real ? `<span class="chip sin-punto">⏱ ${esc(t('mundo.tiempo_real'))}</span>` : '',
      ].join('');
      const necesita = m.extra && (m.estado === 'no_instalado' || m.estado === 'falta_navegador');
      const botonInstalar = necesita ? `<button type="button" class="boton pequeno ${m.lanzable ? '' : 'primario'}" data-instalar="${esc(m.nombre)}"
          ${instalando ? 'disabled' : ''} title="${esc(t('mundo.instala_extra', { extra: m.extra }))}">
          ${esc(instalando ? t('mundo.instalando') : inst && inst.estado === 'error' ? t('mundo.reintentar_instalar') : t('mundo.instalar'))}</button>` : '';
      const botonElegir = m.lanzable ? `<button type="button" class="boton pequeno ${elegido ? 'primario' : ''}" data-elegir="${esc(m.nombre)}"
          aria-pressed="${elegido}">${esc(elegido ? t('mundo.elegido') : t('mundo.elegir'))}</button>` : '';
      const ayuda = m.estado !== 'listo' ? `<small class="suave">${esc(t(`estado.ayuda.${m.estado}`))}</small>` : '';
      const collage = m.estrella ? `<div class="collage" aria-hidden="true">${COLLAGE_CRAFTER.map((s) => `<img src="/web/sprites/crafter/${s}.png" alt="">`).join('')}</div>` : '';
      return `<article class="tarjeta mundo ${m.estrella ? 'estrella' : ''}" data-mundo="${esc(m.nombre)}" data-elegido="${elegido}" data-lanzable="${m.lanzable}">
        <span class="marca-elegido" aria-hidden="true">${ICONO_CHECK}</span>
        ${collage}
        <div class="mundo-cuerpo">
          <div class="mundo-arriba">${m.estrella ? '' : spriteHtml(m.nombre)}<div><h3>${esc(t(`mundo.${m.nombre}.nombre`))}</h3></div></div>
          <div class="chips">${chips}</div>
          <p class="desc">${esc(t(`mundo.${m.nombre}.desc`))}</p>
          <div class="pie">${botonElegir}${botonInstalar}${ayuda}</div>
          <div class="instalacion" data-instalacion="${esc(m.nombre)}">${this.htmlInstalacion(m.nombre)}</div>
        </div>
      </article>`;
    }).join('');
    const listo = this.mundo() && this.mundo().lanzable;
    return `<div class="paso-titulo"><h2 tabindex="-1">${esc(t('mundos.titulo'))}</h2><p>${esc(t('mundos.pista'))}</p></div>
      <div class="mundos">${tarjetas}</div>
      <div class="pie-pasos"><span class="suave">${esc(t('antesala.paso_de', { n: 1 }))}${listo ? '' : ` · ${esc(t('mundos.elige_uno'))}`}</span>
        <button type="button" class="boton primario" data-ir="2" ${listo ? '' : 'disabled'}>${esc(t('antesala.siguiente'))} →</button></div>`;
  }

  htmlPaso2() {
    const e = this.e;
    const rasgos = e.rasgos;
    const tarjeta = (id, icono, nombre, desc, arq) => `<button type="button" role="radio" class="tarjeta preset" data-preset="${esc(id)}" aria-checked="${e.caracter === id}"
        tabindex="${e.caracter === id ? '0' : '-1'}">
        <span class="icono" aria-hidden="true">${icono}</span><b>${esc(nombre)}</b>
        ${radar(arq, rasgos, { titulo: nombre })}
        <small>${esc(desc)}</small></button>`;
    let tarjetas = e.presets.map((p) => tarjeta(p.id, p.icono, texto(p.nombre), texto(p.descripcion),
      p.por_mundo ? p.por_mundo[e.mundo] : p.arquetipo)).join('');
    if (e.caracter === 'personalizado') tarjetas += tarjeta('personalizado', '🎛️', t('caracter.personalizado'), t('caracter.personalizado_desc'), e.arquetipo);
    const arq = this.arquetipoActual();
    const valores = arq || Object.fromEntries(rasgos.map((r) => [r, (e.rangos[r].min + e.rangos[r].max) / 2]));
    const deslizadores = rasgos.map((r) => {
      const g = e.rangos[r];
      const v = Number(valores[r]).toFixed(2);
      return `<div class="rasgo"><label for="rasgo-${r}">${esc(t(`rasgo.${r}.nombre`))}<output id="salida-${r}">${v}</output></label>
        <input type="range" id="rasgo-${r}" data-rasgo="${r}" min="${g.min}" max="${g.max}" step="${g.paso}" value="${v}" aria-describedby="ayuda-${r}">
        <small id="ayuda-${r}">${esc(t(`rasgo.${r}.desc`))}</small></div>`;
    }).join('');
    const etiquetas = rasgos.map((r) => t(`rasgo.${r}.nombre`).slice(0, 5));
    return `<div class="paso-titulo"><h2 tabindex="-1">${esc(t('caracter.titulo'))}</h2><p>${esc(t('caracter.pista'))}</p></div>
      <div class="presets" role="radiogroup" aria-label="${esc(t('paso.caracter'))}">${tarjetas}</div>
      <details class="tarjeta avanzado" ${e.caracter === 'personalizado' ? 'open' : ''}>
        <summary>${esc(t('caracter.avanzado'))}</summary>
        ${arq ? '' : `<p class="suave pequeno" style="margin-bottom:12px">${esc(t('caracter.azar_nota'))}</p>`}
        <div class="rasgos"><div class="rasgos-lista">${deslizadores}</div>
          <div data-radar-grande>${radar(arq, rasgos, { etiquetas, titulo: this.nombreCaracter() })}</div></div>
      </details>
      <div class="pie-pasos"><button type="button" class="boton" data-ir="1">← ${esc(t('antesala.atras'))}</button>
        <span class="suave">${esc(t('antesala.paso_de', { n: 2 }))}</span>
        <button type="button" class="boton primario" data-ir="3">${esc(t('antesala.siguiente'))} →</button></div>`;
  }

  htmlPaso3() {
    const e = this.e;
    const m = this.mundo();
    const decl = m.opciones || [];
    const basicas = decl.filter((d) => !esAvanzada(d));
    const avanzadas = decl.filter(esAvanzada);
    const nombreMundo = t(`mundo.${m.nombre}.nombre`);
    const opciones = decl.length
      ? `<div class="opciones-mundo">${htmlOpciones(basicas, e.opciones)}</div>`
      : `<p class="suave">${esc(t('empezar.sin_opciones'))}</p>`;
    const comp = this.companero();
    const arq = this.origen() === 'continuar' && comp && comp.arquetipo ? comp.arquetipo : this.arquetipoActual();
    return `<div class="paso-titulo"><h2 tabindex="-1">${esc(t('empezar.titulo'))}</h2><p>${esc(t('empezar.pista'))}</p></div>
      <div class="empezar">
        <form id="form-vida" novalidate>
          ${this.htmlCompanero()}
          <section class="tarjeta bloque">
            <h3>${esc(t('empezar.vida'))}</h3>
            <div class="campos">
              <div class="campo"><label for="semilla">${esc(t('empezar.semilla'))}</label>
                <div class="con-boton"><input class="entrada" type="number" id="semilla" min="0" max="2147483646" step="1" value="${e.semilla}" required aria-describedby="semilla-ayuda">
                <button type="button" class="boton-icono" data-accion="azar" aria-label="${esc(t('empezar.azar'))}" title="${esc(t('empezar.azar'))}">🎲</button></div>
                <small id="semilla-ayuda">${esc(t('empezar.semilla_ayuda'))}</small></div>
              <div class="campo"><label for="latidos">${esc(t('empezar.latidos'))}</label>
                <input class="entrada" type="number" id="latidos" min="1" max="1000000" step="1" value="${e.latidos}" required aria-describedby="latidos-ayuda">
                <small id="latidos-ayuda">${esc(t('empezar.latidos_ayuda'))}</small></div>
              <div class="campo"><label for="generaciones">${esc(t('empezar.generaciones'))}</label>
                <input class="entrada" type="number" id="generaciones" min="1" max="100" step="1" value="${e.generaciones}" required aria-describedby="generaciones-ayuda">
                <small id="generaciones-ayuda">${esc(t('empezar.generaciones_ayuda'))}</small></div>
            </div>
          </section>
          <section class="tarjeta bloque">
            <div class="bloque-titulo"><h3>${esc(t('empezar.opciones_de', { mundo: nombreMundo }))}</h3>
              ${decl.length ? `<button type="button" class="boton pequeno discreto" data-accion="recomendados">↺ ${esc(t('empezar.recomendados'))}</button>` : ''}</div>
            ${opciones}
          </section>
          <details class="tarjeta bloque">
            <summary>${esc(t('empezar.avanzado'))}</summary>
            <div class="opciones-mundo">
              ${htmlOpciones(avanzadas, e.opciones)}
              <div class="campo"><label class="interruptor"><input type="checkbox" id="sin_experiencia" ${e.sin_experiencia ? 'checked' : ''}>
                <span>${esc(t('empezar.sin_experiencia'))}</span></label><small>${esc(t('empezar.sin_experiencia_ayuda'))}</small></div>
              <div class="campo"><label class="interruptor"><input type="checkbox" id="grabar" ${e.grabar ? 'checked' : ''}>
                <span>⏺ ${esc(t('empezar.grabar'))}</span></label><small>${esc(t('empezar.grabar_ayuda'))}</small></div>
              <div class="campo"><label class="interruptor"><input type="checkbox" id="otel" ${e.otel && e.observabilidad ? 'checked' : ''} ${e.observabilidad ? '' : 'disabled'}>
                <span>${esc(t('empezar.otel'))}</span></label><small>${esc(t(e.observabilidad ? 'empezar.otel_ayuda' : 'empezar.otel_sin_extra'))}
                ${e.observabilidad ? `<a href="http://localhost:3000" target="_blank" rel="noopener">Grafana</a> · <a href="http://localhost:16686" target="_blank" rel="noopener">Jaeger</a> · <a href="http://localhost:9090" target="_blank" rel="noopener">Prometheus</a>` : ''}</small></div>
            </div>
          </details>
        </form>
        <aside class="tarjeta resumen" aria-labelledby="resumen-titulo">
          <h3 id="resumen-titulo">${esc(t('resumen.titulo'))}</h3>
          ${radar(arq, e.rasgos, { titulo: this.nombreCaracter() })}
          <dl>
            <dt>${esc(t('resumen.mundo'))}</dt><dd>${spriteHtml(m.nombre)}<span>${esc(nombreMundo)}</span></dd>
            <dt>${esc(t('resumen.companero'))}</dt><dd>${esc(this.resumenCompanero())}</dd>
            <dt>${esc(t('resumen.caracter'))}</dt><dd>${esc(this.origen() === 'cero' ? this.nombreCaracter() : t('companero.caracter_heredado_corto'))}</dd>
            <dt>${esc(t('resumen.semilla'))}</dt><dd data-resumen-semilla>${e.semilla}</dd>
          </dl>
          <p class="nota"><span aria-hidden="true">${m.tiempo_real ? '⏱' : '🔁'}</span>${esc(t(m.tiempo_real ? 'resumen.tiempo_real' : 'resumen.reproducible'))}</p>
          <button type="submit" form="form-vida" class="boton vital" ${e.lanzando ? 'disabled' : ''}>
            ${esc(e.lanzando ? t('empezar.lanzando') : t('empezar.boton'))} ${e.lanzando ? '' : '<span aria-hidden="true">🌱</span>'}</button>
          <div aria-live="assertive">${e.errorLanzar ? `<p class="error-texto" role="alert">${esc(e.errorLanzar)}</p>` : ''}</div>
          <button type="button" class="boton discreto pequeno" data-ir="2">← ${esc(t('antesala.atras'))}</button>
        </aside>
      </div>`;
  }

  /** «Tu compañero» (O9): continuar, adoptar de la colección o empezar de cero (la estirpe se archiva). */
  htmlCompanero() {
    const e = this.e;
    const c = this.companero();
    const origen = this.origen();
    const lista = e.coleccion[e.mundo] || [];
    const puntos = (v) => (v == null ? '–' : String(Math.round(Number(v))));
    const opcion = (valor, titulo, ayuda, deshabilitada = false) => `<label class="opcion-companero ${origen === valor ? 'elegida' : ''}">
        <input type="radio" name="origen" value="${valor}" ${origen === valor ? 'checked' : ''} ${deshabilitada ? 'disabled' : ''}>
        <span><b>${esc(titulo)}</b><small>${esc(ayuda)}</small></span></label>`;
    const continuar = c ? opcion('continuar', t('companero.continuar'),
      t('companero.continuar_ayuda',
        { nombre: c.nombre || c.individuo, g: c.generacion + 1, n: c.generaciones, score: puntos(c.mejor_score) })) : '';
    const elegir = origen !== 'adoptar' ? '' : lista.length ? `<div class="campo"><label for="adoptar-id">${esc(t('companero.cual'))}</label>
        <select class="entrada" id="adoptar-id">
          <option value="">${esc(t('companero.elige'))}</option>
          ${lista.map((x) => `<option value="${esc(x.id)}" ${x.id === e.adoptarId ? 'selected' : ''}>${esc(`${x.tipo === 'estirpe' ? '🌳' : '🧬'} ${x.nombre} · ${t('vivero.generacion', { n: x.generacion ?? '?' })} · ${t('companero.score', { score: puntos(x.mejor_score) })}`)}</option>`).join('')}
        </select></div>` : `<p class="suave pequeno">${esc(t('companero.coleccion_vacia'))}</p>`;
    const adoptar = opcion('adoptar', t('companero.adoptar'), c ? t('companero.adoptar_ayuda') : t('companero.adoptar_ayuda_sin'), !lista.length);
    const cero = opcion('cero', c ? t('companero.cero') : t('companero.nueva'), c ? t('companero.cero_ayuda') : t('companero.nueva_ayuda'));
    const nota = origen === 'cero' ? '' : `<p class="suave pequeno">🧬 ${esc(t('companero.caracter_heredado'))}</p>`;
    return `<section class="tarjeta bloque companero-bloque" aria-labelledby="titulo-companero">
        <div class="bloque-titulo"><h3 id="titulo-companero">${esc(t('companero.titulo'))}</h3>
          <a class="boton pequeno discreto" href="#/vivero/coleccion">🗂️ ${esc(t('estirpe.coleccion'))}</a></div>
        <div class="opciones-companero" role="radiogroup" aria-labelledby="titulo-companero">${continuar}${adoptar}${cero}</div>
        ${elegir}${nota}
        <div class="ficha-fila"><label class="boton pequeno" for="ficha">📂 ${esc(t('companero.importar'))}</label>
          <input type="file" id="ficha" accept=".json,application/json" class="oculto">
          <small class="suave">${esc(t('companero.importar_ayuda'))}</small></div>
        ${e.fichaError ? `<p class="error-texto" role="alert">${esc(e.fichaError)}</p>` : ''}
      </section>`;
  }

  resumenCompanero() {
    const c = this.companero();
    const origen = this.origen();
    if (origen === 'continuar' && c) return t('companero.resumen_continuar', { nombre: c.nombre || c.individuo, g: c.generacion + 1 });
    if (origen === 'adoptar') {
      const x = (this.e.coleccion[this.e.mundo] || []).find((y) => y.id === this.e.adoptarId);
      return x ? t('companero.resumen_adoptar', { nombre: x.nombre }) : t('companero.elige');
    }
    return c ? t('companero.resumen_cero') : t('companero.resumen_nueva');
  }

  // --- eventos -------------------------------------------------------------------------------------------------------
  conectar() {
    const e = this.e;
    this.querySelectorAll('[data-ir]').forEach((b) => b.addEventListener('click', () => {
      e.paso = Number(b.dataset.ir);
      e.errorLanzar = '';
      this.pintar();
      window.scrollTo({ top: 0 });
      this.querySelector('h2')?.focus({ preventScroll: true });
    }));
    this.querySelector('[data-accion="recargar"]')?.addEventListener('click', () => this.cargar());
    // paso 1
    this.querySelectorAll('.mundo').forEach((art) => art.addEventListener('click', (ev) => {
      if (ev.target.closest('button, a, summary, pre')) return;
      if (art.dataset.lanzable === 'true') this.elegirMundo(art.dataset.mundo);
    }));
    this.querySelectorAll('[data-elegir]').forEach((b) => b.addEventListener('click', () => this.elegirMundo(b.dataset.elegir)));
    this.querySelectorAll('[data-instalar]').forEach((b) => b.addEventListener('click', () => this.instalar(b.dataset.instalar)));
    // paso 2
    this.querySelectorAll('[data-preset]').forEach((b) => b.addEventListener('click', () => {
      e.caracter = b.dataset.preset;
      if (e.caracter !== 'personalizado') e.arquetipo = null;
      this.guardar();
      this.pintar();
      this.querySelector(`[data-preset="${CSS.escape(e.caracter)}"]`)?.focus();
    }));
    // flechas, Inicio y Fin entre los presets (patrón radiogroup: el foco y la elección se mueven juntos)
    const grupo = this.querySelector('.presets[role="radiogroup"]');
    if (grupo) {
      if (!grupo.querySelector('[tabindex="0"]')) grupo.querySelector('[data-preset]')?.setAttribute('tabindex', '0');
      grupo.addEventListener('keydown', (ev) => {
        const lista = [...grupo.querySelectorAll('[data-preset]')];
        const i = lista.indexOf(document.activeElement);
        if (i < 0) return;
        const destino = { ArrowRight: i + 1, ArrowDown: i + 1, ArrowLeft: i - 1, ArrowUp: i - 1, Home: 0, End: lista.length - 1 }[ev.key];
        if (destino === undefined) return;
        ev.preventDefault();
        lista[(destino + lista.length) % lista.length].click();
      });
    }
    this.querySelectorAll('[data-rasgo]').forEach((s) => s.addEventListener('input', () => {
      const base = this.arquetipoActual() || Object.fromEntries(e.rasgos.map((r) => [r, Number(this.querySelector(`#rasgo-${r}`).value)]));
      e.arquetipo = { ...base, [s.dataset.rasgo]: Number(s.value) };
      this.querySelector(`#salida-${s.dataset.rasgo}`).textContent = Number(s.value).toFixed(2);
      const antes = e.caracter;
      e.caracter = 'personalizado';
      if (antes !== 'personalizado') {                  // aparece la tarjeta «Personalizado» sin perder el foco
        const foco = s.id;
        this.pintar();
        this.querySelector(`#${foco}`)?.focus();
        return;
      }
      const marco = this.querySelector('[data-radar-grande]');
      if (marco) marco.innerHTML = radar(e.arquetipo, e.rasgos, { etiquetas: e.rasgos.map((r) => t(`rasgo.${r}.nombre`).slice(0, 5)), titulo: this.nombreCaracter() });
      const tarjeta = this.querySelector('[data-preset="personalizado"] .radar');
      if (tarjeta) tarjeta.outerHTML = radar(e.arquetipo, e.rasgos, { titulo: t('caracter.personalizado') });
    }));
    // paso 3
    const form = this.querySelector('#form-vida');
    if (!form) return;
    const numero = (id, campo) => this.querySelector(`#${id}`).addEventListener('input', (ev) => {
      e[campo] = ev.target.value === '' ? '' : Number(ev.target.value);
      ev.target.setAttribute('aria-invalid', String(!ev.target.checkValidity()));
      if (campo === 'semilla') this.querySelector('[data-resumen-semilla]').textContent = ev.target.value;
    });
    numero('semilla', 'semilla');
    numero('latidos', 'latidos');
    numero('generaciones', 'generaciones');
    this.querySelector('[data-accion="azar"]').addEventListener('click', () => {
      e.semilla = Math.floor(Math.random() * 99999) + 1;
      this.querySelector('#semilla').value = e.semilla;
      this.querySelector('[data-resumen-semilla]').textContent = e.semilla;
    });
    this.querySelector('#sin_experiencia').addEventListener('change', (ev) => { e.sin_experiencia = ev.target.checked; });
    this.querySelector('#grabar').addEventListener('change', (ev) => { e.grabar = ev.target.checked; });   // T5a (O7)
    this.querySelector('#otel').addEventListener('change', (ev) => { e.otel = ev.target.checked; });       // T6a (O15)
    this.querySelectorAll('input[name="origen"]').forEach((r) => r.addEventListener('change', () => {
      e.origen = r.value;
      if (r.value === 'adoptar' && !e.adoptarId) e.adoptarId = ((e.coleccion[e.mundo] || [])[0] || {}).id || '';
      this.pintar();
      this.querySelector(`input[name="origen"][value="${r.value}"]`)?.focus();
    }));
    this.querySelector('#adoptar-id')?.addEventListener('change', (ev) => {
      e.adoptarId = ev.target.value;
      const dd = this.querySelectorAll('.resumen dd')[1];
      if (dd) dd.textContent = this.resumenCompanero();
    });
    conectarOpciones(form, this.mundo().opciones || [], (nombre, valor) => { e.opciones[nombre] = valor; });
    this.querySelector('[data-accion="recomendados"]')?.addEventListener('click', () => {
      e.opciones = Object.fromEntries((this.mundo().opciones || []).map((d) => [d.nombre, d.defecto]));
      this.pintar();
    });
    this.querySelector('#ficha').addEventListener('change', (ev) => this.leerFicha(ev.target.files[0]));
    form.addEventListener('submit', (ev) => { ev.preventDefault(); this.lanzar(); });
  }

  /** «Importar a la colección» (T4b): la ficha (v1 o antigua del panel) pasa a la colección y queda elegida para adoptar. */
  async leerFicha(fichero) {
    const e = this.e;
    if (!fichero) return;
    e.fichaError = '';
    let doc;
    try {
      doc = JSON.parse(await fichero.text());
      if (!doc || typeof doc !== 'object' || Array.isArray(doc)) throw new Error('forma');
    } catch {
      e.fichaError = t('empezar.ficha_error');
      this.pintar();
      return;
    }
    const de = String(doc.mundo || '').toLowerCase();
    if (de && de !== e.mundo) {
      e.fichaError = t('empezar.ficha_otro_mundo', { mundo: t(`mundo.${de}.nombre`) });
      this.pintar();
      return;
    }
    try {
      const r = await api.importar(doc);
      avisar(r.avisos && r.avisos.length ? t('coleccion.importada_avisos', { nombre: r.ficha.nombre, n: r.avisos.length })
        : t('coleccion.importada', { nombre: r.ficha.nombre }));
      await this.cargarColeccion();
      e.origen = 'adoptar';
      e.adoptarId = r.ficha.id;
    } catch (err) {
      e.fichaError = `${t(`error.${err.codigo || 'red'}`)}${err.message && err.codigo !== 'red' ? ` ${err.message}` : ''}`;
    }
    this.pintar();
  }

  cuerpoVida(reemplazar) {
    const e = this.e;
    const cuerpo = {
      mundo: e.mundo, opciones: e.opciones, semilla: e.semilla, latidos: e.latidos, generaciones: e.generaciones,
      sin_experiencia: e.sin_experiencia, tabula_rasa: this.origen() === 'cero' && Boolean(this.companero()),   // archiva, no borra
    };
    if (e.caracter === 'personalizado') cuerpo.arquetipo = e.arquetipo;
    else cuerpo.caracter = e.caracter;
    if (reemplazar) cuerpo.reemplazar = true;
    if (e.grabar) cuerpo.grabar = true;   // T5a: graba desde el primer latido, con el nivel completo
    if (e.otel && e.observabilidad) cuerpo.otel = true;   // T6a: trazas y métricas por OTLP (extra [observabilidad])
    return cuerpo;
  }

  async lanzar(reemplazar = false) {
    const e = this.e;
    const form = this.querySelector('#form-vida');
    if (form && !form.checkValidity()) {
      const malo = form.querySelector(':invalid');
      malo?.setAttribute('aria-invalid', 'true');
      malo?.focus();
      e.errorLanzar = t('error.campo_invalido');
      this.pintarError();
      return;
    }
    if (this.origen() === 'adoptar' && !e.adoptarId) {
      e.errorLanzar = t('companero.elige');
      this.pintarError();
      return;
    }
    e.lanzando = true;
    e.errorLanzar = '';
    this.pintar();
    try {
      if (this.origen() === 'adoptar') {
        // Adoptar archiva el compañero de antes (nunca lo borra). Con una vida de este mundo en marcha, primero se para.
        try {
          await api.adoptar(e.adoptarId);
        } catch (err) {
          if (err.codigo !== 'vida_en_curso' || !window.confirm(t('empezar.reemplazar'))) throw err;
          await api.parar();
          await api.adoptar(e.adoptarId);
        }
        reemplazar = true;
        e.origen = 'continuar';
        e.adoptarId = '';
      }
      await api.lanzar(this.cuerpoVida(reemplazar));
      e.lanzando = false;
      location.hash = '#/vivero';
    } catch (err) {
      e.lanzando = false;
      if (err.codigo === 'vida_en_curso' && window.confirm(t('empezar.reemplazar'))) return this.lanzar(true);
      e.errorLanzar = `${t(`error.${err.codigo || 'red'}`)}${err.message && err.codigo !== 'red' ? ` ${err.message}` : ''}`;
      this.pintar();
    }
  }

  pintarError() {
    const zona = this.querySelector('.resumen [aria-live]');
    if (zona) zona.innerHTML = this.e.errorLanzar ? `<p class="error-texto" role="alert">${esc(this.e.errorLanzar)}</p>` : '';
  }
}

customElements.define('ida-antesala', IdaAntesala);
