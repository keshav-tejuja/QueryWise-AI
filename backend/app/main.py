import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestContextMiddleware
from app.db.session import engine
from app.security.vault import get_vault   # add with the other imports
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("QueryWise backend starting (env=%s)", settings.app_env)
    yield
    engine.dispose()
    logger.info("QueryWise backend stopped")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("QueryWise backend starting (env=%s)", settings.app_env)
    get_vault()  # fail fast if FERNET_KEYS is invalid
    yield
    engine.dispose()
    logger.info("QueryWise backend stopped")

app = FastAPI(title="QueryWise AI API", version="0.2.0", lifespan=lifespan)
app.add_middleware(RequestContextMiddleware)
register_exception_handlers(app)
app.include_router(api_router, prefix="/api/v1")