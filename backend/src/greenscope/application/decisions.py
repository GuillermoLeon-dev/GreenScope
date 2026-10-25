"""Caso de uso RecordDecision: valida y registra la decisión del técnico."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from greenscope.application.ports import DecisionRepository
from greenscope.domain.entities import Decision, DecisionKind, Thresholds


class InvalidDecisionError(ValueError):
    """La decisión recibida no cumple el contrato."""


class RecordDecision:
    """Registra decisiones completando metadatos de auditoría (fecha, modelo, umbrales)."""

    def __init__(
        self,
        repository: DecisionRepository,
        model_version: str,
        thresholds: Thresholds,
    ) -> None:
        self._repository = repository
        self._model_version = model_version
        self._thresholds = thresholds

    def run(self, payload: dict[str, Any]) -> Decision:
        decision = self._parse(payload)
        self._repository.add(decision)
        return decision

    def list_all(self) -> list[Decision]:
        return self._repository.list_all()

    def _parse(self, p: dict[str, Any]) -> Decision:
        proposal_id = str(p.get("proposal_id") or "").strip()
        if not proposal_id:
            raise InvalidDecisionError("proposal_id es obligatorio")
        try:
            kind = DecisionKind(p.get("decision"))
        except ValueError as exc:
            valid = ", ".join(k.value for k in DecisionKind)
            raise InvalidDecisionError(f"decision debe ser una de: {valid}") from exc
        adjusted = p.get("adjusted_area_m2")
        if kind is DecisionKind.ADJUSTED and (adjusted is None or float(adjusted) <= 0):
            raise InvalidDecisionError("adjusted_area_m2 > 0 es obligatorio si decision=adjusted")
        return Decision(
            proposal_id=proposal_id,
            decision=kind,
            technician=str(p.get("technician") or ""),
            comment=str(p.get("comment") or ""),
            adjusted_area_m2=None if adjusted is None else float(adjusted),
            timestamp=str(p.get("timestamp") or datetime.now().astimezone().isoformat()),
            model_version=str(p.get("model_version") or self._model_version),
            thresholds=dict(p.get("thresholds") or self._thresholds.as_dict()),
        )
