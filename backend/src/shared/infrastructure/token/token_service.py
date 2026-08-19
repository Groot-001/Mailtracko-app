from datetime import UTC, datetime, timedelta

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from src.core.config.settings import config
from src.shared.exceptions.base_exceptions import InvalidError, UnAuthorizedError


class TokenService:
    def __init__(self, algorithm: str = "HS256", expiration_minutes: int = 60):
        self.secret_key = config.SECRET_KEY
        self.algorithm = algorithm
        self.expiration_minutes = expiration_minutes

    def generate_token(
        self, data: dict, expiration_minutes: int | None = None
    ) -> tuple[str, datetime]:
        expire = datetime.now(UTC) + timedelta(
            minutes=(
                expiration_minutes if expiration_minutes else self.expiration_minutes
            )
        )
        token_payload = {**data, "exp": expire}
        encoded_jwt = jwt.encode(
            token_payload, self.secret_key, algorithm=self.algorithm
        )
        return encoded_jwt, expire

    def validate_token(self, token: str) -> dict:
        try:
            decoded_token = jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm]
            )
            return decoded_token
        except ExpiredSignatureError as e:
            raise UnAuthorizedError(
                error="Token has expired", internal_details=str(e)
            ) from e
        except InvalidTokenError as e:
            raise InvalidError(error="Invalid token", internal_details=str(e)) from e

    def random_token(self, digit: int = 6) -> str:
        import secrets

        range_start = 10 ** (digit - 1)
        range_end = (10**digit) - 1
        span = range_end - range_start + 1
        return str(range_start + secrets.randbelow(span))

    def secure_token(self, nbytes: int = 32) -> str:
        import secrets

        return secrets.token_urlsafe(nbytes)
