import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.connection import DbConnection


def list_for_user(db: Session, user_id: uuid.UUID) -> list[DbConnection]:
    return list(
        db.scalars(
            select(DbConnection).where(DbConnection.user_id == user_id).order_by(DbConnection.created_at)
        )
    )


def get_for_user(db: Session, user_id: uuid.UUID, connection_id: uuid.UUID) -> DbConnection | None:
    # Ownership is part of the query itself, so another user's row is simply "not found".
    return db.scalar(
        select(DbConnection).where(DbConnection.id == connection_id, DbConnection.user_id == user_id)
    )


def get_by_name(db: Session, user_id: uuid.UUID, name: str) -> DbConnection | None:
    return db.scalar(
        select(DbConnection).where(
            DbConnection.user_id == user_id, func.lower(DbConnection.name) == name.lower()
        )
    )


def add(db: Session, connection: DbConnection) -> None:
    db.add(connection)
    db.flush()


def delete(db: Session, connection: DbConnection) -> None:
    db.delete(connection)