// Formulario de las opciones de un mundo, generado desde sus declaraciones (O8, Mundo.opciones()).
// Cada declaración: nombre, tipo (entero, real, opcion, booleano), min/max o valores, defecto, etiqueta y ayuda {es, en}
// y, opcionales, vacia y etiquetas_valores ({valor: {es, en}}: el texto de cada valor de una opción, T4a). Las básicas (números y opciones) se ven; las avanzadas (booleanas o que admiten vacío) van plegadas.

import { t, texto } from '../i18n.js';
import { esc } from './util.js';

export function esAvanzada(d) {
  return d.tipo === 'booleano' || Boolean(d.vacia);
}

function paso(d) {
  if (d.tipo === 'entero') return 1;
  const rango = d.max - d.min;
  return rango <= 1 ? 0.01 : rango <= 10 ? 0.1 : 1;
}

/** El texto de un valor de una opción de tipo «opcion»: su etiqueta en el idioma actual o, si no la tiene, el valor. */
export function etiquetaValor(d, v) {
  const ev = d.etiquetas_valores && d.etiquetas_valores[v];
  return ev ? texto(ev) : String(v);
}

export function mostrarValor(d, v) {
  if (v === null || v === undefined || v === '') return t('empezar.vacio');
  if (d.tipo === 'booleano') return v ? t('empezar.si') : t('empezar.no');
  if (d.tipo === 'opcion') return etiquetaValor(d, v);
  return String(v);
}

function control(d, valor, id) {
  const nombre = esc(d.nombre);
  if (d.tipo === 'booleano') {
    return `<label class="interruptor"><input type="checkbox" id="${id}" data-opcion="${nombre}" ${valor ? 'checked' : ''}>
      <span>${esc(texto(d.etiqueta))}</span></label>`;
  }
  if (d.tipo === 'opcion') {
    const opciones = d.valores.map((v) => `<option value="${esc(v)}" ${v === valor ? 'selected' : ''}>${esc(etiquetaValor(d, v))}</option>`).join('');
    return `<select class="entrada" id="${id}" data-opcion="${nombre}">${opciones}</select>`;
  }
  const v = valor === null || valor === undefined ? '' : valor;
  const numero = `<input class="entrada" type="number" id="${id}" data-opcion="${nombre}" min="${d.min}" max="${d.max}" step="${paso(d)}"
    value="${esc(v)}" ${d.vacia ? `placeholder="${esc(t('empezar.vacio'))}"` : 'required'} inputmode="${d.tipo === 'entero' ? 'numeric' : 'decimal'}">`;
  const conDeslizador = !d.vacia && (d.max - d.min) / paso(d) <= 400;
  if (!conDeslizador) return numero;
  return `<div class="deslizador"><input type="range" min="${d.min}" max="${d.max}" step="${paso(d)}" value="${esc(v)}"
    data-espejo="${nombre}" aria-hidden="true" tabindex="-1">${numero}</div>`;
}

function campo(d, valor) {
  const id = `opc-${d.nombre}`;
  const ayuda = `<small id="${id}-ayuda">${esc(texto(d.ayuda))}</small>`;
  const defecto = `<span class="defecto">${esc(t('empezar.defecto', { valor: mostrarValor(d, d.defecto) }))}</span>`;
  if (d.tipo === 'booleano') {
    return `<div class="campo">${control(d, valor, id)}${ayuda}${defecto}</div>`;
  }
  return `<div class="campo"><label for="${id}">${esc(texto(d.etiqueta))}</label>${control(d, valor, id)}${ayuda}${defecto}</div>`;
}

/** El HTML de las opciones dadas (lista de declaraciones) con sus valores actuales. */
export function htmlOpciones(declaraciones, valores) {
  return declaraciones.map((d) => campo(d, d.nombre in valores ? valores[d.nombre] : d.defecto)).join('');
}

/** El valor de una opción desde su control, ya con el tipo de JSON que espera la API (o null si va vacía). */
export function leerControl(d, el) {
  if (d.tipo === 'booleano') return el.checked;
  if (d.tipo === 'opcion') return el.value;
  if (el.value.trim() === '') return d.vacia ? null : el.value;
  const n = Number(el.value);
  return Number.isFinite(n) ? (d.tipo === 'entero' ? Math.round(n) : n) : el.value;
}

/** Conecta los controles de una raíz con un manejador (nombre, valor) y sincroniza deslizador y número. */
export function conectarOpciones(raiz, declaraciones, alCambiar) {
  const porNombre = Object.fromEntries(declaraciones.map((d) => [d.nombre, d]));
  raiz.querySelectorAll('[data-opcion]').forEach((el) => {
    const d = porNombre[el.dataset.opcion];
    if (!d) return;
    const espejo = raiz.querySelector(`[data-espejo="${CSS.escape(d.nombre)}"]`);
    const avisar = () => {
      const fuera = d.tipo !== 'booleano' && d.tipo !== 'opcion' && el.value.trim() !== '' && !el.checkValidity();
      el.setAttribute('aria-invalid', String(fuera));
      alCambiar(d.nombre, leerControl(d, el));
    };
    el.addEventListener(el.type === 'checkbox' || el.tagName === 'SELECT' ? 'change' : 'input', () => {
      if (espejo) espejo.value = el.value;
      avisar();
    });
    if (espejo) espejo.addEventListener('input', () => { el.value = espejo.value; avisar(); });
  });
}
