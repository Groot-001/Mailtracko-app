from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse
from starlette.status import HTTP_201_CREATED

from src.core.config.settings import config
from src.core.utils.response import CustomResponse as cr
from src.core.utils.response import CustomSuccessResponseSchema
from src.modules.contacts.application.usecases.core.initiate_sheets_oauth_usecase import (
    InitiateSheetsOAuthUseCase,
)
from src.modules.contacts.application.usecases.core.sheets_oauth_callback_usecase import (
    SheetsOAuthCallbackUseCase,
)
from src.modules.contacts.application.usecases.core.list_sheet_tabs_usecase import (
    ListSheetTabsUseCase,
)
from src.modules.contacts.application.usecases.core.import_sheet_usecase import (
    ImportSheetUseCase,
)
from src.modules.contacts.contacts_container import (
    ContactContainer,
    get_contact_container,
)
from src.modules.contacts.infrastructure.uow.contact_uow import ContactUOW
from src.modules.contacts.presentation.schemas.contact_list_schemas import (
    ImportResponseSchema,
    SheetImportRequestSchema,
    SheetTabsRequestSchema,
    SheetTabsResponseSchema,
)
from src.shared.dependencies.access_guard import require_access
from src.shared.exceptions.base_exceptions import DomainError, ForbiddenError
from src.shared.infrastructure.db import get_async_session
from src.shared.infrastructure.logger import logger
from src.modules.platform.application.workspace_permissions import effective_workspace_permissions

public_router = APIRouter()
private_router = APIRouter(
    dependencies=[Depends(require_access(authenticated=True, email_verified=True))],
)

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
    request.state.organization_member_id = member.id
    permissions = effective_workspace_permissions(member)
    request.state.organization_permissions = permissions
    if request.method not in {"GET", "HEAD", "OPTIONS"} and member.role_code != "owner":
        if not permissions.get("manage_contacts", False):
            raise ForbiddenError(
                error="Your organization permissions do not allow importing or managing contacts",
                errors={"code": "CONTACT_PERMISSION_REQUIRED"},
            )
    assert organization.id is not None
    return organization.id


@public_router.get("/sheets/oauth/callback")
async def sheets_oauth_callback(
    request: Request,
    session: AsyncSessionDep,
    code: str | None = Query(default=None),
    state: str = Query(default=""),
    error: str | None = Query(default=None),
):
    return_url = f"{config.FRONTEND_URL}/contacts/google-sheets"
    if error:
        logger.warning("[SheetsOAuth] Provider returned error: %s", error)
        return RedirectResponse(url=f"{return_url}?error=oauth_denied")
    if not code or not state:
        return RedirectResponse(url=f"{return_url}?error=oauth_invalid_callback")

    try:
        async with ContactUOW(session):
            container = get_contact_container(session)
            usecase: SheetsOAuthCallbackUseCase = container.sheets_oauth_callback_usecase()
            await usecase.execute(code=code, state=state)
    except DomainError as exc:
        logger.warning("[SheetsOAuth] Callback rejected: %s", exc.error)
        query = urlencode({"error": "oauth_callback_failed", "message": exc.error})
        return RedirectResponse(url=f"{return_url}?{query}")
    except Exception as exc:
        logger.exception("[SheetsOAuth] Callback failed: %s", str(exc))
        return RedirectResponse(url=f"{return_url}?error=oauth_callback_failed")

    return RedirectResponse(url=f"{return_url}?success=sheets_connected")


@private_router.post("/sheets/oauth/init", response_model=CustomSuccessResponseSchema)
async def init_sheets_oauth(
    request: Request,
    session: AsyncSessionDep,
):
    async with ContactUOW(session):
        container = get_contact_container(session)
        usecase: InitiateSheetsOAuthUseCase = container.initiate_sheets_oauth_usecase()
        organization_id = await _load_organization_context(request, container)
        auth_url = await usecase.execute(
            organization_id=organization_id,
            organization_uuid=request.state.organization_uuid,
            actor_id=request.state.user_id,
        )
    return cr.success(data={"auth_url": auth_url}, message="OAuth URL generated")


@private_router.post("/sheets/tabs", response_model=CustomSuccessResponseSchema)
async def list_sheet_tabs(
    request: Request,
    body: SheetTabsRequestSchema,
    session: AsyncSessionDep,
):
    async with ContactUOW(session):
        container = get_contact_container(session)
        usecase: ListSheetTabsUseCase = container.list_sheet_tabs_usecase()
        organization_id = await _load_organization_context(request, container)
        tabs = await usecase.execute(
            sheet_url=body.sheet_url, organization_id=organization_id
        )
        payload = SheetTabsResponseSchema(tabs=tabs).model_dump(mode="json")
    return cr.success(data=payload, message="Sheet tabs retrieved")


@private_router.post(
    "/{list_uuid:str}/sheets/import", response_model=CustomSuccessResponseSchema
)
async def import_from_sheet(
    request: Request,
    list_uuid: str,
    body: SheetImportRequestSchema,
    session: AsyncSessionDep,
):
    async with ContactUOW(session):
        container = get_contact_container(session)
        usecase: ImportSheetUseCase = container.import_sheet_usecase()
        organization_id = await _load_organization_context(request, container)
        result = await usecase.execute(
            list_uuid=list_uuid,
            organization_id=organization_id,
            actor_id=request.state.user_id,
            sheet_url=body.sheet_url,
            tab=body.tab,
        )
        payload = ImportResponseSchema(**result).model_dump(mode="json")
    return cr.success(
        data=payload,
        message="Sheet imported successfully",
        status_code=HTTP_201_CREATED,
    )
