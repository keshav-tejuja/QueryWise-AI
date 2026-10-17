from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.session import get_db
from app.models.user import User
from app.repositories import users
from app.security.tokens import InvalidTokenError, decode_access_token

_bearer = HTTPBearer(auto_error=False)
_WWW_AUTH = {"WWW-Authenticate": "Bearer"}

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: DbSession,
) -> User:
    if credentials is None:
        raise AppError("not_authenticated", "Authentication required.", 401, headers=_WWW_AUTH)
    try:
        user_id = decode_access_token(credentials.credentials)
    except InvalidTokenError:
        raise AppError("invalid_token", "Invalid or expired token.", 401, headers=_WWW_AUTH) from None
    user = users.get_user_by_id(db, user_id)
    if user is None:
        raise AppError("invalid_token", "Invalid or expired token.", 401, headers=_WWW_AUTH)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]