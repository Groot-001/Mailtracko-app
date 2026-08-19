from src.modules.email_template.domain.entities.template_asset_entity import (
    TemplateAssetEntity,
)
from src.modules.email_template.domain.events.template_domain_events import (
    TemplateAssetDeletedEvent,
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
from src.shared.infrastructure.storage.uploader_interface import UploaderInterface
from src.shared.mediator.mediator import mediator


class DeleteTemplateAssetUseCase:
    """
    Use case for deleting a custom-template asset.
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
        asset_uuid: str,
        organization_id: int,
        actor_id: int,
    ) -> TemplateAssetEntity:
        """
        Soft-deletes asset metadata and removes its stored file.
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

            asset = (
                await self.template_asset_domain_service
                .get_template_asset_by_uuid(
                    asset_uuid=asset_uuid,
                    template_id=template.id,
                    organization_id=organization_id,
                )
            )

            if not asset or asset.id is None:
                raise ServerError(
                    error="Template asset not found",
                    internal_details=(
                        f"No template asset found with uuid "
                        f"{asset_uuid}"
                    ),
                )

            deleted_asset = (
                await self.template_asset_domain_service
                .delete_template_asset(
                    asset_uuid=asset_uuid,
                    template_id=template.id,
                    organization_id=organization_id,
                )
            )

            if deleted_asset.id is None:
                raise ServerError(
                    error="Failed to delete template asset",
                    internal_details=(
                        "Deleted template asset id is missing"
                    ),
                )

            await self.uploader.delete_file(
                asset.storage_key
            )

            deleted_asset.add_event(
                TemplateAssetDeletedEvent(
                    asset_id=deleted_asset.id,
                    asset_uuid=deleted_asset.uuid,
                    template_id=template.id,
                    organization_id=organization_id,
                    deleted_by_id=actor_id,
                )
            )

            for event in deleted_asset.pull_events():
                await mediator.publish(event)

            return deleted_asset

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error=(
                    "An error occurred while deleting "
                    "template asset"
                ),
                internal_details=str(e),
            ) from e