from __future__ import annotations

import secrets
from typing import Any

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from src.core.config.settings import config
from src.shared.exceptions.base_exceptions import InvalidError

_DEFAULT_MAX_AGE_SECONDS = 10 * 60


def _serializer(purpose: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        secret_key=config.SECRET_KEY,
        salt=f"mailtracko-oauth-state:{purpose}",
    )


def create_oauth_state(purpose: str, **context: Any) -> str:
    """Create a signed, expiring OAuth state token.

    The state is self-contained so OAuth callbacks remain reliable across API
    restarts and multiple API instances. A random nonce keeps every request
    unique even when the context is identical.
    """

    payload = {
        "purpose": purpose,
        "nonce": secrets.token_urlsafe(24),
        **context,
    }
    return _serializer(purpose).dumps(payload)


def parse_oauth_state(
    state: str,
    purpose: str,
    *,
    max_age_seconds: int = _DEFAULT_MAX_AGE_SECONDS,
) -> dict[str, Any]:
    """Validate and decode a signed OAuth state token."""

    if not state:
        raise InvalidError(error="Google connection state is missing. Please try again.")

    try:
        payload = _serializer(purpose).loads(state, max_age=max_age_seconds)
    except SignatureExpired as exc:
        raise InvalidError(
            error="Google connection expired. Please try connecting again."
        ) from exc
    except BadSignature as exc:
        raise InvalidError(
            error="Google connection could not be verified. Please try again."
        ) from exc

    if not isinstance(payload, dict) or payload.get("purpose") != purpose:
        raise InvalidError(
            error="Google connection could not be verified. Please try again."
        )

    return payload
