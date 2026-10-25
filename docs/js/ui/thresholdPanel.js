/** Panel de umbrales (human-in-the-loop): sliders con recálculo en vivo. */
import { watch } from '../state.js';
import { summarizeCells } from '../domain/thresholds.js';
import { fmtNum, fmtInt } from '../utils/format.js';

const SLIDERS = [
  { key: 'critical', label: 'Umbral crítico', hint: 'Déficit igual o superior = celda crítica.' },
  { key: 'review', label: 'Umbral de revisión', hint: 'Entre revisión y crítico = a revisar. Siempre inferior al crítico.' },
  { key: 'min_proposal_priority', label: 'Prioridad mínima de propuesta', hint: 'Sólo se listan propuestas con prioridad igual o superior.' },
];

function sliderHtml({ key, label, hint }) {
  return `<div class="slider-block">
    <div class="slider-head">
      <label for="th-${key}">${label}</label>
      <span class="slider-value" id="val-${key}" aria-hidden="true"></span>
    </div>
    <p class="slider-hint" id="hint-${key}">${hint}</p>
    <input type="range" id="th-${key}" min="0" max="1" step="0.01" aria-describedby="hint-${key}">
    <div class="slider-foot"><span id="foot-${key}"></span><span id="mod-${key}" class="modified-tag"></span></div>
  </div>`;
}

/**
 * @param {HTMLElement} root
 * @param {ReturnType<import('../state.js').createStore>} store
 * @param {{cells:Object[], defaults:Object, actions:Object}} ctx
 */
export function initThresholdPanel(root, store, { cells, defaults, actions }) {
  root.innerHTML = `<section class="section">
    <h2>Umbrales de decisión</h2>
    <p class="muted">Ajusta los cortes y la clasificación, los KPIs y el mapa se recalculan al instante.</p>
    ${SLIDERS.map(sliderHtml).join('')}
    <div class="btn-row"><button type="button" class="btn" id="reset-thresholds">Restaurar valores del modelo</button></div>
    <p class="muted" id="class-summary" style="margin-top:10px"></p>
  </section>`;

  let frame = 0;
  for (const { key } of SLIDERS) {
    const input = root.querySelector(`#th-${key}`);
    input.addEventListener('input', () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => actions.setThreshold(key, Number(input.value)));
    });
  }
  root.querySelector('#reset-thresholds').addEventListener('click', actions.resetThresholds);

  watch(store, ['thresholds'], ({ thresholds }) => {
    for (const { key } of SLIDERS) {
      const input = root.querySelector(`#th-${key}`);
      const value = thresholds[key];
      if (document.activeElement !== input || Number(input.value) !== value) input.value = value;
      root.querySelector(`#val-${key}`).textContent = fmtNum(value, 2);
      input.setAttribute('aria-valuetext', fmtNum(value, 2));
      root.querySelector(`#foot-${key}`).textContent = `Modelo: ${fmtNum(defaults[key], 2)}`;
      root.querySelector(`#mod-${key}`).textContent = value !== defaults[key] ? 'modificado' : '';
    }
    const s = summarizeCells(cells, thresholds);
    root.querySelector('#class-summary').textContent =
      `${fmtInt(s.critical.cells)} críticas · ${fmtInt(s.review.cells)} a revisar · ${fmtInt(s.ok.cells)} sin déficit (de ${fmtInt(cells.length)} celdas).`;
  });
}
