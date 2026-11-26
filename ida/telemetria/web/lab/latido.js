// Vista «Latido» del Laboratorio (T5a): los ocho pasos de D1 para el latido seleccionado, en SVG.
// - La Onda recorre Onda → Core·Sentir → preatención → plasticidad → regulación → S1 → S2 → S3 → Tribunal → Actuar →
//   cierre (y el efecto vuelve a la plasticidad del latido siguiente). Con prefers-reduced-motion, sin animación.
// - En cada paso: las piezas que crea, las que modifica y las que le entran, con su autor (Pieza.origen y
//   Pieza.registro), y su tiempo (Onda.fases); en S1-S3, el consumo de amplitud y potencia (onda.consumo y
//   onda.restante) y la guillotina si salta; el tribunal con sus candidatos y el ganador.
// Todo sale del registro del latido v1 (nivel completo; con el cognitivo, sin tiempos ni registro de piezas).

import { t } from '../i18n.js';
import { esc } from '../componentes/util.js';
import { hechoFrase } from '../frases.js';
import { FASES_PASO, NUMERO_PASO, PASOS, mediasAgrupadas, ms, pasoDeAutor, tiemposAgrupados } from './catalogo.js';

const SISTEMAS = ['S1', 'S2', 'S3'];
const MODULOS = ['Sentir', 'Interpretar', 'Reaccionar', 'Actuar'];
const ANCHO = 1000;
const ALTO = 560;
// Cajas de cada paso: [x, y, ancho, alto]
const CAJAS = {
  onda: [8, 24, 172, 92], sentir: [206, 24, 172, 92], preatencion: [404, 24, 186, 92], plasticidad: [616, 24, 172, 92],
  regulacion: [814, 24, 178, 92],
  S1: [8, 158, 320, 236], S2: [340, 158, 320, 236], S3: [672, 158, 320, 236],
  tribunal: [8, 440, 430, 112], actuar: [462, 440, 258, 112], cierre: [744, 440, 248, 112],
};
// El camino de la Onda (polilínea ortogonal) y dónde se para en cada paso.
const CAMINO = [[94, 70], [903, 70], [903, 138], [168, 138], [168, 276], [832, 276], [832, 418], [223, 418], [223, 496], [868, 496]];
const PARADAS = {
  onda: [94, 70], sentir: [292, 70], preatencion: [497, 70], plasticidad: [702, 70], regulacion: [903, 70],
  S1: [168, 276], S2: [500, 276], S3: [832, 276], tribunal: [223, 496], actuar: [591, 496], cierre: [868, 496],
};

// --- análisis del registro ----------------------------------------------------------------------------------------
/** Lo que la vista necesita de un registro, por paso. */
export function analizar(r, cat) {
  const completo = Array.isArray(r.piezas);
  const piezas = completo ? r.piezas : ((r.onda && r.onda.piezas) || []);
  const porClave = new Map(piezas.map((p) => [`${p.canal}|${p.id}`, p]));
  const porId = new Map();
  for (const p of piezas) if (!porId.has(p.id)) porId.set(p.id, p);
  const pasos = Object.fromEntries(PASOS.map((p) => [p, { crea: [], modifica: [], entran: [], componentes: {}, ms: null }]));
  for (const p of piezas) {
    const paso = pasoDeAutor(p.origen, cat);
    pasos[paso].crea.push(p);
  }
  if (completo) {
    for (const p of piezas) {
      const visto = new Set();
      for (const e of p.registro || []) {
        if (e.latido !== r.latido || e.autor === p.origen || e.op !== 'modificar') continue;
        const paso = pasoDeAutor(e.autor, cat);
        const k = `${paso}|${p.canal}|${p.id}|${e.autor}`;
        if (visto.has(k)) continue;
        visto.add(k);
        pasos[paso].modifica.push({ pieza: p, autor: e.autor });
      }
      const pasoP = pasoDeAutor(p.origen, cat);
      for (const ent of p.entradas || []) {
        const previa = porId.get(String(ent));
        if (!previa || previa === p) continue;
        const pasoE = pasoDeAutor(previa.origen, cat);
        if (pasoE !== pasoP) pasos[pasoP].entran.push({ pieza: previa, hacia: p });
      }
    }
  }
  const tiempos = tiemposAgrupados(r.tiempos_ms);
  for (const [k, v] of Object.entries(tiempos)) {
    const paso = pasoDeAutor(k, cat);
    pasos[paso].componentes[k] = v;
  }
  const fases = {};
  for (const f of r.fases || []) fases[f[0]] = (fases[f[0]] || 0) + (Number(f[2]) - Number(f[1]));
  for (const [paso, nombres] of Object.entries(FASES_PASO)) {
    const presentes = nombres.filter((n) => n in fases);
    if (presentes.length) pasos[paso].ms = presentes.reduce((s, n) => s + fases[n], 0);
  }
  const motivo = (r.ritmo && r.ritmo.guillotina) || '';
  const cortado = motivo ? (motivo.match(/S[123]/) || [null])[0] : null;
  return { completo, piezas, porClave, porId, pasos, tiempos, fases, motivo, cortado, dormido: Boolean(r.cuerpo && r.cuerpo.dormido) };
}

// --- dibujo ---------------------------------------------------------------------------------------------------------
function texto(x, y, contenido, clase = '', extra = '') {
  return `<text x="${x}" y="${y}" class="${clase}" ${extra}>${esc(contenido)}</text>`;
}

function recortar(s, n) {
  const x = String(s ?? '');
  return x.length > n ? `${x.slice(0, n - 1)}…` : x;
}

function barra(x, y, w, frac, clase, etiqueta) {
  const f = Math.max(0, Math.min(1, Number(frac) || 0));
  return `<g class="barra ${clase}"><rect x="${x}" y="${y}" width="${w}" height="7" rx="3.5" class="pista"/>
    <rect x="${x}" y="${y}" width="${(w * f).toFixed(1)}" height="7" rx="3.5" class="lleno"/>${etiqueta ? `<title>${esc(etiqueta)}</title>` : ''}</g>`;
}

function caja(paso, sel, extraClase = '') {
  const [x, y, w, h] = CAJAS[paso];
  const activo = sel && sel.tipo === 'paso' && sel.id === paso ? ' elegido' : '';
  return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="14" class="caja ${extraClase}${activo}"/>`;
}

function titulo(paso, extra = '') {
  const [x, y] = CAJAS[paso];
  return `${texto(x + 12, y + 20, `${NUMERO_PASO[paso]} · ${t(`lab.paso.${paso}`)}${extra}`, 'titulo-paso')}`;
}

function nodoSimple(paso, lineas, sel, extraClase = '') {
  const [x, y, w] = CAJAS[paso];
  const cuerpo = lineas.map((l, i) => texto(x + 12, y + 40 + i * 16, recortar(l.texto, Math.floor((w - 20) / 7.1)), l.clase || 'linea')).join('');
  return `<g class="nodo" data-paso="${paso}" tabindex="0" role="button" aria-label="${esc(t(`lab.paso.${paso}`))}">
    ${caja(paso, sel, extraClase)}${titulo(paso)}${cuerpo}</g>`;
}

function nodoSistema(s, r, a, cat, sel) {
  const [x, y, w, h] = CAJAS[s];
  const consumo = (r.onda && r.onda.consumo && r.onda.consumo[s]) || null;
  const restante = (r.onda && r.onda.restante && r.onda.restante[s]) || null;
  const amax = (r.ritmo && r.ritmo.amplitud && r.ritmo.amplitud[1]) || 0;
  const pmax = (r.ritmo && r.ritmo.potencia && r.ritmo.potencia[1]) || 0;
  const paso = a.pasos[s];
  const porModulo = Object.fromEntries(MODULOS.map((m) => [m, 0]));
  for (const [k, v] of Object.entries(paso.componentes)) {
    const c = cat && cat.deAutor(k);
    const m = c && MODULOS.includes(c.modulo) ? c.modulo : 'Interpretar';
    porModulo[m] += v;
  }
  const maxMod = Math.max(0.001, ...Object.values(porModulo));
  const indice = SISTEMAS.indexOf(s);
  const cortadoAqui = a.cortado === s;
  const sinTurno = a.cortado && SISTEMAS.indexOf(a.cortado) < indice;
  const estado = a.dormido ? 'dormido' : sinTurno ? 'sin-turno' : '';
  let cuerpo = '';
  if (a.dormido) {
    cuerpo += texto(x + 14, y + 52, t('lab.dormido_sistemas'), 'linea suave');
  } else {
    MODULOS.forEach((m, i) => {
      const yy = y + 42 + i * 24;
      cuerpo += texto(x + 14, yy + 7, t(`lab.modulo.${m}`), 'mini');
      cuerpo += barra(x + 104, yy, w - 190, porModulo[m] / maxMod, 'modulo', `${t(`lab.modulo.${m}`)}: ${ms(porModulo[m])}`);
      cuerpo += texto(x + w - 12, yy + 7, a.completo ? ms(porModulo[m]) : '–', 'mini derecha');
    });
    const yb = y + 146;
    const amp = consumo ? consumo.amplitud : 0;
    const pot = consumo ? consumo.potencia : 0;
    cuerpo += texto(x + 14, yb + 7, t('lab.amplitud'), 'mini');
    cuerpo += barra(x + 104, yb, w - 190, amax ? amp / amax : 0, 'amplitud', t('lab.amplitud_ayuda'));
    cuerpo += texto(x + w - 12, yb + 7, `${Math.round(amp)}/${amax}`, 'mini derecha');
    cuerpo += texto(x + 14, yb + 31, t('lab.potencia'), 'mini');
    cuerpo += barra(x + 104, yb + 24, w - 190, pmax ? pot / pmax : 0, 'potencia', t('lab.potencia_ayuda'));
    cuerpo += texto(x + w - 12, yb + 31, `${Number(pot).toFixed(1)}/${Number(pmax).toFixed(0)}`, 'mini derecha');
    const rechazos = consumo ? (consumo.rechazos_amplitud || 0) + (consumo.recortes_potencia || 0) : 0;
    const propone = ((r.tribunal && r.tribunal.candidatos) || []).filter((c) => c.sistema === s).length;
    const linea = t('lab.sistema_resumen', { crea: paso.crea.length, propone })
      + (restante ? ` · ${t('lab.restante', { a: restante[0] })}` : '') + (rechazos ? ` · ${t('lab.rechazos', { n: rechazos })}` : '');
    cuerpo += texto(x + 14, yb + 58, recortar(linea, 44), 'linea suave');
    const act = ((r.estrategias && r.estrategias.activas) || []).filter((e) => e.sistema === s).map((e) => e.nombre);
    if (act.length) cuerpo += texto(x + 14, yb + 76, recortar(`⟳ ${act.join(', ')}`, 44), 'linea estrategia');
  }
  const cuchilla = cortadoAqui ? `<g class="guillotina-marca"><line x1="${x + 6}" y1="${y + h - 4}" x2="${x + w - 6}" y2="${y + 4}"/>
      ${texto(x + w / 2, y + h / 2 + 4, `✂ ${t('lab.guillotina')}`, 'guillotina-texto', 'text-anchor="middle"')}</g>` : '';
  const sin = sinTurno ? texto(x + w / 2, y + h / 2 + 4, t('lab.sin_turno'), 'guillotina-texto', 'text-anchor="middle"') : '';
  return `<g class="nodo sistema ${s.toLowerCase()} ${estado}" data-paso="${s}" tabindex="0" role="button" aria-label="${esc(t(`lab.paso.${s}`))}">
    ${caja(s, sel, `sistema ${s.toLowerCase()}`)}${titulo(s)}
    ${texto(x + w - 12, y + 20, a.completo && paso.ms != null ? ms(paso.ms) : '', 'mini derecha')}
    ${cuerpo}${cuchilla}${sin}</g>`;
}

function nodoTribunal(r, sel) {
  const [x, y, w] = CAJAS.tribunal;
  const tr = r.tribunal || { candidatos: [] };
  const cands = (tr.candidatos || []).slice(0, 4);
  const ganador = tr.ganador && tr.ganador.id;
  const maximo = Math.max(0.001, ...cands.map((c) => Math.abs(Number(c.total) || 0)));
  let cuerpo = '';
  if (!cands.length) cuerpo = texto(x + 12, y + 44, t('lab.sin_candidatos'), 'linea suave');
  cands.forEach((c, i) => {
    const yy = y + 34 + i * 18;
    const gana = c.id === ganador;
    cuerpo += texto(x + 12, yy + 8, `${gana ? '★' : '·'} ${c.sistema}`, `mini ${gana ? 'ganador' : ''}`);
    cuerpo += texto(x + 52, yy + 8, recortar(`${c.verbo} ${c.objetivo}`, 28), `mini ${gana ? 'ganador' : ''}`);
    cuerpo += barra(x + 250, yy + 1, w - 320, (Number(c.total) || 0) / maximo, gana ? 'ganador' : 'candidato', c.motivo || '');
    cuerpo += texto(x + w - 12, yy + 8, Number(c.total).toFixed(3), 'mini derecha');
  });
  const n = (tr.candidatos || []).length;
  const resto = n > 4 ? texto(x + 12, y + 108, t('lab.mas_candidatos', { n: n - 4 }), 'mini suave') : '';
  return `<g class="nodo" data-paso="tribunal" tabindex="0" role="button" aria-label="${esc(t('lab.paso.tribunal'))}">
    ${caja('tribunal', sel)}${titulo('tribunal', n > 1 ? ` · ${t('lab.disputado', { n })}` : '')}${cuerpo}${resto}</g>`;
}

/** El SVG de la vista para el registro ``r``. */
export function svgLatido(r, a, cat, sel) {
  const ritmo = r.ritmo || {};
  const pasos = a.pasos;
  const nAnotadas = new Set(pasos.preatencion.modifica.map((m) => `${m.pieza.canal}|${m.pieza.id}`)).size;
  const hechosAprende = (r.hechos || []).filter((h) => ['aprende', 'sorpresa', 'duda', 'refuta', 'peligro'].includes(h.tipo)).length;
  const plasticos = cat ? cat.montados(r.mundo).filter((c) => c.aprende).length : 0;
  const tiempo = (paso) => (a.completo && pasos[paso].ms != null ? ms(pasos[paso].ms) : '');
  const accion = r.accion;
  const primitivas = (() => {
    const p = a.piezas.find((x) => x.canal === 'Accion' && x.id === 'Accion');
    return p && p.carga && Array.isArray(p.carga.primitivas) ? p.carga.primitivas.join(' + ') : '';
  })();
  const camino = CAMINO.map(([x, y], i) => `${i ? 'L' : 'M'}${x},${y}`).join(' ');
  const hechosCierre = (r.hechos || []).filter((h) => ['logro', 'muere', 'primera_vez', 'duerme', 'despierta', 'nace'].includes(h.tipo));
  return `<svg class="latido-svg" viewBox="0 0 ${ANCHO} ${ALTO}" role="group" aria-label="${esc(t('lab.latido_aria', { n: r.latido }))}">
    <defs><marker id="punta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" class="punta"/></marker></defs>
    <path d="${camino}" class="camino" marker-end="url(#punta)"/>
    <path d="M992,496 L997,496 L997,10 L702,10 L702,22" class="camino retorno" marker-end="url(#punta)"/>
    ${texto(990, 8, t('lab.retorno'), 'mini suave', 'text-anchor="end"')}
    ${nodoSimple('onda', [
      { texto: t('lab.onda_latido', { n: r.latido, vida: r.vida }) },
      { texto: t('lab.onda_copia'), clase: 'linea suave' },
      { texto: r.cierre ? t('lab.registro_cierre') : '', clase: 'linea aviso' },
    ], sel)}
    ${nodoSimple('sentir', [
      { texto: t('lab.piezas_bruto', { n: pasos.sentir.crea.length }) },
      { texto: tiempo('sentir'), clase: 'linea suave' },
    ], sel)}
    ${nodoSimple('preatencion', [
      { texto: t('lab.anota', { n: nAnotadas }) },
      { texto: t('lab.sin_atencion'), clase: 'linea suave' },
      { texto: tiempo('preatencion'), clase: 'linea suave' },
    ], sel, 'exento')}
    ${nodoSimple('plasticidad', [
      { texto: t('lab.aprenden', { n: plasticos }) },
      { texto: t('lab.hechos_aprende', { n: hechosAprende }), clase: hechosAprende ? 'linea destacado' : 'linea suave' },
      { texto: tiempo('plasticidad'), clase: 'linea suave' },
    ], sel, 'exento')}
    ${nodoSimple('regulacion', [
      { texto: t('lab.regulacion_plazo', { plazo: Math.round(ritmo.plazo_ms || 0) }) },
      { texto: t('lab.regulacion_valores', { a: (ritmo.amplitud || [])[1] ?? '–', p: Number((ritmo.potencia || [])[1] ?? 0).toFixed(0) }) },
      { texto: t('lab.regulacion_fase_a'), clase: 'linea suave' },
    ], sel)}
    ${SISTEMAS.map((s) => nodoSistema(s, r, a, cat, sel)).join('')}
    ${nodoTribunal(r, sel)}
    ${nodoSimple('actuar', [
      { texto: accion ? `${accion.verbo} ${accion.objetivo || ''}` : t('lab.sin_accion') },
      { texto: primitivas ? t('lab.primitivas', { p: primitivas }) : '', clase: 'linea suave' },
      { texto: accion ? (accion.exito === true ? `✓ ${t('lab.exito')}` : accion.exito === false ? `✗ ${t('lab.fracaso')}` : '') : '', clase: 'linea' },
      { texto: tiempo('actuar'), clase: 'linea suave' },
    ], sel)}
    ${nodoSimple('cierre', [
      { texto: hechosCierre.length ? hechosCierre.map((h) => t(`lab.hecho.${h.tipo}`)).join(' · ') : t('lab.cierre_resumen') },
      { texto: (r.experiencia && r.experiencia.episodio) ? t('lab.episodio') : '', clase: 'linea suave' },
      { texto: tiempo('cierre'), clase: 'linea suave' },
    ], sel)}
    ${a.motivo ? texto(500, ALTO - 2, `✂ ${t('lab.guillotina_motivo', { motivo: a.motivo })}`, 'guillotina-texto', 'text-anchor="middle"') : ''}
    <circle class="onda-punto" r="9" cx="${PARADAS.onda[0]}" cy="${PARADAS.onda[1]}" hidden/>
  </svg>`;
}

// --- animación --------------------------------------------------------------------------------------------------
function longitudes() {
  const acumulada = [0];
  for (let i = 1; i < CAMINO.length; i++) {
    const [x0, y0] = CAMINO[i - 1];
    const [x1, y1] = CAMINO[i];
    acumulada.push(acumulada[i - 1] + Math.abs(x1 - x0) + Math.abs(y1 - y0));
  }
  const parada = {};
  for (const [paso, [px, py]] of Object.entries(PARADAS)) {
    for (let i = 1; i < CAMINO.length; i++) {
      const [x0, y0] = CAMINO[i - 1];
      const [x1, y1] = CAMINO[i];
      const dentro = (px >= Math.min(x0, x1) && px <= Math.max(x0, x1) && py >= Math.min(y0, y1) && py <= Math.max(y0, y1));
      if (dentro) { parada[paso] = acumulada[i - 1] + Math.abs(px - x0) + Math.abs(py - y0); break; }
    }
  }
  return { acumulada, parada, total: acumulada[acumulada.length - 1] };
}
const GEOMETRIA = longitudes();

function punto(l) {
  const { acumulada } = GEOMETRIA;
  for (let i = 1; i < CAMINO.length; i++) {
    if (l <= acumulada[i]) {
      const f = (l - acumulada[i - 1]) / Math.max(1, acumulada[i] - acumulada[i - 1]);
      const [x0, y0] = CAMINO[i - 1];
      const [x1, y1] = CAMINO[i];
      return [x0 + (x1 - x0) * f, y0 + (y1 - y0) * f];
    }
  }
  return CAMINO[CAMINO.length - 1];
}

export function sinMovimiento() {
  return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/** Anima la Onda por el latido en ``duracion`` ms: se para en cada paso en proporción a su tiempo medido. Devuelve una
 *  función para cancelarla. Sin animación si el usuario la ha pedido reducida. */
export function animar(svg, a, duracion = 2600) {
  if (!svg || sinMovimiento()) return () => {};
  const circulo = svg.querySelector('.onda-punto');
  if (!circulo) return () => {};
  const orden = PASOS.filter((p) => !(a.dormido && SISTEMAS.includes(p)));
  const pesos = orden.map((p) => (a.pasos[p].ms || 0));
  const totalMs = pesos.reduce((s, x) => s + x, 0) || 1;
  const viaje = duracion * 0.45;
  const pausas = orden.map((_, i) => duracion * 0.55 * (0.4 / orden.length + 0.6 * pesos[i] / totalMs));
  // tramos: [longitud desde, longitud hasta, ms, paso en el que se para al final]
  const tramos = [];
  let previo = 0;
  orden.forEach((p, i) => {
    const l = GEOMETRIA.parada[p];
    tramos.push({ desde: previo, hasta: l, ms: viaje * Math.max(0, l - previo) / GEOMETRIA.total, paso: null });
    tramos.push({ desde: l, hasta: l, ms: pausas[i], paso: p });
    previo = l;
  });
  circulo.removeAttribute('hidden');
  let inicio = null;
  let id = 0;
  const nodos = Object.fromEntries([...svg.querySelectorAll('.nodo[data-paso]')].map((n) => [n.dataset.paso, n]));
  const encender = (paso) => { for (const [p, n] of Object.entries(nodos)) n.classList.toggle('activo', p === paso); };
  const paso = (ahora) => {
    if (inicio === null) inicio = ahora;
    let tiempo = ahora - inicio;
    for (const tr of tramos) {
      if (tiempo <= tr.ms) {
        const f = tr.ms ? tiempo / tr.ms : 1;
        const [x, y] = punto(tr.desde + (tr.hasta - tr.desde) * f);
        circulo.setAttribute('cx', x.toFixed(1));
        circulo.setAttribute('cy', y.toFixed(1));
        encender(tr.paso);
        id = requestAnimationFrame(paso);
        return;
      }
      tiempo -= tr.ms;
    }
    encender(null);
    circulo.setAttribute('hidden', '');
  };
  id = requestAnimationFrame(paso);
  return () => { cancelAnimationFrame(id); encender(null); circulo.setAttribute('hidden', ''); };
}

// --- detalle ---------------------------------------------------------------------------------------------------------
function chipPieza(p, extra = '') {
  return `<button type="button" class="chip-pieza" data-pieza="${esc(`${p.canal}|${p.id}`)}" title="${esc(`${p.tipo} · ${p.origen}`)}">
    <b>${esc(p.id)}</b> <span class="suave">${esc(p.tipo)}${extra}</span></button>`;
}

function grupoPorAutor(lista, autorDe, piezaDe, extraDe = () => '') {
  const grupos = new Map();
  for (const x of lista) {
    const autor = autorDe(x);
    if (!grupos.has(autor)) grupos.set(autor, []);
    grupos.get(autor).push(x);
  }
  return [...grupos.entries()].map(([autor, xs]) => `<div class="grupo-autor">
    <button type="button" class="autor" data-comp="${esc(autor)}">${esc(autor)}</button>
    <div class="chips">${xs.slice(0, 40).map((x) => chipPieza(piezaDe(x), extraDe(x))).join('')}${xs.length > 40 ? `<span class="suave pequeno">+${xs.length - 40}</span>` : ''}</div></div>`).join('');
}

function tablaComponentes(comp, medias) {
  const filas = Object.entries(comp).sort((x, y) => y[1] - x[1]);
  if (!filas.length) return '';
  const max = Math.max(0.001, ...filas.map(([, v]) => v));
  return `<table class="tabla-lab"><thead><tr><th>${esc(t('lab.componente'))}</th><th>${esc(t('lab.tiempo_latido'))}</th><th>${esc(t('lab.tiempo_medio'))}</th></tr></thead><tbody>
    ${filas.map(([k, v]) => `<tr><td><button type="button" class="enlace" data-comp="${esc(k)}">${esc(k.replace(/^preatencion:/, ''))}</button>
      <span class="mini-barra" style="--f:${(v / max).toFixed(3)}"></span></td><td>${esc(ms(v))}</td><td>${esc(ms(medias[k]))}</td></tr>`).join('')}
    </tbody></table>`;
}

/** El detalle de un paso: qué hace, sus Componentes con su tiempo, sus piezas y lo propio de cada paso. */
export function detallePaso(paso, r, a, cat, medias) {
  const m = mediasAgrupadas(medias && medias.tiempos_medios);
  const fm = (medias && medias.fases_medias) || {};
  const mediaPaso = (FASES_PASO[paso] || []).reduce((s, f) => s + ((fm[f] && fm[f].media) || 0), 0);
  const d = a.pasos[paso];
  let propio = '';
  if (paso === 'regulacion') {
    const rt = r.ritmo || {};
    propio = `<dl class="cifras">
      <div><dt>${esc(t('lab.plazo'))}</dt><dd>${Math.round(rt.plazo_ms || 0)} ms${rt.logico ? ` · ${esc(t('lab.logico'))}` : ''}</dd></div>
      <div><dt>${esc(t('lab.amplitud'))}</dt><dd>${(rt.amplitud || [])[1] ?? '–'}</dd></div>
      <div><dt>${esc(t('lab.potencia'))}</dt><dd>${Number((rt.potencia || [])[1] ?? 0).toFixed(1)}</dd></div></dl>`;
  } else if (SISTEMAS.includes(paso)) {
    const c = (r.onda && r.onda.consumo && r.onda.consumo[paso]) || {};
    const rest = (r.onda && r.onda.restante && r.onda.restante[paso]) || [];
    const est = (r.estrategias && r.estrategias.por_sistema && r.estrategias.por_sistema[paso]) || {};
    propio = `<dl class="cifras">
      <div><dt>${esc(t('lab.amplitud'))}</dt><dd>${Math.round(c.amplitud || 0)} · ${esc(t('lab.restante', { a: rest[0] ?? '–' }))}</dd></div>
      <div><dt>${esc(t('lab.potencia'))}</dt><dd>${Number(c.potencia || 0).toFixed(2)} · ${esc(t('lab.restante', { a: rest[1] ?? '–' }))}</dd></div>
      <div><dt>${esc(t('lab.rechazos_titulo'))}</dt><dd>${c.rechazos_amplitud || 0} / ${c.recortes_potencia || 0}</dd></div>
      <div><dt>${esc(t('lab.estrategias'))}</dt><dd>${esc((est.activas || []).join(', ') || '–')}${est.ejecutada ? ` · ${esc(t('lab.ejecutada', { e: est.ejecutada }))}` : ''}</dd></div></dl>
      ${a.cortado === paso ? `<p class="aviso-caja">${esc(t('lab.guillotina_motivo', { motivo: a.motivo }))}</p>` : ''}`;
  } else if (paso === 'tribunal') {
    const tr = r.tribunal || {};
    const g = tr.ganador && tr.ganador.id;
    propio = `<table class="tabla-lab tribunal"><thead><tr><th></th><th>${esc(t('lab.candidato'))}</th><th>${esc(t('lab.base'))}</th><th>${esc(t('lab.activa'))}</th>
      <th>${esc(t('lab.proactiva'))}</th><th>${esc(t('lab.plus'))}</th><th>${esc(t('lab.total'))}</th></tr></thead><tbody>
      ${(tr.candidatos || []).map((c) => `<tr class="${c.id === g ? 'ganador' : ''}"><td>${c.id === g ? '★' : ''}</td>
        <td><b>${esc(c.sistema)}</b> ${esc(c.verbo)} ${esc(c.objetivo)}<br><span class="suave pequeno">${esc(c.motivo)}</span></td>
        <td>${Number(c.base).toFixed(3)}</td><td>${Number(c.activa).toFixed(3)}</td><td>${Number(c.proactiva).toFixed(3)}</td>
        <td>${Number(c.plus).toFixed(3)}</td><td><b>${Number(c.total).toFixed(3)}</b></td></tr>`).join('')}
      </tbody></table>
      <p class="suave pequeno">${esc(t('lab.tribunal_formula'))}</p>
      ${tr.cambio_experiencia ? `<p class="pequeno">↺ ${esc(t('lab.cambio_experiencia'))}</p>` : ''}
      ${tr.plus_decide ? `<p class="pequeno">➕ ${esc(t('lab.plus_decide'))}</p>` : ''}`;
  } else if (paso === 'actuar') {
    const ac = r.accion;
    propio = ac ? `<dl class="cifras">
      <div><dt>${esc(t('lab.accion'))}</dt><dd>${esc(ac.verbo)} ${esc(ac.objetivo)} ${ac.clase ? `(${esc(ac.clase)})` : ''}</dd></div>
      <div><dt>${esc(t('lab.de_sistema'))}</dt><dd>${esc(ac.sistema)}${ac.estrategia ? ` · ${esc(ac.estrategia)}` : ''}</dd></div>
      <div><dt>${esc(t('lab.motivo'))}</dt><dd>${esc(ac.motivo || '–')}</dd></div>
      <div><dt>${esc(t('lab.resultado'))}</dt><dd>${ac.exito === true ? '✓' : ac.exito === false ? '✗' : '–'} ${esc(ac.mensaje || '')}</dd></div></dl>` : `<p class="suave">${esc(t('lab.sin_accion'))}</p>`;
  } else if (paso === 'plasticidad') {
    const plasticos = cat ? cat.montados(r.mundo).filter((c) => c.aprende) : [];
    const notas = (r.experiencia && r.experiencia.aprendizaje) || [];
    const hechos = (r.hechos || []).filter((h) => ['aprende', 'sorpresa', 'duda', 'refuta', 'peligro'].includes(h.tipo));
    propio = `<h4>${esc(t('lab.quien_aprende'))}</h4><div class="chips">${plasticos.map((c) => `<button type="button" class="chip-pieza" data-comp-nombre="${esc(c.nombre)}" data-comp-destino="${esc(c.destino)}">✱ ${esc(c.nombre)}</button>`).join('') || '–'}</div>
      <p class="suave pequeno">${esc(t('lab.plasticidad_sin_tiempo'))}</p>
      ${hechos.length ? `<h4>${esc(t('lab.hechos_latido'))}</h4><ul class="lista-simple">${hechos.map((h) => `<li>${esc(hechoFrase(r.mundo, h))}</li>`).join('')}</ul>` : ''}
      ${notas.length ? `<h4>${esc(t('lab.notas_aprendizaje'))}</h4><ul class="lista-simple">${notas.map((n) => `<li lang="es">${esc(n)}</li>`).join('')}</ul>` : ''}`;
  } else if (paso === 'cierre') {
    const ex = r.experiencia || {};
    propio = `<dl class="cifras">
      <div><dt>${esc(t('lab.episodio_titulo'))}</dt><dd lang="es">${esc(ex.episodio || '–')}</dd></div>
      <div><dt>${esc(t('lab.expectativa'))}</dt><dd lang="es">${esc(ex.expectativa || '–')}</dd></div>
      <div><dt>${esc(t('lab.afecto'))}</dt><dd>${esc((r.afecto && r.afecto.estado) || '–')}</dd></div></dl>`;
  } else if (paso === 'onda') {
    propio = `<dl class="cifras">
      <div><dt>${esc(t('lab.latido'))}</dt><dd>${r.latido} · ${esc(t('lab.vida_n', { n: r.vida }))} · ${esc(r.individuo)}</dd></div>
      <div><dt>${esc(t('lab.nivel'))}</dt><dd>${esc(r.nivel)}</dd></div>
      <div><dt>${esc(t('lab.operaciones'))}</dt><dd>${(r.onda && r.onda.operaciones) ?? '–'}</dd></div>
      <div><dt>${esc(t('lab.cognicion'))}</dt><dd>${esc(ms((r.ritmo || {}).ms))} / ${esc(ms((r.ritmo || {}).ms_total))}</dd></div></dl>`;
  }
  const piezas = a.completo ? `
    ${d.crea.length ? `<h4>${esc(t('lab.salen', { n: d.crea.length }))}</h4>${grupoPorAutor(d.crea, (p) => p.origen, (p) => p, (p) => ` · ${Number(p.arousal).toFixed(2)}`)}` : ''}
    ${d.modifica.length ? `<h4>${esc(t('lab.modifica', { n: d.modifica.length }))}</h4>${grupoPorAutor(d.modifica, (x) => x.autor, (x) => x.pieza)}` : ''}
    ${d.entran.length ? `<h4>${esc(t('lab.entran', { n: d.entran.length }))}</h4>${grupoPorAutor(d.entran, (x) => x.pieza.origen, (x) => x.pieza, (x) => ` → ${x.hacia.id}`)}` : ''}
    ${!d.crea.length && !d.modifica.length && !d.entran.length ? `<p class="suave pequeno">${esc(t('lab.sin_piezas'))}</p>` : ''}`
    : `<p class="suave pequeno">${esc(t('lab.sin_completo'))}</p>`;
  return `<article class="detalle-paso">
    <header><p class="suave pequeno">${esc(t('lab.paso_n', { n: NUMERO_PASO[paso] }))}</p><h3>${esc(t(`lab.paso.${paso}`))}</h3></header>
    <p>${esc(t(`lab.paso.${paso}.que`))}</p>
    <p class="bio">🧠 ${esc(t(`lab.paso.${paso}.bio`))}</p>
    ${d.ms != null ? `<dl class="cifras"><div><dt>${esc(t('lab.tiempo_latido'))}</dt><dd>${esc(ms(d.ms))}</dd></div>
      <div><dt>${esc(t('lab.tiempo_medio'))}</dt><dd>${esc(ms(mediaPaso))}</dd></div></dl>` : ''}
    ${propio}
    ${Object.keys(d.componentes).length ? `<h4>${esc(t('lab.componentes_paso'))}</h4>${tablaComponentes(d.componentes, m)}` : ''}
    ${piezas}
  </article>`;
}

/** El registro completo de una pieza. */
export function detallePieza(clave, a) {
  const p = a.porClave.get(clave);
  if (!p) return `<p class="suave">${esc(t('lab.pieza_no_esta'))}</p>`;
  const reg = (p.registro || []).map((e) => `<tr><td>${esc(e.latido)}</td><td>${esc(e.op)}</td><td><button type="button" class="enlace" data-comp="${esc(e.autor)}">${esc(e.autor)}</button></td></tr>`).join('');
  return `<article class="detalle-pieza">
    <header><p class="suave pequeno">${esc(t('lab.pieza'))} · ${esc(p.canal)} · ${esc(p.fase)}</p><h3>${esc(p.id)}</h3></header>
    <dl class="cifras">
      <div><dt>${esc(t('lab.tipo_pieza'))}</dt><dd>${esc(p.tipo)}</dd></div>
      <div><dt>${esc(t('lab.autor'))}</dt><dd><button type="button" class="enlace" data-comp="${esc(p.origen)}">${esc(p.origen)}</button> (${esc(p.sistema)})</dd></div>
      <div><dt>arousal</dt><dd>${Number(p.arousal).toFixed(4)}</dd></div>
      <div><dt>${esc(t('lab.confianza'))}</dt><dd>${Number(p.confianza).toFixed(4)}</dd></div>
      ${p.creada != null ? `<div><dt>${esc(t('lab.creada'))}</dt><dd>${esc(p.creada)} · ${esc(t('lab.actualizada'))} ${esc(p.actualizada)}</dd></div>` : ''}
    </dl>
    ${(p.entradas || []).length ? `<h4>${esc(t('lab.entradas'))}</h4><div class="chips">${p.entradas.map((e) => {
      const previa = a.porId.get(String(e));
      return previa ? chipPieza(previa) : `<span class="chip-pieza vacio">${esc(e)}</span>`;
    }).join('')}</div>` : ''}
    ${reg ? `<h4>${esc(t('lab.registro_pieza'))}</h4><table class="tabla-lab"><thead><tr><th>${esc(t('lab.latido'))}</th><th>op</th><th>${esc(t('lab.autor'))}</th></tr></thead><tbody>${reg}</tbody></table>` : ''}
    ${p.carga !== undefined ? `<h4>${esc(t('lab.carga'))}</h4><pre class="json">${esc(JSON.stringify(p.carga, null, 2))}</pre>` : `<p class="suave pequeno">${esc(t('lab.sin_completo'))}</p>`}
  </article>`;
}
