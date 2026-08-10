"""FastAPI application skeleton for NPC Wars server."""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from server.db import init_db
from server.logging_setup import configure_logging
from server.middleware.security_headers import SecurityHeadersMiddleware
from server.middleware.session import SessionMiddleware
from server.queue import init_backend
from server.routes import ALL_ROUTERS

_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Make the API's own runtime state legible in the container logs.

    uvicorn only configures its own loggers, so without configure_logging()
    every ``server.*`` INFO record is dropped. init_backend() then pins which
    queue backend this process got: if the app quietly used an in-process
    queue while the worker used Redis, submissions would 202 and never run
    (UP-5 P3). In strict mode it raises here and the container fails to boot,
    which is the loud failure we want.
    """
    configure_logging()
    _logger.info("Results dir: %s | DB: %s", app.state.results_dir, app.state.db_path)
    init_backend()
    yield


app = FastAPI(title="NPC Wars Server", lifespan=lifespan)

# Must match the worker's RESULTS_DIR: both containers mount the same volume,
# and a submission match written by the worker is only readable through
# /api/match/{id}, /api/match/{id}/stream and /api/leaderboard if the API
# looks in the same directory.
app.state.results_dir = os.environ.get("RESULTS_DIR", "results")

_db_path = os.environ.get("DB_PATH", "data/npcwars.db")
app.state.db_path = _db_path
app.state.db = init_db(_db_path)
for _router in ALL_ROUTERS:
    app.include_router(_router)

_static_dir = Path(__file__).resolve().parent / "static"
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

_viewer_dir = Path(__file__).resolve().parent.parent / "viewer"
if _viewer_dir.is_dir():
    app.mount("/static/viewer", StaticFiles(directory=str(_viewer_dir)), name="viewer")

_cors_origins = os.environ.get(
    "NPCWARS_CORS_ORIGINS", "http://localhost:8000,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)
app.add_middleware(SessionMiddleware)
app.add_middleware(SecurityHeadersMiddleware)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
