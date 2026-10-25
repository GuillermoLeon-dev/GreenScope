"""Caso de uso ExportArtifacts: serializa los resultados al contrato de datos v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import h3
import numpy as np
import pandas as pd
import shapely
from shapely.geometry import mapping
from shapely.geometry.polygon import orient

from verdescope.application.geo import Projector
from verdescope.application.models import OsmFeatures, VegetationAnalysis
from verdescope.application.ports import ArtifactWriter
from verdescope.config import MODEL_VERSION, SCHEMA_VERSION, Settings
from verdescope.domain.entities import Cell, Proposal
from verdescope.domain.labels import FEATURE_LABELS

COORD_DECIMALS = 5
ATTR_DECIMALS = 3
GREEN_SIMPLIFY_M = 1.0
MIN_GREEN_EXPORT_M2 = 300.0


@dataclass
class SourceInfo:
    id: str
    name: str
    kind: str
    synthetic: bool


@dataclass
class ExportInput:
    cells: list[Cell]
    proposals: list[Proposal]
    dates: list[str]
    ndvi: pd.DataFrame
    lst: pd.DataFrame
    analysis: VegetationAnalysis
    osm: OsmFeatures
    sources: list[SourceInfo]
    metrics: dict[str, float]
    projector: Projector


def _round_list(values: np.ndarray) -> list[float | None]:
    return [None if np.isnan(v) else round(float(v), ATTR_DECIMALS) for v in values]


def _ring(boundary) -> list[list[float]]:
    pts = [[round(lng, COORD_DECIMALS), round(lat, COORD_DECIMALS)] for lat, lng in boundary]
    poly = orient(shapely.Polygon(pts), sign=1.0)
    return [[round(x, COORD_DECIMALS), round(y, COORD_DECIMALS)] for x, y in poly.exterior.coords]


def _feature(geometry: dict[str, Any], properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "Feature", "geometry": geometry, "properties": properties}


def _collection(features: list[dict[str, Any]]) -> dict[str, Any]:
    return {"type": "FeatureCollection", "features": features}


def _r(value: float) -> float:
    return round(float(value), ATTR_DECIMALS)


class ExportArtifacts:
    """Construye los cinco ficheros del contrato y los entrega al `ArtifactWriter`."""

    def __init__(self, writer: ArtifactWriter, settings: Settings) -> None:
        self._writer = writer
        self._s = settings

    def run(self, data: ExportInput) -> dict[str, int]:
        sizes = {
            "data/cells.geojson": self._write("data/cells.geojson", self.cells_geojson(data.cells)),
            "data/proposals.geojson": self._write(
                "data/proposals.geojson", self.proposals_geojson(data.proposals)
            ),
            "data/timeseries.json": self._write("data/timeseries.json", self.timeseries(data)),
            "data/green_areas.geojson": self._write(
                "data/green_areas.geojson", self.green_areas(data.osm, data.projector)
            ),
        }
        sizes["data/manifest.json"] = self._write("data/manifest.json", self.manifest(data))
        self._write("config.json", {"api_base_url": None})
        return sizes

    def _write(self, path: str, payload: Any) -> int:
        return self._writer.write_json(path, payload)

    def manifest(self, data: ExportInput) -> dict[str, Any]:
        s = self._s
        return {
            "schema_version": SCHEMA_VERSION,
            "app": "VerdeScope",
            "city": s.city,
            "bbox": list(s.bbox),
            "h3_resolution": s.h3_resolution,
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "model_version": MODEL_VERSION,
            "period": {"start": s.period_start, "end": s.period_end},
            "thresholds_default": s.thresholds.as_dict(),
            "sources": [vars(src) for src in data.sources],
            "metrics": {
                **{k: _r(v) for k, v in data.metrics.items()},
                "n_cells": len(data.cells),
                "n_proposals": len(data.proposals),
            },
            "feature_labels": FEATURE_LABELS,
        }

    def cells_geojson(self, cells: list[Cell]) -> dict[str, Any]:
        features = []
        for c in cells:
            geometry = {"type": "Polygon", "coordinates": [_ring(h3.cell_to_boundary(c.h3))]}
            features.append(_feature(geometry, self._cell_properties(c)))
        return _collection(features)

    @staticmethod
    def _cell_properties(c: Cell) -> dict[str, Any]:
        return {
            "h3": c.h3,
            "district": c.district,
            "population": c.population,
            "floating_population": c.floating_population,
            "green_m2_per_capita": _r(c.green_m2_per_capita),
            "dist_green_m": _r(c.dist_green_m),
            "canopy_pct": _r(c.canopy_pct),
            "ndvi_mean": _r(c.ndvi_mean),
            "ndvi_trend": _r(c.ndvi_trend),
            "lst_c": _r(c.lst_c),
            "vulnerability": _r(c.vulnerability),
            "deficit_score": _r(c.deficit_score),
            "uncertainty": _r(c.uncertainty),
            "anomaly": bool(c.anomaly),
            "top_factors": [
                {"feature": f.feature, "contribution": _r(f.contribution)} for f in c.top_factors
            ],
        }

    def proposals_geojson(self, proposals: list[Proposal]) -> dict[str, Any]:
        features = []
        for p in proposals:
            geometry = {"type": "Polygon", "coordinates": [[list(pt) for pt in p.ring]]}
            props = {
                "id": p.id,
                "h3": p.h3,
                "kind": p.kind.value,
                "kind_label": p.kind_label,
                "area_m2": _r(p.area_m2),
                "priority_score": _r(p.priority_score),
                "served_population": int(p.served_population),
                "est_cost_eur": int(p.est_cost_eur),
                "est_cooling_c": _r(p.est_cooling_c),
                "co2_kg_year": _r(p.co2_kg_year),
                "rationale": p.rationale,
                "source": p.source,
            }
            features.append(_feature(geometry, props))
        return _collection(features)

    def timeseries(self, data: ExportInput) -> dict[str, Any]:
        a = data.analysis
        cells = {}
        for c in data.cells:
            cells[c.h3] = {
                "ndvi": _round_list(data.ndvi.loc[c.h3].to_numpy(float)),
                "lst": _round_list(data.lst.loc[c.h3].to_numpy(float)),
                "ndvi_forecast": _round_list(a.forecast.loc[c.h3].to_numpy(float)),
                "ndvi_forecast_lo": _round_list(a.forecast_lo.loc[c.h3].to_numpy(float)),
                "ndvi_forecast_hi": _round_list(a.forecast_hi.loc[c.h3].to_numpy(float)),
            }
        return {"dates": data.dates, "forecast_dates": a.forecast_dates, "cells": cells}

    def green_areas(self, osm: OsmFeatures, projector: Projector) -> dict[str, Any]:
        features = []
        for g in osm.green:
            xy = projector.geom_to_xy(g.geom)
            if xy.area < MIN_GREEN_EXPORT_M2:
                continue
            simple = projector.geom_to_lonlat(xy.simplify(GREEN_SIMPLIFY_M))
            simple = shapely.set_precision(simple, 10**-COORD_DECIMALS)
            if simple.is_empty or simple.geom_type not in ("Polygon", "MultiPolygon"):
                continue
            geometry = mapping(simple)
            props = {"name": g.name, "area_m2": round(float(xy.area), 1), "kind": g.kind}
            features.append(_feature(_round_geometry(geometry), props))
        return _collection(features)


def _round_geometry(geometry: dict[str, Any]) -> dict[str, Any]:
    def rnd(obj):
        if isinstance(obj, (tuple, list)):
            return [rnd(o) for o in obj]
        return round(float(obj), COORD_DECIMALS)

    return {"type": geometry["type"], "coordinates": rnd(geometry["coordinates"])}
