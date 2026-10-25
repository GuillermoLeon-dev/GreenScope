"""Caso de uso ForecastVegetation: tendencia, anomalías y previsión de NDVI por celda."""

from __future__ import annotations

import numpy as np
import pandas as pd

from verdescope.application.models import VegetationAnalysis
from verdescope.application.ports import Forecaster
from verdescope.config import ModelSettings


def next_months(last: str, count: int) -> list[str]:
    """Los `count` meses posteriores a `last` ('YYYY-MM')."""
    start = pd.Period(last, freq="M") + 1
    return [str(p) for p in pd.period_range(start, periods=count, freq="M")]


class ForecastVegetation:
    """Aplica un `Forecaster` a todas las celdas y agrega resultados y métricas."""

    def __init__(self, forecaster: Forecaster, settings: ModelSettings, seed: int) -> None:
        self._forecaster = forecaster
        self._settings = settings
        self._seed = seed

    def run(self, ndvi: pd.DataFrame) -> VegetationAnalysis:
        horizon = self._settings.forecast_horizon
        results = [self._forecaster.analyze(row, horizon) for row in ndvi.to_numpy()]
        future = next_months(str(ndvi.columns[-1]), horizon)
        index = ndvi.index
        return VegetationAnalysis(
            slope=pd.Series([r.slope_per_year for r in results], index=index),
            anomaly=pd.Series([r.anomaly for r in results], index=index),
            forecast=pd.DataFrame([r.forecast for r in results], index=index, columns=future),
            forecast_lo=pd.DataFrame([r.lo for r in results], index=index, columns=future),
            forecast_hi=pd.DataFrame([r.hi for r in results], index=index, columns=future),
            forecast_dates=future,
            mae_forecast=self._backtest(ndvi, horizon),
        )

    def _backtest(self, ndvi: pd.DataFrame, horizon: int) -> float:
        rng = np.random.default_rng(self._seed)
        n = min(self._settings.backtest_cells, len(ndvi))
        picks = rng.choice(len(ndvi), size=n, replace=False)
        maes = [self._forecaster.backtest_mae(ndvi.iloc[i].to_numpy(), horizon) for i in picks]
        return float(np.nanmean(maes))
