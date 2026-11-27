// Gráficas de series del Laboratorio (T5b): SVG sin bibliotecas (O12), con los colores del tema (estilo.css).
// Una gráfica es un rectángulo con su eje x (posiciones de la fuente o latidos), líneas, bandas (el sueño), cortes entre
// vidas, marcas de hechos en una franja de arriba y el cursor del latido que se está viendo. Al pulsar, el Laboratorio
// va a ese latido (data-grafica con el dominio en x; lab.js traduce el clic con xDeClic).

import { esc } from '../componentes/util.js';

export const ANCHO = 1000;
const IZQ = 52;        // margen para las etiquetas del eje y
const DER = 10;
const ARRIBA = 18;     // franja de marcas
const ABAJO = 20;      // etiquetas del eje x
const MAX_PUNTOS = 1400;

// Forma y fila de cada marca (las mismas formas que la línea de tiempo del reproductor).
const FORMAS = { logro: 'estrella', muere: 'cruz', nace: 'triangulo', dano: 'abajo', aprende: 'punto', peligro: 'punto', sorpresa: 'rombo', duda: 'rombo', refuta: 'cruz', duerme: 'luna' };

function forma(f, x, y) {
  if (f === 'estrella') {
    const p = [];
    for (let i = 0; i < 10; i++) {
      const r = i % 2 ? 2.4 : 5.5;
      const a = (Math.PI / 5) * i - Math.PI / 2;
      p.push(`${(x + r * Math.cos(a)).toFixed(1)},${(y + r * Math.sin(a)).toFixed(1)}`);
    }
    return `<polygon points="${p.join(' ')}"/>`;
  }
  if (f === 'cruz') return `<path d="M${x - 4},${y - 4} L${x + 4},${y + 4} M${x + 4},${y - 4} L${x - 4},${y + 4}"/>`;
  if (f === 'triangulo') return `<polygon points="${x},${y - 5} ${x + 5},${y + 4} ${x - 5},${y + 4}"/>`;
  if (f === 'abajo') return `<polygon points="${x - 4.5},${y - 4} ${x + 4.5},${y - 4} ${x},${y + 4.5}"/>`;
  if (f === 'rombo') return `<polygon points="${x},${y - 4.5} ${x + 4},${y} ${x},${y + 4.5} ${x - 4},${y}"/>`;
  if (f === 'luna') return `<circle cx="${x}" cy="${y}" r="3.5"/>`;
  return `<circle cx="${x}" cy="${y}" r="2.8"/>`;
}

/** Números legibles en los ejes: enteros sin decimales, el resto con los justos. */
export function corto(v) {
  if (v == null || !Number.isFinite(v)) return '–';
  const a = Math.abs(v);
  if (a >= 10000) return `${(v / 1000).toFixed(a >= 100000 ? 0 : 1)}k`;
  if (Number.isInteger(v) || a >= 100) return String(Math.round(v));
  if (a >= 10) return v.toFixed(1);
  return v.toFixed(2);
}

/** Reduce una serie larga a lo que cabe en el ancho, conservando los mínimos y máximos de cada tramo. */
function reducir(xs, ys) {
  const n = xs.length;
  if (n <= MAX_PUNTOS) return [xs, ys];
  const tramo = Math.ceil(n / (MAX_PUNTOS / 2));
  const rx = []; const ry = [];
  for (let i = 0; i < n; i += tramo) {
    let iMin = -1; let iMax = -1;
    for (let j = i; j < Math.min(n, i + tramo); j++) {
      if (ys[j] == null) continue;
      if (iMin < 0 || ys[j] < ys[iMin]) iMin = j;
      if (iMax < 0 || ys[j] > ys[iMax]) iMax = j;
    }
    if (iMin < 0) { rx.push(xs[i]); ry.push(null); continue; }
    for (const j of iMin <= iMax ? [iMin, iMax] : [iMax, iMin]) { rx.push(xs[j]); ry.push(ys[j]); }
  }
  return [rx, ry];
}

/** El rango [min, max] de varias series (con un margen si es plano). */
export function rangoDe(listas, fijo = {}) {
  let min = Infinity; let max = -Infinity;
  for (const ys of listas) for (const v of ys) if (v != null && Number.isFinite(v)) { min = Math.min(min, v); max = Math.max(max, v); }
  if (!Number.isFinite(min)) { min = 0; max = 1; }
  if (fijo.min != null) min = Math.min(min, fijo.min);
  if (fijo.max != null) max = Math.max(max, fijo.max);
  if (max - min < 1e-9) { max += 1; min -= fijo.min != null ? 0 : 1; }
  return [min, max];
}

/**
 * El SVG de una gráfica.
 * o = {alto, dominio: [x0, x1], rango: [y0, y1], lineas: [{xs, ys, clase, etiqueta, escalones?, discontinua?}],
 *      bandas: [{x0, x1, clase, titulo}], cortes: [x], marcas: [{x, tipo, titulo}], cursor: x|null, aria, ejeX: fn(x)→texto,
 *      divergencia: x|null}
 */
export function svgGrafica(o) {
  const alto = o.alto || 150;
  const [x0, x1] = o.dominio;
  const [y0, y1] = o.rango;
  const anchoUtil = ANCHO - IZQ - DER;
  const altoUtil = alto - ARRIBA - ABAJO;
  const px = (x) => IZQ + (x1 > x0 ? ((x - x0) / (x1 - x0)) * anchoUtil : anchoUtil / 2);
  const py = (y) => ARRIBA + altoUtil - ((y - y0) / (y1 - y0)) * altoUtil;
  const partes = [];
  // Rejilla y eje y: tres valores.
  for (const v of [y0, (y0 + y1) / 2, y1]) {
    const y = py(v).toFixed(1);
    partes.push(`<line class="rejilla" x1="${IZQ}" x2="${ANCHO - DER}" y1="${y}" y2="${y}"/><text class="eje" x="${IZQ - 6}" y="${(Number(y) + 4).toFixed(1)}" text-anchor="end">${esc(corto(v))}</text>`);
  }
  if (y0 < 0 && y1 > 0) partes.push(`<line class="cero" x1="${IZQ}" x2="${ANCHO - DER}" y1="${py(0).toFixed(1)}" y2="${py(0).toFixed(1)}"/>`);
  // Eje x: principio, mitad y final.
  const ejeX = o.ejeX || ((x) => corto(x));
  for (const [x, ancla] of [[x0, 'start'], [(x0 + x1) / 2, 'middle'], [x1, 'end']]) {
    partes.push(`<text class="eje" x="${px(x).toFixed(1)}" y="${alto - 5}" text-anchor="${ancla}">${esc(ejeX(x))}</text>`);
  }
  for (const b of o.bandas || []) {
    const a = px(b.x0); const w = Math.max(1.5, px(b.x1) - a);
    partes.push(`<rect class="banda ${b.clase || ''}" x="${a.toFixed(1)}" y="${ARRIBA}" width="${w.toFixed(1)}" height="${altoUtil}">${b.titulo ? `<title>${esc(b.titulo)}</title>` : ''}</rect>`);
  }
  for (const x of o.cortes || []) partes.push(`<line class="corte-vida" x1="${px(x).toFixed(1)}" x2="${px(x).toFixed(1)}" y1="${ARRIBA}" y2="${ARRIBA + altoUtil}"/>`);
  for (const l of o.lineas || []) {
    const [xs, ys] = reducir(l.xs, l.ys);
    let d = ''; let abierto = false; let yAnt = null;
    for (let i = 0; i < xs.length; i++) {
      const v = ys[i];
      if (v == null || !Number.isFinite(v)) { abierto = false; continue; }
      const X = px(xs[i]).toFixed(1); const Y = py(v).toFixed(1);
      if (!abierto) d += `M${X},${Y}`;
      else if (l.escalones) d += `L${X},${yAnt}L${X},${Y}`;
      else d += `L${X},${Y}`;
      abierto = true; yAnt = Y;
    }
    if (d) partes.push(`<path class="serie ${l.clase || ''} ${l.discontinua ? 'discontinua' : ''}" d="${d}"><title>${esc(l.etiqueta || '')}</title></path>`);
    for (const p of l.puntos || []) partes.push(`<circle class="punto-serie ${l.clase || ''}" cx="${px(p.x).toFixed(1)}" cy="${py(p.y).toFixed(1)}" r="3"><title>${esc(p.titulo || '')}</title></circle>`);
  }
  for (const m of o.marcas || []) {
    const f = FORMAS[m.tipo] || 'punto';
    partes.push(`<g class="marca ${m.tipo}">${m.titulo ? `<title>${esc(m.titulo)}</title>` : ''}${forma(f, Number(px(m.x).toFixed(1)), 9)}</g>`);
  }
  if (o.divergencia != null) {
    const X = px(o.divergencia).toFixed(1);
    partes.push(`<line class="divergencia" x1="${X}" x2="${X}" y1="2" y2="${ARRIBA + altoUtil}"><title>${esc(o.tituloDivergencia || '')}</title></line>`);
  }
  if (o.cursor != null && o.cursor >= x0 && o.cursor <= x1) {
    const X = px(o.cursor).toFixed(1);
    partes.push(`<line class="cursor" x1="${X}" x2="${X}" y1="2" y2="${ARRIBA + altoUtil}"/>`);
  }
  return `<svg class="grafica" viewBox="0 0 ${ANCHO} ${alto}" role="img" aria-label="${esc(o.aria || '')}" data-grafica
    data-x0="${x0}" data-x1="${x1}" data-izq="${IZQ}" data-der="${DER}">
    <rect class="fondo-grafica" x="${IZQ}" y="${ARRIBA}" width="${anchoUtil}" height="${altoUtil}" rx="4"/>${partes.join('')}</svg>`;
}

/** El valor de x de un clic en una gráfica (``svgGrafica``). */
export function xDeClic(svg, ev) {
  const caja = svg.getBoundingClientRect();
  const escala = caja.width / ANCHO;
  const izq = Number(svg.dataset.izq) * escala;
  const util = caja.width - izq - Number(svg.dataset.der) * escala;
  const f = Math.max(0, Math.min(1, (ev.clientX - caja.left - izq) / Math.max(1, util)));
  const x0 = Number(svg.dataset.x0); const x1 = Number(svg.dataset.x1);
  return x0 + f * (x1 - x0);
}

/** Una leyenda: [{clase, etiqueta, ayuda?}]. */
export function leyenda(items) {
  return `<ul class="leyenda-grafica">${items.map((i) => `<li><span class="muestra ${i.clase || ''} ${i.discontinua ? 'discontinua' : ''}"></span>${esc(i.etiqueta)}${i.ayuda ? ` <span class="suave">· ${esc(i.ayuda)}</span>` : ''}</li>`).join('')}</ul>`;
}

/** Tramos en que una columna booleana (p. ej. «dormido») vale verdadero: [{x0, x1}] en posiciones de la serie. */
export function tramos(col, xs) {
  const salida = [];
  let ini = null;
  for (let i = 0; i < col.length; i++) {
    if (col[i] && ini == null) ini = i;
    if ((!col[i] || i === col.length - 1) && ini != null) {
      const fin = col[i] ? i : i - 1;
      salida.push({ x0: xs[ini], x1: xs[fin] + 1 });
      ini = null;
    }
  }
  return salida;
}
