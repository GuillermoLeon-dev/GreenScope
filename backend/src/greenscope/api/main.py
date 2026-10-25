"""API FastAPI opcional: registro de decisiones y servidor estático de `docs/`."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from greenscope.application.decisions import InvalidDecisionError, RecordDecision
from greenscope.application.ports import DecisionRepository
from greenscope.config import MODEL_VERSION, Settings
from greenscope.domain.entities import Decision
from greenscope.infrastructure.repositories import JsonFileDecisionRepository


class DecisionIn(BaseModel):
    """Esquema de entrada = registro de decisiones del contrato (sección 7)."""

    proposal_id: str = Field(min_length=1)
    decision: str
    technician: str = ""
    comment: str = ""
    adjusted_area_m2: float | None = None
    timestamp: str | None = None
    model_version: str | None = None
    thresholds: dict[str, float] | None = None


def _to_json(decision: Decision) -> dict[str, Any]:
    record = asdict(decision)
    record["decision"] = decision.decision.value
    return record


def create_app(
    repository: DecisionRepository | None = None,
    docs_dir: Path | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    """Fábrica de la aplicación (inyectable para tests)."""
    settings = settings or Settings()
    repository = repository or JsonFileDecisionRepository(settings.decisions_path)
    use_case = RecordDecision(repository, MODEL_VERSION, settings.thresholds)
    app = FastAPI(title="GreenScope API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "model_version": MODEL_VERSION}

    @app.get("/api/decisions")
    def list_decisions() -> list[dict[str, Any]]:
        return [_to_json(d) for d in use_case.list_all()]

    @app.post("/api/decisions", status_code=201)
    def create_decision(body: DecisionIn) -> dict[str, Any]:
        try:
            return _to_json(use_case.run(body.model_dump()))
        except InvalidDecisionError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    static_dir = docs_dir or settings.docs_dir
    if static_dir.exists():  # debe registrarse después de /api para no taparlo
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="docs")
    return app


app = create_app()
