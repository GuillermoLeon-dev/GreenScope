"""Nombres legibles (español) de las variables del modelo."""

from __future__ import annotations

FEATURE_COLUMNS: tuple[str, ...] = (
    "green_m2_per_capita",
    "dist_green_m",
    "canopy_pct",
    "ndvi_mean",
    "ndvi_trend",
    "lst_c",
    "vulnerability",
    "population",
    "floating_population",
)

FEATURE_LABELS: dict[str, str] = {
    "green_m2_per_capita": "m² verde/hab",
    "dist_green_m": "Distancia al verde (m)",
    "canopy_pct": "Cobertura vegetal (%)",
    "ndvi_mean": "NDVI medio",
    "ndvi_trend": "Tendencia NDVI (por año)",
    "lst_c": "Temperatura superficial (°C)",
    "vulnerability": "Vulnerabilidad socioeconómica",
    "population": "Población residente",
    "floating_population": "Población flotante",
}
