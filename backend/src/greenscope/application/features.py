"""Caso de uso BuildFeatures: fusión multi-fuente y features por celda H3."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

from greenscope.application.models import Grid, OsmFeatures, SourceContext
from greenscope.application.ports import (
    DataSource,
    PatchProvider,
    VegetationSegmenter,
)
from greenscope.application.spatial import compute_osm_cell_stats, green_union_xy
from greenscope.config import Settings

SUMMER_MONTHS = (6, 7, 8)
MONTHS_IN_YEAR = 12


@dataclass
class SourceBundle:
    """Conectores de datos (reales o sintéticos) tras la interfaz común."""

    sentinel2: DataSource
    lst: DataSource
    ine: DataSource
    smart_steps: DataSource
    patches: PatchProvider

    def all(self) -> list[DataSource]:
        return [self.sentinel2, self.lst, self.ine, self.smart_steps]


@dataclass
class FeatureSet:
    """Resultado de la fusión: features estáticas + series mensuales."""

    features: pd.DataFrame
    ndvi: pd.DataFrame
    lst: pd.DataFrame
    context: SourceContext


def month_labels(start: str, end: str) -> list[str]:
    """Meses 'YYYY-MM' entre start y end, ambos incluidos."""
    return [str(p) for p in pd.period_range(start, end, freq="M")]


def last_summer_columns(months: list[str]) -> list[str]:
    """Columnas de jun-ago del último verano completo de la serie."""
    last = pd.Period(months[-1], freq="M")
    year = last.year if last.month >= max(SUMMER_MONTHS) else last.year - 1
    cols = [f"{year}-{m:02d}" for m in SUMMER_MONTHS]
    return [c for c in cols if c in months]


class BuildFeatures:
    """Fusiona OSM + Sentinel-2 + LST + INE + Smart Steps en una tabla de features."""

    def __init__(
        self,
        sources: SourceBundle,
        segmenter: VegetationSegmenter,
        settings: Settings,
    ) -> None:
        self._sources = sources
        self._segmenter = segmenter
        self._settings = settings

    def run(self, grid: Grid, osm: OsmFeatures) -> FeatureSet:
        s = self._settings
        months = month_labels(s.period_start, s.period_end)
        stats = compute_osm_cell_stats(grid, osm, s.refs)
        ctx = SourceContext(grid, osm, stats, months, green_union_xy(osm, grid))
        ndvi = self._sources.sentinel2.fetch(ctx)
        ctx = replace(ctx, ndvi=ndvi)
        lst = self._sources.lst.fetch(ctx)
        ine = self._sources.ine.fetch(ctx)
        mobility = self._sources.smart_steps.fetch(ctx)
        canopy = self._canopy_pct(ctx)
        features = self._assemble(ctx, ine, mobility, ndvi, lst, canopy)
        return FeatureSet(features, ndvi, lst, ctx)

    def _canopy_pct(self, ctx: SourceContext) -> np.ndarray:
        patches = self._sources.patches.ndvi_patches(ctx)
        mask = self._segmenter.segment(patches)
        return mask.mean(axis=(1, 2)) * 100.0

    @staticmethod
    def _summer_lst(lst: pd.DataFrame, months: list[str]) -> np.ndarray:
        """LST media del último verano; si todo son nubes, media de todos los veranos."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)  # filas totalmente nubosas
            last = np.nanmean(lst[last_summer_columns(months)].to_numpy(), axis=1)
        all_summers = [c for c in months if int(c[5:7]) in SUMMER_MONTHS]
        fallback = np.nanmean(lst[all_summers].to_numpy(), axis=1)
        return np.where(np.isnan(last), fallback, last)

    def _assemble(
        self,
        ctx: SourceContext,
        ine: pd.DataFrame,
        mobility: pd.DataFrame,
        ndvi: pd.DataFrame,
        lst: pd.DataFrame,
        canopy: np.ndarray,
    ) -> pd.DataFrame:
        refs = self._settings.refs
        grid = ctx.grid
        idx = pd.Index(grid.h3_ids, name="h3")
        df = pd.DataFrame({"lat": grid.lat, "lon": grid.lon}, index=idx)
        df["district"] = ine.loc[idx, "district"]
        df["population"] = ine.loc[idx, "population"].astype(int)
        df["floating_population"] = mobility.loc[idx, "floating_population"].astype(int)
        pop_for_ratio = np.maximum(df["population"].to_numpy(float), refs.min_pop_for_ratio)
        per_capita = ctx.stats["green_accessible_m2"].to_numpy() / pop_for_ratio
        df["green_m2_per_capita"] = np.minimum(per_capita, refs.max_m2_per_capita)
        df["dist_green_m"] = ctx.stats["dist_green_m"].to_numpy()
        df["canopy_pct"] = canopy
        df["ndvi_mean"] = np.nanmean(ndvi.iloc[:, -MONTHS_IN_YEAR:].to_numpy(), axis=1)
        df["ndvi_trend"] = 0.0  # se completa con ForecastVegetation
        df["lst_c"] = self._summer_lst(lst, ctx.months)
        df["vulnerability"] = ine.loc[idx, "vulnerability"].to_numpy()
        return df
