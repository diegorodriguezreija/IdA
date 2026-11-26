// Vista «Cierre» del Laboratorio (T5b): el resumen de una vida y lo que aprendió al morir.
// Sale de las series de la fuente (vidas): el nacimiento y la muerte (hechos «nace» y «muere»), la Score y los logros
// del último registro, el resumen del saber al nacer y al final (resumen_saber, T4b) y el registro de cierre
// (cierre: true, sección 13.5): sus hechos (lo aprendido de la acción que mató) y las notas de aprendizaje del motor.

import { t } from '../i18n.js';
import { esc } from '../componentes/util.js';
import { causaMuerte, hechoFraseConCierre, logro } from '../frases.js';
import { corto } from './graficas.js';

const CIFRAS = ['proposiciones', 'demostradas', 'hipotesis', 'refutadas', 'heredadas', 'requisitos_confirmados', 'aciertos', 'sorpresas'];

/** La vida que se enseña: la elegida o la del latido del cursor. */
export function vidaElegida(series, vida, nCursor) {
  const vidas = series.vidas || [];
  return vidas.find((v) => v.vida === vida) || vidas.find((v) => v.desde <= nCursor && nCursor <= v.hasta) || vidas[vidas.length - 1] || null;
}

/** ctx = {series, mundo, vida, nCursor} */
export function htmlCierre(ctx) {
  const { series, mundo } = ctx;
  const vidas = series.vidas || [];
  if (!vidas.length) return `<p class="suave">${esc(t('cierre.vacio'))}</p>`;
  const v = vidaElegida(series, ctx.vida, ctx.nCursor);
  const selector = vidas.length > 1 ? `<label class="mini">${esc(t('cierre.vida'))}<select class="entrada" data-cierre-vida>
      ${vidas.map((x) => `<option value="${x.vida}" ${x.vida === v.vida ? 'selected' : ''}>${esc(t('cierre.vida_opcion', { vida: x.vida, individuo: x.individuo, g: x.generacion }))}</option>`).join('')}</select></label>` : '';
  const muere = v.muere;
  const latidos = (v.latido_final ?? 0) - (v.latido_inicial ?? 0) + 1;
  const destino = muere ? t('cierre.murio', { causa: causaMuerte(mundo, muere.causa), latido: muere.latidos })
    : t(v.recortada ? 'cierre.recortada' : 'cierre.no_murio', { latido: v.latido_final });
  const ri = v.resumen_inicial || {}; const rf = v.resumen_final || {};
  const filas = CIFRAS.filter((k) => k in rf || k in ri).map((k) => {
    const a = ri[k]; const b = rf[k];
    const dif = typeof a === 'number' && typeof b === 'number' ? b - a : null;
    return `<tr><td>${esc(t(`epi.cifra.${k}`))}</td><td>${a ?? '–'}</td><td>${b ?? '–'}</td><td>${dif == null ? '–' : `${dif > 0 ? '+' : ''}${dif}`}</td></tr>`;
  }).join('');
  const logros = (v.logros || []).map((n) => `<span class="chip sin-punto estrella">${esc(logro(mundo, n))}</span>`).join(' ');
  const c = v.cierre;
  const alMorir = c ? (c.hechos || []).map((h) => hechoFraseConCierre(mundo, { ...h, cierre: true })).filter(Boolean) : [];
  const notas = c ? c.aprendizaje || [] : [];
  const cierreHtml = c
    ? `<p>${esc(alMorir.length ? t('cierre.aprendio_al_morir', { n: alMorir.length }) : t('cierre.nada_al_morir'))}</p>
       ${alMorir.length ? `<ul class="lista-simple">${alMorir.map((f) => `<li>💡 ${esc(f)}</li>`).join('')}</ul>` : ''}
       ${notas.length ? `<h4>${esc(t('cierre.notas'))}</h4><ul class="lista-simple notas-motor">${notas.map((n) => `<li><code>${esc(n)}</code></li>`).join('')}</ul>
         <p class="mini suave">${esc(t('cierre.notas_ayuda'))}</p>` : ''}
       <button type="button" class="boton pequeno" data-ir-n="${c.n}">${esc(t('cierre.ir_registro'))}</button>`
    : `<p class="suave">${esc(muere ? t('cierre.sin_registro_muerte') : t('cierre.sin_registro'))}</p>`;
  return `<div class="vista-series cierre-vista">
    <section class="bloque"><div class="bloque-titulo"><h2>${esc(t('cierre.titulo'))}</h2>${selector}</div>
      <p class="suave pequeno">${esc(t('cierre.ayuda'))}</p></section>
    <div class="dos-columnas">
      <section class="bloque tarjeta-mini"><h3>${esc(v.individuo || '–')} · ${esc(t('cierre.generacion', { g: v.generacion }))}</h3>
        <p class="destino ${muere ? 'murio' : ''}">${muere ? '🕯️' : '🌱'} ${esc(destino)}</p>
        <dl class="cifras"><div><dt>${esc(t('cierre.latidos'))}</dt><dd>${esc(String(latidos))}</dd></div>
          <div><dt>${esc(t('cierre.score'))}</dt><dd>${esc(v.score == null ? '–' : corto(v.score))}</dd></div>
          <div><dt>${esc(t('cierre.logros'))}</dt><dd>${(v.logros || []).length}</dd></div>
          <div><dt>${esc(t('cierre.aprendidas'))}</dt><dd>${v.aprendidas}</dd></div>
          <div><dt>${esc(t('cierre.sorpresas'))}</dt><dd>${v.sorpresas}</dd></div>
          <div><dt>${esc(t('cierre.danos'))}</dt><dd>${v.danos}</dd></div></dl>
        ${logros ? `<div class="chips-logros">${logros}</div>` : ''}
        ${v.nace ? `<p class="mini suave">${esc(t('cierre.nacio', { latido: v.latido_inicial, heredados: v.nace.heredados ?? 0 }))}</p>` : `<p class="mini suave">${esc(t('cierre.sin_nacimiento', { latido: v.latido_inicial }))}</p>`}
        <button type="button" class="boton pequeno discreto" data-ir-n="${v.desde}">${esc(t('cierre.ir_inicio'))}</button></section>
      <section class="bloque tarjeta-mini"><h3>${esc(t('cierre.al_morir'))}</h3>${cierreHtml}</section>
    </div>
    <section class="bloque"><h3>${esc(t('cierre.saber'))}</h3>
      ${filas ? `<div class="tabla-desliza"><table class="tabla-lab"><thead><tr><th></th><th>${esc(t('cierre.al_empezar'))}</th><th>${esc(t('cierre.al_final'))}</th><th>${esc(t('cierre.cambio'))}</th></tr></thead><tbody>${filas}</tbody></table></div>`
    : `<p class="suave">${esc(t('cierre.sin_resumen'))}</p>`}
      <p class="mini suave">${esc(t('cierre.saber_ayuda'))}</p></section></div>`;
}
