// Antesala (O1, O8, O16, O17): elegir mundo (e instalarlo si falta), carácter y los detalles de la vida, y lanzarla.
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
  crafter: { latidos: 600, generaciones: 3 },
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
      ficha: null, fichaNombre: '', fichaError: '',
      opciones: {}, semilla: 1, latidos: 300, generaciones: 1, sin_experiencia: false, tabula_rasa: false,
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
      const [m, p] = await Promise.all([api.mundos(), this.e.presets ? null : api.presets()]);
      this.e.mundos = m.mundos;
      if (p) { this.e.presets = p.presets; this.e.rasgos = p.rasgos; this.e.rangos = p.rangos; }
      for (const mundo of this.e.mundos) {             // una instalación que siguió mientras no se veía la página
        const inst = mundo.instalacion;
        if (inst && inst.estado === 'en_curso' && !this.e.instalaciones[mundo.nombre]) this.seguirInstalacion(mundo.nombre, inst.id);
      }
      if (!this.mundo()) this.e.mundo = 'crafter';
      this.elegirMundo(this.e.mundo, false);
    } catch (err) {
      this.e.error = t(`error.${err.codigo || 'red'}`);
    }
    this.pintar();
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
      if (this.e.ficha && this.e.ficha.mundo && String(this.e.ficha.mundo).toLowerCase() !== nombre) this.quitarFicha(false);
    }
    this.guardar();
    if (pintar) this.pintar();
  }

  guardar() {
    almacen.guardar(GUARDADO, { mundo: this.e.mundo, caracter: this.e.caracter === 'ficha' ? 'optimo' : this.e.caracter });
  }

  arquetipoActual() {
    const e = this.e;
    if (e.caracter === 'personalizado' || e.caracter === 'ficha') return e.arquetipo;
    const p = (e.presets || []).find((x) => x.id === e.caracter);
    if (!p) return null;
    if (p.por_mundo) return p.por_mundo[e.mundo] || null;
    return p.arquetipo;
  }

  nombreCaracter() {
    const e = this.e;
    if (e.caracter === 'personalizado') return t('caracter.personalizado');
    if (e.caracter === 'ficha') return t('caracter.de_ficha');
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
    const tarjeta = (id, icono, nombre, desc, arq) => `<button type="button" role="radio" class="tarjeta preset" data-preset="${esc(id)}" aria-checked="${e.caracter === id}">
        <span class="icono" aria-hidden="true">${icono}</span><b>${esc(nombre)}</b>
        ${radar(arq, rasgos, { titulo: nombre })}
        <small>${esc(desc)}</small></button>`;
    let tarjetas = e.presets.map((p) => tarjeta(p.id, p.icono, texto(p.nombre), texto(p.descripcion),
      p.por_mundo ? p.por_mundo[e.mundo] : p.arquetipo)).join('');
    if (e.caracter === 'personalizado') tarjetas += tarjeta('personalizado', '🎛️', t('caracter.personalizado'), t('caracter.personalizado_desc'), e.arquetipo);
    if (e.ficha && e.arquetipo && e.caracter === 'ficha') tarjetas += tarjeta('ficha', '🧬', t('caracter.de_ficha'), t('caracter.de_ficha_desc'), e.arquetipo);
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
    const fichaHtml = e.ficha
      ? `<span class="chip listo">${esc(t('empezar.ficha_cargada', { nombre: e.fichaNombre }))}</span>
         <button type="button" class="boton pequeno discreto" data-accion="quitar-ficha">${esc(t('empezar.ficha_quitar'))}</button>`
      : `<label class="boton pequeno" for="ficha">📂 ${esc(t('empezar.ficha'))}</label>`;
    const arq = this.arquetipoActual();
    return `<div class="paso-titulo"><h2 tabindex="-1">${esc(t('empezar.titulo'))}</h2><p>${esc(t('empezar.pista'))}</p></div>
      <div class="empezar">
        <form id="form-vida" novalidate>
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
              <div class="campo"><label class="interruptor"><input type="checkbox" id="tabula_rasa" ${e.tabula_rasa ? 'checked' : ''}>
                <span>${esc(t('empezar.tabula_rasa'))}</span></label><small>${esc(t('empezar.tabula_rasa_ayuda'))}</small></div>
            </div>
          </details>
          <section class="tarjeta bloque">
            <div class="ficha-fila">${fichaHtml}<input type="file" id="ficha" accept=".json,application/json" class="oculto">
              <small class="suave">${esc(t('empezar.ficha_ayuda'))}</small></div>
            ${e.fichaError ? `<p class="error-texto" role="alert">${esc(e.fichaError)}</p>` : ''}
          </section>
        </form>
        <aside class="tarjeta resumen" aria-labelledby="resumen-titulo">
          <h3 id="resumen-titulo">${esc(t('resumen.titulo'))}</h3>
          ${radar(arq, e.rasgos, { titulo: this.nombreCaracter() })}
          <dl>
            <dt>${esc(t('resumen.mundo'))}</dt><dd>${spriteHtml(m.nombre)}<span>${esc(nombreMundo)}</span></dd>
            <dt>${esc(t('resumen.caracter'))}</dt><dd>${esc(this.nombreCaracter())}</dd>
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
      if (e.caracter !== 'personalizado' && e.caracter !== 'ficha') e.arquetipo = null;
      this.guardar();
      this.pintar();
      this.querySelector(`[data-preset="${CSS.escape(e.caracter)}"]`)?.focus();
    }));
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
    this.querySelector('#tabula_rasa').addEventListener('change', (ev) => { e.tabula_rasa = ev.target.checked; });
    conectarOpciones(form, this.mundo().opciones || [], (nombre, valor) => { e.opciones[nombre] = valor; });
    this.querySelector('[data-accion="recomendados"]')?.addEventListener('click', () => {
      e.opciones = Object.fromEntries((this.mundo().opciones || []).map((d) => [d.nombre, d.defecto]));
      this.pintar();
    });
    this.querySelector('#ficha').addEventListener('change', (ev) => this.leerFicha(ev.target.files[0]));
    this.querySelector('[data-accion="quitar-ficha"]')?.addEventListener('click', () => this.quitarFicha());
    form.addEventListener('submit', (ev) => { ev.preventDefault(); this.lanzar(); });
  }

  async leerFicha(fichero) {
    const e = this.e;
    if (!fichero) return;
    e.fichaError = '';
    try {
      const doc = JSON.parse(await fichero.text());
      if (!doc || typeof doc !== 'object' || Array.isArray(doc)) throw new Error('forma');
      const de = String(doc.mundo || '').toLowerCase();
      if (de && de !== e.mundo) {
        e.fichaError = t('empezar.ficha_otro_mundo', { mundo: t(`mundo.${de}.nombre`) });
        this.pintar();
        return;
      }
      let arq = doc.arquetipo || doc.arquetipo_actual;
      if (!arq && Array.isArray(doc.generaciones) && doc.generaciones.length) arq = doc.generaciones[doc.generaciones.length - 1].arquetipo;
      if (!arq && !doc.legado) throw new Error('vacía');
      e.ficha = doc;
      e.fichaNombre = doc.individuo || fichero.name;
      if (arq) {
        e.arquetipo = Object.fromEntries(e.rasgos.map((r) => [r, Number(arq[r] ?? 0.5)]));
        e.caracter = 'ficha';
      }
    } catch {
      e.fichaError = t('empezar.ficha_error');
    }
    this.pintar();
  }

  quitarFicha(pintar = true) {
    const e = this.e;
    e.ficha = null;
    e.fichaNombre = '';
    e.fichaError = '';
    if (e.caracter === 'ficha') { e.caracter = 'optimo'; e.arquetipo = null; }
    if (pintar) this.pintar();
  }

  cuerpoVida(reemplazar) {
    const e = this.e;
    const cuerpo = {
      mundo: e.mundo, opciones: e.opciones, semilla: e.semilla, latidos: e.latidos, generaciones: e.generaciones,
      sin_experiencia: e.sin_experiencia, tabula_rasa: e.tabula_rasa,
    };
    if (e.ficha) cuerpo.ficha = e.ficha;
    if (e.caracter === 'personalizado') cuerpo.arquetipo = e.arquetipo;
    else if (e.caracter !== 'ficha') cuerpo.caracter = e.caracter;
    if (reemplazar) cuerpo.reemplazar = true;
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
    e.lanzando = true;
    e.errorLanzar = '';
    this.pintar();
    try {
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
