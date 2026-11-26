// Frases de la vida en el idioma elegido (O5, O16, T4a): la interfaz forma la frase desde datos estructurados.
// - Clases de cada mundo: web/i18n/clases/<mundo>.json, con su forma con artículo definido («el», «la», «the») e
//   indefinido («un», «una», «a» o nada en los incontables) y, en español, su género («g»). También las frases de
//   acción propias del mundo («acciones»: «VERBO» o «VERBO:clase»), los logros y las claves de la puntuación.
// - Plantillas comunes (hechos, saber, verbos, motivos, planes): claves de web/i18n/es.json y en.json.
// Nada de esto sale del motor como frase: solo tipos y parámetros del registro del latido (secciones 4 y 5).

import { idioma, t, texto } from './i18n.js';

const BASE = new URL('.', import.meta.url);
const mundos = {};                 // mundo -> {clases, acciones, logros, puntos, valores} (o {} si no hay fichero)

/** Carga las etiquetas de un mundo (una vez). */
export async function cargarFrases(mundo) {
  if (!mundo || mundos[mundo]) return;
  mundos[mundo] = {};
  try {
    const resp = await fetch(new URL(`i18n/clases/${encodeURIComponent(mundo)}.json`, BASE));
    if (resp.ok) mundos[mundo] = await resp.json();
  } catch { /* sin fichero: nombres tal cual */ }
}

function datos(mundo) { return mundos[mundo] || {}; }

/** Primera letra en mayúscula. */
export function capital(s) { const x = String(s ?? ''); return x ? x[0].toUpperCase() + x.slice(1) : x; }
function minuscula(s) { const x = String(s ?? ''); return x ? x[0].toLowerCase() + x.slice(1) : x; }

/** Contracciones del español: «a el» → «al», «de el» → «del». */
function contraer(s) {
  return idioma() === 'es' ? s.replace(/\b([Aa]) el\b/g, '$1l').replace(/\b([Dd])e el\b/g, '$1el') : s;
}

/** Un nombre legible para una clase sin etiqueta: «Boletus_edulis» → «Boletus edulis». */
function legible(clase) { return String(clase ?? '').replace(/_/g, ' '); }

/** ¿Tiene etiqueta esta clase en este mundo? */
export function tieneEtiqueta(mundo, clase) { return Boolean((datos(mundo).clases || {})[clase]); }

/**
 * La clase en el idioma actual. forma: 'el' (con artículo definido), 'un' (indefinido o nada) o 'nombre' (sin
 * artículo, en mayúscula: para etiquetas sueltas).
 */
export function clase(mundo, c, forma = 'nombre') {
  const e = (datos(mundo).clases || {})[c];
  const f = e && (e[idioma()] || e.es);
  if (!f) return legible(c);
  if (forma === 'el' || forma === 'un') return f[forma];
  return capital(f.el.replace(/^(el|la|los|las|the|su|its)\s+/i, ''));
}

/** La clave del sprite de una clase (la propia o su «sprite», p. ej. «wood» → «madera») y su icono de texto, si tiene. */
export function spriteDe(mundo, c) {
  const e = (datos(mundo).clases || {})[c];
  return { clave: (e && e.sprite) || c, icono: (e && e.icono) || '' };
}

/** «o» o «a» según el género de la clase (para concordar adjetivos en español). */
function terminacion(mundo, c) {
  const e = (datos(mundo).clases || {})[c];
  return e && e.es && e.es.g === 'f' ? 'a' : 'o';
}

/** El texto de un logro del mundo (o el nombre tal cual). */
export function logro(mundo, nombre) {
  const l = (datos(mundo).logros || {})[nombre];
  return l ? texto(l) : legible(nombre);
}

/** Los logros que el mundo declara en sus etiquetas (en orden), o vacío. */
export function logrosDelMundo(mundo) { return Object.keys(datos(mundo).logros || {}); }

/** Cuántos logros tiene el mundo, si los declara. */
export function totalLogros(mundo) { return datos(mundo).total_logros || null; }

/** La etiqueta de una clave de la puntuación del mundo (o la clave tal cual). */
export function etiquetaPuntos(mundo, clave) {
  const p = (datos(mundo).puntos || {})[clave];
  return p ? texto(p) : legible(clave);
}

/** Un valor de la puntuación con texto (p. ej. «VICTORIA»). */
export function valorPuntos(mundo, valor) {
  const v = (datos(mundo).valores || {})[valor];
  return v ? texto(v) : valor;
}

function rellenar(plantilla, mundo, c, objetivo) {
  const s = String(plantilla)
    .replace('{el}', c ? clase(mundo, c, 'el') : '')
    .replace('{un}', c ? clase(mundo, c, 'un') : '')
    .replace('{objetivo}', objetivo || '');
  return s.replace(/\s+/g, ' ').replace(/\s+([),.])/g, '$1').replace(/\(\s*\)/g, '').trim();
}

/** La acción en frase: forma 'pres' («come una baya») o 'inf' («comer una baya»). */
export function accionFrase(mundo, verbo, c, objetivo, forma = 'pres') {
  const propias = datos(mundo).acciones || {};
  const propia = propias[`${verbo}:${c}`] || propias[verbo];
  const p = propia && (propia[idioma()] || propia.es);
  const plantilla = p ? p[forma] : t(`verbo.${verbo}.${forma}`);
  if (plantilla === `verbo.${verbo}.${forma}`) return rellenar(`${String(verbo).toLowerCase()} {un}`, mundo, c, objetivo);
  return contraer(rellenar(plantilla, mundo, c, objetivo));
}

/** El motivo de la acción en frase, desde su estrategia («S1:huir:seguridad») o vacío si no la tiene. */
export function motivoFrase(accion) {
  if (!accion || !accion.estrategia) return '';
  const partes = String(accion.estrategia).split(':');
  const impulso = partes[2];
  if (!impulso) return '';
  const clave = `motivo.${impulso}`;
  const m = t(clave);
  return m === clave ? t('motivo.otro', { impulso: legible(impulso) }) : m;
}

/** El nombre de un plan (estrategia) en el idioma actual. */
export function planNombre(nombre) {
  const clave = `plan.${nombre}`;
  const p = t(clave);
  return p === clave ? legible(nombre) : p;
}

/** El plan de una acción («S1:huir:seguridad» → «Huir»). */
export function planDeAccion(accion) {
  if (!accion || !accion.estrategia) return '';
  return planNombre(String(accion.estrategia).split(':')[1] || '');
}

/** «Ahora», en frase: la acción con su motivo (y si no salió, dicho). */
export function ahoraFrase(mundo, accion) {
  if (!accion) return t('vivero.sin_accion');
  let s = capital(accionFrase(mundo, accion.verbo, accion.clase, accion.objetivo, 'pres'));
  const motivo = motivoFrase(accion);
  if (motivo) s += ` ${motivo}`;
  if (accion.exito === false) s += ` ${t('ahora.sin_exito')}`;
  return s;
}

/** Una proposición en frase («El zombi es peligroso»). p: {sujeto|clase, relacion}. */
export function saberFrase(mundo, p) {
  const c = p.sujeto ?? p.clase;
  const genero = terminacion(mundo, c) === 'a' ? 'f' : 'm';
  const clave = `saber.${p.relacion}.${genero}`;
  const plantilla = t(clave) === clave ? 'saber.otra' : clave;
  return capital(contraer(t(plantilla, { el: clase(mundo, c, 'el'), relacion: legible(p.relacion).toLowerCase() })));
}

function lista(mundo, claves, forma) {
  const nombres = claves.map((c) => clase(mundo, c, forma));
  if (nombres.length <= 1) return nombres.join('');
  return `${nombres.slice(0, -1).join(', ')} ${t('frase.y')} ${nombres[nombres.length - 1]}`;
}

/** Un requisito de acción en frase («La madera sirve para hacer una mesa»). h: el hecho «aprende requisito». */
export function requisitoFrase(mundo, h) {
  const inf = accionFrase(mundo, h.verbo, h.clase, '', 'inf');
  const pres = accionFrase(mundo, h.verbo, h.clase, '', 'pres');
  const requiere = Object.keys(h.requiere || {});
  const cerca = (h.cerca || []).length ? t('saber.req.cerca', { un: lista(mundo, h.cerca, 'un') }) : '';
  const gana = Object.entries(h.efecto || {}).filter(([, n]) => Number(n) > 0).map(([c]) => c);
  let s;
  if (requiere.length) {
    const forma = t('saber.req.forma') === 'un' ? 'un' : 'el';   // es: «La madera sirve…»; en: «It takes wood…»
    s = t(requiere.length > 1 ? 'saber.req.varios' : 'saber.req.uno', { cosas: lista(mundo, requiere, forma), accion: inf, cerca });
  } else if (gana.length) {
    s = t('saber.req.efecto', { un: lista(mundo, gana, 'un'), accion: inf, pres, cerca });
  } else {
    s = t('saber.req.sabe', { accion: inf, cerca });
  }
  return capital(contraer(s));
}

/** La fuente de lo que sabe: manual, experiencia, herencia o biblioteca. */
export function fuenteDe(p) {
  if (p.fuente) return p.fuente;
  if (p.heredada) return 'herencia';
  if (p.autoridad) return 'manual';     // las vidas de la aplicación no usan biblioteca: la autoridad es el manual
  return 'experiencia';
}

/** «de hambre», «por el zombi»…: la causa de muerte en frase. */
export function causaMuerte(mundo, causa) {
  const nec = `muerte.${causa}`;
  if (t(nec) !== nec) return t(nec);
  if (tieneEtiqueta(mundo, causa)) return contraer(t('muerte.por', { el: clase(mundo, causa, 'el') }));
  return t('muerte.otra', { causa: legible(causa) });
}

/** Icono de cada tipo de hecho en el diario. */
export const ICONOS_HECHO = {
  nace: '🌱', primera_vez: '✨', aprende: '💡', duda: '🤔', refuta: '✖️', sorpresa: '❗', logro: '🏅', peligro: '⚠️',
  estrategia: '🧭', duerme: '🌙', despierta: '☀️', muere: '🕯️',
};

/** Un hecho del registro en frase (sección 5). Devuelve '' para lo que no se cuenta. */
export function hechoFrase(mundo, h) {
  switch (h.tipo) {
    case 'nace': return t('hecho.nace', { individuo: h.individuo, generacion: h.generacion, heredados: h.heredados });
    case 'primera_vez': return t('hecho.primera_vez', { accion: accionFrase(mundo, h.verbo, h.clase, '', 'pres') });
    case 'aprende': {
      const frase = h.saber === 'requisito' ? requisitoFrase(mundo, h) : saberFrase(mundo, h);
      const hip = h.saber === 'requisito' ? !h.confirmado : h.estado === 'hipotesis';
      return t(hip ? 'hecho.sospecha' : 'hecho.aprende', { frase: minuscula(frase) });
    }
    case 'duda': return t('hecho.duda', { frase: minuscula(saberFrase(mundo, h)) });
    case 'refuta': return t('hecho.refuta', { frase: minuscula(saberFrase(mundo, h)) });
    case 'peligro':
      return capital(contraer(t(h.estado === 'demostrada' ? 'hecho.peligro' : 'hecho.peligro_hipotesis', { el: clase(mundo, h.clase, 'el') })));
    case 'sorpresa': {
      if (h.origen === 'modelo') {
        return h.clase ? capital(contraer(t('hecho.sorpresa_modelo', { el: clase(mundo, h.clase, 'el') }))) : t('hecho.sorpresa_modelo_sin');
      }
      if (!h.verbo) return t('hecho.sorpresa_sin');
      return t(Number(h.rpe) >= 0 ? 'hecho.sorpresa_mejor' : 'hecho.sorpresa_peor',
        { accion: accionFrase(mundo, h.verbo, h.clase, '', 'pres') });
    }
    case 'logro': return t('hecho.logro', { nombre: logro(mundo, h.nombre) });
    case 'estrategia': return t(h.cambio === 'inicio' ? 'hecho.plan_inicio' : 'hecho.plan_fin', { plan: planNombre(h.nombre) });
    case 'duerme': return t('hecho.duerme');
    case 'despierta': return t(h.motivo === 'alarma' ? 'hecho.despierta_alarma' : h.motivo === 'descansado' ? 'hecho.despierta_descansada' : 'hecho.despierta');
    case 'muere': return t('hecho.muere', { causa: causaMuerte(mundo, h.causa), latidos: h.latidos });
    default: return '';
  }
}

/** Un hecho del cierre de la vida (lo aprendido al morir, T4b): «Al morir, ha aprendido que…». */
export function hechoFraseConCierre(mundo, h) {
  const frase = hechoFrase(mundo, h);
  return frase && h.cierre ? t('hecho.al_morir', { frase: minuscula(frase) }) : frase;
}

const BARRAS = ['vitalidad', 'alimentacion', 'energia', 'descanso'];

/**
 * Las barras del cuerpo que se enseñan en un mundo (T4b, sección 13.6): las que declara su fichero de clases en
 * «cuerpo», con su etiqueta y su ayuda; sin declaración, las cuatro con los nombres generales.
 */
export function barrasDelCuerpo(mundo) {
  const decl = datos(mundo).cuerpo;
  if (!decl) return BARRAS.map((clave) => ({ clave, etiqueta: t(`cuerpo.${clave}`), ayuda: '' }));
  return BARRAS.filter((clave) => decl[clave]).map((clave) => ({
    clave, etiqueta: texto(decl[clave].etiqueta), ayuda: decl[clave].ayuda ? texto(decl[clave].ayuda) : '',
  }));
}

/** Las clases que aparecen en un hecho (para su sprite). */
export function claseDeHecho(h) {
  if (h.clase) return h.clase;
  if (h.tipo === 'muere') return h.causa;
  return null;
}
