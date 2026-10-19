from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from app.core.config import settings


class VaultError(Exception):
    pass


class CredentialVault:
    """Authenticated encryption (Fernet: AES-128-CBC + HMAC-SHA256) with key rotation.

    The FIRST key encrypts; every key can decrypt. To rotate, put a new key first.
    """

    def __init__(self, keys: list[str]) -> None:
        if not keys:
            raise ValueError("At least one Fernet key is required.")
        try:
            self._fernet = MultiFernet([Fernet(key.encode()) for key in keys])
        except (ValueError, TypeError):
            raise ValueError("FERNET_KEYS contains an invalid key (expected 32 URL-safe base64 bytes).") from None

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, token: str) -> str:
        try:
            return self._fernet.decrypt(token.encode()).decode()
        except InvalidToken:
            raise VaultError("Cannot decrypt value.") from None

    def rotate(self, token: str) -> str:
        """Re-encrypt an existing token with the primary (first) key."""
        try:
            return self._fernet.rotate(token.encode()).decode()
        except InvalidToken:
            raise VaultError("Cannot decrypt value.") from None


@lru_cache
def get_vault() -> CredentialVault:
    return CredentialVault(settings.fernet_key_list)