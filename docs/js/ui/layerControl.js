/** Selector de capa de color y interruptores de capas auxiliares (sobre el mapa). */
import { LAYERS } from '../config.js';
import { esc } from '../utils/format.js';

/** @param {HTMLElement} root @param {ReturnType<import('../state.js').createStore>} store */
export function initLayerControl(root, store) {
  const state = store.get();
  root.innerHTML = `
    <label class="field">Capa de color
      <select id="layer-select">
        ${LAYERS.map((l) => `<option value="${esc(l.key)}">${esc(l.label)}</option>`).join('')}
      </select>
    </label>
    <div class="check-row">
      <label><input type="checkbox" id="toggle-green"> Zonas verdes</label>
      <label><input type="checkbox" id="toggle-proposals"> Propuestas</label>
    </div>`;

  const select = root.querySelector('#layer-select');
  const green = root.querySelector('#toggle-green');
  const proposals = root.querySelector('#toggle-proposals');
  select.value = state.layer;
  green.checked = state.showGreen;
  proposals.checked = state.showProposals;

  select.addEventListener('change', () => store.set({ layer: select.value }));
  green.addEventListener('change', () => store.set({ showGreen: green.checked }));
  proposals.addEventListener('change', () => store.set({ showProposals: proposals.checked }));
}
