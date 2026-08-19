from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.requests import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from src.core.utils.response import CustomResponse as cr
from src.core.utils.response import CustomSuccessResponseSchema, get_cookie_response
from src.shared.infrastructure.rate_limiter.rate_limiter import rate_limit
from src.modules.auth.auth_container import get_auth_container
from src.modules.auth.infrastructure.uow.auth_uow import AuthUOW
from src.modules.auth.presentation.schemas.auth_schemas import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    SetupTotpResponseSchema,
    UpdateProfileRequest,
    UserAccountSummarySchema,
    UserActivityListResponseSchema,
    UserActivityResponseSchema,
    UserResponse,
    Verify2FALoginRequest,
    VerifyTotpRequest,
)
from src.modules.organization.organization_container import get_organization_container
from src.modules.organization.presentation.schemas.organization_schemas import (
    AcceptOrganizationInvitationRequestSchema,
)
from src.shared.infrastructure.storage.cloudinary_uploader import CloudinaryUploader
from src.shared.infrastructure.storage.image_validation import validate_image_upload
from src.shared.dependencies.access_guard import require_access
from src.shared.exceptions.base_exceptions import DomainError
from src.shared.infrastructure.db import get_async_session

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
logout_router = APIRouter(
    dependencies=[
        Depends(
            require_access(
                authenticated=True,
                email_verified=False,
            )
        )
    ]
)

router = APIRouter(prefix="/auth", tags=["Authentication - Core"])
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]


@public_router.post("/signup", response_model=CustomSuccessResponseSchema)
async def signup(request: Request, body: RegisterRequest, session: AsyncSessionDep):
    """Register a new user without creating an authenticated product session."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        register_usecase = auth_container.register_user_usecase()
        payload = await register_usecase.execute(
            full_name=body.full_name,
            email=body.email,
            password=body.password,
            ip_address=request.state.ip_address,
            user_agent=request.state.user_agent,
            invite_token=body.invite_token,
        )

        if body.invite_token:
            # The signup schema already accepted invite_token,
            # but the value was previously ignored and no membership was created.
            created_user = await auth_container.user_domain_service().get_user_by_email(
                body.email
            )
            if not created_user or created_user.id is None:
                raise DomainError(error="Registered user could not be resolved")

            organization_container = get_organization_container(session)
            await organization_container.accept_organization_invitation_usecase().execute(
                payload=AcceptOrganizationInvitationRequestSchema(
                    token=body.invite_token
                ),
                actor_id=created_user.id,
                actor_email=created_user.email,
            )

        # Registration is account creation only. A normal login (and MFA when
        # enabled) is required before any product session is issued.
        if payload.get("requires_login") is not True:
            raise DomainError(error="Registration must require login before product access")
        return cr.success(
            data=payload,
            message="Account created successfully. Please sign in to continue.",
            status_code=HTTP_201_CREATED,
        )


@public_router.post("/login", response_model=CustomSuccessResponseSchema)
async def login(request: Request, body: LoginRequest, session: AsyncSessionDep):
    """Authenticate user and return session cookie."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        login_usecase = auth_container.login_user_usecase()
        payload = await login_usecase.execute(
            email=body.email,
            password=body.password,
            ip_address=request.state.ip_address,
            user_agent=request.state.user_agent,
        )
        if payload.get("requires_2fa"):
            return cr.success(
                data=payload,
                message="2FA required. Complete verification to login.",
            )
        response = cr.success(data=payload, message="User logged in successfully")
        return get_cookie_response(
            cookies={"session_uuid": {"value": payload["session_uuid"]}},
            response=response,
        )


@protected_router.get("/me", response_model=CustomSuccessResponseSchema)
async def me(request: Request, session: AsyncSessionDep):
    """Get current user details with account summary."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        usecase = auth_container.get_current_user_usecase()
        payload = await usecase.execute(user_id=request.state.user_id)

        plan_name = None
        if payload.get("organization_uuid"):
            plan_name = (
                await session.execute(
                    text(
                        "SELECT bp.name FROM billing_subscriptions bs "
                        "JOIN billing_plans bp ON bp.id = bs.plan_id "
                        "JOIN org_organizations org ON org.id = bs.organization_id "
                        "WHERE org.uuid = :organization_uuid"
                    ),
                    {"organization_uuid": payload["organization_uuid"]},
                )
            ).scalar()

        summary = UserAccountSummarySchema(
            role=payload.get("role"),
            organization_name=payload.get("organization_name"),
            organization_uuid=payload.get("organization_uuid"),
            member_status=payload.get("member_status"),
            account_status=payload.get("account_status"),
            plan=plan_name,
        )

        user_fields = {k: v for k, v in payload.items() if k in UserResponse.model_fields}
        user_data = UserResponse(**user_fields).model_dump(mode="json")

        return cr.success(
            data={"user": user_data, "account_summary": summary.model_dump(mode="json")},
            message="User information retrieved successfully",
        )


@protected_router.patch("/profile", response_model=CustomSuccessResponseSchema)
async def edit_profile(
    request: Request, body: UpdateProfileRequest, session: AsyncSessionDep
):
    """Update current user profile."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        update_usecase = auth_container.update_profile_usecase()
        user = await update_usecase.execute(
            user_id=request.state.user_id,
            full_name=body.full_name,
            theme=body.theme,
            profile_image=body.profile_image,
            timezone=body.timezone,
            phone=body.phone,
            country_code=body.country_code,
            location=body.location,
        )
        return cr.success(data=user, message="User information updated successfully")


@logout_router.post("/logout", response_model=CustomSuccessResponseSchema)
async def logout(request: Request, session: AsyncSessionDep):
    """Logout user by revoking session."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        logout_usecase = auth_container.logout_user_usecase()
        await logout_usecase.execute(
            session_uuid=request.state.session_uuid,
            user_id=request.state.user_id,
        )

    response = cr.success(message="User logged out successfully")
    response.delete_cookie(key="session_uuid")
    return response


@logout_router.delete("/account", response_model=CustomSuccessResponseSchema, dependencies=[Depends(rate_limit(max_requests=3, window_seconds=300, key_prefix="delete_account"))])
async def delete_account(request: Request, session: AsyncSessionDep):
    """Soft-delete the current user's account and revoke all sessions."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        delete_usecase = auth_container.delete_account_usecase()
        result = await delete_usecase.execute(user_id=request.state.user_id)

    response = cr.success(data=result, message="Account deleted successfully")
    response.delete_cookie(key="session_uuid")
    return response


@protected_router.post("/profile/image", response_model=CustomSuccessResponseSchema)
async def upload_profile_image(
    request: Request,
    session: AsyncSessionDep,
    file: UploadFile = File(...),
):
    """Upload a bounded, supported profile image to Cloudinary."""
    content = await file.read()
    max_size = 5 * 1024 * 1024
    if not content:
        raise DomainError(error="Profile image cannot be empty")
    if len(content) > max_size:
        raise DomainError(error="Profile image must be 5 MB or smaller")
    validate_image_upload(content, file.content_type, allow_svg=False)

    uploader = CloudinaryUploader()
    results = await uploader.upload_files(
        [(file.filename or "profile.jpg", content, file.content_type)]
    )
    url = results[0]["url"]

    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        usecase = auth_container.update_profile_usecase()
        user = await usecase.execute(
            user_id=request.state.user_id,
            profile_image=url,
        )

    return cr.success(
        data={"url": url, **user},
        message="Profile image updated successfully",
        status_code=HTTP_200_OK,
    )


@protected_router.get("/activities", response_model=CustomSuccessResponseSchema)
async def list_user_activities(
    request: Request,
    session: AsyncSessionDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Get paginated activity timeline for the current user."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        usecase = auth_container.list_user_activities_usecase()
        items, total = await usecase.execute(
            user_id=request.state.user_id,
            limit=limit,
            offset=offset,
        )
        payload = UserActivityListResponseSchema(
            items=[UserActivityResponseSchema(**i) for i in items],
            total=total,
            limit=limit,
            offset=offset,
        ).model_dump(mode="json")
    return cr.success(data=payload, message="User activities retrieved successfully")


@protected_router.post("/password/change", response_model=CustomSuccessResponseSchema)
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    session: AsyncSessionDep,
):
    """Change password for the current user."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        usecase = auth_container.change_password_usecase()
        result = await usecase.execute(
            user_id=request.state.user_id,
            current_password=body.current_password,
            new_password=body.new_password,
            confirm_password=body.confirm_password,
            current_session_uuid=request.state.session_uuid,
        )
        return cr.success(data=result, message="Password changed successfully")


@protected_router.post("/2fa/setup", response_model=CustomSuccessResponseSchema)
async def setup_2fa(
    request: Request,
    session: AsyncSessionDep,
):
    """Generate TOTP secret and QR code for 2FA setup."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        usecase = auth_container.setup_totp_usecase()
        result = await usecase.execute(
            user_id=request.state.user_id,
            email=request.state.user.email,
        )
        return cr.success(data=result, message="2FA setup generated")


@protected_router.post("/2fa/verify", response_model=CustomSuccessResponseSchema)
async def verify_and_enable_2fa(
    request: Request,
    body: VerifyTotpRequest,
    session: AsyncSessionDep,
):
    """Verify TOTP code and enable 2FA."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        usecase = auth_container.verify_and_enable_totp_usecase()
        result = await usecase.execute(
            user_id=request.state.user_id,
            code=body.code,
        )
        return cr.success(data=result, message="2FA enabled successfully")


@protected_router.post("/2fa/disable", response_model=CustomSuccessResponseSchema)
async def disable_2fa(
    request: Request,
    session: AsyncSessionDep,
):
    """Disable 2FA for the current user."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        usecase = auth_container.disable_totp_usecase()
        result = await usecase.execute(user_id=request.state.user_id)
        return cr.success(data=result, message="2FA disabled successfully")


@public_router.post("/2fa/verify-login", response_model=CustomSuccessResponseSchema)
async def verify_2fa_login(
    request: Request,
    body: Verify2FALoginRequest,
    session: AsyncSessionDep,
):
    """Complete 2FA verification and return session cookie."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        usecase = auth_container.verify_2fa_login_usecase()
        temp_token = body.temp_token or request.cookies.get("mfa_challenge")
        if not temp_token:
            raise DomainError(error="Invalid or expired 2FA challenge")
        payload = await usecase.execute(
            temp_token=temp_token,
            code=body.code,
            ip_address=request.state.ip_address,
            user_agent=request.state.user_agent,
        )
        response = cr.success(data=payload, message="2FA verified, logged in successfully")
        response = get_cookie_response(
            cookies={"session_uuid": {"value": payload["session_uuid"]}},
            response=response,
        )
        response.delete_cookie(key="mfa_challenge", path="/")
        return response


router.include_router(public_router)
router.include_router(protected_router)
router.include_router(logout_router)
