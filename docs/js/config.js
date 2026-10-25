/** Constantes de configuración de GreenScope (rutas relativas: válidas bajo usuario.github.io/repo/). */

export const PATHS = {
  primary: './data/',
  fallback: './data-sample/',
  config: './config.json',
};

export const FILES = {
  manifest: 'manifest.json',
  cells: 'cells.geojson',
  proposals: 'proposals.geojson',
  timeseries: 'timeseries.json',
  greenAreas: 'green_areas.geojson',
};

export const BASEMAPS = {
  light: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
  dark: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
};

export const STORAGE_KEYS = {
  decisions: 'greenscope.decisions.v1',
  technician: 'greenscope.technician.v1',
};

export const DEFAULT_THRESHOLDS = { critical: 0.7, review: 0.4, min_proposal_priority: 0.5 };
export const THRESHOLD_GAP = 0.01;
export const SELECTED_CELL_PROP = 'h3';

/** Metadatos de las clases de la clasificación por umbrales. */
export const CLASS_META = {
  critical: { label: 'Crítico', color: '#E63780' },
  review: { label: 'Revisar', color: '#F2A900' },
  ok: { label: 'Sin déficit', color: '#00A88E' },
};

/** Metadatos de los estados de decisión. */
export const DECISION_META = {
  pending: { label: 'Pendiente', color: '#0066FF' },
  approved: { label: 'Aprobada', color: '#00A88E' },
  rejected: { label: 'Rechazada', color: '#E63780' },
  adjusted: { label: 'Ajustada', color: '#F2A900' },
};

/** Escala secuencial de déficit (0 -> 1), de la marca. */
export const SEQUENTIAL_PALETTE = ['#E5F0FF', '#8DB9FB', '#F2A900', '#E63780'];

/**
 * Capas de celdas seleccionables. `reverse`: valores altos = bueno (se invierte la rampa).
 * `domain` ausente => percentiles 2-98 calculados desde los datos.
 */
export const LAYERS = [
  { key: 'classification', label: 'Clasificación por umbrales' },
  { key: 'deficit_score', label: 'Déficit de verde (0-1)', domain: [0, 1], decimals: 2, unit: '' },
  { key: 'green_m2_per_capita', label: 'm² de verde por habitante', reverse: true, decimals: 1, unit: 'm²/hab' },
  { key: 'dist_green_m', label: 'Distancia al verde (m)', decimals: 0, unit: 'm' },
  { key: 'lst_c', label: 'Temperatura superficial (°C)', decimals: 1, unit: '°C' },
  { key: 'ndvi_trend', label: 'Tendencia NDVI (por año)', reverse: true, decimals: 3, unit: '' },
  { key: 'floating_population', label: 'Población flotante', decimals: 0, unit: 'pers.' },
];

export const DOCS = [
  ['00_indice.pdf', '00 · Resumen ejecutivo'],
  ['01_mercado_estado_arte.pdf', '01 · Mercado y estado del arte'],
  ['02_propuesta_innovacion.pdf', '02 · Propuesta de innovación'],
  ['03_arquitectura_tecnologias.pdf', '03 · Arquitectura y tecnologías'],
  ['04_ml_crisp_ml.pdf', '04 · ML y CRISP-ML(Q)'],
  ['05_despliegue_escalabilidad.pdf', '05 · Despliegue y escalabilidad'],
  ['06_viabilidad_economica.pdf', '06 · Viabilidad económica'],
  ['07_registro_iteraciones_tiempos.pdf', '07 · Registro de iteraciones y tiempos'],
];
