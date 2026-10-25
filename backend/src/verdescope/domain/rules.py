"""Reglas puras del dominio: clasificación por umbrales y scoring multicriterio."""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np

from verdescope.domain.entities import Classification, ProposalKind, Thresholds
from verdescope.domain.policies import (
    DeficitWeights,
    PriorityWeights,
    ProposalAssumptions,
    ReferenceStandards,
)

Arrays = Mapping[str, np.ndarray]


def classify(score: float, thresholds: Thresholds) -> Classification:
    """Crítico si score >= critical; revisar si >= review; si no, ok."""
    if score >= thresholds.critical:
        return Classification.CRITICAL
    if score >= thresholds.review:
        return Classification.REVIEW
    return Classification.OK


def _unit(x: np.ndarray) -> np.ndarray:
    return np.clip(x, 0.0, 1.0)


def _arr(f: Arrays, name: str) -> np.ndarray:
    return np.asarray(f[name], dtype=float)


def demand_population(
    population: np.ndarray, floating: np.ndarray, floating_weight: float
) -> np.ndarray:
    """Población equivalente de demanda: residentes + flotantes ponderados."""
    return population + floating_weight * floating


def heat_norm(lst_c: np.ndarray, refs: ReferenceStandards) -> np.ndarray:
    """LST estival normalizada a [0, 1] entre 'fresca' y 'extrema'."""
    return _unit((lst_c - refs.lst_cool_c) / (refs.lst_hot_c - refs.lst_cool_c))


def deficit_components(f: Arrays, refs: ReferenceStandards) -> dict[str, np.ndarray]:
    """Cada componente normalizado a [0, 1] donde 1 = peor situación."""
    demand = demand_population(
        _arr(f, "population"), _arr(f, "floating_population"), refs.floating_weight
    )
    return {
        "green_per_capita": 1.0 - _unit(_arr(f, "green_m2_per_capita") / refs.who_m2_per_capita),
        "access": _unit(_arr(f, "dist_green_m") / (2.0 * refs.access_radius_m)),
        "canopy": 1.0 - _unit(_arr(f, "canopy_pct") / refs.canopy_target_pct),
        "heat": heat_norm(_arr(f, "lst_c"), refs),
        "vulnerability": _unit(_arr(f, "vulnerability")),
        "demand": _unit(demand / refs.demand_ref),
        "degradation": _unit(-_arr(f, "ndvi_trend") / refs.trend_ref),
    }


def composite_deficit_index(
    f: Arrays, weights: DeficitWeights, refs: ReferenceStandards
) -> np.ndarray:
    """Índice compuesto ponderado en [0, 1] (1 = máximo déficit)."""
    comps = deficit_components(f, refs)
    w = {k: getattr(weights, k) for k in comps}
    total = sum(w.values())
    return _unit(sum(w[k] * comps[k] for k in comps) / total)


def weak_critical_label(f: Arrays, refs: ReferenceStandards) -> np.ndarray:
    """Etiqueta débil de 'déficit crítico' (OMS 9 m²/hab, 300 m, 30 % de copas).

    Crítico si incumple los tres criterios con calor alto, o dos con calor extremo.
    No es verdad-terreno: es supervisión débil por reglas.
    """
    v_green = _arr(f, "green_m2_per_capita") < refs.who_m2_per_capita
    v_access = _arr(f, "dist_green_m") > refs.access_radius_m
    v_canopy = _arr(f, "canopy_pct") < refs.canopy_target_pct
    n_violations = v_green.astype(int) + v_access.astype(int) + v_canopy.astype(int)
    heat = heat_norm(_arr(f, "lst_c"), refs)
    return ((n_violations >= 3) & (heat >= 0.5)) | ((n_violations >= 2) & (heat >= 0.8))


def priority_score(
    deficit: float,
    served_population: float,
    lst_norm: float,
    vulnerability: float,
    cost_eur: float,
    w: PriorityWeights,
) -> float:
    """Ranking multicriterio de una propuesta en [0, 1] (1 = más prioritaria)."""
    served = min(served_population / w.served_population_ref, 1.0)
    cost_eff = 1.0 - min(cost_eur / w.cost_ref_eur, 1.0)
    total_w = w.deficit + w.served_population + w.heat + w.vulnerability + w.cost_efficiency
    score = (
        w.deficit * deficit
        + w.served_population * served
        + w.heat * lst_norm
        + w.vulnerability * vulnerability
        + w.cost_efficiency * cost_eff
    ) / total_w
    return float(min(max(score, 0.0), 1.0))


def estimate_cost_eur(kind: ProposalKind, area_m2: float, a: ProposalAssumptions) -> int:
    """Coste = superficie x €/m² del tipo de actuación (redondeado a 100 €)."""
    return int(round(area_m2 * a.cost_eur_per_m2[kind], -2))


def estimate_cooling_c(kind: ProposalKind, area_m2: float, a: ProposalAssumptions) -> float:
    """Enfriamiento local = máx x (1 - exp(-A/escala)) x factor del tipo (°C)."""
    saturation = 1.0 - math.exp(-area_m2 / a.cooling_area_scale_m2)
    return round(a.cooling_max_c * saturation * a.cooling_kind_factor[kind], 2)


def estimate_co2_kg_year(area_m2: float, a: ProposalAssumptions) -> float:
    """CO2 anual = superficie x fracción con copa x captura por m² de copa."""
    return round(area_m2 * a.canopy_fraction_new * a.co2_kg_per_m2_canopy_year, 1)
