/** Aviso efímero accesible (aria-live). */
let timer = 0;

/** @param {string} message @param {number} [ms] */
export function showToast(message, ms = 3500) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = message;
  el.classList.add('show');
  clearTimeout(timer);
  timer = setTimeout(() => el.classList.remove('show'), ms);
}
