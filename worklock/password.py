"""Temporary password verification; no password material is written to disk."""

import hashlib
import hmac
import os


class PasswordVerifier:
    def __init__(self, password: str):
        if not password:
            raise ValueError("Password cannot be empty")
        self._salt = os.urandom(16)
        self._digest = hashlib.pbkdf2_hmac("sha256", password.encode(), self._salt, 200_000)

    def verify(self, candidate: str) -> bool:
        digest = hashlib.pbkdf2_hmac("sha256", candidate.encode(), self._salt, 200_000)
        return hmac.compare_digest(self._digest, digest)
