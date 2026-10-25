"""Caso de uso ScoreDeficit: entrena/aplica el modelo y devuelve celdas puntuadas."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from greenscope.application.ports import DeficitModel
from greenscope.domain.entities import Cell, Thresholds


@dataclass
class ScoringResult:
    cells: list[Cell]
    auc: float
    f1_at_critical: float
    label_prevalence: float


class ScoreDeficit:
    """Orquesta DeficitModel y construye las entidades `Cell`."""

    def __init__(self, model: DeficitModel, thresholds: Thresholds) -> None:
        self._model = model
        self._thresholds = thresholds

    def run(self, features: pd.DataFrame, anomaly: pd.Series) -> ScoringResult:
        report = self._model.fit(features)
        prediction = self._model.predict(features)
        cells = [
            self._to_cell(h3_id, row, prediction, i, bool(anomaly.loc[h3_id]))
            for i, (h3_id, row) in enumerate(features.iterrows())
        ]
        f1 = self._f1_at_critical(features, report.oof_probability, report.clean_labels)
        return ScoringResult(cells, report.auc, f1, report.label_prevalence)

    def _f1_at_critical(
        self, features: pd.DataFrame, oof_probability: np.ndarray, labels: np.ndarray
    ) -> float:
        """F1 de (score >= crítico) frente a la etiqueta débil, con predicciones OOF."""
        oof_score = self._model.blend_with_index(features, oof_probability)
        predicted = oof_score >= self._thresholds.critical
        return float(f1_score(labels, predicted, zero_division=0))

    @staticmethod
    def _to_cell(h3_id: str, row: pd.Series, pred, i: int, anomaly: bool) -> Cell:
        return Cell(
            h3=str(h3_id),
            district=str(row["district"]),
            population=int(row["population"]),
            floating_population=int(row["floating_population"]),
            green_m2_per_capita=float(row["green_m2_per_capita"]),
            dist_green_m=float(row["dist_green_m"]),
            canopy_pct=float(row["canopy_pct"]),
            ndvi_mean=float(row["ndvi_mean"]),
            ndvi_trend=float(row["ndvi_trend"]),
            lst_c=float(row["lst_c"]),
            vulnerability=float(row["vulnerability"]),
            deficit_score=float(pred.score[i]),
            uncertainty=float(pred.uncertainty[i]),
            anomaly=anomaly,
            top_factors=pred.top_factors[i],
        )
