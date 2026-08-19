"""Safe deterministic defaults used only while pytest collects the project tests."""

import os


os.environ.setdefault("ENVIRONMENT", "testing")
# This is a non-secret test-only Fernet key. Production still requires its own key.
os.environ.setdefault(
    "SECRET_ENCRYPTION_KEY",
    "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=",
)
