"""Fusión de features, propuestas y cumplimiento del contrato de datos v1."""

from __future__ import annotations

import json
import re

import numpy as np
import pytest

from greenscope.domain.labels import FEATURE_COLUMNS, FEATURE_LABELS

CELL_KEYS = {
    "h3", "district", "population", "floating_population", "green_m2_per_capita",
    "dist_green_m", "canopy_pct", "ndvi_mean", "ndvi_trend", "lst_c", "vulnerability",
    "deficit_score", "uncertainty", "anomaly", "top_factors",
}  # fmt: skip
PROPOSAL_KEYS = {
    "id", "h3", "kind", "kind_label", "area_m2", "priority_score", "served_population",
    "est_cost_eur", "est_cooling_c", "co2_kg_year", "rationale", "source",
}  # fmt: skip
KINDS = {"solar_vacante", "aparcamiento", "interbloque", "chaflan", "calle_pacificable"}
MAX_COORD_DECIMALS = 5
MAX_ATTR_DECIMALS = 3


def decimals(value: float) -> int:
    text = repr(float(value))
    return len(text.split(".")[1]) if "." in text and "e" not in text else 0


def iter_coords(geometry):
    def walk(node):
        if node and isinstance(node[0], (int, float)):
            yield node
        else:
            for child in node:
                yield from walk(child)

    yield from walk(geometry["coordinates"])


# --- fusión de features -------------------------------------------------------------------
def test_feature_table_has_all_model_columns_without_nans(result):
    features = result.feature_set.features
    assert set(FEATURE_COLUMNS) <= set(features.columns)
    assert not features[list(FEATURE_COLUMNS)].isna().any().any()


def test_fusion_is_spatially_coherent(result):
    f = result.feature_set.features
    in_park = f["dist_green_m"] < 1.0
    assert in_park.any() and (~in_park).any()
    assert f.loc[in_park, "canopy_pct"].mean() > f.loc[~in_park, "canopy_pct"].mean()
    assert f.loc[in_park, "ndvi_mean"].mean() > f.loc[~in_park, "ndvi_mean"].mean()
    assert f.loc[in_park, "lst_c"].mean() < f.loc[~in_park, "lst_c"].mean()


def test_sources_are_deterministic(small_settings):
    from greenscope.bootstrap import build_pipeline

    a = build_pipeline(small_settings, offline=True).run().feature_set.features
    b = build_pipeline(small_settings, offline=True).run().feature_set.features
    np.testing.assert_allclose(a["ndvi_mean"], b["ndvi_mean"])
    np.testing.assert_array_equal(a["population"], b["population"])


# --- propuestas ---------------------------------------------------------------------------
def test_proposals_respect_area_range_and_priority_floor(result, small_settings):
    a = small_settings.proposals
    assert result.proposals, "debe haber propuestas"
    for p in result.proposals:
        assert a.min_area_m2 <= p.area_m2 <= a.max_area_m2
        assert p.priority_score >= a.export_priority_floor
        assert p.est_cost_eur > 0 and p.served_population >= 0


def test_proposal_ids_are_unique_and_formatted(result):
    ids = [p.id for p in result.proposals]
    assert len(set(ids)) == len(ids)
    assert all(re.fullmatch(r"P-\d{4}", i) for i in ids)


def test_proposal_ids_are_stable_across_runs(pipeline, result):
    again = pipeline.run().proposals
    assert [(p.id, p.kind, p.area_m2) for p in again] == [
        (p.id, p.kind, p.area_m2) for p in result.proposals
    ]


def test_rationale_is_spanish_and_mentions_key_figures(result):
    text = result.proposals[0].rationale
    assert "m²" in text and "€" in text and "déficit" in text


def test_synthetic_candidates_only_in_cells_with_deficit(result, small_settings):
    review = small_settings.thresholds.review
    scores = {c.h3: c.deficit_score for c in result.scoring.cells}
    for p in result.proposals:
        if p.source == "sintetico":
            assert scores[p.h3] >= review


# --- contrato -----------------------------------------------------------------------------
def test_manifest_matches_contract(data_dir, result):
    m = json.loads((data_dir / "manifest.json").read_text(encoding="utf-8"))
    assert m["schema_version"] == "1.0.0" and m["app"] == "GreenScope"
    assert m["h3_resolution"] == 9 and m["period"] == {"start": "2019-01", "end": "2026-09"}
    assert m["thresholds_default"] == {"critical": 0.7, "review": 0.4, "min_proposal_priority": 0.5}
    assert {s["id"] for s in m["sources"]} == {"osm", "s2", "lst", "ine", "smartsteps"}
    assert m["sources"][0]["synthetic"] is True  # OSM cayó al fallback en los tests
    assert set(m["metrics"]) == {
        "auc", "f1_at_critical", "mae_forecast_ndvi", "n_cells", "n_proposals"
    }  # fmt: skip
    assert set(FEATURE_COLUMNS) <= set(m["feature_labels"])
    assert "..." not in m["feature_labels"]
    assert m["metrics"]["n_cells"] == len(result.scoring.cells)


def test_cells_geojson_properties_and_ranges(cells_geojson):
    assert cells_geojson["type"] == "FeatureCollection"
    for f in cells_geojson["features"]:
        props = f["properties"]
        assert set(props) == CELL_KEYS
        for key in ("deficit_score", "uncertainty", "vulnerability"):
            assert 0.0 <= props[key] <= 1.0
        assert isinstance(props["anomaly"], bool)
        assert 3 <= len(props["top_factors"]) <= 5
        assert all(t["feature"] in FEATURE_LABELS for t in props["top_factors"])
        assert f["geometry"]["type"] == "Polygon"
        for lon, lat in iter_coords(f["geometry"]):
            assert decimals(lon) <= MAX_COORD_DECIMALS and decimals(lat) <= MAX_COORD_DECIMALS
        for key in ("deficit_score", "lst_c", "canopy_pct", "ndvi_trend"):
            assert decimals(props[key]) <= MAX_ATTR_DECIMALS


def test_proposals_geojson_properties(proposals_geojson):
    assert proposals_geojson["features"]
    for f in proposals_geojson["features"]:
        props = f["properties"]
        assert set(props) == PROPOSAL_KEYS
        assert props["kind"] in KINDS and props["source"] in {"osm", "sintetico"}
        assert 0.0 <= props["priority_score"] <= 1.0
        assert isinstance(props["est_cost_eur"], int)
        assert isinstance(props["served_population"], int)
        ring = f["geometry"]["coordinates"][0]
        assert ring[0] == ring[-1]
        assert all(decimals(c) <= MAX_COORD_DECIMALS for pt in ring for c in pt)


def test_timeseries_lengths_and_gaps(data_dir, cells_geojson):
    ts = json.loads((data_dir / "timeseries.json").read_text(encoding="utf-8"))
    assert len(ts["dates"]) == 93 and ts["dates"][0] == "2019-01" and ts["dates"][-1] == "2026-09"
    assert len(ts["forecast_dates"]) == 12 and ts["forecast_dates"][0] == "2026-10"
    assert ts["forecast_dates"][-1] == "2027-09"
    h3_ids = {f["properties"]["h3"] for f in cells_geojson["features"]}
    assert set(ts["cells"]) == h3_ids
    gaps = 0
    for series in ts["cells"].values():
        assert len(series["ndvi"]) == len(series["lst"]) == 93
        for key in ("ndvi_forecast", "ndvi_forecast_lo", "ndvi_forecast_hi"):
            assert len(series[key]) == 12 and None not in series[key]
        gaps += series["ndvi"].count(None)
    assert gaps > 0  # huecos por nubes representados como null


def test_green_areas_and_config(data_dir):
    green = json.loads((data_dir / "green_areas.geojson").read_text(encoding="utf-8"))
    assert green["features"]
    assert set(green["features"][0]["properties"]) == {"name", "area_m2", "kind"}
    config = json.loads((data_dir.parent / "config.json").read_text(encoding="utf-8"))
    assert config == {"api_base_url": None}


def test_model_metrics_are_sane(result):
    assert 0.5 < result.metrics["auc"] <= 1.0
    assert 0.0 <= result.metrics["f1_at_critical"] <= 1.0
    assert 0.0 < result.metrics["mae_forecast_ndvi"] < 0.1


@pytest.mark.parametrize("index", [0, 1, 2])
def test_top_factors_sorted_and_signed(cells_geojson, index):
    factors = cells_geojson["features"][index]["properties"]["top_factors"]
    contributions = [t["contribution"] for t in factors]
    assert contributions == sorted(contributions, reverse=True)
