# Contrato de datos — GreenScope v1

Fuente única de verdad entre el **pipeline ML** (`backend/`, productor) y la **web estática**
(`docs/`, consumidora). El pipeline escribe en `docs/data/`; la web lee con rutas relativas
(`./data/...`). Cualquier cambio de esquema incrementa `schema_version` en `manifest.json`.

Convenciones: coordenadas WGS84 (EPSG:4326) `[lon, lat]`; números con ≤ 5 decimales en geometría
y ≤ 3 en atributos; textos visibles al usuario en **español**; scores normalizados en `[0, 1]`
(1 = peor / más prioritario). Ámbito demo: Madrid central,
bbox `[-3.75, 40.38, -3.64, 40.46]`, H3 resolución 9.

## 1. `docs/data/manifest.json`
```json
{
  "schema_version": "1.0.0",
  "app": "GreenScope",
  "city": "Madrid",
  "bbox": [-3.75, 40.38, -3.64, 40.46],
  "h3_resolution": 9,
  "generated_at": "2026-10-25T03:00:00+02:00",
  "model_version": "deficit-lgbm-0.1.0",
  "period": {"start": "2019-01", "end": "2026-09"},
  "thresholds_default": {"critical": 0.70, "review": 0.40, "min_proposal_priority": 0.50},
  "sources": [
    {"id": "osm", "name": "OpenStreetMap (Overpass)", "kind": "vector", "synthetic": false},
    {"id": "s2", "name": "Sentinel-2 L2A NDVI", "kind": "raster-timeseries", "synthetic": true},
    {"id": "lst", "name": "Landsat 8/9 LST", "kind": "raster-timeseries", "synthetic": true},
    {"id": "ine", "name": "INE padrón + vulnerabilidad", "kind": "tabular", "synthetic": true},
    {"id": "smartsteps", "name": "Movilidad agregada de operador (sintético, tipo Smart Steps)", "kind": "mobility", "synthetic": true}
  ],
  "metrics": {"auc": 0.0, "f1_at_critical": 0.0, "mae_forecast_ndvi": 0.0, "n_cells": 0, "n_proposals": 0},
  "feature_labels": {"green_m2_per_capita": "m² verde/hab", "...": "..."}
}
```

## 2. `docs/data/cells.geojson` — FeatureCollection de hexágonos H3 (Polygon)
`properties`:
| campo | tipo | descripción |
|---|---|---|
| `h3` | str | índice H3 res 9 |
| `district` | str | distrito municipal (nombre) |
| `population` | int | residentes (INE) |
| `floating_population` | int | población flotante media diurna (Smart Steps) |
| `green_m2_per_capita` | float | m² de verde público accesible por habitante |
| `dist_green_m` | float | distancia al espacio verde ≥ 0,5 ha más cercano (m) |
| `canopy_pct` | float | % cobertura vegetal (segmentación NDVI/U-Net) |
| `ndvi_mean` | float | NDVI medio último año |
| `ndvi_trend` | float | pendiente Theil-Sen NDVI (unidades/año) |
| `lst_c` | float | temperatura superficial media de verano (°C) |
| `vulnerability` | float 0-1 | índice de vulnerabilidad socioeconómica |
| `deficit_score` | float 0-1 | **salida del modelo**, déficit de verde fusionado |
| `uncertainty` | float 0-1 | incertidumbre del score (p.ej. desviación entre modelos) |
| `anomaly` | bool | degradación anómala detectada en la serie temporal |
| `top_factors` | list | `[{"feature": "dist_green_m", "contribution": 0.21}, ...]` 3–5 SHAP principales |

**La clasificación (crítico / revisar / ok) NO va en los datos**: la calcula la web con los
umbrales que fija el técnico (`deficit_score >= critical` → crítico; `>= review` → revisar).

## 3. `docs/data/proposals.geojson` — FeatureCollection (Polygon) de parques de bolsillo candidatos
`properties`:
| campo | tipo | descripción |
|---|---|---|
| `id` | str | `P-0001` … estable entre ejecuciones |
| `h3` | str | celda que contiene el centroide |
| `kind` | str | `solar_vacante` \| `aparcamiento` \| `interbloque` \| `chaflan` \| `calle_pacificable` |
| `kind_label` | str | etiqueta en español |
| `area_m2` | float | superficie |
| `priority_score` | float 0-1 | ranking multicriterio |
| `served_population` | int | residentes + flotantes ponderados a ≤ 300 m que ganan acceso |
| `est_cost_eur` | int | coste estimado de ejecución |
| `est_cooling_c` | float | reducción estimada de LST local (°C) |
| `co2_kg_year` | float | captura anual estimada |
| `rationale` | str | explicación legible en español (por qué se propone) |
| `source` | str | origen de la geometría (`osm` / `sintetico`) |

## 4. `docs/data/timeseries.json`
```json
{"dates": ["2019-01", "...", "2026-09"],
 "forecast_dates": ["2026-10", "...", "2027-09"],
 "cells": {"<h3>": {"ndvi": [..], "lst": [..], "ndvi_forecast": [..], "ndvi_forecast_lo": [..], "ndvi_forecast_hi": [..]}}}
```
Series mensuales con 3 decimales; `null` para huecos (nubes).

## 5. `docs/data/green_areas.geojson`
Parques/jardines existentes (OSM), Polygon, `properties`: `name`, `area_m2`, `kind`.

## 6. `docs/config.json`
```json
{"api_base_url": null}
```
`null` → la web usa `LocalDecisionStore` (localStorage). Una URL → `ApiDecisionStore`.

## 7. Registro de decisiones (lo que guarda la web / la API)
```json
{"proposal_id": "P-0001", "decision": "approved | rejected | adjusted | pending",
 "technician": "nombre", "comment": "texto", "adjusted_area_m2": null,
 "timestamp": "ISO-8601", "model_version": "deficit-lgbm-0.1.0",
 "thresholds": {"critical": 0.7, "review": 0.4, "min_proposal_priority": 0.5}}
```
Exportable como `decisiones_greenscope_<fecha>.json` (lista de registros). La API FastAPI expone
`GET/POST /api/decisions` con este mismo esquema; los registros alimentan el active learning.
