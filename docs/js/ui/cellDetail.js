/** Ficha de celda: métricas, incertidumbre, serie NDVI/LST con previsión y factores SHAP. */
import { watch } from '../state.js';
import { CLASS_META } from '../config.js';
import { classify } from '../domain/thresholds.js';
import { esc, fmtInt, fmtNum, fmtPct } from '../utils/format.js';

const LOW_CONFIDENCE = 0.3;
const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

function confidenceLabel(u) {
  if (u > LOW_CONFIDENCE) return { text: 'Confianza baja', cls: 'alert-warn' };
  if (u > 0.15) return { text: 'Confianza media', cls: 'alert-info' };
  return { text: 'Confianza alta', cls: 'alert-info' };
}

function shapHtml(factors, labels) {
  if (!factors?.length) return '<p class="muted">Sin factores explicativos.</p>';
  const max = Math.max(...factors.map((f) => Math.abs(f.contribution)), 1e-9);
  return `<ul class="shap">${factors.map((f) => {
    const w = Math.round((Math.abs(f.contribution) / max) * 50);
    const sign = f.contribution >= 0 ? 'pos' : 'neg';
    return `<li><div>${esc(labels[f.feature] ?? f.feature)}
      <div class="shap-track"><span class="shap-fill shap-${sign}" style="width:${w}%"></span></div></div>
      <span class="shap-val">${f.contribution >= 0 ? '+' : '−'}${fmtNum(Math.abs(f.contribution), 2)}</span></li>`;
  }).join('')}</ul>
  <p class="muted">Rojo: aumenta el déficit estimado. Verde: lo reduce (valores SHAP).</p>`;
}

/** Serie con ceros de relleno para alinear histórico y previsión en el mismo eje. */
function buildChartConfig(series, ts, metric) {
  const hist = series[metric] ?? [];
  const labels = [...ts.dates, ...(metric === 'ndvi' ? ts.forecast_dates : [])];
  const pad = (arr) => [...arr, ...Array(Math.max(0, labels.length - arr.length)).fill(null)];
  const blue = cssVar('--accent') || '#0066FF';
  const critical = '#E63780';
  const grid = cssVar('--border') || '#ddd';
  const text = cssVar('--text-2') || '#58617A';

  const datasets = [{ label: metric === 'ndvi' ? 'NDVI observado' : 'LST (°C)', data: pad(hist), borderColor: blue, backgroundColor: blue, pointRadius: 0, borderWidth: 2, spanGaps: true, tension: 0.2 }];
  if (metric === 'ndvi' && series.ndvi_forecast?.length) {
    const lastIdx = hist.reduce((last, v, i) => (v === null || v === undefined ? last : i), -1);
    const blank = Array(ts.dates.length).fill(null);
    const withAnchor = (arr) => {
      const out = [...blank, ...arr];
      if (lastIdx >= 0) out[lastIdx] = hist[lastIdx];
      return out;
    };
    datasets.push(
      { label: 'Banda baja', data: withAnchor(series.ndvi_forecast_lo), borderWidth: 0, pointRadius: 0, backgroundColor: 'transparent', fill: false },
      { label: 'Intervalo de previsión', data: withAnchor(series.ndvi_forecast_hi), borderWidth: 0, pointRadius: 0, backgroundColor: 'rgba(230,55,128,.18)', fill: '-1' },
      { label: 'Previsión NDVI', data: withAnchor(series.ndvi_forecast), borderColor: critical, backgroundColor: critical, borderDash: [5, 4], pointRadius: 0, borderWidth: 2, tension: 0.2 },
    );
  }
  return {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { labels: { color: text, boxWidth: 12, filter: (item) => item.text !== 'Banda baja' } },
        tooltip: { filter: (item) => item.dataset.label !== 'Banda baja' },
      },
      scales: {
        x: { ticks: { color: text, maxTicksLimit: 7, maxRotation: 0 }, grid: { color: grid } },
        y: { ticks: { color: text }, grid: { color: grid } },
      },
    },
  };
}

/**
 * @param {HTMLElement} root
 * @param {ReturnType<import('../state.js').createStore>} store
 * @param {{cellsByH3:Map<string,Object>, proposals:Object[], timeseries:Object|null, labels:Object, actions:Object}} ctx
 */
export function initCellDetail(root, store, { cellsByH3, proposals, timeseries, labels, actions }) {
  let chart = null;
  let metric = 'ndvi';
  let shownId = null;

  const destroyChart = () => { chart?.destroy(); chart = null; };

  function drawChart(cell) {
    destroyChart();
    const canvas = root.querySelector('#cell-chart');
    const series = timeseries?.cells?.[cell.h3];
    const note = root.querySelector('#chart-note');
    if (!canvas) return;
    if (!series || !window.Chart) {
      canvas.parentElement.hidden = true;
      note.textContent = !window.Chart ? 'No se pudo cargar Chart.js.' : 'Sin serie temporal para esta celda.';
      return;
    }
    canvas.parentElement.hidden = false;
    note.textContent = '';
    chart = new window.Chart(canvas, buildChartConfig(series, timeseries, metric));
  }

  function updateClassBadge(thresholds) {
    const badge = root.querySelector('#cell-class');
    if (!badge || !shownId) return;
    const cls = classify(cellsByH3.get(shownId).deficit_score, thresholds);
    badge.className = `class-badge class-${cls}`;
    badge.textContent = CLASS_META[cls].label;
  }

  function render(state) {
    const { selection, thresholds } = state;
    if (selection?.kind !== 'cell' || !cellsByH3.has(selection.id)) { root.hidden = true; destroyChart(); shownId = null; return; }
    if (shownId === selection.id && !root.hidden) { updateClassBadge(thresholds); return; }

    const c = cellsByH3.get(selection.id);
    shownId = c.h3;
    const conf = confidenceLabel(c.uncertainty);
    const cellProposals = proposals.filter((p) => p.h3 === c.h3);
    root.hidden = false;
    root.innerHTML = `
      <div class="detail-head">
        <div><h2>${esc(c.district)}</h2><div class="sub">Celda H3 ${esc(c.h3)}</div></div>
        <span id="cell-class"></span>
      </div>
      <div class="bar" role="img" aria-label="Déficit ${fmtNum(c.deficit_score, 2)}"><span style="width:${Math.round(c.deficit_score * 100)}%;background:var(--critical)"></span></div>
      <p class="muted">Déficit de verde: <strong>${fmtNum(c.deficit_score, 2)}</strong> (0 = sin déficit, 1 = máximo)</p>
      <div class="alert ${conf.cls}">${conf.text} · incertidumbre ${fmtNum(c.uncertainty, 2)}${c.uncertainty > LOW_CONFIDENCE ? ' · interpreta el score con cautela y valida sobre el terreno.' : ''}</div>
      ${c.anomaly ? '<div class="alert alert-bad"><strong>Anomalía:</strong> se detecta una degradación anómala del verde en la serie temporal.</div>' : ''}
      <dl class="metric-grid">
        <div class="metric"><dt>Población residente</dt><dd>${fmtInt(c.population)}</dd></div>
        <div class="metric"><dt>Población flotante</dt><dd>${fmtInt(c.floating_population)}</dd></div>
        <div class="metric"><dt>m² verde / hab.</dt><dd>${fmtNum(c.green_m2_per_capita, 1)}</dd></div>
        <div class="metric"><dt>Distancia al verde</dt><dd>${fmtInt(c.dist_green_m)} m</dd></div>
        <div class="metric"><dt>Cobertura vegetal</dt><dd>${fmtNum(c.canopy_pct, 1)} %</dd></div>
        <div class="metric"><dt>NDVI medio</dt><dd>${fmtNum(c.ndvi_mean, 2)}</dd></div>
        <div class="metric"><dt>Tendencia NDVI</dt><dd>${c.ndvi_trend >= 0 ? '+' : '−'}${fmtNum(Math.abs(c.ndvi_trend), 3)}/año</dd></div>
        <div class="metric"><dt>LST verano</dt><dd>${fmtNum(c.lst_c, 1)} °C</dd></div>
        <div class="metric"><dt>Vulnerabilidad</dt><dd>${fmtPct(c.vulnerability)}</dd></div>
      </dl>
      <section class="section">
        <div class="chart-head"><h3>Serie temporal</h3>
          <div class="seg" role="group" aria-label="Variable de la serie">
            <button type="button" data-metric="ndvi" aria-pressed="${metric === 'ndvi'}">NDVI</button>
            <button type="button" data-metric="lst" aria-pressed="${metric === 'lst'}">LST</button>
          </div></div>
        <div class="chart-box"><canvas id="cell-chart" role="img" aria-label="Serie temporal de la celda"></canvas></div>
        <p class="muted" id="chart-note"></p>
      </section>
      <section class="section"><h3 style="margin-bottom:8px">Factores que explican el score</h3>${shapHtml(c.top_factors, labels)}</section>
      <section class="section"><h3 style="margin-bottom:8px">Propuestas en esta celda</h3>
        ${cellProposals.length
          ? `<ul class="link-list">${cellProposals.map((p) => `<li><button type="button" class="link-btn" data-proposal="${esc(p.id)}">${esc(p.id)} · ${esc(p.kind_label)} · ${fmtInt(p.area_m2)} m²</button></li>`).join('')}</ul>`
          : '<p class="muted">No hay propuestas en esta celda.</p>'}
      </section>`;

    updateClassBadge(thresholds);
    root.querySelectorAll('[data-proposal]').forEach((b) => b.addEventListener('click', () => actions.select('proposal', b.dataset.proposal, { fly: true })));
    root.querySelectorAll('[data-metric]').forEach((b) => b.addEventListener('click', () => {
      metric = b.dataset.metric;
      root.querySelectorAll('[data-metric]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
      drawChart(c);
    }));
    drawChart(c);
  }

  watch(store, ['selection', 'thresholds'], render);
}
