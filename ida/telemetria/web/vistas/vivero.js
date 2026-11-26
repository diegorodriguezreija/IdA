// Vivero (O1, O3, O9): esqueleto de T3. Escena en directo desde la SSE (dibujo.js, el mismo del visor), barra de
// ritmo (pausa, ×1, ×4, máximo; fija en los mundos de tiempo real), cuerpo básico del nivel vital y botón Parar.
// El Vivero completo (diario de hechos, logros, compañero, colección) es T4.

import { api, escuchar } from '../api.js';
import { t } from '../i18n.js';
import { cargarSprites, dibujarEscena } from '../dibujo.js';
import { avisar, esc } from '../componentes/util.js';

const RITMOS = ['pausa', 'x1', 'x4', 'max'];
const ICONOS_RITMO = { pausa: '❚❚', x1: '▶', x4: '▶▶', max: '⏭' };
const MEDIDORES = ['vitalidad', 'alimentacion', 'energia', 'descanso'];

class IdaVivero extends HTMLElement {
  constructor() {
    super();
    this.vida = null;
    this.registro = null;
    this.escena = null;
    this.pendiente = false;
    this.cerrar = null;
    this._alIdioma = () => this.pintar();
    this._alTema = () => this.dibujar();
  }

  connectedCallback() {
    document.addEventListener('ida:idioma', this._alIdioma);
    document.addEventListener('ida:tema', this._alTema);
    this.innerHTML = `<p class="suave">${esc(t('vivero.conectando'))}</p>`;
    this.iniciar();
  }

  disconnectedCallback() {
    document.removeEventListener('ida:idioma', this._alIdioma);
    document.removeEventListener('ida:tema', this._alTema);
    if (this.cerrar) this.cerrar();
  }

  async iniciar() {
    try {
      this.vida = (await api.vidaActual()).vida;
    } catch (err) {
      this.innerHTML = `<div class="aviso-caja" role="alert">${esc(t(`error.${err.codigo || 'red'}`))}</div>`;
      return;
    }
    if (this.vida) await cargarSprites(this.vida.mundo);
    this.pintar();
    this.cerrar = escuchar('vidas/actual/registro?nivel=vital', {
      vida: async (v) => {
        const nueva = !this.vida || v.id !== this.vida.id;
        this.vida = v;
        if (nueva) { this.registro = null; this.escena = null; await cargarSprites(v.mundo); }
        this.pintar();
      },
      registro: (r) => {
        if (this.registro && r.vida !== this.registro.vida) this.escena = null;
        this.registro = r;
        if (r.escena) this.escena = r.escena;
        this.programar();
      },
      ritmo: (d) => { if (this.vida) { this.vida.ritmo = d.ritmo; this.pintarRitmo(); } },
      fin: (v) => { this.vida = v; this.pintar(); },
    });
  }

  /** Un dibujo por fotograma como mucho: a ritmo máximo llegan muchos registros por segundo. */
  programar() {
    if (this.pendiente) return;
    this.pendiente = true;
    requestAnimationFrame(() => {
      this.pendiente = false;
      this.dibujar();
      this.pintarCuerpo();
    });
  }

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
    this.innerHTML = `
      <div class="paso-titulo"><h1>${esc(t('vivero.titulo'))}</h1><p class="suave pequeno">${esc(t('vivero.esqueleto'))}</p></div>
      ${fin}
      <div class="vivero" style="margin-top:${fin ? '16px' : '0'}">
        <section class="tarjeta escenario" aria-labelledby="vivero-quien">
          <div class="escenario-cabeza">
            <div class="quien"><h2 id="vivero-quien" data-individuo>${esc(v.individuo || nombreMundo)}</h2>
              <span class="chip sin-punto">${esc(nombreMundo)}</span>
              <span class="chip sin-punto" data-generacion></span></div>
            <span class="chip listo" data-latido>${esc(t('vivero.latido', { n: v.latido ?? 0 }))}</span>
          </div>
          <div class="lienzo-marco"><canvas id="vivero-lienzo" width="432" height="336" role="img" aria-label="${esc(nombreMundo)}"></canvas><pre hidden></pre></div>
          <div class="bloque-titulo">
            <div class="segmentos" role="group" aria-label="${esc(t('vivero.ritmo'))}" data-ritmos></div>
            <div style="display:flex; gap:10px; align-items:center">
              <a class="boton pequeno discreto" href="/panel">${esc(t('vivero.panel_clasico'))} ↗</a>
              <button type="button" class="boton pequeno peligro" data-parar ${v.activa ? '' : 'disabled'}>■ ${esc(t('vivero.parar'))}</button>
            </div>
          </div>
          <p class="suave pequeno" data-ritmo-nota ${v.ritmo_ajustable ? 'hidden' : ''}>⏱ ${esc(t('vivero.ritmo_fijo'))}</p>
        </section>
        <div class="panel-lateral">
          <section class="tarjeta" aria-labelledby="vivero-cuerpo">
            <h3 id="vivero-cuerpo">${esc(t('vivero.cuerpo'))}</h3>
            ${MEDIDORES.map((m) => `<div class="medidor ${m}"><span>${esc(t(`cuerpo.${m}`))}</span>
              <div class="pista-barra" role="meter" aria-label="${esc(t(`cuerpo.${m}`))}" aria-valuemin="0" aria-valuemax="100" data-barra="${m}"><i style="width:0"></i></div>
              <output data-valor="${m}">–</output></div>`).join('')}
            <div class="animo"><span class="suave">${esc(t('vivero.animo'))}</span><span class="chip" data-animo>–</span></div>
          </section>
          <section class="tarjeta">
            <h3>${esc(t('vivero.accion'))}</h3>
            <div class="accion" data-accion>${esc(t('vivero.sin_accion'))}</div>
          </section>
          <section class="tarjeta">
            <h3>${esc(t('vivero.puntuacion'))}</h3>
            <div class="puntos" data-puntos></div>
            <p class="suave pequeno" data-logros></p>
          </section>
        </div>
      </div>`;
    this.querySelector('[data-parar]').addEventListener('click', () => this.parar());
    this.pintarRitmo();
    this.dibujar();
    this.pintarCuerpo();
  }

  pintarRitmo() {
    const caja = this.querySelector('[data-ritmos]');
    if (!caja || !this.vida) return;
    const v = this.vida;
    const fijo = !v.ritmo_ajustable || !v.activa;
    caja.innerHTML = RITMOS.map((r) => `<button type="button" data-ritmo="${r}" aria-pressed="${v.ritmo === r}" ${fijo ? 'disabled' : ''}
      title="${esc(t(`ritmo.${r}`))}"><span aria-hidden="true">${ICONOS_RITMO[r]}</span> ${esc(t(`ritmo.${r}`))}</button>`).join('');
    caja.querySelectorAll('[data-ritmo]').forEach((b) => b.addEventListener('click', () => this.cambiarRitmo(b.dataset.ritmo)));
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

  dibujar() {
    const lienzo = this.querySelector('#vivero-lienzo');
    if (!lienzo || !this.vida) return;
    const pre = lienzo.nextElementSibling;
    const ok = this.escena && dibujarEscena(lienzo, this.escena, this.vida.mundo, { inventario: t('escena.inventario') });
    lienzo.hidden = !ok;
    pre.hidden = Boolean(ok) || !this.registro;
    if (!ok && this.registro) pre.textContent = this.registro.vista || t('vivero.sin_escena');
  }

  pintarCuerpo() {
    const r = this.registro;
    if (!r || !this.querySelector('[data-latido]')) return;
    this.querySelector('[data-latido]').textContent = t('vivero.latido', { n: r.latido });
    this.querySelector('[data-individuo]').textContent = r.individuo;
    this.querySelector('[data-generacion]').textContent = t('vivero.generacion', { n: r.generacion });
    for (const m of MEDIDORES) {
      const valor = Number((r.cuerpo || {})[m]);
      if (!Number.isFinite(valor)) continue;
      const pct = Math.max(0, Math.min(100, valor));
      const barra = this.querySelector(`[data-barra="${m}"]`);
      barra.firstElementChild.style.width = `${pct}%`;
      barra.setAttribute('aria-valuenow', pct.toFixed(0));
      barra.dataset.nivel = pct < 30 ? 'bajo' : pct < 60 ? 'medio' : 'alto';
      this.querySelector(`[data-valor="${m}"]`).textContent = pct.toFixed(0);
    }
    const afecto = (r.afecto || {}).estado;
    const animo = this.querySelector('[data-animo]');
    animo.textContent = afecto ? t(`afecto.${afecto}`) : '–';
    animo.className = `chip ${['MIEDO', 'PANICO', 'ALERTA'].includes(afecto) ? 'falta' : ['CALMA', 'CURIOSIDAD'].includes(afecto) ? 'listo' : 'aviso'}`;
    const a = r.accion;
    this.querySelector('[data-accion]').textContent = a ? `${a.verbo} ${a.objetivo || ''}${a.motivo ? ` · «${a.motivo}»` : ''}` : t('vivero.sin_accion');
    const puntos = (r.score && r.score.puntuacion) || {};
    this.querySelector('[data-puntos]').innerHTML = Object.entries(puntos)
      .filter(([, v]) => typeof v === 'number' || typeof v === 'string')
      .map(([k, v]) => `<span class="chip sin-punto">${esc(k)}: <b>${esc(typeof v === 'number' ? Math.round(v * 100) / 100 : v)}</b></span>`).join('');
    const logros = (r.score && r.score.logros) || [];
    this.querySelector('[data-logros]').textContent = logros.length ? `${t('vivero.logros')} (${logros.length}): ${logros.join(', ')}` : '';
  }
}

customElements.define('ida-vivero', IdaVivero);
