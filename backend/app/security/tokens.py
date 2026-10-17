import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings

ALGORITHM = "HS256"


class InvalidTokenError(Exception):
    pass


def create_access_token(user_id: uuid.UUID) -> tuple[str, int]:
    """Return (jwt, lifetime_seconds)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
        "typ": "access",
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    return token, settings.access_token_minutes * 60


def decode_access_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "iat", "sub"]},
        )
        if payload.get("typ") != "access":
            raise InvalidTokenError("wrong token type")
        return uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError) as exc:
        raise InvalidTokenError("invalid token") from exc


def hash_refresh_token(raw: str) -> str:
    # SHA-256 is appropriate here: the token is 384 bits of randomness, not a human password.
    return hashlib.sha256(raw.encode()).hexdigest()


def new_refresh_token() -> tuple[str, str]:
    """Return (raw_token_for_cookie, hash_for_database)."""
    raw = secrets.token_urlsafe(48)
    return raw, hash_refresh_token(raw)