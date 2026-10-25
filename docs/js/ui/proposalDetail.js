/** Ficha de propuesta: métricas, justificación, formulario de decisión e historial. */
import { watch } from '../state.js';
import { DECISION_META } from '../config.js';
import { isProposalAboveThreshold } from '../domain/thresholds.js';
import { statusOf, effectiveArea } from '../domain/decisions.js';
import { esc, fmtInt, fmtNum, fmtEur, fmtDateTime } from '../utils/format.js';

const SOURCE_LABELS = { osm: 'OpenStreetMap', sintetico: 'Sintético (demo)' };

function historyHtml(records) {
  if (!records.length) return '<p class="muted">Sin decisiones registradas todavía.</p>';
  return `<ul class="history">${records.slice().reverse().map((r) => `<li>
      <strong>${DECISION_META[r.decision].label}</strong> · ${esc(r.technician || 'sin nombre')} · ${fmtDateTime(r.timestamp)}
      ${r.adjusted_area_m2 ? `<br>Área ajustada: ${fmtInt(r.adjusted_area_m2)} m²` : ''}
      ${r.comment ? `<br>“${esc(r.comment)}”` : ''}
      <br><span class="muted">umbrales ${fmtNum(r.thresholds?.critical, 2)} / ${fmtNum(r.thresholds?.review, 2)} / ${fmtNum(r.thresholds?.min_proposal_priority, 2)} · ${esc(r.model_version)}</span>
    </li>`).join('')}</ul>`;
}

/**
 * @param {HTMLElement} root
 * @param {ReturnType<import('../state.js').createStore>} store
 * @param {{proposals:Object[], actions:Object}} ctx
 */
export function initProposalDetail(root, store, { proposals, actions }) {
  const byId = new Map(proposals.map((p) => [p.id, p]));
  const drafts = new Map(); // id -> {comment, area}: no se pierde al re-renderizar

  function render(state) {
    const { selection, decisionIndex, decisions, thresholds } = state;
    if (selection?.kind !== 'proposal' || !byId.has(selection.id)) { root.hidden = true; return; }
    const p = byId.get(selection.id);
    const rec = decisionIndex.get(p.id);
    const status = statusOf(decisionIndex, p.id);
    const draft = drafts.get(p.id) ?? { comment: rec?.comment ?? '', area: String(effectiveArea(p, rec)) };
    const history = decisions.filter((r) => r.proposal_id === p.id);

    root.hidden = false;
    root.innerHTML = `
      <div class="detail-head">
        <div><h2>${esc(p.id)} · ${esc(p.kind_label)}</h2><div class="sub">Celda ${esc(p.h3)}</div></div>
        <span class="status status-${status}">${DECISION_META[status].label}</span>
      </div>
      ${isProposalAboveThreshold(p, thresholds) ? '' : '<div class="alert alert-info">Esta propuesta queda por debajo de la prioridad mínima actual.</div>'}
      <p>${esc(p.rationale)}</p>
      <dl class="metric-grid">
        <div class="metric"><dt>Prioridad</dt><dd>${fmtNum(p.priority_score, 2)}</dd></div>
        <div class="metric"><dt>Superficie</dt><dd>${fmtInt(effectiveArea(p, rec))} m²${rec?.decision === 'adjusted' ? ` (orig. ${fmtInt(p.area_m2)})` : ''}</dd></div>
        <div class="metric"><dt>Coste estimado</dt><dd>${fmtEur(p.est_cost_eur)}</dd></div>
        <div class="metric"><dt>Población servida</dt><dd>${fmtInt(p.served_population)}</dd></div>
        <div class="metric"><dt>Enfriamiento est.</dt><dd>−${fmtNum(p.est_cooling_c, 1)} °C</dd></div>
        <div class="metric"><dt>CO₂ captado</dt><dd>${fmtInt(p.co2_kg_year)} kg/año</dd></div>
        <div class="metric"><dt>Origen geometría</dt><dd>${esc(SOURCE_LABELS[p.source] ?? p.source)}</dd></div>
      </dl>
      <p><button type="button" class="link-btn" id="goto-cell">Ver la celda ${esc(p.h3)}</button></p>

      <form class="decision-form" id="decision-form" aria-label="Decisión del técnico">
        <h3>Decisión del técnico</h3>
        <label>Comentario
          <textarea id="d-comment" maxlength="500" placeholder="Motivo o condiciones (opcional)">${esc(draft.comment)}</textarea>
        </label>
        <label>Superficie ajustada (m²) — sólo para «Ajustar»
          <input type="number" id="d-area" min="1" step="1" value="${esc(draft.area)}">
        </label>
        <div class="btn-row">
          <button type="button" class="btn btn-ok" data-decision="approved">Aprobar</button>
          <button type="button" class="btn btn-bad" data-decision="rejected">Rechazar</button>
          <button type="button" class="btn btn-adj" data-decision="adjusted">Ajustar</button>
          <button type="button" class="btn" data-decision="pending">Volver a pendiente</button>
        </div>
      </form>

      <h3>Historial de decisiones</h3>
      ${historyHtml(history)}`;

    const comment = root.querySelector('#d-comment');
    const area = root.querySelector('#d-area');
    const saveDraft = () => drafts.set(p.id, { comment: comment.value, area: area.value });
    comment.addEventListener('input', saveDraft);
    area.addEventListener('input', saveDraft);

    root.querySelector('#goto-cell').addEventListener('click', () => actions.select('cell', p.h3, { fly: true }));
    root.querySelector('#decision-form').addEventListener('click', async (ev) => {
      const decision = ev.target.closest('button[data-decision]')?.dataset.decision;
      if (!decision) return;
      const adjustedArea = Number(area.value);
      if (decision === 'adjusted' && !(adjustedArea > 0)) { actions.notify('Indica una superficie ajustada válida (m²).'); area.focus(); return; }
      const ok = await actions.decide({ proposalId: p.id, decision, comment: comment.value, adjustedArea: decision === 'adjusted' ? adjustedArea : null });
      if (ok) drafts.delete(p.id);
    });
  }

  watch(store, ['selection', 'decisions', 'decisionIndex', 'thresholds'], (state, changed) => {
    // Con sólo cambio de umbrales evitamos reconstruir el formulario si no hay propuesta abierta.
    render(state);
  });

  store.subscribe((state, changed) => {
    if (changed.includes('focusAdjust') && state.focusAdjust) {
      root.querySelector('#d-area')?.focus();
      store.set({ focusAdjust: false });
    }
  });
}
