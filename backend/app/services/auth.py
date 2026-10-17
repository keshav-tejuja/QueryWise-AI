from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppError
from app.models.user import User
from app.repositories import users
from app.security.passwords import DUMMY_HASH, hash_password, needs_rehash, verify_password
from app.security.tokens import create_access_token, hash_refresh_token, new_refresh_token


@dataclass
class IssuedTokens:
    access_token: str
    expires_in: int
    refresh_token: str  # raw value, destined for the httpOnly cookie only


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _email_taken() -> AppError:
    return AppError("email_taken", "An account with this email already exists.", 409)


def _invalid_refresh() -> AppError:
    return AppError("invalid_refresh_token", "Session expired. Please sign in again.", 401)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register_user(db: Session, email: str, password: str, display_name: str) -> User:
    email = normalize_email(email)
    if users.get_user_by_email(db, email):
        raise _email_taken()
    try:
        user = users.create_user(
            db, email=email, password_hash=hash_password(password), display_name=display_name
        )
        db.commit()
    except IntegrityError:  # two simultaneous registrations for the same email
        db.rollback()
        raise _email_taken() from None
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = users.get_user_by_email(db, normalize_email(email))
    # Always run one Argon2 verification so response time doesn't reveal whether the email exists.
    password_ok = verify_password(user.password_hash if user else DUMMY_HASH, password)
    if user is None or not password_ok:
        raise AppError("invalid_credentials", "Invalid email or password.", 401)
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
        db.commit()
    return user


def issue_tokens(db: Session, user: User) -> IssuedTokens:
    access_token, expires_in = create_access_token(user.id)
    raw, token_hash = new_refresh_token()
    users.add_refresh_token(
        db,
        user_id=user.id,
        token_hash=token_hash,
        expires_at=_now() + timedelta(days=settings.refresh_token_days),
    )
    db.commit()
    return IssuedTokens(access_token, expires_in, raw)


def rotate_refresh_token(db: Session, raw_token: str) -> tuple[User, IssuedTokens]:
    record = users.get_refresh_token(db, hash_refresh_token(raw_token))
    if record is None:
        raise _invalid_refresh()
    now = _now()
    if record.revoked_at is not None:
        # A revoked token was presented again: it may have been stolen. Kill every session.
        users.revoke_all_for_user(db, record.user_id, now)
        db.commit()
        raise _invalid_refresh()
    if record.expires_at <= now:
        raise _invalid_refresh()
    user = users.get_user_by_id(db, record.user_id)
    if user is None:
        raise _invalid_refresh()
    record.revoked_at = now
    return user, issue_tokens(db, user)  # commits the revocation and the new token together


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    record = users.get_refresh_token(db, hash_refresh_token(raw_token))
    if record is not None and record.revoked_at is None:
        record.revoked_at = _now()
        db.commit()