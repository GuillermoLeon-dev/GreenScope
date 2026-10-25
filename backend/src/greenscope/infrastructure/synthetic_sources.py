"""Conectores sintéticos deterministas, coherentes espacialmente con la capa OSM.

Sustituyen a Sentinel-2, Landsat LST, INE y Smart Steps mientras no haya acceso real.
Cada fuente usa su propia semilla derivada de `Settings.seed` (reproducible e independiente
del orden de ejecución).
"""

from __future__ import annotations

import json
from importlib import resources

import numpy as np
import pandas as pd
import shapely

from greenscope.application.models import SourceContext
from greenscope.config import Settings

MONTHS_IN_YEAR = 12
NDVI_RANGE = (-0.1, 0.95)
SOL_LAT_LON = (40.4168, -3.7038)
# Polos de actividad (lat, lon, amplitud de población flotante, radio m)
ACTIVITY_HOTSPOTS = (
    (40.4168, -3.7038, 9000.0, 650.0),  # Puerta del Sol
    (40.4200, -3.7050, 8000.0, 600.0),  # Gran Vía
    (40.4460, -3.6920, 7000.0, 900.0),  # Castellana / Nuevos Ministerios
    (40.4065, -3.6895, 5500.0, 500.0),  # Atocha
    (40.4660, -3.6890, 5000.0, 700.0),  # Plaza de Castilla
    (40.4300, -3.6790, 5000.0, 700.0),  # Salamanca comercial
)


def smooth_field(
    x: np.ndarray, y: np.ndarray, rng: np.random.Generator, scale_m: float, n_waves: int = 6
) -> np.ndarray:
    """Campo aleatorio suave (suma de ondas) normalizado a media 0 y desviación 1."""
    field = np.zeros_like(x, dtype=float)
    for _ in range(n_waves):
        angle = rng.uniform(0, 2 * np.pi)
        wavelength = scale_m * rng.uniform(0.6, 1.6)
        phase = rng.uniform(0, 2 * np.pi)
        field += np.sin(2 * np.pi * (x * np.cos(angle) + y * np.sin(angle)) / wavelength + phase)
    return (field - field.mean()) / (field.std() + 1e-9)


def _months_numbers(months: list[str]) -> np.ndarray:
    return np.array([int(m[5:7]) for m in months])


def _years_since_start(months: list[str]) -> np.ndarray:
    return np.arange(len(months)) / MONTHS_IN_YEAR


def _winter_weight(month_numbers: np.ndarray) -> np.ndarray:
    """1 en enero, 0 en julio."""
    return 0.5 * (1.0 + np.cos(2 * np.pi * (month_numbers - 1) / MONTHS_IN_YEAR))


class SyntheticSentinel2Source:
    """NDVI mensual sintético: más NDVI dentro de parques, estacionalidad, degradación, nubes."""

    id = "s2"
    name = "Sentinel-2 L2A NDVI"
    kind = "raster-timeseries"
    synthetic = True

    N_HOTSPOTS = 5
    HOTSPOT_SIGMA_M = 350.0
    HOTSPOT_RATE = (0.012, 0.030)  # pérdida NDVI/año en el centro de la zona degradada
    HOTSPOT_MIN_WEIGHT = 0.15
    GREEN_NDVI = (0.55, 0.14)  # media y desviación dentro de parques
    URBAN_NDVI = (0.18, 0.22, 0.10)  # base, coef. arbolado, desviación fuera de parques
    CLOUD_P = (0.05, 0.10)  # prob. base y extra invernal de hueco por nubes
    NOISE_SD, NOISE_PHI = 0.02, 0.5

    def __init__(self, settings: Settings) -> None:
        self._s = settings

    def ndvi_patches(self, ctx: SourceContext) -> np.ndarray:
        """Parches NDVI (n, P, P) del año reciente; dentro de parques el NDVI es alto."""
        rng = np.random.default_rng(self._s.seed + 10)
        grid, p = ctx.grid, self._s.patch_size
        offsets = (np.arange(p) - (p - 1) / 2) * self._s.patch_pixel_m
        ox, oy = np.meshgrid(offsets, offsets)
        xs = grid.x[:, None, None] + ox[None]
        ys = grid.y[:, None, None] + oy[None]
        if not ctx.green_union_xy.is_empty:
            shapely.prepare(ctx.green_union_xy)
            inside = shapely.contains_xy(ctx.green_union_xy, xs.ravel(), ys.ravel()).reshape(
                xs.shape
            )
        else:
            inside = np.zeros(xs.shape, bool)
        tree_field = np.clip(
            0.35
            + 0.2 * smooth_field(grid.x, grid.y, rng, 1200.0)
            + 0.1 * rng.normal(size=len(grid)),
            0.0,
            1.0,
        )
        base, coef, sd = self.URBAN_NDVI
        urban = rng.normal(base + coef * tree_field[:, None, None], sd, size=xs.shape)
        green = rng.normal(self.GREEN_NDVI[0], self.GREEN_NDVI[1], size=xs.shape)
        return np.clip(np.where(inside, green, urban), *NDVI_RANGE)

    def fetch(self, ctx: SourceContext) -> pd.DataFrame:
        rng = np.random.default_rng(self._s.seed + 11)
        grid, months = ctx.grid, ctx.months
        n, t = len(grid), len(months)
        patches = self.ndvi_patches(ctx)
        base = patches.mean(axis=(1, 2))
        green_frac = ctx.stats["green_frac"].to_numpy()
        month_no, years = _months_numbers(months), _years_since_start(months)
        season = np.cos(2 * np.pi * (month_no - 4.5) / MONTHS_IN_YEAR)  # pico abril-mayo
        amp = 0.04 + 0.10 * green_frac
        slope = self._trend_per_year(ctx, rng)
        centered_years = years - years.mean()
        ndvi = (
            base[:, None]
            + amp[:, None] * season[None]
            + slope[:, None] * centered_years[None]
            + self._ar_noise(rng, n, t)
        )
        ndvi = np.clip(ndvi, *NDVI_RANGE)
        cloud_p = self.CLOUD_P[0] + self.CLOUD_P[1] * _winter_weight(month_no)
        ndvi[rng.random((n, t)) < cloud_p[None]] = np.nan
        return pd.DataFrame(ndvi, index=pd.Index(grid.h3_ids, name="h3"), columns=months)

    def _trend_per_year(self, ctx: SourceContext, rng: np.random.Generator) -> np.ndarray:
        """Pendiente por celda: ligera deriva aleatoria + zonas verdes en degradación."""
        grid = ctx.grid
        slope = rng.normal(0.0, 0.003, size=len(grid))
        green_cells = np.flatnonzero(ctx.stats["green_frac"].to_numpy() > 0.25)
        if len(green_cells) == 0:
            return slope
        centers = rng.choice(
            green_cells, size=min(self.N_HOTSPOTS, len(green_cells)), replace=False
        )
        for c in centers:
            dist2 = (grid.x - grid.x[c]) ** 2 + (grid.y - grid.y[c]) ** 2
            weight = np.exp(-dist2 / (2 * self.HOTSPOT_SIGMA_M**2))
            weight[weight < self.HOTSPOT_MIN_WEIGHT] = 0.0
            slope -= weight * rng.uniform(*self.HOTSPOT_RATE)
        return slope

    def _ar_noise(self, rng: np.random.Generator, n: int, t: int) -> np.ndarray:
        eps = rng.normal(0.0, self.NOISE_SD, size=(n, t))
        out = np.zeros((n, t))
        out[:, 0] = eps[:, 0]
        for k in range(1, t):
            out[:, k] = self.NOISE_PHI * out[:, k - 1] + eps[:, k]
        return out


class SyntheticLstSource:
    """LST mensual sintética: efecto isla de calor, enfriada por el NDVI, estacional."""

    id = "lst"
    name = "Landsat 8/9 LST"
    kind = "raster-timeseries"
    synthetic = True

    BASE_C, AMP_C, PEAK_MONTH = 21.0, 13.0, 7.3
    UHI_C = 10.0  # calentamiento máximo por superficie impermeable en verano
    UHI_WINTER_FRACTION = 0.35
    NDVI_BARE, NDVI_FULL = 0.10, 0.60
    NOISE_C = 1.2
    CLOUD_P = (0.08, 0.07)

    def __init__(self, settings: Settings) -> None:
        self._s = settings

    def fetch(self, ctx: SourceContext) -> pd.DataFrame:
        rng = np.random.default_rng(self._s.seed + 20)
        grid, months = ctx.grid, ctx.months
        n, t = len(grid), len(months)
        month_no = _months_numbers(months)
        season = np.cos(2 * np.pi * (month_no - self.PEAK_MONTH) / MONTHS_IN_YEAR)
        ndvi = ctx.ndvi.to_numpy() if ctx.ndvi is not None else np.full((n, t), 0.25)
        row_mean = np.nanmean(ndvi, axis=1, keepdims=True)
        ndvi = np.where(np.isnan(ndvi), row_mean, ndvi)
        vegetation = np.clip((ndvi - self.NDVI_BARE) / (self.NDVI_FULL - self.NDVI_BARE), 0.0, 1.0)
        summer = np.clip((season + 0.2) / 1.2, 0.0, 1.0)
        uhi = (
            self.UHI_C
            * (1.0 - vegetation)
            * (self.UHI_WINTER_FRACTION + (1 - self.UHI_WINTER_FRACTION) * summer[None])
        )
        local = smooth_field(grid.x, grid.y, rng, 2000.0)
        lst = (
            self.BASE_C
            + self.AMP_C * season[None]
            + uhi
            + 0.8 * local[:, None]
            + rng.normal(0.0, self.NOISE_C, size=(n, t))
        )
        cloud_p = self.CLOUD_P[0] + self.CLOUD_P[1] * _winter_weight(month_no)
        lst[rng.random((n, t)) < cloud_p[None]] = np.nan
        return pd.DataFrame(lst, index=pd.Index(grid.h3_ids, name="h3"), columns=months)


def load_districts() -> list[dict]:
    """Distritos de Madrid (centroides aproximados) empaquetados con el código."""
    text = resources.files("greenscope.infrastructure.data").joinpath("districts_madrid.json")
    return json.loads(text.read_text(encoding="utf-8"))["districts"]


def assign_districts(lat: np.ndarray, lon: np.ndarray) -> list[str]:
    """Distrito por centroide más cercano (aproximación en grados corregida por latitud)."""
    districts = load_districts()
    d_lat = np.array([d["lat"] for d in districts])
    d_lon = np.array([d["lon"] for d in districts])
    cos_lat = np.cos(np.radians(np.mean(lat)))
    dist2 = (lat[:, None] - d_lat[None]) ** 2 + ((lon[:, None] - d_lon[None]) * cos_lat) ** 2
    return [districts[i]["name"] for i in dist2.argmin(axis=1)]


class SyntheticIneSource:
    """Padrón y vulnerabilidad sintéticos: más población en el centro, menos en parques."""

    id = "ine"
    name = "INE padrón + vulnerabilidad"
    kind = "tabular"
    synthetic = True

    CORE_DENSITY, BASE_DENSITY, DECAY_M = 21_000.0, 3_000.0, 3_500.0  # hab/km²
    GREEN_DISPLACEMENT = 0.97
    DENSITY_LOGNORMAL_SD = 0.25
    VULN_BASE, VULN_SOUTH, VULN_FIELD, VULN_NOISE = 0.35, 0.25, 0.10, 0.05
    SOUTH_REF_LAT, SOUTH_SPAN_DEG = 40.43, 0.06

    def __init__(self, settings: Settings) -> None:
        self._s = settings

    def fetch(self, ctx: SourceContext) -> pd.DataFrame:
        rng = np.random.default_rng(self._s.seed + 30)
        grid = ctx.grid
        cx, cy = grid.projector.to_xy(SOL_LAT_LON[1], SOL_LAT_LON[0])
        dist = np.hypot(grid.x - cx, grid.y - cy)
        density = self.BASE_DENSITY + self.CORE_DENSITY * np.exp(-dist / self.DECAY_M)
        density *= 1.0 - self.GREEN_DISPLACEMENT * ctx.stats["green_frac"].to_numpy()
        density *= rng.lognormal(0.0, self.DENSITY_LOGNORMAL_SD, size=len(grid))
        population = (density * grid.area_m2 / 1e6).round().astype(int)
        south = np.clip((self.SOUTH_REF_LAT - grid.lat) / self.SOUTH_SPAN_DEG, 0.0, 1.0)
        vuln = (
            self.VULN_BASE
            + self.VULN_SOUTH * south
            + self.VULN_FIELD * smooth_field(grid.x, grid.y, rng, 1800.0)
            + rng.normal(0.0, self.VULN_NOISE, size=len(grid))
        )
        return pd.DataFrame(
            {
                "district": assign_districts(grid.lat, grid.lon),
                "population": population,
                "vulnerability": np.clip(vuln, 0.0, 1.0),
            },
            index=pd.Index(grid.h3_ids, name="h3"),
        )


class SyntheticSmartStepsSource:
    """Población flotante sintética: alta en Sol, Gran Vía y Castellana."""

    id = "smartsteps"
    name = "Movilidad agregada de operador (sintético, tipo Smart Steps)"
    kind = "mobility"
    synthetic = True

    BASE_FLOATING = 150.0
    PARK_ATTRACTION = 400.0  # los grandes parques atraen visitantes
    NOISE_SD = 0.2

    def __init__(self, settings: Settings) -> None:
        self._s = settings

    def fetch(self, ctx: SourceContext) -> pd.DataFrame:
        rng = np.random.default_rng(self._s.seed + 40)
        grid = ctx.grid
        floating = np.full(len(grid), self.BASE_FLOATING)
        for lat, lon, amplitude, radius in ACTIVITY_HOTSPOTS:
            hx, hy = grid.projector.to_xy(lon, lat)
            dist2 = (grid.x - hx) ** 2 + (grid.y - hy) ** 2
            floating += amplitude * np.exp(-dist2 / (2 * radius**2))
        floating += self.PARK_ATTRACTION * ctx.stats["green_frac"].to_numpy()
        floating *= rng.lognormal(0.0, self.NOISE_SD, size=len(grid))
        return pd.DataFrame(
            {"floating_population": floating.round().astype(int)},
            index=pd.Index(grid.h3_ids, name="h3"),
        )
