// Línea de tiempo del reproductor (T5a): una franja SVG con los hechos marcados (logros, lo aprendido, la muerte, el
// nacimiento, la guillotina y los cambios de vida) y, debajo, un deslizador accesible con el teclado.

import { t } from '../i18n.js';
import { esc } from '../componentes/util.js';
import { hechoFrase } from '../frases.js';

const ANCHO = 1000;
const ALTO = 46;
// Fila y forma de cada tipo de hecho en la franja.
const MARCAS = {
  logro: { y: 12, forma: 'estrella', clase: 'logro' },
  muere: { y: 12, forma: 'cruz', clase: 'muere' },
  nace: { y: 12, forma: 'triangulo', clase: 'nace' },
  aprende: { y: 28, forma: 'punto', clase: 'aprende' },
  peligro: { y: 28, forma: 'punto', clase: 'peligro' },
  sorpresa: { y: 28, forma: 'punto', clase: 'sorpresa' },
  duda: { y: 28, forma: 'punto', clase: 'sorpresa' },
  refuta: { y: 28, forma: 'punto', clase: 'sorpresa' },
};

function forma(f, x, y) {
  if (f === 'estrella') {
    const p = [];
    for (let i = 0; i < 10; i++) {
      const r = i % 2 ? 2.6 : 6;
      const a = (Math.PI / 5) * i - Math.PI / 2;
      p.push(`${(x + r * Math.cos(a)).toFixed(1)},${(y + r * Math.sin(a)).toFixed(1)}`);
    }
    return `<polygon points="${p.join(' ')}"/>`;
  }
  if (f === 'cruz') return `<path d="M${x - 4},${y - 4} L${x + 4},${y + 4} M${x + 4},${y - 4} L${x - 4},${y + 4}"/>`;
  if (f === 'triangulo') return `<polygon points="${x},${y - 5} ${x + 5},${y + 4} ${x - 5},${y + 4}"/>`;
  return `<circle cx="${x}" cy="${y}" r="2.6"/>`;
}

/** El SVG de la franja para un índice (``indice`` de una fuente) y la posición actual. */
export function svgLinea(indice, pos, mundo) {
  const n = indice.length;
  const x = (i) => (n <= 1 ? ANCHO / 2 : 6 + (i / (n - 1)) * (ANCHO - 12));
  const marcas = [];
  const vidas = [];
  let vidaAnt = null;
  indice.forEach((e, i) => {
    if (vidaAnt !== null && e.vida !== vidaAnt) vidas.push(`<line class="corte-vida" x1="${x(i)}" x2="${x(i)}" y1="2" y2="${ALTO - 2}"/>`);
    vidaAnt = e.vida;
    if (e.guillotina) marcas.push(`<line class="marca-guillotina" x1="${x(i)}" x2="${x(i)}" y1="36" y2="44"><title>${esc(t('lab.guillotina'))} · ${esc(t('lab.latido'))} ${e.latido}</title></line>`);
    for (const h of e.hechos || []) {
      const m = MARCAS[h.tipo];
      if (!m) continue;
      const frase = hechoFrase(mundo, h) || t(`lab.hecho.${h.tipo}`);
      marcas.push(`<g class="marca ${m.clase}" data-pos="${i}"><title>${esc(`${t('lab.latido')} ${e.latido}: ${frase}`)}</title>${forma(m.forma, x(i), m.y)}</g>`);
    }
  });
  const cursor = n ? `<line class="cursor" x1="${x(pos)}" x2="${x(pos)}" y1="0" y2="${ALTO}"/>` : '';
  return `<svg class="linea-svg" viewBox="0 0 ${ANCHO} ${ALTO}" preserveAspectRatio="none" aria-hidden="true">
    <rect class="fondo-linea" x="0" y="0" width="${ANCHO}" height="${ALTO}" rx="8"/>${vidas.join('')}${marcas.join('')}${cursor}</svg>`;
}

/** La posición del índice más cercana a un clic en la franja. */
export function posicionDeClic(svg, ev, n) {
  const caja = svg.getBoundingClientRect();
  const f = Math.max(0, Math.min(1, (ev.clientX - caja.left - (6 / ANCHO) * caja.width) / (caja.width * (1 - 12 / ANCHO))));
  return Math.round(f * Math.max(0, n - 1));
}
