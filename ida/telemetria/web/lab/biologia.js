// Vista «Biología» del Laboratorio (T5b): qué siente el cuerpo de IdA a lo largo de la vida.
// Series del registro (nivel vital): el cuerpo (con las etiquetas de cada mundo, sección 13.6), la química, el afecto
// (valencia, activación y estado), los indicadores viscerales y el déficit de cada necesidad, con los hechos marcados
// (logros, daños, muerte, nacimiento) y el sueño en bandas. Cada serie lleva un análogo biológico breve, tomado de lo
// que el código hace de verdad (ida/nucleo/soma.py y quien lo llama); las que no tienen uno honesto, ninguno. La tabla
// del final da la línea de código que justifica cada uno (DISENO_OBSERVABILIDAD, sección 15.3).

import { t } from '../i18n.js';
import { esc } from '../componentes/util.js';
import { barrasDelCuerpo } from '../frases.js';
import { leyenda, rangoDe, svgGrafica, tramos } from './graficas.js';

/**
 * Cada serie: columna de las series, si tiene análogo (las claves «bio.analogo.<id>» y «bio.que.<id>» en i18n) y las
 * líneas de código de lo que hace. Sin análogo: «analogo: false» (solo «bio.que.<id>»).
 */
export const SERIES_BIO = [
  { id: 'vitalidad', columna: 'cuerpo/vitalidad', analogo: false, codigo: 'ida/nucleo/soma.py:63,69,71' },
  { id: 'alimentacion', columna: 'cuerpo/alimentacion', analogo: true, codigo: 'ida/nucleo/soma.py:65,80' },
  { id: 'energia', columna: 'cuerpo/energia', analogo: false, codigo: 'ida/nucleo/soma.py:61,67' },
  { id: 'descanso', columna: 'cuerpo/descanso', analogo: true, codigo: 'ida/nucleo/soma.py:60,66 · ida/core/latido.py:310' },
  { id: 'dormido', columna: 'dormido', analogo: true, codigo: 'ida/core/latido.py:310 (_dormir)' },
  { id: 'dopamina', columna: 'quimica/dopamina', analogo: true, codigo: 'ida/core/latido.py:256 · ida/nucleo/soma.py:73,92' },
  { id: 'placer', columna: 'quimica/placer', analogo: true, codigo: 'ida/nucleo/soma.py:72,80 · ida/nucleo/arquitectura.py:57' },
  { id: 'estres', columna: 'quimica/estres', analogo: true, codigo: 'ida/nucleo/soma.py:81-82,97-98 · ida/core/actuar/tribunal.py:50' },
  { id: 'valencia', columna: 'afecto/valencia', analogo: true, codigo: 'ida/nucleo/soma.py:43' },
  { id: 'activacion', columna: 'quimica/estres', analogo: true, codigo: 'ida/s2/sentir/emocion.py:17' },
  { id: 'estado', columna: 'afecto/estado', analogo: true, codigo: 'ida/nucleo/soma.py:101-112' },
  { id: 'peligro', columna: 'indicadores/peligro', analogo: true, codigo: 'ida/core/latido.py:320-323' },
  { id: 'tension', columna: 'indicadores/tension', analogo: false, codigo: 'ida/core/latido.py:325' },
  { id: 'calma', columna: 'indicadores/calma', analogo: false, codigo: 'ida/nucleo/soma.py:99' },
  { id: 'necesidad', columna: 'necesidad/*', analogo: true, codigo: 'ida/nucleo/mundo.py:189 (Necesidad.deficit)' },
];
const POR_ID = Object.fromEntries(SERIES_BIO.map((s) => [s.id, s]));
const COLORES = ['s-musgo', 's-sol', 's-foco', 's-arcilla', 's-tinta', 's-violeta'];
const ESTADOS_AFECTO = ['CALMA', 'CURIOSIDAD', 'ALERTA', 'MIEDO', 'PANICO', 'CANSANCIO', 'DORMIDO'];

function itemLeyenda(id, etiqueta, clase, extra = {}) {
  const s = POR_ID[id];
  return { clase, etiqueta, ayuda: s && s.analogo ? t(`bio.analogo_corto.${id}`) : '', ...extra };
}

/** Bandas del estado afectivo: un tramo por estado seguido. */
function bandasAfecto(col) {
  const salida = [];
  let ini = 0;
  for (let i = 1; i <= col.length; i++) {
    if (i === col.length || col[i] !== col[ini]) {
      if (col[ini]) salida.push({ x0: ini, x1: i, clase: `afecto-${col[ini]}`, titulo: t(`afecto.${col[ini]}`) });
      ini = i;
    }
  }
  return salida;
}

/** El nombre de una necesidad en el idioma de la interfaz (o su nombre en el código si no tiene etiqueta). */
function nombreNecesidad(n) {
  const clave = `necesidad.${n}`;
  return t(clave) === clave ? n : t(clave);
}

/** ctx = {series, mundo, iCursor, cortes, ejeX, marcasDe} */
export function htmlBiologia(ctx) {
  const { series, mundo, iCursor, cortes } = ctx;
  const col = series.columnas;
  const L = series.registros;
  if (!L) return `<p class="suave">${esc(t('bio.vacio'))}</p>`;
  const xs = col.n.map((_, i) => i);
  const dominio = [0, Math.max(1, L - 1)];
  const sueno = tramos(col.dormido || [], xs).map((b) => ({ ...b, clase: 'sueno', titulo: t('bio.dormida') }));
  const marcas = ctx.marcasDe(['logro', 'dano', 'muere', 'nace']);
  const base = { dominio, cortes, cursor: iCursor, ejeX: ctx.ejeX, bandas: sueno, marcas };
  const grafica = (titulo, lineas, rango, ayuda = '') => `<section class="bloque"><h3>${esc(titulo)}</h3>
    ${svgGrafica({ ...base, alto: 160, rango, aria: titulo, lineas: lineas.map((l) => ({ xs, ys: col[l.columna], clase: l.clase, etiqueta: l.etiqueta, discontinua: l.discontinua })) })}
    ${leyenda(lineas)}${ayuda ? `<p class="mini suave">${esc(ayuda)}</p>` : ''}</section>`;

  const barras = barrasDelCuerpo(mundo).filter((b) => col[`cuerpo/${b.clave}`]);
  const cuerpo = barras.map((b, i) => itemLeyenda(b.clave, b.etiqueta, COLORES[i], { columna: `cuerpo/${b.clave}` }));
  const quimica = [
    itemLeyenda('dopamina', t('bio.serie.dopamina'), 's-sol', { columna: 'quimica/dopamina' }),
    itemLeyenda('placer', t('bio.serie.placer'), 's-musgo', { columna: 'quimica/placer' }),
  ];
  const afecto = [
    itemLeyenda('valencia', t('bio.serie.valencia'), 's-musgo', { columna: 'afecto/valencia' }),
    itemLeyenda('estres', t('bio.serie.estres_activacion'), 's-arcilla', { columna: 'quimica/estres' }),
  ];
  const indicadores = ['peligro', 'tension', 'calma'].map((k, i) => itemLeyenda(k, t(`bio.serie.${k}`), ['s-arcilla', 's-sol', 's-musgo'][i], { columna: `indicadores/${k}` }));
  const necesidades = Object.keys(col).filter((k) => k.startsWith('necesidad/')).map((k, i) => ({
    columna: k, clase: COLORES[i % COLORES.length], etiqueta: t('bio.deficit_de', { nombre: nombreNecesidad(k.slice(10)) }),
  }));
  const estado = col['afecto/estado'] || [];
  const presentes = ESTADOS_AFECTO.filter((e) => estado.includes(e));
  const franjaAfecto = svgGrafica({ ...base, alto: 70, rango: [0, 1], lineas: [], bandas: [...bandasAfecto(estado), ...sueno.map((b) => ({ ...b, clase: 'sueno-borde' }))], aria: t('bio.estado') });
  const v = (k) => (col[k] ? col[k][iCursor] : null);
  const ahora = `<dl class="cifras cifras-7">
    ${barras.map((b) => `<div><dt>${esc(b.etiqueta)}</dt><dd>${esc(String(v(`cuerpo/${b.clave}`) ?? '–'))}</dd></div>`).join('')}
    <div><dt>${esc(t('bio.serie.dopamina'))}</dt><dd>${esc(String(v('quimica/dopamina') ?? '–'))}</dd></div>
    <div><dt>${esc(t('bio.serie.estres'))}</dt><dd>${esc(String(v('quimica/estres') ?? '–'))}</dd></div>
    <div><dt>${esc(t('bio.estado'))}</dt><dd>${esc(estado[iCursor] ? t(`afecto.${estado[iCursor]}`) : '–')}${v('dormido') ? ' 🌙' : ''}</dd></div></dl>`;
  return `<div class="vista-series biologia">
    <section class="bloque"><div class="bloque-titulo"><h2>${esc(t('bio.titulo'))}</h2><span class="mini suave">${esc(t('epi.en_latido', { latido: col.latido[iCursor] }))}</span></div>
      <p class="suave pequeno">${esc(t('bio.ayuda'))}</p>${ahora}
      <div class="leyenda-carril mini suave"><span>★ ${esc(t('lab.hecho.logro'))}</span><span>▼ ${esc(t('bio.dano'))}</span><span>✕ ${esc(t('lab.hecho.muere'))}</span>
        <span>▲ ${esc(t('lab.hecho.nace'))}</span><span><i class="tramo-muestra sueno"></i>${esc(t('bio.dormida'))}</span></div></section>
    ${grafica(t('bio.cuerpo'), cuerpo, [0, 100], t('bio.cuerpo_ayuda'))}
    ${grafica(t('bio.quimica'), quimica, rangoDe(quimica.map((l) => col[l.columna]), { min: 0, max: 100 }))}
    ${grafica(t('bio.afecto'), afecto, [-1, 1], t('bio.afecto_ayuda'))}
    <section class="bloque"><h3>${esc(t('bio.estado'))}</h3>${franjaAfecto}
      <div class="leyenda-carril mini suave">${presentes.map((e) => `<span><i class="tramo-muestra afecto-${e}"></i>${esc(t(`afecto.${e}`))}</span>`).join('')}</div>
      <p class="mini suave">${esc(t('bio.analogo_corto.estado'))}</p></section>
    ${grafica(t('bio.indicadores'), indicadores, [0, 1])}
    ${necesidades.length ? grafica(t('bio.necesidades'), necesidades, [0, 1], t('bio.analogo_corto.necesidad')) : ''}
    <section class="bloque"><h3>${esc(t('bio.tabla'))}</h3><p class="suave pequeno">${esc(t('bio.tabla_ayuda'))}</p>
      <div class="tabla-desliza"><table class="tabla-lab tabla-analogos"><thead><tr><th>${esc(t('bio.col_serie'))}</th><th>${esc(t('bio.col_que'))}</th>
        <th>${esc(t('bio.col_analogo'))}</th><th>${esc(t('bio.col_codigo'))}</th></tr></thead><tbody>
        ${SERIES_BIO.map((s) => `<tr><td><b>${esc(t(`bio.serie.${s.id}`))}</b></td><td>${esc(t(`bio.que.${s.id}`))}</td>
          <td>${s.analogo ? esc(t(`bio.analogo.${s.id}`)) : `<span class="suave">${esc(t('bio.sin_analogo'))}</span>`}</td><td><code>${esc(s.codigo)}</code></td></tr>`).join('')}
      </tbody></table></div></section></div>`;
}
