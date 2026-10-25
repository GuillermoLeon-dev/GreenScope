/** Arranque de GreenScope: carga datos, crea el estado y conecta los módulos de UI. */
import { DEFAULT_THRESHOLDS, STORAGE_KEYS } from './config.js';
import { loadData, loadConfig } from './data/dataRepository.js';
import { createDecisionStore } from './stores/decisionStore.js';
import { createStore, watch } from './state.js';
import { withThreshold } from './domain/thresholds.js';
import { buildRecord, latestByProposal, parseImported, exportFilename } from './domain/decisions.js';
import { readJson, writeJson } from './utils/storage.js';
import { isoDay } from './utils/format.js';
import { createMap } from './ui/map.js';
import { initLayerControl } from './ui/layerControl.js';
import { initLegend } from './ui/legend.js';
import { initThresholdPanel } from './ui/thresholdPanel.js';
import { initKpis } from './ui/kpis.js';
import { initProposalList } from './ui/proposalList.js';
import { initProposalDetail } from './ui/proposalDetail.js';
import { initCellDetail } from './ui/cellDetail.js';
import { renderSourcesPanel } from './ui/sourcesPanel.js';
import { renderHeader } from './ui/header.js';
import { initTabs } from './ui/tabs.js';
import { showToast } from './ui/toast.js';

const $ = (id) => document.getElementById(id);

/** Devuelve umbrales por defecto del manifest, validados. */
function defaultThresholds(manifest) {
  const t = { ...DEFAULT_THRESHOLDS, ...(manifest.thresholds_default ?? {}) };
  return t.review < t.critical ? t : { ...DEFAULT_THRESHOLDS };
}

function initialState(thresholds) {
  const mobile = window.matchMedia('(max-width: 860px)').matches;
  return {
    thresholds,
    layer: 'classification',
    showGreen: true,
    showProposals: true,
    selection: null,
    tab: 'panel',
    sheetOpen: !mobile,
    sortBy: 'priority',
    onlyPending: false,
    technician: readJson(STORAGE_KEYS.technician, ''),
    decisions: [],
    decisionIndex: new Map(),
    focusAdjust: false,
  };
}

/** Descarga un objeto como fichero JSON usando Blob. */
function downloadJson(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement('a'), { href: url, download: filename });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Crea las acciones de usuario (única vía de mutación del estado de dominio). */
function createActions({ store, decisionStore, manifest, defaults, mapRef }) {
  const setDecisions = (decisions) => store.set({ decisions, decisionIndex: latestByProposal(decisions) });

  return {
    notify: showToast,
    setThreshold: (key, value) => store.set({ thresholds: withThreshold(store.get().thresholds, key, value) }),
    resetThresholds: () => store.set({ thresholds: { ...defaults } }),

    select(kind, id, { fly = false, focusAdjust = false } = {}) {
      store.set({ selection: { kind, id }, tab: 'detail', sheetOpen: true });
      if (fly) mapRef.current.flyTo(kind, id);
      if (focusAdjust) store.set({ focusAdjust: true });
    },
    clearSelection: () => store.set({ selection: null }),

    setTechnician(name) {
      store.set({ technician: name });
      writeJson(STORAGE_KEYS.technician, name);
    },

    /** @returns {Promise<boolean>} true si se registró */
    async decide({ proposalId, decision, comment = '', adjustedArea = null }) {
      const { technician, thresholds, decisions } = store.get();
      if (!technician.trim()) {
        showToast('Indica tu nombre de técnico/a antes de decidir.');
        $('technician').focus();
        return false;
      }
      const record = buildRecord({ proposalId, decision, technician, comment, adjustedArea, thresholds, modelVersion: manifest.model_version });
      try {
        await decisionStore.save(record);
      } catch (err) {
        console.error(err);
        showToast('No se pudo guardar la decisión en el servidor. Se mantiene sólo en esta sesión.');
      }
      setDecisions([...decisions, record]);
      showToast(`${proposalId}: ${{ approved: 'aprobada', rejected: 'rechazada', adjusted: 'ajustada', pending: 'vuelta a pendiente' }[decision]}.`);
      return true;
    },

    exportDecisions() {
      const { decisions } = store.get();
      if (!decisions.length) { showToast('Aún no hay decisiones que exportar.'); return; }
      downloadJson(exportFilename(isoDay()), decisions);
    },

    async importDecisions(file) {
      try {
        const json = JSON.parse(await file.text());
        const { accepted, skipped } = parseImported(json, store.get().decisions);
        for (const record of accepted) await decisionStore.save(record);
        setDecisions([...store.get().decisions, ...accepted]);
        showToast(`Importadas ${accepted.length} decisiones${skipped ? ` (${skipped} omitidas)` : ''}.`);
      } catch (err) {
        showToast(`No se pudo importar: ${err.message}`);
      }
    },
  };
}

/** Crea el mapa; si MapLibre no carga, la app sigue funcionando sin él. */
function safeCreateMap(data, handlers) {
  try {
    return createMap({ container: $('map'), data, handlers });
  } catch (err) {
    console.error(err);
    const msg = $('map-message');
    msg.hidden = false;
    msg.textContent = `No se pudo cargar el mapa: ${err.message}`;
    return { domains: {}, update() {}, flyTo() {}, resize() {} };
  }
}

async function boot() {
  const [data, config] = await Promise.all([loadData(), loadConfig()]);
  const { manifest } = data;
  const defaults = defaultThresholds(manifest);
  const cells = data.cells.features.map((f) => f.properties);
  const proposals = data.proposals.features.map((f) => f.properties);
  const cellsByH3 = new Map(cells.map((c) => [c.h3, c]));

  const store = createStore(initialState({ ...defaults }));
  const decisionStore = createDecisionStore(config);
  const mapRef = { current: null };
  const actions = createActions({ store, decisionStore, manifest, defaults, mapRef });

  renderHeader(manifest, data.isSample);
  renderSourcesPanel($('sources-panel'), manifest, data.isSample);
  initTabs(store);

  mapRef.current = safeCreateMap(data, {
    onCellClick: (h3) => actions.select('cell', h3),
    onProposalClick: (id) => actions.select('proposal', id),
    onEmptyClick: actions.clearSelection,
  });

  initLayerControl($('layer-control'), store);
  initLegend($('legend'), store, mapRef.current.domains);
  initThresholdPanel($('threshold-panel'), store, { cells, defaults, actions });
  initKpis($('kpis'), store, { cells, proposals });
  initProposalList($('proposal-list'), store, { proposals, actions });
  initProposalDetail($('proposal-detail'), store, { proposals, actions });
  initCellDetail($('cell-detail'), store, { cellsByH3, proposals, timeseries: data.timeseries, labels: manifest.feature_labels ?? {}, actions });

  watch(store, ['selection'], ({ selection }) => { $('detail-empty').hidden = !!selection; });

  const technicianInput = $('technician');
  technicianInput.value = store.get().technician;
  technicianInput.addEventListener('input', () => actions.setTechnician(technicianInput.value));

  watch(store, ['thresholds', 'layer', 'decisionIndex', 'selection', 'showGreen', 'showProposals'], (state) => mapRef.current.update(state));
  window.addEventListener('resize', () => mapRef.current.resize());

  try {
    const stored = await decisionStore.list();
    store.set({ decisions: stored, decisionIndex: latestByProposal(stored) });
  } catch (err) {
    console.error(err);
    showToast('No se pudieron leer las decisiones guardadas.');
  }
}

boot().catch((err) => {
  console.error(err);
  const msg = $('map-message');
  msg.hidden = false;
  msg.textContent = `No se pudieron cargar los datos: ${err.message}`;
});
