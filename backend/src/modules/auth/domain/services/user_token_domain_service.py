from datetime import UTC, datetime, timedelta

from src.core.config.settings import config
from src.modules.auth.domain.entities.user_token_entity import UserTokenEntity
from src.modules.auth.domain.repositories.user_token_repository import IUserTokenRepository
from src.shared.exceptions.base_exceptions import DomainError, ServerError
from src.shared.infrastructure.hasher.hasher import HasherService
from src.shared.infrastructure.token.token_service import TokenService


class UserTokenDomainService:
    """Domain service for user token entity operations."""

    def __init__(self, repository: IUserTokenRepository, hasher_service: HasherService):
        self.repository = repository
        self.hasher_service = hasher_service
        self.token_service = TokenService()

    async def create_user_token(
        self, user_id: int, type: str, expiry_minutes: int = 60
    ) -> str:
        """Generate a numeric one-time token, hash it, persist, and return the raw token."""
        try:
            raw_token = self.token_service.random_token(digit=config.OTP_DIGIT)
            token_entity = UserTokenEntity(
                user_id=user_id,
                type=type,
                token_hash=self.hasher_service.deterministic_hash(raw_token),
                expires_at=datetime.now(UTC) + timedelta(minutes=expiry_minutes),
            )
            await self.repository.add(token_entity)
            return raw_token
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to create token", internal_details=str(e)) from e

    async def verify_user_token(
        self, type: str, token: str, user_id: int | None = None
    ) -> tuple[bool, UserTokenEntity | None]:
        """Verify a raw token against stored hashes for a given type.

        If user_id is provided, only tokens for that user are considered.
        """
        try:
            criteria: dict = {"type": type, "used_at": None}
            if user_id is not None:
                criteria["user_id"] = user_id
            tokens = await self.repository.filter(**criteria)
            for t in tokens:
                if self.hasher_service.verify_deterministic_hash(token, t.token_hash) and not t.is_expired():
                    return True, t
            return False, None
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to verify token", internal_details=str(e)) from e

    async def mark_token_as_used(self, token_entity: UserTokenEntity) -> None:
        """Mark a token as consumed."""
        try:
            token_entity.mark_used()
            await self.repository.update(token_entity)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to mark token as used", internal_details=str(e)) from e

    async def invalidate_active_tokens(self, user_id: int, type: str) -> None:
        """Mark all active tokens of a given type as used for a user."""
        try:
            tokens = await self.repository.filter(user_id=user_id, type=type, used_at=None)
            for token in tokens:
                token.mark_used()
                await self.repository.update(token)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to invalidate tokens", internal_details=str(e)) from e
