import uuid

from fastapi import APIRouter, Response

from app.api.deps import CurrentUser, DbSession, RateLimitedUser
from app.connections.tester import CheckResult, TargetParams, check_connection
from app.models.connection import DbConnection
from app.schemas.connections import (
    ConnectionCheckOut,
    ConnectionCreate,
    ConnectionOut,
    ConnectionTestRequest,
    ConnectionUpdate,
    ConnectionWithCheck,
)
from app.services import connections as service

router = APIRouter(prefix="/connections", tags=["connections"])


def _with_check(connection: DbConnection, check: CheckResult | None) -> ConnectionWithCheck:
    return ConnectionWithCheck(
        connection=ConnectionOut.model_validate(connection),
        check=ConnectionCheckOut.model_validate(check) if check is not None else None,
    )


@router.post("/test", response_model=ConnectionCheckOut)
def check_unsaved(body: ConnectionTestRequest, user: RateLimitedUser):
    """Test connection details without saving them. A failed test is a 200 with ok=false."""
    return check_connection(TargetParams(**body.model_dump()))


@router.get("", response_model=list[ConnectionOut])
def list_connections(user: CurrentUser, db: DbSession):
    return service.list_connections(db, user)


@router.post("", response_model=ConnectionWithCheck, status_code=201)
def create_connection(body: ConnectionCreate, user: RateLimitedUser, db: DbSession):
    connection, check = service.create_connection(db, user, body)
    return _with_check(connection, check)


@router.get("/{connection_id}", response_model=ConnectionOut)
def get_connection(connection_id: uuid.UUID, user: CurrentUser, db: DbSession):
    return service.get_connection(db, user, connection_id)


@router.patch("/{connection_id}", response_model=ConnectionWithCheck)
def update_connection(connection_id: uuid.UUID, body: ConnectionUpdate, user: RateLimitedUser, db: DbSession):
    connection, check = service.update_connection(db, user, connection_id, body)
    return _with_check(connection, check)


@router.post("/{connection_id}/test", response_model=ConnectionWithCheck)
def test_saved(connection_id: uuid.UUID, user: RateLimitedUser, db: DbSession):
    connection, check = service.test_saved_connection(db, user, connection_id)
    return _with_check(connection, check)


@router.post("/{connection_id}/disconnect", response_model=ConnectionOut)
def disconnect(connection_id: uuid.UUID, user: CurrentUser, db: DbSession):
    return service.disconnect_connection(db, user, connection_id)


@router.delete("/{connection_id}", status_code=204)
def delete_connection(connection_id: uuid.UUID, user: CurrentUser, db: DbSession):
    service.delete_connection(db, user, connection_id)
    return Response(status_code=204)