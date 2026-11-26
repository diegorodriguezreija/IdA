// Laboratorio (O1): página «próximamente» de T3, con el visor de grabaciones (/escena) enlazado. El Laboratorio es T5.

import { t } from '../i18n.js';
import { esc } from '../componentes/util.js';

const LISTA = ['lab.lista.latido', 'lab.lista.componentes', 'lab.lista.saber', 'lab.lista.quimica', 'lab.lista.comparar'];

class IdaLab extends HTMLElement {
  connectedCallback() {
    this._alIdioma = () => this.pintar();
    document.addEventListener('ida:idioma', this._alIdioma);
    this.pintar();
  }

  disconnectedCallback() {
    document.removeEventListener('ida:idioma', this._alIdioma);
  }

  pintar() {
    this.innerHTML = `
      <div class="paso-titulo"><h1>${esc(t('lab.titulo'))}</h1></div>
      <div class="lab">
        <section class="tarjeta">
          <span class="chip aviso" style="align-self:flex-start">${esc(t('lab.proximamente'))}</span>
          <h2>${esc(t('lab.subtitulo'))}</h2>
          <ul>${LISTA.map((k) => `<li>${esc(t(k))}</li>`).join('')}</ul>
        </section>
        <section class="tarjeta">
          <svg class="lab-ilustracion" viewBox="0 0 180 180" aria-hidden="true">
            <circle cx="90" cy="96" r="70" fill="var(--musgo-suave)"/>
            <path d="M74 30h32M80 30v38L50 128a12 12 0 0 0 10.6 18h58.8A12 12 0 0 0 130 128L100 68V30" fill="var(--superficie)" stroke="var(--tinta-2)" stroke-width="4" stroke-linejoin="round"/>
            <path d="M58 116h64l9 14a8 8 0 0 1-7 12H56a8 8 0 0 1-7-12z" fill="var(--musgo)" opacity="0.85"/>
            <circle cx="78" cy="126" r="5" fill="var(--sobre-musgo)" opacity="0.8"/><circle cx="98" cy="132" r="3.5" fill="var(--sobre-musgo)" opacity="0.7"/>
            <path d="M92 116c0-14 8-22 20-24-1 12-8 20-20 24z" fill="var(--sol)"/>
            <path d="M92 116c0-10-6-17-16-18 1 9 6 15 16 18z" fill="var(--arcilla)" opacity="0.85"/>
          </svg>
          <h3>${esc(t('lab.visor_titulo'))}</h3>
          <p class="suave">${esc(t('lab.visor_texto'))}</p>
          <a class="boton primario" href="/escena" style="align-self:flex-start">${esc(t('lab.visor'))} ↗</a>
        </section>
      </div>`;
  }
}

customElements.define('ida-lab', IdaLab);
