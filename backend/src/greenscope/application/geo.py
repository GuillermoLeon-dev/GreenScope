"""Utilidades geométricas: proyección WGS84 <-> ETRS89/UTM 30N (metros) con pyproj."""

from __future__ import annotations

import numpy as np
import shapely
from pyproj import Transformer
from shapely.geometry.base import BaseGeometry

from greenscope.config import METRIC_CRS


class Projector:
    """Convierte coordenadas y geometrías entre lon/lat (EPSG:4326) y metros (EPSG:25830)."""

    def __init__(self) -> None:
        self._fwd = Transformer.from_crs("EPSG:4326", METRIC_CRS, always_xy=True)
        self._inv = Transformer.from_crs(METRIC_CRS, "EPSG:4326", always_xy=True)

    def to_xy(self, lon, lat) -> tuple[np.ndarray, np.ndarray]:
        x, y = self._fwd.transform(np.asarray(lon, float), np.asarray(lat, float))
        return np.asarray(x), np.asarray(y)

    def to_lonlat(self, x, y) -> tuple[np.ndarray, np.ndarray]:
        lon, lat = self._inv.transform(np.asarray(x, float), np.asarray(y, float))
        return np.asarray(lon), np.asarray(lat)

    def geom_to_xy(self, geom: BaseGeometry) -> BaseGeometry:
        return shapely.transform(geom, lambda c: np.column_stack(self.to_xy(c[:, 0], c[:, 1])))

    def geom_to_lonlat(self, geom: BaseGeometry) -> BaseGeometry:
        return shapely.transform(geom, lambda c: np.column_stack(self.to_lonlat(c[:, 0], c[:, 1])))
