"""FastAPI application skeleton for NPC Wars server."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from server.db import init_db
from server.middleware.session import SessionMiddleware
from server.routes.bots import router as bots_router
from server.routes.health import router as health_router
from server.routes.lobby import router as lobby_router
from server.routes.pages import router as pages_router
from server.routes.match import router as match_router
from server.routes.share import router as share_router
from server.routes.stats import router as stats_router
from server.routes.stream import router as stream_router
from server.routes.submit import router as submit_router

app = FastAPI(title="NPC Wars Server")
app.state.results_dir = "results"
app.state.db = init_db(os.environ.get("DB_PATH", ":memory:"))
app.include_router(bots_router)
app.include_router(health_router)
app.include_router(lobby_router)
app.include_router(match_router)
app.include_router(pages_router)
app.include_router(share_router)
app.include_router(stats_router)
app.include_router(stream_router)
app.include_router(submit_router)

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
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
