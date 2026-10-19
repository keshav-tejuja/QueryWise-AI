import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.connection import SchemaSnapshot


def latest(db: Session, connection_id: uuid.UUID) -> SchemaSnapshot | None:
    return db.scalar(
        select(SchemaSnapshot)
        .where(SchemaSnapshot.connection_id == connection_id)
        .order_by(SchemaSnapshot.captured_at.desc())
        .limit(1)
    )


def add(db: Session, connection_id: uuid.UUID, schema_hash: str, payload: dict[str, Any]) -> SchemaSnapshot:
    snapshot = SchemaSnapshot(connection_id=connection_id, schema_hash=schema_hash, payload=payload)
    db.add(snapshot)
    db.flush()
    return snapshot


def prune(db: Session, connection_id: uuid.UUID, keep: int = 5) -> None:
    old_ids = list(
        db.scalars(
            select(SchemaSnapshot.id)
            .where(SchemaSnapshot.connection_id == connection_id)
            .order_by(SchemaSnapshot.captured_at.desc())
            .offset(keep)
        )
    )
    if old_ids:
        db.execute(delete(SchemaSnapshot).where(SchemaSnapshot.id.in_(old_ids)))