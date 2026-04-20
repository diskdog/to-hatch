"""ASGI middleware for request tracing."""

from __future__ import annotations

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request and echo it in the response.

    The middleware reads ``X-Request-ID`` from the incoming request headers.
    If absent a UUID4 is generated.  The resolved ID is:

    * Stored in ``request.state.request_id`` for use by route handlers.
    * Bound to the structlog context so all log records within the request
      carry a ``request_id`` field.
    * Written to the ``X-Request-ID`` response header.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request, inject request ID, and forward to the next handler.

        Args:
            request: The incoming ASGI request.
            call_next: Callable that passes the request to the next middleware
                or route handler and returns a :class:`Response`.

        Returns:
            The response from the next handler with ``X-Request-ID`` set.
        """
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
