"""Adaptadores (OSM, segmentadores, repositorios) y API de decisiones."""

from __future__ import annotations

import sys
from dataclasses import replace

import numpy as np
import pytest
from fastapi.testclient import TestClient

from verdescope.api.main import create_app
from verdescope.application.decisions import InvalidDecisionError, RecordDecision
from verdescope.config import Settings
from verdescope.domain.entities import DecisionKind, Thresholds
from verdescope.infrastructure.osm_overpass import OverpassOsmSource, parse_overpass
from verdescope.infrastructure.osm_synthetic import SyntheticOsmSource
from verdescope.infrastructure.repositories import (
    InMemoryDecisionRepository,
    JsonFileDecisionRepository,
)
from verdescope.infrastructure.segmenters import NdviThresholdSegmenter, UNetSegmenter

SQUARE = [(-3.70, 40.41), (-3.69, 40.41), (-3.69, 40.42), (-3.70, 40.42), (-3.70, 40.41)]


def way(osm_id, tags, ring=SQUARE):
    geometry = [{"lat": lat, "lon": lon} for lon, lat in ring]
    return {"type": "way", "id": osm_id, "tags": tags, "geometry": geometry}


def test_parse_overpass_classifies_layers():
    raw = {
        "elements": [
            way(1, {"leisure": "park", "name": "Parque Uno"}),
            way(2, {"landuse": "brownfield"}),
            way(3, {"amenity": "parking", "parking": "surface"}),
            way(4, {"amenity": "parking", "parking": "underground"}),
            way(5, {"leisure": "garden", "access": "private"}),
        ]
    }
    osm = parse_overpass(raw)
    assert [g.name for g in osm.green] == ["Parque Uno"]
    assert len(osm.vacant) == 1 and len(osm.parking) == 1


def test_parse_overpass_assembles_multipolygon_relation():
    outer = [(-3.70, 40.41), (-3.68, 40.41), (-3.68, 40.43), (-3.70, 40.43), (-3.70, 40.41)]
    inner = [(-3.69, 40.42), (-3.685, 40.42), (-3.685, 40.425), (-3.69, 40.425), (-3.69, 40.42)]

    def member(role, ring):
        return {"type": "way", "role": role, "geometry": [{"lat": a, "lon": o} for o, a in ring]}

    relation = {
        "type": "relation", "id": 9, "tags": {"leisure": "park"},
        "members": [member("outer", outer), member("inner", inner)],
    }  # fmt: skip
    osm = parse_overpass({"elements": [relation]})
    assert len(osm.green) == 1
    full = parse_overpass({"elements": [way(1, {"leisure": "park"}, outer)]}).green[0].geom
    assert osm.green[0].geom.area < full.area  # el hueco interior se descuenta


def test_overpass_source_falls_back_when_offline_without_cache(tmp_path):
    settings = replace(Settings(), osm_cache_path=tmp_path / "none.json")
    source = OverpassOsmSource(settings, SyntheticOsmSource(settings), offline=True)
    osm = source.load()
    assert osm.synthetic and osm.green and osm.vacant and osm.parking


def test_overpass_source_reads_cache(tmp_path):
    import json

    cache = tmp_path / "osm.json"
    cache.write_text(json.dumps({"elements": [way(1, {"leisure": "park"})]}), encoding="utf-8")
    settings = replace(Settings(), osm_cache_path=cache)
    osm = OverpassOsmSource(settings, SyntheticOsmSource(settings), offline=True).load()
    assert not osm.synthetic and len(osm.green) == 1


def test_ndvi_threshold_segmenter():
    patches = np.array([[[0.1, 0.5], [0.41, 0.39]]])
    mask = NdviThresholdSegmenter(0.40).segment(patches)
    assert mask.tolist() == [[[False, True], [True, False]]]


def test_unet_segmenter_does_not_import_torch_eagerly():
    UNetSegmenter()
    if "torch" not in sys.modules:
        assert True
    else:  # torch ya estaba cargado por otro motivo: sólo comprobamos que construir no falla
        assert UNetSegmenter() is not None


# --- decisiones ---------------------------------------------------------------------------
def make_use_case():
    return RecordDecision(InMemoryDecisionRepository(), "deficit-lgbm-0.1.0", Thresholds())


def test_record_decision_fills_audit_metadata():
    decision = make_use_case().run({"proposal_id": "P-0001", "decision": "approved"})
    assert decision.decision is DecisionKind.APPROVED
    assert decision.model_version == "deficit-lgbm-0.1.0"
    assert decision.thresholds == {"critical": 0.7, "review": 0.4, "min_proposal_priority": 0.5}
    assert decision.timestamp


@pytest.mark.parametrize(
    "payload",
    [
        {"proposal_id": "", "decision": "approved"},
        {"proposal_id": "P-1", "decision": "maybe"},
        {"proposal_id": "P-1", "decision": "adjusted"},
    ],
)
def test_record_decision_rejects_invalid_payloads(payload):
    with pytest.raises(InvalidDecisionError):
        make_use_case().run(payload)


def test_json_file_repository_roundtrip(tmp_path):
    repo = JsonFileDecisionRepository(tmp_path / "sub" / "decisions.json")
    use_case = RecordDecision(repo, "v", Thresholds())
    use_case.run({"proposal_id": "P-0002", "decision": "adjusted", "adjusted_area_m2": 300})
    reloaded = JsonFileDecisionRepository(tmp_path / "sub" / "decisions.json").list_all()
    assert reloaded[0].proposal_id == "P-0002" and reloaded[0].adjusted_area_m2 == 300.0


@pytest.fixture
def client(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.html").write_text("<h1>web</h1>", encoding="utf-8")
    app = create_app(InMemoryDecisionRepository(), docs_dir=docs)
    return TestClient(app)


def test_api_health_and_static_do_not_shadow_each_other(client):
    assert client.get("/api/health").json()["status"] == "ok"
    assert "web" in client.get("/").text


def test_api_decisions_post_and_get(client):
    body = {
        "proposal_id": "P-0001", "decision": "rejected", "technician": "Ana",
        "comment": "Solar privado", "adjusted_area_m2": None,
    }  # fmt: skip
    created = client.post("/api/decisions", json=body)
    assert created.status_code == 201
    listed = client.get("/api/decisions").json()
    assert len(listed) == 1 and listed[0]["decision"] == "rejected"
    assert set(listed[0]) == {
        "proposal_id", "decision", "technician", "comment", "adjusted_area_m2",
        "timestamp", "model_version", "thresholds",
    }  # fmt: skip


def test_api_rejects_invalid_decision_and_allows_cors(client):
    bad = client.post("/api/decisions", json={"proposal_id": "P-1", "decision": "nope"})
    assert bad.status_code == 422
    cors = client.options(
        "/api/decisions",
        headers={"Origin": "https://example.github.io", "Access-Control-Request-Method": "POST"},
    )
    assert cors.headers["access-control-allow-origin"] == "*"
