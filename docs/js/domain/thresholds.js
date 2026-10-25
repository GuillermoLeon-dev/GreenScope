/** Clasificación pura por umbrales (sin DOM). El modelo entrega scores; el técnico fija los cortes. */
import { THRESHOLD_GAP } from '../config.js';
import { clamp } from '../utils/format.js';

/**
 * @typedef {{critical:number, review:number, min_proposal_priority:number}} Thresholds
 * @typedef {'critical'|'review'|'ok'} CellClass
 */

/**
 * @param {number} score deficit_score en [0,1]
 * @param {Thresholds} t
 * @returns {CellClass}
 */
export function classify(score, t) {
  if (score >= t.critical) return 'critical';
  if (score >= t.review) return 'review';
  return 'ok';
}

const round2 = (n) => Math.round(n * 100) / 100;

/**
 * Aplica un cambio a un umbral garantizando review < critical.
 * El umbral que se mueve nunca cruza al otro.
 * @param {Thresholds} current
 * @param {keyof Thresholds} key
 * @param {number} value
 * @returns {Thresholds}
 */
export function withThreshold(current, key, value) {
  const v = round2(value);
  if (key === 'critical') return { ...current, critical: clamp(v, round2(current.review + THRESHOLD_GAP), 1) };
  if (key === 'review') return { ...current, review: clamp(v, 0, round2(current.critical - THRESHOLD_GAP)) };
  return { ...current, [key]: clamp(v, 0, 1) };
}

/**
 * Cuenta celdas y población residente por clase.
 * @param {Array<{deficit_score:number, population:number}>} cells
 * @param {Thresholds} t
 */
export function summarizeCells(cells, t) {
  const out = {
    critical: { cells: 0, population: 0 },
    review: { cells: 0, population: 0 },
    ok: { cells: 0, population: 0 },
  };
  for (const c of cells) {
    const bucket = out[classify(c.deficit_score, t)];
    bucket.cells += 1;
    bucket.population += c.population || 0;
  }
  return out;
}

/** @param {{priority_score:number}} proposal @param {Thresholds} t */
export function isProposalAboveThreshold(proposal, t) {
  return proposal.priority_score >= t.min_proposal_priority;
}
