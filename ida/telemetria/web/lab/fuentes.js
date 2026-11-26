// Fuentes del reproductor del Laboratorio (T5a, O7): la vida en directo (los últimos latidos que guarda el servidor),
// una grabación de la lista (el servidor la indexa y da cada latido) o un fichero cargado en el navegador (.jsonl.gz,
// .jsonl o un registro .json). Las tres dan lo mismo:
//   indice   [{n, vida, generacion, latido, cierre?, hechos, guillotina, sistema, candidatos, dormido, nivel}]
//   medias   {tiempos_medios, fases_medias, registros, guillotinas}: medias por Componente y por fase del latido
//   registro(pos) → Promise<registro del latido v1>, con su escena vigente (la escena solo viaja cuando cambia)

import { api } from '../api.js';

const CACHE = 40;                 // registros enteros que se guardan en el navegador (los últimos vistos)
const HECHOS_INDICE = new Set(['nace', 'primera_vez', 'aprende', 'logro', 'peligro', 'sorpresa', 'duda', 'refuta', 'muere', 'duerme', 'despierta']);

class Cache {
  constructor() { this.mapa = new Map(); }
  async dar(clave, pedir) {
    if (this.mapa.has(clave)) {
      const v = this.mapa.get(clave);
      this.mapa.delete(clave);
      this.mapa.set(clave, v);
      return v;
    }
    const v = await pedir();
    this.mapa.set(clave, v);
    while (this.mapa.size > CACHE) this.mapa.delete(this.mapa.keys().next().value);
    return v;
  }
}

/** La entrada de índice de un registro (como laboratorio.entrada_indice en el servidor). */
export function entradaIndice(r, n) {
  const e = {
    n, vida: r.vida, generacion: r.generacion, latido: r.latido,
    hechos: (r.hechos || []).filter((h) => h && HECHOS_INDICE.has(h.tipo)),
    guillotina: Boolean(r.ritmo && r.ritmo.guillotina), sistema: (r.accion && r.accion.sistema) || '',
    candidatos: ((r.tribunal && r.tribunal.candidatos) || []).length, dormido: Boolean(r.cuerpo && r.cuerpo.dormido), nivel: r.nivel,
  };
  if (r.cierre) e.cierre = true;
  return e;
}

/** Medias por clave de los tiempos de cada Componente y de cada fase (como laboratorio.Medias). */
class Medias {
  constructor() { this.tiempos = {}; this.fases = {}; this.registros = 0; this.guillotinas = 0; }
  sumar(r) {
    for (const [k, v] of Object.entries(r.tiempos_ms || {})) {
      const a = this.tiempos[k] || (this.tiempos[k] = [0, 0]);
      a[0] += Number(v) || 0; a[1] += 1;
    }
    const porFase = {};
    for (const f of r.fases || []) porFase[f[0]] = (porFase[f[0]] || 0) + (Number(f[2]) - Number(f[1]));
    for (const [k, v] of Object.entries(porFase)) {
      const a = this.fases[k] || (this.fases[k] = [0, 0]);
      a[0] += v; a[1] += 1;
    }
    this.registros += 1;
    if (r.ritmo && r.ritmo.guillotina) this.guillotinas += 1;
  }
  resumen() {
    const medias = (d) => Object.fromEntries(Object.entries(d).filter(([, [, n]]) => n > 0)
      .map(([k, [s, n]]) => [k, { media: s / n, latidos: n }]));
    return { tiempos_medios: medias(this.tiempos), fases_medias: medias(this.fases), registros: this.registros, guillotinas: this.guillotinas };
  }
}

/** La vida en curso: el índice de lo que guarda el servidor y, al pedirlo, cada registro entero. */
export class FuenteDirecto {
  constructor() {
    this.tipo = 'directo';
    this.indice = [];
    this.siguiente = 0;
    this.maximo = 0;
    this.lanzamiento = null;
    this.mundo = null;
    this.medias = {};
    this.cache = new Cache();
  }

  get nombre() { return this.mundo || ''; }

  async cargar() {
    const d = await api.directo(0);
    this.aplicar(d, true);
    return this;
  }

  aplicar(d, entero) {
    if (entero || d.lanzamiento !== this.lanzamiento) {
      this.indice = [];
      this.cache = new Cache();
    }
    this.lanzamiento = d.lanzamiento;
    this.mundo = d.mundo;
    this.maximo = d.maximo;
    this.siguiente = d.siguiente;
    this.medias = { tiempos_medios: d.tiempos_medios, fases_medias: d.fases_medias, registros: d.registros, guillotinas: d.guillotinas };
    const vistos = this.indice.length ? this.indice[this.indice.length - 1].n : -1;
    for (const e of d.indice) if (e.n > vistos) this.indice.push(e);
    const quitar = this.indice.findIndex((e) => e.n >= d.primero);
    if (quitar > 0) this.indice.splice(0, quitar);
    else if (quitar < 0) this.indice = [];
  }

  /** Pide lo nuevo. Devuelve cuántas posiciones se perdieron por el principio (el directo guarda los últimos N). */
  async refrescar() {
    const antes = this.indice.length ? this.indice[0].n : null;
    const lanz = this.lanzamiento;
    const d = await api.directo(this.siguiente);
    this.aplicar(d, d.lanzamiento !== lanz);
    if (d.lanzamiento !== lanz) return { nueva: true, perdidas: 0 };
    const ahora = this.indice.length ? this.indice[0].n : null;
    return { nueva: false, perdidas: antes == null || ahora == null ? 0 : Math.max(0, ahora - antes) };
  }

  registro(pos) {
    const e = this.indice[pos];
    if (!e) return Promise.reject(new Error('fuera'));
    return this.cache.dar(`${this.lanzamiento}:${e.n}`, async () => (await api.latidoDirecto(e.n)).registro);
  }
}

/** Una grabación de <datos>/grabaciones, indexada por el servidor. */
export class FuenteGrabacion {
  constructor(id) {
    this.tipo = 'grabacion';
    this.id = id;
    this.indice = [];
    this.cache = new Cache();
  }

  get nombre() { return this.id; }

  async cargar() {
    const d = await api.indiceGrabacion(this.id);
    this.cabecera = d.cabecera;
    this.grabacion = d.grabacion;
    this.truncada = d.truncada;
    this.mundo = d.cabecera.mundo;
    this.indice = d.indice;
    this.medias = { tiempos_medios: d.tiempos_medios, fases_medias: d.fases_medias, registros: d.registros, guillotinas: d.guillotinas };
    return this;
  }

  registro(pos) {
    const e = this.indice[pos];
    if (!e) return Promise.reject(new Error('fuera'));
    return this.cache.dar(e.n, async () => (await api.latidoGrabacion(this.id, e.n)).registro);
  }
}

/** Un fichero elegido en el navegador. Las líneas se guardan como texto y se leen al pedirlas. */
export class FuenteFichero {
  constructor(fichero) {
    this.tipo = 'fichero';
    this.fichero = fichero;
    this.indice = [];
    this.lineas = [];
    this.escenaDe = [];
    this.cache = new Cache();
  }

  get nombre() { return this.fichero.name; }

  async texto() {
    const f = this.fichero;
    if (f.name.endsWith('.gz')) {
      if (typeof DecompressionStream === 'undefined') throw new Error('sin_gzip');
      return new Response(f.stream().pipeThrough(new DecompressionStream('gzip'))).text();
    }
    return f.text();
  }

  async cargar() {
    const texto = await this.texto();
    const medias = new Medias();
    let lineas = texto.split('\n').filter((l) => l.trim());
    if (lineas.length === 1 && lineas[0].trim().startsWith('{') && !lineas[0].includes('"cabecera"')) {
      lineas = [JSON.stringify(JSON.parse(texto))];   // un registro .json (con saltos de línea)
    }
    let escena = -1;
    let vida = null;
    for (const linea of lineas) {
      const d = JSON.parse(linea);
      if (d.tipo === 'cabecera') {
        if (this.cabecera) continue;
        this.cabecera = d;
        continue;
      }
      if (d.v !== 1) throw new Error('no_es_registro');
      const i = this.lineas.length;
      if (d.vida !== vida) { vida = d.vida; escena = -1; }
      if (d.escena) escena = i;
      this.lineas.push(linea);
      this.escenaDe.push(escena);
      this.indice.push(entradaIndice(d, i));
      medias.sumar(d);
    }
    if (!this.lineas.length) throw new Error('vacio');
    this.cabecera = this.cabecera || {};
    this.mundo = this.cabecera.mundo || JSON.parse(this.lineas[0]).mundo;
    this.medias = medias.resumen();
    return this;
  }

  registro(pos) {
    const e = this.indice[pos];
    if (!e) return Promise.reject(new Error('fuera'));
    return this.cache.dar(e.n, async () => {
      const r = JSON.parse(this.lineas[e.n]);
      const k = this.escenaDe[e.n];
      if (!r.escena && k >= 0) r.escena = JSON.parse(this.lineas[k]).escena;
      return r;
    });
  }
}
