from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from src.core.config.settings import config
from src.shared.exceptions.base_exceptions import InvalidError

_serializer = URLSafeTimedSerializer(
    config.SECRET_KEY, salt="mailtracko-unsubscribe-v1"
)


def create_unsubscribe_token(*, organization_id: int, email: str) -> str:
    return _serializer.dumps(
        {"organization_id": organization_id, "email": email.strip().lower()}
    )


def read_unsubscribe_token(token: str, *, max_age_seconds: int = 31_536_000) -> dict:
    try:
        payload = _serializer.loads(token, max_age=max_age_seconds)
    except SignatureExpired as exc:
        raise InvalidError(error="This unsubscribe link has expired") from exc
    except BadSignature as exc:
        raise InvalidError(error="This unsubscribe link is invalid") from exc
    if not payload.get("organization_id") or not payload.get("email"):
        raise InvalidError(error="This unsubscribe link is incomplete")
    return payload


def unsubscribe_url(*, organization_id: int, email: str) -> str:
    token = create_unsubscribe_token(organization_id=organization_id, email=email)
    return f"{config.APP_URL.rstrip('/')}/api/v1/platform/unsubscribe?token={token}"
