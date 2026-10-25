"""Análisis espacial de la capa OSM sobre la malla H3 (todo en metros, EPSG:25830)."""

from __future__ import annotations

import h3
import numpy as np
import pandas as pd
import shapely
from shapely import STRtree
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from greenscope.application.models import GeoPolygon, Grid, OsmFeatures
from greenscope.domain.policies import ReferenceStandards


def project_polygons(polys: list[GeoPolygon], grid: Grid) -> list[BaseGeometry]:
    """Proyecta a metros y repara geometrías inválidas."""
    out = []
    for p in polys:
        g = grid.projector.geom_to_xy(p.geom)
        out.append(g if g.is_valid else shapely.make_valid(g))
    return out


def green_union_xy(osm: OsmFeatures, grid: Grid) -> BaseGeometry:
    """Unión de todo el verde (en metros)."""
    geoms = project_polygons(osm.green, grid)
    return unary_union(geoms) if geoms else shapely.Polygon()


def compute_osm_cell_stats(grid: Grid, osm: OsmFeatures, refs: ReferenceStandards) -> pd.DataFrame:
    """Por celda: m² de verde, fracción, distancia al verde >= 0,5 ha y verde accesible."""
    union = green_union_xy(osm, grid)
    cell_area = grid.area_m2
    green_m2 = np.array([p.intersection(union).area for p in grid.polygons])
    big_parks = [g for g in project_polygons(osm.green, grid) if g.area >= refs.min_park_area_m2]
    dist = _distance_to_nearest(grid, big_parks)
    by_id = dict(zip(grid.h3_ids, green_m2, strict=True))
    accessible = np.array(
        [
            by_id[c]
            + refs.neighbor_green_weight * sum(by_id.get(n, 0.0) for n in h3.grid_ring(c, 1))
            for c in grid.h3_ids
        ]
    )
    return pd.DataFrame(
        {
            "green_m2": green_m2,
            "green_frac": np.clip(green_m2 / cell_area, 0.0, 1.0),
            "dist_green_m": dist,
            "green_accessible_m2": accessible,
        },
        index=pd.Index(grid.h3_ids, name="h3"),
    )


def _distance_to_nearest(grid: Grid, parks: list[BaseGeometry]) -> np.ndarray:
    """Distancia (m) del centroide de cada celda al parque más cercano."""
    if not parks:
        return np.full(len(grid), 2000.0)
    tree = STRtree(parks)
    points = shapely.points(grid.x, grid.y)
    _, dist = tree.query_nearest(points, return_distance=True, all_matches=False)
    return np.asarray(dist, dtype=float)
