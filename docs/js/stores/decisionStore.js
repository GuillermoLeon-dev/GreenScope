/**
 * Almacén de decisiones (adaptador). Interfaz:
 *   list(): Promise<DecisionRecord[]>   save(record): Promise<void>
 * Local (localStorage, para GitHub Pages) o API (FastAPI) según config.json.
 */
import { STORAGE_KEYS } from '../config.js';
import { readJson, writeJson } from '../utils/storage.js';

/** Registro de auditoría en localStorage; si no está disponible, en memoria. */
export class LocalDecisionStore {
  constructor(key = STORAGE_KEYS.decisions) {
    this.key = key;
    this.memory = null;
  }

  async list() {
    if (this.memory) return this.memory;
    const data = readJson(this.key, []);
    return Array.isArray(data) ? data : [];
  }

  async save(record) {
    const all = [...(await this.list()), record];
    if (!writeJson(this.key, all)) this.memory = all; // sin localStorage: sólo sesión
  }
}

/** Cliente de la API: GET/POST {base}/api/decisions. */
export class ApiDecisionStore {
  /** @param {string} baseUrl */
  constructor(baseUrl) {
    this.endpoint = `${baseUrl.replace(/\/+$/, '')}/api/decisions`;
  }

  async list() {
    const res = await fetch(this.endpoint, { headers: { Accept: 'application/json' } });
    if (!res.ok) throw new Error(`API ${res.status}`);
    const data = await res.json();
    return Array.isArray(data) ? data : data.decisions ?? [];
  }

  async save(record) {
    const res = await fetch(this.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(record),
    });
    if (!res.ok) throw new Error(`API ${res.status}`);
  }
}

/** Factoría: API si `api_base_url` está definido; si no, local. */
export function createDecisionStore(config) {
  return config?.api_base_url ? new ApiDecisionStore(config.api_base_url) : new LocalDecisionStore();
}
