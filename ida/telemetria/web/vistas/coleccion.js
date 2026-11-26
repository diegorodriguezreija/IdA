// Colección (O9, O10; sección 13 del diseño): por mundo, el compañero, las estirpes archivadas y las fichas guardadas,
// con su ranking (mejor Score) y las acciones: guardar, adoptar, renombrar, exportar, importar y borrar.
// Nada se borra sin confirmación: «Borrar» pide al servidor un testigo y enseña lo que se perdería; solo el segundo
// clic, con ese testigo, borra. Adoptar y archivar nunca borran: el compañero de antes queda archivado aquí.

import { api, descargas } from '../api.js';
import { t } from '../i18n.js';
import { avisar, esc } from '../componentes/util.js';
import { radar } from '../componentes/radar.js';

const RASGOS = ['apertura', 'responsabilidad', 'neuroticismo', 'extraversion', 'umbral_miedo'];
const ICONOS = { companero: '🌱', estirpe: '🌳', ficha: '🧬' };

function vidas(n) { return Number(n) === 1 ? t('coleccion.vidas_1') : t('coleccion.vidas', { n }); }
function puntos(v) { return v == null || !Number.isFinite(Number(v)) ? '–' : String(Math.round(Number(v))); }
function fecha(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? String(iso) : d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

class IdaColeccion extends HTMLElement {
  constructor() {
    super();
    this.datos = null;
    this.error = '';
    this.mundo = '';                 // filtro ('' = todos)
    this.renombrando = null;         // id del elemento que se está renombrando
    this.borrando = null;            // {id, testigo, elemento}: primer paso dado, falta confirmar
    this.ocupado = false;
    this._alIdioma = () => this.pintar();
  }

  connectedCallback() {
    document.addEventListener('ida:idioma', this._alIdioma);
    this.innerHTML = `<p class="suave">${esc(t('coleccion.cargando'))}</p>`;
    this.cargar();
  }

  disconnectedCallback() { document.removeEventListener('ida:idioma', this._alIdioma); }

  async cargar() {
    try {
      this.datos = await api.coleccion();
      this.error = '';
    } catch (err) {
      this.error = t(`error.${err.codigo || 'red'}`);
    }
    this.pintar();
  }

  mundos() {
    const r = (this.datos && this.datos.ranking) || {};
    return Object.keys(r).sort((a, b) => (a === 'crafter' ? -1 : b === 'crafter' ? 1 : a.localeCompare(b)));
  }

  // --- pintado -------------------------------------------------------------------------------------------------------
  pintar() {
    if (this.error) {
      this.innerHTML = `<div class="aviso-caja" role="alert">${esc(this.error)}
        <button type="button" class="boton pequeno" data-accion="recargar">${esc(t('mundos.reintentar'))}</button></div>`;
      this.conectar();
      return;
    }
    if (!this.datos) return;
    const mundos = this.mundos();
    if (this.mundo && !mundos.includes(this.mundo)) this.mundo = '';
    const filtro = mundos.length > 1 ? `<div class="segmentos" role="group" aria-label="${esc(t('coleccion.filtro'))}">
        <button type="button" data-filtro="" aria-pressed="${this.mundo === ''}">${esc(t('coleccion.todos'))}</button>
        ${mundos.map((m) => `<button type="button" data-filtro="${esc(m)}" aria-pressed="${this.mundo === m}">${esc(t(`mundo.${m}.nombre`))}</button>`).join('')}</div>` : '';
    const secciones = mundos.filter((m) => !this.mundo || m === this.mundo).map((m) => this.htmlMundo(m)).join('');
    this.innerHTML = `
      <div class="antesala-cabeza">
        <div><h1>🗂️ ${esc(t('coleccion.titulo'))}</h1><p>${esc(t('coleccion.subtitulo'))}</p></div>
        <div class="coleccion-mandos">
          <label class="boton pequeno" for="importar-ficha">📂 ${esc(t('coleccion.importar'))}</label>
          <input type="file" id="importar-ficha" accept=".json,application/json" class="oculto">
          <a class="boton pequeno discreto" href="#/vivero">← ${esc(t('coleccion.volver'))}</a>
        </div>
      </div>
      ${filtro}
      <div aria-live="polite" data-zona-aviso></div>
      ${secciones || `<div class="tarjeta vacio-estado"><h2>${esc(t('coleccion.vacia_titulo'))}</h2><p>${esc(t('coleccion.vacia_texto'))}</p>
        <a class="boton primario" href="#/antesala">${esc(t('vivero.ir_antesala'))}</a></div>`}
      <p class="suave pequeno nota-coleccion">${esc(t('coleccion.nota_score'))}</p>`;
    this.conectar();
  }

  htmlMundo(mundo) {
    const lista = (this.datos.ranking || {})[mundo] || [];
    const filas = lista.map((x) => this.htmlFila(x)).join('');
    return `<section class="tarjeta bloque coleccion-mundo" aria-labelledby="col-${esc(mundo)}">
      <h2 id="col-${esc(mundo)}">${esc(t(`mundo.${mundo}.nombre`))} <span class="suave pequeno">· ${esc(t('coleccion.ranking'))}</span></h2>
      <ol class="ranking">${filas}</ol></section>`;
  }

  elementoDe(x) {
    if (x.tipo === 'companero') return (this.datos.companeros || []).find((c) => c.mundo === x.mundo) || {};
    const lista = x.tipo === 'ficha' ? this.datos.fichas : this.datos.estirpes;
    return (lista || []).find((e) => e.id === x.id) || {};
  }

  htmlFila(x) {
    const el = this.elementoDe(x);
    const tipo = t(`coleccion.tipo.${x.tipo}`);
    const nombre = this.renombrando && this.renombrando === x.id
      ? `<form class="renombrar" data-renombrar="${esc(x.id)}"><label class="oculto" for="nombre-${esc(x.id)}">${esc(t('coleccion.nuevo_nombre'))}</label>
          <input class="entrada" id="nombre-${esc(x.id)}" maxlength="60" required value="${esc(x.nombre || '')}">
          <button type="submit" class="boton pequeno primario">${esc(t('coleccion.guardar_nombre'))}</button>
          <button type="button" class="boton pequeno discreto" data-accion="cancelar">${esc(t('coleccion.cancelar'))}</button></form>`
      : `<b>${esc(x.nombre || x.individuo || '–')}</b>`;
    const detalles = [
      x.individuo && x.individuo !== x.nombre ? x.individuo : '',
      x.generacion ? t('vivero.generacion', { n: x.generacion }) : '',
      el.vidas != null ? vidas(el.vidas) : el.generaciones != null ? vidas(el.generaciones) : '',
      x.tipo === 'estirpe' ? t('coleccion.archivada', { fecha: fecha(el.fecha), motivo: t(`coleccion.motivo.${el.motivo || 'archivar'}`) })
        : x.tipo === 'ficha' ? t('coleccion.guardada', { fecha: fecha(el.fecha) }) : t('coleccion.companero_ayuda'),
    ].filter(Boolean).map((d) => `<span>${esc(d)}</span>`).join(' · ');
    const avisos = (el.avisos || []).length ? `<details class="avisos"><summary>⚠️ ${esc(t('coleccion.avisos', { n: el.avisos.length }))}</summary>
      <ul class="lista-simple pequeno">${el.avisos.map((a) => `<li>${esc(a)}</li>`).join('')}</ul></details>` : '';
    const incompleta = el.incompleta ? `<span class="chip falta">${esc(t('coleccion.incompleta'))}</span>` : '';
    const acciones = this.htmlAcciones(x, el);
    const confirmar = this.borrando && this.borrando.id === x.id ? `<div class="confirmar-borrado" role="alertdialog" aria-labelledby="borrar-${esc(x.id)}">
        <p id="borrar-${esc(x.id)}"><b>${esc(t('coleccion.borrar_pregunta', { nombre: x.nombre || x.id }))}</b><br>
          <span class="pequeno">${esc(t(x.tipo === 'estirpe' ? 'coleccion.borrar_estirpe' : 'coleccion.borrar_ficha'))}</span></p>
        <button type="button" class="boton pequeno peligro" data-accion="confirmar-borrado" data-id="${esc(x.id)}">${esc(t('coleccion.borrar_si'))}</button>
        <button type="button" class="boton pequeno discreto" data-accion="cancelar">${esc(t('coleccion.cancelar'))}</button></div>` : '';
    const arq = el.arquetipo && Object.values(el.arquetipo).some((v) => v != null) ? radar(el.arquetipo, RASGOS, { titulo: x.nombre || '' }) : '';
    return `<li class="fila-coleccion tipo-${esc(x.tipo)}" data-fila="${esc(x.id || `companero-${x.mundo}`)}">
      <span class="puesto" aria-label="${esc(t('coleccion.puesto', { n: x.puesto }))}">${x.puesto === 1 ? '🏆' : `#${esc(x.puesto)}`}</span>
      <span class="mini-radar">${arq}</span>
      <div class="cuerpo-fila"><div class="nombre-fila"><span class="chip sin-punto tipo">${ICONOS[x.tipo]} ${esc(tipo)}</span> ${nombre} ${incompleta}</div>
        <div class="suave pequeno">${detalles}</div>${avisos}${confirmar}</div>
      <div class="score-fila"><b>${esc(puntos(x.mejor_score))}</b><span class="suave pequeno">${esc(t('coleccion.mejor_score'))}</span></div>
      <div class="acciones-fila">${acciones}</div></li>`;
  }

  htmlAcciones(x, el) {
    const b = (accion, texto, extra = '') => `<button type="button" class="boton pequeno ${extra}" data-accion="${accion}" data-id="${esc(x.id || '')}" data-mundo="${esc(x.mundo)}" ${this.ocupado ? 'disabled' : ''}>${texto}</button>`;
    if (x.tipo === 'companero') {
      return `${b('guardar', `💾 ${esc(t('estirpe.guardar'))}`)}
        <a class="boton pequeno discreto" href="${esc(descargas.companero(x.mundo))}" download>⬇️ ${esc(t('coleccion.exportar'))}</a>
        ${b('archivar', `📦 ${esc(t('coleccion.archivar'))}`, 'discreto')}`;
    }
    return `${el.incompleta ? '' : b('adoptar', `🌱 ${esc(t('coleccion.adoptar'))}`, 'primario')}
      ${b('renombrar', `✏️ ${esc(t('coleccion.renombrar'))}`, 'discreto')}
      <a class="boton pequeno discreto" href="${esc(descargas.elemento(x.id))}" download>⬇️ ${esc(t('coleccion.exportar'))}</a>
      ${b('borrar', `🗑️ ${esc(t('coleccion.borrar'))}`, 'peligro')}`;
  }

  // --- acciones ------------------------------------------------------------------------------------------------------
  conectar() {
    this.querySelector('[data-accion="recargar"]')?.addEventListener('click', () => this.cargar());
    this.querySelectorAll('[data-filtro]').forEach((b) => b.addEventListener('click', () => { this.mundo = b.dataset.filtro; this.pintar(); }));
    this.querySelector('#importar-ficha')?.addEventListener('change', (ev) => this.importar(ev.target.files[0]));
    this.querySelectorAll('button[data-accion]').forEach((b) => b.addEventListener('click', () => this.accion(b.dataset.accion, b.dataset)));
    const form = this.querySelector('form[data-renombrar]');
    if (form) {
      form.addEventListener('submit', (ev) => { ev.preventDefault(); this.renombrar(form.dataset.renombrar, form.querySelector('input').value); });
      form.querySelector('input').focus();
    }
  }

  async accion(accion, { id, mundo }) {
    if (accion === 'cancelar') { this.renombrando = null; this.borrando = null; this.pintar(); return; }
    if (accion === 'renombrar') { this.renombrando = id; this.borrando = null; this.pintar(); return; }
    this.ocupado = true;
    try {
      if (accion === 'guardar') {
        const { ficha } = await api.guardar(mundo);
        avisar(t('estirpe.guardada', { nombre: ficha.nombre }));
      } else if (accion === 'archivar') {
        if (!window.confirm(t('coleccion.archivar_pregunta'))) return;
        await api.archivar(mundo);
        avisar(t('coleccion.archivado'));
      } else if (accion === 'adoptar') {
        const hay = (this.datos.companeros || []).find((c) => c.mundo === mundo);
        if (hay && !window.confirm(t('coleccion.adoptar_pregunta', { actual: hay.nombre || hay.individuo }))) return;
        const r = await api.adoptar(id);
        avisar(t('coleccion.adoptado', { nombre: r.companero.nombre || r.companero.individuo }));
      } else if (accion === 'borrar') {
        // Primer paso: el servidor da un testigo y no borra nada todavía
        const r = await api.pedirBorrado(id);
        this.borrando = { id, testigo: r.testigo };
        this.renombrando = null;
      } else if (accion === 'confirmar-borrado') {
        if (!this.borrando || this.borrando.id !== id) return;
        await api.confirmarBorrado(id, this.borrando.testigo);
        this.borrando = null;
        avisar(t('coleccion.borrado'));
      }
      await this.recargar();
    } catch (err) {
      if (accion === 'confirmar-borrado') this.borrando = null;
      avisar(`${t(`error.${err.codigo || 'red'}`)}${err.message && err.codigo !== 'red' ? ` ${err.message}` : ''}`);
      this.pintar();
    } finally {
      this.ocupado = false;
      this.pintar();
    }
  }

  async recargar() {
    try { this.datos = await api.coleccion(); } catch (err) { this.error = t(`error.${err.codigo || 'red'}`); }
  }

  async renombrar(id, nombre) {
    try {
      await api.renombrar(id, nombre);
      this.renombrando = null;
      await this.recargar();
    } catch (err) {
      avisar(t(`error.${err.codigo || 'red'}`));
    }
    this.pintar();
  }

  async importar(fichero) {
    if (!fichero) return;
    let doc;
    try {
      doc = JSON.parse(await fichero.text());
    } catch {
      avisar(t('empezar.ficha_error'));
      return;
    }
    try {
      const r = await api.importar(doc);
      avisar(r.avisos && r.avisos.length ? t('coleccion.importada_avisos', { nombre: r.ficha.nombre, n: r.avisos.length })
        : t('coleccion.importada', { nombre: r.ficha.nombre }));
      this.mundo = r.ficha.mundo;
      await this.recargar();
    } catch (err) {
      avisar(`${t(`error.${err.codigo || 'red'}`)}${err.message && err.codigo !== 'red' ? ` ${err.message}` : ''}`);
    }
    this.pintar();
  }
}

customElements.define('ida-coleccion', IdaColeccion);
