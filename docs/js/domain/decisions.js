/** Reglas puras de decisión sobre propuestas (contrato de datos, sección 7). */

export const DECISION_VALUES = ['pending', 'approved', 'rejected', 'adjusted'];

/**
 * @typedef {Object} DecisionRecord
 * @property {string} proposal_id
 * @property {'pending'|'approved'|'rejected'|'adjusted'} decision
 * @property {string} technician
 * @property {string} comment
 * @property {number|null} adjusted_area_m2
 * @property {string} timestamp ISO-8601
 * @property {string} model_version
 * @property {{critical:number, review:number, min_proposal_priority:number}} thresholds
 */

/**
 * Crea un registro con snapshot de umbrales y versión del modelo.
 * @returns {DecisionRecord}
 */
export function buildRecord({ proposalId, decision, technician, comment = '', adjustedArea = null, thresholds, modelVersion, now = new Date() }) {
  return {
    proposal_id: proposalId,
    decision,
    technician: technician.trim(),
    comment: comment.trim(),
    adjusted_area_m2: decision === 'adjusted' ? adjustedArea : null,
    timestamp: now.toISOString(),
    model_version: modelVersion,
    thresholds: { ...thresholds },
  };
}

/**
 * Último registro por propuesta (la lista es un log de auditoría ordenado por inserción).
 * @param {DecisionRecord[]} records
 * @returns {Map<string, DecisionRecord>}
 */
export function latestByProposal(records) {
  const map = new Map();
  for (const r of records) map.set(r.proposal_id, r);
  return map;
}

/** @param {Map<string, DecisionRecord>} index @param {string} id */
export function statusOf(index, id) {
  return index.get(id)?.decision ?? 'pending';
}

/** Aprobada o ajustada cuenta como aceptada por el técnico. */
export function isAccepted(status) {
  return status === 'approved' || status === 'adjusted';
}

/** Superficie efectiva: la ajustada si existe. */
export function effectiveArea(proposal, record) {
  return record?.decision === 'adjusted' && record.adjusted_area_m2 > 0 ? record.adjusted_area_m2 : proposal.area_m2;
}

/** Coste proporcional a la superficie efectiva. */
export function effectiveCost(proposal, record) {
  const ratio = proposal.area_m2 > 0 ? effectiveArea(proposal, record) / proposal.area_m2 : 1;
  return proposal.est_cost_eur * ratio;
}

/** @param {unknown} r */
export function isValidRecord(r) {
  return (
    !!r && typeof r === 'object' &&
    typeof r.proposal_id === 'string' && r.proposal_id.length > 0 &&
    DECISION_VALUES.includes(r.decision) &&
    typeof r.timestamp === 'string' && !Number.isNaN(Date.parse(r.timestamp))
  );
}

/** Normaliza un registro importado para que cumpla el contrato. */
function normalizeRecord(r) {
  return {
    proposal_id: r.proposal_id,
    decision: r.decision,
    technician: String(r.technician ?? ''),
    comment: String(r.comment ?? ''),
    adjusted_area_m2: Number.isFinite(r.adjusted_area_m2) ? r.adjusted_area_m2 : null,
    timestamp: r.timestamp,
    model_version: String(r.model_version ?? ''),
    thresholds: r.thresholds && typeof r.thresholds === 'object' ? r.thresholds : {},
  };
}

/**
 * Valida una lista importada y descarta duplicados ya presentes.
 * @param {unknown} json
 * @param {DecisionRecord[]} existing
 * @returns {{accepted: DecisionRecord[], skipped: number}}
 */
export function parseImported(json, existing) {
  const list = Array.isArray(json) ? json : Array.isArray(json?.decisions) ? json.decisions : null;
  if (!list) throw new Error('El fichero no contiene una lista de decisiones.');
  const seen = new Set(existing.map((r) => `${r.proposal_id}|${r.timestamp}`));
  const accepted = [];
  let skipped = 0;
  for (const r of list) {
    const key = `${r?.proposal_id}|${r?.timestamp}`;
    if (!isValidRecord(r) || seen.has(key)) { skipped += 1; continue; }
    seen.add(key);
    accepted.push(normalizeRecord(r));
  }
  accepted.sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp));
  return { accepted, skipped };
}

/** @param {string} day YYYY-MM-DD */
export function exportFilename(day) {
  return `decisiones_verdescope_${day}.json`;
}
