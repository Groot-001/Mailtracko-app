from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.requests import Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from src.core.utils.response import CustomResponse as cr
from src.core.utils.response import CustomSuccessResponseSchema
from src.modules.campaign.domain.enums import CampaignStatus
from src.modules.campaign.infrastructure.models.campaign_models import (
    CampaignModel,
    CampaignSuppressionModel,
)
from src.modules.contacts.application.usecases.core.create_contact_list_usecase import (
    CreateContactListUseCase,
)
from src.modules.contacts.application.usecases.core.create_contact_usecase import (
    CreateContactUseCase,
)
from src.modules.contacts.application.usecases.core.delete_contact_list_usecase import (
    DeleteContactListUseCase,
)
from src.modules.contacts.application.usecases.core.delete_contact_usecase import (
    DeleteContactUseCase,
)
from src.modules.contacts.application.usecases.core.export_contacts_usecase import (
    ExportContactsUseCase,
)
from src.modules.contacts.application.usecases.core.get_contact_list_usecase import (
    GetContactListUseCase,
)
from src.modules.contacts.application.usecases.core.import_contacts_usecase import (
    ImportContactsUseCase,
)
from src.modules.contacts.application.usecases.core.list_contact_lists_usecase import (
    ListContactListsUseCase,
)
from src.modules.contacts.application.usecases.core.list_contact_timeline_usecase import (
    ListContactTimelineUseCase,
)
from src.modules.contacts.application.usecases.core.list_contacts_usecase import (
    ListContactsUseCase,
)
from src.modules.contacts.application.usecases.core.update_contact_list_usecase import (
    UpdateContactListUseCase,
)
from src.modules.contacts.application.verification import EmailVerificationService
from src.modules.contacts.contacts_container import (
    ContactContainer,
    get_contact_container,
)
from src.modules.contacts.infrastructure.models.contact_models import (
    ContactActivityModel,
    ContactImportLogModel,
    ContactListModel,
    ContactModel,
)
from src.modules.contacts.infrastructure.uow.contact_uow import ContactUOW
from src.modules.organization.domain.enums.organization_enums import OrganizationRoleCodeEnum
from src.modules.platform.application.workspace_permissions import effective_workspace_permissions
from src.modules.contacts.presentation.schemas.contact_list_schemas import (
    BulkVerifyContactsRequestSchema,
    ContactActivityResponseSchema,
    ContactListItemsResponseSchema,
    ContactListListResponseSchema,
    ContactListResponseSchema,
    ContactResponseSchema,
    ContactTimelineResponseSchema,
    CreateContactListRequestSchema,
    CreateContactRequestSchema,
    ImportResponseSchema,
    UpdateContactListRequestSchema,
    UpdateContactRequestSchema,
)
from src.shared.dependencies.access_guard import require_access
from src.shared.exceptions.base_exceptions import (
    ConflictError,
    DomainError,
    ForbiddenError,
    NotFoundError,
)
from src.shared.infrastructure.db import get_async_session

protected_router = APIRouter(
    dependencies=[Depends(require_access(authenticated=True, email_verified=True))]
)

private_router = APIRouter(
    dependencies=[Depends(require_access(authenticated=True, email_verified=True))]
)

router = APIRouter()

AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]


async def _load_organization_context(
    request: Request, container: ContactContainer
) -> int:
    member = await container.organization_member_domain_service().get_active_member_by_user_id(
        user_id=request.state.user_id,
    )
    if not member:
        raise ForbiddenError(
            error="User does not have an active organization",
            errors={"code": "USER_HAS_NO_ORGANIZATION"},
        )
    organization = await container.organization_domain_service().get_organization_by_id(
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
    assert organization.id is not None
    return organization.id


def _ensure_contact_delete_permission(request: Request) -> None:
    role_code = getattr(request.state, "organization_role_code", None)
    permissions = getattr(request.state, "organization_permissions", {})
    if role_code == OrganizationRoleCodeEnum.OWNER.value:
        return
    if not permissions.get("delete_contacts", False):
        raise ForbiddenError(
            error="Your organization permissions do not allow deleting contacts or collections",
            errors={"code": "CONTACT_DELETE_PERMISSION_REQUIRED"},
        )


async def _contact_list_campaign_usage(
    session: AsyncSession, *, organization_id: int, contact_list_id: int
) -> list[CampaignModel]:
    terminal_statuses = {
        CampaignStatus.COMPLETED.value,
        CampaignStatus.CANCELLED.value,
        CampaignStatus.FAILED.value,
        CampaignStatus.ARCHIVED.value,
    }
    return list(
        (
            (
                await session.execute(
                    select(CampaignModel)
                    .where(
                        CampaignModel.organization_id == organization_id,
                        CampaignModel.contact_list_id == contact_list_id,
                        CampaignModel.deleted_at.is_(None),
                        CampaignModel.status.not_in(terminal_statuses),
                    )
                    .order_by(CampaignModel.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
    )


def _campaign_usage_payload(items: list[CampaignModel]) -> list[dict]:
    return [
        {
            "uuid": item.uuid,
            "name": item.name,
            "status": item.status,
            "scheduled_at": item.scheduled_at,
        }
        for item in items
    ]


def _contact_payload(contact: ContactModel) -> dict:
    return {
        "uuid": contact.uuid,
        "email": contact.email,
        "metadata": contact.metadata_,
        "subscribed": contact.subscribed,
        "unsubscribed_at": contact.unsubscribed_at,
        "last_contacted_at": contact.last_contacted_at,
        "status": contact.status,
        "verification_status": contact.verification_status,
        "verification_sub_status": contact.verification_sub_status,
        "verification_score": contact.verification_score,
        "verification_details": contact.verification_details,
        "verified_at": contact.verified_at,
        "bounce_risk": contact.bounce_risk,
        "last_bounced_at": contact.last_bounced_at,
        "archived_at": contact.archived_at,
        "created_at": contact.created_at,
        "updated_at": contact.updated_at,
    }


async def _apply_verification_result(
    session: AsyncSession,
    contact: ContactModel,
    result: dict,
) -> dict:
    now = datetime.now(UTC)
    provider_status = result["status"]
    contact.verification_status = provider_status
    contact.verification_sub_status = result.get("sub_status")
    contact.verification_score = result["score"]
    contact.verification_details = result.get("details")
    contact.bounce_risk = result["bounce_risk"]
    contact.verified_at = now
    contact.updated_at = now

    if provider_status == "invalid":
        contact.status = "bounced"
        contact.subscribed = False
        contact.last_bounced_at = now
    elif provider_status in {"spamtrap", "abuse", "do_not_mail"}:
        contact.status = "suppressed"
        contact.subscribed = False

    if provider_status in {"invalid", "spamtrap", "abuse", "do_not_mail"}:
        suppression = (
            (
                await session.execute(
                    select(CampaignSuppressionModel).where(
                        CampaignSuppressionModel.organization_id
                        == contact.organization_id,
                        CampaignSuppressionModel.normalized_email
                        == contact.email.lower(),
                    )
                )
            )
            .scalars()
            .first()
        )
        reason = f"verification_{provider_status}"[:50]
        if suppression:
            suppression.active = True
            suppression.reason = reason
            suppression.suppressed_at = now
            suppression.updated_at = now
        else:
            session.add(
                CampaignSuppressionModel(
                    organization_id=contact.organization_id,
                    normalized_email=contact.email.lower(),
                    reason=reason,
                    active=True,
                    suppressed_at=now,
                )
            )

    session.add(
        ContactActivityModel(
            contact_id=contact.id,
            organization_id=contact.organization_id,
            activity_type="email_verified",
            description=f"Email verification completed: {provider_status}",
            metadata_={
                "verification_status": provider_status,
                "sub_status": result.get("sub_status"),
                "score": result["score"],
                "bounce_risk": result["bounce_risk"],
            },
        )
    )
    return _contact_payload(contact)


@protected_router.post("/", response_model=CustomSuccessResponseSchema)
async def create_contact_list(
    request: Request,
    body: CreateContactListRequestSchema,
    session: AsyncSessionDep,
):
    async with ContactUOW(session):
        container = get_contact_container(session)
        usecase: CreateContactListUseCase = container.create_contact_list_usecase()

        organization_id = await _load_organization_context(request, container)

        result = await usecase.execute(
            payload=body,
            actor_id=request.state.user_id,
            organization_id=organization_id,
        )

        payload = ContactListResponseSchema(**result).model_dump(mode="json")

    return cr.success(
        data=payload,
        message="Contact list created successfully",
        status_code=HTTP_201_CREATED,
    )


@private_router.get("/", response_model=CustomSuccessResponseSchema)
async def list_contact_lists(
    request: Request,
    session: AsyncSessionDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    async with ContactUOW(session):
        container = get_contact_container(session)
        usecase: ListContactListsUseCase = container.list_contact_lists_usecase()

        organization_id = await _load_organization_context(request, container)

        items, total = await usecase.execute(
            organization_id=organization_id,
            limit=limit,
            offset=offset,
        )

        payload = ContactListListResponseSchema(
            items=[ContactListResponseSchema(**i) for i in items],
            total=total,
            limit=limit,
            offset=offset,
        ).model_dump(mode="json")

    return cr.success(
        data=payload,
        message="Contact lists retrieved successfully",
    )


@private_router.get("/import-history", response_model=CustomSuccessResponseSchema)
async def list_import_history(
    request: Request,
    session: AsyncSessionDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    container = get_contact_container(session)
    organization_id = await _load_organization_context(request, container)
    total = int(
        (
            await session.execute(
                select(func.count(ContactImportLogModel.id)).where(
                    ContactImportLogModel.organization_id == organization_id
                )
            )
        ).scalar()
        or 0
    )
    logs = (
        (
            await session.execute(
                select(ContactImportLogModel)
                .where(ContactImportLogModel.organization_id == organization_id)
                .order_by(ContactImportLogModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    items = [
        {
            "uuid": item.uuid,
            "contact_list_id": item.contact_list_id,
            "filename": item.filename,
            "column_mapping": item.column_mapping,
            "total_rows": item.total_rows,
            "success_count": item.success_count,
            "error_count": item.error_count,
            "errors": item.errors or [],
            "status": item.status,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
        for item in logs
    ]
    return cr.success(
        data={"items": items, "total": total, "limit": limit, "offset": offset},
        message="Contact import history retrieved",
    )


@private_router.get("/{list_uuid:str}", response_model=CustomSuccessResponseSchema)
async def get_contact_list(
    request: Request,
    list_uuid: str,
    session: AsyncSessionDep,
):
    async with ContactUOW(session):
        container = get_contact_container(session)
        usecase: GetContactListUseCase = container.get_contact_list_usecase()

        organization_id = await _load_organization_context(request, container)

        result = await usecase.execute(
            list_uuid=list_uuid,
            organization_id=organization_id,
        )

        payload = ContactListResponseSchema(**result).model_dump(mode="json")

    return cr.success(
        data=payload,
        message="Contact list retrieved successfully",
    )


@private_router.patch("/{list_uuid:str}", response_model=CustomSuccessResponseSchema)
async def update_contact_list(
    request: Request,
    list_uuid: str,
    body: UpdateContactListRequestSchema,
    session: AsyncSessionDep,
):
    async with ContactUOW(session):
        container = get_contact_container(session)
        usecase: UpdateContactListUseCase = container.update_contact_list_usecase()

        organization_id = await _load_organization_context(request, container)

        result = await usecase.execute(
            list_uuid=list_uuid,
            payload=body,
            actor_id=request.state.user_id,
            organization_id=organization_id,
        )

        payload = ContactListResponseSchema(**result).model_dump(mode="json")

    return cr.success(
        data=payload,
        message="Contact list updated successfully",
    )


@private_router.get(
    "/{list_uuid:str}/campaign-usage", response_model=CustomSuccessResponseSchema
)
async def get_contact_list_campaign_usage(
    request: Request,
    list_uuid: str,
    session: AsyncSessionDep,
):
    container = get_contact_container(session)
    organization_id = await _load_organization_context(request, container)
    contact_list = (
        (
            await session.execute(
                select(ContactListModel).where(
                    ContactListModel.uuid == list_uuid,
                    ContactListModel.organization_id == organization_id,
                    ContactListModel.deleted_at.is_(None),
                )
            )
        )
        .scalars()
        .first()
    )
    if not contact_list:
        raise NotFoundError(error="Contact list not found")
    usage = await _contact_list_campaign_usage(
        session, organization_id=organization_id, contact_list_id=contact_list.id
    )
    return cr.success(
        data={"in_use": bool(usage), "campaigns": _campaign_usage_payload(usage)},
        message="Contact list campaign usage retrieved",
    )


@private_router.delete("/{list_uuid:str}", response_model=CustomSuccessResponseSchema)
async def delete_contact_list(
    request: Request,
    list_uuid: str,
    session: AsyncSessionDep,
    force: bool = Query(default=False),
):
    async with ContactUOW(session):
        container = get_contact_container(session)
        usecase: DeleteContactListUseCase = container.delete_contact_list_usecase()

        organization_id = await _load_organization_context(request, container)
        _ensure_contact_delete_permission(request)

        contact_list = (
            (
                await session.execute(
                    select(ContactListModel).where(
                        ContactListModel.uuid == list_uuid,
                        ContactListModel.organization_id == organization_id,
                        ContactListModel.deleted_at.is_(None),
                    )
                )
            )
            .scalars()
            .first()
        )
        if not contact_list:
            raise NotFoundError(error="Contact list not found")
        usage = await _contact_list_campaign_usage(
            session, organization_id=organization_id, contact_list_id=contact_list.id
        )
        if usage and not force:
            raise ConflictError(
                error=(
                    "This contact collection is currently being used by one or more unfinished campaigns. "
                    "Deleting it may stop those campaigns from sending."
                ),
                errors={
                    "code": "CONTACT_LIST_IN_USE",
                    "campaigns": _campaign_usage_payload(usage),
                },
            )

        result = await usecase.execute(
            list_uuid=list_uuid,
            organization_id=organization_id,
        )

        payload = ContactListResponseSchema(**result).model_dump(mode="json")

    return cr.success(
        data=payload,
        message="Contact list deleted successfully",
        status_code=HTTP_200_OK,
    )


@private_router.get(
    "/{list_uuid:str}/contacts", response_model=CustomSuccessResponseSchema
)
async def list_contacts_in_list(
    request: Request,
    list_uuid: str,
    session: AsyncSessionDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
    subscribed: bool | None = Query(default=None),
    company: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    status: str | None = Query(default=None),
    verification_status: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
):
    """Paginated list of contacts within a list, with search/filter/sort."""
    async with ContactUOW(session):
        container = get_contact_container(session)
        usecase: ListContactsUseCase = container.list_contacts_usecase()

        organization_id = await _load_organization_context(request, container)

        items, total = await usecase.execute(
            list_uuid=list_uuid,
            organization_id=organization_id,
            limit=limit,
            offset=offset,
            search=search,
            subscribed=subscribed,
            company=company,
            tag=tag,
            status=status,
            verification_status=verification_status,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        payload = ContactListItemsResponseSchema(
            items=[ContactResponseSchema(**i) for i in items],
            total=total,
            limit=limit,
            offset=offset,
        ).model_dump(mode="json")

    return cr.success(
        data=payload,
        message="Contacts retrieved successfully",
    )


@private_router.post(
    "/{list_uuid:str}/contacts", response_model=CustomSuccessResponseSchema
)
async def create_contact(
    request: Request,
    list_uuid: str,
    body: CreateContactRequestSchema,
    session: AsyncSessionDep,
):
    async with ContactUOW(session):
        container = get_contact_container(session)
        usecase: CreateContactUseCase = container.create_contact_usecase()

        organization_id = await _load_organization_context(request, container)

        result = await usecase.execute(
            list_uuid=list_uuid,
            payload=body,
            actor_id=request.state.user_id,
            organization_id=organization_id,
        )

        payload = ContactResponseSchema(**result).model_dump(mode="json")

    return cr.success(
        data=payload,
        message="Contact created successfully",
        status_code=HTTP_201_CREATED,
    )


@private_router.get("/{list_uuid:str}/contacts/export")
async def export_contacts(
    request: Request,
    list_uuid: str,
    session: AsyncSessionDep,
):
    async with ContactUOW(session):
        container = get_contact_container(session)
        usecase: ExportContactsUseCase = container.export_contacts_usecase()

        organization_id = await _load_organization_context(request, container)

        csv_content = await usecase.execute(
            list_uuid=list_uuid,
            organization_id=organization_id,
        )

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=contacts-{list_uuid}.csv"
        },
    )


@private_router.post(
    "/{list_uuid:str}/import", response_model=CustomSuccessResponseSchema
)
async def import_contacts(
    request: Request,
    list_uuid: str,
    session: AsyncSessionDep,
    file: UploadFile = File(...),
):
    async with ContactUOW(session):
        container = get_contact_container(session)
        usecase: ImportContactsUseCase = container.import_contacts_usecase()

        organization_id = await _load_organization_context(request, container)

        allowed_types = {
            "text/csv",
            "application/csv",
            "text/comma-separated-values",
            "text/x-csv",
            "application/x-csv",
            "text/plain",
            "application/vnd.ms-excel",
            "application/octet-stream",
        }
        is_csv_ext = bool(file.filename and file.filename.lower().endswith(".csv"))
        if (
            file.content_type
            and file.content_type not in allowed_types
            and not is_csv_ext
        ):
            raise DomainError(error="Only CSV files are supported")

        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            raise DomainError(error="CSV files must be 5 MB or smaller")
        result = await usecase.execute(
            list_uuid=list_uuid,
            organization_id=organization_id,
            actor_id=request.state.user_id,
            filename=file.filename or "unknown.csv",
            csv_content=content,
        )

        payload = ImportResponseSchema(**result).model_dump(mode="json")

    return cr.success(
        data=payload,
        message="Contacts imported successfully",
        status_code=HTTP_201_CREATED,
    )


@private_router.patch(
    "/{list_uuid:str}/contacts/{contact_uuid:str}",
    response_model=CustomSuccessResponseSchema,
)
async def update_contact(
    request: Request,
    list_uuid: str,
    contact_uuid: str,
    body: UpdateContactRequestSchema,
    session: AsyncSessionDep,
):
    container = get_contact_container(session)
    organization_id = await _load_organization_context(request, container)
    contact_list = (
        (
            await session.execute(
                select(ContactListModel).where(
                    ContactListModel.uuid == list_uuid,
                    ContactListModel.organization_id == organization_id,
                    ContactListModel.deleted_at.is_(None),
                )
            )
        )
        .scalars()
        .first()
    )
    if not contact_list:
        raise NotFoundError(error="Contact list not found")
    contact = (
        (
            await session.execute(
                select(ContactModel).where(
                    ContactModel.uuid == contact_uuid,
                    ContactModel.contact_list_id == contact_list.id,
                    ContactModel.organization_id == organization_id,
                )
            )
        )
        .scalars()
        .first()
    )
    if not contact:
        raise NotFoundError(error="Contact not found")
    values = body.model_dump(exclude_unset=True)
    if values.get("email"):
        normalized = str(values["email"]).strip().lower()
        duplicate = (
            (
                await session.execute(
                    select(ContactModel).where(
                        ContactModel.contact_list_id == contact_list.id,
                        func.lower(ContactModel.email) == normalized,
                        ContactModel.id != contact.id,
                    )
                )
            )
            .scalars()
            .first()
        )
        if duplicate:
            raise ConflictError(
                error="This email already exists in the selected contact list"
            )
        contact.email = normalized
    if "metadata" in values:
        contact.metadata_ = values["metadata"]
    if "subscribed" in values and values["subscribed"] is not None:
        contact.subscribed = values["subscribed"]
        contact.unsubscribed_at = None if contact.subscribed else datetime.now(UTC)
        if not contact.subscribed and contact.status == "active":
            contact.status = "unsubscribed"
        elif contact.subscribed and contact.status == "unsubscribed":
            contact.status = "active"
    if "status" in values and values["status"] is not None:
        now = datetime.now(UTC)
        contact.status = values["status"]
        if contact.status == "active":
            contact.archived_at = None
            contact.subscribed = True
            contact.unsubscribed_at = None
        elif contact.status == "archived":
            contact.archived_at = now
            contact.subscribed = False
        elif contact.status == "unsubscribed":
            contact.unsubscribed_at = now
            contact.subscribed = False
        elif contact.status == "bounced":
            contact.last_bounced_at = now
            contact.subscribed = False
        elif contact.status == "suppressed":
            contact.subscribed = False
    contact.updated_at = datetime.now(UTC)
    await session.commit()
    payload = _contact_payload(contact)
    return cr.success(data=payload, message="Contact updated successfully")


@private_router.post(
    "/{list_uuid:str}/contacts/{contact_uuid:str}/verify",
    response_model=CustomSuccessResponseSchema,
)
async def verify_contact_email(
    request: Request,
    list_uuid: str,
    contact_uuid: str,
    session: AsyncSessionDep,
):
    container = get_contact_container(session)
    organization_id = await _load_organization_context(request, container)
    contact = (
        (
            await session.execute(
                select(ContactModel)
                .join(
                    ContactListModel,
                    ContactListModel.id == ContactModel.contact_list_id,
                )
                .where(
                    ContactModel.uuid == contact_uuid,
                    ContactModel.organization_id == organization_id,
                    ContactListModel.uuid == list_uuid,
                    ContactListModel.deleted_at.is_(None),
                )
            )
        )
        .scalars()
        .first()
    )
    if not contact:
        raise NotFoundError(error="Contact not found")
    result = await EmailVerificationService().verify(contact.email)
    payload = await _apply_verification_result(session, contact, result)
    await session.commit()
    return cr.success(data=payload, message="Email verification completed")


@private_router.post(
    "/{list_uuid:str}/contacts/verify/bulk",
    response_model=CustomSuccessResponseSchema,
)
async def bulk_verify_contact_emails(
    request: Request,
    list_uuid: str,
    body: BulkVerifyContactsRequestSchema,
    session: AsyncSessionDep,
):
    container = get_contact_container(session)
    organization_id = await _load_organization_context(request, container)
    contacts = (
        (
            await session.execute(
                select(ContactModel)
                .join(
                    ContactListModel,
                    ContactListModel.id == ContactModel.contact_list_id,
                )
                .where(
                    ContactModel.uuid.in_(body.contact_uuids),
                    ContactModel.organization_id == organization_id,
                    ContactListModel.uuid == list_uuid,
                    ContactListModel.deleted_at.is_(None),
                )
            )
        )
        .scalars()
        .all()
    )
    if len(contacts) != len(set(body.contact_uuids)):
        raise NotFoundError(error="One or more contacts were not found in this list")
    ordered = {contact.uuid: contact for contact in contacts}
    contacts = [ordered[uuid] for uuid in body.contact_uuids]
    results = await EmailVerificationService().verify_many(
        [contact.email for contact in contacts]
    )
    payload = [
        await _apply_verification_result(session, contact, result)
        for contact, result in zip(contacts, results, strict=True)
    ]
    await session.commit()
    return cr.success(
        data={"items": payload, "total": len(payload)},
        message="Bulk email verification completed",
    )


@private_router.delete(
    "/{list_uuid:str}/contacts/{contact_uuid:str}",
    response_model=CustomSuccessResponseSchema,
)
async def delete_contact(
    request: Request,
    list_uuid: str,
    contact_uuid: str,
    session: AsyncSessionDep,
):
    async with ContactUOW(session):
        container = get_contact_container(session)
        usecase: DeleteContactUseCase = container.delete_contact_usecase()

        organization_id = await _load_organization_context(request, container)
        _ensure_contact_delete_permission(request)

        result = await usecase.execute(
            list_uuid=list_uuid,
            contact_uuid=contact_uuid,
            organization_id=organization_id,
        )

        payload = ContactResponseSchema(**result).model_dump(mode="json")

    return cr.success(
        data=payload,
        message="Contact deleted successfully",
    )


@private_router.get(
    "/{list_uuid:str}/contacts/{contact_uuid:str}/timeline",
    response_model=CustomSuccessResponseSchema,
)
async def list_contact_timeline(
    request: Request,
    list_uuid: str,
    contact_uuid: str,
    session: AsyncSessionDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Paginated timeline of activities for a specific contact."""
    async with ContactUOW(session):
        container = get_contact_container(session)
        usecase: ListContactTimelineUseCase = container.list_contact_timeline_usecase()

        organization_id = await _load_organization_context(request, container)

        items, total = await usecase.execute(
            list_uuid=list_uuid,
            contact_uuid=contact_uuid,
            organization_id=organization_id,
            limit=limit,
            offset=offset,
        )

        payload = ContactTimelineResponseSchema(
            items=[ContactActivityResponseSchema(**i) for i in items],
            total=total,
            limit=limit,
            offset=offset,
        ).model_dump(mode="json")

    return cr.success(
        data=payload,
        message="Contact timeline retrieved successfully",
    )


router.include_router(protected_router)
router.include_router(private_router)
