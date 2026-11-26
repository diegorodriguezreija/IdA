// Dibujo de escena() en Canvas (O6, O12): módulo ES sin dependencias, compartido por el visor de grabaciones
// (escena.js) y el Vivero. Dibuja los tres tipos del contrato v1: «rejilla», «arbol» y «tablero».
// Los colores salen de las variables CSS del documento (--panel, --texto, --suave, --borde, --acento, --vacio).

const BASE = new URL('.', import.meta.url);          // .../web/
export const CELDA = 48;                             // píxeles por casilla (sprites de 16 × 3)
const FILA_INVENTARIO = 28;

const UNICODE_PIEZAS = {
  blanco: { rey: '♔', dama: '♕', torre: '♖', alfil: '♗', caballo: '♘', peon: '♙' },
  negro: { rey: '♚', dama: '♛', torre: '♜', alfil: '♝', caballo: '♞', peon: '♟' },
};

const sprites = {};                                   // mundo -> {imagenes, mapa, listo}

/** Carga el índice y las imágenes de los sprites de un mundo (sin índice: colores y letras). */
export async function cargarSprites(mundo) {
  if (!mundo) return;
  if (sprites[mundo]) { await sprites[mundo].listo; return; }
  const s = { imagenes: {}, mapa: {}, listo: null };
  sprites[mundo] = s;
  s.listo = (async () => {
    try {
      const resp = await fetch(new URL(`sprites/${encodeURIComponent(mundo)}/indice.json`, BASE));
      if (!resp.ok) return;
      const indice = await resp.json();
      s.mapa = indice.mapa_sprites || {};
      const ficheros = [...new Set(Object.values(s.mapa))];
      await Promise.all(ficheros.map((f) => new Promise((ok) => {
        const img = new Image();
        img.onload = () => { s.imagenes[f] = img; ok(); };
        img.onerror = ok;
        img.src = new URL(`sprites/${encodeURIComponent(mundo)}/${f}`, BASE).href;
      })));
    } catch { /* sin servidor: colores y letras */ }
  })();
  await s.listo;
}

/** La URL del sprite de una clave en un mundo, si el índice ya está cargado (para <img>). */
export function urlSprite(mundo, clave) {
  const s = sprites[mundo];
  const f = s && s.mapa[clave];
  return f ? new URL(`sprites/${encodeURIComponent(mundo)}/${f}`, BASE).href : null;
}

function variable(nombre, defecto) {
  return getComputedStyle(document.documentElement).getPropertyValue(nombre).trim() || defecto;
}

function colorDe(clase) {
  let h = 0;
  for (const c of String(clase)) h = (h * 31 + c.codePointAt(0)) % 360;
  return `hsl(${h} 45% 52%)`;
}

function imagen(mundo, claves) {
  const s = sprites[mundo];
  if (!s) return null;
  for (const k of claves) {
    const f = k && s.mapa[k];
    if (f && s.imagenes[f]) return s.imagenes[f];
  }
  return null;
}

function pintar(ctx, mundo, claves, x, y, tam, letra) {
  const img = imagen(mundo, claves);
  if (img) { ctx.drawImage(img, x, y, tam, tam); return; }
  ctx.fillStyle = colorDe(claves[claves.length - 1]);
  ctx.fillRect(x + 2, y + 2, tam - 4, tam - 4);
  ctx.fillStyle = '#fff';
  ctx.font = `bold ${Math.round(tam * 0.45)}px system-ui`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(letra, x + tam / 2, y + tam / 2);
}

function dibujarRejilla(lienzo, ctx, escena, mundo) {
  const inv = Object.entries(escena.inventario || {}).filter(([, n]) => n);
  const porFila = Math.max(1, Math.floor((escena.ancho * CELDA) / (FILA_INVENTARIO * 2.6)));
  const filasInv = Math.ceil(inv.length / porFila);
  lienzo.width = escena.ancho * CELDA;
  lienzo.height = escena.alto * CELDA + filasInv * (FILA_INVENTARIO + 6) + (filasInv ? 8 : 0);
  ctx.imageSmoothingEnabled = false;
  ctx.fillStyle = variable('--vacio', '#222');
  ctx.fillRect(0, 0, lienzo.width, lienzo.height);
  escena.celdas.forEach((fila, y) => fila.forEach((clase, x) => {
    if (clase != null) pintar(ctx, mundo, [clase, '?'], x * CELDA, y * CELDA, CELDA, String(clase)[0] || '?');
  }));
  for (const e of escena.entidades || []) {
    const claves = [e.estado ? `${e.clase}.${e.estado}` : null, e.clase, '?'];
    pintar(ctx, mundo, claves, e.x * CELDA, e.y * CELDA, CELDA, String(e.clase)[0].toUpperCase());
  }
  if (escena.yo) {
    const yo = escena.yo;
    pintar(ctx, mundo, [yo.estado ? `yo.${yo.estado}` : null, yo.orientacion ? `yo.${yo.orientacion}` : null, 'yo.sur', 'yo'],
      yo.x * CELDA, yo.y * CELDA, CELDA, '@');
  }
  const luz = escena.extra && typeof escena.extra.luz === 'number' ? escena.extra.luz : 1;
  if (luz < 1) {                                       // noche: oscurece la parte del mapa
    ctx.fillStyle = `rgba(0, 0, 20, ${((1 - luz) * 0.65).toFixed(3)})`;
    ctx.fillRect(0, 0, lienzo.width, escena.alto * CELDA);
  }
  const y0 = escena.alto * CELDA + 8;
  inv.forEach(([clase, n], k) => {
    const x = (k % porFila) * FILA_INVENTARIO * 2.6;
    const y = y0 + Math.floor(k / porFila) * (FILA_INVENTARIO + 6);
    pintar(ctx, mundo, [clase, '?'], x + 4, y, FILA_INVENTARIO, String(clase)[0]);
    ctx.fillStyle = '#f2f1ec';                         // sobre el fondo oscuro de la franja del inventario
    ctx.font = 'bold 14px system-ui';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(String(n), x + FILA_INVENTARIO + 8, y + FILA_INVENTARIO / 2);
  });
}

function dibujarArbol(lienzo, ctx, escena, mundo, etiquetas) {
  const filaAlt = 32;
  const inv = Object.entries(escena.inventario || {}).filter(([, n]) => n);
  const items = [];
  for (const nodo of escena.nodos || []) {
    items.push({ tipo: 'nodo', nodo });
    for (const ent of escena.entidades || []) {
      if (ent.ruta === nodo.ruta) items.push({ tipo: 'entidad', ent, ruta: nodo.ruta });
    }
  }
  const margen = 16;
  const ancho = 480;
  const alto = margen * 2 + items.length * filaAlt + (inv.length ? 50 : 0);
  lienzo.width = ancho;
  lienzo.height = Math.max(200, alto);
  ctx.imageSmoothingEnabled = true;
  const textoColor = variable('--texto', '#1d1d1b');
  const suaveColor = variable('--suave', '#6b6a65');
  const acentoColor = variable('--acento', '#2f6f4f');
  ctx.fillStyle = variable('--panel', '#ffffff');
  ctx.fillRect(0, 0, lienzo.width, lienzo.height);

  let y = margen;
  for (const it of items) {
    if (it.tipo === 'nodo') {
      const n = it.nodo;
      const nivel = n.ruta ? n.ruta.split('/').length : 0;
      const x = margen + nivel * 24;
      const esYo = escena.yo && escena.yo.ruta === n.ruta;
      if (esYo) {
        ctx.fillStyle = 'rgba(47, 111, 79, 0.15)';
        ctx.fillRect(x - 4, y, ancho - x - margen + 4, filaAlt);
        ctx.fillStyle = acentoColor;
        ctx.fillRect(x - 4, y, 3, filaAlt);
      }
      pintar(ctx, mundo, [n.clase, 'carpeta', '?'], x, y + 4, 24, n.clase === 'raiz' ? 'R' : 'C');
      const nombre = n.ruta ? n.ruta.split('/').pop() : 'bioma';
      ctx.fillStyle = textoColor;
      ctx.font = esYo ? 'bold 14px system-ui' : '14px system-ui';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      ctx.fillText(nombre + '/', x + 30, y + filaAlt / 2);
      if (esYo) {
        ctx.fillStyle = acentoColor;
        ctx.font = 'bold 12px system-ui';
        ctx.fillText('◀ IdA', x + 30 + ctx.measureText(nombre + '/ ').width + 6, y + filaAlt / 2);
      }
    } else {
      const e = it.ent;
      const nivel = (it.ruta ? it.ruta.split('/').length : 0) + 1;
      const x = margen + nivel * 24;
      pintar(ctx, mundo, [e.clase, '?'], x, y + 6, 20, String(e.clase)[0]);
      ctx.fillStyle = suaveColor;
      ctx.font = '13px monospace, system-ui';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      ctx.fillText(e.nombre || e.clase, x + 26, y + filaAlt / 2);
    }
    y += filaAlt;
  }
  if (inv.length) {
    y += 10;
    ctx.strokeStyle = variable('--borde', '#dddcd6');
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(margen, y);
    ctx.lineTo(ancho - margen, y);
    ctx.stroke();
    y += 10;
    ctx.fillStyle = suaveColor;
    ctx.font = '12px system-ui';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${etiquetas.inventario || 'inventario'}:`, margen, y + 10);
    inv.forEach(([clase], k) => {
      const ix = margen + 80 + k * 80;
      pintar(ctx, mundo, [clase, '?'], ix, y, 20, String(clase)[0]);
      ctx.fillStyle = textoColor;
      ctx.font = '13px system-ui';
      ctx.fillText(clase, ix + 26, y + 10);
    });
  }
}

function dibujarTablero(lienzo, ctx, escena) {
  const lado = 48;
  const margen = 24;
  lienzo.width = 8 * lado + margen * 2;
  lienzo.height = 8 * lado + margen * 2;
  ctx.imageSmoothingEnabled = true;
  ctx.fillStyle = variable('--panel', '#ffffff');
  ctx.fillRect(0, 0, lienzo.width, lienzo.height);
  for (let y = 0; y < 8; y++) {
    for (let x = 0; x < 8; x++) {
      ctx.fillStyle = (x + y) % 2 === 0 ? '#f0d9b5' : '#b58863';
      ctx.fillRect(margen + x * lado, margen + y * lado, lado, lado);
    }
  }
  for (const m of escena.marcas || []) {
    if (m.clase === 'ultima') {
      ctx.fillStyle = 'rgba(205, 210, 106, 0.65)';
      ctx.fillRect(margen + m.x * lado, margen + m.y * lado, lado, lado);
    }
  }
  ctx.fillStyle = variable('--suave', '#6b6a65');
  ctx.font = '11px system-ui';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  const letras = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
  for (let x = 0; x < 8; x++) {
    ctx.fillText(letras[x], margen + x * lado + lado / 2, margen + 8 * lado + 12);
    ctx.fillText(letras[x], margen + x * lado + lado / 2, margen - 10);
  }
  for (let y = 0; y < 8; y++) {
    ctx.fillText(String(8 - y), margen - 12, margen + y * lado + lado / 2);
    ctx.fillText(String(8 - y), margen + 8 * lado + 12, margen + y * lado + lado / 2);
  }
  for (const p of escena.piezas || []) {
    const simbolo = (UNICODE_PIEZAS[p.color] && UNICODE_PIEZAS[p.color][p.clase]) || '?';
    const px = margen + p.x * lado + lado / 2;
    const py = margen + p.y * lado + lado / 2;
    ctx.font = '36px system-ui, "Segoe UI Symbol", sans-serif';
    ctx.fillStyle = p.color === 'blanco' ? '#ffffff' : '#111111';
    ctx.strokeStyle = p.color === 'blanco' ? '#222222' : '#ffffff';
    ctx.lineWidth = 1;
    ctx.strokeText(simbolo, px, py);
    ctx.fillText(simbolo, px, py);
  }
}

/**
 * Dibuja una escena en un <canvas>. Devuelve true si la reconoce (rejilla, árbol o tablero) y false si no (el que
 * llama enseña entonces la vista de texto). etiquetas: textos traducidos ({inventario}).
 */
export function dibujarEscena(lienzo, escena, mundo, etiquetas = {}) {
  const ctx = lienzo.getContext('2d');
  if (escena && escena.tipo === 'rejilla') dibujarRejilla(lienzo, ctx, escena, mundo);
  else if (escena && escena.tipo === 'arbol') dibujarArbol(lienzo, ctx, escena, mundo, etiquetas);
  else if (escena && escena.tipo === 'tablero') dibujarTablero(lienzo, ctx, escena);
  else return false;
  return true;
}
