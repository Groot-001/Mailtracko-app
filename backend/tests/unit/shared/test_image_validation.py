import pytest

from src.shared.exceptions.base_exceptions import InvalidError
from src.shared.infrastructure.storage.image_validation import validate_image_upload


def test_accepts_supported_raster_signatures() -> None:
    validate_image_upload(b"\x89PNG\r\n\x1a\nrest", "image/png", allow_svg=False)
    validate_image_upload(b"\xff\xd8\xffrest", "image/jpeg", allow_svg=False)
    validate_image_upload(b"RIFF\x04\x00\x00\x00WEBPrest", "image/webp", allow_svg=False)


def test_rejects_spoofed_raster_content_type() -> None:
    with pytest.raises(InvalidError, match="invalid file content"):
        validate_image_upload(b"not a png", "image/png", allow_svg=False)


def test_accepts_passive_svg_logo() -> None:
    validate_image_upload(
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><circle cx="5" cy="5" r="4"/></svg>',
        "image/svg+xml",
        allow_svg=True,
    )


@pytest.mark.parametrize(
    "payload",
    [
        b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
        b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"></svg>',
        b'<svg xmlns="http://www.w3.org/2000/svg"><a href="javascript:alert(1)">x</a></svg>',
        b'<svg xmlns="http://www.w3.org/2000/svg"><foreignObject><div>html</div></foreignObject></svg>',
    ],
)
def test_rejects_active_svg_content(payload: bytes) -> None:
    with pytest.raises(InvalidError):
        validate_image_upload(payload, "image/svg+xml", allow_svg=True)


def test_profile_images_do_not_allow_svg() -> None:
    with pytest.raises(InvalidError, match="PNG, JPG, or WEBP"):
        validate_image_upload(b"<svg/>", "image/svg+xml", allow_svg=False)
