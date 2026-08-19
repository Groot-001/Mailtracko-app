from typing import Any

from src.shared.infrastructure.logger import logger


class DomainError(Exception):
    """
    Custom base domain  exception
    """

    code: str = "domain_error"

    def __init__(
        self,
        error: str,
        internal_details: Any | None = None,
        errors: Any | None = None,
    ):
        """Initialize with detail message and optional data."""
        super().__init__(error)
        if internal_details:
            logger.error("[%s] Internal Details: %s", error, internal_details)
        else:
            logger.debug("[%s]", error)
        self.error = error
        self.internal_details = internal_details
        self.errors = errors


class NotFoundError(DomainError):
    """
    Custom Exception for not found
    """

    code: str = "not_found"

    def __init__(
        self,
        error: str = "Not found Error",
        internal_details: Any | None = None,
        errors: Any | None = None,
    ):
        """Initialize with detail message and optional data."""
        super().__init__(error=error, internal_details=internal_details, errors=errors)


class ConflictError(DomainError):
    """
    Exception for already exists
    """

    code: str = "conflict_error"

    def __init__(
        self,
        error: str = "Already exists",
        internal_details: Any | None = None,
        errors: Any | None = None,
    ):
        """Initialize with detail message and optional data."""
        super().__init__(error=error, internal_details=internal_details, errors=errors)


class CreateError(DomainError):
    """
    Exception for create error
    """

    code: str = "create_error"

    def __init__(
        self,
        error: str = "Create error",
        internal_details: Any | None = None,
        errors: Any | None = None,
    ):
        """Initialize with detail message and optional data."""
        super().__init__(error=error, internal_details=internal_details, errors=errors)


class UpdateError(DomainError):
    """
    Exception for update error
    """

    code: str = "update_error"

    def __init__(
        self,
        error: str = "Update error",
        internal_details: Any | None = None,
        errors: Any | None = None,
    ):
        """Initialize with detail message and optional data."""
        super().__init__(error=error, internal_details=internal_details, errors=errors)


class DeleteError(DomainError):
    """
    Exception for delete error
    """

    code: str = "delete_error"

    def __init__(
        self,
        error: str = "Delete error",
        internal_details: Any | None = None,
        errors: Any | None = None,
    ):
        """Initialize with detail message and optional data."""
        super().__init__(error=error, internal_details=internal_details, errors=errors)


class InvalidError(DomainError):
    """
    Invalid error
    """

    code: str = "invalid_error"

    def __init__(
        self,
        error: str = "Invalid error",
        internal_details: Any | None = None,
        errors: Any | None = None,
    ):
        super().__init__(error=error, internal_details=internal_details, errors=errors)


class UnAuthorizedError(DomainError):
    """
    unauthorized error
    """

    code: str = "unauthorized_error"

    def __init__(
        self,
        error: str = "Unauthorized error",
        internal_details: Any | None = None,
        errors: Any | None = None,
    ):
        super().__init__(error=error, internal_details=internal_details, errors=errors)


class ServerError(DomainError):
    """
    Server error
    """

    code: str = "server_error"

    def __init__(
        self,
        error: str = "Server error",
        internal_details: Any | None = None,
        errors: Any | None = None,
    ):
        super().__init__(error=error, internal_details=internal_details, errors=errors)


class ForbiddenError(DomainError):
    code: str = "forbidden_error"

    def __init__(
        self,
        error: str = "You do not have permission to perform this action",
        internal_details: Any | None = None,
        errors: Any | None = None,
    ):
        super().__init__(error=error, internal_details=internal_details, errors=errors)


class NotImplementedError(DomainError):
    code: str = "not_implemented"

    def __init__(
        self,
        error: str = "Not implemented",
        internal_details: Any | None = None,
        errors: Any | None = None,
    ):
        super().__init__(error=error, internal_details=internal_details, errors=errors)
