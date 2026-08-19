from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from src.core.utils.response import CustomResponse as cr
from src.core.utils.response import CustomSuccessResponseSchema
from src.modules.organization.application.usecases.core.accept_organization_invitation_usecase import (
    AcceptOrganizationInvitationUseCase,
)
from src.modules.organization.application.usecases.core.get_organization_details_usecase import (
    GetOrganizationDetailsUseCase,
)
from src.modules.organization.application.usecases.core.list_organization_invitations_usecase import (
    ListOrganizationInvitationsUseCase,
)
from src.modules.organization.application.usecases.core.list_organization_members_usecase import (
    ListOrganizationMembersUseCase,
)
from src.modules.organization.application.usecases.core.list_recent_organization_activities_usecase import (
    ListRecentOrganizationActivitiesUseCase,
)
from src.modules.organization.application.usecases.core.get_organization_deletion_summary_usecase import (
    GetOrganizationDeletionSummaryUseCase,
)

from src.modules.organization.infrastructure.uow.organization_uow import OrganizationUOW
from src.modules.organization.organization_container import get_organization_container
from src.modules.organization.presentation.schemas.organization_schemas import (
    AcceptOrganizationInvitationRequestSchema,
    AcceptOrganizationInvitationResponseSchema,
    CreateOrganizationRequestSchema,
    CreateOrganizationResponseSchema,
    CurrentOrganizationDetailsResponseSchema,
    DeclineOrganizationInvitationRequestSchema,
    DeclineOrganizationInvitationResponseSchema,
    OrganizationActivityListResponseSchema,
    EditOrganizationRequestSchema,
    InviteOrganizationMemberRequestSchema,
    InviteOrganizationMemberResponseSchema,
    OrganizationInvitationListResponseSchema,
    OrganizationInvitationResponseSchema,
    OrganizationMemberListResponseSchema,
    OrganizationMemberResponseSchema,
    OrganizationOnboardingStatusResponseSchema,
    RemoveOrganizationMemberResponseSchema,
    OrganizationDeletionSummaryResponseSchema,
    RequestOrganizationDeletionResponseSchema,
    RevokeOrganizationInvitationResponseSchema,
    ResendOrganizationInvitationResponseSchema,
    ValidateOrganizationInvitationResponseSchema,
)
from src.modules.platform.application.workspace_permissions import effective_workspace_permissions
from src.shared.dependencies.access_guard import require_access
from src.shared.exceptions.base_exceptions import ForbiddenError, InvalidError
from src.shared.infrastructure.db import get_async_session
from src.shared.infrastructure.storage.cloudinary_uploader import CloudinaryUploader
from src.shared.infrastructure.storage.image_validation import validate_image_upload

public_router = APIRouter()

protected_router = APIRouter(
    dependencies=[
        Depends(
            require_access(
                authenticated=True,
                email_verified=True,
            )
        )
    ]
)

private_router = APIRouter(
    dependencies=[
        Depends(
            require_access(
                authenticated=True,
                email_verified=True,
            )
        )
    ]
)

router = APIRouter()

AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]


async def _load_current_organization_context(
    request: Request,
    organization_container,
):
    """
    Loads the current user's active organization context from membership.
    """
    member = (
        await organization_container.organization_member_domain_service().get_active_member_by_user_id(
            user_id=request.state.user_id,
        )
    )

    if not member:
        raise ForbiddenError(
            error="User does not belong to any organization",
            errors={"code": "USER_HAS_NO_ORGANIZATION"},
        )

    organization = await organization_container.organization_domain_service().get_organization_by_id(
        organization_id=member.organization_id,
    )

    if not organization:
        raise ForbiddenError(
            error="Organization not found for current user",
            errors={"code": "ORGANIZATION_NOT_FOUND"},
        )

    request.state.organization_id = organization.id
    request.state.organization_uuid = organization.uuid
    request.state.organization_role_code = member.role_code
    request.state.organization_permissions = effective_workspace_permissions(member)
    request.state.organization_member_id = member.id

    return organization, member


def _require_workspace_permission(request: Request, permission: str) -> None:
    if getattr(request.state, "organization_role_code", None) == "owner":
        return
    permissions = getattr(request.state, "organization_permissions", {})
    if not permissions.get(permission, False):
        raise ForbiddenError(
            error="Your organization permissions do not allow this action",
            errors={"code": "WORKSPACE_PERMISSION_REQUIRED", "permission": permission},
        )


## ------------------------------------------------ Public Endpoints ------------------------------------------------ ##


@public_router.get(
    "/invitations/validate",
    response_model=CustomSuccessResponseSchema,
)
async def validate_organization_invitation(
    token: Annotated[str, Query(min_length=1)],
    session: AsyncSessionDep,
):
    """Return safe invitation details before an invited user registers."""
    async with OrganizationUOW(session):
        organization_container = get_organization_container(session)
        invitation_service = (
            organization_container.organization_invitation_domain_service()
        )
        token_hash = invitation_service.hash_invitation_token(token.strip())
        invitation = await invitation_service.get_invitation_by_token_hash(token_hash)

        if not invitation or not invitation.is_pending() or invitation.is_expired():
            raise InvalidError(error="Invitation is invalid or has expired")

        organization = (
            await organization_container.organization_domain_service().get_organization_by_id(
                organization_id=invitation.organization_id
            )
        )
        if not organization:
            raise InvalidError(error="Invitation organization no longer exists")

        payload = ValidateOrganizationInvitationResponseSchema(
            email=invitation.email,
            organization_name=organization.name,
            role_code=invitation.role_code,
            expires_at=invitation.expires_at,
        ).model_dump(mode="json")

    return cr.success(data=payload, message="Organization invitation is valid")


@public_router.post(
    "/invitations/public/decline",
    response_model=CustomSuccessResponseSchema,
)
async def decline_organization_invitation_public(
    body: DeclineOrganizationInvitationRequestSchema,
    session: AsyncSessionDep,
):
    """Decline an invitation using possession of its one-time token."""
    async with OrganizationUOW(session):
        organization_container = get_organization_container(session)
        invitation_service = (
            organization_container.organization_invitation_domain_service()
        )
        token_hash = invitation_service.hash_invitation_token(body.token)
        invitation = await invitation_service.get_invitation_by_token_hash(token_hash)
        if not invitation:
            raise InvalidError(error="Invitation is invalid or has expired")

        usecase = organization_container.decline_organization_invitation_usecase()
        result = await usecase.execute(
            payload=body,
            actor_email=invitation.email,
            actor_id=None,
        )
        payload = DeclineOrganizationInvitationResponseSchema(**result).model_dump(
            mode="json"
        )

    return cr.success(
        data=payload,
        message="Organization invitation declined successfully",
    )


## ------------------------------------------------ Protected Endpoints ------------------------------------------------ ##


@protected_router.post("/", response_model=CustomSuccessResponseSchema)
async def create_organization(
    request: Request,
    body: CreateOrganizationRequestSchema,
    session: AsyncSessionDep,
):
    """
    Endpoint for creating organization and owner membership.
    """
    async with OrganizationUOW(session):
        organization_container = get_organization_container(session)
        create_organization_usecase = (
            organization_container.create_organization_usecase()
        )

        result = await create_organization_usecase.execute(
            payload=body,
            actor_id=request.state.user_id,
        )

        payload = CreateOrganizationResponseSchema(**result).model_dump(
            mode="json"
        )

    return cr.success(
        data=payload,
        message="Organization created successfully",
        status_code=HTTP_201_CREATED,
    )


@protected_router.get(
    "/onboarding-status",
    response_model=CustomSuccessResponseSchema,
)
async def get_organization_onboarding_status(
    request: Request,
    session: AsyncSessionDep,
):
    """
    Endpoint for checking whether current user has completed organization onboarding.
    """
    async with OrganizationUOW(session):
        organization_container = get_organization_container(session)
        usecase = organization_container.get_organization_onboarding_status_usecase()

        result = await usecase.execute(
            user_id=request.state.user_id,
            actor_email=request.state.user.email,
        )

        payload = OrganizationOnboardingStatusResponseSchema(**result).model_dump(
            mode="json"
        )

    return cr.success(
        data=payload,
        message="Organization onboarding status retrieved successfully",
    )


@protected_router.post(
    "/invitations/accept",
    response_model=CustomSuccessResponseSchema,
)
async def accept_organization_invitation(
    request: Request,
    body: AcceptOrganizationInvitationRequestSchema,
    session: AsyncSessionDep,
):
    """
    Endpoint for accepting organization invitation.
    """
    async with OrganizationUOW(session):
        organization_container = get_organization_container(session)
        usecase: AcceptOrganizationInvitationUseCase = (
            organization_container.accept_organization_invitation_usecase()
        )

        result = await usecase.execute(
            payload=body,
            actor_id=request.state.user_id,
            actor_email=request.state.user.email,
        )

        payload = AcceptOrganizationInvitationResponseSchema(**result).model_dump(
            mode="json"
        )

    return cr.success(
        data=payload,
        message="Organization invitation accepted successfully",
    )


@protected_router.post(
    "/invitations/decline",
    response_model=CustomSuccessResponseSchema,
)
async def decline_organization_invitation(
    request: Request,
    body: DeclineOrganizationInvitationRequestSchema,
    session: AsyncSessionDep,
):
    """
    Endpoint for declining organization invitation.
    """
    async with OrganizationUOW(session):
        organization_container = get_organization_container(session)
        usecase = organization_container.decline_organization_invitation_usecase()

        result = await usecase.execute(
            payload=body,
            actor_email=request.state.user.email,
            actor_id=request.state.user_id,
        )

        payload = DeclineOrganizationInvitationResponseSchema(**result).model_dump(
            mode="json"
        )

    return cr.success(
        data=payload,
        message="Organization invitation declined successfully",
    )
## ------------------------------------------------ Private Endpoints ------------------------------------------------ ##


@private_router.get("/current", response_model=CustomSuccessResponseSchema)
async def get_organization_details(
    request: Request,
    session: AsyncSessionDep,
):
    """
    Endpoint for getting current organization details.
    """
    async with OrganizationUOW(session):
        organization_container = get_organization_container(session)

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: GetOrganizationDetailsUseCase = (
            organization_container.get_organization_details_usecase()
        )

        organization = await usecase.execute(
            organization_id=request.state.organization_id,
        )

        payload = {
            "organization": CurrentOrganizationDetailsResponseSchema.model_validate(
                organization
            ).model_dump(mode="json")
        }

    return cr.success(
        data=payload,
        message="Organization details retrieved successfully",
    )

@private_router.post(
    "/delete-request",
    response_model=CustomSuccessResponseSchema,
)
async def request_organization_deletion(
    request: Request,
    session: AsyncSessionDep,
):
    """
    Endpoint for requesting/scheduling current organization deletion.
    """
    async with OrganizationUOW(session):
        organization_container = get_organization_container(session)

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase = organization_container.request_organization_deletion_usecase()

        result = await usecase.execute(
            organization_id=request.state.organization_id,
            actor_id=request.state.user_id,
            actor_email=request.state.user.email,
            actor_role_code=request.state.organization_role_code,
            actor_full_name=request.state.user.full_name,
        )

        payload = RequestOrganizationDeletionResponseSchema(**result).model_dump(
            mode="json"
        )

    return cr.success(
        data=payload,
        message="Organization deletion requested successfully",
    )

@private_router.get(
    "/recent-activities",
    response_model=CustomSuccessResponseSchema,
)
async def list_recent_organization_activities(
    request: Request,
    session: AsyncSessionDep,
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
):
    """
    Endpoint for listing recent organization activities.
    """
    async with OrganizationUOW(session):
        organization_container = get_organization_container(session)

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: ListRecentOrganizationActivitiesUseCase = (
            organization_container.list_recent_organization_activities_usecase()
        )

        result = await usecase.execute(
            organization_id=request.state.organization_id,
            limit=limit,
            offset=offset,
        )

        payload = OrganizationActivityListResponseSchema(**result).model_dump(
            mode="json"
        )

    return cr.success(
        data=payload,
        message="Recent organization activities listed successfully",
    )

@private_router.get(
    "/deletion-summary",
    response_model=CustomSuccessResponseSchema,
)
async def get_organization_deletion_summary(
    request: Request,
    session: AsyncSessionDep,
):
    """
    Endpoint for getting organization deletion summary before delete request.
    """
    async with OrganizationUOW(session):
        organization_container = get_organization_container(session)

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: GetOrganizationDeletionSummaryUseCase = (
            organization_container.get_organization_deletion_summary_usecase()
        )

        result = await usecase.execute(
            organization_id=request.state.organization_id,
            actor_role_code=request.state.organization_role_code,
        )

        payload = OrganizationDeletionSummaryResponseSchema(**result).model_dump(
            mode="json"
        )

    return cr.success(
        data=payload,
        message="Organization deletion summary retrieved successfully",
    )


@protected_router.post(
    "/onboarding-logo",
    response_model=CustomSuccessResponseSchema,
)
async def upload_onboarding_logo(
    file: UploadFile = File(...),
):
    """Upload a logo before the organization record exists during onboarding."""
    content = await file.read()
    if not content:
        raise InvalidError(error="Logo file is empty")
    if len(content) > 5 * 1024 * 1024:
        raise InvalidError(error="Organization logo must be 5 MB or smaller")
    validate_image_upload(content, file.content_type, allow_svg=True)

    uploader = CloudinaryUploader()
    uploaded = await uploader.upload_files(
        [(file.filename or "organization-logo", content, file.content_type)]
    )
    return cr.success(
        data={"url": uploaded[0]["url"]},
        message="Onboarding logo uploaded successfully",
    )


@private_router.post(
    "/logo",
    response_model=CustomSuccessResponseSchema,
)
async def upload_organization_logo(
    request: Request,
    session: AsyncSessionDep,
    file: UploadFile = File(...),
):
    """Upload and persist the current organization's logo."""
    content = await file.read()
    if not content:
        raise InvalidError(error="Logo file is empty")
    if len(content) > 5 * 1024 * 1024:
        raise InvalidError(error="Organization logo must be 5 MB or smaller")
    validate_image_upload(content, file.content_type, allow_svg=True)

    async with OrganizationUOW(session):
        organization_container = get_organization_container(session)
        organization, _ = await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )
        _require_workspace_permission(request, "manage_organization")

        uploader = CloudinaryUploader()
        uploaded = await uploader.upload_files(
            [(file.filename or "organization-logo", content, file.content_type)]
        )
        logo_url = uploaded[0]["url"]
        # Uploading a file is only a staging operation. Persist the URL together
        # with the rest of the editable organization form on Save Changes so an
        # upload never mutates organization state or creates duplicate activity.
        _ = organization

    return cr.success(
        data={"url": logo_url},
        message="Organization logo uploaded successfully. Save changes to apply it.",
    )

@private_router.patch(
    "/{organization_uuid:str}",
    response_model=CustomSuccessResponseSchema,
)
async def edit_organization(
    request: Request,
    organization_uuid: str,
    body: EditOrganizationRequestSchema,
    session: AsyncSessionDep,
):
    """
    Endpoint for editing organization details.
    """
    async with OrganizationUOW(session):
        organization_container = get_organization_container(session)

        current_organization, _ = await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )
        _require_workspace_permission(request, "manage_organization")

        if organization_uuid != current_organization.uuid:
            raise ForbiddenError(
                error="You do not have access to this organization",
                errors={"code": "USER_NO_ORG_ACCESS"},
            )

        edit_organization_usecase = organization_container.edit_organization_usecase()

        organization = await edit_organization_usecase.execute(
            organization_uuid=organization_uuid,
            payload=body,
            actor_id=request.state.user_id,
        )

        payload = {
            "current_organization": CurrentOrganizationDetailsResponseSchema.model_validate(
                organization
            ).model_dump(mode="json")
        }

    return cr.success(
        data=payload,
        message="Organization details updated successfully",
    )


@private_router.get(
    "/members",
    response_model=CustomSuccessResponseSchema,
)
async def list_organization_members(
    request: Request,
    session: AsyncSessionDep,
    member_status: Annotated[str | None, Query(alias="status")] = None,
    role: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=160)] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """
    Endpoint for listing organization members.
    """
    async with OrganizationUOW(session):
        organization_container = get_organization_container(session)

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: ListOrganizationMembersUseCase = (
            organization_container.list_organization_members_usecase()
        )

        members, total = await usecase.execute(
            organization_id=request.state.organization_id,
            status=member_status,
            role=role,
            search=search,
            limit=limit,
            offset=offset,
        )

        items = [
            OrganizationMemberResponseSchema(**member)
            for member in members
        ]

        payload = OrganizationMemberListResponseSchema(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        ).model_dump(mode="json")

    return cr.success(
        data=payload,
        message="Organization members listed successfully",
    )


@private_router.delete(
    "/members/{member_id:int}",
    response_model=CustomSuccessResponseSchema,
)
async def remove_organization_member(
    request: Request,
    member_id: int,
    session: AsyncSessionDep,
):
    """
    Endpoint for removing a member from the organization.
    """
    async with OrganizationUOW(session):
        organization_container = get_organization_container(session)

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        _require_workspace_permission(request, "manage_members")

        usecase = organization_container.remove_organization_member_usecase()

        result = await usecase.execute(
            member_id=member_id,
            organization_id=request.state.organization_id,
            actor_id=request.state.user_id,
            actor_role_code=request.state.organization_role_code,
        )

        payload = RemoveOrganizationMemberResponseSchema(**result).model_dump(
            mode="json"
        )

    return cr.success(
        data=payload,
        message="Organization member removed successfully",
        status_code=HTTP_200_OK,
    )


@private_router.post(
    "/invitations",
    response_model=CustomSuccessResponseSchema,
)
async def invite_organization_member(
    request: Request,
    body: InviteOrganizationMemberRequestSchema,
    session: AsyncSessionDep,
):
    """
    Endpoint for inviting member to organization.
    """
    async with OrganizationUOW(session):
        organization_container = get_organization_container(session)

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        _require_workspace_permission(request, "manage_members")

        usecase = organization_container.invite_organization_member_usecase()

        invitation = await usecase.execute(
            organization_id=request.state.organization_id,
            payload=body,
            actor_id=request.state.user_id,
        )

        payload = InviteOrganizationMemberResponseSchema(**invitation).model_dump(
            mode="json"
        )

    return cr.success(
        data=payload,
        message="Organization invitation created successfully",
        status_code=HTTP_201_CREATED,
    )


@private_router.get(
    "/invitations",
    response_model=CustomSuccessResponseSchema,
)
async def list_organization_invitations(
    request: Request,
    session: AsyncSessionDep,
    invitation_status: Annotated[str | None, Query(alias="status")] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """
    Endpoint for listing organization invitations.
    """
    async with OrganizationUOW(session):
        organization_container = get_organization_container(session)

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: ListOrganizationInvitationsUseCase = (
            organization_container.list_organization_invitations_usecase()
        )

        invitations, total = await usecase.execute(
            organization_id=request.state.organization_id,
            status=invitation_status,
            limit=limit,
            offset=offset,
        )

        items = [
            OrganizationInvitationResponseSchema.model_validate(invitation)
            for invitation in invitations
        ]

        payload = OrganizationInvitationListResponseSchema(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        ).model_dump(mode="json")

    return cr.success(
        data=payload,
        message="Organization invitations listed successfully",
    )


@private_router.post(
    "/invitations/{invitation_uuid:str}/resend",
    response_model=CustomSuccessResponseSchema,
)
async def resend_organization_invitation(
    request: Request,
    invitation_uuid: str,
    session: AsyncSessionDep,
):
    """Regenerate a pending invitation link and send a fresh invitation email."""
    async with OrganizationUOW(session):
        organization_container = get_organization_container(session)
        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )
        _require_workspace_permission(request, "manage_members")

        usecase = organization_container.resend_organization_invitation_usecase()
        result = await usecase.execute(
            organization_id=request.state.organization_id,
            invitation_uuid=invitation_uuid,
            actor_id=request.state.user_id,
        )
        payload = ResendOrganizationInvitationResponseSchema(**result).model_dump(mode="json")

    return cr.success(
        data=payload,
        message="Organization invitation resent successfully",
    )


@private_router.post(
    "/invitations/{invitation_uuid:str}/revoke",
    response_model=CustomSuccessResponseSchema,
)
async def revoke_organization_invitation(
    request: Request,
    invitation_uuid: str,
    session: AsyncSessionDep,
):
    """
    Endpoint for revoking organization invitation.
    """
    async with OrganizationUOW(session):
        organization_container = get_organization_container(session)

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        _require_workspace_permission(request, "manage_members")

        usecase = organization_container.revoke_organization_invitation_usecase()

        result = await usecase.execute(
            organization_id=request.state.organization_id,
            invitation_uuid=invitation_uuid,
            actor_id=request.state.user_id,
        )

        payload = RevokeOrganizationInvitationResponseSchema(**result).model_dump(
            mode="json"
        )

    return cr.success(
        data=payload,
        message="Organization invitation revoked successfully",
    )

## ------------------------------------------------ Include Routers ------------------------------------------------ ##

router.include_router(public_router)
router.include_router(protected_router)
router.include_router(private_router)
