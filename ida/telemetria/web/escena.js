// Visor de comprobación de escena() (T2a/T2b, O6, O12): módulo ES sin compilación ni dependencias.
// Lee una grabación (.jsonl.gz con DecompressionStream, o .jsonl) o un registro suelto (.json), reconstruye la escena
// de cada latido (el registro solo la lleva cuando cambia: la de un latido es la última que llegó en su vida) y la
// dibuja con el módulo compartido dibujo.js (el mismo que usa el Vivero). Los textos, con i18n.js (O16).

import { cargarSprites, dibujarEscena } from './dibujo.js';
import { iniciar as iniciarIdioma, t, traducir } from './i18n.js';

await iniciarIdioma();
document.title = t('escena.titulo');
traducir(document);

const $ = (id) => document.getElementById(id);
const lienzo = $('lienzo');
const estado = { cabecera: null, registros: [], escenas: [], i: 0, reproduciendo: false, temporizador: null };

// --- lectura -------------------------------------------------------------------------------------------------------
async function leerTexto(fichero) {
  const comprimido = fichero.name.endsWith('.gz');
  if (!comprimido) return fichero.text();
  if (typeof DecompressionStream === 'undefined') throw new Error(t('escena.sin_gzip'));
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

async function abrir(fichero) {
  $('error').textContent = '';
  try {
    const lineas = analizar(await leerTexto(fichero));
    const cabecera = lineas[0] && lineas[0].tipo === 'cabecera' ? lineas.shift() : null;
    if (!lineas.length) throw new Error(t('escena.vacio'));
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

// --- presentación --------------------------------------------------------------------------------------------------
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
  if (!dibujarEscena(lienzo, escena, mundo, { inventario: t('escena.inventario') })) {
    lienzo.width = 1;
    lienzo.height = 1;
    crudo.hidden = false;
    crudo.textContent = escena ? `${t('escena.no_reconocida', { t: escena.tipo })}\n\n${JSON.stringify(escena, null, 2)}`
      : `${t('escena.sin_escena')}\n\n${r.vista || ''}`;
  }
  $('datos').replaceChildren();
  fila(t('escena.mundo'), mundo || '–');
  fila(`${t('escena.vida')} · ${t('escena.latido')}`, `${r.vida ?? '–'} · ${r.latido ?? '–'}`);
  const a = r.accion;
  fila(t('escena.accion'), a ? `${a.verbo} ${a.objetivo || ''}${a.exito === false ? ' ✗' : ''}` : '–');
  if (escena && escena.extra && typeof escena.extra.luz === 'number') fila(t('escena.luz'), escena.extra.luz.toFixed(2));
  const logros = (r.score && r.score.logros) || [];
  fila(`${t('escena.logros')} (${logros.length})`, logros.join(', ') || '–');
  if (estado.cabecera) {
    fila(t('escena.semilla'), String(estado.cabecera.semilla));
    fila(t('escena.opciones'), JSON.stringify(estado.cabecera.opciones || {}));
  }
}

// --- controles -----------------------------------------------------------------------------------------------------
function parar() {
  estado.reproduciendo = false;
  clearInterval(estado.temporizador);
  $('jugar').textContent = t('escena.jugar');
}

function jugar() {
  if (estado.reproduciendo) { parar(); return; }
  estado.reproduciendo = true;
  $('jugar').textContent = t('escena.pausa');
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
