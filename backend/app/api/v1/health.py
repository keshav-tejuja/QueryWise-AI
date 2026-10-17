import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.db.session import check_database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def live() -> dict[str, str]:
    """Liveness: the process is up. Never touches dependencies."""
    return {"status": "live"}


@router.get("/ready")
def ready():
    """Readiness: the app can serve traffic, i.e. the application database is reachable."""
    try:
        check_database()
    except Exception:
        # Log the exception type only; connection errors can contain host/user details.
        logger.exception("Readiness check failed: application database unreachable")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "unavailable"},
        )
    return {"status": "ready", "database": "ok"}