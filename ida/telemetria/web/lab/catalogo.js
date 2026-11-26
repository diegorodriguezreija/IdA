// Mapa de Componentes del Laboratorio (T5a, O13): sale de doc-repositorio/componentes.toml por la API
// (GET /api/v1/componentes), la misma fuente que los diagramas 06 y 07. Aquí: buscar el Componente de cada autor o
// clave de tiempo, saber a qué paso del latido (D1) pertenece y formar su ficha.

import { api } from '../api.js';
import { t, texto } from '../i18n.js';
import { esc } from '../componentes/util.js';

let promesa = null;

/** El catálogo ({componentes, decisiones, mundos}) o null si la instalación no lo trae. */
export function cargarCatalogo() {
  if (!promesa) {
    promesa = api.componentes().then((d) => new Catalogo(d)).catch(() => null);
  }
  return promesa;
}

// Los pasos del latido (D1), en orden. «cognicion» se reparte en S1, S2 y S3; «actuar» en Tribunal y Actuador.
export const PASOS = ['onda', 'sentir', 'preatencion', 'plasticidad', 'regulacion', 'S1', 'S2', 'S3', 'tribunal', 'actuar', 'cierre'];
export const NUMERO_PASO = { onda: 1, sentir: 2, preatencion: 3, plasticidad: 4, regulacion: 5, S1: 6, S2: 6, S3: 6, tribunal: 7, actuar: 7, cierre: 8 };
// La fase del registro (Onda.fases) que mide cada paso. «percibir» es la observación del mundo, que el Core transduce.
export const FASES_PASO = { sentir: ['percibir', 'sentir'], preatencion: ['preatencion'], plasticidad: ['aprender'], S1: ['S1'], S2: ['S2'], S3: ['S3'], actuar: ['actuar'], cierre: ['cierre'] };

export class Catalogo {
  constructor(d) {
    this.componentes = d.componentes || [];
    this.decisiones = d.decisiones || {};
    this.porClave = new Map();
    for (const c of this.componentes) {
      if (c.clave_tiempo) this.porClave.set(c.clave_tiempo, c);
    }
  }

  /** El elemento de un autor del registro («S1.Objeto», «CORE.Interocepcion», «preatencion:S1.Amenaza»). */
  deAutor(autor) {
    if (!autor) return null;
    const limpio = String(autor).replace(/^preatencion:/, '');
    if (this.porClave.has(autor)) return this.porClave.get(autor);
    const pre = this.porClave.get(`preatencion:${limpio}`);
    if (pre) return pre;
    if (this.porClave.has(limpio)) return this.porClave.get(limpio);
    if (/^CORE\.Actuador(_|$)/.test(limpio)) return this.porClave.get('CORE.Actuador') || null;
    return null;
  }

  /** Lo que monta el mundo, en el orden de la especificación. */
  montados(mundo) { return this.componentes.filter((c) => c.mundos.includes(mundo)); }

  esPreatentivo(autor) { const c = this.deAutor(autor); return Boolean(c && c.preatentivo); }
}

/** El paso del latido (D1) de un autor de piezas. */
export function pasoDeAutor(autor, cat) {
  const a = String(autor || '');
  if (a === 'CORE.Tribunal') return 'tribunal';
  if (a === 'CORE' || a.startsWith('CORE.Actuador')) return 'actuar';
  if (a === 'CORE.Organismo') return 'plasticidad';        // el Core pone la Sorpresa al contrastar (paso 4)
  if (a.startsWith('preatencion:')) return 'preatencion';
  const c = cat ? cat.deAutor(a) : null;
  if (c && c.preatentivo) return 'preatencion';
  if (c && c.sistema === 'CORE') return c.modulo === 'Actuar' ? 'actuar' : c.modulo === 'Regulacion' ? 'regulacion' : 'sentir';
  const s = a.split('.')[0];
  if (s === 'S1' || s === 'S2' || s === 'S3') return s;
  if (s === 'CORE') return 'sentir';
  return 'onda';
}

/** Suma los tiempos del Actuador por verbo (CORE.Actuador_MOVER...) en una sola clave. */
export function tiemposAgrupados(tiempos) {
  const salida = {};
  for (const [k, v] of Object.entries(tiempos || {})) {
    const clave = /^CORE\.Actuador_/.test(k) ? 'CORE.Actuador' : k;
    salida[clave] = (salida[clave] || 0) + (Number(v) || 0);
  }
  return salida;
}

/** Medias agrupadas igual que tiemposAgrupados (el Actuador: suma de las medias de cada verbo). */
export function mediasAgrupadas(medias) {
  const salida = {};
  for (const [k, v] of Object.entries(medias || {})) {
    const clave = /^CORE\.Actuador_/.test(k) ? 'CORE.Actuador' : k;
    salida[clave] = (salida[clave] || 0) + (Number(v.media) || 0);
  }
  return salida;
}

export function ms(v) {
  if (v == null || !Number.isFinite(Number(v))) return '–';
  const x = Number(v);
  return x >= 10 ? `${x.toFixed(1)} ms` : x >= 0.1 ? `${x.toFixed(2)} ms` : `${(x * 1000).toFixed(0)} µs`;
}

const CLASES = { general: 'general', opcional: 'opcional', cuerpo: 'cuerpo', mundo: 'mundo' };

/** Las insignias de un elemento: clase, preatentivo, plástico. */
export function insignias(c) {
  const b = [`<span class="insignia ${CLASES[c.clase] || ''}">${esc(t(`lab.clase.${c.clase}`))}${c.dueno ? ` · ${esc(c.dueno)}` : ''}</span>`];
  if (c.preatentivo) b.push(`<span class="insignia pre" title="${esc(t('lab.preatentivo_ayuda'))}">◐ ${esc(t('lab.preatentivo'))}</span>`);
  if (c.aprende) b.push(`<span class="insignia plastico" title="${esc(t('lab.plastico_ayuda'))}">✱ ${esc(t('lab.plastico'))}</span>`);
  if (c.tipo !== 'componente') b.push(`<span class="insignia">${esc(t(`lab.tipo.${c.tipo}`))}</span>`);
  return b.join(' ');
}

/** La ficha de un Componente (O13): nombre, sistema, análogo, descripción, decisión, preatentivo o plástico y tiempo. */
export function fichaComponente(c, cat, { tiempo, media, mundo } = {}) {
  const ubic = c.sistema === 'cuerpo' ? t('lab.sistema.cuerpo') : `${t(`lab.sistema.${c.sistema}`)} · ${t(`lab.modulo.${c.modulo}`)}`;
  const analogo = texto(c.analogo);
  const dec = c.decision !== 'previo' && cat.decisiones[c.decision];
  const decision = c.decision === 'previo' ? `<p class="suave pequeno">${esc(t('lab.decision_previa'))}</p>`
    : `<details class="decision"><summary>${esc(t('lab.decision', { d: c.decision }))}${dec ? ` · ${esc(dec.titulo)}` : ''}</summary>
        ${dec ? `<div class="texto-decision" lang="es">${esc(dec.texto)}</div>` : ''}
        <p class="suave pequeno">${esc(t('lab.decision_fuente', { d: c.decision }))}</p></details>`;
  const montado = mundo ? (c.mundos.includes(mundo) ? t('lab.montado_si', { mundo: t(`mundo.${mundo}.nombre`) })
    : t('lab.montado_no', { mundo: t(`mundo.${mundo}.nombre`) })) : '';
  const tiempos = c.clave_tiempo ? `<dl class="cifras">
      <div><dt>${esc(t('lab.tiempo_latido'))}</dt><dd>${esc(ms(tiempo))}</dd></div>
      <div><dt>${esc(t('lab.tiempo_medio'))}</dt><dd>${esc(ms(media))}</dd></div></dl>`
    : `<p class="suave pequeno">${esc(t(c.tipo === 'estrategia' ? 'lab.sin_tiempo_estrategia' : c.tipo === 'biblioteca' ? 'lab.sin_tiempo_biblioteca' : 'lab.sin_tiempo'))}</p>`;
  return `<article class="ficha-componente">
    <header><h3>${esc(c.nombre)}</h3><p class="suave">${esc(ubic)}</p><div class="insignias">${insignias(c)}</div></header>
    <section><h4>${esc(t('lab.analogo'))}</h4>
      ${analogo ? `<p>${esc(analogo)}</p>` : `<p class="suave">${esc(t('lab.sin_analogo'))}</p>`}</section>
    <section><h4>${esc(t('lab.que_hace'))}</h4><p>${esc(texto(c.descripcion))}</p></section>
    <section><h4>${esc(t('lab.tiempo'))}</h4>${tiempos}</section>
    <section>${decision}</section>
    ${montado ? `<p class="suave pequeno">${esc(montado)}</p>` : ''}
    ${c.sustituye ? `<p class="suave pequeno">${esc(t('lab.sustituye', { a: c.sustituye }))}</p>` : ''}
    ${c.nota ? `<details><summary>${esc(t('lab.nota_tecnica'))}</summary><p class="pequeno" lang="es">${esc(c.nota)}</p></details>` : ''}
  </article>`;
}
