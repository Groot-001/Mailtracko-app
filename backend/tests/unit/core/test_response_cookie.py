from fastapi.responses import JSONResponse

from src.core.config.settings import config
from src.core.utils.response import get_cookie_response


def _set_cookie_header(*, secure: bool | None = None) -> str:
    options: dict[str, object] = {"value": "session-test"}
    if secure is not None:
        options["secure"] = secure
    response = get_cookie_response(
        cookies={"session_uuid": options},
        response=JSONResponse({"ok": True}),
    )
    return response.headers["set-cookie"]


def test_session_cookie_uses_environment_appropriate_secure_default() -> None:
    header = _set_cookie_header()
    assert "HttpOnly" in header
    assert "SameSite=lax" in header
    assert ("Secure" in header) is (config.is_production or config.is_staging)


def test_session_cookie_allows_explicit_secure_override() -> None:
    assert "Secure" in _set_cookie_header(secure=True)
