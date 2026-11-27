// Vivero (O1, O3, O9, O19, O20, O21): IdA de un vistazo.
// - La escena en grande (dibujo.js, el mismo del visor), con el ritmo (pausa, lento, cómodo, ×4, máximo y, en pausa,
//   paso a paso) y un diario vivo de los hechos de la vida, en frases (frases.js).
// - Tarjetas: Cuerpo y ánimo, Ahora, Lo que sabe, Logros y puntuación, Carácter y Estirpe. Cada una con «Ver más», que
//   abre un panel lateral con su detalle y, al pie, «Abrir en el Laboratorio».
// - T4b: la Estirpe y el cambio de carácter salen del linaje del compañero (GET companeros/{m}), no de lo visto en la
//   página; las barras del cuerpo, de las etiquetas de cada mundo; el reparto entre sistemas, del servidor (desde el
//   inicio de la vida); y el registro de cierre (cierre: true) pone en el diario lo aprendido al morir.
// - Datos: la SSE de la vida al nivel cognitivo (?nivel=cognitivo) y su evento «diario» (lo de antes de conectarse).
//   Nada se pide al motor: todo sale del registro del latido (secciones 4 y 5 de DISENO_OBSERVABILIDAD).

import { api, descargas, escuchar } from '../api.js';
import { t } from '../i18n.js';
import { cargarSprites, dibujarEscena, urlSprite } from '../dibujo.js';
import { avisar, esc } from '../componentes/util.js';
import { radar } from '../componentes/radar.js';
import {
  ICONOS_HECHO, ahoraFrase, accionFrase, barrasDelCuerpo, cargarFrases, capital, causaMuerte, clase, claseDeHecho,
  etiquetaPuntos, fuenteDe, hechoFraseConCierre, logro, logrosDelMundo, planDeAccion, planNombre, requisitoFrase, saberFrase,
  spriteDe, totalLogros, valorPuntos,
} from '../frases.js';

const RITMOS = ['pausa', 'lento', 'comodo', 'x4', 'max'];
const ICONOS_RITMO = { pausa: '❚❚', lento: '◀▶', comodo: '▶', x4: '▶▶', max: '⏭' };
const QUIMICA = { dopamina: 100, placer: 100, estres: 1 };   // escala de cada sustancia en el registro
const RASGOS = ['apertura', 'responsabilidad', 'neuroticismo', 'extraversion', 'umbral_miedo'];
const DIARIO_VISIBLE = 7;          // hechos en el diario de un vistazo
const DIARIO_MAX = 400;            // hechos que se guardan de la vida en curso
const NUEVO_MS = 2600;             // cuánto se resalta lo recién aprendido
const SISTEMAS = ['S1', 'S2', 'S3'];
const ESTIRPE_VISIBLE = 6;         // generaciones en la línea de tiempo de la tarjeta Estirpe
// Hechos que el diario de un vistazo no enseña (son muchos y técnicos): van al detalle de «Ahora».
const FUERA_DEL_DIARIO = new Set(['estrategia']);
const TARJETAS = ['cuerpo', 'ahora', 'sabe', 'logros', 'caracter', 'estirpe'];
const ICONOS_TARJETA = { cuerpo: '💗', ahora: '🎯', sabe: '💡', logros: '🏅', caracter: '🧬', estirpe: '🌳' };
const URL_SNAKE = 'https://playsnake.org/';

function barra(valor, nombre, { max = 100, nivel = true } = {}) {
  const pct = Math.max(0, Math.min(100, (Number(valor) / max) * 100));
  const n = !nivel ? '' : pct < 30 ? 'bajo' : pct < 60 ? 'medio' : 'alto';
  return `<div class="pista-barra" role="meter" aria-label="${esc(nombre)}" aria-valuemin="0" aria-valuemax="100"
    aria-valuenow="${pct.toFixed(0)}" data-nivel="${n}"><i style="width:${pct.toFixed(1)}%"></i></div>`;
}

function claveSaber(p) { return `p:${p.sujeto ?? p.clase}|${p.relacion}`; }
function puntos(v) { return v == null || !Number.isFinite(Number(v)) ? '–' : String(Math.round(Number(v))); }
function claveReq(h) { return `r:${h.verbo}|${h.clase}`; }

class IdaVivero extends HTMLElement {
  constructor() {
    super();
    this.vida = null;
    this.registro = null;
    this.escena = null;
    this.pendiente = false;
    this.cerrar = null;
    this.diario = [];              // hechos de la vida en curso, del más antiguo al más reciente
    this.requisitos = new Map();   // clave -> último «aprende requisito»
    this.nuevos = new Map();       // clave de lo aprendido -> momento (ms) en que se aprendió
    this.reparto = { vida: null, cuenta: {} };   // sistema de cada acción de la vida, desde su inicio (lo da el servidor)
    this.generaciones = new Map(); // generación -> arquetipo visto (por si aún no está en el linaje)
    this.estirpe = null;           // el compañero de este mundo con su linaje (GET companeros/{m})
    this.detalle = null;           // tarjeta abierta en el panel lateral
    this.foco = null;              // a quién devolver el foco al cerrar el panel
    this._alIdioma = () => this.pintar();
    this._alTema = () => this.dibujar();
    this._alTecla = (ev) => { if (ev.key === 'Escape' && this.detalle) this.cerrarDetalle(); };
    this._alClic = (ev) => {
      const b = ev.target.closest('[data-estirpe]');
      if (b && this.contains(b)) this.accionEstirpe(b.dataset.estirpe, b);
    };
  }

  connectedCallback() {
    document.addEventListener('ida:idioma', this._alIdioma);
    document.addEventListener('ida:tema', this._alTema);
    document.addEventListener('keydown', this._alTecla);
    this.addEventListener('click', this._alClic);
    this.innerHTML = `<p class="suave">${esc(t('vivero.conectando'))}</p>`;
    this.iniciar();
  }

  disconnectedCallback() {
    document.removeEventListener('ida:idioma', this._alIdioma);
    document.removeEventListener('ida:tema', this._alTema);
    document.removeEventListener('keydown', this._alTecla);
    this.removeEventListener('click', this._alClic);
    if (this.cerrar) this.cerrar();
  }

  async prepararMundo(mundo) {
    await Promise.all([cargarSprites(mundo), cargarFrases(mundo), this.cargarEstirpe(mundo)]);
  }

  /** El compañero con su linaje: al empezar cada vida y al terminar (el linaje solo cambia entre vidas). */
  async cargarEstirpe(mundo = this.vida && this.vida.mundo) {
    if (!mundo) return;
    try {
      this.estirpe = (await api.companero(mundo)).companero;
    } catch { /* sin linaje: la tarjeta lo dice */ }
    this.programar();
  }

  reiniciarVida() {
    this.registro = null;
    this.escena = null;
    this.diario = [];
    this.requisitos = new Map();
    this.nuevos = new Map();
    this.reparto = { vida: null, cuenta: {} };
    this.generaciones = new Map();
  }

  async iniciar() {
    try {
      this.vida = (await api.vidaActual()).vida;
    } catch (err) {
      this.innerHTML = `<div class="aviso-caja" role="alert">${esc(t(`error.${err.codigo || 'red'}`))}</div>`;
      return;
    }
    if (this.vida) await this.prepararMundo(this.vida.mundo);
    this.pintar();
    this.cerrar = escuchar('vidas/actual/registro?nivel=cognitivo', {
      vida: async (v) => {
        const nueva = !this.vida || v.id !== this.vida.id;
        this.vida = v;
        if (nueva) { this.reiniciarVida(); await this.prepararMundo(v.mundo); }
        this.pintar();
      },
      diario: (d) => {
        this.diario = (d.hechos || []).slice(-DIARIO_MAX);
        this.requisitos = new Map((d.requisitos || []).map((h) => [claveReq(h), h]));
        if (d.reparto) this.reparto = { vida: d.reparto.vida, cuenta: { ...(d.reparto.cuenta || {}) } };
        this.hasta = d.hasta || null;   // el último registro que el diario y el reparto ya cuentan
        this.programar();
      },
      registro: (r) => this.recibir(r),
      ritmo: (d) => { if (this.vida) { this.vida.ritmo = d.ritmo; this.pintarRitmo(); } },
      fin: (v) => { this.vida = v; this.pintar(); this.cargarEstirpe(v.mundo); },
    });
  }

  /** Un registro nuevo: el estado de la vida, el diario, lo recién aprendido y el reparto entre sistemas. */
  recibir(r) {
    const otraVida = this.registro && r.vida !== this.registro.vida;
    if (otraVida) { this.escena = null; this.cargarEstirpe(); }   // la generación anterior ya está en el linaje
    const mismo = (x) => x && x.vida === r.vida && x.latido === r.latido && Boolean(x.cierre) === Boolean(r.cierre);
    const repetido = mismo(this.registro) || mismo(this.hasta);   // ya contado (p. ej. el que llega al conectarse)
    this.hasta = null;
    this.registro = r;
    if (r.escena) this.escena = r.escena;
    if (r.arquetipo) this.generaciones.set(r.generacion, r.arquetipo);
    if (!repetido) {
      const ahora = performance.now();
      for (const h of r.hechos || []) {
        const marcado = { ...h, latido: r.latido, vida: r.vida, generacion: r.generacion, ...(r.cierre ? { cierre: true } : {}) };
        this.diario.push(marcado);
        if (h.tipo === 'aprende') {
          if (h.saber === 'requisito') { this.requisitos.set(claveReq(h), marcado); this.nuevos.set(claveReq(h), ahora); }
          else this.nuevos.set(claveSaber(h), ahora);
        }
      }
      if (this.diario.length > DIARIO_MAX) this.diario.splice(0, this.diario.length - DIARIO_MAX);
      if (!r.cierre && r.accion && r.accion.sistema) {
        if (this.reparto.vida !== r.vida) this.reparto = { vida: r.vida, cuenta: {} };
        this.reparto.cuenta[r.accion.sistema] = (this.reparto.cuenta[r.accion.sistema] || 0) + 1;
      }
    }
    this.programar();
  }

  /** Un dibujo por fotograma como mucho: a ritmo máximo llegan muchos registros por segundo. */
  programar() {
    if (this.pendiente) return;
    this.pendiente = true;
    requestAnimationFrame(() => {
      this.pendiente = false;
      this.dibujar();
      this.pintarTarjetas();
    });
  }

  // --- estructura ------------------------------------------------------------------------------------------------
  pintar() {
    if (!this.vida) {
      this.innerHTML = `<div class="tarjeta vacio-estado">
        <svg viewBox="0 0 140 140" aria-hidden="true">
          <ellipse cx="70" cy="118" rx="46" ry="9" fill="var(--fondo-2)"/>
          <path d="M70 116V70" stroke="var(--musgo)" stroke-width="5" stroke-linecap="round"/>
          <path d="M70 84C70 62 56 50 34 50c0 22 14 34 36 34z" fill="var(--musgo)"/>
          <path d="M70 74c0-20 13-32 34-32 0 20-13 32-34 32z" fill="color-mix(in srgb, var(--musgo) 70%, var(--sol))"/>
        </svg>
        <h2>${esc(t('vivero.vacio_titulo'))}</h2><p>${esc(t('vivero.vacio_texto'))}</p>
        <a class="boton primario" href="#/antesala">${esc(t('vivero.ir_antesala'))}</a></div>`;
      return;
    }
    const v = this.vida;
    const nombreMundo = t(`mundo.${v.mundo}.nombre`);
    const fin = !v.activa ? `<div class="franja" role="status"><span>${esc(v.error ? t('vivero.terminada_error', { error: v.error }) : t('vivero.terminada'))}</span>
        <a class="boton pequeno primario" href="#/antesala">${esc(t('vivero.nueva'))}</a></div>` : '';
    const snake = v.mundo === 'snake' ? `<div class="franja web-real" role="note"><span>🌐 ${esc(t('vivero.snake_jugando'))}
        <a href="${URL_SNAKE}" target="_blank" rel="noopener noreferrer">playsnake.org ↗</a></span>
        <span class="suave pequeno">${esc(v.opciones && v.opciones.ventana ? t('vivero.snake_ventana') : t('vivero.snake_sin_ventana'))}</span></div>` : '';
    const tarjeta = (id, extra = '') => `<section class="tarjeta ficha-vivero ${extra}" data-tarjeta="${id}" aria-labelledby="t-${id}">
        <header><h3 id="t-${id}"><span aria-hidden="true">${ICONOS_TARJETA[id]}</span> ${esc(t(`tarjeta.${id}`))}</h3>
          <button type="button" class="boton pequeno discreto ver-mas" data-ver="${id}" aria-haspopup="dialog">${esc(t('vivero.ver_mas'))} →</button></header>
        <div data-cuerpo="${id}"></div></section>`;
    this.innerHTML = `
      <div class="vivero-cabeza">
        <div class="quien"><h1 data-individuo>${esc(v.individuo || nombreMundo)}</h1>
          <span class="chip sin-punto">${esc(nombreMundo)}</span>
          <span class="chip sin-punto" data-generacion></span>
          <span class="chip listo" data-latido>${esc(t('vivero.latido', { n: v.latido ?? 0 }))}</span></div>
        <a class="boton pequeno discreto" href="/panel">${esc(t('vivero.panel_clasico'))} ↗</a>
      </div>
      ${fin}${snake}
      <div class="vivero">
        <div class="columna-escena">
          <section class="tarjeta escenario" aria-label="${esc(nombreMundo)}">
            <div class="lienzo-marco"><canvas id="vivero-lienzo" width="432" height="336" role="img" aria-label="${esc(nombreMundo)}"></canvas><pre hidden></pre></div>
            <div class="mandos">
              <div class="segmentos ritmos" role="group" aria-label="${esc(t('vivero.ritmo'))}" data-ritmos></div>
              <button type="button" class="boton pequeno" data-paso hidden>⏯ ${esc(t('vivero.paso'))}</button>
              <span class="suave pequeno" data-ritmo-ms></span>
              <button type="button" class="boton pequeno peligro" data-parar ${v.activa ? '' : 'disabled'}>■ ${esc(t('vivero.parar'))}</button>
              <button type="button" class="boton pequeno" data-grabar ${v.activa ? '' : 'disabled'}></button>
              <a class="chip falta grabando" data-grabando href="#/lab?vista=grabaciones" hidden></a>
            </div>
            <p class="suave pequeno" ${v.ritmo_ajustable ? 'hidden' : ''}>⏱ ${esc(t('vivero.ritmo_fijo'))}</p>
          </section>
          <section class="tarjeta diario" aria-labelledby="t-diario">
            <h3 id="t-diario"><span aria-hidden="true">📖</span> ${esc(t('vivero.diario'))}</h3>
            <ol class="lista-diario" data-diario aria-live="polite"></ol>
          </section>
        </div>
        <div class="columna-tarjetas">${tarjeta('cuerpo')}${tarjeta('ahora')}${tarjeta('sabe')}</div>
      </div>
      <div class="fila-tarjetas">${tarjeta('logros')}${tarjeta('caracter')}${tarjeta('estirpe')}</div>
      <div class="velo" data-velo hidden></div>
      <aside class="cajon tarjeta" role="dialog" aria-modal="true" aria-labelledby="cajon-titulo" data-cajon hidden>
        <header><h2 id="cajon-titulo" tabindex="-1"></h2>
          <button type="button" class="boton-icono" data-cerrar aria-label="${esc(t('vivero.cerrar'))}" title="${esc(t('vivero.cerrar'))}">✕</button></header>
        <div class="cajon-cuerpo" data-cajon-cuerpo></div>
        <footer><a class="boton pequeno" data-lab href="#/lab">🔬 ${esc(t('vivero.abrir_lab'))}</a></footer>
      </aside>`;
    this.querySelector('[data-parar]').addEventListener('click', () => this.parar());
    this.querySelector('[data-paso]').addEventListener('click', () => this.paso());
    this.querySelector('[data-grabar]').addEventListener('click', () => this.grabar());
    this.querySelectorAll('[data-ver]').forEach((b) => b.addEventListener('click', () => this.abrirDetalle(b.dataset.ver, b)));
    this.querySelector('[data-cerrar]').addEventListener('click', () => this.cerrarDetalle());
    this.querySelector('[data-velo]').addEventListener('click', () => this.cerrarDetalle());
    this.pintarRitmo();
    this.pintarGrabacion();
    this.dibujar();
    this.pintarTarjetas();
    if (this.detalle) this.abrirDetalle(this.detalle, null);
  }

  // --- ritmo -----------------------------------------------------------------------------------------------------
  pintarRitmo() {
    const caja = this.querySelector('[data-ritmos]');
    if (!caja || !this.vida) return;
    const v = this.vida;
    const fijo = !v.ritmo_ajustable || !v.activa;
    caja.innerHTML = RITMOS.map((r) => `<button type="button" data-ritmo="${r}" aria-pressed="${v.ritmo === r}" ${fijo ? 'disabled' : ''}
      title="${esc(t(`ritmo.ayuda.${r}`))}"><span aria-hidden="true">${ICONOS_RITMO[r]}</span> ${esc(t(`ritmo.${r}`))}</button>`).join('');
    caja.querySelectorAll('[data-ritmo]').forEach((b) => b.addEventListener('click', () => this.cambiarRitmo(b.dataset.ritmo)));
    const paso = this.querySelector('[data-paso]');
    paso.hidden = fijo || v.ritmo !== 'pausa';
    const ms = this.querySelector('[data-ritmo-ms]');
    const comodo = Number(v.ritmo_comodo_ms);
    const factor = { lento: 2, comodo: 1, x4: 0.25 }[v.ritmo];
    ms.textContent = !fijo && factor && comodo ? t('vivero.ms_latido', { ms: Math.round(comodo * factor) }) : '';
  }

  async cambiarRitmo(ritmo) {
    try {
      const r = await api.ritmo(ritmo);
      this.vida.ritmo = r.ritmo;
      this.pintarRitmo();
      this.querySelector(`[data-ritmo="${ritmo}"]`)?.focus();
    } catch (err) {
      avisar(t(`error.${err.codigo || 'red'}`));
    }
  }

  // --- grabar (T5a, O7) -------------------------------------------------------------------------------------------
  pintarGrabacion() {
    const boton = this.querySelector('[data-grabar]');
    const chip = this.querySelector('[data-grabando]');
    if (!boton || !this.vida) return;
    const g = this.vida.activa ? this.vida.grabacion : null;
    boton.textContent = g ? `■ ${t('grabar.terminar')}` : `⏺ ${t('grabar.empezar')}`;
    boton.title = g ? t('grabar.terminar_ayuda') : t('grabar.empezar_ayuda');
    boton.disabled = !this.vida.activa;
    chip.hidden = !g;
    if (g) chip.textContent = t('grabar.grabando');
  }

  async grabar() {
    const boton = this.querySelector('[data-grabar]');
    if (boton) boton.disabled = true;
    try {
      if (this.vida.grabacion) {
        const { grabacion } = await api.terminarGrabacion();
        this.vida.grabacion = null;
        avisar(t('grabar.guardada', { id: grabacion.id, n: grabacion.registros ?? 0 }));
      } else {
        this.vida.grabacion = (await api.grabar()).grabacion;
        avisar(t('grabar.empezada', { id: this.vida.grabacion.id }));
      }
    } catch (err) {
      avisar(t(`error.${err.codigo || 'red'}`));
    }
    this.pintarGrabacion();
  }

  async paso() {
    try { await api.paso(); } catch (err) { avisar(t(`error.${err.codigo || 'red'}`)); }
  }

  async parar() {
    const boton = this.querySelector('[data-parar]');
    if (boton) boton.disabled = true;
    try {
      this.vida = (await api.parar()).vida || this.vida;
    } catch (err) {
      avisar(t(`error.${err.codigo || 'red'}`));
    }
    this.pintar();
  }

  // --- escena ----------------------------------------------------------------------------------------------------
  dibujar() {
    const lienzo = this.querySelector('#vivero-lienzo');
    if (!lienzo || !this.vida) return;
    const pre = lienzo.nextElementSibling;
    const ok = this.escena && dibujarEscena(lienzo, this.escena, this.vida.mundo, { inventario: t('escena.inventario') });
    lienzo.hidden = !ok;
    lienzo.parentElement.dataset.tipo = ok ? this.escena.tipo : 'texto';
    pre.hidden = Boolean(ok) || !this.registro;
    if (!ok && this.registro) pre.textContent = this.registro.vista || t('vivero.sin_escena');
  }

  // --- piezas comunes --------------------------------------------------------------------------------------------
  /** El sprite de una clase (o su icono de texto, o su inicial). estricto: nada si no hay sprite ni icono. */
  icono(c, estricto = false) {
    if (!c || !this.vida) return estricto ? '' : '<span class="icono-clase vacio" aria-hidden="true"></span>';
    const { clave, icono } = spriteDe(this.vida.mundo, c);
    const url = urlSprite(this.vida.mundo, clave);
    if (url) return `<span class="icono-clase" aria-hidden="true"><img src="${esc(url)}" alt=""></span>`;
    if (estricto && !icono) return '';
    const letra = icono || String(clase(this.vida.mundo, c, 'nombre'))[0] || '?';
    return `<span class="icono-clase texto" aria-hidden="true">${esc(letra)}</span>`;
  }

  esNuevo(clave) {
    const t0 = this.nuevos.get(clave);
    return t0 !== undefined && performance.now() - t0 < NUEVO_MS;
  }

  /** Lo que sabe, ordenado: lo aprendido en esta vida (lo más reciente primero) y después lo de más confianza. */
  loQueSabe() {
    const mundo = this.vida.mundo;
    const r = this.registro || {};
    const items = [];
    const vistos = new Set();
    const saber = (r.saber || []).filter((p) => p.estado !== 'refutada');
    const porClave = new Map(saber.map((p) => [claveSaber(p), p]));
    const aprendidos = this.diario.filter((h) => h.tipo === 'aprende' && h.vida === r.vida).reverse();
    const añadir = (clave, item) => { if (!vistos.has(clave)) { vistos.add(clave); items.push(item); } };
    for (const h of aprendidos) {
      if (h.saber === 'requisito') {
        const req = this.requisitos.get(claveReq(h)) || h;
        añadir(claveReq(h), { clave: claveReq(h), frase: requisitoFrase(mundo, req), clase: req.clase,
          hipotesis: !req.confirmado, fuente: fuenteDe(req), confianza: req.confianza, req });
      } else {
        const p = porClave.get(claveSaber(h));
        if (!p) continue;
        añadir(claveSaber(h), { clave: claveSaber(h), frase: saberFrase(mundo, p), clase: p.sujeto,
          hipotesis: p.estado === 'hipotesis', fuente: fuenteDe(p), confianza: p.confianza });
      }
    }
    for (const p of saber) {
      añadir(claveSaber(p), { clave: claveSaber(p), frase: saberFrase(mundo, p), clase: p.sujeto,
        hipotesis: p.estado === 'hipotesis', fuente: fuenteDe(p), confianza: p.confianza });
    }
    // Todos los requisitos (T4b: el registro cognitivo los trae, también los del manual que no cambian en la vida)
    const reqs = Array.isArray(r.requisitos) ? r.requisitos : [...this.requisitos.values()].filter((q) => q.vida === r.vida);
    for (const req of reqs) {
      añadir(claveReq(req), { clave: claveReq(req), frase: requisitoFrase(mundo, req), clase: req.clase,
        hipotesis: !req.confirmado, fuente: fuenteDe(req), confianza: req.confianza, req });
    }
    return items;
  }

  /** Cuánto sabe en total (T4b): proposiciones no refutadas y requisitos, de toda la memoria (resumen_saber). */
  totalSaber() {
    const rs = (this.registro || {}).resumen_saber;
    if (!rs) return null;
    return Math.max(0, Number(rs.proposiciones) - Number(rs.refutadas)) + Number(rs.requisitos || 0);
  }

  itemSaber(it, detalle = false) {
    const nuevo = this.esNuevo(it.clave);
    const estado = it.hipotesis ? 'hipotesis' : 'demostrada';
    const extra = detalle ? `<span class="meta">
        <span class="chip sin-punto fuente-${esc(it.fuente)}">${esc(t(`fuente.${it.fuente}`))}</span>
        <span class="confianza" title="${esc(t('sabe.confianza'))}">${barra(Number(it.confianza) * 100, t('sabe.confianza'), { nivel: false })}
        <b>${Math.round(Number(it.confianza) * 100)} %</b></span>
        ${it.req ? `<span class="suave pequeno">${esc(this.cantidades(it.req))}</span>` : ''}</span>` : '';
    return `<li class="saber ${estado}${nuevo ? ' nuevo' : ''}">${this.icono(it.clase)}
      <span class="texto"><span>${esc(it.frase)}</span>
      ${it.hipotesis ? `<span class="marca-hipotesis">${esc(t('sabe.hipotesis'))}</span>` : ''}
      ${nuevo ? `<span class="marca-nuevo">${esc(t('sabe.nuevo'))}</span>` : ''}${extra}</span></li>`;
  }

  cantidades(req) {
    const mundo = this.vida.mundo;
    const partes = [];
    const req2 = Object.entries(req.requiere || {});
    if (req2.length) partes.push(`${t('sabe.necesita')}: ${req2.map(([c, n]) => `${n ?? '?'} × ${clase(mundo, c)}`).join(', ')}`);
    const ef = Object.entries(req.efecto || {});
    if (ef.length) partes.push(`${t('sabe.efecto')}: ${ef.map(([c, n]) => `${Number(n) > 0 ? '+' : ''}${n} ${clase(mundo, c)}`).join(', ')}`);
    return partes.join(' · ');
  }

  itemHecho(h) {
    const frase = hechoFraseConCierre(this.vida.mundo, h);
    if (!frase) return '';
    const c = claseDeHecho(h);
    return `<li class="hecho hecho-${esc(h.tipo)}${h.cierre ? ' al-morir' : ''}"><span class="icono-hecho" aria-hidden="true">${h.cierre ? '🕯️' : ICONOS_HECHO[h.tipo] || '•'}</span>
      ${c && h.tipo !== 'muere' ? this.icono(c) : ''}<span class="texto">${esc(frase)}</span>
      <span class="latido-hecho">${esc(t('vivero.latido_corto', { n: h.latido ?? '' }))}</span></li>`;
  }

  // --- tarjetas --------------------------------------------------------------------------------------------------
  pintarTarjetas() {
    const r = this.registro;
    if (!this.querySelector('[data-latido]')) return;
    if (r) {
      this.querySelector('[data-latido]').textContent = t('vivero.latido', { n: r.latido });
      this.querySelector('[data-individuo]').textContent = r.individuo;
      this.querySelector('[data-generacion]').textContent = t('vivero.generacion', { n: r.generacion });
    }
    const pintar = (id, html) => { const el = this.querySelector(`[data-cuerpo="${id}"]`); if (el) el.innerHTML = html; };
    pintar('cuerpo', this.htmlCuerpo(false));
    pintar('ahora', this.htmlAhora(false));
    pintar('sabe', this.htmlSabe(false));
    pintar('logros', this.htmlLogros(false));
    pintar('caracter', this.htmlCaracter(false));
    pintar('estirpe', this.htmlEstirpe(false));
    const diario = this.querySelector('[data-diario]');
    if (diario) {
      const visibles = this.diario.filter((h) => !FUERA_DEL_DIARIO.has(h.tipo)).slice(-DIARIO_VISIBLE).reverse();
      diario.innerHTML = visibles.length ? visibles.map((h) => this.itemHecho(h)).join('') : `<li class="suave">${esc(t('vivero.diario_vacio'))}</li>`;
    }
    if (this.detalle) this.pintarDetalle();
  }

  htmlCuerpo(detalle) {
    const r = this.registro;
    if (!r) return `<p class="suave">${esc(t('vivero.esperando'))}</p>`;
    const cuerpo = r.cuerpo || {};
    const barras = barrasDelCuerpo(this.vida.mundo);   // T4b: las de este mundo, con sus nombres (sección 13.6)
    const medidores = barras.map(({ clave: m, etiqueta, ayuda }) => `<div class="medidor ${m}" ${ayuda ? `title="${esc(ayuda)}"` : ''}><span>${esc(etiqueta)}</span>
      ${barra(cuerpo[m], etiqueta)}<output>${Number.isFinite(Number(cuerpo[m])) ? Number(cuerpo[m]).toFixed(0) : '–'}</output></div>`).join('');
    const afecto = (r.afecto || {}).estado;
    const tono = ['MIEDO', 'PANICO', 'ALERTA'].includes(afecto) ? 'falta' : ['CALMA', 'CURIOSIDAD'].includes(afecto) ? 'listo' : 'aviso';
    const estados = [cuerpo.dormido ? t('cuerpo.dormida') : '', cuerpo.cargando ? t('cuerpo.cargando', { que: clase(this.vida.mundo, cuerpo.cargando) }) : '']
      .filter(Boolean).map((s) => `<span class="chip sin-punto">${esc(s)}</span>`).join('');
    const animo = `<div class="animo"><span class="suave">${esc(t('vivero.animo'))}</span>
      <span class="chip ${tono}">${esc(afecto ? t(`afecto.${afecto}`) : '–')}</span>${estados}</div>`;
    if (!detalle) return medidores + animo;
    const quimica = Object.entries(QUIMICA).map(([q, max]) => {
      const v = Number((r.quimica || {})[q] ?? 0);
      return `<div class="medidor"><span>${esc(t(`quimica.${q}`))}</span>${barra(v, t(`quimica.${q}`), { max, nivel: false })}
        <output>${max > 1 ? v.toFixed(0) : v.toFixed(2)}</output></div>`;
    }).join('');
    const ind = Object.entries((r.afecto || {}).indicadores || {}).map(([k, v]) => `<div class="medidor"><span>${esc(t(`indicador.${k}`) === `indicador.${k}` ? k : t(`indicador.${k}`))}</span>
      ${barra(Number(v) * 100, k, { nivel: false })}<output>${Number(v).toFixed(2)}</output></div>`).join('');
    const nec = (r.necesidades || []).map((n) => `<div class="medidor"><span>${esc(t(`necesidad.${n.nombre}`) === `necesidad.${n.nombre}` ? n.nombre : t(`necesidad.${n.nombre}`))}</span>
      ${barra(Number(n.deficit) * 100, n.nombre, { nivel: false })}<output>${Math.round(Number(n.deficit) * 100)} %</output></div>`).join('');
    const valencia = Number((r.afecto || {}).valencia ?? 0);
    const ayudas = barras.filter((b) => b.ayuda).map((b) => `<li><b>${esc(b.etiqueta)}</b>: ${esc(b.ayuda)}</li>`).join('');
    return `${medidores}${animo}
      ${ayudas ? `<ul class="lista-simple suave pequeno">${ayudas}</ul>` : ''}
      <h4>${esc(t('detalle.quimica'))}</h4>${quimica}
      <p class="suave pequeno">${esc(t('detalle.valencia', { v: valencia.toFixed(2) }))}</p>
      <h4>${esc(t('detalle.indicadores'))}</h4>${ind || `<p class="suave pequeno">–</p>`}
      <h4>${esc(t('detalle.necesidades'))}</h4><p class="suave pequeno">${esc(t('detalle.necesidades_ayuda'))}</p>${nec || '<p class="suave pequeno">–</p>'}`;
  }

  htmlAhora(detalle) {
    const r = this.registro;
    if (!r) return `<p class="suave">${esc(t('vivero.esperando'))}</p>`;
    const mundo = this.vida.mundo;
    const a = r.accion;
    const plan = planDeAccion(a);
    const principal = `<p class="frase-ahora">${a ? this.icono(a.clase, true) : ''}<span>${esc(ahoraFrase(mundo, a))}</span></p>
      ${plan ? `<p class="suave pequeno">🧭 ${esc(t('ahora.plan', { plan }))} · ${esc(t(`sistema.${a.sistema}`) === `sistema.${a.sistema}` ? a.sistema : t(`sistema.${a.sistema}`))}</p>` : ''}`;
    if (!detalle) return principal;
    const trib = r.tribunal || {};
    const candidatos = (trib.candidatos || []).map((c) => {
      const gana = trib.ganador && trib.ganador.id === c.id;
      return `<tr class="${gana ? 'gana' : ''}"><td>${esc(c.sistema)}</td>
        <td>${esc(capital(accionFrase(mundo, c.verbo, '', c.objetivo, 'inf')))} <code>${esc(c.objetivo || '')}</code>
          ${c.motivo ? `<br><span class="suave pequeno">${esc(c.motivo)}</span>` : ''}</td>
        <td class="num">${Number(c.total).toFixed(2)}</td></tr>`;
    }).join('');
    const activas = ((r.estrategias || {}).activas || []).map((e) => `<li>🧭 ${esc(planNombre(e.nombre))} <span class="suave">· ${esc(e.sistema)}</span></li>`).join('');
    const cuenta = Object.fromEntries(SISTEMAS.map((s) => [s, 0]));
    const propia = this.reparto.vida === r.vida ? this.reparto.cuenta : {};
    for (const [s, n] of Object.entries(propia)) cuenta[s] = (cuenta[s] || 0) + n;
    const acciones = Object.values(cuenta).reduce((a, b) => a + b, 0);
    const total = Math.max(1, acciones);
    const reparto = Object.entries(cuenta).filter(([, n]) => n || true).map(([s, n]) => `<div class="medidor"><span>${esc(t(`sistema.${s}`) === `sistema.${s}` ? s : t(`sistema.${s}`))}</span>
      ${barra((n / total) * 100, s, { nivel: false })}<output>${Math.round((n / total) * 100)} %</output></div>`).join('');
    const planes = this.diario.filter((h) => h.tipo === 'estrategia').slice(-8).reverse().map((h) => this.itemHecho(h)).join('');
    const motivo = a && a.motivo ? `<p class="suave pequeno">${esc(t('detalle.motivo_motor'))}: <q>${esc(a.motivo)}</q></p>` : '';
    return `${principal}${motivo}
      ${a ? `<p class="suave pequeno">${esc(t('detalle.accion_cruda'))}: <code>${esc(`${a.verbo} ${a.objetivo || ''}`.trim())}</code>${a.clase ? ` · <code>${esc(a.clase)}</code>` : ''}</p>` : ''}
      <h4>${esc(t('detalle.tribunal'))}</h4>
      ${candidatos ? `<table class="tabla"><thead><tr><th>${esc(t('detalle.sistema'))}</th><th>${esc(t('detalle.candidato'))}</th><th class="num">${esc(t('detalle.total'))}</th></tr></thead><tbody>${candidatos}</tbody></table>` : `<p class="suave pequeno">–</p>`}
      ${trib.plus_decide ? `<p class="suave pequeno">${esc(t('detalle.plus_decide'))}</p>` : ''}
      <h4>${esc(t('detalle.estrategias'))}</h4>${activas ? `<ul class="lista-simple">${activas}</ul>` : `<p class="suave pequeno">–</p>`}
      <h4>${esc(t('detalle.reparto', { n: acciones }))}</h4>${reparto}
      <h4>${esc(t('detalle.planes'))}</h4>${planes ? `<ol class="lista-diario">${planes}</ol>` : `<p class="suave pequeno">–</p>`}`;
  }

  htmlSabe(detalle) {
    const r = this.registro;
    if (!r) return `<p class="suave">${esc(t('vivero.esperando'))}</p>`;
    const items = this.loQueSabe();
    if (!detalle) {
      const vistos = Math.min(5, items.length);
      const total = this.totalSaber() ?? items.length;   // T4b: de toda la memoria, no de lo que trae el registro
      return items.length ? `<ul class="lista-saber">${items.slice(0, 5).map((it) => this.itemSaber(it)).join('')}</ul>
        ${total > vistos ? `<p class="suave pequeno">${esc(t('sabe.y_mas', { n: total - vistos }))}</p>` : ''}`
        : `<p class="suave">${esc(t('sabe.nada'))}</p>`;
    }
    const m = r.memoria || {};
    const rs = r.resumen_saber || {};
    const cifras = [['demostradas', rs.demostradas ?? m.demostradas], ['hipotesis', rs.hipotesis ?? m.hipotesis],
      ['refutadas', rs.refutadas ?? m.refutadas], ['requisitos', rs.requisitos ?? 0], ['aciertos', rs.aciertos ?? m.aciertos],
      ['sorpresas', rs.sorpresas ?? m.sorpresas], ['heredadas', rs.heredadas ?? m.heredados]]
      .map(([k, v]) => `<div class="cifra"><b>${esc(v ?? 0)}</b><span>${esc(t(`sabe.cifra.${k}`))}</span></div>`).join('');
    const mundo = this.vida.mundo;
    const refutadas = (r.saber || []).filter((p) => p.estado === 'refutada')
      .map((p) => `<li class="saber refutada">${this.icono(p.sujeto)}<span class="texto"><span>${esc(saberFrase(mundo, p))}</span>
        <span class="meta"><span class="chip sin-punto">${esc(t(`fuente.${fuenteDe(p)}`))}</span><b>${Math.round(p.confianza * 100)} %</b></span></span></li>`).join('');
    const sorpresas = this.diario.filter((h) => h.tipo === 'sorpresa' || h.tipo === 'duda' || h.tipo === 'refuta').slice(-8).reverse()
      .map((h) => this.itemHecho(h)).join('');
    return `<div class="cifras">${cifras}</div>
      <p class="suave pequeno">${esc(t('sabe.leyenda'))}</p>
      ${rs.fuentes ? `<p class="suave pequeno">${esc(t('sabe.fuentes', { manual: rs.fuentes.manual ?? 0, experiencia: rs.fuentes.experiencia ?? 0,
        herencia: rs.fuentes.herencia ?? 0, biblioteca: rs.fuentes.biblioteca ?? 0 }))}</p>` : ''}
      <ul class="lista-saber detalle">${items.map((it) => this.itemSaber(it, true)).join('') || `<li class="suave">${esc(t('sabe.nada'))}</li>`}</ul>
      <h4>${esc(t('sabe.refutadas'))}</h4>${refutadas ? `<ul class="lista-saber detalle">${refutadas}</ul>` : `<p class="suave pequeno">${esc(t('sabe.refutadas_vacio', { n: m.refutadas ?? 0 }))}</p>`}
      <h4>${esc(t('sabe.sorpresas'))}</h4>${sorpresas ? `<ol class="lista-diario">${sorpresas}</ol>` : `<p class="suave pequeno">–</p>`}
      <p class="suave pequeno">${esc(t('sabe.nota_nivel'))}</p>`;
  }

  htmlLogros(detalle) {
    const r = this.registro;
    if (!r) return `<p class="suave">${esc(t('vivero.esperando'))}</p>`;
    const mundo = this.vida.mundo;
    const logros = (r.score && r.score.logros) || [];
    const total = totalLogros(mundo);
    const punt = (r.score && r.score.puntuacion) || {};
    const valor = (v) => (typeof v === 'number' ? String(Math.round(v * 100) / 100)
      : Array.isArray(v) ? v.map((x) => (typeof x === 'number' ? Math.round(x * 10) / 10 : x)).join(' / ')
        : typeof v === 'object' && v ? Object.entries(v).map(([k, n]) => `${clase(mundo, k)} ${n}`).join(', ') : valorPuntos(mundo, String(v)));
    const filas = Object.entries(punt).filter(([k]) => k !== 'logros' && !(total && k === 'n_logros'))
      .map(([k, v]) => `<div class="punto"><span>${esc(etiquetaPuntos(mundo, k))}</span><b>${esc(valor(v))}</b></div>`).join('');
    const ultimos = logros.length ? `<ul class="chips-logros">${(detalle ? logros : logros.slice(-4)).map((l) => `<li class="chip listo">🏅 ${esc(logro(mundo, l))}</li>`).join('')}</ul>` : '';
    const cabeza = total ? `<p class="logros-cuenta"><b>${logros.length}</b> / ${total} ${esc(t('vivero.logros').toLowerCase())}</p>` : '';
    if (!detalle) return `${cabeza}<div class="puntos-lista">${filas}</div>${ultimos}`;
    const todos = logrosDelMundo(mundo);
    const rejilla = todos.length ? `<h4>${esc(t('detalle.todos_logros'))}</h4><ul class="rejilla-logros">${todos.map((l) => {
      const si = logros.includes(l);
      return `<li class="${si ? 'si' : 'no'}"><span aria-hidden="true">${si ? '🏅' : '○'}</span> ${esc(logro(mundo, l))}
        <span class="oculto">${esc(si ? t('detalle.conseguido') : t('detalle.pendiente'))}</span></li>`;
    }).join('')}</ul>` : '';
    const historia = this.diario.filter((h) => !FUERA_DEL_DIARIO.has(h.tipo)).slice().reverse().map((h) => this.itemHecho(h)).join('');
    return `${cabeza}<div class="puntos-lista">${filas}</div>${rejilla}
      <h4>${esc(t('detalle.historia'))}</h4><p class="suave pequeno">${esc(t('detalle.historia_ayuda', { n: DIARIO_MAX }))}</p>
      ${historia ? `<ol class="lista-diario">${historia}</ol>` : `<p class="suave pequeno">–</p>`}`;
  }

  htmlCaracter(detalle) {
    const r = this.registro;
    const arq = (r && r.arquetipo) || (this.vida && this.vida.arquetipo);
    if (!arq) return `<p class="suave">${esc(t('vivero.esperando'))}</p>`;
    const etiquetas = RASGOS.map((x) => t(`rasgo.${x}.nombre`).slice(0, 5));
    const grafico = radar(arq, RASGOS, { etiquetas: detalle ? etiquetas : null, titulo: t('tarjeta.caracter') });
    const gen = r ? r.generacion : null;
    const previo = gen != null ? this.arquetipoDe(gen - 1) : null;
    const filas = RASGOS.map((x) => {
      const d = previo ? Number(arq[x]) - Number(previo[x]) : null;
      const cambio = d == null ? '' : `<span class="cambio ${d > 0.004 ? 'sube' : d < -0.004 ? 'baja' : ''}">${d > 0 ? '+' : ''}${d.toFixed(2)}</span>`;
      return `<div class="rasgo-fila"><span>${esc(t(`rasgo.${x}.nombre`))}</span>${barra(Number(arq[x]) * 100, x, { nivel: false })}
        <output>${Number(arq[x]).toFixed(2)}</output>${detalle ? cambio : ''}</div>`;
    }).join('');
    if (!detalle) return `<div class="caracter-mini">${grafico}<div>${filas}</div></div>`;
    const nota = previo ? t('caracter.mutacion', { g: gen - 1 }) : t('caracter.sin_previa');
    const linaje = this.lineaEstirpe();
    const evolucion = linaje.filter((v) => v.arquetipo).length > 1 ? `<h4>${esc(t('estirpe.mutacion'))}</h4>${this.htmlMutacion(linaje)}` : '';
    return `<div class="caracter-grande">${grafico}</div>${filas}
      <p class="suave pequeno">${esc(nota)}</p>
      <ul class="lista-simple">${RASGOS.map((x) => `<li><b>${esc(t(`rasgo.${x}.nombre`))}</b>: ${esc(t(`rasgo.${x}.desc`))}</li>`).join('')}</ul>
      ${evolucion}`;
  }

  /** Los rasgos de una generación de la estirpe: del linaje (o, si aún no está, de lo visto en esta página). */
  arquetipoDe(gen) {
    const v = this.lineaEstirpe().find((x) => x.generacion === gen && x.arquetipo);
    return v ? v.arquetipo : this.generaciones.get(gen) || null;
  }

  /**
   * La línea de la estirpe: las vidas del linaje en orden de generación y, al final, la que está en curso (si aún no
   * ha terminado). Cada una: individuo, generación, Score, causa de muerte, arquetipo.
   */
  lineaEstirpe() {
    const linaje = ((this.estirpe && this.estirpe.linaje) || []).map((v) => ({ ...v }));
    const r = this.registro;
    if (r && !linaje.some((v) => v.individuo === r.individuo)) {
      linaje.push({ individuo: r.individuo, generacion: r.generacion, score: null, causa_muerte: null, vivo: true,
        en_curso: Boolean(this.vida && this.vida.activa) && !r.cierre, latidos: r.latido, arquetipo: r.arquetipo });
    }
    return linaje;
  }

  itemEstirpe(v) {
    const mundo = this.vida.mundo;
    const fin = v.en_curso ? t('estirpe.en_curso', { n: v.latidos ?? 0 })
      : v.vivo === false ? t('estirpe.murio', { causa: causaMuerte(mundo, v.causa_muerte || 'desgaste'), n: v.latidos ?? '?' })
        : v.vivo ? t('estirpe.vivio', { n: v.latidos ?? '?' }) : t('estirpe.sin_dato');
    const mejor = this.estirpe && v.score != null && v.score === this.estirpe.mejor_score;
    return `<li class="gen${v.en_curso ? ' en-curso' : ''}${mejor ? ' mejor' : ''}"><span class="nudo" aria-hidden="true"></span>
      <span class="texto"><b>${esc(v.individuo)}</b> <span class="suave pequeno">· ${esc(fin)}</span></span>
      <span class="score" title="${esc(t('estirpe.score'))}">${mejor ? '🏆 ' : ''}${esc(puntos(v.score))}</span></li>`;
  }

  htmlEstirpe(detalle) {
    const linea = this.lineaEstirpe();
    const e = this.estirpe || {};
    const r = this.registro;
    const gen = r ? r.generacion : (this.vida && this.vida.generacion) || 1;
    const visibles = detalle ? linea : linea.slice(-ESTIRPE_VISIBLE);
    const ocultas = linea.length - visibles.length;
    const cabeza = `<div class="estirpe-cabeza"><p class="generacion-grande"><b>${esc(t('vivero.generacion', { n: gen }))}</b></p>
      <p class="suave pequeno">${esc(t(e.generaciones === 1 ? 'estirpe.resumen_1' : 'estirpe.resumen', { n: e.generaciones ?? 0, score: puntos(e.mejor_score) }))}</p></div>`;
    const lista = linea.length ? `<ol class="linea-estirpe">${ocultas > 0 ? `<li class="suave pequeno">${esc(t('estirpe.anteriores', { n: ocultas }))}</li>` : ''}
      ${visibles.map((v) => this.itemEstirpe(v)).join('')}</ol>` : `<p class="suave pequeno">${esc(t('estirpe.vacia'))}</p>`;
    const puedeGuardar = Boolean(e.existe);
    const botones = `<div class="botones-estirpe">
      <button type="button" class="boton pequeno" data-estirpe="guardar" ${puedeGuardar ? '' : 'disabled'} title="${esc(t('estirpe.guardar_ayuda'))}">💾 ${esc(t('estirpe.guardar'))}</button>
      <a class="boton pequeno discreto" href="#/vivero/coleccion">🗂️ ${esc(t('estirpe.coleccion'))}</a>
      ${detalle && puedeGuardar ? `<a class="boton pequeno discreto" href="${esc(descargas.companero(this.vida.mundo))}" download>⬇️ ${esc(t('coleccion.exportar'))}</a>` : ''}</div>`;
    if (!detalle) return `${cabeza}${lista}${botones}`;
    const filas = linea.map((v) => `<tr class="${v.en_curso ? 'en-curso' : ''}"><td>${esc(v.generacion ?? '–')}</td><td>${esc(v.individuo)}</td>
      <td class="num">${esc(puntos(v.score))}</td><td class="num">${esc(v.latidos ?? '–')}</td>
      <td>${esc(v.en_curso ? t('estirpe.en_curso_corto') : v.vivo === false ? causaMuerte(this.vida.mundo, v.causa_muerte || 'desgaste') : v.vivo ? t('estirpe.vivo') : '–')}</td>
      <td class="num">${esc((v.logros || []).length || '')}</td></tr>`).join('');
    const tabla = linea.length ? `<table class="tabla"><thead><tr><th>${esc(t('estirpe.col_gen'))}</th><th>${esc(t('estirpe.col_individuo'))}</th>
      <th class="num">${esc(t('estirpe.score'))}</th><th class="num">${esc(t('estirpe.col_latidos'))}</th><th>${esc(t('estirpe.col_fin'))}</th>
      <th class="num">${esc(t('estirpe.col_logros'))}</th></tr></thead><tbody>${filas}</tbody></table>` : '';
    const mutacion = linea.filter((v) => v.arquetipo).length > 1 ? this.htmlMutacion(linea) : `<p class="suave pequeno">${esc(t('estirpe.sin_mutacion'))}</p>`;
    const adoptada = e.adoptada_de ? `<p class="suave pequeno">${esc(t('estirpe.adoptada'))}</p>` : '';
    return `${cabeza}${botones}${adoptada}
      <h4>${esc(t('estirpe.linaje'))}</h4><p class="suave pequeno">${esc(t('estirpe.linaje_ayuda'))}</p>${tabla}
      <h4>${esc(t('estirpe.mutacion'))}</h4>${mutacion}`;
  }

  /** La mutación de cada rasgo a lo largo de las generaciones: una línea por rasgo, con el primero y el último. */
  htmlMutacion(linea) {
    const puntosArq = linea.filter((v) => v.arquetipo);
    const n = puntosArq.length;
    const ancho = 220;
    const alto = 34;
    const x = (i) => (n === 1 ? ancho / 2 : 6 + (i * (ancho - 12)) / (n - 1));
    const y = (v) => alto - 4 - Number(v) * (alto - 8);
    return `<div class="mutacion">${RASGOS.map((rasgo) => {
      const valores = puntosArq.map((v) => Number(v.arquetipo[rasgo] ?? 0.5));
      const camino = valores.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
      const d = valores[valores.length - 1] - valores[0];
      return `<div class="mutacion-fila"><span>${esc(t(`rasgo.${rasgo}.nombre`))}</span>
        <svg viewBox="0 0 ${ancho} ${alto}" role="img" aria-label="${esc(t('estirpe.mutacion_rasgo', { rasgo: t(`rasgo.${rasgo}.nombre`), desde: valores[0].toFixed(2), hasta: valores[valores.length - 1].toFixed(2), n }))}">
          <line x1="0" x2="${ancho}" y1="${y(0.5).toFixed(1)}" y2="${y(0.5).toFixed(1)}" class="guia"/>
          <polyline points="${camino}" class="trazo"/>${valores.map((v, i) => `<circle cx="${x(i).toFixed(1)}" cy="${y(v).toFixed(1)}" r="2.6" class="punto"/>`).join('')}</svg>
        <output>${valores[0].toFixed(2)} → ${valores[valores.length - 1].toFixed(2)}
          <span class="cambio ${d > 0.004 ? 'sube' : d < -0.004 ? 'baja' : ''}">${d > 0 ? '+' : ''}${d.toFixed(2)}</span></output></div>`;
    }).join('')}</div>`;
  }

  async accionEstirpe(accion, boton) {
    if (accion !== 'guardar' || !this.vida) return;
    boton.disabled = true;
    try {
      const { ficha } = await api.guardar(this.vida.mundo);
      avisar(t('estirpe.guardada', { nombre: ficha.nombre }));
    } catch (err) {
      avisar(t(`error.${err.codigo || 'red'}`));
    }
    boton.disabled = false;
  }

  // --- panel lateral ----------------------------------------------------------------------------------------------
  abrirDetalle(id, origen) {
    if (!TARJETAS.includes(id)) return;
    this.detalle = id;
    if (origen) this.foco = origen;
    const cajon = this.querySelector('[data-cajon]');
    const velo = this.querySelector('[data-velo]');
    if (!cajon) return;
    cajon.hidden = false;
    velo.hidden = false;
    this.querySelector('#cajon-titulo').innerHTML = `<span aria-hidden="true">${ICONOS_TARJETA[id]}</span> ${esc(t(`tarjeta.${id}`))}`;
    this.pintarDetalle();
    if (origen) this.querySelector('#cajon-titulo').focus();
  }

  pintarDetalle() {
    const caja = this.querySelector('[data-cajon-cuerpo]');
    if (!caja) return;
    const id = this.detalle;
    // T5a: «Abrir en el Laboratorio» lleva a la sección y al latido que se está viendo (el directo en memoria). T5b: con
    // el mundo, para que Carácter y Estirpe abran la comparación de estirpes aunque no haya directo.
    const r = this.registro;
    const latido = r ? `&vida=${encodeURIComponent(r.vida)}&latido=${encodeURIComponent(r.latido)}` : '';
    const mundo = this.vida && this.vida.mundo ? `&mundo=${encodeURIComponent(this.vida.mundo)}` : '';
    this.querySelector('[data-lab]').href = `#/lab?seccion=${id}&fuente=directo${latido}${mundo}`;
    const html = id === 'cuerpo' ? this.htmlCuerpo(true) : id === 'ahora' ? this.htmlAhora(true) : id === 'sabe' ? this.htmlSabe(true)
      : id === 'logros' ? this.htmlLogros(true) : id === 'caracter' ? this.htmlCaracter(true) : this.htmlEstirpe(true);
    if (html === this._ultimoDetalle) return;
    this._ultimoDetalle = html;
    const scroll = caja.scrollTop;
    caja.innerHTML = html;
    caja.scrollTop = scroll;
  }

  cerrarDetalle() {
    this.detalle = null;
    this._ultimoDetalle = null;
    const cajon = this.querySelector('[data-cajon]');
    if (cajon) { cajon.hidden = true; this.querySelector('[data-velo]').hidden = true; }
    if (this.foco && this.foco.isConnected) this.foco.focus();
    else this.querySelector('[data-ver]')?.focus();
  }
}

customElements.define('ida-vivero', IdaVivero);
