/** Utilidades de formato (es-ES). Sin dependencias del DOM. */

const intFmt = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 0 });
const eurFmt = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });
const dateFmt = new Intl.DateTimeFormat('es-ES', { dateStyle: 'medium', timeStyle: 'short' });
const dayFmt = new Intl.DateTimeFormat('es-ES', { dateStyle: 'medium' });

/** @param {number|null|undefined} n */
export function fmtInt(n) {
  return Number.isFinite(n) ? intFmt.format(n) : '—';
}

/** @param {number|null|undefined} n @param {number} [decimals] */
export function fmtNum(n, decimals = 2) {
  return Number.isFinite(n)
    ? new Intl.NumberFormat('es-ES', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(n)
    : '—';
}

/** @param {number|null|undefined} n */
export function fmtEur(n) {
  return Number.isFinite(n) ? eurFmt.format(n) : '—';
}

/** Euros abreviados (k€ / M€) para tarjetas pequeñas. */
export function fmtEurShort(n) {
  if (!Number.isFinite(n)) return '—';
  if (Math.abs(n) >= 1e6) return `${fmtNum(n / 1e6, 2)} M€`;
  if (Math.abs(n) >= 1e3) return `${fmtNum(n / 1e3, 0)} k€`;
  return fmtEur(n);
}

/** @param {number|null|undefined} n */
export function fmtPct(n, decimals = 0) {
  return Number.isFinite(n) ? `${fmtNum(n * 100, decimals)} %` : '—';
}

/** @param {string} iso */
export function fmtDateTime(iso) {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '—' : dateFmt.format(d);
}

/** @param {string} iso */
export function fmtDay(iso) {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '—' : dayFmt.format(d);
}

/** Fecha local YYYY-MM-DD para nombres de fichero. */
export function isoDay(date = new Date()) {
  const p = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${p(date.getMonth() + 1)}-${p(date.getDate())}`;
}

/** Escapa texto para insertarlo en HTML. */
export function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}

/** Limita un número al rango [min, max]. */
export function clamp(n, min, max) {
  return Math.min(max, Math.max(min, n));
}
