import hmac
import hashlib

from argon2 import PasswordHasher


class HasherService:
    """
    Service for hashing and verifying passwords using Argon2.
    """

    def __init__(self):
        self.hasher = PasswordHasher()
        self._constant_time_hash = self.hasher.hash("constant-time-password-check")

    def hash(self, plain_password: str) -> str:
        return self.hasher.hash(plain_password)

    def verify(self, hashed_password: str, plain_password: str) -> bool:
        try:
            return self.hasher.verify(hashed_password, plain_password)
        except Exception:
            return False

    def constant_time_verify(self, plain_password: str) -> None:
        self.verify(self._constant_time_hash, plain_password)

    def deterministic_hash(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def verify_deterministic_hash(self, value: str, hashed_value: str) -> bool:
        return hmac.compare_digest(self.deterministic_hash(value), hashed_value)


hasher = HasherService()
