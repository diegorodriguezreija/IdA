// Aplicación de IdA (O1, O12): cabecera con idioma y tema, y rutas #/antesala, #/vivero y #/lab.
// Módulos ES y Web Components, sin compilación ni dependencias.

import { cambiar, idioma, iniciar, t, traducir } from './i18n.js';
import './vistas/antesala.js';
import './vistas/vivero.js';
import './vistas/lab.js';

const RUTAS = { antesala: 'ida-antesala', vivero: 'ida-vivero', lab: 'ida-lab' };
const CLAVE_TEMA = 'ida.tema';

/** El modo elegido: «sistema» (el del sistema operativo), «light» o «dark». */
function modoTema() {
  const fijado = document.documentElement.dataset.theme;
  return fijado === 'light' || fijado === 'dark' ? fijado : 'sistema';
}

function pintarTema() {
  const modo = modoTema();
  document.querySelectorAll('#temas [data-tema]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.tema === modo)));
}

function elegirTema(modo) {
  if (modo === 'light' || modo === 'dark') document.documentElement.dataset.theme = modo;
  else delete document.documentElement.dataset.theme;
  try {
    if (modo === 'light' || modo === 'dark') localStorage.setItem(CLAVE_TEMA, modo);
    else localStorage.removeItem(CLAVE_TEMA);
  } catch { /* sin almacenamiento: no se recuerda */ }
  pintarTema();
  document.dispatchEvent(new CustomEvent('ida:tema', { detail: { tema: modo } }));
}

function pintarIdioma() {
  document.querySelectorAll('#idiomas button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.idioma === idioma())));
  document.title = t('app.titulo');
}

function ruta() {
  const nombre = (location.hash.replace(/^#\/?/, '').split(/[/?]/)[0] || 'antesala');
  return RUTAS[nombre] ? nombre : 'antesala';
}

function mostrar() {
  const nombre = ruta();
  if (!location.hash.startsWith(`#/${nombre}`)) history.replaceState(null, '', `#/${nombre}`);
  document.querySelectorAll('.navegacion a').forEach((a) => {
    if (a.dataset.ruta === nombre) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
  });
  const vista = document.getElementById('vista');
  if (vista.firstElementChild && vista.firstElementChild.localName === RUTAS[nombre]) return;
  vista.replaceChildren(document.createElement(RUTAS[nombre]));
  window.scrollTo({ top: 0 });
}

await iniciar();
traducir(document);
pintarIdioma();
pintarTema();
document.querySelectorAll('#idiomas button').forEach((b) => b.addEventListener('click', async () => {
  await cambiar(b.dataset.idioma);
  pintarIdioma();
}));
document.querySelectorAll('#temas [data-tema]').forEach((b) => b.addEventListener('click', () => elegirTema(b.dataset.tema)));
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { pintarTema(); document.dispatchEvent(new CustomEvent('ida:tema')); });
window.addEventListener('hashchange', mostrar);
mostrar();
