import logging
import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import request_id_ctx

logger = logging.getLogger("app.request")
_VALID_ID = re.compile(r"^[A-Za-z0-9-]{8,64}$")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        incoming = request.headers.get("x-request-id", "")
        request_id = incoming if _VALID_ID.match(incoming) else uuid.uuid4().hex
        request.state.request_id = request_id
        token = request_id_ctx.set(request_id)
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            level = logging.DEBUG if request.url.path.startswith("/api/v1/health") else logging.INFO
            logger.log(
                level,
                "request completed",
                extra={
                    "extra_fields": {
                        "method": request.method,
                        "path": request.url.path,
                        "status": status,
                        "duration_ms": round((time.perf_counter() - start) * 1000, 1),
                    }
                },
            )
            request_id_ctx.reset(token)