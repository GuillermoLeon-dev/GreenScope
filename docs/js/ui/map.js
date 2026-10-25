/** Mapa MapLibre: un source GeoJSON por capa; el recoloreado usa setPaintProperty (sin recrear capas). */
import { BASEMAPS, CLASS_META, DECISION_META } from '../config.js';
import { classify } from '../domain/thresholds.js';
import { fillColorExpression, proposalColorExpression, computeDomains } from './colorScales.js';
import { esc, fmtNum, fmtInt } from '../utils/format.js';

const SRC = { cells: 'cells', green: 'green', proposals: 'proposals' };
const hasDarkScheme = () => window.matchMedia('(prefers-color-scheme: dark)').matches;

/** Caja [minX,minY,maxX,maxY] de una geometría Polygon. */
function bboxOf(geometry) {
  const ring = geometry.coordinates[0];
  const xs = ring.map((p) => p[0]);
  const ys = ring.map((p) => p[1]);
  return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
}

function collectionBounds(fc) {
  const boxes = fc.features.map((f) => bboxOf(f.geometry));
  return [
    [Math.min(...boxes.map((b) => b[0])), Math.min(...boxes.map((b) => b[1]))],
    [Math.max(...boxes.map((b) => b[2])), Math.max(...boxes.map((b) => b[3]))],
  ];
}

function fitPadding() {
  const mobile = window.matchMedia('(max-width: 860px)').matches;
  return mobile
    ? { top: 20, left: 20, right: 20, bottom: Math.round(window.innerHeight * 0.45) }
    : { top: 20, left: 20, right: 20, bottom: 20 };
}

/**
 * @param {Object} opts
 * @param {HTMLElement} opts.container
 * @param {{cells:Object, proposals:Object, greenAreas:Object}} opts.data
 * @param {{onCellClick:(h3:string)=>void, onProposalClick:(id:string)=>void, onEmptyClick:()=>void}} opts.handlers
 */
export function createMap({ container, data, handlers }) {
  const maplibregl = window.maplibregl;
  if (!maplibregl) throw new Error('MapLibre GL no se pudo cargar (¿sin conexión al CDN?).');

  const cellProps = data.cells.features.map((f) => f.properties);
  const domains = computeDomains(cellProps);
  const featureById = {
    cell: new Map(data.cells.features.map((f) => [f.properties.h3, f])),
    proposal: new Map(data.proposals.features.map((f) => [f.properties.id, f])),
  };
  let current = null; // último estado aplicado
  let styleReady = false;

  const map = new maplibregl.Map({
    container,
    style: hasDarkScheme() ? BASEMAPS.dark : BASEMAPS.light,
    bounds: collectionBounds(data.cells),
    fitBoundsOptions: { padding: fitPadding() },
    attributionControl: { compact: true },
    minZoom: 9,
    maxZoom: 18,
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');

  const tooltip = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 10, className: 'vs-tooltip' });

  /** Añade fuentes y capas (se repite al cambiar de estilo base). */
  function installLayers() {
    map.addSource(SRC.cells, { type: 'geojson', data: data.cells });
    map.addSource(SRC.green, { type: 'geojson', data: data.greenAreas });
    map.addSource(SRC.proposals, { type: 'geojson', data: data.proposals });

    map.addLayer({ id: 'cells-fill', type: 'fill', source: SRC.cells, paint: { 'fill-color': CLASS_META.ok.color, 'fill-opacity': 0.55 } });
    map.addLayer({ id: 'cells-line', type: 'line', source: SRC.cells, paint: { 'line-color': '#ffffff', 'line-opacity': 0.6, 'line-width': 0.6 } });
    map.addLayer({ id: 'green-fill', type: 'fill', source: SRC.green, paint: { 'fill-color': '#00A88E', 'fill-opacity': 0.32 } });
    map.addLayer({ id: 'green-line', type: 'line', source: SRC.green, paint: { 'line-color': '#00A88E', 'line-width': 1.2 } });
    map.addLayer({ id: 'cell-selected', type: 'line', source: SRC.cells, filter: ['==', ['get', 'h3'], ''], paint: { 'line-color': hasDarkScheme() ? '#ffffff' : '#0B2739', 'line-width': 3 } });
    map.addLayer({ id: 'proposals-fill', type: 'fill', source: SRC.proposals, paint: { 'fill-color': DECISION_META.pending.color, 'fill-opacity': 0.45 } });
    map.addLayer({ id: 'proposals-line', type: 'line', source: SRC.proposals, paint: { 'line-color': DECISION_META.pending.color, 'line-width': 2.5 } });
    map.addLayer({ id: 'proposal-selected', type: 'line', source: SRC.proposals, filter: ['==', ['get', 'id'], ''], paint: { 'line-color': hasDarkScheme() ? '#ffffff' : '#0B2739', 'line-width': 5, 'line-gap-width': 1 } });
  }

  /** Aplica el estado de la app a las capas existentes. */
  function apply(state) {
    if (!styleReady || !state) return;
    const { thresholds, layer, decisionIndex, selection, showGreen, showProposals } = state;
    map.setPaintProperty('cells-fill', 'fill-color', fillColorExpression(layer, thresholds, domains));

    const color = proposalColorExpression(decisionIndex);
    const above = ['>=', ['get', 'priority_score'], thresholds.min_proposal_priority];
    map.setPaintProperty('proposals-fill', 'fill-color', color);
    map.setPaintProperty('proposals-line', 'line-color', color);
    map.setPaintProperty('proposals-fill', 'fill-opacity', ['case', above, 0.45, 0.08]);
    map.setPaintProperty('proposals-line', 'line-opacity', ['case', above, 1, 0.3]);

    const vis = (on) => (on ? 'visible' : 'none');
    map.setLayoutProperty('green-fill', 'visibility', vis(showGreen));
    map.setLayoutProperty('green-line', 'visibility', vis(showGreen));
    for (const id of ['proposals-fill', 'proposals-line', 'proposal-selected']) map.setLayoutProperty(id, 'visibility', vis(showProposals));

    map.setFilter('cell-selected', ['==', ['get', 'h3'], selection?.kind === 'cell' ? selection.id : '']);
    map.setFilter('proposal-selected', ['==', ['get', 'id'], selection?.kind === 'proposal' ? selection.id : '']);
  }

  function tooltipHtml(feature) {
    const p = feature.properties;
    if (feature.layer.id.startsWith('proposals')) {
      return `<div class="tip-title">${esc(p.id)} · ${esc(p.kind_label)}</div>
        <div class="tip-row">${fmtInt(p.area_m2)} m² · prioridad ${fmtNum(p.priority_score, 2)}</div>`;
    }
    const cls = classify(p.deficit_score, current.thresholds);
    return `<div class="tip-title">${esc(p.district)} · ${esc(CLASS_META[cls].label)}</div>
      <div class="tip-row">Déficit ${fmtNum(p.deficit_score, 2)} · ${fmtNum(p.green_m2_per_capita, 1)} m²/hab</div>
      <div class="tip-row">Verde a ${fmtInt(p.dist_green_m)} m · ${fmtInt(p.population)} hab.</div>`;
  }

  function interactiveLayers() {
    const layers = ['cells-fill'];
    if (current?.showProposals) layers.unshift('proposals-fill');
    return layers.filter((id) => map.getLayer(id));
  }

  let firstLoad = true;
  map.on('style.load', () => {
    if (firstLoad) {
      firstLoad = false;
      map.resize();
      map.fitBounds(collectionBounds(data.cells), { padding: fitPadding(), duration: 0 });
    }
    installLayers();
    styleReady = true;
    apply(current);
  });

  map.on('mousemove', (e) => {
    if (!styleReady || !current) return;
    const [feature] = map.queryRenderedFeatures(e.point, { layers: interactiveLayers() });
    map.getCanvas().style.cursor = feature ? 'pointer' : '';
    if (!feature) { tooltip.remove(); return; }
    tooltip.setLngLat(e.lngLat).setHTML(tooltipHtml(feature)).addTo(map);
  });
  map.on('mouseout', () => tooltip.remove());

  map.on('click', (e) => {
    if (!styleReady) return;
    const [feature] = map.queryRenderedFeatures(e.point, { layers: interactiveLayers() });
    if (!feature) { handlers.onEmptyClick(); return; }
    if (feature.layer.id === 'proposals-fill') handlers.onProposalClick(feature.properties.id);
    else handlers.onCellClick(feature.properties.h3);
  });

  const scheme = window.matchMedia('(prefers-color-scheme: dark)');
  scheme.addEventListener?.('change', () => {
    styleReady = false;
    map.setStyle(hasDarkScheme() ? BASEMAPS.dark : BASEMAPS.light);
  });

  return {
    domains,
    /** @param {Object} state estado relevante de la app */
    update(state) { current = state; apply(state); },
    /** Encuadra una celda o propuesta. */
    flyTo(kind, id) {
      const feature = featureById[kind]?.get(id);
      if (!feature) return;
      const [x0, y0, x1, y1] = bboxOf(feature.geometry);
      map.fitBounds([[x0, y0], [x1, y1]], { padding: { ...fitPadding(), top: 60, left: 60, right: 60 }, maxZoom: 17, duration: 600 });
    },
    resize: () => map.resize(),
    onError(fn) { map.on('error', (ev) => fn(ev.error)); },
  };
}
