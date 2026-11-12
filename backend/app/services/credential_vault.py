"""Secure Credential Vault using Authenticated Encryption (Fernet).

Provides encryption, decryption, and safe masking for target authentication credentials.
Enforces that raw credentials are never persisted in plaintext, logged, or returned via API.
"""

import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

logger = logging.getLogger("api_sentinel.credential_vault")


class CredentialVaultError(RuntimeError):
    """Raised when encryption or decryption fails, or encryption key is missing/invalid."""
    pass


def _get_fernet_cipher(override_key: Optional[str] = None) -> Fernet:
    """Retrieve initialized Fernet cipher using configured TARGET_CREDENTIAL_ENCRYPTION_KEY."""
    raw_key = override_key if override_key is not None else settings.TARGET_CREDENTIAL_ENCRYPTION_KEY
    if not raw_key or not str(raw_key).strip():
        raise CredentialVaultError(
            "TARGET_CREDENTIAL_ENCRYPTION_KEY is not configured in environment or .env. "
            "Credential encryption requires a valid 32-byte url-safe base64 Fernet key."
        )

    clean_key = str(raw_key).strip()
    try:
        key_bytes = clean_key.encode("utf-8")
        decoded = base64.urlsafe_b64decode(key_bytes)
        if len(decoded) != 32:
            raise ValueError(f"Fernet key must decode to exactly 32 bytes (got {len(decoded)})")
        return Fernet(key_bytes)
    except Exception as err:
        raise CredentialVaultError(f"Invalid TARGET_CREDENTIAL_ENCRYPTION_KEY: {str(err)}")


def encrypt_credential(plaintext: str, key: Optional[str] = None) -> str:
    """Encrypt sensitive credential using Fernet authenticated encryption."""
    if not plaintext:
        return ""
    cipher = _get_fernet_cipher(override_key=key)
    try:
        encrypted_bytes = cipher.encrypt(plaintext.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")
    except Exception as err:
        raise CredentialVaultError(f"Credential encryption failed: {str(err)}")


def decrypt_credential(ciphertext: str, key: Optional[str] = None) -> str:
    """Decrypt credential ciphertext. Used strictly internally during scan execution."""
    if not ciphertext:
        return ""
    cipher = _get_fernet_cipher(override_key=key)
    try:
        decrypted_bytes = cipher.decrypt(ciphertext.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except InvalidToken:
        raise CredentialVaultError("Failed to decrypt credential: Invalid encryption token or mismatching key.")
    except Exception as err:
        raise CredentialVaultError(f"Credential decryption failed: {str(err)}")


def mask_credential(val: str, auth_type: str = "bearer") -> str:
    """Generate safe masked string for display (e.g. 'ey...9aB2'). Never reveals full string."""
    if not val:
        return "Not configured"

    clean = val.strip()
    if len(clean) <= 8:
        return "****"

    if auth_type == "bearer" and clean.lower().startswith("bearer "):
        token = clean[7:].strip()
        if len(token) > 8:
            return f"Bearer {token[:4]}...{token[-4:]}"
        return "Bearer ****"

    # Standard prefix + suffix masking
    prefix = clean[:4]
    suffix = clean[-4:]
    return f"{prefix}...{suffix}"
