// Visor de comprobación de escena() (T2a/T2b, O6, O12): módulo ES sin compilación ni dependencias.
// Lee una grabación (.jsonl.gz con DecompressionStream, o .jsonl) o un registro suelto (.json), reconstruye la escena
// de cada latido (el registro solo la lleva cuando cambia: la de un latido es la última que llegó en su vida) y dibuja
// en Canvas las de tipo «rejilla», «arbol» y «tablero».

const BASE = new URL('.', import.meta.url);          // .../web/
const CELDA = 48;                                    // píxeles por casilla (sprites de 16 × 3)
const FILA_INVENTARIO = 28;

const UNICODE_PIEZAS = {
  blanco: { rey: '♔', dama: '♕', torre: '♖', alfil: '♗', caballo: '♘', peon: '♙' },
  negro: { rey: '♚', dama: '♛', torre: '♜', alfil: '♝', caballo: '♞', peon: '♟' },
};

const TEXTOS = {
  es: { titulo: 'Visor de escena', pista: 'Comprobación de escena() (T2a/T2b), no es el Vivero. Carga una grabación .jsonl.gz o .jsonl, o un registro .json.',
        soltar: 'o suelta aquí el fichero', jugar: '▶ Reproducir', pausa: '❚❚ Pausa', latido: 'latido', vida: 'vida', mundo: 'mundo',
        accion: 'acción', luz: 'luz', logros: 'logros', inventario: 'inventario', sinEscena: 'Este registro no trae escena: vista de texto.',
        sinGzip: 'Este navegador no tiene DecompressionStream: descomprime la grabación y carga el .jsonl.',
        noRejilla: 'Escena de tipo «{t}»: formato no reconocido.', vacio: 'El fichero no tiene registros.',
        opciones: 'opciones', semilla: 'semilla' },
  en: { titulo: 'Scene viewer', pista: 'scene() check (T2a/T2b), not the Nursery. Load a .jsonl.gz or .jsonl recording, or a .json record.',
        soltar: 'or drop the file here', jugar: '▶ Play', pausa: '❚❚ Pause', latido: 'beat', vida: 'life', mundo: 'world',
        accion: 'action', luz: 'light', logros: 'achievements', inventario: 'inventory', sinEscena: 'This record has no scene: text view.',
        sinGzip: 'This browser lacks DecompressionStream: decompress the recording and load the .jsonl.',
        noRejilla: 'Scene of type “{t}”: unrecognized format.', vacio: 'The file has no records.',
        opciones: 'options', semilla: 'seed' },
};
const idioma = (navigator.language || 'en').toLowerCase().startsWith('es') ? 'es' : 'en';
const t = (k, p = {}) => (TEXTOS[idioma][k] || k).replace(/\{(\w+)\}/g, (_, n) => p[n] ?? '');
document.documentElement.lang = idioma;
document.querySelectorAll('[data-t]').forEach((el) => { el.textContent = t(el.dataset.t); });

const $ = (id) => document.getElementById(id);
const lienzo = $('lienzo');
const ctx = lienzo.getContext('2d');
const estado = { cabecera: null, registros: [], escenas: [], i: 0, reproduciendo: false, temporizador: null, sprites: {} };

// --- lectura -------------------------------------------------------------------------------------------------------
async function leerTexto(fichero) {
  const comprimido = fichero.name.endsWith('.gz');
  if (!comprimido) return fichero.text();
  if (typeof DecompressionStream === 'undefined') throw new Error(t('sinGzip'));
  const flujo = fichero.stream().pipeThrough(new DecompressionStream('gzip'));
  return new Response(flujo).text();
}

function analizar(texto) {
  const limpio = texto.trim();
  try {                                              // un registro suelto (.json) o una lista de registros
    const uno = JSON.parse(limpio);
    return Array.isArray(uno) ? uno : [uno];
  } catch { /* .jsonl: un registro por línea */ }
  return limpio.split('\n').filter((l) => l.trim()).map((l) => JSON.parse(l));
}

/** La escena de cada registro: la última que llegó en su vida (O6). */
function reconstruir(registros) {
  const salida = [];
  let actual = null;
  let vida;
  for (const r of registros) {
    if (r.vida !== vida) { vida = r.vida; actual = null; }
    if (r.escena) actual = r.escena;
    salida.push(actual);
  }
  return salida;
}

async function cargarSprites(mundo) {
  if (!mundo || estado.sprites[mundo]) return;
  const sprites = { imagenes: {}, mapa: {} };
  estado.sprites[mundo] = sprites;
  try {
    const url = new URL(`sprites/${encodeURIComponent(mundo)}/indice.json`, BASE);
    const resp = await fetch(url);
    if (!resp.ok) return;                         // sin sprites: colores y letras
    const indice = await resp.json();
    sprites.mapa = indice.mapa_sprites || {};
    const ficheros = [...new Set(Object.values(sprites.mapa))];
    await Promise.all(ficheros.map((f) => new Promise((ok) => {
      const img = new Image();
      img.onload = () => { sprites.imagenes[f] = img; ok(); };
      img.onerror = ok;
      img.src = new URL(`sprites/${encodeURIComponent(mundo)}/${f}`, BASE).href;
    })));
  } catch { /* sin servidor: colores y letras */ }
}

async function abrir(fichero) {
  $('error').textContent = '';
  try {
    const lineas = analizar(await leerTexto(fichero));
    const cabecera = lineas[0] && lineas[0].tipo === 'cabecera' ? lineas.shift() : null;
    if (!lineas.length) throw new Error(t('vacio'));
    estado.cabecera = cabecera;
    estado.registros = lineas;
    estado.escenas = reconstruir(lineas);
    const mundos = new Set(lineas.map((r) => r.mundo).filter(Boolean));
    if (cabecera && cabecera.mundo) mundos.add(cabecera.mundo);
    await Promise.all([...mundos].map(cargarSprites));
    const cursor = $('cursor');
    cursor.max = String(lineas.length - 1);
    cursor.value = '0';
    for (const id of ['cursor', 'atras', 'adelante', 'jugar']) $(id).disabled = lineas.length < 2 && id !== 'cursor';
    cursor.disabled = false;
    ir(0);
  } catch (e) {
    $('error').textContent = String(e.message || e);
  }
}

// --- dibujo --------------------------------------------------------------------------------------------------------
function colorDe(clase) {
  let h = 0;
  for (const c of String(clase)) h = (h * 31 + c.codePointAt(0)) % 360;
  return `hsl(${h} 45% 52%)`;
}

function sprite(mundo, claves) {
  const s = estado.sprites[mundo];
  if (!s) return null;
  for (const k of claves) {
    const f = k && s.mapa[k];
    if (f && s.imagenes[f]) return s.imagenes[f];
  }
  return null;
}

function pintar(mundo, claves, x, y, tam, letra) {
  const img = sprite(mundo, claves);
  if (img) { ctx.drawImage(img, x, y, tam, tam); return; }
  ctx.fillStyle = colorDe(claves[claves.length - 1]);
  ctx.fillRect(x + 2, y + 2, tam - 4, tam - 4);
  ctx.fillStyle = '#fff';
  ctx.font = `bold ${Math.round(tam * 0.45)}px system-ui`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(letra, x + tam / 2, y + tam / 2);
}

function dibujarRejilla(escena, mundo) {
  const inv = Object.entries(escena.inventario || {}).filter(([, n]) => n);
  const porFila = Math.max(1, Math.floor((escena.ancho * CELDA) / (FILA_INVENTARIO * 2.6)));
  const filasInv = Math.ceil(inv.length / porFila);
  lienzo.width = escena.ancho * CELDA;
  lienzo.height = escena.alto * CELDA + filasInv * (FILA_INVENTARIO + 6) + (filasInv ? 8 : 0);
  ctx.imageSmoothingEnabled = false;
  const vacio = getComputedStyle(document.documentElement).getPropertyValue('--vacio').trim() || '#222';
  ctx.fillStyle = vacio;
  ctx.fillRect(0, 0, lienzo.width, lienzo.height);
  escena.celdas.forEach((fila, y) => fila.forEach((clase, x) => {
    if (clase != null) pintar(mundo, [clase, '?'], x * CELDA, y * CELDA, CELDA, String(clase)[0] || '?');
  }));
  for (const e of escena.entidades || []) {
    const claves = [e.estado ? `${e.clase}.${e.estado}` : null, e.clase, '?'];
    pintar(mundo, claves, e.x * CELDA, e.y * CELDA, CELDA, String(e.clase)[0].toUpperCase());
  }
  if (escena.yo) {
    const yo = escena.yo;
    pintar(mundo, [yo.estado ? `yo.${yo.estado}` : null, yo.orientacion ? `yo.${yo.orientacion}` : null, 'yo.sur', 'yo'],
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
    pintar(mundo, [clase, '?'], x + 4, y, FILA_INVENTARIO, String(clase)[0]);
    ctx.fillStyle = '#f2f1ec';                         // sobre el fondo oscuro de la franja del inventario
    ctx.font = 'bold 14px system-ui';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(String(n), x + FILA_INVENTARIO + 8, y + FILA_INVENTARIO / 2);
  });
}

function dibujarArbol(escena, mundo) {
  const filaAlt = 32;
  const inv = Object.entries(escena.inventario || {}).filter(([, n]) => n);
  const items = [];

  for (const nodo of escena.nodos || []) {
    items.push({ tipo: 'nodo', nodo });
    for (const ent of escena.entidades || []) {
      if (ent.ruta === nodo.ruta) {
        items.push({ tipo: 'entidad', ent, ruta: nodo.ruta });
      }
    }
  }

  const margen = 16;
  const ancho = 480;
  const alto = margen * 2 + items.length * filaAlt + (inv.length ? 50 : 0);
  lienzo.width = ancho;
  lienzo.height = Math.max(200, alto);
  ctx.imageSmoothingEnabled = true;

  const fondo = getComputedStyle(document.documentElement).getPropertyValue('--panel').trim() || '#ffffff';
  const textoColor = getComputedStyle(document.documentElement).getPropertyValue('--texto').trim() || '#1d1d1b';
  const suaveColor = getComputedStyle(document.documentElement).getPropertyValue('--suave').trim() || '#6b6a65';
  const bordeColor = getComputedStyle(document.documentElement).getPropertyValue('--borde').trim() || '#dddcd6';
  const acentoColor = getComputedStyle(document.documentElement).getPropertyValue('--acento').trim() || '#2f6f4f';

  ctx.fillStyle = fondo;
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

      pintar(mundo, [n.clase, 'carpeta', '?'], x, y + 4, 24, n.clase === 'raiz' ? 'R' : 'C');

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

      pintar(mundo, [e.clase, '?'], x, y + 6, 20, String(e.clase)[0]);

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
    ctx.strokeStyle = bordeColor;
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
    ctx.fillText(t('inventario') + ':', margen, y + 10);
    inv.forEach(([clase, n], k) => {
      const ix = margen + 80 + k * 80;
      pintar(mundo, [clase, '?'], ix, y, 20, String(clase)[0]);
      ctx.fillStyle = textoColor;
      ctx.font = '13px system-ui';
      ctx.fillText(clase, ix + 26, y + 10);
    });
  }
}

function dibujarTablero(escena, mundo) {
  const lado = 48;
  const margen = 24;
  lienzo.width = 8 * lado + margen * 2;
  lienzo.height = 8 * lado + margen * 2;
  ctx.imageSmoothingEnabled = true;

  const fondo = getComputedStyle(document.documentElement).getPropertyValue('--panel').trim() || '#ffffff';
  ctx.fillStyle = fondo;
  ctx.fillRect(0, 0, lienzo.width, lienzo.height);

  const colorClara = '#f0d9b5';
  const colorOscura = '#b58863';
  for (let y = 0; y < 8; y++) {
    for (let x = 0; x < 8; x++) {
      ctx.fillStyle = (x + y) % 2 === 0 ? colorClara : colorOscura;
      ctx.fillRect(margen + x * lado, margen + y * lado, lado, lado);
    }
  }

  for (const m of escena.marcas || []) {
    if (m.clase === 'ultima') {
      ctx.fillStyle = 'rgba(205, 210, 106, 0.65)';
      ctx.fillRect(margen + m.x * lado, margen + m.y * lado, lado, lado);
    }
  }

  ctx.fillStyle = '#6b6a65';
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
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = p.color === 'blanco' ? '#ffffff' : '#111111';
    ctx.strokeStyle = p.color === 'blanco' ? '#222222' : '#ffffff';
    ctx.lineWidth = 1;
    ctx.strokeText(simbolo, px, py);
    ctx.fillText(simbolo, px, py);
  }
}

function fila(dt, dd) {
  const a = document.createElement('dt');
  a.textContent = dt;
  const b = document.createElement('dd');
  b.textContent = dd;
  $('datos').append(a, b);
}

function ir(i) {
  const n = estado.registros.length;
  if (!n) return;
  estado.i = Math.max(0, Math.min(n - 1, i));
  const r = estado.registros[estado.i];
  const escena = estado.escenas[estado.i];
  const mundo = r.mundo || (estado.cabecera && estado.cabecera.mundo);
  $('cursor').value = String(estado.i);
  $('posicion').textContent = `${estado.i + 1} / ${n}`;
  const crudo = $('crudo');
  crudo.hidden = true;
  if (escena && escena.tipo === 'rejilla') {
    dibujarRejilla(escena, mundo);
  } else if (escena && escena.tipo === 'arbol') {
    dibujarArbol(escena, mundo);
  } else if (escena && escena.tipo === 'tablero') {
    dibujarTablero(escena, mundo);
  } else {
    lienzo.width = 1;
    lienzo.height = 1;
    crudo.hidden = false;
    crudo.textContent = escena ? `${t('noRejilla', { t: escena.tipo })}\n\n${JSON.stringify(escena, null, 2)}`
      : `${t('sinEscena')}\n\n${r.vista || ''}`;
  }
  $('datos').replaceChildren();
  fila(t('mundo'), mundo || '–');
  fila(`${t('vida')} · ${t('latido')}`, `${r.vida ?? '–'} · ${r.latido ?? '–'}`);
  const a = r.accion;
  fila(t('accion'), a ? `${a.verbo} ${a.objetivo || ''}${a.exito === false ? ' ✗' : ''}` : '–');
  if (escena && escena.extra && typeof escena.extra.luz === 'number') fila(t('luz'), escena.extra.luz.toFixed(2));
  const logros = (r.score && r.score.logros) || [];
  fila(`${t('logros')} (${logros.length})`, logros.join(', ') || '–');
  if (estado.cabecera) {
    fila(t('semilla'), String(estado.cabecera.semilla));
    fila(t('opciones'), JSON.stringify(estado.cabecera.opciones || {}));
  }
}

// --- controles -----------------------------------------------------------------------------------------------------
function parar() {
  estado.reproduciendo = false;
  clearInterval(estado.temporizador);
  $('jugar').textContent = t('jugar');
}

function jugar() {
  if (estado.reproduciendo) { parar(); return; }
  estado.reproduciendo = true;
  $('jugar').textContent = t('pausa');
  const ms = Math.max(8, 400 / Number($('velocidad').value));
  estado.temporizador = setInterval(() => {
    if (estado.i >= estado.registros.length - 1) { parar(); return; }
    ir(estado.i + 1);
  }, ms);
}

$('fichero').addEventListener('change', (ev) => { parar(); if (ev.target.files[0]) abrir(ev.target.files[0]); });
$('cursor').addEventListener('input', (ev) => { parar(); ir(Number(ev.target.value)); });
$('atras').addEventListener('click', () => { parar(); ir(estado.i - 1); });
$('adelante').addEventListener('click', () => { parar(); ir(estado.i + 1); });
$('jugar').addEventListener('click', jugar);
$('velocidad').addEventListener('change', () => { if (estado.reproduciendo) { parar(); jugar(); } });
document.addEventListener('keydown', (ev) => {
  if (ev.target.tagName === 'INPUT' && ev.target.type !== 'range') return;
  if (ev.key === 'ArrowLeft') { parar(); ir(estado.i - 1); }
  if (ev.key === 'ArrowRight') { parar(); ir(estado.i + 1); }
  if (ev.key === ' ') { ev.preventDefault(); jugar(); }
});
const zona = $('soltar');
zona.addEventListener('dragover', (ev) => { ev.preventDefault(); zona.classList.add('encima'); });
zona.addEventListener('dragleave', () => zona.classList.remove('encima'));
zona.addEventListener('drop', (ev) => {
  ev.preventDefault();
  zona.classList.remove('encima');
  if (ev.dataTransfer.files[0]) { parar(); abrir(ev.dataTransfer.files[0]); }
});
