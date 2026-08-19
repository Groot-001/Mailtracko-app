from types import SimpleNamespace

import pytest

from src.shared.infrastructure.storage import cloudinary_uploader as module
from src.shared.infrastructure.storage.cloudinary_uploader import CloudinaryUploader


@pytest.mark.asyncio
async def test_local_upload_fallback_persists_and_deletes_file(monkeypatch):
    monkeypatch.setattr(
        module,
        "config",
        SimpleNamespace(
            CLOUDINARY_CLOUD_NAME="",
            CLOUDINARY_API_KEY="",
            CLOUDINARY_API_SECRET="",
            CLOUDINARY_FOLDER="mailtracko",
            ENVIRONMENT=SimpleNamespace(value="development"),
        ),
    )
    uploader = CloudinaryUploader()
    result = await uploader.upload_files(
        [("logo.png", b"fake-png-content", "image/png")]
    )
    assert len(result) == 1
    item = result[0]
    assert item["provider"] == "local"
    assert item["url"].startswith("/assets/uploads/")
    assert item["storage_key"].startswith("local:uploads/")

    stored_name = item["storage_key"].split("/", 1)[1]
    target = module.Path(module.__file__).resolve().parents[4] / "assets" / "uploads" / stored_name
    assert target.read_bytes() == b"fake-png-content"

    await uploader.delete_file(item["storage_key"])
    assert not target.exists()


def test_production_without_cloudinary_does_not_fall_back(monkeypatch):
    monkeypatch.setattr(
        module,
        "config",
        SimpleNamespace(
            CLOUDINARY_CLOUD_NAME="",
            CLOUDINARY_API_KEY="",
            CLOUDINARY_API_SECRET="",
            CLOUDINARY_FOLDER="mailtracko",
            ENVIRONMENT=SimpleNamespace(value="production"),
        ),
    )
    uploader = CloudinaryUploader()
    with pytest.raises(Exception, match="Cloudinary"):
        uploader._validate_configuration()
