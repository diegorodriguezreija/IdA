// Radar de los cinco rasgos del carácter (SVG): un pentágono por rasgo, de 0 a 1.

import { esc } from './util.js';

const R = 40;                     // radio del pentágono en el viewBox de 100 × 100

function punto(i, n, r) {
  const ang = -Math.PI / 2 + (2 * Math.PI * i) / n;
  return [50 + r * Math.cos(ang), 50 + r * Math.sin(ang)];
}

/**
 * El SVG del radar. arquetipo: {rasgo: valor 0..1} o null (desconocido: «?»). rasgos: el orden de los ejes.
 * etiquetas: nombres cortos de los ejes (opcional). titulo: texto accesible.
 */
export function radar(arquetipo, rasgos, { etiquetas = null, titulo = '' } = {}) {
  const n = rasgos.length;
  const malla = [0.33, 0.66, 1].map((f) => {
    const pts = rasgos.map((_, i) => punto(i, n, R * f).map((v) => v.toFixed(1)).join(',')).join(' ');
    return `<polygon class="malla" points="${pts}"/>`;
  }).join('');
  const ejes = rasgos.map((_, i) => {
    const [x, y] = punto(i, n, R);
    return `<line class="eje" x1="50" y1="50" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}"/>`;
  }).join('');
  let forma;
  if (arquetipo) {
    const pts = rasgos.map((r, i) => punto(i, n, R * Math.max(0.06, Math.min(1, Number(arquetipo[r]) || 0))).map((v) => v.toFixed(1)).join(',')).join(' ');
    forma = `<polygon class="forma" points="${pts}"/>`;
  } else {
    const pts = rasgos.map((_, i) => punto(i, n, R * 0.55).map((v) => v.toFixed(1)).join(',')).join(' ');
    forma = `<polygon class="forma desconocida" points="${pts}"/><text class="interrogacion" x="50" y="59" text-anchor="middle">?</text>`;
  }
  const textos = etiquetas ? rasgos.map((r, i) => {
    const [x, y] = punto(i, n, R + 7);
    const ancla = x < 45 ? 'end' : x > 55 ? 'start' : 'middle';
    return `<text x="${x.toFixed(1)}" y="${(y + 3).toFixed(1)}" text-anchor="${ancla}">${esc(etiquetas[i])}</text>`;
  }).join('') : '';
  const vista = etiquetas ? '-22 -6 144 112' : '0 0 100 100';
  return `<svg class="radar" viewBox="${vista}" role="img" aria-label="${esc(titulo)}">${malla}${ejes}${forma}${textos}</svg>`;
}
