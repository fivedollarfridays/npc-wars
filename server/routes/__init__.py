"""Server route modules.

Exposes every router as one ordered tuple so ``server/app.py`` registers the
whole surface with a single import instead of thirteen. Adding a route module
means adding it here, not editing the app factory.
"""

from fastapi import APIRouter

from server.routes.badges import router as badges_router
from server.routes.bots import router as bots_router
from server.routes.cosmetics import router as cosmetics_router
from server.routes.health import router as health_router
from server.routes.lobby import router as lobby_router
from server.routes.match import router as match_router
from server.routes.pages import router as pages_router
from server.routes.rival import router as rival_router
from server.routes.share import router as share_router
from server.routes.stats import router as stats_router
from server.routes.stream import router as stream_router
from server.routes.submit import router as submit_router
from server.routes.tournament import router as tournament_router

#: Registration order is the original app.py order (alphabetical by module).
ALL_ROUTERS: tuple[APIRouter, ...] = (
    badges_router,
    bots_router,
    cosmetics_router,
    health_router,
    lobby_router,
    match_router,
    pages_router,
    rival_router,
    share_router,
    stats_router,
    stream_router,
    submit_router,
    tournament_router,
)

__all__ = ["ALL_ROUTERS"]
