"""Fixtures: un pipeline completo sobre un bbox pequeño con OSM sintético (sin red)."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from verdescope.application.pipeline import PipelineResult, RunPipeline
from verdescope.bootstrap import build_pipeline
from verdescope.config import ModelSettings, Settings

TEST_BBOX = (-3.72, 40.40, -3.67, 40.44)


@pytest.fixture(scope="session")
def small_settings(tmp_path_factory) -> Settings:
    docs = tmp_path_factory.mktemp("docs")
    cache = tmp_path_factory.mktemp("cache") / "missing.json"  # no existe -> fallback sintético
    return replace(
        Settings(),
        bbox=TEST_BBOX,
        docs_dir=docs,
        osm_cache_path=cache,
        model=replace(ModelSettings(), backtest_cells=10, n_estimators=60),
    )


@pytest.fixture(scope="session")
def pipeline(small_settings) -> RunPipeline:
    return build_pipeline(small_settings, offline=True)


@pytest.fixture(scope="session")
def result(pipeline) -> PipelineResult:
    return pipeline.run()


@pytest.fixture(scope="session")
def data_dir(result, small_settings) -> Path:
    return small_settings.data_dir


@pytest.fixture(scope="session")
def cells_geojson(data_dir):
    return json.loads((data_dir / "cells.geojson").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def proposals_geojson(data_dir):
    return json.loads((data_dir / "proposals.geojson").read_text(encoding="utf-8"))
