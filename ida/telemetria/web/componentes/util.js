// Utilidades pequeñas de la interfaz: escapar HTML, avisos y almacenamiento local seguro.

const ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

/** Texto seguro para meterlo en una plantilla HTML. */
export function esc(valor) {
  return String(valor ?? '').replace(/[&<>"']/g, (c) => ESCAPES[c]);
}

/** Un aviso breve abajo a la derecha (también lo lee un lector de pantalla: role=status). */
export function avisar(texto, ms = 4200) {
  const caja = document.getElementById('notificaciones');
  if (!caja) return;
  const el = document.createElement('div');
  el.className = 'notificacion';
  el.textContent = texto;
  caja.append(el);
  setTimeout(() => el.remove(), ms);
}

/** localStorage dentro de try/catch: en privado o sin permiso, no se recuerda y la página sigue igual. */
export const almacen = {
  leer(clave) {
    try { const v = localStorage.getItem(clave); return v == null ? null : JSON.parse(v); } catch { return null; }
  },
  guardar(clave, valor) {
    try { localStorage.setItem(clave, JSON.stringify(valor)); } catch { /* sin almacenamiento */ }
  },
};

export const ICONO_CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';
