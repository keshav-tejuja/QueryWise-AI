import json
import uuid

from app.models.connection import DbConnection
from app.security.vault import CredentialVault, VaultError


class CredentialError(Exception):
    """Saved credentials are unreadable: wrong/lost key, corruption, or tampered columns."""


def seal_password(
    vault: CredentialVault,
    *,
    connection_id: uuid.UUID,
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
) -> str:
    """Encrypt the password TOGETHER with the connection's identity.

    Without this binding, someone who can write to the database could change a row's host to
    a server they control and have the app send the decrypted password there.
    """
    payload = json.dumps(
        {"id": str(connection_id), "host": host, "port": port, "db": database, "user": username, "pw": password},
        separators=(",", ":"),
    )
    return vault.encrypt(payload)


def open_password(vault: CredentialVault, conn: DbConnection) -> str:
    try:
        data = json.loads(vault.decrypt(conn.password_encrypted))
    except (VaultError, ValueError):
        raise CredentialError("unreadable") from None
    expected = {
        "id": str(conn.id),
        "host": conn.host,
        "port": conn.port,
        "db": conn.database,
        "user": conn.username,
    }
    if not isinstance(data, dict) or not isinstance(data.get("pw"), str):
        raise CredentialError("malformed")
    if any(data.get(key) != value for key, value in expected.items()):
        raise CredentialError("context mismatch")
    return data["pw"]