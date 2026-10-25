"""Conectores reales (stubs) tras la interfaz `DataSource`; desactivados por configuración.

Se activan con `Settings.sources` y requieren credenciales/extras opcionales
(`uv sync --extra stac`). Los imports pesados son perezosos.
"""

from __future__ import annotations

import pandas as pd

from greenscope.application.models import SourceContext

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
S2_COLLECTION = "sentinel-2-l2a"
MAX_CLOUD_COVER_PCT = 30
INE_API_URL = "https://servicios.ine.es/wstempus/js/ES"


class ConnectorDisabledError(RuntimeError):
    """El conector real está desactivado por configuración."""


class StacSentinel2Source:
    """NDVI mensual real desde Sentinel-2 L2A en Microsoft Planetary Computer (STAC)."""

    id = "s2"
    name = "Sentinel-2 L2A NDVI"
    kind = "raster-timeseries"
    synthetic = False

    def __init__(self, enabled: bool = False) -> None:
        self._enabled = enabled

    def fetch(self, context: SourceContext) -> pd.DataFrame:
        if not self._enabled:
            raise ConnectorDisabledError("StacSentinel2Source desactivado (Settings.sources)")
        import planetary_computer  # noqa: F401  (import perezoso, extra 'stac')
        import pystac_client

        catalog = pystac_client.Client.open(STAC_URL)
        west, south, east, north = (
            context.grid.lon.min(),
            context.grid.lat.min(),
            context.grid.lon.max(),
            context.grid.lat.max(),
        )
        search = catalog.search(
            collections=[S2_COLLECTION],
            bbox=[west, south, east, north],
            datetime=f"{context.months[0]}-01/{context.months[-1]}-28",
            query={"eo:cloud_cover": {"lt": MAX_CLOUD_COVER_PCT}},
        )
        items = list(search.items())
        raise NotImplementedError(
            f"{len(items)} escenas encontradas; falta muestrear B04/B08 por celda H3 "
            "(odc-stac + mediana mensual enmascarada con SCL)."
        )

    def ndvi_patches(self, context: SourceContext):  # pragma: no cover - stub
        raise NotImplementedError("Recorte de parches B04/B08 pendiente de implementar")


class IneApiSource:
    """Padrón por sección censal desde el API del INE (reparto a celdas H3 por área)."""

    id = "ine"
    name = "INE padrón + vulnerabilidad"
    kind = "tabular"
    synthetic = False

    def __init__(self, enabled: bool = False) -> None:
        self._enabled = enabled

    def fetch(self, context: SourceContext) -> pd.DataFrame:
        if not self._enabled:
            raise ConnectorDisabledError("IneApiSource desactivado (Settings.sources)")
        raise NotImplementedError(
            f"Consultar {INE_API_URL} y repartir secciones censales a H3 ponderando por área"
        )


class SmartStepsApiSource:
    """Movilidad agregada y anonimizada de Telefónica Tech Smart Steps (API de pago)."""

    id = "smartsteps"
    name = "Telefónica Tech Smart Steps"
    kind = "mobility"
    synthetic = False

    def __init__(self, enabled: bool = False, api_key: str | None = None) -> None:
        self._enabled = enabled
        self._api_key = api_key

    def fetch(self, context: SourceContext) -> pd.DataFrame:
        if not self._enabled or not self._api_key:
            raise ConnectorDisabledError("SmartStepsApiSource desactivado o sin credenciales")
        raise NotImplementedError("Integración con el contrato comercial de Smart Steps pendiente")
