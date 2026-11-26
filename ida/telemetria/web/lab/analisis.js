// Vista «Análisis y comparación» del Laboratorio (T5b). Tres modos:
// - «Esta vida»: curvas de la fuente abierta (Score de la colección o puntuación del mundo, logros, saber, consumo de
//   amplitud y potencia, guillotinas).
// - «Dos grabaciones»: la abierta (A) y otra de la lista (B), alineadas por latido (vida, latido, cierre), superpuestas o
//   lado a lado. La primera divergencia sale del servidor (grabacion.divergencia, con grabacion.comparar como base) y se
//   marca con una raya; con la misma configuración (cabecera) y sin divergencia, son la misma vida.
// - «Estirpes»: dos estirpes de la colección (el compañero, una archivada o una ficha) generación a generación: Score,
//   causa de muerte, logros y rasgos (GET estirpes/comparar, ida/telemetria/analisis.py, comparar_estirpes).

import { t } from '../i18n.js';
import { esc } from '../componentes/util.js';
import { causaMuerte, etiquetaPuntos } from '../frases.js';
import { corto, leyenda, rangoDe, svgGrafica } from './graficas.js';

export const MODOS = ['vida', 'grabaciones', 'estirpes'];
// Series que se pueden comparar entre dos grabaciones.
export const SERIES_COMPARABLES = ['score', 'logros', 'saber/demostradas', 'saber/proposiciones', 'cuerpo/vitalidad', 'cuerpo/alimentacion',
  'quimica/dopamina', 'quimica/estres', 'afecto/valencia', 'ritmo/amplitud', 'ritmo/potencia'];

export const nombreSerie = (col) => t(`ana.serie.${col.replace(/[./]/g, '_')}`);

function tieneDatos(c) { return Array.isArray(c) && c.some((v) => v != null); }

// --- esta vida ---------------------------------------------------------------------------------------------------------
function htmlVida(ctx) {
  const { series, mundo, iCursor, cortes } = ctx;
  const col = series.columnas;
  const L = series.registros;
  const xs = col.n.map((_, i) => i);
  const base = { dominio: [0, Math.max(1, L - 1)], cortes, cursor: iCursor, ejeX: ctx.ejeX, alto: 150 };
  const guillotinas = (col['ritmo/guillotina'] || []).map((g, i) => (g ? { x0: i, x1: i + 1, clase: 'guillotina', titulo: `${t('lab.guillotina')} · ${t('lab.latido')} ${col.latido[i]}` } : null)).filter(Boolean);
  const bloque = (titulo, lineas, extra = {}, ayuda = '') => {
    const ls = lineas.filter((l) => tieneDatos(col[l.columna]));
    if (!ls.length) return '';
    return `<section class="bloque"><h3>${esc(titulo)}</h3>${svgGrafica({ ...base, aria: titulo, rango: rangoDe(ls.map((l) => col[l.columna]), { min: 0 }), ...extra,
      lineas: ls.map((l) => ({ xs, ys: col[l.columna], clase: l.clase, etiqueta: l.etiqueta, escalones: l.escalones, discontinua: l.discontinua })) })}
      ${leyenda(ls)}${ayuda ? `<p class="mini suave">${esc(ayuda)}</p>` : ''}</section>`;
  };
  const puntuacion = tieneDatos(col.score)
    ? [{ columna: 'score', clase: 's-musgo', etiqueta: t('ana.serie.score') }]
    : Object.keys(col).filter((k) => k.startsWith('puntuacion/')).map((k, i) => ({ columna: k, clase: ['s-musgo', 's-sol', 's-foco', 's-arcilla'][i % 4], etiqueta: etiquetaPuntos(mundo, k.slice(11)) }));
  const nGuillotinas = guillotinas.length;
  return `${bloque(t('ana.puntuacion'), puntuacion, { marcas: ctx.marcasDe(['logro', 'muere', 'nace']) }, tieneDatos(col.score) ? t('ana.score_ayuda') : t('ana.sin_score'))}
    ${bloque(t('ana.logros'), [{ columna: 'logros', clase: 's-sol', etiqueta: t('ana.serie.logros'), escalones: true }], { marcas: ctx.marcasDe(['logro']) })}
    ${bloque(t('ana.saber'), [
    { columna: 'saber/proposiciones', clase: 's-foco', etiqueta: t('ana.serie.saber_proposiciones'), escalones: true },
    { columna: 'saber/demostradas', clase: 's-musgo', etiqueta: t('ana.serie.saber_demostradas'), escalones: true },
    { columna: 'saber/requisitos_confirmados', clase: 's-sol', etiqueta: t('ana.serie.saber_requisitos_confirmados'), escalones: true },
  ], { marcas: ctx.marcasDe(['aprende']) })}
    ${bloque(t('ana.amplitud'), [
    { columna: 'ritmo/amplitud', clase: 's-foco', etiqueta: t('ana.serie.ritmo_amplitud') },
    { columna: 'ritmo/amplitud_max', clase: 's-tinta', etiqueta: t('ana.maximo'), discontinua: true },
  ], { bandas: guillotinas })}
    ${bloque(t('ana.potencia'), [
    { columna: 'ritmo/potencia', clase: 's-arcilla', etiqueta: t('ana.serie.ritmo_potencia') },
    { columna: 'ritmo/potencia_max', clase: 's-tinta', etiqueta: t('ana.maximo'), discontinua: true },
  ], { bandas: guillotinas }, t('ana.guillotinas', { n: nGuillotinas, total: L }))}`;
}

// --- dos grabaciones ----------------------------------------------------------------------------------------------------
const clave = (col, i) => `${col.vida[i]}|${col.latido[i]}|${col.cierre[i] ? 1 : 0}`;

/** Las posiciones de las dos series en un eje común: (vida, latido, cierre) en orden. */
export function alinear(a, b) {
  const todas = new Map();
  for (const s of [a, b]) {
    const c = s.columnas;
    for (let i = 0; i < s.registros; i++) todas.set(clave(c, i), [Number(c.vida[i]), Number(c.latido[i]), c.cierre[i] ? 1 : 0]);
  }
  const orden = [...todas.entries()].sort((x, y) => x[1][0] - y[1][0] || x[1][1] - y[1][1] || x[1][2] - y[1][2]);
  const indice = new Map(orden.map(([k], i) => [k, i]));
  const xs = (s) => s.columnas.n.map((_, i) => indice.get(clave(s.columnas, i)));
  return { total: orden.length, etiqueta: (x) => { const e = orden[Math.round(x)]; return e ? (e[1][0] > 1 || orden[orden.length - 1][1][0] > 1 ? `v${e[1][0]}·${e[1][1]}` : String(e[1][1])) : ''; },
    xsA: xs(a), xsB: xs(b), indice };
}

function columnaComparable(s, col) {
  if (col === 'score' && !tieneDatos(s.columnas.score)) return null;
  return s.columnas[col] || null;
}

function htmlGrabaciones(ctx) {
  const c = ctx.comparacion;
  const lista = (ctx.grabaciones || []).filter((g) => g.valida && !g.en_curso);
  const actual = ctx.fuente.tipo === 'grabacion' ? ctx.fuente.id : null;
  const opciones = (elegido, excluir) => lista.filter((g) => g.id !== excluir).map((g) => `<option value="${esc(g.id)}" ${g.id === elegido ? 'selected' : ''}>${esc(g.id)} · ${esc(t('ana.semilla', { s: g.semilla ?? '–' }))}</option>`).join('');
  const mandos = `<div class="filtros">
      <label class="mini">A<select class="entrada" data-comp="a"><option value="">–</option>${opciones(c.a || actual, null)}</select></label>
      <label class="mini">B<select class="entrada" data-comp="b"><option value="">–</option>${opciones(c.b, null)}</select></label>
      <label class="mini">${esc(t('ana.serie_comparar'))}<select class="entrada" data-comp="serie">${SERIES_COMPARABLES.map((s) => `<option value="${s}" ${s === c.serie ? 'selected' : ''}>${esc(nombreSerie(s))}</option>`).join('')}</select></label>
      <div class="segmentos" role="group" aria-label="${esc(t('ana.disposicion'))}">${['superpuestas', 'lado'].map((m) => `<button type="button" data-comp-modo="${m}" aria-pressed="${c.modo === m}">${esc(t(`ana.modo.${m}`))}</button>`).join('')}</div>
    </div>`;
  if (!lista.length) return `${mandos}<p class="suave">${esc(t('ana.sin_grabaciones'))}</p>`;
  if (!c.datos) return `${mandos}<p class="suave">${esc(c.cargando ? t('app.cargando') : t('ana.elige_dos'))}</p>`;
  const { a, b, comp } = c.datos;
  const al = alinear(a, b);
  const div = comp.divergencia;
  const xDiv = div.primera ? al.indice.get(`${div.primera.vida}|${div.primera.latido}|${div.primera.cierre ? 1 : 0}`) : null;
  const conf = comp.configuracion;
  const resumen = `<div class="comparacion-resumen">
    <p><b>A</b> ${esc(comp.a.id)} · ${esc(t('ana.semilla', { s: comp.a.semilla ?? '–' }))} · ${esc(t('ana.registros', { n: a.registros }))}<br>
       <b>B</b> ${esc(comp.b.id)} · ${esc(t('ana.semilla', { s: comp.b.semilla ?? '–' }))} · ${esc(t('ana.registros', { n: b.registros }))}</p>
    <p class="${conf.misma ? '' : 'suave'}">${esc(conf.misma ? t('ana.misma_configuracion') : t('ana.otra_configuracion', { campos: conf.distintas.join(', ') }))}
      ${conf.otras.length ? `<span class="mini suave">· ${esc(t('ana.otras_diferencias', { campos: conf.otras.join(', ') }))}</span>` : ''}</p>
    <p class="divergencia-texto ${div.primera ? 'hay' : 'no-hay'}">${div.primera
    ? esc(t('ana.divergencia', { latido: div.primera.latido, vida: div.primera.vida, campos: div.primera.campos.join(', '), n: div.iguales }))
    : esc(t(div.comunes ? (conf.misma ? 'ana.misma_vida' : 'ana.sin_divergencia') : 'ana.sin_solape', { n: div.comunes }))}</p></div>`;
  const ya = columnaComparable(a, c.serie); const yb = columnaComparable(b, c.serie);
  if (!ya && !yb) return `${mandos}${resumen}<p class="suave">${esc(t('ana.serie_sin_datos'))}</p>`;
  const rango = rangoDe([ya || [], yb || []], { min: c.serie.startsWith('afecto') ? -1 : 0 });
  const dominio = [0, Math.max(1, al.total - 1)];
  const comun = { alto: 190, dominio, rango, ejeX: al.etiqueta, divergencia: xDiv, tituloDivergencia: div.primera ? t('ana.divergencia_corta', { latido: div.primera.latido }) : '' };
  const lineaA = { xs: al.xsA, ys: ya || [], clase: 's-musgo', etiqueta: `A · ${nombreSerie(c.serie)}` };
  const lineaB = { xs: al.xsB, ys: yb || [], clase: 's-arcilla', etiqueta: `B · ${nombreSerie(c.serie)}`, discontinua: c.modo === 'superpuestas' };
  const graficas = c.modo === 'lado'
    ? `<div class="dos-columnas"><div><h4>A</h4>${svgGrafica({ ...comun, lineas: [lineaA], aria: 'A' })}</div><div><h4>B</h4>${svgGrafica({ ...comun, lineas: [lineaB], aria: 'B' })}</div></div>`
    : `${svgGrafica({ ...comun, lineas: [lineaA, lineaB], aria: nombreSerie(c.serie) })}${leyenda([lineaA, lineaB])}`;
  return `${mandos}${resumen}<section class="bloque"><h3>${esc(nombreSerie(c.serie))}</h3>${graficas}
    <p class="mini suave">${esc(t('ana.alineadas'))}</p></section>`;
}

// --- estirpes -----------------------------------------------------------------------------------------------------------
function htmlEstirpes(ctx) {
  const e = ctx.estirpes;
  const ops = e.opciones || [];
  const nombre = (o) => `${o.nombre || o.individuo || o.ref} · ${t(`coleccion.tipo.${o.tipo}`)}${o.mejor_score != null ? ` · ${corto(o.mejor_score)}` : ''}`;
  const sel = (k) => `<select class="entrada" data-est="${k}"><option value="">–</option>${ops.map((o) => `<option value="${esc(o.ref)}" ${o.ref === e[k] ? 'selected' : ''}>${esc(nombre(o))}</option>`).join('')}</select>`;
  const mandos = `<div class="filtros"><label class="mini">A${sel('a')}</label><label class="mini">B${sel('b')}</label></div>`;
  if (!ops.length) return `${mandos}<p class="suave">${esc(e.cargando ? t('app.cargando') : t('ana.sin_estirpes', { mundo: t(`mundo.${ctx.fuente.mundo}.nombre`) }))}</p>`;
  if (!e.datos) return `${mandos}<p class="suave">${esc(t('ana.elige_estirpes'))}</p>`;
  const d = e.datos;
  const gens = d.filas.map((f) => f.generacion);
  const xs = d.filas.map((_, i) => i);
  const ys = (lado, f) => d.filas.map((fila) => (fila[lado] ? f(fila[lado]) : null));
  const dominio = [0, Math.max(1, d.filas.length - 1)];
  const ejeX = (x) => `G${gens[Math.round(x)] ?? ''}`;
  const sA = ys('a', (v) => v.score); const sB = ys('b', (v) => v.score);
  const lineas = [
    { xs, ys: sA, clase: 's-musgo', etiqueta: `A · ${d.a.nombre || d.a.ref}`, puntos: sA.map((y, i) => (y == null ? null : { x: i, y, titulo: `G${gens[i]}: ${corto(y)}` })).filter(Boolean) },
    { xs, ys: sB, clase: 's-arcilla', etiqueta: `B · ${d.b.nombre || d.b.ref}`, discontinua: true, puntos: sB.map((y, i) => (y == null ? null : { x: i, y, titulo: `G${gens[i]}: ${corto(y)}` })).filter(Boolean) },
  ];
  const gScore = svgGrafica({ alto: 190, dominio, rango: rangoDe([sA, sB], { min: 0 }), lineas, ejeX, aria: t('ana.estirpe_score') });
  const rasgos = d.rasgos.map((r) => {
    const ra = d.filas.map((f) => f.rasgos[r][0]); const rb = d.filas.map((f) => f.rasgos[r][1]);
    return `<div class="rasgo-mini"><h4>${esc(t(`rasgo.${r}.nombre`))}</h4>${svgGrafica({ alto: 150, dominio, rango: [0, 1], ejeX, aria: t(`rasgo.${r}.nombre`),
      lineas: [{ xs, ys: ra, clase: 's-musgo', etiqueta: 'A' }, { xs, ys: rb, clase: 's-arcilla', etiqueta: 'B', discontinua: true }] })}</div>`;
  }).join('');
  const celda = (v) => (v ? `<b>${esc(corto(v.score))}</b> <span class="mini suave">${esc(t('ana.latidos', { n: v.latidos ?? '–' }))} · ${esc(v.vivo ? t('ana.viva') : causaMuerte(d.a.mundo, v.causa_muerte || '?'))} · ${esc(t('ana.n_logros', { n: (v.logros || []).length }))}</span>` : '<span class="suave">–</span>');
  const tabla = d.filas.map((f) => `<tr><td>G${f.generacion}</td><td>${celda(f.a)}</td><td>${celda(f.b)}</td>
    <td>${f.diferencia == null ? '–' : `${f.diferencia > 0 ? '+' : ''}${esc(corto(f.diferencia))}`}</td></tr>`).join('');
  const resumen = (r, k) => `<div class="tarjeta-mini"><h4>${k} · ${esc(r.nombre || r.ref)}</h4><p class="mini">${esc(t('ana.estirpe_resumen', { n: r.generaciones, mejor: corto(r.mejor_score), media: corto(r.media_score) }))}</p>
    <p class="mini suave">${esc(Object.entries(r.causas).map(([c, n]) => `${causaMuerte(r.mundo, c)} ×${n}`).join(' · ') || '–')}</p></div>`;
  return `${mandos}${d.mismo_mundo ? '' : `<p class="aviso-caja info">${esc(t('ana.otro_mundo'))}</p>`}
    <div class="dos-columnas">${resumen(d.a, 'A')}${resumen(d.b, 'B')}</div>
    <section class="bloque"><h3>${esc(t('ana.estirpe_score'))}</h3>${gScore}${leyenda(lineas)}</section>
    <section class="bloque"><h3>${esc(t('ana.estirpe_rasgos'))}</h3><div class="rejilla-rasgos">${rasgos}</div></section>
    <section class="bloque"><h3>${esc(t('ana.estirpe_tabla'))}</h3><div class="tabla-desliza"><table class="tabla-lab"><thead><tr><th>${esc(t('ana.generacion'))}</th><th>A</th><th>B</th><th>B − A</th></tr></thead>
      <tbody>${tabla}</tbody></table></div><p class="mini suave">${esc(t('ana.estirpe_ayuda'))}</p></section>`;
}

/** ctx = {modo, series, mundo, iCursor, cortes, ejeX, marcasDe, fuente, grabaciones, comparacion, estirpes} */
export function htmlAnalisis(ctx) {
  const pestanas = `<div class="segmentos submodos" role="group" aria-label="${esc(t('ana.modo_aria'))}">${MODOS.map((m) => `<button type="button" data-ana-modo="${m}" aria-pressed="${ctx.modo === m}">${esc(t(`ana.modo.${m}`))}</button>`).join('')}</div>`;
  let cuerpo;
  if (ctx.modo === 'grabaciones') cuerpo = htmlGrabaciones(ctx);
  else if (ctx.modo === 'estirpes') cuerpo = htmlEstirpes(ctx);
  else cuerpo = ctx.series && ctx.series.registros ? htmlVida(ctx) : `<p class="suave">${esc(t('app.cargando'))}</p>`;
  return `<div class="vista-series analisis"><section class="bloque"><div class="bloque-titulo"><h2>${esc(t('ana.titulo'))}</h2>${pestanas}</div>
    <p class="suave pequeno">${esc(t(`ana.ayuda.${ctx.modo}`))}</p></section>${cuerpo}</div>`;
}

