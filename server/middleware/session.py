"""Session middleware — assigns a session cookie to every request."""

import logging
import os
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

_logger = logging.getLogger(__name__)

COOKIE_NAME = "npcwars_session"
COOKIE_MAX_AGE = 86400 * 30  # 30 days


class SessionMiddleware(BaseHTTPMiddleware):
    """Assign a session token cookie if one is not already present."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        token = request.cookies.get(COOKIE_NAME)
        is_new = token is None
        if is_new:
            token = uuid.uuid4().hex

        request.state.session_token = token
        response = await call_next(request)

        if is_new:
            _secure = os.environ.get("NPCWARS_SECURE_COOKIES", "1") != "0"
            if not _secure:
                _logger.warning(
                    "Secure cookies disabled via NPCWARS_SECURE_COOKIES=0. "
                    "Only use this for local development."
                )
            response.set_cookie(
                key=COOKIE_NAME,
                value=token,
                max_age=COOKIE_MAX_AGE,
                httponly=True,
                samesite="lax",
                secure=_secure,
            )

        return response
