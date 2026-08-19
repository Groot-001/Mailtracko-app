from typing import Any, Generic, TypeVar
from urllib.parse import urlsplit

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from src.core.config.settings import config

T = TypeVar("T")
R = TypeVar("R", bound=Response)


class CustomSuccessResponseSchema(BaseModel, Generic[T]):
    """Schema for successful API responses.

    Wraps data in a standard envelope with success flag and message.
    """

    success: bool = True
    message: str = "Success"
    data: T | None = None


class CustomResponse:
    """Helper class for building consistent API responses."""

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = 200,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content=jsonable_encoder(
                {"success": True, "message": message, "data": data}
            ),
        )

    @staticmethod
    def error(
        message: str = "Error",
        status_code: int = 400,
        errors: dict | None = None,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content=jsonable_encoder(
                {"success": False, "message": message, "errors": errors or {}}
            ),
        )


def success(
    data: dict | list | None = None, message: str = "Success", status_code: int = 200
):
    """Legacy success response helper."""
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            {"success": True, "message": message, "data": data or {}}
        ),
    )


def error(message: str = "Error", status_code: int = 400, errors: dict | None = None):
    """Legacy error response helper."""
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            {"success": False, "message": message, "errors": errors or {}}
        ),
    )


def get_cookie_response(cookies: dict[str, dict], response: R) -> R:
    """Attach cookies to a response object."""
    for key, opts in cookies.items():
        response.set_cookie(
            key=key,
            value=opts.get("value", ""),
            # Authentication cookies are session cookies by default. This
            # prevents a closed/restarted browser from silently reopening an
            # authenticated MailTracko session. A future "remember me" flow
            # can opt into persistence by passing an explicit max_age.
            max_age=opts.get("max_age"),
            httponly=opts.get("httponly", True),
            samesite=opts.get("samesite", "lax"),
            # Localhost uses HTTP, so a Secure cookie would be silently
            # rejected by the browser. Keep
            # cookies Secure by default in staging/production while allowing
            # the documented local/development Docker setup to authenticate.
            # Base cookie security on the browser-facing frontend scheme.
            # This keeps HTTPS production cookies Secure while preventing
            # localhost HTTP sessions from being silently rejected even if a
            # developer accidentally reuses a production-like environment flag.
            secure=opts.get(
                "secure",
                urlsplit(config.FRONTEND_URL).scheme.lower() == "https",
            ),
            path=opts.get("path", "/"),
        )
    return response
