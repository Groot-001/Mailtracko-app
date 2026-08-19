from __future__ import annotations

import re
from xml.etree import ElementTree

from src.shared.exceptions.base_exceptions import InvalidError


_IMAGE_SIGNATURES: dict[str, tuple[bytes, ...]] = {
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/jpeg": (b"\xff\xd8\xff",),
}

_DANGEROUS_SVG_TAGS = {"script", "foreignobject", "iframe", "object", "embed", "style"}
_DANGEROUS_STYLE = re.compile(r"(?:javascript\s*:|expression\s*\(|url\s*\()", re.IGNORECASE)
_DANGEROUS_HREF = re.compile(r"^(?:javascript\s*:|https?\s*:|//|data\s*:\s*text/html)", re.IGNORECASE)


def _local_name(name: str) -> str:
    return name.rsplit("}", 1)[-1].casefold()


def _validate_svg(content: bytes) -> None:
    # SVG is served from the same origin in local mode. Keep support for normal
    # vector logos while rejecting executable/remote-active SVG content.
    lowered = content[:65536].lower()
    if b"<!doctype" in lowered or b"<!entity" in lowered:
        raise InvalidError(error="SVG logos cannot contain document type or entity declarations")

    try:
        root = ElementTree.fromstring(content)
    except (ElementTree.ParseError, ValueError) as exc:
        raise InvalidError(error="SVG logo is not valid XML") from exc

    if _local_name(root.tag) != "svg":
        raise InvalidError(error="Uploaded SVG content must contain an <svg> root element")

    for element in root.iter():
        if _local_name(element.tag) in _DANGEROUS_SVG_TAGS:
            raise InvalidError(error="SVG logo contains unsupported active content")
        for raw_name, raw_value in element.attrib.items():
            name = _local_name(raw_name)
            value = str(raw_value).strip()
            if name.startswith("on"):
                raise InvalidError(error="SVG logo contains unsupported event handlers")
            if name in {"href", "xlink:href"} and _DANGEROUS_HREF.search(value):
                raise InvalidError(error="SVG logo cannot load executable or remote content")
            if name == "style" and _DANGEROUS_STYLE.search(value):
                raise InvalidError(error="SVG logo contains unsupported active styles")


def validate_image_upload(content: bytes, content_type: str | None, *, allow_svg: bool) -> None:
    """Validate that uploaded image bytes match the declared supported format.

    Content-Type headers are client controlled, so the server also checks a file
    signature (or parses SVG) before persisting the upload.
    """
    resolved_type = (content_type or "").split(";", 1)[0].strip().casefold()
    allowed = {"image/png", "image/jpeg", "image/webp"}
    if allow_svg:
        allowed.add("image/svg+xml")
    if resolved_type not in allowed:
        label = "PNG, JPG, WEBP, or SVG" if allow_svg else "PNG, JPG, or WEBP"
        raise InvalidError(error=f"Image must be a {label} file")

    if resolved_type == "image/svg+xml":
        _validate_svg(content)
        return

    if resolved_type == "image/webp":
        if len(content) < 12 or not (content.startswith(b"RIFF") and content[8:12] == b"WEBP"):
            raise InvalidError(error="Uploaded WEBP image has invalid file content")
        return

    if not any(content.startswith(signature) for signature in _IMAGE_SIGNATURES[resolved_type]):
        raise InvalidError(error=f"Uploaded {resolved_type.removeprefix('image/').upper()} image has invalid file content")
