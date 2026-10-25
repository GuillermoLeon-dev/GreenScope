"""Caso de uso GenerateProposals: candidatas -> propuestas priorizadas y explicadas."""

from __future__ import annotations

import h3
import numpy as np
import pandas as pd
from shapely.geometry.polygon import orient

from verdescope.application.candidates import Candidate, osm_candidates, synthetic_candidates
from verdescope.application.models import Grid, OsmFeatures
from verdescope.config import Settings
from verdescope.domain import rules
from verdescope.domain.entities import Cell, Proposal
from verdescope.domain.labels import FEATURE_LABELS

SERVED_MIN_ACCESS_GAIN_DISTANCE_FRACTION = 0.5  # por debajo de 150 m ya hay acceso


def format_es_int(value: int) -> str:
    """Entero con separador de miles español (punto)."""
    return f"{value:,}".replace(",", ".")


def format_es_decimal(value: float, decimals: int) -> str:
    """Decimal con coma española."""
    return f"{value:.{decimals}f}".replace(".", ",")


def build_rationale(proposal_kind_label: str, cell: Cell, p: Proposal) -> str:
    """Explicación legible en español, generada por plantilla a partir de los factores."""
    drivers = [FEATURE_LABELS[f.feature].lower() for f in cell.top_factors if f.contribution > 0][
        :2
    ]
    drivers_txt = " y ".join(drivers) if drivers else "varios factores combinados"
    return (
        f"{proposal_kind_label} de {p.area_m2:.0f} m² en {cell.district}: la celda tiene un "
        f"déficit de verde de {format_es_decimal(cell.deficit_score, 2)} "
        f"(factores clave: {drivers_txt}). "
        f"Daría acceso a espacio verde a unas {format_es_int(p.served_population)} personas "
        f"a menos de 300 m, con un enfriamiento local estimado de "
        f"{format_es_decimal(p.est_cooling_c, 1)} °C "
        f"y un coste aproximado de {format_es_int(p.est_cost_eur)} €."
    )


class GenerateProposals:
    """Genera, puntúa y ordena parques de bolsillo candidatos."""

    def __init__(self, settings: Settings) -> None:
        self._s = settings

    def run(
        self, grid: Grid, osm: OsmFeatures, cells: list[Cell], green_union_xy
    ) -> list[Proposal]:
        a = self._s.proposals
        frame = pd.DataFrame([c.__dict__ for c in cells]).set_index("h3")
        by_id = {c.h3: c for c in cells}
        candidates = osm_candidates(grid, osm, a) + synthetic_candidates(
            grid, frame["deficit_score"], green_union_xy, self._s.thresholds.review, a, self._s.seed
        )
        located = [(c, self._locate(c, grid, by_id)) for c in candidates]
        located = [(c, loc) for c, loc in located if loc is not None]
        located.sort(key=lambda item: item[1]["sort_key"])
        proposals = [
            self._build(f"P-{i:04d}", c, loc, grid, frame, by_id)
            for i, (c, loc) in enumerate(located, start=1)
        ]
        kept = [p for p in proposals if p.priority_score >= a.export_priority_floor]
        return sorted(kept, key=lambda p: p.id)

    def _locate(self, cand: Candidate, grid: Grid, by_id: dict[str, Cell]) -> dict | None:
        centroid = cand.geom.centroid
        lon, lat = grid.projector.to_lonlat(centroid.x, centroid.y)
        cell_id = h3.latlng_to_cell(float(lat), float(lon), self._s.h3_resolution)
        if cell_id not in by_id:
            return None
        key = (round(float(lat), 5), round(float(lon), 5), cand.kind.value)
        return {"h3": cell_id, "centroid": centroid, "sort_key": key}

    def _build(
        self,
        pid: str,
        cand: Candidate,
        loc: dict,
        grid: Grid,
        frame: pd.DataFrame,
        by_id: dict[str, Cell],
    ) -> Proposal:
        a = self._s.proposals
        cell = by_id[loc["h3"]]
        area = float(cand.geom.area)
        served = self._served_population(loc["centroid"], grid, frame)
        cost = rules.estimate_cost_eur(cand.kind, area, a)
        lst_norm = float(rules.heat_norm(np.array([cell.lst_c]), self._s.refs)[0])
        priority = rules.priority_score(
            cell.deficit_score, served, lst_norm, cell.vulnerability, cost, self._s.priority
        )
        ring = self._ring_lonlat(cand.geom, grid)
        proposal = Proposal(
            id=pid,
            h3=cell.h3,
            kind=cand.kind,
            area_m2=round(area, 1),
            ring=ring,
            priority_score=round(priority, 3),
            served_population=served,
            est_cost_eur=cost,
            est_cooling_c=rules.estimate_cooling_c(cand.kind, area, a),
            co2_kg_year=rules.estimate_co2_kg_year(area, a),
            rationale="",
            source=cand.source,
        )
        proposal.rationale = build_rationale(proposal.kind_label, cell, proposal)
        return proposal

    def _served_population(self, centroid, grid: Grid, frame: pd.DataFrame) -> int:
        """Residentes + flotantes ponderados en el radio que ganan acceso (>150 m del verde)."""
        a, refs = self._s.proposals, self._s.refs
        circle = centroid.buffer(a.served_radius_m)
        near = np.hypot(grid.x - centroid.x, grid.y - centroid.y) <= a.served_radius_m * 2
        total = 0.0
        for i in np.flatnonzero(near):
            poly = grid.polygons[i]
            share = poly.intersection(circle).area / poly.area
            if share <= 0:
                continue
            row = frame.iloc[i]
            gain = np.clip(
                (
                    row["dist_green_m"]
                    - refs.access_radius_m * SERVED_MIN_ACCESS_GAIN_DISTANCE_FRACTION
                )
                / (refs.access_radius_m * (1 - SERVED_MIN_ACCESS_GAIN_DISTANCE_FRACTION)),
                0.0,
                1.0,
            )
            demand = row["population"] + refs.floating_weight * row["floating_population"]
            total += share * gain * demand
        return int(round(total))

    @staticmethod
    def _ring_lonlat(geom, grid: Grid) -> tuple[tuple[float, float], ...]:
        lonlat = orient(grid.projector.geom_to_lonlat(geom), sign=1.0)
        return tuple((round(x, 5), round(y, 5)) for x, y in lonlat.exterior.coords)
