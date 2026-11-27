// Series de una vida (T5b) para un fichero cargado en el navegador: la misma forma que ida/telemetria/analisis.py
// (Series.resultado), que es la que da el servidor para el directo y las grabaciones:
//   {mundo, registros, niveles, columnas: {nombre: [valor por registro]}, hechos: [{n, vida, latido, tipo, ...}],
//    saber: [{clave, tipo, sujeto|verbo, relacion|clase, fuente, historia: [[n, latido, estado, confianza, fuente, vida]],
//             eventos: [{n, vida, latido, tipo, estado, confianza}]}], vidas: [...]}
// Una diferencia: la Score de la colección (ida/historico.py, calcular_fitness) se calcula en el servidor; con un fichero
// cargado la columna «score» va vacía y Análisis enseña la puntuación del mundo.

const HECHOS_SERIES = new Set(['nace', 'primera_vez', 'aprende', 'logro', 'peligro', 'sorpresa', 'duda', 'refuta', 'muere', 'duerme', 'despierta']);
const VITALES = ['vitalidad', 'alimentacion', 'energia', 'descanso'];
const QUIMICA = ['dopamina', 'placer', 'estres'];
const INDICADORES = ['peligro', 'tension', 'calma'];
const RESUMEN = ['proposiciones', 'demostradas', 'hipotesis', 'refutadas', 'heredadas', 'requisitos', 'requisitos_confirmados', 'aciertos', 'sorpresas'];

function num(x) {
  if (typeof x === 'boolean') return Number(x);
  return typeof x === 'number' && Number.isFinite(x) ? Math.round(x * 1e4) / 1e4 : null;
}

export function fuenteSaber(s) {
  if (s.heredada) return 'herencia';
  if (s.autoridad) return 'manual';
  return 'experiencia';
}

export const claveProposicion = (sujeto, relacion) => `p|${sujeto}|${relacion}`;
export const claveRequisito = (verbo, clase) => `r|${verbo}|${clase}`;

export class Series {
  constructor() {
    this.columnas = {};
    this.longitud = 0;
    this.mundo = null;
    this.niveles = {};
    this.hechos = [];
    this.saber = new Map();
    this.vidas = [];
    this.previo = null;
  }

  poner(fila) {
    for (const [nombre, valor] of Object.entries(fila)) {
      let col = this.columnas[nombre];
      if (!col) col = this.columnas[nombre] = new Array(this.longitud).fill(null);
      col.push(valor);
    }
    this.longitud += 1;
    for (const col of Object.values(this.columnas)) if (col.length < this.longitud) col.push(null);
  }

  anadir(r, n) {
    this.mundo = this.mundo || String(r.mundo || '');
    this.niveles[r.nivel || ''] = (this.niveles[r.nivel || ''] || 0) + 1;
    const cuerpo = r.cuerpo || {}; const quimica = r.quimica || {}; const afecto = r.afecto || {};
    const ritmo = r.ritmo || {}; const score = r.score || {};
    const resumen = r.resumen_saber || r.memoria || {};
    const amplitud = ritmo.amplitud || [null, null]; const potencia = ritmo.potencia || [null, null];
    const hechos = (r.hechos || []).filter((h) => h && typeof h === 'object');
    const rpe = hechos.filter((h) => h.tipo === 'sorpresa' && typeof h.rpe === 'number').map((h) => h.rpe);
    const fila = {
      n, vida: r.vida, generacion: r.generacion, latido: r.latido, cierre: Boolean(r.cierre), dormido: Boolean(cuerpo.dormido),
      'afecto/valencia': num(afecto.valencia), 'afecto/estado': afecto.estado ?? null,
      score: null, logros: (score.logros || []).length,
      'ritmo/amplitud': num(amplitud[0]), 'ritmo/amplitud_max': num(amplitud[1]),
      'ritmo/potencia': num(potencia[0]), 'ritmo/potencia_max': num(potencia[1]),
      'ritmo/guillotina': Boolean(ritmo.guillotina), 'ritmo/ms': num(ritmo.ms),
      rpe: rpe.length ? Math.round(rpe.reduce((a, b) => a + b, 0) * 1000) / 1000 : null,
      sistema: String((r.accion && r.accion.sistema) || ''),
    };
    for (const k of VITALES) fila[`cuerpo/${k}`] = num(cuerpo[k]);
    for (const k of QUIMICA) fila[`quimica/${k}`] = num(quimica[k]);
    for (const k of INDICADORES) fila[`indicadores/${k}`] = num((afecto.indicadores || {})[k]);
    for (const k of RESUMEN) if (k in resumen) fila[`saber/${k}`] = num(resumen[k]);
    for (const nec of r.necesidades || []) if (nec && nec.nombre) fila[`necesidad/${nec.nombre}`] = num(nec.deficit);
    if (score.puntuacion && typeof score.puntuacion === 'object') {
      for (const [k, v] of Object.entries(score.puntuacion)) if (typeof v === 'number') fila[`puntuacion/${k}`] = num(v);
    }
    this.poner(fila);
    this.anadirHechos(r, n, hechos);
    this.anadirSaber(r, n, hechos);
    this.anadirVida(r, n, hechos);
    this.previo = r;
  }

  anadirHechos(r, n, hechos) {
    const base = { n, vida: r.vida, latido: r.latido, ...(r.cierre ? { cierre: true } : {}) };
    for (const h of hechos) if (HECHOS_SERIES.has(h.tipo)) this.hechos.push({ ...base, ...h });
    const p = this.previo;
    if (p && p.vida === r.vida && !r.cierre) {
      const antes = num((p.cuerpo || {}).vitalidad); const ahora = num((r.cuerpo || {}).vitalidad);
      if (antes != null && ahora != null && ahora < antes) this.hechos.push({ ...base, tipo: 'dano', perdida: Math.round((antes - ahora) * 1000) / 1000, vitalidad: ahora });
    }
  }

  paso(p, n, r, estado, confianza, fuente) {
    const h = p.historia;
    const u = h[h.length - 1];
    if (u && u[2] === estado && u[3] === confianza && u[4] === fuente && u[5] === r.vida) return;
    h.push([n, r.latido, estado, confianza, fuente, r.vida]);
  }

  anadirSaber(r, n, hechos) {
    if (Array.isArray(r.saber)) {
      const vistos = new Set();
      for (const s of r.saber) {
        const clave = claveProposicion(s.sujeto, s.relacion);
        vistos.add(clave);
        if (!this.saber.has(clave)) this.saber.set(clave, { tipo: 'proposicion', sujeto: s.sujeto, relacion: s.relacion, historia: [], eventos: [] });
        const p = this.saber.get(clave);
        p.fuente = fuenteSaber(s);
        this.paso(p, n, r, String(s.estado), num(s.confianza), p.fuente);
      }
      for (const [clave, p] of this.saber) {
        const u = p.historia[p.historia.length - 1];
        if (p.tipo === 'proposicion' && !vistos.has(clave) && u && u[2] !== 'fuera' && u[2] !== 'olvidada') {
          this.paso(p, n, r, r.nivel === 'completo' ? 'olvidada' : 'fuera', null, p.fuente);
        }
      }
    }
    if (Array.isArray(r.requisitos)) {
      for (const q of r.requisitos) {
        const clave = claveRequisito(q.verbo, q.clase);
        if (!this.saber.has(clave)) this.saber.set(clave, { tipo: 'requisito', verbo: q.verbo, clase: q.clase, historia: [], eventos: [] });
        const p = this.saber.get(clave);
        Object.assign(p, { fuente: String(q.fuente || ''), requiere: q.requiere, cerca: q.cerca, efecto: q.efecto });
        this.paso(p, n, r, q.confirmado ? 'confirmado' : 'sin_confirmar', num(q.confianza), p.fuente);
      }
    }
    for (const h of hechos) {
      if (!['aprende', 'duda', 'refuta'].includes(h.tipo)) continue;
      const req = h.saber === 'requisito';
      const clave = req ? claveRequisito(h.verbo, h.clase) : claveProposicion(h.clase, h.relacion);
      if (!this.saber.has(clave)) {
        this.saber.set(clave, req ? { tipo: 'requisito', verbo: h.verbo, clase: h.clase, historia: [], eventos: [] }
          : { tipo: 'proposicion', sujeto: h.clase, relacion: h.relacion, historia: [], eventos: [] });
      }
      const p = this.saber.get(clave);
      if (h.fuente && !p.fuente) p.fuente = h.fuente;
      let estado = h.estado || { duda: 'hipotesis', refuta: 'refutada' }[h.tipo];
      if (req) estado = h.confirmado ? 'confirmado' : 'sin_confirmar';
      p.eventos.push({ n, vida: r.vida, latido: r.latido, tipo: h.tipo, estado, confianza: num(h.confianza), ...(r.cierre ? { cierre: true } : {}) });
      if (!Array.isArray(req ? r.requisitos : r.saber)) this.paso(p, n, r, String(estado), num(h.confianza), p.fuente);
    }
  }

  anadirVida(r, n, hechos) {
    let v = this.vidas[this.vidas.length - 1];
    if (!v || v.vida !== r.vida) {
      v = { vida: r.vida, individuo: r.individuo, generacion: r.generacion, desde: n, latido_inicial: r.latido, nace: null, muere: null,
        cierre: null, resumen_inicial: r.resumen_saber || null, aprendidas: 0, sorpresas: 0, danos: 0 };
      this.vidas.push(v);
    }
    Object.assign(v, { hasta: n, latido_final: r.latido, resumen_final: r.resumen_saber || null, logros: [...((r.score || {}).logros || [])],
      puntuacion: (r.score || {}).puntuacion, score: null, arquetipo: r.arquetipo });
    for (const h of hechos) {
      if (h.tipo === 'nace') v.nace = h;
      else if (h.tipo === 'muere') v.muere = { ...h, n };
      else if (h.tipo === 'aprende' && !r.cierre) v.aprendidas += 1;
      else if (h.tipo === 'sorpresa') v.sorpresas += 1;
    }
    const u = this.hechos[this.hechos.length - 1];
    if (u && u.tipo === 'dano' && u.n === n) v.danos += 1;
    if (r.cierre) v.cierre = { n, latido: r.latido, hechos, aprendizaje: [...((r.experiencia || {}).aprendizaje || [])] };
  }

  resultado() {
    const saber = [...this.saber].filter(([, p]) => p.historia.length || p.eventos.length).map(([clave, p]) => ({ ...p, clave }));
    return { mundo: this.mundo, registros: this.longitud, niveles: this.niveles, columnas: this.columnas, hechos: this.hechos, saber, vidas: this.vidas };
  }
}
