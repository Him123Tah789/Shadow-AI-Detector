"""
Crypto Utility — Email encryption/decryption + hashing
=======================================================
Uses AES-256-GCM for email encryption at rest.
Uses SHA-256 for email hashing (lookups without decryption).

Config: ENCRYPTION_KEY env var (32-byte base64-encoded key)
"""

import os
import hashlib
import base64
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _get_key() -> bytes:
    """Get or auto-generate encryption key from env."""
    key_b64 = os.getenv("ENCRYPTION_KEY", "")
    if key_b64:
        return base64.b64decode(key_b64)
    # Auto-generate a key for development (NOT for production)
    # In prod, set ENCRYPTION_KEY env var to a stable 32-byte base64 key
    if not hasattr(_get_key, "_dev_key"):
        _get_key._dev_key = AESGCM.generate_key(bit_length=256)
    return _get_key._dev_key


def encrypt_email(email: str) -> str:
    """Encrypt email with AES-256-GCM. Returns base64(nonce + ciphertext)."""
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)  # 96-bit nonce
    ciphertext = aesgcm.encrypt(nonce, email.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt_email(encrypted: str) -> str:
    """Decrypt email from base64(nonce + ciphertext)."""
    key = _get_key()
    raw = base64.b64decode(encrypted)
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


def hash_email(email: str) -> str:
    """One-way SHA-256 hash for dedup/lookup. Normalized to lowercase."""
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


def mask_email(email: str) -> str:
    """Mask email for display: u***r@example.com"""
    parts = email.split("@")
    if len(parts) != 2:
        return "***"
    local = parts[0]
    if len(local) <= 2:
        masked_local = local[0] + "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    return f"{masked_local}@{parts[1]}"
