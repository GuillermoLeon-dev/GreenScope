"""Generación de parcelas candidatas: OSM (solares, aparcamientos) y sintéticas."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import shapely
from shapely import affinity
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry

from verdescope.application.models import Grid, OsmFeatures
from verdescope.application.spatial import project_polygons
from verdescope.domain.entities import ProposalKind
from verdescope.domain.policies import ProposalAssumptions

# Dimensiones (m) de las parcelas sintéticas por tipo: (mín, máx)
INTERBLOQUE_WIDTH_M = (12.0, 25.0)
INTERBLOQUE_LENGTH_M = (18.0, 45.0)
CHAFLAN_LEG_M = (18.0, 28.0)
CALLE_WIDTH_M = (4.0, 6.0)
CALLE_LENGTH_M = (40.0, 90.0)
MAX_PLACEMENT_TRIES = 12


@dataclass
class Candidate:
    """Parcela candidata con geometría en metros (EPSG:25830)."""

    kind: ProposalKind
    geom: BaseGeometry
    source: str  # 'osm' | 'sintetico'


def osm_candidates(grid: Grid, osm: OsmFeatures, a: ProposalAssumptions) -> list[Candidate]:
    """Solares y aparcamientos de OSM con área dentro de [min, max]."""
    result: list[Candidate] = []
    layers = (
        (osm.vacant, ProposalKind.SOLAR_VACANTE),
        (osm.parking, ProposalKind.APARCAMIENTO),
    )
    for polygons, kind in layers:
        for geom in project_polygons(polygons, grid):
            if geom.geom_type == "Polygon" and a.min_area_m2 <= geom.area <= a.max_area_m2:
                result.append(Candidate(kind, geom, "osm"))
    return result


def synthetic_candidates(
    grid: Grid,
    scores: pd.Series,
    green_union_xy: BaseGeometry,
    review_threshold: float,
    a: ProposalAssumptions,
    seed: int,
) -> list[Candidate]:
    """Candidatas sintéticas (interbloque, chaflán, calle pacificable) en celdas con déficit."""
    placed: list[Candidate] = []
    obstacles = [green_union_xy] if not green_union_xy.is_empty else []
    kinds = list(a.synthetic_kind_weights)
    weights = np.array([a.synthetic_kind_weights[k] for k in kinds], float)
    weights /= weights.sum()
    for h3_id, polygon in zip(grid.h3_ids, grid.polygons, strict=True):
        score = float(scores.loc[h3_id])
        if score < review_threshold:
            continue
        rng = np.random.default_rng([seed, int(h3_id, 16) % (2**32)])
        count = 2 if score >= a.synthetic_extra_score else 1
        for _ in range(count):
            kind = kinds[int(rng.choice(len(kinds), p=weights))]
            geom = _place(kind, polygon, rng, obstacles + [c.geom for c in placed])
            if geom is not None and a.min_area_m2 <= geom.area <= a.max_area_m2:
                placed.append(Candidate(kind, geom, "sintetico"))
    return placed


def _place(
    kind: ProposalKind, cell: Polygon, rng: np.random.Generator, obstacles: list[BaseGeometry]
) -> Polygon | None:
    """Coloca una forma dentro de la celda sin solaparse con obstáculos."""
    for _ in range(MAX_PLACEMENT_TRIES):
        cx, cy = _random_point_in(cell, rng)
        shape = _make_shape(kind, rng)
        shape = affinity.rotate(shape, rng.uniform(0, 180), origin=(0, 0))
        shape = affinity.translate(shape, cx, cy)
        if cell.contains(shape) and not any(shape.intersects(o) for o in obstacles):
            return shape
    return None


def _random_point_in(polygon: Polygon, rng: np.random.Generator) -> tuple[float, float]:
    minx, miny, maxx, maxy = polygon.bounds
    while True:
        x, y = rng.uniform(minx, maxx), rng.uniform(miny, maxy)
        if shapely.contains_xy(polygon, x, y):
            return float(x), float(y)


def _make_shape(kind: ProposalKind, rng: np.random.Generator) -> Polygon:
    """Forma centrada en el origen según el tipo de parcela."""
    if kind is ProposalKind.CHAFLAN:
        a, b = rng.uniform(*CHAFLAN_LEG_M), rng.uniform(*CHAFLAN_LEG_M)
        return Polygon([(0, 0), (a, 0), (0, b)])
    if kind is ProposalKind.CALLE_PACIFICABLE:
        w, length = rng.uniform(*CALLE_WIDTH_M), rng.uniform(*CALLE_LENGTH_M)
    else:
        w, length = rng.uniform(*INTERBLOQUE_WIDTH_M), rng.uniform(*INTERBLOQUE_LENGTH_M)
    return shapely.box(-length / 2, -w / 2, length / 2, w / 2)
