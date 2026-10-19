import logging
import uuid
from dataclasses import dataclass
from datetime import datetime

import psycopg
from sqlalchemy.orm import Session

from app.connections.credentials import CredentialError, open_password
from app.connections.pool_manager import pools
from app.connections.tester import FAILURE_MESSAGES, TargetParams, classify_error
from app.core.errors import AppError
from app.models.user import User
from app.repositories import schema_snapshots as snapshots
from app.schema_intel.introspect import introspect
from app.schema_intel.models import RetrievalResult, SchemaData, SchemaDiff, compute_schema_hash, diff_schemas
from app.schema_intel.retrieval import retrieve_relevant
from app.security.network_guard import NetworkPolicyError
from app.security.vault import get_vault
from app.services.connections import get_connection

logger = logging.getLogger(__name__)


@dataclass
class LoadedSchema:
    connection_id: uuid.UUID
    data: SchemaData
    schema_hash: str
    captured_at: datetime


def _loaded(connection_id: uuid.UUID, snapshot) -> LoadedSchema:
    return LoadedSchema(
        connection_id, SchemaData.model_validate(snapshot.payload), snapshot.schema_hash, snapshot.captured_at
    )


def get_schema(db: Session, user: User, connection_id: uuid.UUID) -> LoadedSchema:
    connection = get_connection(db, user, connection_id)  # ownership check
    snapshot = snapshots.latest(db, connection.id)
    if snapshot is None:
        raise AppError("schema_not_loaded", "The schema hasn't been loaded yet. Refresh it first.", 404)
    return _loaded(connection.id, snapshot)


def refresh_schema(
    db: Session, user: User, connection_id: uuid.UUID
) -> tuple[LoadedSchema, SchemaDiff | None, bool]:
    connection = get_connection(db, user, connection_id)
    if connection.status == "disconnected":
        raise AppError("connection_disconnected", "This connection is disconnected. Reconnect it first.", 409)
    try:
        password = open_password(get_vault(), connection)
    except CredentialError:
        raise AppError(
            "credentials_unreadable", "Saved credentials can't be decrypted. Re-enter the password.", 409
        ) from None

    params = TargetParams(
        host=connection.host, port=connection.port, database=connection.database,
        username=connection.username, password=password, ssl_mode=connection.ssl_mode,
    )
    try:
        with pools.connection(connection.id, params) as pg:
            data = introspect(pg)
    except NetworkPolicyError as exc:
        raise AppError(exc.code, exc.message, 400) from None
    except psycopg.Error as exc:
        pools.discard(connection.id)  # don't keep a pool that may be broken
        code = classify_error(exc)
        logger.warning("Schema introspection failed", extra={"extra_fields": {"code": code}})
        raise AppError(code, FAILURE_MESSAGES[code], 502) from None

    new_hash = compute_schema_hash(data)
    latest = snapshots.latest(db, connection.id)
    if latest is not None and latest.schema_hash == new_hash:
        return _loaded(connection.id, latest), None, False

    diff = diff_schemas(SchemaData.model_validate(latest.payload), data) if latest is not None else None
    snapshot = snapshots.add(db, connection.id, new_hash, data.model_dump(mode="json"))
    snapshots.prune(db, connection.id)
    db.commit()
    db.refresh(snapshot)
    return LoadedSchema(connection.id, data, new_hash, snapshot.captured_at), diff, True


def retrieve(
    db: Session, user: User, connection_id: uuid.UUID, question: str, max_tables: int
) -> RetrievalResult:
    loaded = get_schema(db, user, connection_id)
    return retrieve_relevant(question, loaded.data, max_tables)


def try_initial_snapshot(db: Session, user: User, connection_id: uuid.UUID) -> None:
    """Discover the schema right after a connection is saved. Never fails the caller."""
    try:
        refresh_schema(db, user, connection_id)
    except AppError as exc:
        db.rollback()
        logger.warning("Initial schema discovery failed", extra={"extra_fields": {"code": exc.code}})
    except Exception:
        db.rollback()
        logger.exception("Unexpected error during initial schema discovery")