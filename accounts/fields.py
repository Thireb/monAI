"""A model field that keeps its text encrypted in the database (for API keys).

The value is encrypted with Fernet (AES-128-CBC with HMAC-SHA256). The Fernet key is derived
from Django's ``SECRET_KEY`` with HKDF, so changing ``SECRET_KEY`` makes the stored values
unreadable: they then read as "" and the user must enter them again.

Stored values start with ``enc1:``. A value without the prefix is old plain text; it is read
as it is and encrypted on the next save.
"""

from __future__ import annotations

import base64
import logging
from functools import lru_cache
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models

logger = logging.getLogger(__name__)

PREFIX = "enc1:"
# Longest plain text that still fits in 255 characters once encrypted.
PLAIN_MAX_LENGTH = 120


@lru_cache(maxsize=4)
def _fernet(secret_key: str) -> Fernet:
    """The Fernet object for ``secret_key``."""
    key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"monai-field-encryption",
        info=b"accounts.EncryptedCharField",
    ).derive(secret_key.encode())
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt(text: str) -> str:
    """Encrypt ``text`` and add the prefix. Empty text stays empty."""
    if not text or text.startswith(PREFIX):
        return text
    token = _fernet(settings.SECRET_KEY).encrypt(text.encode()).decode()
    return PREFIX + token


def decrypt(value: str | None) -> str:
    """Return the plain text of a stored value; old plain text comes back as it is."""
    if not value:
        return ""
    if not value.startswith(PREFIX):
        return value
    try:
        return _fernet(settings.SECRET_KEY).decrypt(value[len(PREFIX) :].encode()).decode()
    except InvalidToken:
        logger.warning("An encrypted field cannot be read; SECRET_KEY may have changed.")
        return ""


class EncryptedCharField(models.CharField):
    """A ``CharField`` whose value is encrypted in the database and plain in Python."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Default to 255 characters in the database; the plain text is limited further."""
        kwargs.setdefault("max_length", 255)
        super().__init__(*args, **kwargs)
        self.validators.append(MaxLengthValidator(PLAIN_MAX_LENGTH))

    def from_db_value(self, value: str | None, expression: Any, connection: Any) -> str:
        """Decrypt the stored value."""
        return decrypt(value)

    def to_python(self, value: Any) -> str:
        """Return plain text for any input."""
        if value is None:
            return ""
        return decrypt(str(value))

    def get_prep_value(self, value: Any) -> Any:
        """Encrypt the value before it goes to the database."""
        value = super().get_prep_value(value)
        if value is None:
            return value
        return encrypt(str(value))

    def formfield(self, **kwargs: Any) -> Any:  # type: ignore[override]
        """Form fields allow only as much text as fits once encrypted."""
        kwargs.setdefault("max_length", PLAIN_MAX_LENGTH)
        return super().formfield(**kwargs)
