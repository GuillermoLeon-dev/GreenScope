"""Configuración central. Todos los parámetros 'mágicos' del proyecto viven aquí."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from greenscope.domain.entities import Thresholds
from greenscope.domain.policies import (
    DeficitWeights,
    PriorityWeights,
    ProposalAssumptions,
    ReferenceStandards,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "backend"
MODEL_VERSION = "deficit-lgbm-0.1.0"
SCHEMA_VERSION = "1.0.0"
METRIC_CRS = "EPSG:25830"  # ETRS89 / UTM 30N (metros)


@dataclass(frozen=True)
class ModelSettings:
    """Hiperparámetros del modelo de déficit (fusión índice + LightGBM) y series."""

    blend_index_weight: float = 0.5  # peso del índice compuesto en el score final
    label_noise: float = 0.08  # ruido de las etiquetas débiles de entrenamiento
    n_folds: int = 5
    group_h3_resolution: int = 7  # celdas padre para validación cruzada espacial
    n_estimators: int = 150
    learning_rate: float = 0.05
    num_leaves: int = 15
    min_child_samples: int = 10
    n_top_factors: int = 4
    anomaly_min_slope: float = -0.01  # NDVI/año: pendiente mínima de degradación
    anomaly_resid_z: float = -3.0  # residuo STL extremo en los últimos meses
    anomaly_recent_months: int = 6
    forecast_horizon: int = 12
    backtest_cells: int = 80
    band_z: float = 1.645  # banda de previsión al 90 %


@dataclass(frozen=True)
class SourceToggles:
    """Conectores reales desactivados por defecto (datos sintéticos coherentes)."""

    stac_sentinel2: bool = False
    ine_api: bool = False
    smart_steps_api: bool = False


@dataclass(frozen=True)
class Settings:
    bbox: tuple[float, float, float, float] = (-3.75, 40.38, -3.64, 40.46)
    h3_resolution: int = 9
    city: str = "Madrid"
    period_start: str = "2019-01"
    period_end: str = "2026-09"
    seed: int = 42
    patch_size: int = 8
    patch_pixel_m: float = 20.0
    ndvi_vegetation_threshold: float = 0.40
    thresholds: Thresholds = field(default_factory=Thresholds)
    weights: DeficitWeights = field(default_factory=DeficitWeights)
    refs: ReferenceStandards = field(default_factory=ReferenceStandards)
    priority: PriorityWeights = field(default_factory=PriorityWeights)
    proposals: ProposalAssumptions = field(default_factory=ProposalAssumptions)
    model: ModelSettings = field(default_factory=ModelSettings)
    sources: SourceToggles = field(default_factory=SourceToggles)
    overpass_endpoints: tuple[str, ...] = (
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    )
    overpass_timeout_s: int = 90
    osm_cache_path: Path = BACKEND_ROOT / "data" / "cache" / "osm_madrid.json"
    decisions_path: Path = BACKEND_ROOT / "data" / "decisions.json"
    docs_dir: Path = REPO_ROOT / "docs"

    @property
    def data_dir(self) -> Path:
        return self.docs_dir / "data"
