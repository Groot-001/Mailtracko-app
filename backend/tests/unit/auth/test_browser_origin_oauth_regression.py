from starlette.requests import Request

from src.shared.security.browser_origin import (
    cookie_secure_for_origin,
    frontend_origin_from_state,
    normalize_origin,
    resolve_frontend_origin,
)


def _request(*, headers: dict[str, str] | None = None, scheme: str = "http", host: str = "api:8000") -> Request:
    raw_headers = [
        (key.lower().encode("latin-1"), value.encode("latin-1"))
        for key, value in (headers or {}).items()
    ]
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": scheme,
        "path": "/api/v1/auth/oauth/login/google",
        "raw_path": b"/api/v1/auth/oauth/login/google",
        "query_string": b"",
        "headers": raw_headers,
        "client": ("127.0.0.1", 50000),
        "server": tuple(host.rsplit(":", 1)) if ":" in host else (host, 80),
    }
    return Request(scope)


def test_normalize_origin_strips_paths_and_default_ports():
    assert normalize_origin("http://localhost:80/login") == "http://localhost"
    assert normalize_origin("https://app.mailtracko.com/dashboard") == "https://app.mailtracko.com"


def test_local_oauth_uses_exact_browser_referer_origin():
    request = _request(headers={"referer": "http://localhost:3000/login"})
    assert resolve_frontend_origin(request) == "http://localhost:3000"


def test_localhost_and_127_origin_are_not_collapsed_into_each_other():
    localhost = frontend_origin_from_state("http://localhost:3000")
    loopback_ip = frontend_origin_from_state("http://127.0.0.1:3000")
    assert localhost == "http://localhost:3000"
    assert loopback_ip == "http://127.0.0.1:3000"
    assert localhost != loopback_ip


def test_cookie_secure_tracks_actual_browser_origin():
    assert cookie_secure_for_origin("https://app.mailtracko.com") is True
    assert cookie_secure_for_origin("http://localhost:3000") is False
    assert cookie_secure_for_origin("http://127.0.0.1:3000") is False


def test_production_mode_allows_loopback_only_when_google_callback_is_loopback(monkeypatch):
    from types import SimpleNamespace
    import src.shared.security.browser_origin as browser_origin

    def make_config(redirect_uri: str):
        cfg = SimpleNamespace(
            FRONTEND_URL="https://app.mailtracko.com",
            CORS_ALLOWED_ORIGINS=["https://app.mailtracko.com"],
            GOOGLE_REDIRECT_URI=redirect_uri,
            is_production=True,
        )
        # The code now uses the computed property google_redirect_uri
        @property
        def google_redirect_uri(self):
            return self.GOOGLE_REDIRECT_URI or f"{self.FRONTEND_URL.rstrip('/')}/api/v1/auth/oauth/callback/google"
        type(cfg).google_redirect_uri = google_redirect_uri
        return cfg

    local_oauth_config = make_config("http://localhost:3000/api/v1/auth/oauth/callback/google")
    monkeypatch.setattr(browser_origin, "config", local_oauth_config)
    assert browser_origin.is_trusted_frontend_origin("http://localhost:3000") is True

    real_production_config = make_config("https://app.mailtracko.com/api/v1/auth/oauth/callback/google")
    monkeypatch.setattr(browser_origin, "config", real_production_config)
    assert browser_origin.is_trusted_frontend_origin("http://localhost:3000") is False
    assert (
        browser_origin.frontend_origin_from_state("http://localhost:3000")
        == "https://app.mailtracko.com"
    )
