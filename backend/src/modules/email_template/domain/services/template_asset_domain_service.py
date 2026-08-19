from src.modules.email_template.domain.entities.template_asset_entity import (
    TemplateAssetEntity,
)
from src.modules.email_template.domain.enums.template_enums import (
    TemplateAssetTypeEnum,
    TemplateAssetUsageEnum,
)
from src.modules.email_template.domain.repositories.template_asset_repository import (
    ITemplateAssetRepository,
)
from src.shared.exceptions.base_exceptions import (
    CreateError,
    DomainError,
    InvalidError,
    ServerError,
    UpdateError,
)


class TemplateAssetDomainService:
    """
    Service class for template asset domain logic.
    """

    VALID_ASSET_TYPES = {
        TemplateAssetTypeEnum.IMAGE.value,
        TemplateAssetTypeEnum.DOCUMENT.value,
    }

    VALID_ASSET_USAGES = {
        TemplateAssetUsageEnum.INLINE.value,
        TemplateAssetUsageEnum.ATTACHMENT.value,
    }

    def __init__(self, repository: ITemplateAssetRepository):
        self.repository = repository

    async def create_template_asset(
        self,
        asset_entity: TemplateAssetEntity,
    ) -> TemplateAssetEntity:
        """
        Creates a template asset record.

        The application use case uploads the file and builds the asset
        entity before calling this method.
        """
        try:
            self._validate_asset(asset_entity)

            asset_entity.is_active = True

            return await self.repository.add(asset_entity)

        except DomainError:
            raise
        except Exception as e:
            raise CreateError(
                error="Failed to create template asset",
                internal_details=str(e),
            ) from e

    async def delete_template_asset(
        self,
        asset_uuid: str,
        template_id: int,
        organization_id: int,
    ) -> TemplateAssetEntity:
        """
        Soft-deletes an organization-owned template asset.

        External storage deletion is handled by the application use case.
        """
        try:
            asset = await self.repository.get_by_uuid_and_template_id(
                asset_uuid=asset_uuid,
                template_id=template_id,
                organization_id=organization_id,
            )

            if not asset or not asset.id:
                raise InvalidError(error="Template asset not found")

            asset.is_active = False
            asset.soft_delete()
            asset.mark_updated()

            return await self.repository.update(asset)

        except DomainError:
            raise
        except Exception as e:
            raise UpdateError(
                error="Failed to delete template asset",
                internal_details=str(e),
            ) from e

    async def get_template_asset_by_uuid(
        self,
        *,
        asset_uuid: str,
        template_id: int,
        organization_id: int | None,
    ) -> TemplateAssetEntity | None:
        """
        Retrieves a template asset by UUID and template ownership.
        """
        try:
            return await self.repository.get_by_uuid_and_template_id(
                asset_uuid=asset_uuid,
                template_id=template_id,
                organization_id=organization_id,
            )

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to retrieve template asset",
                internal_details=str(e),
            ) from e

    async def list_paginated(
        self,
        *,
        template_id: int,
        organization_id: int | None,
        usage: str | None = None,
        asset_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TemplateAssetEntity], int]:
        """
        Lists active assets belonging to a template.

        Returns paginated asset records and total count.
        """
        try:
            if usage:
                self._validate_asset_usage(usage)

            if asset_type:
                self._validate_asset_type(asset_type)

            return await self.repository.list_paginated(
                template_id=template_id,
                organization_id=organization_id,
                usage=usage,
                asset_type=asset_type,
                limit=limit,
                offset=offset,
            )

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to list template assets",
                internal_details=str(e),
            ) from e

    def _validate_asset(
        self,
        asset_entity: TemplateAssetEntity,
    ) -> None:
        """
        Validates template asset metadata.
        """
        if not asset_entity.template_id:
            raise InvalidError(error="Template id is required")

        if (
            not asset_entity.original_filename
            or not asset_entity.original_filename.strip()
        ):
            raise InvalidError(error="Original filename is required")

        if (
            not asset_entity.storage_key
            or not asset_entity.storage_key.strip()
        ):
            raise InvalidError(error="Asset storage key is required")

        if not asset_entity.file_url or not asset_entity.file_url.strip():
            raise InvalidError(error="Asset file URL is required")

        if (
            not asset_entity.content_type
            or not asset_entity.content_type.strip()
        ):
            raise InvalidError(error="Asset content type is required")

        if asset_entity.file_size <= 0:
            raise InvalidError(
                error="Asset file size must be greater than zero"
            )

        self._validate_asset_type(asset_entity.asset_type)
        self._validate_asset_usage(asset_entity.usage)

        if (
            asset_entity.usage
            == TemplateAssetUsageEnum.INLINE.value
            and asset_entity.asset_type
            != TemplateAssetTypeEnum.IMAGE.value
        ):
            raise InvalidError(
                error="Inline template asset must be an image"
            )

    def _validate_asset_type(
        self,
        asset_type: str,
    ) -> None:
        """
        Validates template asset type.
        """
        if asset_type not in self.VALID_ASSET_TYPES:
            raise InvalidError(error="Invalid template asset type")

    def _validate_asset_usage(
        self,
        usage: str,
    ) -> None:
        """
        Validates template asset usage.
        """
        if usage not in self.VALID_ASSET_USAGES:
            raise InvalidError(error="Invalid template asset usage")