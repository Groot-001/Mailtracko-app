from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse
from starlette.status import HTTP_201_CREATED

from src.core.config.settings import config
from src.core.utils.response import CustomResponse as cr
from src.core.utils.response import CustomSuccessResponseSchema
from src.modules.email_account.email_account_container import (
    get_email_account_container,
)
from src.modules.email_account.presentation.schemas.email_account_schemas import (
    ConnectOAuthRequestSchema,
    ConnectSmtpRequestSchema,
    EmailAccountConnectResponseSchema,
    EmailAccountListResponseSchema,
    EmailAccountResponseSchema,
    UpdateEmailAccountRequestSchema,
    VerifySmtpRequestSchema,
)
from src.shared.dependencies.access_guard import require_access
from src.shared.exceptions.base_exceptions import ConflictError, ForbiddenError
from src.shared.infrastructure.db import get_async_session
from src.shared.infrastructure.logger import logger
from src.shared.infrastructure.uow.base_uow import BaseUOW
from src.modules.platform.application.workspace_permissions import effective_workspace_permissions

protected_router = APIRouter(
    dependencies=[Depends(require_access(authenticated=True, email_verified=True))]
)

router = APIRouter()

AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]


async def _load_current_organization_context(
    request: Request,
    email_account_container,
):
    member = await email_account_container.organization_member_domain_service().get_active_member_by_user_id(
        user_id=request.state.user_id,
    )

    if not member:
        raise ForbiddenError(
            error="User does not belong to any organization",
            errors={"code": "USER_HAS_NO_ORGANIZATION"},
        )

    organization = await email_account_container.organization_domain_service().get_organization_by_id(
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
        if not permissions.get("manage_integrations", False):
            raise ForbiddenError(
                error="Your organization permissions do not allow managing integrations",
                errors={"code": "INTEGRATION_PERMISSION_REQUIRED"},
            )

    return organization, member


# ---- OAuth Connect ----


@protected_router.post("/oauth/connect", response_model=CustomSuccessResponseSchema)
async def oauth_connect(
    request: Request,
    body: ConnectOAuthRequestSchema,
    session: AsyncSessionDep,
):
    container = get_email_account_container(session)
    await _load_current_organization_context(request, container)
    usecase = container.oauth_connect_usecase()
    authorization_url = await usecase.execute(
        provider=body.provider,
        organization_id=request.state.organization_id,
        actor_id=request.state.user_id,
        account_uuid=body.account_uuid,
    )
    return cr.success(
        data={"authorization_url": authorization_url},
        message="OAuth authorization URL generated",
    )


# ---- OAuth Callbacks (public - OAuth redirects) ----


@router.get("/oauth/callback/google")
async def google_oauth_callback(
    request: Request,
    session: AsyncSessionDep,
    code: str | None = Query(default=None),
    state: str = Query(default=""),
    error: str | None = Query(default=None),
):
    return_url = f"{config.FRONTEND_URL}/organization/account-settings/email-accounts"
    if error:
        logger.warning("[GoogleOAuth] Provider returned error: %s", error)
        return RedirectResponse(url=f"{return_url}?error=oauth_denied")
    if not code or not state:
        return RedirectResponse(url=f"{return_url}?error=oauth_invalid_callback")

    try:
        async with BaseUOW(session):
            container = get_email_account_container(session)
            usecase = container.oauth_callback_usecase()
            await usecase.execute(code=code, state=state)
    except ConflictError as e:
        logger.info("[GoogleOAuth] Connection conflict: %s", e.error)
        if e.error == "This email is already connected to your organization":
            return RedirectResponse(url=f"{return_url}?error=oauth_account_already_connected")
        return RedirectResponse(url=f"{return_url}?error=oauth_conflict")
    except Exception as e:
        logger.exception("[GoogleOAuth] Callback failed: %s", str(e))
        return RedirectResponse(url=f"{return_url}?error=oauth_callback_failed")
    return RedirectResponse(url=f"{return_url}?success=email_connected")


# ---- SMTP Connect ----


@protected_router.post(
    "/smtp/test-credentials", response_model=CustomSuccessResponseSchema
)
async def smtp_test_credentials(
    request: Request,
    body: ConnectSmtpRequestSchema,
    session: AsyncSessionDep,
):
    container = get_email_account_container(session)
    await _load_current_organization_context(request, container)
    result = await container.smtp_connect_usecase().test_credentials(body)
    return cr.success(data=result, message="SMTP credentials verified")


@protected_router.post(
    "/smtp/connect",
    response_model=CustomSuccessResponseSchema,
    status_code=HTTP_201_CREATED,
)
async def smtp_connect(
    request: Request,
    body: ConnectSmtpRequestSchema,
    session: AsyncSessionDep,
):
    container = get_email_account_container(session)
    await _load_current_organization_context(request, container)
    async with BaseUOW(session):
        usecase = container.smtp_connect_usecase()
        result = await usecase.execute(
            payload=body,
            organization_id=request.state.organization_id,
            actor_id=request.state.user_id,
        )
        payload = EmailAccountConnectResponseSchema(**result).model_dump(mode="json")
    return cr.success(
        data=payload,
        message="SMTP account connected. Verification code sent.",
        status_code=HTTP_201_CREATED,
    )


# ---- SMTP Verify ----


@protected_router.post("/{uuid}/verify", response_model=CustomSuccessResponseSchema)
async def smtp_verify(
    request: Request,
    uuid: str,
    body: VerifySmtpRequestSchema,
    session: AsyncSessionDep,
):
    container = get_email_account_container(session)
    await _load_current_organization_context(request, container)
    async with BaseUOW(session):
        usecase = container.smtp_verify_usecase()
        result = await usecase.execute(
            account_uuid=uuid,
            code=body.code,
            organization_id=request.state.organization_id,
            actor_id=request.state.user_id,
        )
        payload = EmailAccountConnectResponseSchema(**result).model_dump(mode="json")
    return cr.success(data=payload, message="Email account verified successfully")


# ---- Resend Verification Code ----


@protected_router.post(
    "/{uuid}/resend-code", response_model=CustomSuccessResponseSchema
)
async def resend_verification_code(
    request: Request,
    uuid: str,
    session: AsyncSessionDep,
):
    container = get_email_account_container(session)
    await _load_current_organization_context(request, container)
    async with BaseUOW(session):
        usecase = container.resend_verification_usecase()
        result = await usecase.execute(
            account_uuid=uuid, organization_id=request.state.organization_id
        )
    return cr.success(data=result, message="Verification code resent")


# ---- Test Connection ----


@protected_router.post("/{uuid}/test", response_model=CustomSuccessResponseSchema)
async def test_connection(
    request: Request,
    uuid: str,
    session: AsyncSessionDep,
):
    container = get_email_account_container(session)
    await _load_current_organization_context(request, container)
    async with BaseUOW(session):
        usecase = container.test_connection_usecase()
        result = await usecase.execute(
            account_uuid=uuid,
            organization_id=request.state.organization_id,
            actor_id=request.state.user_id,
        )
    return cr.success(data=result, message="Connection test completed")


# ---- CRUD ----


@protected_router.get("/", response_model=CustomSuccessResponseSchema)
async def list_email_accounts(
    request: Request,
    session: AsyncSessionDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    container = get_email_account_container(session)
    await _load_current_organization_context(request, container)
    async with BaseUOW(session):
        usecase = container.list_accounts_usecase()
        accounts, total = await usecase.execute(
            organization_id=request.state.organization_id, limit=limit, offset=offset
        )
        items = [
            EmailAccountResponseSchema.model_validate(a).model_dump(mode="json")
            for a in accounts
        ]
        payload = EmailAccountListResponseSchema(
            items=items, total=total, limit=limit, offset=offset
        ).model_dump(mode="json")
    return cr.success(data=payload, message="Email accounts listed successfully")


@protected_router.get("/{uuid}", response_model=CustomSuccessResponseSchema)
async def get_email_account(
    request: Request,
    uuid: str,
    session: AsyncSessionDep,
):
    container = get_email_account_container(session)
    await _load_current_organization_context(request, container)
    async with BaseUOW(session):
        usecase = container.get_account_usecase()
        result = await usecase.execute(
            account_uuid=uuid, organization_id=request.state.organization_id
        )
        payload = EmailAccountResponseSchema(**result).model_dump(mode="json")
    return cr.success(
        data={"email_account": payload}, message="Email account retrieved successfully"
    )


@protected_router.patch("/{uuid}", response_model=CustomSuccessResponseSchema)
async def update_email_account(
    request: Request,
    uuid: str,
    body: UpdateEmailAccountRequestSchema,
    session: AsyncSessionDep,
):
    container = get_email_account_container(session)
    await _load_current_organization_context(request, container)
    async with BaseUOW(session):
        usecase = container.update_account_usecase()
        result = await usecase.execute(
            account_uuid=uuid,
            organization_id=request.state.organization_id,
            sender_name=body.sender_name,
            sending_limit=body.sending_limit,
            reply_to=body.reply_to,
            signature=body.signature,
            actor_id=request.state.user_id,
        )
        payload = EmailAccountResponseSchema(**result).model_dump(mode="json")
    return cr.success(
        data={"email_account": payload}, message="Email account updated successfully"
    )


@protected_router.delete("/{uuid}", response_model=CustomSuccessResponseSchema)
async def disconnect_email_account(
    request: Request,
    uuid: str,
    session: AsyncSessionDep,
):
    container = get_email_account_container(session)
    await _load_current_organization_context(request, container)
    async with BaseUOW(session):
        usecase = container.disconnect_account_usecase()
        result = await usecase.execute(
            account_uuid=uuid,
            organization_id=request.state.organization_id,
            actor_id=request.state.user_id,
        )
    return cr.success(data=result, message="Email account disconnected successfully")


# ---- Include Routers ----

router.include_router(protected_router)
