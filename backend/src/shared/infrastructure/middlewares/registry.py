from urllib.parse import urlsplit, urlunsplit

from fastapi.middleware.cors import CORSMiddleware

from src.core.config.settings import config
from src.shared.infrastructure.middlewares.session_middleware import SessionMiddleware


def _cors_origins() -> list[str]:
    """Return configured origins plus the localhost loopback alias in non-prod.

    Browsers treat ``localhost`` and ``127.0.0.1`` as different origins. Local
    OAuth development commonly switches between them, so accepting only one
    alias can make the post-login auth bootstrap look like a lost session.
    Production/staging remain strictly limited to configured origins.
    """

    origins = {origin.rstrip("/") for origin in config.CORS_ALLOWED_ORIGINS}

    if not (config.is_production or config.is_staging):
        for origin in list(origins):
            parsed = urlsplit(origin)
            if parsed.hostname not in {"localhost", "127.0.0.1"}:
                continue

            alias_host = "127.0.0.1" if parsed.hostname == "localhost" else "localhost"
            alias_netloc = alias_host
            if parsed.port:
                alias_netloc = f"{alias_host}:{parsed.port}"
            origins.add(
                urlunsplit((parsed.scheme, alias_netloc, parsed.path, parsed.query, parsed.fragment)).rstrip("/")
            )

    return sorted(origins)


def register_middlewares(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SessionMiddleware)
