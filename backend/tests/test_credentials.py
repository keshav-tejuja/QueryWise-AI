import uuid

import pytest
from cryptography.fernet import Fernet

from app.connections.credentials import CredentialError, open_password, seal_password
from app.models.connection import DbConnection
from app.security.vault import CredentialVault

FIELDS = {"host": "db.example.com", "port": 5432, "database": "sales", "username": "reader"}


@pytest.fixture()
def vault():
    return CredentialVault([Fernet.generate_key().decode()])


def _row(vault, **overrides) -> DbConnection:
    connection_id = uuid.uuid4()
    sealed = seal_password(vault, connection_id=connection_id, password="pw-123", **FIELDS)
    kwargs = {"id": connection_id, "password_encrypted": sealed, **FIELDS}
    kwargs.update(overrides)
    return DbConnection(**kwargs)


def test_password_roundtrips(vault):
    assert open_password(vault, _row(vault)) == "pw-123"


@pytest.mark.parametrize(
    "override",
    [
        {"host": "evil.example.com"},
        {"port": 5433},
        {"database": "other"},
        {"username": "admin"},
        {"id": uuid.uuid4()},
    ],
)
def test_changing_any_bound_column_makes_password_unreadable(vault, override):
    with pytest.raises(CredentialError):
        open_password(vault, _row(vault, **override))


def test_garbage_ciphertext_is_unreadable(vault):
    with pytest.raises(CredentialError):
        open_password(vault, _row(vault, password_encrypted="not-a-token"))


def test_wrong_key_is_unreadable(vault):
    row = _row(vault)
    other = CredentialVault([Fernet.generate_key().decode()])
    with pytest.raises(CredentialError):
        open_password(other, row)