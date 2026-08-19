import asyncio
import hashlib
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

from src.core.config.settings import config
from src.shared.exceptions.base_exceptions import ServerError
from src.shared.infrastructure.storage.uploader_interface import UploaderInterface


class CloudinaryUploader(UploaderInterface):
    """
    Cloudinary uploader adapter.
    """

    def __init__(self):
        self.cloud_name = config.CLOUDINARY_CLOUD_NAME
        self.api_key = config.CLOUDINARY_API_KEY
        self.api_secret = config.CLOUDINARY_API_SECRET
        self.folder = config.CLOUDINARY_FOLDER

    async def upload_files(
        self,
        files: list[tuple[str, bytes, str | None]],
    ) -> list[dict[str, Any]]:
        """
        Uploads files to Cloudinary and returns storage metadata.
        """
        if not self._is_configured():
            if config.ENVIRONMENT.value == "production":
                self._validate_configuration()
            return await self._upload_local_files(files)

        upload_url = (
            f"https://api.cloudinary.com/v1_1/"
            f"{self.cloud_name}/auto/upload"
        )

        timeout = httpx.Timeout(
            connect=10.0,
            read=60.0,
            write=60.0,
            pool=10.0,
        )

        results: list[dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=timeout) as client:
            for filename, content, content_type in files:
                resolved_content_type = (
                    content_type or "application/octet-stream"
                )

                timestamp = int(time.time())

                signature_parameters: dict[str, str | int] = {
                    "folder": self.folder,
                    "timestamp": timestamp,
                }

                signature = self._generate_signature(
                    signature_parameters
                )

                request_data = {
                    **signature_parameters,
                    "api_key": self.api_key,
                    "signature": signature,
                }

                request_files = {
                    "file": (
                        filename,
                        content,
                        resolved_content_type,
                    )
                }

                try:
                    response = await client.post(
                        upload_url,
                        data=request_data,
                        files=request_files,
                    )
                    response.raise_for_status()

                except httpx.TimeoutException as e:
                    raise ServerError(
                        error=(
                            "Cloudinary upload timed out. "
                            "Please try again."
                        ),
                        internal_details=str(e),
                    ) from e

                except httpx.HTTPStatusError as e:
                    raise ServerError(
                        error="Failed to upload file to Cloudinary",
                        internal_details=e.response.text,
                    ) from e

                except httpx.RequestError as e:
                    raise ServerError(
                        error="Failed to connect to Cloudinary",
                        internal_details=str(e),
                    ) from e

                try:
                    response_payload = response.json()

                except ValueError as e:
                    raise ServerError(
                        error="Invalid response from Cloudinary",
                        internal_details=str(e),
                    ) from e

                public_id = response_payload.get("public_id")
                secure_url = response_payload.get("secure_url")
                resource_type = response_payload.get("resource_type")
                uploaded_size = response_payload.get("bytes")

                if not isinstance(public_id, str) or not public_id:
                    raise ServerError(
                        error="Cloudinary response missing public id"
                    )

                if not isinstance(secure_url, str) or not secure_url:
                    raise ServerError(
                        error="Cloudinary response missing secure URL"
                    )

                if not isinstance(resource_type, str) or not resource_type:
                    raise ServerError(
                        error="Cloudinary response missing resource type"
                    )

                storage_key = f"{resource_type}:{public_id}"

                results.append(
                    {
                        "filename": public_id,
                        "storage_key": storage_key,
                        "original_filename": (
                            response_payload.get("original_filename")
                            or filename
                        ),
                        "content_type": resolved_content_type,
                        "size": (
                            uploaded_size
                            if isinstance(uploaded_size, int)
                            else len(content)
                        ),
                        "url": secure_url,
                        "provider": "cloudinary",
                    }
                )

        return results

    async def delete_file(
        self,
        storage_key: str,
    ) -> None:
        """
        Deletes a Cloudinary resource using its stored resource type
        and public ID.
        """
        if storage_key.startswith("local:"):
            await self._delete_local_file(storage_key)
            return

        self._validate_configuration()

        resource_type, public_id = self._parse_storage_key(
            storage_key
        )

        destroy_url = (
            f"https://api.cloudinary.com/v1_1/"
            f"{self.cloud_name}/{resource_type}/destroy"
        )

        timestamp = int(time.time())

        signature_parameters: dict[str, str | int] = {
            "invalidate": "true",
            "public_id": public_id,
            "timestamp": timestamp,
        }

        signature = self._generate_signature(
            signature_parameters
        )

        request_data = {
            **signature_parameters,
            "api_key": self.api_key,
            "signature": signature,
        }

        timeout = httpx.Timeout(
            connect=10.0,
            read=30.0,
            write=30.0,
            pool=10.0,
        )

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    destroy_url,
                    data=request_data,
                )
                response.raise_for_status()

        except httpx.TimeoutException as e:
            raise ServerError(
                error="Cloudinary deletion timed out",
                internal_details=str(e),
            ) from e

        except httpx.HTTPStatusError as e:
            raise ServerError(
                error="Failed to delete file from Cloudinary",
                internal_details=e.response.text,
            ) from e

        except httpx.RequestError as e:
            raise ServerError(
                error="Failed to connect to Cloudinary",
                internal_details=str(e),
            ) from e

        try:
            response_payload = response.json()

        except ValueError as e:
            raise ServerError(
                error="Invalid response from Cloudinary",
                internal_details=str(e),
            ) from e

        deletion_result = response_payload.get("result")

        if deletion_result not in {"ok", "not found"}:
            raise ServerError(
                error="Cloudinary did not delete the file",
                internal_details=str(response_payload),
            )


    def _is_configured(self) -> bool:
        return bool(self.cloud_name and self.api_key and self.api_secret)

    async def _upload_local_files(
        self,
        files: list[tuple[str, bytes, str | None]],
    ) -> list[dict[str, Any]]:
        """Persist uploads locally for development/testing when Cloudinary is absent.

        Docker mounts ``assets/uploads`` to a named volume so uploaded logos/profile
        images survive API container recreation. Production still requires a real
        storage provider.
        """
        assets_dir = Path(__file__).resolve().parents[4] / "assets" / "uploads"
        await asyncio.to_thread(assets_dir.mkdir, parents=True, exist_ok=True)
        extension_by_type = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/webp": ".webp",
            "image/svg+xml": ".svg",
        }
        results: list[dict[str, Any]] = []
        for filename, content, content_type in files:
            suffix = Path(filename).suffix.lower()[:10]
            if not suffix:
                suffix = extension_by_type.get(content_type or "", "")
            stored_name = f"{uuid4().hex}{suffix}"
            target = assets_dir / stored_name
            await asyncio.to_thread(target.write_bytes, content)
            results.append(
                {
                    "filename": stored_name,
                    "storage_key": f"local:uploads/{stored_name}",
                    "original_filename": filename,
                    "content_type": content_type or "application/octet-stream",
                    "size": len(content),
                    "url": f"/assets/uploads/{stored_name}",
                    "provider": "local",
                }
            )
        return results

    async def _delete_local_file(self, storage_key: str) -> None:
        relative = storage_key.removeprefix("local:").lstrip("/")
        if not relative.startswith("uploads/") or ".." in Path(relative).parts:
            raise ServerError(error="Invalid local storage key")
        target = Path(__file__).resolve().parents[4] / "assets" / relative
        await asyncio.to_thread(target.unlink, missing_ok=True)

    def _generate_signature(
        self,
        parameters: dict[str, str | int],
    ) -> str:
        """
        Generates a Cloudinary SHA-1 request signature.
        """
        signature_string = "&".join(
            f"{key}={parameters[key]}"
            for key in sorted(parameters)
            if parameters[key] not in {"", None}
        )

        raw_signature = (
            f"{signature_string}{self.api_secret}"
        ).encode("utf-8")

        return hashlib.sha1(
            raw_signature,
            usedforsecurity=False,
        ).hexdigest()

    def _parse_storage_key(
        self,
        storage_key: str,
    ) -> tuple[str, str]:
        """
        Extracts Cloudinary resource type and public ID.
        """
        if not storage_key or ":" not in storage_key:
            raise ServerError(
                error="Invalid Cloudinary storage key"
            )

        resource_type, public_id = storage_key.split(":", 1)

        if resource_type not in {"image", "raw", "video"}:
            raise ServerError(
                error="Invalid Cloudinary resource type"
            )

        if not public_id:
            raise ServerError(
                error="Cloudinary public id is missing"
            )

        return resource_type, public_id

    def _validate_configuration(self) -> None:
        """
        Ensures Cloudinary configuration is available.
        """
        if (
            not self.cloud_name
            or not self.api_key
            or not self.api_secret
        ):
            raise ServerError(
                error="Cloudinary configuration is missing"
            )