import re

from src.modules.auth.domain.entities.user_entity import UserEntity
from src.modules.auth.domain.repositories.user_repository import IUserRepository
from src.shared.exceptions.base_exceptions import DomainError, InvalidError, ServerError
from src.shared.infrastructure.hasher.hasher import HasherService


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class UserDomainService:
    """Domain service for user entity operations."""

    def __init__(self, repository: IUserRepository, hasher_service: HasherService):
        self.repository = repository
        self.hasher_service = hasher_service

    async def create_user(self, user_entity: UserEntity) -> UserEntity:
        """Persist a new user entity."""
        try:
            return await self.repository.add(user_entity)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to create user", internal_details=str(e)) from e

    async def get_user_by_id(self, user_id: int) -> UserEntity | None:
        """Retrieve a user by their primary key."""
        try:
            return await self.repository.get_by_id(user_id)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to retrieve user", internal_details=str(e)) from e

    async def get_user_by_email(self, email: str) -> UserEntity | None:
        """Retrieve an active (non-deleted) user by their email address.

        If the user has an expired scheduled deletion, they are soft-deleted
        automatically and None is returned (frees the email for re-registration).
        """
        try:
            user = await self.repository.get_by(email=email, deleted_at=None)
            if not user:
                return None
            if user.is_deletion_schedule_expired():
                user.soft_delete()
                await self.repository.update(user)
                return None
            return user
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to retrieve user", internal_details=str(e)) from e

    async def get_user_by_uuid(self, user_uuid: str) -> UserEntity | None:
        """Retrieve a user by their UUID."""
        try:
            return await self.repository.get_by(uuid=user_uuid)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to retrieve user", internal_details=str(e)) from e

    async def get_active_user_by_id(self, user_id: int) -> UserEntity | None:
        """Retrieve a non-deleted user by their primary key."""
        try:
            return await self.repository.get_by(id=user_id, deleted_at=None)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to retrieve user", internal_details=str(e)) from e

    async def update_user(self, user_entity: UserEntity) -> UserEntity:
        """Persist changes to an existing user."""
        try:
            return await self.repository.update(user_entity)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to update user", internal_details=str(e)) from e

    async def mark_email_verified(self, user_id: int) -> UserEntity:
        """Mark a user's email as verified."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise InvalidError(error="User not found")
        user.mark_email_verified()
        return await self.update_user(user)

    def validate_email(self, email: str) -> str:
        """Validate and normalize an email address."""
        email = email.strip().lower()
        if not EMAIL_REGEX.match(email):
            raise InvalidError("Invalid email format")
        return email

    def validate_password(self, password: str) -> str:
        """Validate password strength."""
        if len(password) < 12:
            raise InvalidError("Password must be at least 12 characters")
        if len(password) > 128:
            raise InvalidError("Password must be at most 128 characters")
        if not any(c.isupper() for c in password):
            raise InvalidError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            raise InvalidError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            raise InvalidError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?`~" for c in password):
            raise InvalidError("Password must contain at least one special character")
        return password

    def hash_password(self, password: str) -> str:
        """Hash a plaintext password using Argon2."""
        return self.hasher_service.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its Argon2 hash."""
        return self.hasher_service.verify(password_hash, password)
