from src.modules.email_template.domain.entities.template_asset_entity import (
    TemplateAssetEntity,
)
from src.modules.email_template.domain.services.template_asset_domain_service import (
    TemplateAssetDomainService,
)
from src.modules.email_template.domain.services.template_domain_service import (
    TemplateDomainService,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    ServerError,
)


class ListTemplateAssetsUseCase:
    """
    Use case for listing assets belonging to a custom template.
    """

    def __init__(
        self,
        template_domain_service: TemplateDomainService,
        template_asset_domain_service: TemplateAssetDomainService,
    ):
        self.template_domain_service = template_domain_service
        self.template_asset_domain_service = (
            template_asset_domain_service
        )

    async def execute(
        self,
        *,
        template_uuid: str,
        organization_id: int,
        usage: str | None = None,
        asset_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TemplateAssetEntity], int]:
        """
        Lists active template assets with pagination.
        """
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

            assets, total = (
                await self.template_asset_domain_service
                .list_paginated(
                    template_id=template.id,
                    organization_id=organization_id,
                    usage=usage,
                    asset_type=asset_type,
                    limit=limit,
                    offset=offset,
                )
            )

            return assets, total

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to list template assets",
                internal_details=str(e),
            ) from e