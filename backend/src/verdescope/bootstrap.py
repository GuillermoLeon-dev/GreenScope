"""Raíz de composición: ensambla adaptadores concretos según la configuración."""

from __future__ import annotations

from verdescope.application.features import SourceBundle
from verdescope.application.pipeline import RunPipeline
from verdescope.config import Settings
from verdescope.infrastructure.deficit_model import FusionDeficitModel
from verdescope.infrastructure.forecaster import StlTheilSenForecaster
from verdescope.infrastructure.osm_overpass import OverpassOsmSource
from verdescope.infrastructure.osm_synthetic import SyntheticOsmSource
from verdescope.infrastructure.real_sources import (
    IneApiSource,
    SmartStepsApiSource,
    StacSentinel2Source,
)
from verdescope.infrastructure.repositories import JsonArtifactWriter
from verdescope.infrastructure.segmenters import NdviThresholdSegmenter
from verdescope.infrastructure.synthetic_sources import (
    SyntheticIneSource,
    SyntheticLstSource,
    SyntheticSentinel2Source,
    SyntheticSmartStepsSource,
)


def build_sources(settings: Settings) -> SourceBundle:
    """Elige conectores reales o sintéticos según `Settings.sources`."""
    synthetic_s2 = SyntheticSentinel2Source(settings)
    toggles = settings.sources
    return SourceBundle(
        sentinel2=StacSentinel2Source(True) if toggles.stac_sentinel2 else synthetic_s2,
        lst=SyntheticLstSource(settings),
        ine=IneApiSource(True) if toggles.ine_api else SyntheticIneSource(settings),
        smart_steps=(
            SmartStepsApiSource(True)
            if toggles.smart_steps_api
            else SyntheticSmartStepsSource(settings)
        ),
        patches=synthetic_s2,
    )


def build_pipeline(settings: Settings, offline: bool = False) -> RunPipeline:
    """Pipeline completo con la configuración dada."""
    return RunPipeline(
        settings=settings,
        vector_source=OverpassOsmSource(settings, SyntheticOsmSource(settings), offline=offline),
        sources=build_sources(settings),
        segmenter=NdviThresholdSegmenter(settings.ndvi_vegetation_threshold),
        forecaster=StlTheilSenForecaster(settings.model),
        model=FusionDeficitModel(settings),
        writer=JsonArtifactWriter(settings.docs_dir),
    )
