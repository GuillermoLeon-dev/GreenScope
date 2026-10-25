"""Entidades del dominio. Sin dependencias de infraestructura."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Classification(StrEnum):
    """Clasificación de una celda según los umbrales fijados por el técnico."""

    CRITICAL = "critico"
    REVIEW = "revisar"
    OK = "ok"


class ProposalKind(StrEnum):
    """Tipos de parcela candidata a parque de bolsillo."""

    SOLAR_VACANTE = "solar_vacante"
    APARCAMIENTO = "aparcamiento"
    INTERBLOQUE = "interbloque"
    CHAFLAN = "chaflan"
    CALLE_PACIFICABLE = "calle_pacificable"


KIND_LABELS: dict[ProposalKind, str] = {
    ProposalKind.SOLAR_VACANTE: "Solar vacante",
    ProposalKind.APARCAMIENTO: "Aparcamiento en superficie",
    ProposalKind.INTERBLOQUE: "Espacio interbloque",
    ProposalKind.CHAFLAN: "Chaflán",
    ProposalKind.CALLE_PACIFICABLE: "Calle pacificable",
}


class DecisionKind(StrEnum):
    """Resolución del técnico sobre una propuesta."""

    APPROVED = "approved"
    REJECTED = "rejected"
    ADJUSTED = "adjusted"
    PENDING = "pending"


@dataclass(frozen=True)
class Thresholds:
    """Umbrales configurables por el técnico (human-in-the-loop)."""

    critical: float = 0.70
    review: float = 0.40
    min_proposal_priority: float = 0.50

    def __post_init__(self) -> None:
        if not (0.0 <= self.review < self.critical <= 1.0):
            raise ValueError("Se exige 0 <= review < critical <= 1")
        if not 0.0 <= self.min_proposal_priority <= 1.0:
            raise ValueError("min_proposal_priority debe estar en [0, 1]")

    def as_dict(self) -> dict[str, float]:
        return {
            "critical": self.critical,
            "review": self.review,
            "min_proposal_priority": self.min_proposal_priority,
        }


@dataclass(frozen=True)
class Factor:
    """Contribución (SHAP normalizada) de una variable al déficit de una celda."""

    feature: str
    contribution: float


@dataclass
class Cell:
    """Celda H3 con sus features y la salida del modelo."""

    h3: str
    district: str
    population: int
    floating_population: int
    green_m2_per_capita: float
    dist_green_m: float
    canopy_pct: float
    ndvi_mean: float
    ndvi_trend: float
    lst_c: float
    vulnerability: float
    deficit_score: float = 0.0
    uncertainty: float = 0.0
    anomaly: bool = False
    top_factors: list[Factor] = field(default_factory=list)


@dataclass
class Proposal:
    """Parque de bolsillo candidato. La geometría es un anillo [lon, lat]."""

    id: str
    h3: str
    kind: ProposalKind
    area_m2: float
    ring: tuple[tuple[float, float], ...]
    priority_score: float
    served_population: int
    est_cost_eur: int
    est_cooling_c: float
    co2_kg_year: float
    rationale: str
    source: str

    @property
    def kind_label(self) -> str:
        return KIND_LABELS[self.kind]


@dataclass(frozen=True)
class Decision:
    """Registro auditable de la decisión del técnico (alimenta el active learning)."""

    proposal_id: str
    decision: DecisionKind
    technician: str
    comment: str
    adjusted_area_m2: float | None
    timestamp: str
    model_version: str
    thresholds: dict[str, float]
