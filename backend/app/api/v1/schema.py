import uuid

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, RateLimitedUser
from app.schema_intel.models import RetrievalResult
from app.schemas.schema_api import RefreshOut, RetrieveRequest, SchemaOut
from app.services import schema as service

router = APIRouter(prefix="/connections/{connection_id}/schema", tags=["schema"])


def _out(loaded: service.LoadedSchema) -> SchemaOut:
    return SchemaOut(
        connection_id=loaded.connection_id,
        schema_hash=loaded.schema_hash,
        captured_at=loaded.captured_at,
        truncated=loaded.data.truncated,
        tables=loaded.data.tables,
    )


@router.get("", response_model=SchemaOut)
def get_schema(connection_id: uuid.UUID, user: CurrentUser, db: DbSession):
    return _out(service.get_schema(db, user, connection_id))


@router.post("/refresh", response_model=RefreshOut)
def refresh_schema(connection_id: uuid.UUID, user: RateLimitedUser, db: DbSession):
    loaded, diff, changed = service.refresh_schema(db, user, connection_id)
    return RefreshOut(snapshot=_out(loaded), changed=changed, diff=diff)


@router.post("/retrieve", response_model=RetrievalResult)
def retrieve(connection_id: uuid.UUID, body: RetrieveRequest, user: CurrentUser, db: DbSession):
    return service.retrieve(db, user, connection_id, body.question, body.max_tables)