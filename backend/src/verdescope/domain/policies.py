"""Parámetros de política del dominio (pesos, referencias normativas y supuestos).

Son valores de configuración, expresados como dataclasses inmutables para que las reglas
puras del dominio no dependan de la infraestructura.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from verdescope.domain.entities import ProposalKind


@dataclass(frozen=True)
class DeficitWeights:
    """Pesos del índice compuesto. Inspirado en OMS 9 m²/hab y regla 3-30-300."""

    green_per_capita: float = 0.25
    access: float = 0.25
    canopy: float = 0.15
    heat: float = 0.15
    vulnerability: float = 0.10
    demand: float = 0.05
    degradation: float = 0.05


@dataclass(frozen=True)
class ReferenceStandards:
    """Referencias normativas y rangos de normalización."""

    who_m2_per_capita: float = 9.0  # OMS: 9 m² de verde por habitante (mínimo)
    access_radius_m: float = 300.0  # regla 300 m al espacio verde
    canopy_target_pct: float = 30.0  # regla 30 % de copas
    min_park_area_m2: float = 5000.0  # espacio verde >= 0,5 ha
    lst_cool_c: float = 32.0  # LST estival considerada "fresca"
    lst_hot_c: float = 44.0  # LST estival considerada "extrema"
    demand_ref: float = 3000.0  # demanda (hab. equivalentes/celda) que satura el criterio
    trend_ref: float = 0.03  # pendiente NDVI/año que satura el criterio de degradación
    floating_weight: float = 0.5  # peso de la población flotante frente a la residente
    max_m2_per_capita: float = 100.0  # tope del ratio m²/hab (celdas casi sin población)
    min_pop_for_ratio: float = 100.0  # población mínima usada en el ratio m²/hab
    neighbor_green_weight: float = 0.25  # peso del verde de celdas vecinas (accesible)


@dataclass(frozen=True)
class PriorityWeights:
    """Pesos del ranking multicriterio de propuestas."""

    deficit: float = 0.35
    served_population: float = 0.25
    heat: float = 0.15
    vulnerability: float = 0.10
    cost_efficiency: float = 0.15
    served_population_ref: float = 3000.0
    cost_ref_eur: float = 600_000.0


@dataclass(frozen=True)
class ProposalAssumptions:
    """Supuestos (configurables y documentados) de coste, enfriamiento y CO2."""

    cost_eur_per_m2: dict[ProposalKind, float] = field(
        default_factory=lambda: {
            ProposalKind.SOLAR_VACANTE: 180.0,
            ProposalKind.APARCAMIENTO: 260.0,  # incluye desasfaltado
            ProposalKind.INTERBLOQUE: 120.0,
            ProposalKind.CHAFLAN: 220.0,
            ProposalKind.CALLE_PACIFICABLE: 300.0,
        }
    )
    cooling_max_c: float = 2.5  # enfriamiento local máximo de un parque grande
    cooling_area_scale_m2: float = 2000.0  # saturación: 1 - exp(-A/escala)
    cooling_kind_factor: dict[ProposalKind, float] = field(
        default_factory=lambda: {
            ProposalKind.SOLAR_VACANTE: 1.0,
            ProposalKind.APARCAMIENTO: 1.2,  # sustituir asfalto enfría más
            ProposalKind.INTERBLOQUE: 0.9,
            ProposalKind.CHAFLAN: 0.9,
            ProposalKind.CALLE_PACIFICABLE: 1.1,
        }
    )
    canopy_fraction_new: float = 0.6  # fracción del parque que acaba con copa arbórea
    co2_kg_per_m2_canopy_year: float = 1.5  # captura anual por m² de copa (arbolado mixto)
    min_area_m2: float = 150.0
    max_area_m2: float = 5000.0
    served_radius_m: float = 300.0
    export_priority_floor: float = 0.30  # no se exportan candidatas por debajo (tamaño)
    synthetic_extra_score: float = 0.70  # celdas con score >= este valor: candidata extra
    synthetic_kind_weights: dict[ProposalKind, float] = field(
        default_factory=lambda: {
            ProposalKind.INTERBLOQUE: 0.4,
            ProposalKind.CHAFLAN: 0.3,
            ProposalKind.CALLE_PACIFICABLE: 0.3,
        }
    )
