import pytest
from cryptography.fernet import Fernet

from app.security.vault import CredentialVault, VaultError


def _key() -> str:
    return Fernet.generate_key().decode()


def test_roundtrip_and_ciphertext_hides_plaintext():
    vault = CredentialVault([_key()])
    token = vault.encrypt("s3cret-password")
    assert "s3cret-password" not in token
    assert vault.decrypt(token) == "s3cret-password"


def test_encrypting_twice_gives_different_ciphertext():
    vault = CredentialVault([_key()])
    assert vault.encrypt("same") != vault.encrypt("same")


def test_wrong_key_cannot_decrypt():
    token = CredentialVault([_key()]).encrypt("pw")
    with pytest.raises(VaultError):
        CredentialVault([_key()]).decrypt(token)


def test_tampered_ciphertext_rejected():
    vault = CredentialVault([_key()])
    token = vault.encrypt("pw")
    tampered = token[:-4] + ("AAAA" if token[-4:] != "AAAA" else "BBBB")
    with pytest.raises(VaultError):
        vault.decrypt(tampered)


def test_rotation_moves_data_to_the_new_primary_key():
    old, new = _key(), _key()
    token = CredentialVault([old]).encrypt("pw")

    rotating = CredentialVault([new, old])
    assert rotating.decrypt(token) == "pw"  # old data stays readable during rotation

    rotated = rotating.rotate(token)
    assert CredentialVault([new]).decrypt(rotated) == "pw"  # no longer needs the old key
    with pytest.raises(VaultError):
        CredentialVault([old]).decrypt(rotated)


def test_invalid_key_rejected():
    with pytest.raises(ValueError):
        CredentialVault(["not-a-valid-key"])
    with pytest.raises(ValueError):
        CredentialVault([])