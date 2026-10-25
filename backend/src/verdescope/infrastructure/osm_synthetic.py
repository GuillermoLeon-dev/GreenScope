"""Fallback sintético de OSM (parques, solares y aparcamientos plausibles de Madrid)."""

from __future__ import annotations

import numpy as np
from shapely import affinity
from shapely.geometry import Point, box

from verdescope.application.models import GeoPolygon, OsmFeatures
from verdescope.config import Settings

# (nombre, lat, lon, semieje E-O m, semieje N-S m)
MAJOR_PARKS = (
    ("Parque del Retiro", 40.4153, -3.6844, 700.0, 550.0),
    ("Casa de Campo", 40.4167, -3.7450, 800.0, 1500.0),
    ("Parque del Oeste", 40.4300, -3.7230, 350.0, 700.0),
    ("Madrid Río", 40.4020, -3.7170, 120.0, 1500.0),
    ("Parque de las Siete Tetas", 40.3960, -3.6760, 200.0, 220.0),
    ("Jardín Botánico", 40.4110, -3.6910, 180.0, 160.0),
)
N_SMALL_PARKS, N_VACANT, N_PARKING = 45, 28, 45
METERS_PER_DEG_LAT = 111_000.0
ELLIPSE_RESOLUTION = 16


class SyntheticOsmSource:
    """Datos vectoriales sintéticos, deterministas. Sólo se usan si Overpass falla."""

    id = "osm"
    name = "OpenStreetMap (Overpass)"

    def __init__(self, settings: Settings) -> None:
        self._s = settings

    def load(self) -> OsmFeatures:
        rng = np.random.default_rng(self._s.seed + 1)
        features = OsmFeatures(synthetic=True)
        for name, lat, lon, a, b in MAJOR_PARKS:
            features.green.append(
                GeoPolygon(f"s-{name}", name, "parque", self._ellipse(lat, lon, a, b))
            )
        for i in range(N_SMALL_PARKS):
            lat, lon = self._random_point(rng)
            a, b = rng.uniform(40, 130, size=2)
            features.green.append(
                GeoPolygon(f"s-g{i}", f"Jardín {i + 1}", "jardin", self._ellipse(lat, lon, a, b))
            )
        for i in range(N_VACANT):
            lat, lon = self._random_point(rng)
            features.vacant.append(
                GeoPolygon(f"s-v{i}", "", "solar_vacante", self._lot(lat, lon, rng))
            )
        for i in range(N_PARKING):
            lat, lon = self._random_point(rng)
            features.parking.append(
                GeoPolygon(f"s-p{i}", "", "aparcamiento", self._lot(lat, lon, rng))
            )
        return features

    def _random_point(self, rng: np.random.Generator) -> tuple[float, float]:
        west, south, east, north = self._s.bbox
        return float(rng.uniform(south, north)), float(rng.uniform(west, east))

    def _to_deg(self, lat: float) -> tuple[float, float]:
        return METERS_PER_DEG_LAT * np.cos(np.radians(lat)), METERS_PER_DEG_LAT

    def _ellipse(self, lat: float, lon: float, a_m: float, b_m: float):
        m_lon, m_lat = self._to_deg(lat)
        circle = Point(0, 0).buffer(1.0, quad_segs=ELLIPSE_RESOLUTION // 4)
        scaled = affinity.scale(circle, a_m / m_lon, b_m / m_lat, origin=(0, 0))
        return affinity.translate(scaled, lon, lat)

    def _lot(self, lat: float, lon: float, rng: np.random.Generator):
        m_lon, m_lat = self._to_deg(lat)
        w, h = rng.uniform(15, 70, size=2)
        rect = box(-w / 2 / m_lon, -h / 2 / m_lat, w / 2 / m_lon, h / 2 / m_lat)
        return affinity.translate(rect, lon, lat)
