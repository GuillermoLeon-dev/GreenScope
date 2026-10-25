"""Reglas puras del dominio: umbrales, índice compuesto, etiquetas débiles y scoring."""

from __future__ import annotations

import numpy as np
import pytest

from verdescope.domain import rules
from verdescope.domain.entities import Classification, ProposalKind, Thresholds
from verdescope.domain.policies import (
    DeficitWeights,
    PriorityWeights,
    ProposalAssumptions,
    ReferenceStandards,
)

REFS = ReferenceStandards()


def features(**overrides):
    base = {
        "green_m2_per_capita": [20.0, 1.0],
        "dist_green_m": [50.0, 700.0],
        "canopy_pct": [40.0, 3.0],
        "lst_c": [33.0, 43.0],
        "vulnerability": [0.1, 0.9],
        "population": [500, 2500],
        "floating_population": [100, 6000],
        "ndvi_trend": [0.0, -0.03],
    }
    base.update(overrides)
    return {k: np.array(v, dtype=float) for k, v in base.items()}


def test_default_thresholds_match_contract():
    t = Thresholds()
    assert (t.critical, t.review, t.min_proposal_priority) == (0.70, 0.40, 0.50)


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.95, Classification.CRITICAL),
        (0.70, Classification.CRITICAL),
        (0.699, Classification.REVIEW),
        (0.40, Classification.REVIEW),
        (0.399, Classification.OK),
        (0.0, Classification.OK),
    ],
)
def test_classify_uses_inclusive_thresholds(score, expected):
    assert rules.classify(score, Thresholds()) is expected


def test_classify_respects_custom_thresholds():
    strict = Thresholds(critical=0.9, review=0.6)
    assert rules.classify(0.8, strict) is Classification.REVIEW


def test_thresholds_reject_inconsistent_values():
    with pytest.raises(ValueError):
        Thresholds(critical=0.3, review=0.5)


def test_composite_index_is_bounded_and_orders_cells():
    index = rules.composite_deficit_index(features(), DeficitWeights(), REFS)
    assert ((index >= 0) & (index <= 1)).all()
    assert index[1] > index[0]
    assert index[1] > 0.85 and index[0] < 0.2


def test_composite_index_weights_are_normalised():
    doubled = DeficitWeights(*(2 * v for v in vars(DeficitWeights()).values()))
    a = rules.composite_deficit_index(features(), DeficitWeights(), REFS)
    b = rules.composite_deficit_index(features(), doubled, REFS)
    np.testing.assert_allclose(a, b)


def test_who_threshold_is_respected_in_components():
    f = features(green_m2_per_capita=[9.0, 4.5])
    comps = rules.deficit_components(f, REFS)
    np.testing.assert_allclose(comps["green_per_capita"], [0.0, 0.5])


def test_weak_label_follows_who_300m_and_canopy_rules():
    f = features()
    labels = rules.weak_critical_label(f, REFS)
    assert labels.tolist() == [False, True]


def test_priority_score_monotonic_in_each_criterion():
    w = PriorityWeights()
    base = rules.priority_score(0.5, 1000, 0.5, 0.5, 100_000, w)
    assert rules.priority_score(0.9, 1000, 0.5, 0.5, 100_000, w) > base
    assert rules.priority_score(0.5, 2000, 0.5, 0.5, 100_000, w) > base
    assert rules.priority_score(0.5, 1000, 0.9, 0.5, 100_000, w) > base
    assert rules.priority_score(0.5, 1000, 0.5, 0.9, 100_000, w) > base
    assert rules.priority_score(0.5, 1000, 0.5, 0.5, 20_000, w) > base  # más barato = mejor


def test_priority_score_is_clamped_to_unit_interval():
    w = PriorityWeights()
    assert rules.priority_score(1, 10**9, 1, 1, 0, w) == pytest.approx(1.0)
    assert rules.priority_score(0, 0, 0, 0, 10**9, w) == pytest.approx(0.0)


def test_cost_uses_per_kind_unit_prices():
    a = ProposalAssumptions()
    assert rules.estimate_cost_eur(ProposalKind.SOLAR_VACANTE, 1000, a) == 180_000
    assert rules.estimate_cost_eur(ProposalKind.APARCAMIENTO, 1000, a) == 260_000
    assert rules.estimate_cost_eur(ProposalKind.INTERBLOQUE, 1000, a) == 120_000
    assert rules.estimate_cost_eur(ProposalKind.CHAFLAN, 1000, a) == 220_000
    assert rules.estimate_cost_eur(ProposalKind.CALLE_PACIFICABLE, 1000, a) == 300_000


def test_cooling_and_co2_grow_with_area_and_saturate():
    a = ProposalAssumptions()
    small = rules.estimate_cooling_c(ProposalKind.SOLAR_VACANTE, 300, a)
    large = rules.estimate_cooling_c(ProposalKind.SOLAR_VACANTE, 5000, a)
    assert 0 < small < large <= a.cooling_max_c
    assert rules.estimate_co2_kg_year(1000, a) == pytest.approx(900.0)
