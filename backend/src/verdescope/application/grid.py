"""Construcción de la malla H3 sobre el bbox de la ciudad."""

from __future__ import annotations

import h3
import numpy as np
from shapely.geometry import Polygon

from verdescope.application.geo import Projector
from verdescope.application.models import Grid
from verdescope.config import Settings


def build_grid(settings: Settings) -> Grid:
    """Celdas H3 cuyo centro cae dentro del bbox, ordenadas por índice (determinista)."""
    west, south, east, north = settings.bbox
    shape = h3.LatLngPoly([(south, west), (south, east), (north, east), (north, west)])
    ids = sorted(h3.geo_to_cells(shape, settings.h3_resolution))
    projector = Projector()
    centers = np.array([h3.cell_to_latlng(c) for c in ids])
    lat, lon = centers[:, 0], centers[:, 1]
    x, y = projector.to_xy(lon, lat)
    polygons = [_cell_polygon_xy(c, projector) for c in ids]
    return Grid(ids, lat, lon, x, y, polygons, projector)


def _cell_polygon_xy(cell: str, projector: Projector) -> Polygon:
    boundary = h3.cell_to_boundary(cell)
    lon = np.array([p[1] for p in boundary])
    lat = np.array([p[0] for p in boundary])
    x, y = projector.to_xy(lon, lat)
    return Polygon(np.column_stack([x, y]))
