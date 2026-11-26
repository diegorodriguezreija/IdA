// Idiomas de la aplicación (O16): español e inglés. Módulo ES sin dependencias.
// - Por defecto, el del navegador (es* → español; el resto → inglés). La elección se recuerda en localStorage.
// - t(clave, {param}) traduce; los textos están en i18n/es.json e i18n/en.json (mismas claves, lo comprueba un test).
// - En el HTML: data-i18n (texto), data-i18n-aria (aria-label), data-i18n-title y data-i18n-placeholder, con la
//   clave como valor. traducir(raiz) los aplica.
// - texto({es, en}) elige el idioma de los textos que vienen de la API (opciones de los mundos, presets).

export const IDIOMAS = ['es', 'en'];
const CLAVE_GUARDADA = 'ida.idioma';
const BASE = new URL('.', import.meta.url);
const diccionarios = {};
let actual = 'en';

function leerGuardado() {
  try { return localStorage.getItem(CLAVE_GUARDADA); } catch { return null; }
}

function guardar(idioma) {
  try { localStorage.setItem(CLAVE_GUARDADA, idioma); } catch { /* sin almacenamiento: no se recuerda */ }
}

export function idiomaDelNavegador() {
  const nav = (navigator.languages && navigator.languages[0]) || navigator.language || 'en';
  return nav.toLowerCase().startsWith('es') ? 'es' : 'en';
}

async function cargar(idioma) {
  if (!diccionarios[idioma]) {
    const resp = await fetch(new URL(`i18n/${idioma}.json`, BASE));
    diccionarios[idioma] = resp.ok ? await resp.json() : {};
  }
  return diccionarios[idioma];
}

export function idioma() { return actual; }

export async function iniciar() {
  const guardado = leerGuardado();
  await usar(IDIOMAS.includes(guardado) ? guardado : idiomaDelNavegador(), false);
}

async function usar(idiomaNuevo, recordar) {
  actual = IDIOMAS.includes(idiomaNuevo) ? idiomaNuevo : 'en';
  await cargar(actual);
  if (recordar) guardar(actual);
  document.documentElement.lang = actual;
}

export async function cambiar(idiomaNuevo) {
  await usar(idiomaNuevo, true);
  traducir(document);
  document.dispatchEvent(new CustomEvent('ida:idioma', { detail: { idioma: actual } }));
}

// Plurales (T5b): «{n|latido|latidos}» da «latido» si params.n es 1 y «latidos» si no. Así cada plantilla tiene sus dos
// formas en su idioma («{n} {n|latido|latidos}», «{n} {n|heartbeat|heartbeats}») y nunca sale «1 cosas».
const PLURAL = /\{(\w+)\|([^|{}]*)\|([^|{}]*)\}/g;

export function plural(plantilla, params = {}) {
  return String(plantilla).replace(PLURAL, (_, n, uno, varios) => (Number(params[n]) === 1 ? uno : varios));
}

export function t(clave, params = {}) {
  const dic = diccionarios[actual] || {};
  const plantilla = dic[clave] ?? (diccionarios.es || {})[clave] ?? clave;
  return plural(plantilla, params).replace(/\{(\w+)\}/g, (_, n) => (params[n] ?? `{${n}}`));
}

/** El texto de un objeto {es, en} en el idioma actual (o el primero que haya). */
export function texto(obj) {
  if (obj == null) return '';
  if (typeof obj === 'string') return obj;
  return obj[actual] ?? obj.es ?? obj.en ?? Object.values(obj)[0] ?? '';
}

const ATRIBUTOS = { aria: 'aria-label', title: 'title', placeholder: 'placeholder' };

export function traducir(raiz = document) {
  raiz.querySelectorAll('[data-i18n]').forEach((el) => { el.textContent = t(el.dataset.i18n); });
  for (const [sufijo, atributo] of Object.entries(ATRIBUTOS)) {
    const campo = `i18n${sufijo[0].toUpperCase()}${sufijo.slice(1)}`;
    raiz.querySelectorAll(`[data-i18n-${sufijo}]`).forEach((el) => { el.setAttribute(atributo, t(el.dataset[campo])); });
  }
}
