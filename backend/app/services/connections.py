import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.connections.credentials import CredentialError, open_password, seal_password
from app.connections.tester import CheckResult, TargetParams, check_connection
from app.core.errors import AppError
from app.models.connection import DbConnection
from app.models.user import User
from app.repositories import connections as repo
from app.schemas.connections import ConnectionCreate, ConnectionUpdate
from app.security.vault import get_vault

_UNREADABLE = "Saved credentials can't be decrypted. Re-enter the password."


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _name_taken() -> AppError:
    return AppError("connection_name_taken", "You already have a connection with this name.", 409)


def _owned(db: Session, user: User, connection_id: uuid.UUID) -> DbConnection:
    connection = repo.get_for_user(db, user.id, connection_id)
    if connection is None:
        raise AppError("connection_not_found", "Connection not found.", 404)
    return connection


def _ensure_name_free(db: Session, user: User, name: str, exclude_id: uuid.UUID | None = None) -> None:
    existing = repo.get_by_name(db, user.id, name)
    if existing is not None and existing.id != exclude_id:
        raise _name_taken()


def _require_ok(params: TargetParams) -> CheckResult:
    check = check_connection(params)
    if not check.ok:
        raise AppError(check.code, check.message, 400)
    return check


def list_connections(db: Session, user: User) -> list[DbConnection]:
    return repo.list_for_user(db, user.id)


def get_connection(db: Session, user: User, connection_id: uuid.UUID) -> DbConnection:
    return _owned(db, user, connection_id)


def create_connection(db: Session, user: User, data: ConnectionCreate) -> tuple[DbConnection, CheckResult]:
    _ensure_name_free(db, user, data.name)
    params = TargetParams(
        host=data.host,
        port=data.port,
        database=data.database,
        username=data.username,
        password=data.password,
        ssl_mode=data.ssl_mode,
    )
    check = _require_ok(params)  # verify connectivity BEFORE saving anything

    connection_id = uuid.uuid4()
    connection = DbConnection(
        id=connection_id,
        user_id=user.id,
        name=data.name,
        host=data.host,
        port=data.port,
        database=data.database,
        username=data.username,
        password_encrypted=seal_password(
            get_vault(),
            connection_id=connection_id,
            host=data.host,
            port=data.port,
            database=data.database,
            username=data.username,
            password=data.password,
        ),
        key_version=1,
        ssl_mode=data.ssl_mode,
        status="connected",
        last_tested_at=_now(),
    )
    try:
        repo.add(db, connection)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _name_taken() from None
    return connection, check


def update_connection(
    db: Session, user: User, connection_id: uuid.UUID, data: ConnectionUpdate
) -> tuple[DbConnection, CheckResult | None]:
    connection = _owned(db, user, connection_id)
    changes = data.model_dump(exclude_none=True)

    if "name" in changes:
        _ensure_name_free(db, user, changes["name"], exclude_id=connection.id)

    target_fields = ("host", "port", "database", "username", "ssl_mode")
    target_changed = any(
        field in changes and changes[field] != getattr(connection, field) for field in target_fields
    )
    check: CheckResult | None = None

    if target_changed or "password" in changes:
        password = changes.get("password")
        if password is None:
            try:
                password = open_password(get_vault(), connection)
            except CredentialError:
                raise AppError("credentials_unreadable", _UNREADABLE, 409) from None
        host = changes.get("host", connection.host)
        port = changes.get("port", connection.port)
        database = changes.get("database", connection.database)
        username = changes.get("username", connection.username)
        ssl_mode = changes.get("ssl_mode", connection.ssl_mode)

        # Test first: a failed edit must leave the saved connection untouched.
        check = _require_ok(
            TargetParams(host=host, port=port, database=database, username=username, password=password, ssl_mode=ssl_mode)
        )
        connection.host, connection.port = host, port
        connection.database, connection.username = database, username
        connection.ssl_mode = ssl_mode
        connection.password_encrypted = seal_password(
            get_vault(),
            connection_id=connection.id,
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
        )
        connection.status = "connected"
        connection.last_tested_at = _now()

    if "name" in changes:
        connection.name = changes["name"]

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _name_taken() from None
    return connection, check


def test_saved_connection(db: Session, user: User, connection_id: uuid.UUID) -> tuple[DbConnection, CheckResult]:
    connection = _owned(db, user, connection_id)
    try:
        password = open_password(get_vault(), connection)
    except CredentialError:
        check = CheckResult(False, "credentials_unreadable", _UNREADABLE)
    else:
        check = check_connection(
            TargetParams(
                host=connection.host,
                port=connection.port,
                database=connection.database,
                username=connection.username,
                password=password,
                ssl_mode=connection.ssl_mode,
            )
        )
    connection.status = "connected" if check.ok else "error"
    connection.last_tested_at = _now()
    db.commit()
    return connection, check


def disconnect_connection(db: Session, user: User, connection_id: uuid.UUID) -> DbConnection:
    connection = _owned(db, user, connection_id)
    connection.status = "disconnected"
    db.commit()
    return connection


def delete_connection(db: Session, user: User, connection_id: uuid.UUID) -> None:
    connection = _owned(db, user, connection_id)
    repo.delete(db, connection)
    db.commit()