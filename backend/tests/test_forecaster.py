"""Series temporales: STL + Theil-Sen, previsión Holt-Winters y backtest."""

from __future__ import annotations

import numpy as np
import pytest

from verdescope.application.forecasting import next_months
from verdescope.config import ModelSettings
from verdescope.infrastructure.forecaster import StlTheilSenForecaster, fill_gaps

MONTHS = 93
HORIZON = 12


def seasonal_series(slope_per_year=0.0, noise=0.01, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(MONTHS)
    season = 0.08 * np.cos(2 * np.pi * (t % 12 - 4.5) / 12)
    return 0.4 + season + slope_per_year * t / 12 + rng.normal(0, noise, MONTHS)


@pytest.fixture(scope="module")
def forecaster():
    return StlTheilSenForecaster(ModelSettings())


def test_stable_series_is_not_anomalous(forecaster):
    result = forecaster.analyze(seasonal_series(0.0), HORIZON)
    assert abs(result.slope_per_year) < 0.01
    assert result.anomaly is False


def test_declining_series_is_flagged(forecaster):
    result = forecaster.analyze(seasonal_series(-0.03), HORIZON)
    assert result.slope_per_year == pytest.approx(-0.03, abs=0.008)
    assert result.anomaly is True


def test_forecast_shape_and_band_ordering(forecaster):
    result = forecaster.analyze(seasonal_series(), HORIZON)
    assert len(result.forecast) == len(result.lo) == len(result.hi) == HORIZON
    assert (result.lo <= result.forecast).all() and (result.forecast <= result.hi).all()
    assert (result.hi - result.lo)[-1] >= (result.hi - result.lo)[0]


def test_gaps_are_interpolated_and_do_not_break_analysis(forecaster):
    series = seasonal_series()
    series[[5, 6, 40, 41, 42, 90]] = np.nan
    assert not np.isnan(fill_gaps(series)).any()
    assert len(forecaster.analyze(series, HORIZON).forecast) == HORIZON


def test_backtest_mae_is_small_for_clean_seasonal_series(forecaster):
    mae = forecaster.backtest_mae(seasonal_series(noise=0.01), HORIZON)
    assert 0 <= mae < 0.03


def test_next_months_continue_after_last_date():
    months = next_months("2026-09", 12)
    assert months[0] == "2026-10" and months[-1] == "2027-09" and len(months) == 12
