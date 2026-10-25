/** Tarjetas de KPIs, recalculadas con umbrales y decisiones. */
import { watch } from '../state.js';
import { computeKpis } from '../domain/kpis.js';
import { fmtInt, fmtEurShort } from '../utils/format.js';

function card(cls, value, label, sub) {
  return `<div class="kpi ${cls}"><div class="kpi-value">${value}</div><div class="kpi-label">${label}</div><div class="kpi-sub">${sub}</div></div>`;
}

/**
 * @param {HTMLElement} root
 * @param {ReturnType<import('../state.js').createStore>} store
 * @param {{cells:Object[], proposals:Object[]}} ctx
 */
export function initKpis(root, store, { cells, proposals }) {
  root.innerHTML = '<section class="section"><h2>Indicadores</h2><div class="kpi-grid" id="kpi-grid" aria-live="polite"></div></section>';
  const grid = root.querySelector('#kpi-grid');

  watch(store, ['thresholds', 'decisionIndex'], ({ thresholds, decisionIndex }) => {
    const k = computeKpis(cells, proposals, thresholds, decisionIndex);
    grid.innerHTML = [
      card('k-critical', fmtInt(k.critical), 'Celdas críticas', `de ${fmtInt(k.totalCells)} celdas`),
      card('k-review', fmtInt(k.review), 'Celdas a revisar', 'entre ambos umbrales'),
      card('k-critical', fmtInt(k.affectedPopulation), 'Población afectada', 'residentes en celdas críticas'),
      card('k-blue', fmtInt(k.proposalsAbove), 'Propuestas sobre umbral', `de ${fmtInt(k.proposalsTotal)} · ${fmtInt(k.pending)} pendientes`),
      card('k-blue', `${fmtInt(k.proposedArea)} m²`, 'Superficie propuesta', 'propuestas sobre umbral'),
      card('k-ok', fmtEurShort(k.approvedCost), 'Coste de aprobadas', `${fmtInt(k.approvedCount)} propuestas (incl. ajustadas)`),
      card('k-ok', fmtInt(k.approvedServed), 'Población servida', 'por las aprobadas'),
    ].join('');
  });
}
