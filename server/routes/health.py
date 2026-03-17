"""Health check and monitoring endpoints."""

from __future__ import annotations

import os
import shutil
import sqlite3
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


def _check_redis() -> dict:
    """Check Redis connectivity."""
    try:
        from server.queue import _get_backend

        backend = _get_backend()
        backend.ping()
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)[:100]}


def _check_sqlite(request: Request) -> dict:
    """Check SQLite database accessibility."""
    try:
        db_path = getattr(request.app.state, "db_path", "data/npcwars.db")
        conn = sqlite3.connect(db_path)
        conn.execute("SELECT 1")
        conn.close()
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)[:100]}


def _check_disk(request: Request) -> dict:
    """Check available disk space."""
    try:
        results_dir = getattr(request.app.state, "results_dir", "results")
        target = results_dir if os.path.isdir(results_dir) else "."
        usage = shutil.disk_usage(target)
        free_mb = round(usage.free / (1024 * 1024))
        status = "ok" if free_mb > 100 else "warning"
        return {"status": status, "free_mb": free_mb}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)[:100]}


@router.get("/health")
async def health(request: Request) -> dict:
    """Extended health check with component status."""
    checks = {
        "redis": _check_redis(),
        "sqlite": _check_sqlite(request),
        "disk": _check_disk(request),
    }
    all_ok = all(c["status"] == "ok" for c in checks.values())
    return {"status": "ok" if all_ok else "degraded", "components": checks}


@router.get("/health/ready")
async def readiness(request: Request) -> JSONResponse:
    """Lightweight readiness probe for load balancers."""
    health_data = await health(request)
    status_code = 200 if health_data["status"] == "ok" else 503
    return JSONResponse(content=health_data, status_code=status_code)


@router.get("/metrics")
async def metrics(request: Request) -> dict:
    """Return operational metrics."""
    results_dir = getattr(request.app.state, "results_dir", "results")

    match_count = 0
    results_path = Path(results_dir)
    if results_path.is_dir():
        match_count = len(list(results_path.glob("match_*.json")))

    try:
        from server.queue import queue_depth

        depth = queue_depth()
    except Exception:
        depth = 0

    return {
        "match_count": match_count,
        "queue_depth": depth,
    }
