// Vista «Epistemología» del Laboratorio (T5b): qué sabe IdA y cómo lo sabe, a lo largo de la vida.
// - Totales en el tiempo (demostradas, hipótesis, refutadas, heredadas) y las cifras del resumen del saber (T4b).
// - La expectativa: aciertos y sorpresas acumulados y el error de predicción (rpe) de cada sorpresa.
// - Un carril por proposición o requisito: su estado en cada tramo (color), su confianza (línea) y sus hechos
//   (● aprende, ◆ duda, ✕ refuta). Filtros por clase, fuente, estado y tipo. Al pulsar, su historia completa.
// Datos: las series de la fuente (ida/telemetria/analisis.py o lab/series.js): columnas «saber.*», «rpe», y «saber»,
// la historia de cada saber sacada del campo «saber» (20 de más confianza en cognitivo; entero en completo), de
// «requisitos» y de los hechos «aprende», «duda» y «refuta».

import { t } from '../i18n.js';
import { esc } from '../componentes/util.js';
import { clase as claseFrase, hechoFraseConCierre, requisitoFrase, saberFrase } from '../frases.js';
import { ANCHO, leyenda, rangoDe, svgGrafica } from './graficas.js';

export const FUENTES = ['manual', 'experiencia', 'herencia', 'biblioteca'];
export const ESTADOS = ['hipotesis', 'demostrada', 'refutada', 'fuera', 'olvidada', 'sin_confirmar', 'confirmado'];
const ALTO_CARRIL = 30;

/** La frase de un saber (proposición o requisito). */
export function fraseSaber(mundo, p) {
  return p.tipo === 'requisito' ? requisitoFrase(mundo, p) : saberFrase(mundo, p);
}

/** El último paso de la historia con n ≤ ``n`` (o null si aún no existía). */
export function pasoEn(p, n) {
  let u = null;
  for (const h of p.historia) { if (h[0] <= n) u = h; else break; }
  return u;
}

/** La clase del mundo de la que habla un saber. */
export function claseDeSaber(p) { return p.tipo === 'requisito' ? p.clase : p.sujeto; }

function opciones(valores, elegido, etiqueta) {
  return `<option value="">${esc(t('epi.todas'))}</option>${valores.map((v) => `<option value="${esc(v)}" ${v === elegido ? 'selected' : ''}>${esc(etiqueta(v))}</option>`).join('')}`;
}

/** Los saberes que pasan los filtros, con su estado en el latido del cursor. */
export function filtrar(series, filtros, nCursor) {
  return series.saber.filter((p) => {
    if (filtros.tipo && p.tipo !== filtros.tipo) return false;
    if (filtros.clase && claseDeSaber(p) !== filtros.clase) return false;
    if (filtros.fuente && (p.fuente || '') !== filtros.fuente) return false;
    if (filtros.estado) {
      const paso = pasoEn(p, nCursor);
      if (!paso || paso[2] !== filtros.estado) return false;
    }
    return true;
  });
}

/** El carril de un saber: estado por tramos, confianza en línea y hechos marcados. ``x`` va de 0 a ``fin`` (índices). */
function svgCarril(p, xDeN, fin, cursor) {
  const ancho = ANCHO;
  const px = (x) => (fin > 0 ? (x / fin) * (ancho - 4) + 2 : ancho / 2);
  const partes = [];
  const h = p.historia;
  h.forEach((paso, i) => {
    const a = px(xDeN(paso[0]));
    const b = i + 1 < h.length ? px(xDeN(h[i + 1][0])) : px(fin) + 2;
    partes.push(`<rect class="tramo ${esc(paso[2])}" x="${a.toFixed(1)}" y="4" width="${Math.max(1.5, b - a).toFixed(1)}" height="${ALTO_CARRIL - 8}" rx="3"/>`);
  });
  let d = '';
  h.forEach((paso, i) => {
    if (paso[3] == null) return;
    const a = px(xDeN(paso[0]));
    const b = i + 1 < h.length ? px(xDeN(h[i + 1][0])) : px(fin) + 2;
    const y = (ALTO_CARRIL - 5 - paso[3] * (ALTO_CARRIL - 10)).toFixed(1);
    d += `M${a.toFixed(1)},${y}L${b.toFixed(1)},${y}`;
  });
  if (d) partes.push(`<path class="confianza" d="${d}"/>`);
  for (const e of p.eventos) {
    const x = px(xDeN(e.n)).toFixed(1);
    const forma = e.tipo === 'aprende' ? `<circle cx="${x}" cy="${ALTO_CARRIL / 2}" r="4.2"/>`
      : e.tipo === 'duda' ? `<polygon points="${x},${ALTO_CARRIL / 2 - 5} ${Number(x) + 4.5},${ALTO_CARRIL / 2} ${x},${ALTO_CARRIL / 2 + 5} ${Number(x) - 4.5},${ALTO_CARRIL / 2}"/>`
        : `<path d="M${Number(x) - 4},${ALTO_CARRIL / 2 - 4}L${Number(x) + 4},${ALTO_CARRIL / 2 + 4}M${Number(x) + 4},${ALTO_CARRIL / 2 - 4}L${Number(x) - 4},${ALTO_CARRIL / 2 + 4}"/>`;
    partes.push(`<g class="evento ${e.tipo} ${esc(e.estado || '')}"><title>${esc(`${t('lab.latido')} ${e.latido}: ${t(`epi.evento.${e.tipo}`)} (${t(`epi.estado.${e.estado}`)})`)}</title>${forma}</g>`);
  }
  if (cursor != null) partes.push(`<line class="cursor" x1="${px(cursor).toFixed(1)}" x2="${px(cursor).toFixed(1)}" y1="0" y2="${ALTO_CARRIL}"/>`);
  return `<svg class="carril" viewBox="0 0 ${ancho} ${ALTO_CARRIL}" preserveAspectRatio="none" aria-hidden="true">${partes.join('')}</svg>`;
}

/**
 * La vista. ctx = {series, mundo, iCursor, filtros, sel, xDeN, ejeX, marcasDe}
 */
export function htmlEpistemologia(ctx) {
  const { series, mundo, iCursor, filtros } = ctx;
  const col = series.columnas;
  const L = series.registros;
  if (!L) return `<p class="suave">${esc(t('epi.vacio'))}</p>`;
  const xs = col.n.map((_, i) => i);
  const nCursor = col.n[iCursor];
  const dominio = [0, Math.max(1, L - 1)];
  const cortes = ctx.cortes;
  const conSaber = (series.niveles.cognitivo || 0) + (series.niveles.completo || 0) > 0;
  const cifras = ['demostradas', 'hipotesis', 'refutadas', 'heredadas', 'requisitos_confirmados', 'aciertos', 'sorpresas']
    .map((k) => `<div><dt>${esc(t(`epi.cifra.${k}`))}</dt><dd>${col[`saber/${k}`] ? esc(String(col[`saber/${k}`][iCursor] ?? '–')) : '–'}</dd></div>`).join('');
  const totales = [
    { clave: 'saber/demostradas', clase: 's-musgo', etiqueta: t('epi.cifra.demostradas') },
    { clave: 'saber/hipotesis', clase: 's-sol', etiqueta: t('epi.cifra.hipotesis') },
    { clave: 'saber/refutadas', clase: 's-arcilla', etiqueta: t('epi.cifra.refutadas') },
    { clave: 'saber/heredadas', clase: 's-foco', etiqueta: t('epi.cifra.heredadas'), discontinua: true },
  ].filter((l) => col[l.clave]);
  const marcasSaber = ctx.marcasDe(['aprende', 'duda', 'refuta']);
  const gTotales = svgGrafica({
    alto: 170, dominio, rango: rangoDe(totales.map((l) => col[l.clave]), { min: 0 }), cortes, cursor: iCursor, ejeX: ctx.ejeX,
    lineas: totales.map((l) => ({ xs, ys: col[l.clave], clase: l.clase, etiqueta: l.etiqueta, escalones: true, discontinua: l.discontinua })),
    marcas: marcasSaber, aria: t('epi.totales'),
  });
  const expectativa = [
    { clave: 'saber/aciertos', clase: 's-musgo', etiqueta: t('epi.cifra.aciertos') },
    { clave: 'saber/sorpresas', clase: 's-arcilla', etiqueta: t('epi.cifra.sorpresas') },
  ].filter((l) => col[l.clave]);
  const gExpectativa = svgGrafica({
    alto: 150, dominio, rango: rangoDe(expectativa.map((l) => col[l.clave]), { min: 0 }), cortes, cursor: iCursor, ejeX: ctx.ejeX,
    lineas: expectativa.map((l) => ({ xs, ys: col[l.clave], clase: l.clase, etiqueta: l.etiqueta, escalones: true })),
    aria: t('epi.expectativa'),
  });
  const rpe = col.rpe || [];
  const puntosRpe = rpe.map((v, i) => (v == null ? null : { x: i, y: v, titulo: `${t('lab.latido')} ${col.latido[i]}: rpe ${v}` })).filter(Boolean);
  const maxRpe = Math.max(1, ...puntosRpe.map((p) => Math.abs(p.y)));
  const gRpe = svgGrafica({
    alto: 120, dominio, rango: [-maxRpe, maxRpe], cortes, cursor: iCursor, ejeX: ctx.ejeX,
    lineas: [{ xs: [], ys: [], clase: 's-arcilla', puntos: puntosRpe, etiqueta: 'rpe' }], aria: t('epi.rpe'),
  });
  // Filtros
  const clases = [...new Set(series.saber.map(claseDeSaber).filter(Boolean))].sort();
  const fuentes = FUENTES.filter((f) => series.saber.some((p) => p.fuente === f));
  const estados = ESTADOS.filter((e) => series.saber.some((p) => p.historia.some((h) => h[2] === e)));
  const lista = filtrar(series, filtros, nCursor).sort((a, b) => (a.historia[0] || [a.eventos[0]?.n])[0] - (b.historia[0] || [b.eventos[0]?.n])[0]);
  const xDeN = (n) => { const i = ctx.iDeN(n); return i < 0 ? 0 : i; };
  const filas = lista.map((p) => {
    const paso = pasoEn(p, nCursor);
    const estado = paso ? paso[2] : null;
    const conf = paso && paso[3] != null ? paso[3].toFixed(2) : '–';
    const elegido = ctx.sel && ctx.sel.tipo === 'saber' && ctx.sel.clave === p.clave;
    return `<li class="saber-fila ${elegido ? 'elegido' : ''}"><button type="button" class="saber-boton" data-saber="${esc(p.clave)}" aria-pressed="${elegido}">
        <span class="saber-texto"><b>${esc(fraseSaber(mundo, p))}</b>
          <span class="chips-saber">${p.fuente ? `<span class="chip sin-punto fuente-${esc(p.fuente)}">${esc(t(`epi.fuente.${p.fuente}`))}</span>` : ''}
          <span class="chip sin-punto estado-${esc(estado || 'nada')}">${esc(estado ? t(`epi.estado.${estado}`) : t('epi.aun_no'))}</span>
          <span class="mini suave">${esc(t('epi.confianza', { c: conf }))}</span></span></span>
        ${svgCarril(p, xDeN, L - 1, iCursor)}</button></li>`;
  }).join('');
  const avisoNivel = conSaber ? (series.niveles.cognitivo ? `<p class="mini suave">${esc(t('epi.aviso_cognitivo'))}</p>` : '')
    : `<p class="aviso-caja info">${esc(t('epi.aviso_vital'))}</p>`;
  return `<div class="vista-series epistemologia">
    <section class="bloque"><div class="bloque-titulo"><h2>${esc(t('epi.titulo'))}</h2><span class="mini suave">${esc(t('epi.en_latido', { latido: col.latido[iCursor] }))}</span></div>
      <p class="suave pequeno">${esc(t('epi.ayuda'))}</p>
      <dl class="cifras cifras-7">${cifras}</dl></section>
    <section class="bloque"><h3>${esc(t('epi.totales'))}</h3>${gTotales}${leyenda(totales)}</section>
    <section class="bloque dos-columnas">
      <div><h3>${esc(t('epi.expectativa'))}</h3>${gExpectativa}${leyenda(expectativa)}</div>
      <div><h3>${esc(t('epi.rpe'))}</h3>${gRpe}<p class="mini suave">${esc(t('epi.rpe_ayuda', { n: puntosRpe.length }))}</p></div>
    </section>
    <section class="bloque">
      <div class="bloque-titulo"><h3>${esc(t('epi.saberes', { n: lista.length, total: series.saber.length }))}</h3></div>
      ${avisoNivel}
      <div class="filtros" role="group" aria-label="${esc(t('epi.filtros'))}">
        <label class="mini">${esc(t('epi.filtro.tipo'))}<select class="entrada" data-filtro="tipo">
          <option value="">${esc(t('epi.todas'))}</option>${['proposicion', 'requisito'].map((v) => `<option value="${v}" ${filtros.tipo === v ? 'selected' : ''}>${esc(t(`epi.tipo.${v}`))}</option>`).join('')}</select></label>
        <label class="mini">${esc(t('epi.filtro.clase'))}<select class="entrada" data-filtro="clase">${opciones(clases, filtros.clase, (c) => claseFrase(mundo, c, 'nombre'))}</select></label>
        <label class="mini">${esc(t('epi.filtro.fuente'))}<select class="entrada" data-filtro="fuente">${opciones(fuentes, filtros.fuente, (f) => t(`epi.fuente.${f}`))}</select></label>
        <label class="mini">${esc(t('epi.filtro.estado'))}<select class="entrada" data-filtro="estado">${opciones(estados, filtros.estado, (e) => t(`epi.estado.${e}`))}</select></label>
      </div>
      <div class="leyenda-carril mini suave">${['hipotesis', 'demostrada', 'refutada', 'fuera'].map((e) => `<span><i class="tramo-muestra ${e}"></i>${esc(t(`epi.estado.${e}`))}</span>`).join('')}
        <span>● ${esc(t('epi.evento.aprende'))}</span><span>◆ ${esc(t('epi.evento.duda'))}</span><span>✕ ${esc(t('epi.evento.refuta'))}</span><span>— ${esc(t('epi.linea_confianza'))}</span></div>
      ${lista.length ? `<ul class="saberes">${filas}</ul>` : `<p class="suave">${esc(t('epi.nada_con_filtros'))}</p>`}
    </section></div>`;
}

/** La historia completa de un saber, para el lateral. */
export function detalleSaber(series, clave, mundo, iDeN) {
  const p = series.saber.find((x) => x.clave === clave);
  if (!p) return `<p class="suave">${esc(t('epi.sin_saber'))}</p>`;
  const nace = p.historia[0] || null;
  const primeraDemostrada = p.historia.find((h) => h[2] === 'demostrada' || h[2] === 'confirmado');
  const refutada = p.historia.find((h) => h[2] === 'refutada');
  const resumen = [];
  if (nace) resumen.push(t('epi.resumen_nace', { latido: nace[1], estado: t(`epi.estado.${nace[2]}`) }));
  if (primeraDemostrada && primeraDemostrada !== nace) resumen.push(t('epi.resumen_demuestra', { latido: primeraDemostrada[1] }));
  if (refutada) resumen.push(t('epi.resumen_refuta', { latido: refutada[1] }));
  const eventos = new Map(p.eventos.map((e) => [e.n, e]));
  const filas = p.historia.map((h) => {
    const e = eventos.get(h[0]);
    eventos.delete(h[0]);
    return { n: h[0], latido: h[1], estado: h[2], confianza: h[3], fuente: h[4], evento: e };
  });
  for (const e of eventos.values()) filas.push({ n: e.n, latido: e.latido, estado: e.estado, confianza: e.confianza, fuente: p.fuente, evento: e });
  filas.sort((a, b) => a.n - b.n);
  const tabla = filas.map((f) => `<tr><td><button type="button" class="enlace" data-ir-n="${f.n}">${esc(f.latido)}</button>${f.evento && f.evento.cierre ? ' †' : ''}</td>
      <td><span class="chip sin-punto estado-${esc(f.estado)}">${esc(t(`epi.estado.${f.estado}`))}</span></td>
      <td>${f.confianza != null ? Number(f.confianza).toFixed(3) : '–'}</td>
      <td>${f.evento ? esc(hechoFraseConCierre(mundo, eventoComoHecho(p, f.evento)) || t(`epi.evento.${f.evento.tipo}`)) : ''}</td></tr>`).join('');
  const extra = p.tipo === 'requisito' && (p.requiere || p.efecto)
    ? `<p class="mini suave">${esc(t('epi.requisito_detalle', { requiere: Object.entries(p.requiere || {}).map(([c, n]) => `${n} ${claseFrase(mundo, c, 'nombre')}`).join(', ') || '–', efecto: Object.entries(p.efecto || {}).map(([c, n]) => `${n > 0 ? '+' : ''}${n} ${claseFrase(mundo, c, 'nombre')}`).join(', ') || '–' }))}</p>` : '';
  return `<p class="mini suave">${esc(t(`epi.tipo.${p.tipo}`))}${p.fuente ? ` · ${esc(t(`epi.fuente.${p.fuente}`))}` : ''}</p>
    <h3>${esc(fraseSaber(mundo, p))}</h3>
    ${resumen.length ? `<p>${esc(resumen.join(' '))}</p>` : ''}${extra}
    <h4>${esc(t('epi.historia', { n: filas.length }))}</h4>
    <div class="tabla-desliza"><table class="tabla-lab historia-saber"><thead><tr><th>${esc(t('lab.latido'))}</th><th>${esc(t('epi.col_estado'))}</th>
      <th>${esc(t('epi.col_confianza'))}</th><th>${esc(t('epi.col_hecho'))}</th></tr></thead><tbody>${tabla}</tbody></table></div>
    <p class="mini suave">${esc(t('epi.historia_ayuda'))}</p>`;
}

function eventoComoHecho(p, e) {
  if (p.tipo === 'requisito') {
    return { tipo: e.tipo, saber: 'requisito', verbo: p.verbo, clase: p.clase, requiere: p.requiere, cerca: p.cerca, efecto: p.efecto, confirmado: e.estado === 'confirmado', cierre: e.cierre };
  }
  return { tipo: e.tipo, saber: 'proposicion', clase: p.sujeto, relacion: p.relacion, estado: e.estado, cierre: e.cierre };
}
