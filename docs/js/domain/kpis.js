/** Cálculo puro de KPIs a partir de umbrales y decisiones. */
import { classify, isProposalAboveThreshold } from './thresholds.js';
import { statusOf, isAccepted, effectiveArea, effectiveCost } from './decisions.js';

/**
 * @param {Array<Object>} cells propiedades de celdas
 * @param {Array<Object>} proposals propiedades de propuestas
 * @param {import('./thresholds.js').Thresholds} t
 * @param {Map<string, import('./decisions.js').DecisionRecord>} decisionIndex
 */
export function computeKpis(cells, proposals, t, decisionIndex) {
  let critical = 0;
  let review = 0;
  let affectedPopulation = 0;
  for (const c of cells) {
    const cls = classify(c.deficit_score, t);
    if (cls === 'critical') { critical += 1; affectedPopulation += c.population || 0; }
    else if (cls === 'review') review += 1;
  }

  const above = proposals.filter((p) => isProposalAboveThreshold(p, t));
  const accepted = above.filter((p) => isAccepted(statusOf(decisionIndex, p.id)));
  const pending = above.filter((p) => statusOf(decisionIndex, p.id) === 'pending');

  return {
    totalCells: cells.length,
    critical,
    review,
    affectedPopulation,
    proposalsAbove: above.length,
    proposalsTotal: proposals.length,
    pending: pending.length,
    proposedArea: above.reduce((s, p) => s + effectiveArea(p, decisionIndex.get(p.id)), 0),
    approvedCount: accepted.length,
    approvedCost: accepted.reduce((s, p) => s + effectiveCost(p, decisionIndex.get(p.id)), 0),
    approvedServed: accepted.reduce((s, p) => s + (p.served_population || 0), 0),
  };
}
