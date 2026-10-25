/** Pestañas del panel lateral y hoja inferior en móvil. */
import { watch } from '../state.js';

const TABS = ['panel', 'proposals', 'detail', 'data'];

/** @param {ReturnType<import('../state.js').createStore>} store */
export function initTabs(store) {
  const buttons = TABS.map((t) => document.querySelector(`[data-tab="${t}"]`));
  const panels = TABS.map((t) => document.getElementById(`tab-${t}`));
  const sidebar = document.getElementById('sidebar');
  const handle = document.getElementById('sheet-handle');
  const handleLabel = handle.querySelector('.sheet-label');

  buttons.forEach((b) => b.addEventListener('click', () => store.set({ tab: b.dataset.tab, sheetOpen: true })));
  buttons.forEach((b, i) => b.addEventListener('keydown', (ev) => {
    const step = ev.key === 'ArrowRight' ? 1 : ev.key === 'ArrowLeft' ? -1 : 0;
    if (!step) return;
    const next = buttons[(i + step + buttons.length) % buttons.length];
    next.focus();
    store.set({ tab: next.dataset.tab });
  }));
  handle.addEventListener('click', () => store.set({ sheetOpen: !store.get().sheetOpen }));

  watch(store, ['tab'], ({ tab }) => {
    TABS.forEach((t, i) => {
      const active = t === tab;
      buttons[i].setAttribute('aria-selected', String(active));
      buttons[i].tabIndex = active ? 0 : -1;
      panels[i].hidden = !active;
    });
  });

  watch(store, ['sheetOpen', 'tab'], ({ sheetOpen, tab }) => {
    sidebar.classList.toggle('collapsed', !sheetOpen);
    sidebar.parentElement.classList.toggle('sheet-collapsed', !sheetOpen);
    handle.setAttribute('aria-expanded', String(sheetOpen));
    handleLabel.textContent = sheetOpen ? 'Ocultar panel' : 'Mostrar panel';
    handle.setAttribute('aria-label', sheetOpen ? 'Ocultar panel' : `Mostrar panel (${tab})`);
  });
}
