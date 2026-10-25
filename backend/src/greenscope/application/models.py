"""Tipos de datos compartidos entre casos de uso y puertos."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry

from greenscope.application.geo import Projector
from greenscope.domain.entities import Factor


@dataclass(frozen=True)
class GeoPolygon:
    """Polígono vectorial (OSM o sintético) con atributos mínimos. Geometría en lon/lat."""

    osm_id: str
    name: str
    kind: str
    geom: BaseGeometry


@dataclass
class OsmFeatures:
    """Capas vectoriales de OSM relevantes para el análisis."""

    green: list[GeoPolygon] = field(default_factory=list)
    vacant: list[GeoPolygon] = field(default_factory=list)
    parking: list[GeoPolygon] = field(default_factory=list)
    synthetic: bool = False  # True si se usó el fallback sintético


@dataclass
class Grid:
    """Malla H3 con geometrías en metros (EPSG:25830)."""

    h3_ids: list[str]
    lat: np.ndarray
    lon: np.ndarray
    x: np.ndarray
    y: np.ndarray
    polygons: list[Polygon]
    projector: Projector

    @property
    def area_m2(self) -> np.ndarray:
        return np.array([p.area for p in self.polygons])

    def __len__(self) -> int:
        return len(self.h3_ids)


@dataclass
class SourceContext:
    """Contexto que reciben los conectores: malla, vector OSM y estadísticas espaciales."""

    grid: Grid
    osm: OsmFeatures
    stats: pd.DataFrame  # índice h3: green_m2, green_frac, dist_green_m, green_accessible_m2
    months: list[str]
    green_union_xy: BaseGeometry
    ndvi: pd.DataFrame | None = None  # serie NDVI mensual (la usan los conectores dependientes)


@dataclass
class ModelReport:
    """Resultado del entrenamiento del modelo de déficit."""

    auc: float
    oof_probability: np.ndarray
    clean_labels: np.ndarray
    label_prevalence: float


@dataclass
class DeficitPrediction:
    """Salida del modelo para todas las celdas."""

    score: np.ndarray
    uncertainty: np.ndarray
    top_factors: list[list[Factor]]


@dataclass
class SeriesAnalysis:
    """Análisis de la serie NDVI de una celda."""

    slope_per_year: float
    anomaly: bool
    forecast: np.ndarray
    lo: np.ndarray
    hi: np.ndarray


@dataclass
class VegetationAnalysis:
    """Análisis temporal de todas las celdas."""

    slope: pd.Series
    anomaly: pd.Series
    forecast: pd.DataFrame
    forecast_lo: pd.DataFrame
    forecast_hi: pd.DataFrame
    forecast_dates: list[str]
    mae_forecast: float
