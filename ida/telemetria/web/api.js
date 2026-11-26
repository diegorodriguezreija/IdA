// Cliente de la API v1 (O14). Las respuestas de error traen {error: {codigo, mensaje, campo?}}.

export class ErrorApi extends Error {
  constructor(estado, codigo, mensaje, campo) {
    super(mensaje || codigo);
    this.estado = estado;
    this.codigo = codigo;
    this.campo = campo;
  }
}

async function pedir(metodo, ruta, cuerpo) {
  let resp;
  try {
    resp = await fetch(`/api/v1/${ruta}`, {
      method: metodo,
      headers: cuerpo !== undefined ? { 'Content-Type': 'application/json' } : {},
      body: cuerpo !== undefined ? JSON.stringify(cuerpo) : undefined,
    });
  } catch {
    throw new ErrorApi(0, 'red', '');
  }
  let datos = null;
  try { datos = await resp.json(); } catch { /* sin cuerpo */ }
  if (!resp.ok) {
    const e = (datos && datos.error) || {};
    throw new ErrorApi(resp.status, e.codigo || 'error_interno', e.mensaje || '', e.campo);
  }
  return datos;
}

export const api = {
  mundos: () => pedir('GET', 'mundos'),
  presets: () => pedir('GET', 'presets'),
  instalar: (mundo) => pedir('POST', `mundos/${encodeURIComponent(mundo)}/instalar`, {}),
  lanzar: (cuerpo) => pedir('POST', 'vidas', cuerpo),
  vidaActual: () => pedir('GET', 'vidas/actual'),
  ritmo: (ritmo) => pedir('POST', 'vidas/actual/ritmo', { ritmo }),
  paso: () => pedir('POST', 'vidas/actual/paso', {}),
  parar: () => pedir('POST', 'vidas/actual/parar', {}),
  // T4b: compañero y colección (sección 13)
  companeros: () => pedir('GET', 'companeros'),
  companero: (mundo) => pedir('GET', `companeros/${encodeURIComponent(mundo)}`),
  guardar: (mundo, nombre) => pedir('POST', `companeros/${encodeURIComponent(mundo)}/guardar`, nombre ? { nombre } : {}),
  archivar: (mundo) => pedir('POST', `companeros/${encodeURIComponent(mundo)}/archivar`, {}),
  coleccion: (mundo) => pedir('GET', mundo ? `coleccion?mundo=${encodeURIComponent(mundo)}` : 'coleccion'),
  elemento: (id) => pedir('GET', `coleccion/${encodeURIComponent(id)}`),
  importar: (ficha) => pedir('POST', 'coleccion/importar', { ficha }),
  renombrar: (id, nombre) => pedir('POST', `coleccion/${encodeURIComponent(id)}/renombrar`, { nombre }),
  adoptar: (id) => pedir('POST', `coleccion/${encodeURIComponent(id)}/adoptar`, {}),
  pedirBorrado: (id) => pedir('POST', `coleccion/${encodeURIComponent(id)}/borrar`, {}),
  confirmarBorrado: (id, testigo) => pedir('POST', `coleccion/${encodeURIComponent(id)}/borrar/confirmar`, { testigo }),
};

/** Enlaces de descarga de fichas v1 (GET con Content-Disposition). */
export const descargas = {
  elemento: (id) => `/api/v1/coleccion/${encodeURIComponent(id)}/exportar`,
  companero: (mundo) => `/api/v1/companeros/${encodeURIComponent(mundo)}/exportar`,
};

/** EventSource con oyentes por evento; devuelve una función para cerrarlo. */
export function escuchar(ruta, oyentes) {
  const fuente = new EventSource(`/api/v1/${ruta}`);
  for (const [evento, fn] of Object.entries(oyentes)) {
    if (evento === 'error' || evento === 'open') fuente.addEventListener(evento, fn);
    else fuente.addEventListener(evento, (ev) => fn(JSON.parse(ev.data)));
  }
  return () => fuente.close();
}
