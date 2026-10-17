from typing import Annotated

from fastapi import APIRouter, Cookie, Response

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.errors import AppError
from app.schemas.auth import LoginRequest, RegisterRequest, TokenOut, UserOut
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "qw_refresh"
COOKIE_PATH = "/api/v1/auth"  # the browser only sends this cookie to auth endpoints


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=raw_token,
        max_age=settings.refresh_token_days * 86400,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path=COOKIE_PATH,
    )


def _token_response(user, issued: auth_service.IssuedTokens, response: Response) -> TokenOut:
    _set_refresh_cookie(response, issued.refresh_token)
    return TokenOut(
        access_token=issued.access_token,
        expires_in=issued.expires_in,
        user=UserOut.model_validate(user),
    )


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: RegisterRequest, db: DbSession):
    return auth_service.register_user(db, body.email, body.password, body.display_name)


@router.post("/login", response_model=TokenOut)
def login(body: LoginRequest, response: Response, db: DbSession):
    user = auth_service.authenticate(db, body.email, body.password)
    issued = auth_service.issue_tokens(db, user)
    return _token_response(user, issued, response)


@router.post("/refresh", response_model=TokenOut)
def refresh(
    response: Response,
    db: DbSession,
    refresh_cookie: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
):
    if not refresh_cookie:
        raise AppError("not_authenticated", "Authentication required.", 401)
    user, issued = auth_service.rotate_refresh_token(db, refresh_cookie)
    return _token_response(user, issued, response)


@router.post("/logout", status_code=204)
def logout(
    db: DbSession,
    refresh_cookie: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
):
    if refresh_cookie:
        auth_service.revoke_refresh_token(db, refresh_cookie)
    response = Response(status_code=204)
    response.delete_cookie(REFRESH_COOKIE, path=COOKIE_PATH)
    return response


@router.get("/me", response_model=UserOut)
def me(current_user: CurrentUser):
    return current_user