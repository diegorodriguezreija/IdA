// Laboratorio (O1, O7, O13, T5a): la vista experta. Cómo funciona IdA latido a latido.
// - Fuente: la vida en directo (los últimos latidos que guarda el servidor, sin grabar), una grabación de la lista o un
//   fichero cargado (lab/fuentes.js).
// - Reproductor: línea de tiempo con los hechos marcados (logros, lo aprendido, la muerte), reproducir, pausa, paso a
//   paso adelante y atrás, ir a un latido y velocidad. La escena pequeña, siempre a la vista.
// - Vistas: «Latido» (los 8 pasos de D1 con la Onda, lab/latido.js), «Ingeniería» (el mapa de Componentes con sus
//   tiempos, lab/ingenieria.js) y «Grabaciones» (listar, abrir, descargar y borrar en dos pasos).
// - Al pulsar una pieza, su registro; al pulsar un Componente, su ficha (análogo y descripción de componentes.toml, O13).
// - «Abrir en el Laboratorio» del Vivero llega con #/lab?seccion=<tarjeta>&fuente=directo&vida=<v>&latido=<l>.

import { api, descargas } from '../api.js';
import { t } from '../i18n.js';
import { cargarSprites, dibujarEscena } from '../dibujo.js';
import { cargarFrases, hechoFrase } from '../frases.js';
import { almacen, avisar, esc } from '../componentes/util.js';
import { FuenteDirecto, FuenteFichero, FuenteGrabacion } from '../lab/fuentes.js';
import { cargarCatalogo, fichaComponente, mediasAgrupadas, tiemposAgrupados } from '../lab/catalogo.js';
import { analizar, animar, detallePaso, detallePieza, sinMovimiento, svgLatido } from '../lab/latido.js';
import { htmlIngenieria } from '../lab/ingenieria.js';
import { posicionDeClic, svgLinea } from '../lab/linea.js';

const VISTAS = ['latido', 'ingenieria', 'grabaciones'];
const VELOCIDADES = [0.5, 1, 2, 4, 8];        // latidos por segundo al reproducir
const SONDEO_MS = 1000;                        // cada cuánto se pregunta al directo por latidos nuevos
// De la tarjeta del Vivero (O19) al paso del latido que la explica; Carácter y Estirpe tendrán su vista en T5b.
const SECCION_PASO = { cuerpo: 'sentir', ahora: 'tribunal', sabe: 'plasticidad', logros: 'cierre', caracter: 'onda', estirpe: 'onda' };
const SECCIONES_T5B = new Set(['caracter', 'estirpe']);
const PREFERENCIAS = 'ida.lab';

function parametros() { return new URLSearchParams(location.hash.split('?')[1] || ''); }

function tamano(bytes) {
  const b = Number(bytes) || 0;
  return b >= 1048576 ? `${(b / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1024))} KB`;
}

class IdaLab extends HTMLElement {
  constructor() {
    super();
    const pref = almacen.leer(PREFERENCIAS) || {};
    this.fuente = null;
    this.pos = 0;
    this.registro = null;
    this.analisis = null;
    this.vista = VISTAS.includes(pref.vista) ? pref.vista : 'latido';
    this.velocidad = VELOCIDADES.includes(pref.velocidad) ? pref.velocidad : 1;
    this.verNoMontados = false;
    this.sel = null;                 // {tipo: 'paso'|'pieza'|'componente', ...}
    this.reproduciendo = false;
    this.siguiendo = false;          // en directo, avanzar con cada latido nuevo
    this.cat = null;
    this.grabaciones = null;
    this.grabando = null;
    this.borrando = null;            // {id, testigo, grabacion}: primer paso del borrado hecho
    this.aviso = '';
    this._token = 0;
    this._cancelarAnimacion = () => {};
    this._alIdioma = () => this.pintar();
    this._alTema = () => this.dibujarEscena();
  }

  connectedCallback() {
    document.addEventListener('ida:idioma', this._alIdioma);
    document.addEventListener('ida:tema', this._alTema);
    this.addEventListener('click', (ev) => this.alClic(ev));
    this.addEventListener('keydown', (ev) => this.alTecla(ev));
    this.innerHTML = `<p class="suave">${esc(t('app.cargando'))}</p>`;
    this.iniciar();
  }

  disconnectedCallback() {
    document.removeEventListener('ida:idioma', this._alIdioma);
    document.removeEventListener('ida:tema', this._alTema);
    this.parar();
    clearInterval(this._sondeo);
    this._cancelarAnimacion();
  }

  guardarPreferencias() { almacen.guardar(PREFERENCIAS, { vista: this.vista, velocidad: this.velocidad }); }

  // --- arranque ------------------------------------------------------------------------------------------------------
  async iniciar() {
    const p = parametros();
    const seccion = p.get('seccion');
    if (VISTAS.includes(p.get('vista'))) this.vista = p.get('vista');
    if (seccion && SECCION_PASO[seccion]) {
      this.vista = 'latido';
      this.sel = { tipo: 'paso', id: SECCION_PASO[seccion] };
      this.aviso = t(SECCIONES_T5B.has(seccion) ? 'lab.desde_t5b' : 'lab.desde', { seccion: t(`tarjeta.${seccion}`) });
    }
    this.cat = await cargarCatalogo();
    this.pintar();
    this.cargarGrabaciones();
    const fuente = p.get('fuente');
    if (fuente === 'grabacion' && p.get('id')) {
      await this.abrirGrabacion(p.get('id'), Number(p.get('latido')) || null);
    } else if (fuente === 'directo' || !fuente) {
      await this.abrirDirecto(p.get('vida') != null ? { vida: Number(p.get('vida')), latido: Number(p.get('latido')) } : null, Boolean(fuente));
    }
  }

  // --- fuentes -------------------------------------------------------------------------------------------------------
  async usarFuente(fuente, posInicial) {
    this.parar();
    clearInterval(this._sondeo);
    this.fuente = fuente;
    this.siguiendo = false;
    await Promise.all([cargarSprites(fuente.mundo), cargarFrases(fuente.mundo)]);
    this.pintar();
    await this.ir(Math.max(0, Math.min(fuente.indice.length - 1, posInicial ?? fuente.indice.length - 1)));
    if (fuente.tipo === 'directo') this._sondeo = setInterval(() => this.sondear(), SONDEO_MS);
  }

  /** El directo; ``destino`` = {vida, latido} para ir a ese latido (desde el Vivero). ``avisar``: decir si no hay. */
  async abrirDirecto(destino, avisarSiNo = true) {
    try {
      const f = await new FuenteDirecto().cargar();
      if (!f.indice.length) {
        if (avisarSiNo) avisar(t('lab.directo_vacio'));
        if (!this.fuente) this.pintar();
        return;
      }
      let pos = null;
      if (destino) {
        const i = f.indice.findIndex((e) => e.vida === destino.vida && e.latido === destino.latido && !e.cierre);
        if (i >= 0) pos = i; else this.aviso = t('lab.latido_no_esta', { n: destino.latido, max: f.maximo });
      }
      await this.usarFuente(f, pos);
      this.siguiendo = pos == null;
      this.pintarMandos();
    } catch (err) {
      avisar(t(`error.${err.codigo || 'red'}`));
    }
  }

  async abrirGrabacion(id, latido = null) {
    try {
      const f = await new FuenteGrabacion(id).cargar();
      const i = latido != null ? f.indice.findIndex((e) => e.latido === latido) : 0;
      if (this.vista === 'grabaciones') this.vista = 'latido';
      await this.usarFuente(f, i >= 0 ? i : 0);
      history.replaceState(null, '', `#/lab?fuente=grabacion&id=${encodeURIComponent(id)}`);
    } catch (err) {
      avisar(t(`error.${err.codigo || 'red'}`));
    }
  }

  async abrirFichero(fichero) {
    try {
      const f = await new FuenteFichero(fichero).cargar();
      if (this.vista === 'grabaciones') this.vista = 'latido';
      await this.usarFuente(f, 0);
    } catch (err) {
      avisar(t('lab.fichero_invalido', { error: err.message || '' }));
    }
  }

  async sondear() {
    const f = this.fuente;
    if (!f || f.tipo !== 'directo') return;
    try {
      const { nueva, perdidas } = await f.refrescar();
      if (nueva) { await this.usarFuente(f, null); this.siguiendo = true; return; }
      this.pintarFuenteActual();
      this.pos = Math.max(0, this.pos - perdidas);
      if (this.siguiendo && !this.reproduciendo && this.pos < f.indice.length - 1) await this.ir(f.indice.length - 1, { animar: false });
      else this.pintarLinea();
    } catch { /* el servidor puede estar ocupado: se reintenta */ }
  }

  async cargarGrabaciones() {
    try {
      const d = await api.grabaciones();
      this.grabaciones = d.grabaciones;
      this.grabando = d.grabando;
    } catch (err) {
      this.grabaciones = [];
    }
    if (this.vista === 'grabaciones') this.pintarVista();
  }

  // --- navegación ----------------------------------------------------------------------------------------------------
  async ir(pos, { animar: conAnimacion = true } = {}) {
    const f = this.fuente;
    if (!f || !f.indice.length) return;
    pos = Math.max(0, Math.min(f.indice.length - 1, pos));
    this.pos = pos;
    const token = ++this._token;
    this.pintarLinea();
    let r;
    try {
      r = await f.registro(pos);
    } catch (err) {
      if (token === this._token) avisar(t(`error.${err.codigo || 'latido_fuera'}`));
      return;
    }
    if (token !== this._token) return;
    this.registro = r;
    this.analisis = analizar(r, this.cat);
    if (this.sel && this.sel.tipo === 'pieza' && !this.analisis.porClave.has(this.sel.clave)) this.sel = null;
    this.pintarResumen();
    this.dibujarEscena();
    this.pintarVista({ animar: conAnimacion && !this.reproduciendo });
    this.pintarDetalle();
  }

  reproducir() {
    if (!this.fuente) return;
    if (this.pos >= this.fuente.indice.length - 1) this.pos = -1;
    this.reproduciendo = true;
    this.siguiendo = false;
    this.pintarMandos();
    const avanzar = async () => {
      if (!this.reproduciendo) return;
      if (this.pos >= this.fuente.indice.length - 1) {
        if (this.fuente.tipo === 'directo') { this.siguiendo = true; }
        this.parar();
        return;
      }
      await this.ir(this.pos + 1, { animar: false });
      this._reloj = setTimeout(avanzar, 1000 / this.velocidad);
    };
    avanzar();
  }

  parar() {
    this.reproduciendo = false;
    clearTimeout(this._reloj);
    this.pintarMandos();
  }

  // --- estructura ----------------------------------------------------------------------------------------------------
  pintar() {
    const f = this.fuente;
    const pestanas = VISTAS.map((v) => `<button type="button" role="tab" data-vista="${v}" aria-selected="${this.vista === v}">${esc(t(`lab.vista.${v}`))}</button>`).join('');
    this.innerHTML = `
      <div class="lab-cabeza">
        <div><h1>${esc(t('lab.titulo'))}</h1><p class="suave">${esc(t('lab.subtitulo_t5a'))}</p></div>
        <div class="fuentes" role="group" aria-label="${esc(t('lab.fuente'))}">
          <span class="suave pequeno">${esc(t('lab.fuente'))}</span>
          <button type="button" class="boton pequeno ${f && f.tipo === 'directo' ? 'primario' : ''}" data-accion="directo">● ${esc(t('lab.fuente_directo'))}</button>
          <button type="button" class="boton pequeno ${f && f.tipo === 'grabacion' ? 'primario' : ''}" data-vista="grabaciones">🎞 ${esc(t('lab.fuente_grabacion'))}</button>
          <label class="boton pequeno ${f && f.tipo === 'fichero' ? 'primario' : ''}">📂 ${esc(t('lab.fuente_fichero'))}
            <input type="file" accept=".gz,.jsonl,.json" data-fichero hidden></label>
        </div>
      </div>
      ${this.aviso ? `<div class="aviso-caja info lab-aviso" role="status">${esc(this.aviso)}</div>` : ''}
      <section class="tarjeta reproductor" aria-label="${esc(t('lab.reproductor'))}" ${f ? '' : 'hidden'}>
        <div class="fuente-actual" data-fuente-actual></div>
        <div class="linea" data-linea></div>
        <div class="mandos-lab" data-mandos></div>
      </section>
      <div class="lab-rejilla ${f ? '' : 'sin-lateral'}">
        <div class="lab-principal">
          <div class="pestanas" role="tablist" aria-label="${esc(t('lab.vistas'))}">${pestanas}</div>
          <div class="lab-vista" data-vista-cuerpo role="tabpanel"></div>
        </div>
        <aside class="lab-lateral tarjeta" ${f ? '' : 'hidden'}>
          <div class="lab-escena">
            <div class="lienzo-marco"><canvas id="lab-lienzo" width="432" height="336" role="img" aria-label="${esc(t('lab.escena'))}"></canvas><pre hidden></pre></div>
            <div data-resumen></div>
          </div>
          <div class="lab-detalle" data-detalle aria-live="polite"></div>
        </aside>
      </div>`;
    this.querySelector('[data-fichero]').addEventListener('change', (ev) => {
      const fichero = ev.target.files && ev.target.files[0];
      if (fichero) this.abrirFichero(fichero);
    });
    this.pintarFuenteActual();
    this.pintarLinea();
    this.pintarMandos();
    this.pintarResumen();
    this.dibujarEscena();
    this.pintarVista({ animar: false });
    this.pintarDetalle();
  }

  pintarFuenteActual() {
    const caja = this.querySelector('[data-fuente-actual]');
    const f = this.fuente;
    if (!caja || !f) return;
    const mundo = t(`mundo.${f.mundo}.nombre`);
    let texto;
    if (f.tipo === 'directo') texto = t('lab.fuente_directo_info', { mundo, n: f.indice.length, max: f.maximo });
    else if (f.tipo === 'grabacion') texto = t('lab.fuente_grabacion_info', { id: f.id, mundo, n: f.indice.length, nivel: (f.cabecera || {}).nivel || '–' });
    else texto = t('lab.fuente_fichero_info', { nombre: f.nombre, mundo, n: f.indice.length });
    caja.innerHTML = `<span class="chip sin-punto ${f.tipo === 'directo' ? 'listo' : ''}">${esc(texto)}</span>${f.truncada ? ` <span class="chip aviso">${esc(t('lab.truncada'))}</span>` : ''}`;
  }

  pintarLinea() {
    const caja = this.querySelector('[data-linea]');
    const f = this.fuente;
    if (!caja || !f) return;
    const n = f.indice.length;
    const e = f.indice[this.pos] || {};
    caja.innerHTML = `${svgLinea(f.indice, this.pos, f.mundo)}
      <input type="range" min="0" max="${Math.max(0, n - 1)}" value="${this.pos}" data-deslizador aria-label="${esc(t('lab.linea_aria'))}"
        aria-valuetext="${esc(t('lab.latido_de', { latido: e.latido ?? '–', vida: e.vida ?? '–' }))}">
      <div class="leyenda-linea mini suave"><span class="m logro">★ ${esc(t('lab.hecho.logro'))}</span><span class="m aprende">● ${esc(t('lab.hecho.aprende'))}</span>
        <span class="m muere">✕ ${esc(t('lab.hecho.muere'))}</span><span class="m nace">▲ ${esc(t('lab.hecho.nace'))}</span><span class="m guillotina">| ${esc(t('lab.guillotina'))}</span></div>`;
    const svg = caja.querySelector('svg');
    svg.addEventListener('click', (ev) => {
      const marca = ev.target.closest('[data-pos]');
      this.parar();
      this.siguiendo = false;
      this.ir(marca ? Number(marca.dataset.pos) : posicionDeClic(svg, ev, n));
    });
    const desl = caja.querySelector('[data-deslizador]');
    desl.addEventListener('input', () => { this.parar(); this.siguiendo = false; this.ir(Number(desl.value), { animar: false }); });
    const entrada = this.querySelector('[data-ir]');
    if (entrada && document.activeElement !== entrada) entrada.value = e.latido ?? '';
    const etiqueta = this.querySelector('[data-posicion]');
    if (etiqueta) etiqueta.textContent = t('lab.posicion', { latido: e.latido ?? '–', vida: e.vida ?? '–', i: this.pos + 1, n });
  }

  pintarMandos() {
    const caja = this.querySelector('[data-mandos]');
    const f = this.fuente;
    if (!caja || !f) return;
    const enVivo = f.tipo === 'directo';
    caja.innerHTML = `
      <div class="segmentos" role="group" aria-label="${esc(t('lab.reproductor'))}">
        <button type="button" data-accion="inicio" title="${esc(t('lab.inicio'))}" aria-label="${esc(t('lab.inicio'))}">⏮</button>
        <button type="button" data-accion="atras" title="${esc(t('lab.atras'))}" aria-label="${esc(t('lab.atras'))}">◀︎</button>
        <button type="button" data-accion="${this.reproduciendo ? 'pausa' : 'reproducir'}" aria-pressed="${this.reproduciendo}"
          title="${esc(t(this.reproduciendo ? 'lab.pausa' : 'lab.reproducir'))}">${this.reproduciendo ? '❚❚' : '▶'} ${esc(t(this.reproduciendo ? 'lab.pausa' : 'lab.reproducir'))}</button>
        <button type="button" data-accion="adelante" title="${esc(t('lab.adelante'))}" aria-label="${esc(t('lab.adelante'))}">▶︎|</button>
        <button type="button" data-accion="fin" title="${esc(t(enVivo ? 'lab.seguir_directo' : 'lab.fin'))}" aria-pressed="${enVivo && this.siguiendo}">⏭${enVivo ? ` ${esc(t('lab.en_directo'))}` : ''}</button>
      </div>
      <form class="ir-a" data-form-ir><label class="mini" for="lab-ir">${esc(t('lab.ir_a'))}</label>
        <input class="entrada" id="lab-ir" type="number" min="0" data-ir value="${esc((f.indice[this.pos] || {}).latido ?? '')}">
        <button type="submit" class="boton pequeno">${esc(t('lab.ir'))}</button></form>
      <label class="mini velocidad">${esc(t('lab.velocidad'))}
        <select class="entrada" data-velocidad>${VELOCIDADES.map((v) => `<option value="${v}" ${v === this.velocidad ? 'selected' : ''}>${esc(t('lab.por_segundo', { n: v }))}</option>`).join('')}</select></label>
      <span class="mini suave" data-posicion></span>`;
    caja.querySelector('[data-form-ir]').addEventListener('submit', (ev) => {
      ev.preventDefault();
      const latido = Number(caja.querySelector('[data-ir]').value);
      const vida = (f.indice[this.pos] || {}).vida;
      let i = f.indice.findIndex((e) => e.latido === latido && e.vida === vida && !e.cierre);
      if (i < 0) i = f.indice.findIndex((e) => e.latido === latido);
      if (i < 0) { avisar(t('lab.latido_no_esta', { n: latido, max: f.indice.length })); return; }
      this.parar(); this.siguiendo = false; this.ir(i);
    });
    caja.querySelector('[data-velocidad]').addEventListener('change', (ev) => { this.velocidad = Number(ev.target.value); this.guardarPreferencias(); });
    this.pintarLinea();
  }

  pintarResumen() {
    const caja = this.querySelector('[data-resumen]');
    const r = this.registro;
    if (!caja || !r) return;
    const ac = r.accion;
    const hechos = (r.hechos || []).filter((h) => h.tipo !== 'estrategia').map((h) => hechoFrase(r.mundo, h)).filter(Boolean);
    caja.innerHTML = `<dl class="cifras compactas">
      <div><dt>${esc(t('lab.latido'))}</dt><dd>${r.latido}${r.cierre ? ` · ${esc(t('lab.registro_cierre'))}` : ''}</dd></div>
      <div><dt>${esc(t('lab.individuo'))}</dt><dd>${esc(r.individuo)} · ${esc(t('lab.vida_n', { n: r.vida }))}</dd></div>
      <div><dt>${esc(t('lab.accion'))}</dt><dd>${ac ? `${esc(ac.verbo)} ${esc(ac.objetivo)} <span class="suave">(${esc(ac.sistema)})</span>` : '–'}</dd></div>
      <div><dt>${esc(t('lab.afecto'))}</dt><dd>${esc((r.afecto && r.afecto.estado) || '–')}${r.cuerpo && r.cuerpo.dormido ? ` · 🌙` : ''}</dd></div></dl>
      ${hechos.length ? `<ul class="lista-simple hechos-latido">${hechos.slice(0, 4).map((h) => `<li>${esc(h)}</li>`).join('')}</ul>` : ''}`;
  }

  dibujarEscena() {
    const lienzo = this.querySelector('#lab-lienzo');
    const r = this.registro;
    if (!lienzo || !r || !this.fuente) return;
    const pre = lienzo.nextElementSibling;
    const ok = r.escena && dibujarEscena(lienzo, r.escena, this.fuente.mundo, { inventario: t('escena.inventario') });
    lienzo.hidden = !ok;
    lienzo.parentElement.dataset.tipo = ok ? r.escena.tipo : 'texto';
    pre.hidden = Boolean(ok);
    if (!ok) pre.textContent = r.vista || t('vivero.sin_escena');
  }

  // --- vistas --------------------------------------------------------------------------------------------------------
  pintarVista({ animar: conAnimacion = true } = {}) {
    const caja = this.querySelector('[data-vista-cuerpo]');
    if (!caja) return;
    this._cancelarAnimacion();
    this.querySelectorAll('[role="tab"][data-vista]').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.vista === this.vista)));
    const detalle = this.querySelector('[data-detalle]');
    if (detalle) detalle.hidden = this.vista === 'grabaciones';
    if (this.vista === 'grabaciones') { caja.innerHTML = this.htmlGrabaciones(); return; }
    if (!this.fuente) { caja.innerHTML = this.htmlSinFuente(); return; }
    const r = this.registro;
    if (!r) { caja.innerHTML = `<p class="suave">${esc(t('app.cargando'))}</p>`; return; }
    if (this.vista === 'latido') {
      caja.innerHTML = `<div class="latido-marco">${svgLatido(r, this.analisis, this.cat, this.sel)}</div>
        <p class="suave pequeno">${esc(t(sinMovimiento() ? 'lab.latido_ayuda_quieto' : 'lab.latido_ayuda'))}</p>`;
      if (conAnimacion) this._cancelarAnimacion = animar(caja.querySelector('svg'), this.analisis);
    } else {
      caja.innerHTML = htmlIngenieria(r, this.cat, this.fuente.medias, this.sel, { noMontados: this.verNoMontados });
    }
  }

  htmlSinFuente() {
    return `<div class="vacio-estado tarjeta"><h2>${esc(t('lab.sin_fuente_titulo'))}</h2><p>${esc(t('lab.sin_fuente_texto'))}</p>
      <div class="acciones"><a class="boton primario" href="#/antesala">${esc(t('vivero.ir_antesala'))}</a>
      <button type="button" class="boton" data-vista="grabaciones">🎞 ${esc(t('lab.vista.grabaciones'))}</button></div></div>`;
  }

  htmlGrabaciones() {
    const lista = this.grabaciones;
    if (lista == null) return `<p class="suave">${esc(t('app.cargando'))}</p>`;
    const filas = lista.map((g) => {
      const borrando = this.borrando && this.borrando.id === g.id;
      const tras = g.empieza_tras ? t('lab.desde_latido', { n: g.empieza_tras.latido }) : t('lab.desde_inicio');
      const abierta = this.fuente && this.fuente.tipo === 'grabacion' && this.fuente.id === g.id;
      return `<tr class="${abierta ? 'abierta' : ''}">
        <td><b>${esc(g.id)}</b>${g.en_curso ? ` <span class="chip falta grabando">${esc(t('grabar.grabando'))}</span>` : ''}${g.valida ? '' : ` <span class="chip aviso">${esc(t('lab.no_valida'))}</span>`}
          <br><span class="mini suave">${esc(t(`mundo.${g.mundo}.nombre`))} · ${esc(String(g.creada || '').replace('T', ' ').slice(0, 16))} · ${esc(tras)}</span></td>
        <td>${esc(g.nivel || '–')}</td><td>${g.registros ?? '–'}</td><td>${esc(tamano(g.bytes))}</td>
        <td><div class="acciones-fila">
          <button type="button" class="boton pequeno primario" data-abrir="${esc(g.id)}" ${g.en_curso || !g.valida ? 'disabled' : ''}>${esc(t('lab.abrir'))}</button>
          <a class="boton pequeno" href="${esc(descargas.grabacion(g.id))}" download ${g.en_curso ? 'aria-disabled="true" tabindex="-1"' : ''}>⬇ ${esc(t('lab.descargar'))}</a>
          ${borrando ? `<span class="confirmar-borrado" role="alert">${esc(t('lab.borrar_seguro', { id: g.id, n: g.registros ?? '?' }))}
              <button type="button" class="boton pequeno peligro" data-borrar-confirmar="${esc(g.id)}">${esc(t('lab.borrar_si'))}</button>
              <button type="button" class="boton pequeno discreto" data-borrar-cancelar>${esc(t('lab.cancelar'))}</button></span>`
    : `<button type="button" class="boton pequeno discreto peligro" data-borrar="${esc(g.id)}" ${g.en_curso ? 'disabled' : ''}>🗑 ${esc(t('lab.borrar'))}</button>`}
        </div></td></tr>`;
    }).join('');
    return `<div class="grabaciones">
      <div class="bloque-titulo"><h2>${esc(t('lab.vista.grabaciones'))}</h2>
        <button type="button" class="boton pequeno discreto" data-accion="refrescar-grabaciones">↻ ${esc(t('lab.refrescar'))}</button></div>
      <p class="suave">${esc(t('lab.grabaciones_ayuda'))}</p>
      ${this.grabando ? `<p class="aviso-caja info">${esc(t('lab.grabando_ahora', { id: this.grabando.id, n: this.grabando.registros }))}</p>` : ''}
      ${lista.length ? `<table class="tabla-lab grabaciones-tabla"><thead><tr><th>${esc(t('lab.grabacion'))}</th><th>${esc(t('lab.nivel'))}</th>
        <th>${esc(t('lab.registros'))}</th><th>${esc(t('lab.tamano'))}</th><th></th></tr></thead><tbody>${filas}</tbody></table>`
    : `<div class="vacio-estado"><p>${esc(t('lab.sin_grabaciones'))}</p></div>`}
    </div>`;
  }

  // --- detalle -------------------------------------------------------------------------------------------------------
  pintarDetalle() {
    const caja = this.querySelector('[data-detalle]');
    if (!caja) return;
    const r = this.registro;
    if (!r || !this.analisis) { caja.innerHTML = ''; return; }
    const s = this.sel;
    let html;
    if (!s) html = `<p class="suave">${esc(t(this.vista === 'ingenieria' ? 'lab.detalle_vacio_ing' : 'lab.detalle_vacio'))}</p>`;
    else if (s.tipo === 'paso') html = detallePaso(s.id, r, this.analisis, this.cat, this.fuente.medias);
    else if (s.tipo === 'pieza') html = detallePieza(s.clave, this.analisis);
    else if (s.tipo === 'componente') {
      // Abierta desde una pieza: la ficha del autor encima y la pieza debajo, las dos a la vista.
      html = this.htmlFicha(s);
      if (s.anterior && s.anterior.tipo === 'pieza') html += `<hr class="separador">${detallePieza(s.anterior.clave, this.analisis)}`;
    }
    else html = '';
    const volver = s && s.anterior ? `<button type="button" class="boton pequeno discreto volver" data-volver>← ${esc(t('lab.volver'))}</button>` : '';
    caja.innerHTML = volver + html;
    caja.scrollTop = 0;
  }

  htmlFicha(s) {
    if (!this.cat) return `<p class="suave">${esc(t('error.componentes_no_disponibles'))}</p>`;
    let c = null;
    if (s.autor) c = this.cat.deAutor(s.autor);
    else c = this.cat.componentes.find((x) => x.nombre === s.nombre && x.destino === s.destino && (!s.dueno || (x.dueno || '') === s.dueno));
    if (!c) return `<p class="suave">${esc(t('lab.sin_ficha', { autor: s.autor || s.nombre }))}</p>`;
    const tiempos = tiemposAgrupados(this.registro.tiempos_ms);
    const medias = mediasAgrupadas(this.fuente.medias && this.fuente.medias.tiempos_medios);
    return fichaComponente(c, this.cat, { tiempo: c.clave_tiempo ? tiempos[c.clave_tiempo] : undefined, media: c.clave_tiempo ? medias[c.clave_tiempo] : undefined, mundo: this.fuente.mundo });
  }

  elegir(sel) {
    const anterior = this.sel && this.sel.tipo !== sel.tipo ? this.sel : (this.sel && this.sel.anterior) || null;
    this.sel = { ...sel, anterior: sel.tipo === 'paso' ? null : anterior };
    if (this.vista === 'latido' && sel.tipo === 'paso') {
      this.querySelectorAll('.latido-svg .nodo').forEach((n) => n.querySelector('.caja')?.classList.toggle('elegido', n.dataset.paso === sel.id));
    }
    if (this.vista === 'ingenieria') this.pintarVista({ animar: false });
    this.pintarDetalle();
    const detalle = this.querySelector('[data-detalle]');
    if (detalle && window.matchMedia('(max-width: 1100px)').matches) detalle.scrollIntoView({ behavior: sinMovimiento() ? 'auto' : 'smooth', block: 'start' });
  }

  // --- eventos ---------------------------------------------------------------------------------------------------------
  alClic(ev) {
    const el = ev.target.closest('[data-accion],[data-vista],[data-paso],[data-pieza],[data-comp],[data-comp-nombre],[data-abrir],[data-borrar],[data-borrar-confirmar],[data-borrar-cancelar],[data-volver],[data-no-montados]');
    if (!el || !this.contains(el)) return;
    const d = el.dataset;
    if (d.accion) return this.accion(d.accion);
    if (el.matches('[role="tab"], [data-vista]') && d.vista) {
      this.vista = d.vista;
      this.guardarPreferencias();
      if (d.vista === 'grabaciones') this.cargarGrabaciones();
      this.pintarVista({ animar: d.vista === 'latido' });
      this.pintarDetalle();
      return;
    }
    if (d.paso) return this.elegir({ tipo: 'paso', id: d.paso });
    if (d.pieza) return this.elegir({ tipo: 'pieza', clave: d.pieza });
    if (d.comp) return this.elegir({ tipo: 'componente', autor: d.comp });
    if (d.compNombre) return this.elegir({ tipo: 'componente', nombre: d.compNombre, destino: d.compDestino, dueno: d.compDueno || '' });
    if (d.abrir) return this.abrirGrabacion(d.abrir);
    if (d.borrar) return this.pedirBorrado(d.borrar);
    if ('borrarConfirmar' in d) return this.confirmarBorrado(d.borrarConfirmar);
    if ('borrarCancelar' in d) { this.borrando = null; this.pintarVista(); return; }
    if ('volver' in d && this.sel && this.sel.anterior) { this.sel = this.sel.anterior; this.pintarDetalle(); return; }
    if ('noMontados' in d) { this.verNoMontados = el.checked; this.pintarVista({ animar: false }); }
  }

  alTecla(ev) {
    const nodo = ev.target.closest && ev.target.closest('.nodo[data-paso]');
    if (nodo && (ev.key === 'Enter' || ev.key === ' ')) { ev.preventDefault(); this.elegir({ tipo: 'paso', id: nodo.dataset.paso }); }
  }

  accion(nombre) {
    const f = this.fuente;
    switch (nombre) {
      case 'directo': this.abrirDirecto(null, true); break;
      case 'refrescar-grabaciones': this.cargarGrabaciones(); break;
      case 'reproducir': this.reproducir(); break;
      case 'pausa': this.parar(); break;
      case 'inicio': this.parar(); this.siguiendo = false; this.ir(0); break;
      case 'atras': this.parar(); this.siguiendo = false; this.ir(this.pos - 1); break;
      case 'adelante': this.parar(); this.siguiendo = false; this.ir(this.pos + 1); break;
      case 'fin':
        this.parar();
        this.siguiendo = Boolean(f && f.tipo === 'directo');
        this.ir(f ? f.indice.length - 1 : 0);
        this.pintarMandos();
        break;
      default: break;
    }
  }

  async pedirBorrado(id) {
    try {
      const d = await api.pedirBorradoGrabacion(id);
      this.borrando = { id, testigo: d.testigo, grabacion: d.grabacion };
    } catch (err) {
      avisar(t(`error.${err.codigo || 'red'}`));
    }
    this.pintarVista();
    this.querySelector('[data-borrar-confirmar]')?.focus();
  }

  async confirmarBorrado(id) {
    const b = this.borrando;
    if (!b || b.id !== id) return;
    try {
      await api.confirmarBorradoGrabacion(id, b.testigo);
      avisar(t('lab.borrada', { id }));
      if (this.fuente && this.fuente.tipo === 'grabacion' && this.fuente.id === id) { this.fuente = null; this.registro = null; this.pintar(); }
    } catch (err) {
      avisar(t(`error.${err.codigo || 'red'}`));
    }
    this.borrando = null;
    await this.cargarGrabaciones();
  }
}

customElements.define('ida-lab', IdaLab);
