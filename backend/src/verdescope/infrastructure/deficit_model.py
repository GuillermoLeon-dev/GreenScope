"""Modelo de déficit: fusión de índice compuesto (reglas) y LightGBM con SHAP."""

from __future__ import annotations

import warnings

import h3
import numpy as np
import pandas as pd
import shap
from lightgbm import LGBMClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

from verdescope.application.models import DeficitPrediction, ModelReport
from verdescope.config import Settings
from verdescope.domain import rules
from verdescope.domain.entities import Factor
from verdescope.domain.labels import FEATURE_COLUMNS

PROB_EPS = 1e-4
MAX_STD_OF_UNIT_VALUES = 0.5  # desviación máxima de valores en [0, 1]; escala la incertidumbre


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, PROB_EPS, 1.0 - PROB_EPS)
    return np.log(p / (1.0 - p))


class FusionDeficitModel:
    """Score = mezcla de índice compuesto ponderado y probabilidad calibrada de LightGBM.

    - Etiquetas débiles: reglas OMS 9 m²/hab, 300 m y 30 % de copas (+ ruido configurable).
    - Validación cruzada espacial (GroupKFold por celda H3 padre) para métricas honestas.
    - Incertidumbre: desviación típica entre estimadores (índice + modelos de cada fold).
    - Explicabilidad: SHAP (TreeExplainer) promediado entre los modelos del ensamble.
    """

    def __init__(self, settings: Settings) -> None:
        self._s = settings
        self._models: list[LGBMClassifier] = []
        self._calibrator: LogisticRegression | None = None

    def fit(self, features: pd.DataFrame) -> ModelReport:
        m = self._s.model
        x = features[list(FEATURE_COLUMNS)]
        clean = rules.weak_critical_label(features, self._s.refs)
        noisy = self._add_label_noise(clean)
        groups = [h3.cell_to_parent(c, m.group_h3_resolution) for c in features.index]
        if len(set(groups)) < 2:  # malla diminuta: bloques por posición
            groups = [i * m.n_folds // len(features) for i in range(len(features))]
        n_splits = max(2, min(m.n_folds, len(set(groups))))
        oof = np.zeros(len(x))
        self._models = []
        for train, test in GroupKFold(n_splits=n_splits).split(x, noisy, groups):
            model = self._new_model()
            model.fit(x.iloc[train], noisy[train])
            oof[test] = model.predict_proba(x.iloc[test])[:, 1]
            self._models.append(model)
        self._calibrator = LogisticRegression().fit(_logit(oof)[:, None], noisy)
        oof_calibrated = self._calibrator.predict_proba(_logit(oof)[:, None])[:, 1]
        auc = (
            float(roc_auc_score(clean, oof_calibrated))
            if 0 < clean.sum() < len(clean)
            else float("nan")
        )
        return ModelReport(auc, oof_calibrated, clean, float(clean.mean()))

    def predict(self, features: pd.DataFrame) -> DeficitPrediction:
        x = features[list(FEATURE_COLUMNS)]
        index = self._index(features)
        fold_probs = np.column_stack(
            [self._calibrate(mdl.predict_proba(x)[:, 1]) for mdl in self._models]
        )
        probability = self._calibrate(
            np.mean([mdl.predict_proba(x)[:, 1] for mdl in self._models], axis=0)
        )
        score = self.blend_with_index(features, probability)
        estimators = np.column_stack([index, fold_probs])
        uncertainty = np.clip(estimators.std(axis=1) / MAX_STD_OF_UNIT_VALUES, 0.0, 1.0)
        return DeficitPrediction(score, uncertainty, self._top_factors(x))

    def blend_with_index(self, features: pd.DataFrame, probability: np.ndarray) -> np.ndarray:
        w = self._s.model.blend_index_weight
        return np.clip(w * self._index(features) + (1.0 - w) * np.asarray(probability), 0.0, 1.0)

    def _index(self, features: pd.DataFrame) -> np.ndarray:
        return rules.composite_deficit_index(features, self._s.weights, self._s.refs)

    def _calibrate(self, raw_probability: np.ndarray) -> np.ndarray:
        assert self._calibrator is not None, "fit() debe llamarse antes de predict()"
        return self._calibrator.predict_proba(_logit(raw_probability)[:, None])[:, 1]

    def _add_label_noise(self, labels: np.ndarray) -> np.ndarray:
        rng = np.random.default_rng(self._s.seed + 50)
        flip = rng.random(len(labels)) < self._s.model.label_noise
        return np.where(flip, ~labels, labels).astype(int)

    def _new_model(self) -> LGBMClassifier:
        m = self._s.model
        return LGBMClassifier(
            n_estimators=m.n_estimators,
            learning_rate=m.learning_rate,
            num_leaves=m.num_leaves,
            min_child_samples=m.min_child_samples,
            random_state=self._s.seed,
            verbose=-1,
        )

    def _top_factors(self, x: pd.DataFrame) -> list[list[Factor]]:
        """SHAP medio entre modelos, normalizado por la suma de |SHAP| de cada celda."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            values = np.mean([self._shap_values(mdl, x) for mdl in self._models], axis=0)
        totals = np.abs(values).sum(axis=1, keepdims=True) + 1e-12
        shares = values / totals
        n_top = self._s.model.n_top_factors
        result = []
        for row in shares:
            strongest = np.argsort(-np.abs(row))[:n_top]
            ordered = sorted(strongest, key=lambda i: -row[i])
            result.append([Factor(FEATURE_COLUMNS[i], float(row[i])) for i in ordered])
        return result

    @staticmethod
    def _shap_values(model: LGBMClassifier, x: pd.DataFrame) -> np.ndarray:
        raw = shap.TreeExplainer(model).shap_values(x)
        if isinstance(raw, list):  # versiones antiguas: [clase0, clase1]
            raw = raw[1]
        raw = np.asarray(raw)
        return raw[:, :, 1] if raw.ndim == 3 else raw
