"""Adaptadores de persistencia y de escritura de artefactos."""

from __future__ import annotations

import json
import threading
from dataclasses import asdict
from pathlib import Path
from typing import Any

from greenscope.domain.entities import Decision, DecisionKind


class JsonFileDecisionRepository:
    """Repositorio de decisiones en un fichero JSON (demo). En producción: PostGIS."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()

    def add(self, decision: Decision) -> None:
        with self._lock:
            records = self._read()
            records.append(_to_record(decision))
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
            )

    def list_all(self) -> list[Decision]:
        with self._lock:
            return [_from_record(r) for r in self._read()]

    def _read(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        return json.loads(self._path.read_text(encoding="utf-8") or "[]")


def _to_record(decision: Decision) -> dict[str, Any]:
    record = asdict(decision)
    record["decision"] = decision.decision.value
    return record


def _from_record(record: dict[str, Any]) -> Decision:
    return Decision(**{**record, "decision": DecisionKind(record["decision"])})


class InMemoryDecisionRepository:
    """Repositorio en memoria (tests)."""

    def __init__(self) -> None:
        self._items: list[Decision] = []

    def add(self, decision: Decision) -> None:
        self._items.append(decision)

    def list_all(self) -> list[Decision]:
        return list(self._items)


class JsonArtifactWriter:
    """Escribe JSON compacto (UTF-8) bajo un directorio base (p. ej. `docs/`)."""

    def __init__(self, base_dir: Path) -> None:
        self._base = base_dir

    def write_json(self, relative_path: str, payload: Any) -> int:
        target = self._base / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        target.write_text(text, encoding="utf-8")
        return target.stat().st_size
