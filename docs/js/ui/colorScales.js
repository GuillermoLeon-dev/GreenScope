/** Escalas de color de capas: expresiones MapLibre y degradados CSS (compartido por mapa y leyenda). */
import { LAYERS, SEQUENTIAL_PALETTE, CLASS_META, DECISION_META } from '../config.js';

/** Percentil sobre un array ordenado. */
function quantile(sorted, q) {
  if (!sorted.length) return 0;
  const pos = (sorted.length - 1) * q;
  const lo = Math.floor(pos);
  const hi = Math.ceil(pos);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
}

/**
 * Dominio [min, max] de cada capa continua.
 * @param {Array<Object>} cellProps
 * @returns {Record<string, [number, number]>}
 */
export function computeDomains(cellProps) {
  const domains = {};
  for (const layer of LAYERS) {
    if (layer.key === 'classification') continue;
    if (layer.domain) { domains[layer.key] = layer.domain; continue; }
    const values = cellProps.map((c) => c[layer.key]).filter(Number.isFinite).sort((a, b) => a - b);
    domains[layer.key] = [quantile(values, 0.02), quantile(values, 0.98)];
  }
  return domains;
}

/** @param {{reverse?:boolean}} layer */
export function rampFor(layer) {
  return layer.reverse ? [...SEQUENTIAL_PALETTE].reverse() : [...SEQUENTIAL_PALETTE];
}

/** Degradado CSS lineal para la leyenda. */
export function cssGradient(layer) {
  return `linear-gradient(90deg, ${rampFor(layer).join(', ')})`;
}

/** Expresión de color de relleno para el hexágono según la capa activa. */
export function fillColorExpression(layerKey, thresholds, domains) {
  if (layerKey === 'classification') {
    return ['case',
      ['>=', ['get', 'deficit_score'], thresholds.critical], CLASS_META.critical.color,
      ['>=', ['get', 'deficit_score'], thresholds.review], CLASS_META.review.color,
      CLASS_META.ok.color];
  }
  const layer = LAYERS.find((l) => l.key === layerKey);
  const [a, b0] = domains[layerKey];
  const b = b0 > a ? b0 : a + 1e-6;
  const colors = rampFor(layer);
  const stops = colors.flatMap((c, i) => [a + ((b - a) * i) / (colors.length - 1), c]);
  return ['interpolate', ['linear'], ['coalesce', ['get', layerKey], a], ...stops];
}

/** Color de propuestas según el estado de decisión (pendiente por defecto). */
export function proposalColorExpression(decisionIndex) {
  const pairs = [];
  for (const [id, rec] of decisionIndex) {
    if (rec.decision !== 'pending') pairs.push(id, DECISION_META[rec.decision].color);
  }
  return pairs.length
    ? ['match', ['get', 'id'], ...pairs, DECISION_META.pending.color]
    : DECISION_META.pending.color;
}
