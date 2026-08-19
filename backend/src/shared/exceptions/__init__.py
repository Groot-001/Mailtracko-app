from src.shared.exceptions.base_exceptions import (
    ConflictError,
    CreateError,
    DeleteError,
    DomainError,
    ForbiddenError,
    InvalidError,
    NotFoundError,
    NotImplementedError,
    ServerError,
    UnAuthorizedError,
    UpdateError,
)

# Backward-compatible alias
UnauthorizedError = UnAuthorizedError

__all__ = [
    "ConflictError",
    "CreateError",
    "DeleteError",
    "DomainError",
    "ForbiddenError",
    "InvalidError",
    "NotFoundError",
    "NotImplementedError",
    "ServerError",
    "UnAuthorizedError",
    "UnauthorizedError",
    "UpdateError",
]
