/** Cabecera: badge de versión del modelo, fecha del manifest y aviso de datos de ejemplo. */
import { fmtDateTime } from '../utils/format.js';

/** @param {Object} manifest @param {boolean} isSample */
export function renderHeader(manifest, isSample) {
  document.getElementById('model-badge').textContent = `modelo ${manifest.model_version}`;
  const date = document.getElementById('date-badge');
  date.textContent = fmtDateTime(manifest.generated_at);
  date.title = `Datos generados: ${manifest.generated_at}`;
  document.getElementById('sample-badge').hidden = !isSample;
}
