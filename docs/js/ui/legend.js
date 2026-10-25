/** Leyenda del mapa según la capa activa. */
import { LAYERS, CLASS_META, DECISION_META } from '../config.js';
import { watch } from '../state.js';
import { cssGradient } from './colorScales.js';
import { fmtNum } from '../utils/format.js';

function classificationBlock(t) {
  const rows = [
    ['critical', `Crítico · déficit ≥ ${fmtNum(t.critical, 2)}`],
    ['review', `Revisar · ${fmtNum(t.review, 2)} – ${fmtNum(t.critical, 2)}`],
    ['ok', `Sin déficit · < ${fmtNum(t.review, 2)}`],
  ];
  return `<div class="legend-title">Clasificación por umbrales</div>
    <ul class="legend-items">${rows.map(([k, text]) => `<li><span class="swatch" style="background:${CLASS_META[k].color}"></span>${text}</li>`).join('')}</ul>`;
}

function continuousBlock(layer, domain) {
  const [a, b] = domain;
  const hint = layer.reverse ? 'Valores bajos = más déficit' : 'Valores altos = más presión';
  return `<div class="legend-title">${layer.label}</div>
    <div class="gradient-bar" style="background:${cssGradient(layer)}"></div>
    <div class="gradient-labels"><span>${fmtNum(a, layer.decimals)} ${layer.unit}</span><span>${fmtNum(b, layer.decimals)} ${layer.unit}</span></div>
    <div class="muted">${hint}</div>`;
}

function extrasBlock(state) {
  const items = [];
  if (state.showGreen) items.push('<li><span class="swatch" style="background:rgba(0,168,142,.35);border-color:#00A88E"></span>Zona verde existente</li>');
  if (state.showProposals) {
    for (const k of ['pending', 'approved', 'adjusted', 'rejected']) {
      items.push(`<li><span class="swatch swatch-outline" style="border-color:${DECISION_META[k].color}"></span>Propuesta ${DECISION_META[k].label.toLowerCase()}</li>`);
    }
  }
  return items.length ? `<div class="legend-sep"></div><ul class="legend-items cols">${items.join('')}</ul>` : '';
}

/**
 * @param {HTMLElement} root @param {ReturnType<import('../state.js').createStore>} store
 * @param {Record<string,[number,number]>} domains
 */
export function initLegend(root, store, domains) {
  root.setAttribute('aria-label', 'Leyenda del mapa');
  watch(store, ['layer', 'thresholds', 'showGreen', 'showProposals'], (state) => {
    const layer = LAYERS.find((l) => l.key === state.layer);
    const main = layer.key === 'classification' ? classificationBlock(state.thresholds) : continuousBlock(layer, domains[layer.key]);
    root.innerHTML = main + extrasBlock(state);
  });
}
