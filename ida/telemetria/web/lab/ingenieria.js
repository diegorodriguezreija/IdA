// Vista «Ingeniería» del Laboratorio (T5a): el mapa de Componentes de cada sistema (CORE, S1, S2, S3 y cuerpo)
// generado desde componentes.toml (GET /api/v1/componentes, la misma fuente que los diagramas 06 y 07), con lo que
// monta el mundo de la vida y, encima, el tiempo de cada Componente en el latido (tiempos_ms) frente a su media en la
// fuente; preatentivos y plásticos marcados; y la guillotina, si saltó, en el sistema donde cortó.

import { t } from '../i18n.js';
import { esc } from '../componentes/util.js';
import { mediasAgrupadas, ms, tiemposAgrupados } from './catalogo.js';

const COLUMNAS = [
  { sistema: 'CORE', modulos: ['Sentir', 'Regulacion', 'Actuar'] },
  { sistema: 'S1', modulos: ['Sentir', 'Interpretar', 'Reaccionar', 'Actuar'] },
  { sistema: 'S2', modulos: ['Sentir', 'Interpretar', 'Reaccionar', 'Actuar'] },
  { sistema: 'S3', modulos: ['Sentir', 'Interpretar', 'Reaccionar', 'Actuar'] },
  { sistema: 'cuerpo', modulos: [''] },
];
const FASE_SISTEMA = { S1: 'S1', S2: 'S2', S3: 'S3' };

function normal(nombre) { return String(nombre || '').toLowerCase().replace(/[^a-z]/g, ''); }

// Escala logarítmica de las barras: un Componente de 8 ms (el Actuador al mover) no aplasta a los de microsegundos.
const PISO_MS = 0.002;
function escala(v, maximo) {
  if (!(v > 0)) return 0;
  return Math.min(1, Math.log10(1 + v / PISO_MS) / Math.log10(1 + maximo / PISO_MS));
}

function tarjeta(c, ctx) {
  const montado = c.mundos.includes(ctx.mundo);
  const tiempo = c.clave_tiempo ? ctx.tiempos[c.clave_tiempo] : undefined;
  const media = c.clave_tiempo ? ctx.medias[c.clave_tiempo] : undefined;
  const corrio = tiempo !== undefined;
  let barra = '';
  if (montado && c.sistema === 'CORE' && c.modulo === 'Regulacion') {
    barra = `<span class="mini suave">${esc(t('lab.sin_tiempo_regulacion'))}</span>`;
  } else if (montado && c.aprende && !corrio && media === undefined) {
    barra = `<span class="mini suave">${esc(t('lab.solo_aprende'))}</span>`;
  } else if (c.clave_tiempo && montado) {
    barra = `<span class="tiempo-barra" style="--f:${escala(tiempo, ctx.maximo).toFixed(3)};--m:${escala(media, ctx.maximo).toFixed(3)}"
      title="${esc(t('lab.tiempo_vs_media', { t: ms(tiempo), m: ms(media) }))}"></span>
    <span class="mini">${corrio ? esc(ms(tiempo)) : esc(t('lab.no_corrio'))} · <span class="suave">${esc(t('lab.media_corta', { m: ms(media) }))}</span></span>`;
  }
  let estado = '';
  if (c.tipo === 'estrategia' && montado) {
    const activa = ctx.activas.has(`${c.sistema}|${normal(c.nombre)}`);
    const ejecutada = ctx.ejecutadas.has(`${c.sistema}|${normal(c.nombre)}`);
    estado = activa ? ` activa${ejecutada ? ' ejecutada' : ''}` : '';
  }
  const sel = ctx.sel && ctx.sel.tipo === 'componente' && ctx.sel.nombre === c.nombre && ctx.sel.destino === c.destino ? ' elegido' : '';
  return `<button type="button" class="tarjeta-comp ${c.tipo} ${c.clase}${montado ? '' : ' no-montado'}${estado}${sel}"
      data-comp-nombre="${esc(c.nombre)}" data-comp-destino="${esc(c.destino)}" data-comp-dueno="${esc(c.dueno || '')}">
    <span class="nombre">${c.aprende ? '<span class="marca-plastico" aria-hidden="true">✱</span>' : ''}${c.preatentivo ? '<span class="marca-pre" aria-hidden="true">◐</span>' : ''}${esc(c.nombre)}${c.dueno && c.clase === 'mundo' ? ` <span class="suave mini">(${esc(c.dueno)})</span>` : ''}</span>
    ${barra}
    ${estado.includes('activa') ? `<span class="mini estado-estrategia">${esc(t(estado.includes('ejecutada') ? 'lab.estrategia_ejecutada' : 'lab.estrategia_activa'))}</span>` : ''}
  </button>`;
}

/** La vista entera. ``ver`` = {noMontados: bool}. */
export function htmlIngenieria(r, cat, medias, sel, ver = {}) {
  if (!cat) return `<div class="aviso-caja">${esc(t('error.componentes_no_disponibles'))}</div>`;
  const mundo = r.mundo;
  const tiempos = tiemposAgrupados(r.tiempos_ms);
  const mediasT = mediasAgrupadas(medias && medias.tiempos_medios);
  const maximo = Math.max(0.001, ...Object.values(tiempos), ...Object.values(mediasT));
  const activas = new Set(((r.estrategias && r.estrategias.activas) || []).map((e) => `${e.sistema}|${normal(e.nombre)}`));
  const ejecutadas = new Set(Object.entries((r.estrategias && r.estrategias.por_sistema) || {})
    .filter(([, v]) => v && v.ejecutada).map(([s, v]) => `${s}|${normal(v.ejecutada)}`));
  const ctx = { mundo, tiempos, medias: mediasT, maximo, activas, ejecutadas, sel };
  const motivo = (r.ritmo && r.ritmo.guillotina) || '';
  const cortado = motivo ? (motivo.match(/S[123]/) || [null])[0] : null;
  const fases = {};
  for (const f of r.fases || []) fases[f[0]] = (fases[f[0]] || 0) + (Number(f[2]) - Number(f[1]));
  const fm = (medias && medias.fases_medias) || {};
  const ocultos = cat.componentes.filter((c) => !c.mundos.includes(mundo)).length;
  const columnas = COLUMNAS.map(({ sistema, modulos }) => {
    const deSistema = cat.componentes.filter((c) => c.sistema === sistema && (ver.noMontados || c.mundos.includes(mundo)));
    const consumo = (r.onda && r.onda.consumo && r.onda.consumo[sistema]) || null;
    const fase = FASE_SISTEMA[sistema];
    const cabeza = fase ? `<span class="mini">${esc(ms(fases[fase]))} · <span class="suave">${esc(t('lab.media_corta', { m: ms(fm[fase] && fm[fase].media) }))}</span>${consumo ? ` · A ${Math.round(consumo.amplitud)}` : ''}</span>` : '';
    const cuerpoCol = modulos.map((m) => {
      const enModulo = deSistema.filter((c) => c.modulo === m);
      if (!enModulo.length) return '';
      const pre = enModulo.filter((c) => c.preatentivo);
      const resto = enModulo.filter((c) => !c.preatentivo);
      const componentes = resto.filter((c) => c.tipo !== 'estrategia');
      const estrategias = resto.filter((c) => c.tipo === 'estrategia');
      return `<section class="modulo-ing"><h4>${esc(m ? t(`lab.modulo.${m}`) : t('lab.bibliotecas'))}</h4>
        ${pre.length ? `<div class="grupo-pre"><p class="mini suave">◐ ${esc(t('lab.preatencion_grupo'))}</p>${pre.map((c) => tarjeta(c, ctx)).join('')}</div>` : ''}
        ${componentes.map((c) => tarjeta(c, ctx)).join('')}
        ${estrategias.length ? `<div class="grupo-estrategias"><p class="mini suave">${esc(t('lab.estrategias'))}</p>${estrategias.map((c) => tarjeta(c, ctx)).join('')}</div>` : ''}
      </section>`;
    }).join('');
    const guillotina = cortado === sistema ? `<p class="guillotina-banda">✂ ${esc(t('lab.guillotina_motivo', { motivo }))}</p>`
      : cortado && ['S1', 'S2', 'S3'].indexOf(cortado) < ['S1', 'S2', 'S3'].indexOf(sistema) ? `<p class="guillotina-banda tenue">${esc(t('lab.sin_turno'))}</p>` : '';
    return `<div class="columna-ing ${sistema.toLowerCase()}"><header><h3>${esc(t(`lab.sistema.${sistema}`))}</h3>${cabeza}</header>${guillotina}${cuerpoCol}</div>`;
  }).join('');
  const total = (r.ritmo && r.ritmo.ms) || 0;
  return `<div class="ingenieria">
    <div class="ing-cabeza">
      <p>${esc(t('lab.ing_resumen', { latido: r.latido, ms: ms(total), plazo: Math.round((r.ritmo && r.ritmo.plazo_ms) || 0), g: (medias && medias.guillotinas) || 0, n: (medias && medias.registros) || 0 }))}</p>
      <div class="leyenda-ing mini">
        <span><span class="tiempo-barra muestra" style="--f:.6;--m:.4"></span> ${esc(t('lab.leyenda_tiempo'))}</span>
        <span>✱ ${esc(t('lab.plastico'))}</span><span>◐ ${esc(t('lab.preatentivo'))}</span>
        <span class="muestra-clase general">${esc(t('lab.clase.general'))}</span><span class="muestra-clase opcional">${esc(t('lab.clase.opcional'))}</span>
        <span class="muestra-clase cuerpo">${esc(t('lab.clase.cuerpo'))}</span><span class="muestra-clase mundo">${esc(t('lab.clase.mundo'))}</span>
      </div>
      <label class="interruptor mini"><input type="checkbox" data-no-montados ${ver.noMontados ? 'checked' : ''}><span>${esc(t('lab.ver_no_montados', { n: ocultos, mundo: t(`mundo.${mundo}.nombre`) }))}</span></label>
    </div>
    ${r.tiempos_ms ? '' : `<p class="aviso-caja info">${esc(t('lab.sin_completo'))}</p>`}
    <div class="mapa-ing">${columnas}</div>
  </div>`;
}

