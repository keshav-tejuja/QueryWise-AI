from fastapi import APIRouter

from app.api.v1 import auth, connections, health, schema

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(connections.router)
api_router.include_router(schema.router)