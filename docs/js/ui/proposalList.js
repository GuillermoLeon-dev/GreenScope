/** Lista de propuestas filtrada por umbral, ordenable, con acciones de decisión. */
import { watch } from '../state.js';
import { DECISION_META } from '../config.js';
import { isProposalAboveThreshold } from '../domain/thresholds.js';
import { statusOf, effectiveArea } from '../domain/decisions.js';
import { esc, fmtInt, fmtNum, fmtEurShort } from '../utils/format.js';

const SORTERS = {
  priority: { label: 'Prioridad', fn: (a, b) => b.priority_score - a.priority_score },
  cost: { label: 'Coste (menor primero)', fn: (a, b) => a.est_cost_eur - b.est_cost_eur },
  population: { label: 'Población servida', fn: (a, b) => b.served_population - a.served_population },
};

function cardHtml(p, status, selected, area) {
  const meta = DECISION_META[status];
  return `<li class="proposal-card${selected ? ' is-selected' : ''}" data-id="${esc(p.id)}">
    <button type="button" class="proposal-head" data-act="open" aria-label="Ver ficha de ${esc(p.id)}">
      <span><span class="proposal-title">${esc(p.id)}</span><br><span class="proposal-kind">${esc(p.kind_label)}</span></span>
      <span class="status status-${status}">${meta.label}</span>
    </button>
    <div class="bar" role="img" aria-label="Prioridad ${fmtNum(p.priority_score, 2)}"><span style="width:${Math.round(p.priority_score * 100)}%"></span></div>
    <dl class="proposal-metrics">
      <div><dt>Prioridad</dt><dd>${fmtNum(p.priority_score, 2)}</dd></div>
      <div><dt>Superficie</dt><dd>${fmtInt(area)} m²</dd></div>
      <div><dt>Coste</dt><dd>${fmtEurShort(p.est_cost_eur)}</dd></div>
      <div><dt>Pob. servida</dt><dd>${fmtInt(p.served_population)}</dd></div>
    </dl>
    <div class="btn-row">
      <button type="button" class="btn btn-sm btn-ok" data-act="approved">Aprobar</button>
      <button type="button" class="btn btn-sm btn-bad" data-act="rejected">Rechazar</button>
      <button type="button" class="btn btn-sm btn-adj" data-act="adjust">Ajustar</button>
    </div>
  </li>`;
}

/**
 * @param {HTMLElement} root
 * @param {ReturnType<import('../state.js').createStore>} store
 * @param {{proposals:Object[], actions:Object}} ctx
 */
export function initProposalList(root, store, { proposals, actions }) {
  root.innerHTML = `
    <section class="section">
      <h2>Propuestas de parques de bolsillo</h2>
      <div class="list-toolbar">
        <div class="pending-banner" id="pending-banner" aria-live="polite"></div>
        <div class="row">
          <label for="sort-select">Ordenar por
            <select id="sort-select">${Object.entries(SORTERS).map(([k, s]) => `<option value="${k}">${s.label}</option>`).join('')}</select>
          </label>
          <label><input type="checkbox" id="only-pending"> Sólo pendientes</label>
        </div>
        <div class="btn-row">
          <button type="button" class="btn btn-sm" id="export-btn">Exportar decisiones (JSON)</button>
          <button type="button" class="btn btn-sm" id="import-btn">Importar JSON</button>
          <input type="file" id="import-file" accept="application/json,.json" hidden>
        </div>
      </div>
      <ul class="proposal-items" id="proposal-items"></ul>
      <p class="proposal-note" id="hidden-note"></p>
    </section>`;

  const list = root.querySelector('#proposal-items');
  const sortSelect = root.querySelector('#sort-select');
  const onlyPending = root.querySelector('#only-pending');
  const fileInput = root.querySelector('#import-file');
  const pendingBadge = document.getElementById('pending-count');

  sortSelect.value = store.get().sortBy;
  onlyPending.checked = store.get().onlyPending;
  sortSelect.addEventListener('change', () => store.set({ sortBy: sortSelect.value }));
  onlyPending.addEventListener('change', () => store.set({ onlyPending: onlyPending.checked }));
  root.querySelector('#export-btn').addEventListener('click', actions.exportDecisions);
  root.querySelector('#import-btn').addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', async () => {
    const [file] = fileInput.files;
    fileInput.value = '';
    if (file) await actions.importDecisions(file);
  });

  list.addEventListener('click', (ev) => {
    const btn = ev.target.closest('button[data-act]');
    const card = ev.target.closest('.proposal-card');
    if (!btn || !card) return;
    const id = card.dataset.id;
    const act = btn.dataset.act;
    if (act === 'open') actions.select('proposal', id, { fly: true });
    else if (act === 'adjust') actions.select('proposal', id, { fly: true, focusAdjust: true });
    else actions.decide({ proposalId: id, decision: act, comment: '' });
  });

  watch(store, ['thresholds', 'decisionIndex', 'sortBy', 'onlyPending', 'selection'], (state) => {
    const { thresholds, decisionIndex, sortBy, onlyPending: pendingOnly, selection } = state;
    const above = proposals.filter((p) => isProposalAboveThreshold(p, thresholds));
    const pending = above.filter((p) => statusOf(decisionIndex, p.id) === 'pending');
    const shown = (pendingOnly ? pending : above).slice().sort(SORTERS[sortBy].fn);

    pendingBadge.textContent = pending.length ? String(pending.length) : '';
    root.querySelector('#pending-banner').textContent =
      pending.length ? `${pending.length} decisiones pendientes` : 'Sin decisiones pendientes sobre el umbral';
    list.innerHTML = shown.length
      ? shown.map((p) => cardHtml(p, statusOf(decisionIndex, p.id), selection?.kind === 'proposal' && selection.id === p.id, effectiveArea(p, decisionIndex.get(p.id)))).join('')
      : '<li class="empty-state">Ninguna propuesta cumple el filtro actual.</li>';
    const hidden = proposals.length - above.length;
    root.querySelector('#hidden-note').textContent = hidden > 0 ? `${hidden} propuestas bajo la prioridad mínima no se muestran.` : '';
  });
}
