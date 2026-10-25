/** Fuentes de datos (data fusion), métricas del modelo y enlaces a documentación. */
import { DOCS } from '../config.js';
import { esc, fmtNum, fmtInt } from '../utils/format.js';

const KIND_LABELS = {
  vector: 'Vectorial',
  'raster-timeseries': 'Serie ráster',
  tabular: 'Tabular',
  mobility: 'Movilidad agregada',
};

function metricsHtml(m = {}) {
  const rows = [
    ['AUC', Number.isFinite(m.auc) && m.auc > 0 ? fmtNum(m.auc, 3) : null],
    ['F1 en crítico', Number.isFinite(m.f1_at_critical) && m.f1_at_critical > 0 ? fmtNum(m.f1_at_critical, 3) : null],
    ['MAE previsión NDVI', Number.isFinite(m.mae_forecast_ndvi) && m.mae_forecast_ndvi > 0 ? fmtNum(m.mae_forecast_ndvi, 3) : null],
    ['Celdas', fmtInt(m.n_cells)],
    ['Propuestas', fmtInt(m.n_proposals)],
  ].filter(([, v]) => v !== null);
  return `<dl class="metric-grid">${rows.map(([k, v]) => `<div class="metric"><dt>${k}</dt><dd>${v}</dd></div>`).join('')}</dl>`;
}

/** @param {HTMLElement} root @param {Object} manifest @param {boolean} isSample */
export function renderSourcesPanel(root, manifest, isSample) {
  const sources = manifest.sources ?? [];
  root.innerHTML = `
    <section class="section">
      <h2>Fuentes de datos (data fusion)</h2>
      <p class="muted">El índice de déficit fusiona observación de la Tierra, cartografía abierta, censo y movilidad agregada.</p>
      <ul class="source-list">
        ${sources.map((s) => `<li><div><div class="source-name">${esc(s.name)}</div><div class="source-kind">${esc(KIND_LABELS[s.kind] ?? s.kind)}</div></div>
          <span class="tag ${s.synthetic ? 'tag-synth' : 'tag-real'}">${s.synthetic ? 'sintético' : 'real'}</span></li>`).join('')}
      </ul>
      ${isSample ? '<div class="alert alert-warn" style="margin-top:10px">Estás viendo datos de ejemplo (<code>./data-sample/</code>): no proceden del pipeline.</div>' : ''}
    </section>
    <section class="section">
      <h2>Modelo</h2>
      <p class="muted">Versión <strong>${esc(manifest.model_version)}</strong> · periodo ${esc(manifest.period?.start)} – ${esc(manifest.period?.end)} · esquema ${esc(manifest.schema_version)}</p>
      ${metricsHtml(manifest.metrics)}
    </section>
    <section class="section">
      <h2>Documentación</h2>
      <ul class="doc-list">
        ${DOCS.map(([file, label]) => `<li><a href="./pdf/${file}" target="_blank" rel="noopener">${esc(label)}</a></li>`).join('')}
      </ul>
    </section>
    <p class="muted">GreenScope · Proyecto independiente, sin afiliación con Telefónica ni con ninguna otra empresa. Smart Steps es una marca de Telefónica Tech, citada como posible fuente de datos.</p>`;
}
