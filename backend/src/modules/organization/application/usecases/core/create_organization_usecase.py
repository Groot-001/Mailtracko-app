from datetime import UTC, datetime

from src.modules.organization.domain.entities.organization_entity import (
    OrganizationEntity,
)
from src.modules.organization.domain.entities.organization_member_entity import (
    OrganizationMemberEntity,
)
from src.modules.organization.domain.enums.organization_enums import (
    OrganizationMemberStatusEnum,
    OrganizationRoleCodeEnum,
    OrganizationStatusEnum,
    OrganizationThemeEnum,
)
from src.modules.organization.domain.events.organization_domain_events import (
    OrganizationCreatedEvent,
    OrganizationMemberAddedEvent,
)
from src.modules.organization.domain.services.organization_domain_service import (
    OrganizationDomainService,
)
from src.modules.organization.domain.services.organization_member_domain_service import (
    OrganizationMemberDomainService,
)
from src.modules.organization.presentation.schemas.organization_schemas import (
    CreateOrganizationRequestSchema,
)
from src.shared.exceptions.base_exceptions import (
    CreateError,
    DomainError,
    ForbiddenError,
    ServerError,
)
from src.shared.mediator.mediator import mediator


class CreateOrganizationUseCase:
    """
    Use case for creating an organization and adding its owner as member.
    """

    def __init__(
        self,
        organization_domain_service: OrganizationDomainService,
        organization_member_domain_service: OrganizationMemberDomainService,
    ):
        self.organization_domain_service = organization_domain_service
        self.organization_member_domain_service = organization_member_domain_service

    async def execute(
        self,
        payload: CreateOrganizationRequestSchema,
        actor_id: int,
    ) -> dict:
        """
        Creates organization during onboarding.

        Normal user flow:
        signup/login -> onboarding -> create organization -> become owner.
        """
        try:
            await self._ensure_user_has_no_membership(actor_id)

            organization = OrganizationEntity(
                name=payload.name,
                website_url=getattr(payload, "website_url", None),
                org_size=getattr(payload, "org_size", None),
                monthly_email_volume=getattr(payload, "monthly_email_volume", None),
                domain_email=getattr(payload, "domain_email", None),
                org_logo=getattr(payload, "org_logo", None),
                description=getattr(payload, "description", None),
                industry_sector=self._get_value(
                    getattr(payload, "industry_sector", None)
                ),
                source=self._get_value(getattr(payload, "source", None)),
                theme=self._get_value(getattr(payload, "theme", None))
                or OrganizationThemeEnum.LIGHT.value,
                timezone=getattr(payload, "timezone", None) or "UTC",
                status=OrganizationStatusEnum.ACTIVE.value,
                owner_id=actor_id,
                created_by_id=actor_id,
            )

            created_organization = (
                await self.organization_domain_service.create_organization(
                    organization
                )
            )

            if not created_organization.id:
                raise CreateError(error="Failed to create organization")

            owner_member = OrganizationMemberEntity(
                organization_id=created_organization.id,
                user_id=actor_id,
                role_code=OrganizationRoleCodeEnum.OWNER.value,
                status=OrganizationMemberStatusEnum.ACTIVE.value,
                invited_by_id=None,
                joined_at=datetime.now(UTC),
                created_by_id=actor_id,
            )

            created_member = await self.organization_member_domain_service.add_member(
                owner_member
            )

            if not created_member.id:
                raise CreateError(
                    error="Failed to create organization",
                    internal_details="Owner membership was not created",
                )

            created_organization.add_event(
                OrganizationCreatedEvent(
                    organization_id=created_organization.id,
                    organization_uuid=created_organization.uuid,
                    name=created_organization.name,
                    owner_id=actor_id,
                )
            )
            created_organization.add_event(
                OrganizationMemberAddedEvent(
                    member_id=created_member.id,
                    user_id=actor_id,
                    organization_id=created_organization.id,
                    role_code=OrganizationRoleCodeEnum.OWNER.value,
                )
            )

            for event in created_organization.pull_events():
                await mediator.publish(event)

            return {
                "uuid": created_organization.uuid,
                "name": created_organization.name,
                "website_url": created_organization.website_url,
                "org_size": created_organization.org_size,
                "monthly_email_volume": created_organization.monthly_email_volume,
                "domain_email": created_organization.domain_email,
                "org_logo": created_organization.org_logo,
                "description": created_organization.description,
                "industry_sector": created_organization.industry_sector,
                "source": created_organization.source,
                "theme": created_organization.theme,
                "timezone": created_organization.timezone,
                "status": created_organization.status,
                "owner_id": created_organization.owner_id,
                "member_uuid": created_member.uuid,
                "role_code": created_member.role_code,
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while creating organization",
                internal_details=str(e),
            ) from e

    async def _ensure_user_has_no_membership(
        self,
        user_id: int,
    ) -> None:
        """
        Ensures user does not already belong to an organization.
        """
        existing_membership = (
            await self.organization_member_domain_service.get_member_by_user_id(
                user_id=user_id
            )
        )

        if existing_membership:
            raise ForbiddenError(
                error="User already belongs to an organization",
                errors={
                    "code": "USER_ALREADY_HAS_ORGANIZATION",
                    "message": "A user who already belongs to an organization cannot create another organization.",
                },
            )

    def _get_value(self, value):
        """
        Returns enum value when enum is passed, otherwise returns plain value.
        """
        if value is None:
            return None

        return value.value if hasattr(value, "value") else value