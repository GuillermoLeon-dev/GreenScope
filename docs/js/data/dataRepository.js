/** Carga del contrato de datos (./data/) con caída a ./data-sample/ si falla. */
import { PATHS, FILES } from '../config.js';

/** @param {string} url */
async function fetchJson(url) {
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  return res.json();
}

/** Carga los ficheros obligatorios desde `base`. La serie temporal es opcional. */
async function loadFrom(base) {
  const [manifest, cells, proposals, greenAreas] = await Promise.all([
    fetchJson(base + FILES.manifest),
    fetchJson(base + FILES.cells),
    fetchJson(base + FILES.proposals),
    fetchJson(base + FILES.greenAreas).catch(() => ({ type: 'FeatureCollection', features: [] })),
  ]);
  if (!Array.isArray(cells.features) || !Array.isArray(proposals.features)) {
    throw new Error(`${base}: GeoJSON inválido`);
  }
  const timeseries = await fetchJson(base + FILES.timeseries).catch(() => null);
  return { manifest, cells, proposals, greenAreas, timeseries };
}

/**
 * Carga todos los datos; si ./data/ no existe o está corrupto usa ./data-sample/.
 * @returns {Promise<{manifest:Object, cells:Object, proposals:Object, greenAreas:Object, timeseries:Object|null, isSample:boolean}>}
 */
export async function loadData() {
  try {
    return { ...(await loadFrom(PATHS.primary)), isSample: false };
  } catch (primaryError) {
    console.warn('[GreenScope] datos reales no disponibles, uso datos de ejemplo:', primaryError.message);
    return { ...(await loadFrom(PATHS.fallback)), isSample: true };
  }
}

/** config.json ausente o inválido => {api_base_url: null}. */
export async function loadConfig() {
  try {
    const cfg = await fetchJson(PATHS.config);
    return { api_base_url: cfg?.api_base_url ?? null };
  } catch {
    return { api_base_url: null };
  }
}
