"""Raíz de composición: ensambla adaptadores concretos según la configuración."""

from __future__ import annotations

from greenscope.application.features import SourceBundle
from greenscope.application.pipeline import RunPipeline
from greenscope.config import Settings
from greenscope.infrastructure.deficit_model import FusionDeficitModel
from greenscope.infrastructure.forecaster import StlTheilSenForecaster
from greenscope.infrastructure.osm_overpass import OverpassOsmSource
from greenscope.infrastructure.osm_synthetic import SyntheticOsmSource
from greenscope.infrastructure.real_sources import (
    IneApiSource,
    SmartStepsApiSource,
    StacSentinel2Source,
)
from greenscope.infrastructure.repositories import JsonArtifactWriter
from greenscope.infrastructure.segmenters import NdviThresholdSegmenter
from greenscope.infrastructure.synthetic_sources import (
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
