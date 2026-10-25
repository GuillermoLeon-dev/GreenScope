"""Orquestación del pipeline completo (casos de uso encadenados)."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from verdescope.application.export import ExportArtifacts, ExportInput, SourceInfo
from verdescope.application.features import BuildFeatures, FeatureSet, SourceBundle
from verdescope.application.forecasting import ForecastVegetation
from verdescope.application.grid import build_grid
from verdescope.application.models import VegetationAnalysis
from verdescope.application.ports import (
    ArtifactWriter,
    DeficitModel,
    Forecaster,
    VectorSource,
    VegetationSegmenter,
)
from verdescope.application.proposals import GenerateProposals
from verdescope.application.scoring import ScoreDeficit, ScoringResult
from verdescope.config import Settings
from verdescope.domain.entities import Proposal

log = logging.getLogger("verdescope")


@dataclass
class PipelineResult:
    scoring: ScoringResult
    proposals: list[Proposal]
    analysis: VegetationAnalysis
    feature_set: FeatureSet
    sizes: dict[str, int]
    osm_synthetic: bool
    metrics: dict[str, float]


class RunPipeline:
    """Fuentes -> features -> series temporales -> déficit -> propuestas -> artefactos."""

    def __init__(
        self,
        settings: Settings,
        vector_source: VectorSource,
        sources: SourceBundle,
        segmenter: VegetationSegmenter,
        forecaster: Forecaster,
        model: DeficitModel,
        writer: ArtifactWriter,
    ) -> None:
        self._s = settings
        self._vector = vector_source
        self._sources = sources
        self._segmenter = segmenter
        self._forecaster = forecaster
        self._model = model
        self._writer = writer

    def run(self) -> PipelineResult:
        s = self._s
        t0 = time.perf_counter()
        grid = build_grid(s)
        log.info("Malla H3 res %d: %d celdas", s.h3_resolution, len(grid))
        osm = self._vector.load()
        log.info(
            "OSM (%s): %d verdes, %d solares, %d aparcamientos",
            "sintético" if osm.synthetic else "real",
            len(osm.green),
            len(osm.vacant),
            len(osm.parking),
        )
        feature_set = BuildFeatures(self._sources, self._segmenter, s).run(grid, osm)
        analysis = ForecastVegetation(self._forecaster, s.model, s.seed).run(feature_set.ndvi)
        feature_set.features["ndvi_trend"] = analysis.slope.reindex(feature_set.features.index)
        log.info("Series temporales listas (MAE previsión %.4f)", analysis.mae_forecast)
        scoring = ScoreDeficit(self._model, s.thresholds).run(
            feature_set.features, analysis.anomaly
        )
        log.info("Modelo: AUC %.3f, F1@crítico %.3f", scoring.auc, scoring.f1_at_critical)
        proposals = GenerateProposals(s).run(
            grid, osm, scoring.cells, feature_set.context.green_union_xy
        )
        metrics = {
            "auc": scoring.auc,
            "f1_at_critical": scoring.f1_at_critical,
            "mae_forecast_ndvi": analysis.mae_forecast,
        }
        sizes = self._export(feature_set, scoring, proposals, analysis, osm, metrics, grid)
        log.info("Pipeline completado en %.1f s", time.perf_counter() - t0)
        return PipelineResult(
            scoring, proposals, analysis, feature_set, sizes, osm.synthetic, metrics
        )

    def _export(self, fs, scoring, proposals, analysis, osm, metrics, grid) -> dict[str, int]:
        sources = [self._osm_info(osm.synthetic)] + [
            SourceInfo(src.id, src.name, src.kind, src.synthetic) for src in self._sources.all()
        ]
        data = ExportInput(
            cells=scoring.cells,
            proposals=proposals,
            dates=fs.context.months,
            ndvi=fs.ndvi,
            lst=fs.lst,
            analysis=analysis,
            osm=osm,
            sources=sources,
            metrics=metrics,
            projector=grid.projector,
        )
        return ExportArtifacts(self._writer, self._s).run(data)

    def _osm_info(self, synthetic: bool) -> SourceInfo:
        name = self._vector.name + (" - fallback sintético" if synthetic else "")
        return SourceInfo(self._vector.id, name, "vector", synthetic)
