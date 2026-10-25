"""Línea de comandos: `greenscope pipeline [--offline]` y `greenscope serve`."""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import replace
from pathlib import Path

from greenscope.bootstrap import build_pipeline
from greenscope.config import Settings


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="greenscope", description="GreenScope: backend y pipeline ML"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    pipe = sub.add_parser("pipeline", help="Ejecuta el pipeline y escribe docs/data/")
    pipe.add_argument(
        "--offline", action="store_true", help="No usar la red (caché OSM o sintético)"
    )
    pipe.add_argument("--out", type=Path, default=None, help="Directorio docs/ de salida")
    serve = sub.add_parser("serve", help="Arranca la API FastAPI (sirve docs/ y /api)")
    serve.add_argument("--port", type=int, default=8000)
    return parser


def _run_pipeline(args: argparse.Namespace) -> int:
    settings = Settings()
    if args.out is not None:
        settings = replace(settings, docs_dir=args.out.resolve())
    result = build_pipeline(settings, offline=args.offline).run()
    total = sum(result.sizes.values())
    print(f"OSM: {'FALLBACK sintético' if result.osm_synthetic else 'real (Overpass/caché)'}")
    print(f"Celdas: {len(result.scoring.cells)}  Propuestas: {len(result.proposals)}")
    print(f"Métricas: { {k: round(v, 3) for k, v in result.metrics.items()} }")
    print(f"Artefactos en {settings.data_dir} ({total / 1e6:.2f} MB): {result.sizes}")
    return 0


def _serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run("greenscope.api.main:app", host="127.0.0.1", port=args.port)
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = _build_parser().parse_args(argv)
    return _run_pipeline(args) if args.command == "pipeline" else _serve(args)


if __name__ == "__main__":
    raise SystemExit(main())
