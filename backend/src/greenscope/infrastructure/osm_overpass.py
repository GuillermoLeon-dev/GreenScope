"""Fuente vectorial real: OpenStreetMap vía Overpass API, con caché y fallback sintético."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests
import shapely
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import polygonize, unary_union

from greenscope.application.models import GeoPolygon, OsmFeatures
from greenscope.application.ports import VectorSource
from greenscope.config import Settings

log = logging.getLogger("greenscope.osm")

USER_AGENT = "GreenScope/0.1 (piloto academico; contacto: guillermoleonae.dev@gmail.com)"
GREEN_LEISURE = {"park": "parque", "garden": "jardin"}
GREEN_LANDUSE = {"grass": "cesped", "recreation_ground": "zona_recreativa"}
VACANT_LANDUSE = {"brownfield", "vacant", "construction"}


def build_query(bbox: tuple[float, float, float, float], timeout_s: int) -> str:
    """Consulta Overpass QL para verde, solares y aparcamientos en superficie."""
    west, south, east, north = bbox
    box = f"({south},{west},{north},{east})"
    return (
        f"[out:json][timeout:{timeout_s}];\n(\n"
        f'  nwr["leisure"~"^(park|garden)$"]{box};\n'
        f'  nwr["landuse"~"^(grass|recreation_ground)$"]{box};\n'
        f'  nwr["landuse"~"^(brownfield|vacant|construction)$"]{box};\n'
        f'  nwr["amenity"="parking"]["parking"="surface"]{box};\n'
        ");\nout geom tags;"
    )


def _ring_from_geometry(points: list[dict[str, float]]) -> list[tuple[float, float]]:
    return [(p["lon"], p["lat"]) for p in points]


def _way_polygon(element: dict[str, Any]) -> BaseGeometry | None:
    ring = _ring_from_geometry(element.get("geometry", []))
    if len(ring) < 4 or ring[0] != ring[-1]:
        return None
    poly = Polygon(ring)
    return poly if poly.is_valid else shapely.make_valid(poly)


def _relation_polygon(element: dict[str, Any]) -> BaseGeometry | None:
    """Ensambla un multipolígono a partir de los miembros outer/inner (polygonize)."""
    lines = {"outer": [], "inner": []}
    for member in element.get("members", []):
        role = member.get("role")
        if member.get("type") == "way" and role in lines and member.get("geometry"):
            lines[role].append(shapely.LineString(_ring_from_geometry(member["geometry"])))
    outers = list(polygonize(unary_union(lines["outer"]))) if lines["outer"] else []
    if not outers:
        return None
    result = unary_union(outers)
    inners = list(polygonize(unary_union(lines["inner"]))) if lines["inner"] else []
    if inners:
        result = result.difference(unary_union(inners))
    return result if result.is_valid else shapely.make_valid(result)


def _element_geometry(element: dict[str, Any]) -> BaseGeometry | None:
    kind = element.get("type")
    geom = _way_polygon(element) if kind == "way" else None
    if kind == "relation":
        geom = _relation_polygon(element)
    if geom is None or geom.is_empty:
        return None
    polygons = [g for g in getattr(geom, "geoms", [geom]) if g.geom_type == "Polygon"]
    if not polygons:
        return None
    return polygons[0] if len(polygons) == 1 else shapely.MultiPolygon(polygons)


def _classify(tags: dict[str, str]) -> tuple[str, str] | None:
    """Devuelve (capa, tipo) o None si el elemento no interesa."""
    if tags.get("access") in {"private", "no"}:
        return None
    if tags.get("leisure") in GREEN_LEISURE:
        return "green", GREEN_LEISURE[tags["leisure"]]
    if tags.get("landuse") in GREEN_LANDUSE:
        return "green", GREEN_LANDUSE[tags["landuse"]]
    if tags.get("landuse") in VACANT_LANDUSE:
        return "vacant", "solar_vacante"
    if tags.get("amenity") == "parking" and tags.get("parking") == "surface":
        return "parking", "aparcamiento"
    return None


def parse_overpass(raw: dict[str, Any]) -> OsmFeatures:
    """Convierte la respuesta JSON de Overpass en capas de polígonos."""
    features = OsmFeatures()
    layers = {"green": features.green, "vacant": features.vacant, "parking": features.parking}
    for element in raw.get("elements", []):
        tags = element.get("tags", {})
        label = _classify(tags)
        if label is None:
            continue
        geom = _element_geometry(element)
        if geom is None:
            continue
        layer, kind = label
        osm_id = f"{element['type'][0]}{element['id']}"
        name = tags.get("name") or ""
        layers[layer].append(GeoPolygon(osm_id, name, kind, geom))
    return features


class OverpassOsmSource:
    """OSM real. Usa la caché si existe; si no descarga y la guarda; si falla, fallback."""

    id = "osm"
    name = "OpenStreetMap (Overpass)"

    def __init__(self, settings: Settings, fallback: VectorSource, offline: bool = False) -> None:
        self._s = settings
        self._fallback = fallback
        self._offline = offline

    def load(self) -> OsmFeatures:
        raw = self._read_cache() or (None if self._offline else self._download())
        if raw is None:
            log.warning("OSM no disponible (sin caché ni red): se usa el fallback sintético")
            return self._fallback.load()
        features = parse_overpass(raw)
        if not features.green:
            log.warning("La respuesta OSM no contiene zonas verdes: fallback sintético")
            return self._fallback.load()
        return features

    def _read_cache(self) -> dict[str, Any] | None:
        path: Path = self._s.osm_cache_path
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            log.warning("Caché OSM ilegible: %s", path)
            return None

    def _download(self) -> dict[str, Any] | None:
        query = build_query(self._s.bbox, self._s.overpass_timeout_s)
        for endpoint in self._s.overpass_endpoints:
            try:
                log.info("Descargando OSM de %s ...", endpoint)
                response = requests.post(
                    endpoint,
                    data={"data": query},
                    headers={"User-Agent": USER_AGENT},
                    timeout=self._s.overpass_timeout_s + 30,
                )
                response.raise_for_status()
                raw = response.json()
            except (requests.RequestException, ValueError) as exc:
                log.warning("Fallo en %s: %s", endpoint, exc)
                continue
            if raw.get("elements"):
                self._write_cache(raw)
                return raw
        return None

    def _write_cache(self, raw: dict[str, Any]) -> None:
        path: Path = self._s.osm_cache_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(raw, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
        )
        log.info("Caché OSM escrita: %s (%.1f MB)", path, path.stat().st_size / 1e6)
