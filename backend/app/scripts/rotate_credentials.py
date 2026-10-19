"""Re-encrypt every saved database password with the primary (first) key in FERNET_KEYS.

Rotation procedure:
  1. Generate a new key and put it FIRST in FERNET_KEYS, keeping the old key after it.
  2. Restart the backend, then run:  python -m app.scripts.rotate_credentials
  3. Once it reports success, the old key can be removed from FERNET_KEYS.
"""

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.connection import DbConnection
from app.security.vault import VaultError, get_vault


def main() -> None:
    vault = get_vault()
    rotated, failed = 0, 0
    with SessionLocal() as db:
        for connection in db.scalars(select(DbConnection)):
            try:
                connection.password_encrypted = vault.rotate(connection.password_encrypted)
                rotated += 1
            except VaultError:
                failed += 1
        db.commit()
    print(f"Re-encrypted {rotated} connection(s) with the primary key; {failed} could not be decrypted.")


if __name__ == "__main__":
    main()