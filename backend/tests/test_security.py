import uuid

import jwt
import pytest

from app.core.config import settings
from app.security.passwords import hash_password, verify_password
from app.security.tokens import (
    ALGORITHM,
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_refresh_token,
    new_refresh_token,
)


def test_password_roundtrip():
    hashed = hash_password("correct horse battery")
    assert hashed != "correct horse battery"
    assert verify_password(hashed, "correct horse battery")
    assert not verify_password(hashed, "wrong password")


def test_same_password_hashes_differently():
    assert hash_password("same-password-1") != hash_password("same-password-1")


def test_access_token_roundtrip():
    user_id = uuid.uuid4()
    token, expires_in = create_access_token(user_id)
    assert expires_in == settings.access_token_minutes * 60
    assert decode_access_token(token) == user_id


def test_tampered_token_rejected():
    token, _ = create_access_token(uuid.uuid4())
    with pytest.raises(InvalidTokenError):
        decode_access_token(token[:-2] + "xx")


def test_expired_token_rejected(monkeypatch):
    monkeypatch.setattr(settings, "access_token_minutes", -1)
    token, _ = create_access_token(uuid.uuid4())
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_wrong_token_type_rejected():
    forged = jwt.encode(
        {"sub": str(uuid.uuid4()), "iat": 1, "exp": 9999999999, "typ": "refresh"},
        settings.secret_key,
        algorithm=ALGORITHM,
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(forged)


def test_refresh_token_hash_matches():
    raw, token_hash = new_refresh_token()
    assert hash_refresh_token(raw) == token_hash
    assert raw != token_hash