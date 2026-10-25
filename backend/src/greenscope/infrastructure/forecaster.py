"""Series temporales: STL + Theil-Sen (tendencia/anomalía) y Holt-Winters (previsión)."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy.stats import theilslopes
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import STL

from greenscope.application.models import SeriesAnalysis
from greenscope.config import ModelSettings

PERIOD = 12
SLOPE_CONFIDENCE = 0.90
NDVI_FLOOR, NDVI_CEIL = -0.1, 1.0


def fill_gaps(series: np.ndarray) -> np.ndarray:
    """Interpola huecos (nubes) linealmente; los extremos se rellenan con el vecino."""
    s = pd.Series(series, dtype=float)
    return s.interpolate(limit_direction="both").to_numpy()


class StlTheilSenForecaster:
    """Implementa el puerto `Forecaster` para series mensuales de NDVI."""

    def __init__(self, settings: ModelSettings) -> None:
        self._s = settings

    def analyze(self, series: np.ndarray, horizon: int) -> SeriesAnalysis:
        y = fill_gaps(np.asarray(series, float))
        slope, resid_z = self._trend_and_residual(y)
        mean, lo, hi = self._forecast(y, horizon)
        return SeriesAnalysis(
            slope_per_year=float(slope[0]),
            anomaly=self._is_anomalous(slope, resid_z),
            forecast=mean,
            lo=lo,
            hi=hi,
        )

    def backtest_mae(self, series: np.ndarray, horizon: int) -> float:
        """MAE de la previsión sobre los últimos `horizon` meses observados (sin nubes)."""
        raw = np.asarray(series, float)
        mean, _, _ = self._forecast(fill_gaps(raw[:-horizon]), horizon)
        actual = raw[-horizon:]
        observed = ~np.isnan(actual)
        if not observed.any():
            return float("nan")
        return float(np.mean(np.abs(mean[observed] - actual[observed])))

    def _trend_and_residual(self, y: np.ndarray) -> tuple[tuple[float, float, float], float]:
        stl = STL(y, period=PERIOD, robust=True).fit()
        deseasonal = stl.trend + stl.resid
        years = np.arange(len(y)) / PERIOD
        slope, _, lo, hi = theilslopes(deseasonal, years, alpha=SLOPE_CONFIDENCE)
        recent = stl.resid[-self._s.anomaly_recent_months :]
        scale = 1.4826 * np.median(np.abs(stl.resid - np.median(stl.resid))) + 1e-9
        return (float(slope), float(lo), float(hi)), float(np.min(recent) / scale)

    def _is_anomalous(self, slope: tuple[float, float, float], resid_z: float) -> bool:
        """Pendiente significativamente negativa (IC 90 % < 0) y relevante, o residuo extremo."""
        point, _, upper = slope
        significant_decline = upper < 0.0 and point <= self._s.anomaly_min_slope
        return bool(significant_decline or resid_z <= self._s.anomaly_resid_z)

    def _forecast(self, y: np.ndarray, horizon: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = ExponentialSmoothing(
                y, trend="add", damped_trend=True, seasonal="add", seasonal_periods=PERIOD
            ).fit()
        mean = np.clip(model.forecast(horizon), NDVI_FLOOR, NDVI_CEIL)
        sigma = float(np.std(model.resid))
        alpha = float(model.params["smoothing_level"])
        steps = np.arange(horizon)
        spread = self._s.band_z * sigma * np.sqrt(1.0 + steps * alpha**2)
        return (
            mean,
            np.clip(mean - spread, NDVI_FLOOR, NDVI_CEIL),
            np.clip(mean + spread, NDVI_FLOOR, NDVI_CEIL),
        )
