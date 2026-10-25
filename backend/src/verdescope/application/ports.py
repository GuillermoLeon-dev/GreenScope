"""Puertos (Protocols) que la capa de aplicación exige a la infraestructura."""

from __future__ import annotations

from typing import Any, Protocol

import numpy as np
import pandas as pd

from verdescope.application.models import (
    DeficitPrediction,
    ModelReport,
    OsmFeatures,
    SeriesAnalysis,
    SourceContext,
)
from verdescope.domain.entities import Decision


class VectorSource(Protocol):
    """Fuente vectorial (OSM): parques, solares y aparcamientos."""

    id: str
    name: str

    def load(self) -> OsmFeatures: ...


class DataSource(Protocol):
    """Conector de datos con interfaz común (data fusion).

    `fetch` devuelve un DataFrame indexado por h3. Las fuentes de series temporales
    devuelven una columna por mes ("YYYY-MM"); las tabulares, columnas con nombre.
    """

    id: str
    name: str
    kind: str
    synthetic: bool

    def fetch(self, context: SourceContext) -> pd.DataFrame: ...


class PatchProvider(Protocol):
    """Fuente raster que entrega parches NDVI (n_celdas, P, P) para segmentar."""

    def ndvi_patches(self, context: SourceContext) -> np.ndarray: ...


class VegetationSegmenter(Protocol):
    """Segmenta vegetación en parches NDVI. Devuelve máscara booleana de igual forma."""

    def segment(self, ndvi_patches: np.ndarray) -> np.ndarray: ...


class DeficitModel(Protocol):
    """Modelo de déficit de verde (fusión de índice compuesto + ML)."""

    def fit(self, features: pd.DataFrame) -> ModelReport: ...

    def predict(self, features: pd.DataFrame) -> DeficitPrediction: ...

    def blend_with_index(self, features: pd.DataFrame, probability: np.ndarray) -> np.ndarray:
        """Score final a partir de una probabilidad del modelo (p.ej. fuera de muestra)."""
        ...


class Forecaster(Protocol):
    """Análisis y previsión de una serie mensual de NDVI."""

    def analyze(self, series: np.ndarray, horizon: int) -> SeriesAnalysis: ...

    def backtest_mae(self, series: np.ndarray, horizon: int) -> float: ...


class DecisionRepository(Protocol):
    """Persistencia de decisiones (fichero JSON en demo, PostGIS en producción)."""

    def add(self, decision: Decision) -> None: ...

    def list_all(self) -> list[Decision]: ...


class ArtifactWriter(Protocol):
    """Escribe los artefactos del contrato de datos."""

    def write_json(self, relative_path: str, payload: Any) -> int:
        """Escribe JSON compacto y devuelve el tamaño en bytes."""
        ...
