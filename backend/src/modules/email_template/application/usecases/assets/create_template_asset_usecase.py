from typing import Any

from src.modules.email_template.domain.entities.template_asset_entity import (
    TemplateAssetEntity,
)
from src.modules.email_template.domain.enums.template_enums import (
    TemplateAssetTypeEnum,
    TemplateAssetUsageEnum,
)
from src.modules.email_template.domain.events.template_domain_events import (
    TemplateAssetCreatedEvent,
)
from src.modules.email_template.domain.services.template_asset_domain_service import (
    TemplateAssetDomainService,
)
from src.modules.email_template.domain.services.template_domain_service import (
    TemplateDomainService,
)
from src.modules.email_template.presentation.schemas.template_schemas import (
    CreateTemplateAssetRequestSchema,
)
from src.shared.exceptions.base_exceptions import (
    CreateError,
    DomainError,
    InvalidError,
    ServerError,
)
from src.shared.infrastructure.storage.uploader_interface import UploaderInterface
from src.shared.mediator.mediator import mediator


class CreateTemplateAssetUseCase:
    """
    Use case for uploading and creating a template asset.
    """

    def __init__(
        self,
        template_domain_service: TemplateDomainService,
        template_asset_domain_service: TemplateAssetDomainService,
        uploader: UploaderInterface,
    ):
        self.template_domain_service = template_domain_service
        self.template_asset_domain_service = (
            template_asset_domain_service
        )
        self.uploader = uploader

    async def execute(
        self,
        template_uuid: str,
        payload: CreateTemplateAssetRequestSchema,
        filename: str,
        content: bytes,
        content_type: str | None,
        organization_id: int,
        actor_id: int,
    ) -> TemplateAssetEntity:
        """
        Uploads an inline image or attachment and saves its metadata.
        """
        uploaded_storage_key: str | None = None

        try:
            template = (
                await self.template_domain_service
                .get_custom_template_by_uuid(
                    template_uuid=template_uuid,
                    organization_id=organization_id,
                )
            )

            if not template or template.id is None:
                raise ServerError(
                    error="Template not found",
                    internal_details=(
                        f"No custom template found with uuid "
                        f"{template_uuid}"
                    ),
                )

            resolved_filename = filename.strip()
            resolved_content_type = (
                content_type or "application/octet-stream"
            )
            usage = self._get_value(payload.usage)
            asset_type = self._resolve_asset_type(
                resolved_content_type
            )

            self._validate_upload(
                filename=resolved_filename,
                content=content,
                usage=usage,
                asset_type=asset_type,
            )

            uploaded_files = await self.uploader.upload_files(
                [
                    (
                        resolved_filename,
                        content,
                        resolved_content_type,
                    )
                ]
            )

            if not uploaded_files:
                raise CreateError(
                    error="Failed to upload template asset",
                    internal_details=(
                        "Uploader returned no file metadata"
                    ),
                )

            uploaded_file = uploaded_files[0]

            uploaded_storage_key = self._get_required_string(
                uploaded_file,
                "storage_key",
            )
            file_url = self._get_required_string(
                uploaded_file,
                "url",
            )

            original_filename = (
                uploaded_file.get("original_filename")
                or resolved_filename
            )
            uploaded_content_type = (
                uploaded_file.get("content_type")
                or resolved_content_type
            )
            uploaded_size = uploaded_file.get("size")

            file_size = (
                uploaded_size
                if isinstance(uploaded_size, int)
                else len(content)
            )

            asset = TemplateAssetEntity(
                template_id=template.id,
                organization_id=organization_id,
                original_filename=str(original_filename),
                storage_key=uploaded_storage_key,
                file_url=file_url,
                content_type=str(uploaded_content_type),
                file_size=file_size,
                asset_type=asset_type,
                usage=usage,
                is_active=True,
                uploaded_by_id=actor_id,
            )

            created_asset = (
                await self.template_asset_domain_service
                .create_template_asset(asset)
            )

            if created_asset.id is None:
                raise CreateError(
                    error="Failed to create template asset",
                    internal_details=(
                        "Created template asset id is missing"
                    ),
                )

            created_asset.add_event(
                TemplateAssetCreatedEvent(
                    asset_id=created_asset.id,
                    asset_uuid=created_asset.uuid,
                    template_id=template.id,
                    organization_id=organization_id,
                    uploaded_by_id=actor_id,
                )
            )

            for event in created_asset.pull_events():
                await mediator.publish(event)

            return created_asset

        except DomainError:
            if uploaded_storage_key:
                await self._delete_uploaded_file_safely(
                    uploaded_storage_key
                )
            raise

        except Exception as e:
            if uploaded_storage_key:
                await self._delete_uploaded_file_safely(
                    uploaded_storage_key
                )

            raise ServerError(
                error=(
                    "An error occurred while creating "
                    "template asset"
                ),
                internal_details=str(e),
            ) from e

    def _resolve_asset_type(
        self,
        content_type: str,
    ) -> str:
        """
        Resolves the asset type from its MIME content type.
        """
        if content_type.lower().startswith("image/"):
            return TemplateAssetTypeEnum.IMAGE.value

        return TemplateAssetTypeEnum.DOCUMENT.value

    def _validate_upload(
        self,
        *,
        filename: str,
        content: bytes,
        usage: str,
        asset_type: str,
    ) -> None:
        """
        Validates upload information before external storage is called.
        """
        if not filename:
            raise InvalidError(
                error="Uploaded filename is required"
            )

        if not content:
            raise InvalidError(
                error="Uploaded file cannot be empty"
            )

        if len(content) > 5 * 1024 * 1024:
            raise InvalidError(
                error="Template assets must be 5 MB or smaller"
            )

        valid_usages = {
            TemplateAssetUsageEnum.INLINE.value,
            TemplateAssetUsageEnum.ATTACHMENT.value,
        }

        if usage not in valid_usages:
            raise InvalidError(
                error="Invalid template asset usage"
            )

        if (
            usage == TemplateAssetUsageEnum.INLINE.value
            and asset_type != TemplateAssetTypeEnum.IMAGE.value
        ):
            raise InvalidError(
                error="Inline template asset must be an image"
            )

    def _get_required_string(
        self,
        metadata: dict[str, Any],
        key: str,
    ) -> str:
        """
        Retrieves a required string value from uploaded metadata.
        """
        value = metadata.get(key)

        if not isinstance(value, str) or not value:
            raise CreateError(
                error="Invalid uploaded file metadata",
                internal_details=(
                    f"Uploaded file metadata is missing {key}"
                ),
            )

        return value

    async def _delete_uploaded_file_safely(
        self,
        storage_key: str,
    ) -> None:
        """
        Removes an uploaded file when database persistence fails.
        """
        try:
            await self.uploader.delete_file(storage_key)
        except Exception:
            pass

    def _get_value(self, value):
        """
        Returns enum value when enum is passed.
        """
        return value.value if hasattr(value, "value") else value