from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    UploadFile,
)
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from src.core.utils.response import CustomResponse as cr
from src.core.utils.response import CustomSuccessResponseSchema

from src.modules.email_template.application.usecases.lifecycle.archive_template_usecase import (
    ArchiveTemplateUseCase,
)
from src.modules.email_template.application.usecases.gallery.copy_system_template_usecase import (
    CopySystemTemplateUseCase,
)
from src.modules.email_template.application.usecases.assets.create_template_asset_usecase import (
    CreateTemplateAssetUseCase,
)
from src.modules.email_template.application.usecases.core.create_template_usecase import (
    CreateTemplateUseCase,
)
from src.modules.email_template.application.usecases.assets.delete_template_asset_usecase import (
    DeleteTemplateAssetUseCase,
)
from src.modules.email_template.application.usecases.core.delete_template_usecase import (
    DeleteTemplateUseCase,
)
from src.modules.email_template.application.usecases.lifecycle.duplicate_template_usecase import (
    DuplicateTemplateUseCase,
)
from src.modules.email_template.application.usecases.core.edit_template_details_usecase import (
    EditTemplateDetailsUseCase,
)
from src.modules.email_template.application.usecases.gallery.get_system_template_details_usecase import (
    GetSystemTemplateDetailsUseCase,
)
from src.modules.email_template.application.usecases.core.get_template_details_usecase import (
    GetTemplateDetailsUseCase,
)
from src.modules.email_template.application.usecases.gallery.list_system_templates_usecase import (
    ListSystemTemplatesUseCase,
)
from src.modules.email_template.application.usecases.assets.list_template_assets_usecase import (
    ListTemplateAssetsUseCase,
)
from src.modules.email_template.application.usecases.gallery.list_template_categories_usecase import (
    ListTemplateCategoriesUseCase,
)
from src.modules.email_template.application.usecases.categories.create_template_category_usecase import (
    CreateTemplateCategoryUseCase,
)
from src.modules.email_template.application.usecases.categories.list_organization_template_categories_usecase import (
    ListOrganizationTemplateCategoriesUseCase,
)
from src.modules.email_template.application.usecases.core.list_templates_usecase import (
    ListTemplatesUseCase,
)
from src.modules.email_template.application.usecases.core.preview_template_usecase import (
    PreviewTemplateUseCase,
)
from src.modules.email_template.application.usecases.lifecycle.publish_template_usecase import (
    PublishTemplateUseCase,
)
from src.modules.email_template.application.usecases.lifecycle.restore_template_usecase import (
    RestoreTemplateUseCase,
)
from src.modules.email_template.domain.enums.template_enums import (
    TemplateAssetTypeEnum,
    TemplateAssetUsageEnum,
    TemplateStatusEnum,
)
from src.modules.email_template.email_template_container import (
    get_email_template_container,
)
from src.modules.email_template.infrastructure.uow.email_template_uow import (
    EmailTemplateUOW,
)
from src.modules.email_template.application.usecases.core.get_template_dashboard_summary_usecase import (
    GetTemplateDashboardSummaryUseCase,
)
from src.modules.email_template.application.usecases.test_email.send_template_test_email_usecase import (
    SendTemplateTestEmailUseCase,
)
from src.modules.email_template.presentation.schemas.template_schemas import (
    CreateTemplateAssetRequestSchema,
    CreateTemplateCategoryRequestSchema,
    CreateTemplateRequestSchema,
    DuplicateTemplateRequestSchema,
    PreviewTemplateRequestSchema,
    PreviewTemplateResponseSchema,
    TemplateAssetListResponseSchema,
    TemplateAssetResponseSchema,
    TemplateCategoryListResponseSchema,
    TemplateCategoryResponseSchema,
    TemplateListResponseSchema,
    TemplateResponseSchema,
    UpdateTemplateRequestSchema,
    TemplateDashboardSummaryResponseSchema,
    TemplateDetailResponseSchema,
    SendTemplateTestEmailRequestSchema,
    SendTemplateTestEmailResponseSchema,
)
from src.modules.organization.organization_container import (
    get_organization_container,
)
from src.shared.dependencies.access_guard import require_access
from src.shared.exceptions.base_exceptions import ForbiddenError
from src.shared.infrastructure.db import get_async_session
from src.modules.platform.application.workspace_permissions import effective_workspace_permissions


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

AsyncSessionDep = Annotated[
    AsyncSession,
    Depends(get_async_session),
]


async def _load_current_organization_context(
    request: Request,
    organization_container,
):
    """
    Loads the current user's active organization context from membership.
    """
    member = (
        await organization_container
        .organization_member_domain_service()
        .get_active_member_by_user_id(
            user_id=request.state.user_id,
        )
    )

    if not member:
        raise ForbiddenError(
            error="User does not belong to any organization",
            errors={
                "code": "USER_HAS_NO_ORGANIZATION",
            },
        )

    organization = (
        await organization_container
        .organization_domain_service()
        .get_organization_by_id(
            organization_id=member.organization_id,
        )
    )

    if not organization:
        raise ForbiddenError(
            error="Organization not found for current user",
            errors={
                "code": "ORGANIZATION_NOT_FOUND",
            },
        )

    request.state.organization_id = organization.id
    request.state.organization_uuid = organization.uuid
    request.state.organization_role_code = member.role_code
    request.state.organization_member_id = member.id
    permissions = effective_workspace_permissions(member)
    request.state.organization_permissions = permissions
    if request.method not in {"GET", "HEAD", "OPTIONS"} and member.role_code != "owner":
        if not permissions.get("manage_templates", False):
            raise ForbiddenError(
                error="Your organization permissions do not allow managing templates",
                errors={"code": "TEMPLATE_PERMISSION_REQUIRED"},
            )

    return organization, member


## ------------------------------------------------ Protected Endpoints ------------------------------------------------ ##


@protected_router.post(
    "/email_templates/preview",
    response_model=CustomSuccessResponseSchema,
)
async def preview_template(
    body: PreviewTemplateRequestSchema,
    session: AsyncSessionDep,
):
    """
    Endpoint for previewing saved or unsaved template content.

    This endpoint performs no database write.
    """
    async with EmailTemplateUOW(session):
        email_template_container = get_email_template_container(
            session
        )

        usecase: PreviewTemplateUseCase = (
            email_template_container.preview_template_usecase()
        )

        result = await usecase.execute(
            payload=body,
        )

        payload = (
            PreviewTemplateResponseSchema
            .model_validate(result)
            .model_dump(mode="json")
        )

    return cr.success(
        data=payload,
        message="Email template preview generated successfully",
    )


@protected_router.get(
    "/templates/categories",
    response_model=CustomSuccessResponseSchema,
)
async def list_organization_template_categories(
    request: Request,
    session: AsyncSessionDep,
):
    """List global categories and categories owned by the current organization."""
    async with EmailTemplateUOW(session):
        email_template_container = get_email_template_container(session)
        organization_container = get_organization_container(session)
        organization, _ = await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )
        usecase: ListOrganizationTemplateCategoriesUseCase = (
            email_template_container.list_organization_template_categories_usecase()
        )
        categories = await usecase.execute(organization_id=organization.id)
        payload = TemplateCategoryListResponseSchema(
            items=[
                TemplateCategoryResponseSchema.model_validate(category)
                for category in categories
            ]
        ).model_dump(mode="json")

    return cr.success(data=payload, message="Template categories listed successfully")


@protected_router.post(
    "/templates/categories",
    response_model=CustomSuccessResponseSchema,
    status_code=HTTP_201_CREATED,
)
async def create_organization_template_category(
    request: Request,
    body: CreateTemplateCategoryRequestSchema,
    session: AsyncSessionDep,
):
    """Create a category visible only to the current organization."""
    async with EmailTemplateUOW(session):
        email_template_container = get_email_template_container(session)
        organization_container = get_organization_container(session)
        organization, _ = await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )
        usecase: CreateTemplateCategoryUseCase = (
            email_template_container.create_template_category_usecase()
        )
        category = await usecase.execute(
            payload=body,
            organization_id=organization.id,
            actor_id=request.state.user_id,
        )
        payload = TemplateCategoryResponseSchema.model_validate(category).model_dump(
            mode="json"
        )

    return cr.success(data=payload, message="Template category created successfully")


@protected_router.get(
    "/template-gallery/categories",
    response_model=CustomSuccessResponseSchema,
)
async def list_template_categories(
    session: AsyncSessionDep,
):
    """
    Endpoint for listing active system-template categories.
    """
    async with EmailTemplateUOW(session):
        email_template_container = get_email_template_container(
            session
        )

        usecase: ListTemplateCategoriesUseCase = (
            email_template_container
            .list_template_categories_usecase()
        )

        categories = await usecase.execute()

        items = [
            TemplateCategoryResponseSchema.model_validate(
                category
            )
            for category in categories
        ]

        payload = TemplateCategoryListResponseSchema(
            items=items,
        ).model_dump(mode="json")

    return cr.success(
        data=payload,
        message="Template categories listed successfully",
    )


@protected_router.get(
    "/template-gallery/templates",
    response_model=CustomSuccessResponseSchema,
)
async def list_system_templates(
    session: AsyncSessionDep,
    category_id: Annotated[
        int | None,
        Query(ge=1),
    ] = None,
    search: Annotated[
        str | None,
        Query(),
    ] = None,
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
):
    """
    Endpoint for listing published global system templates.
    """
    async with EmailTemplateUOW(session):
        email_template_container = get_email_template_container(
            session
        )

        usecase: ListSystemTemplatesUseCase = (
            email_template_container
            .list_system_templates_usecase()
        )

        templates, total = await usecase.execute(
            category_id=category_id,
            search=search,
            limit=limit,
            offset=offset,
        )

        items = [
            TemplateResponseSchema.model_validate(template)
            for template in templates
        ]

        payload = TemplateListResponseSchema(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        ).model_dump(mode="json")

    return cr.success(
        data=payload,
        message="System templates listed successfully",
    )


@protected_router.get(
    "/template-gallery/templates/{template_uuid:str}",
    response_model=CustomSuccessResponseSchema,
)
async def get_system_template_details(
    template_uuid: str,
    session: AsyncSessionDep,
):
    """
    Endpoint for retrieving one published system template.
    """
    async with EmailTemplateUOW(session):
        email_template_container = get_email_template_container(
            session
        )

        usecase: GetSystemTemplateDetailsUseCase = (
            email_template_container
            .get_system_template_details_usecase()
        )

        template = await usecase.execute(
            template_uuid=template_uuid,
        )

        payload = {
            "template": (
                # Editor/detail screens require body_html; the
                # summary schema intentionally omits it for list responses.
                TemplateDetailResponseSchema
                .model_validate(template)
                .model_dump(mode="json")
            )
        }

    return cr.success(
        data=payload,
        message="System template details retrieved successfully",
    )


## ------------------------------------------------ Private Endpoints ------------------------------------------------ ##


@private_router.post(
    "/email_templates/test-email",
    response_model=CustomSuccessResponseSchema,
)
async def send_template_test_email(
    request: Request,
    body: SendTemplateTestEmailRequestSchema,
    session: AsyncSessionDep,
):
    """
    Sends saved or unsaved template content as a test email through an
    organization-owned connected email account.
    """
    async with EmailTemplateUOW(session):
        organization_container = get_organization_container(
            session
        )
        email_template_container = get_email_template_container(
            session
        )

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: SendTemplateTestEmailUseCase = (
            email_template_container
            .send_template_test_email_usecase()
        )

        result = await usecase.execute(
            payload=body,
            organization_id=request.state.organization_id,
            actor_id=request.state.user_id,
        )

        payload = (
            SendTemplateTestEmailResponseSchema
            .model_validate(result)
            .model_dump(mode="json")
        )

    return cr.success(
        data=payload,
        message="Template test email sent successfully",
    )


@private_router.post(
    "/templates/",
    response_model=CustomSuccessResponseSchema,
)
async def create_template(
    request: Request,
    body: CreateTemplateRequestSchema,
    session: AsyncSessionDep,
):
    """
    Endpoint for creating an organization-owned custom template.
    """
    async with EmailTemplateUOW(session):
        organization_container = get_organization_container(
            session
        )
        email_template_container = get_email_template_container(
            session
        )

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: CreateTemplateUseCase = (
            email_template_container.create_template_usecase()
        )

        template = await usecase.execute(
            payload=body,
            organization_id=request.state.organization_id,
            actor_id=request.state.user_id,
        )

        payload = {
            "template": (
                TemplateResponseSchema
                .model_validate(template)
                .model_dump(mode="json")
            )
        }

    return cr.success(
        data=payload,
        message="Email template created successfully",
        status_code=HTTP_201_CREATED,
    )


@private_router.get(
    "/templates/",
    response_model=CustomSuccessResponseSchema,
)
async def list_templates(
    request: Request,
    session: AsyncSessionDep,
    template_status: Annotated[
        TemplateStatusEnum | None,
        Query(alias="status"),
    ] = None,
    category_id: Annotated[
        int | None,
        Query(ge=1),
    ] = None,
    search: Annotated[
        str | None,
        Query(),
    ] = None,
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
):
    """
    Endpoint for listing active organization's custom templates.
    """
    async with EmailTemplateUOW(session):
        organization_container = get_organization_container(
            session
        )
        email_template_container = get_email_template_container(
            session
        )

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: ListTemplatesUseCase = (
            email_template_container.list_templates_usecase()
        )

        templates, total = await usecase.execute(
            organization_id=request.state.organization_id,
            status=(
                template_status.value
                if template_status
                else None
            ),
            category_id=category_id,
            search=search,
            limit=limit,
            offset=offset,
        )

        items = [
            TemplateResponseSchema.model_validate(template)
            for template in templates
        ]

        payload = TemplateListResponseSchema(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        ).model_dump(mode="json")

    return cr.success(
        data=payload,
        message="Email templates listed successfully",
    )

@private_router.get(
    "/templates/dashboard-summary",
    response_model=CustomSuccessResponseSchema,
)
async def get_template_dashboard_summary(
    request: Request,
    session: AsyncSessionDep,
):
    """
    Endpoint for retrieving template dashboard statistics.
    """
    async with EmailTemplateUOW(session):
        organization_container = get_organization_container(
            session
        )
        email_template_container = (
            get_email_template_container(
                session
            )
        )

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: GetTemplateDashboardSummaryUseCase = (
            email_template_container
            .get_template_dashboard_summary_usecase()
        )

        result = await usecase.execute(
            organization_id=(
                request.state.organization_id
            ),
        )

        payload = (
            TemplateDashboardSummaryResponseSchema
            .model_validate(result)
            .model_dump(mode="json")
        )

    return cr.success(
        data=payload,
        message=(
            "Template dashboard summary retrieved successfully"
        ),
    )

@private_router.get(
    "/templates/{template_uuid:str}",
    response_model=CustomSuccessResponseSchema,
)
async def get_template_details(
    request: Request,
    template_uuid: str,
    session: AsyncSessionDep,
):
    """
    Endpoint for retrieving an organization-owned custom template.
    """
    async with EmailTemplateUOW(session):
        organization_container = get_organization_container(
            session
        )
        email_template_container = get_email_template_container(
            session
        )

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: GetTemplateDetailsUseCase = (
            email_template_container
            .get_template_details_usecase()
        )

        template = await usecase.execute(
            template_uuid=template_uuid,
            organization_id=request.state.organization_id,
        )

        payload = {
            "template": (
                # Use the detail schema only on the detail
                # endpoint so saved HTML can be loaded back into the editor.
                TemplateDetailResponseSchema
                .model_validate(template)
                .model_dump(mode="json")
            )
        }

    return cr.success(
        data=payload,
        message="Email template details retrieved successfully",
    )


@private_router.patch(
    "/templates/{template_uuid:str}",
    response_model=CustomSuccessResponseSchema,
)
async def edit_template_details(
    request: Request,
    template_uuid: str,
    body: UpdateTemplateRequestSchema,
    session: AsyncSessionDep,
):
    """
    Endpoint for editing an organization-owned custom template.
    """
    async with EmailTemplateUOW(session):
        organization_container = get_organization_container(
            session
        )
        email_template_container = get_email_template_container(
            session
        )

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: EditTemplateDetailsUseCase = (
            email_template_container
            .edit_template_details_usecase()
        )

        template = await usecase.execute(
            template_uuid=template_uuid,
            payload=body,
            organization_id=request.state.organization_id,
            actor_id=request.state.user_id,
        )

        payload = {
            "template": (
                TemplateResponseSchema
                .model_validate(template)
                .model_dump(mode="json")
            )
        }

    return cr.success(
        data=payload,
        message="Email template updated successfully",
    )


@private_router.post(
    "/templates/{template_uuid:str}/publish",
    response_model=CustomSuccessResponseSchema,
)
async def publish_template(
    request: Request,
    template_uuid: str,
    session: AsyncSessionDep,
):
    """
    Endpoint for publishing a custom template.
    """
    async with EmailTemplateUOW(session):
        organization_container = get_organization_container(
            session
        )
        email_template_container = get_email_template_container(
            session
        )

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: PublishTemplateUseCase = (
            email_template_container.publish_template_usecase()
        )

        template = await usecase.execute(
            template_uuid=template_uuid,
            organization_id=request.state.organization_id,
            actor_id=request.state.user_id,
        )

        payload = {
            "template": (
                TemplateResponseSchema
                .model_validate(template)
                .model_dump(mode="json")
            )
        }

    return cr.success(
        data=payload,
        message="Email template published successfully",
    )


@private_router.get(
    "/templates/{template_uuid:str}/campaign-usage",
    response_model=CustomSuccessResponseSchema,
)
async def get_template_campaign_usage(
    request: Request,
    template_uuid: str,
    session: AsyncSessionDep,
):
    """Returns whether an unfinished campaign still depends on the template."""
    async with EmailTemplateUOW(session):
        organization_container = get_organization_container(session)
        email_template_container = get_email_template_container(session)
        await _load_current_organization_context(
            request=request, organization_container=organization_container,
        )
        domain_service = email_template_container.template_domain_service()
        template = await domain_service.get_custom_template_by_uuid(
            template_uuid=template_uuid, organization_id=request.state.organization_id,
        )
        if not template or template.id is None:
            from src.shared.exceptions.base_exceptions import NotFoundError
            raise NotFoundError(error="Template not found")
        usage_count = await email_template_container.template_repository().count_campaign_usages(
            template_id=template.id, organization_id=request.state.organization_id,
        )
    return cr.success(
        data={"in_use": usage_count > 0, "usage_count": usage_count},
        message="Template campaign usage retrieved successfully",
    )


@private_router.post(
    "/templates/{template_uuid:str}/archive",
    response_model=CustomSuccessResponseSchema,
)
async def archive_template(
    request: Request,
    template_uuid: str,
    session: AsyncSessionDep,
):
    """
    Endpoint for archiving a custom template.
    """
    async with EmailTemplateUOW(session):
        organization_container = get_organization_container(
            session
        )
        email_template_container = get_email_template_container(
            session
        )

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: ArchiveTemplateUseCase = (
            email_template_container.archive_template_usecase()
        )

        template = await usecase.execute(
            template_uuid=template_uuid,
            organization_id=request.state.organization_id,
            actor_id=request.state.user_id,
        )

        payload = {
            "template": (
                TemplateResponseSchema
                .model_validate(template)
                .model_dump(mode="json")
            )
        }

    return cr.success(
        data=payload,
        message="Email template archived successfully",
    )


@private_router.post(
    "/templates/{template_uuid:str}/duplicate",
    response_model=CustomSuccessResponseSchema,
)
async def duplicate_template(
    request: Request,
    template_uuid: str,
    session: AsyncSessionDep,
    body: DuplicateTemplateRequestSchema | None = None,
):
    """
    Endpoint for duplicating a custom template as a new draft.

    Downloadable attachment records are not copied.
    """
    async with EmailTemplateUOW(session):
        organization_container = get_organization_container(
            session
        )
        email_template_container = get_email_template_container(
            session
        )

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: DuplicateTemplateUseCase = (
            email_template_container
            .duplicate_template_usecase()
        )

        duplicate_payload = (
            body or DuplicateTemplateRequestSchema()
        )

        template = await usecase.execute(
            template_uuid=template_uuid,
            payload=duplicate_payload,
            organization_id=request.state.organization_id,
            actor_id=request.state.user_id,
        )

        payload = {
            "template": (
                TemplateResponseSchema
                .model_validate(template)
                .model_dump(mode="json")
            )
        }

    return cr.success(
        data=payload,
        message="Email template duplicated successfully",
        status_code=HTTP_201_CREATED,
    )


@private_router.post(
    "/templates/{template_uuid:str}/restore",
    response_model=CustomSuccessResponseSchema,
)
async def restore_template(
    request: Request,
    template_uuid: str,
    session: AsyncSessionDep,
):
    """
    Endpoint for restoring an archived custom template back to draft.
    """
    async with EmailTemplateUOW(session):
        organization_container = get_organization_container(
            session
        )
        email_template_container = get_email_template_container(
            session
        )

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: RestoreTemplateUseCase = (
            email_template_container.restore_template_usecase()
        )

        template = await usecase.execute(
            template_uuid=template_uuid,
            organization_id=request.state.organization_id,
            actor_id=request.state.user_id,
        )

        payload = {
            "template": (
                TemplateResponseSchema
                .model_validate(template)
                .model_dump(mode="json")
            )
        }

    return cr.success(
        data=payload,
        message="Email template restored successfully",
    )


@private_router.delete(
    "/templates/{template_uuid:str}",
    response_model=CustomSuccessResponseSchema,
)
async def delete_template(
    request: Request,
    template_uuid: str,
    session: AsyncSessionDep,
):
    """
    Endpoint for soft-deleting a custom template.
    """
    async with EmailTemplateUOW(session):
        organization_container = get_organization_container(
            session
        )
        email_template_container = get_email_template_container(
            session
        )

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: DeleteTemplateUseCase = (
            email_template_container.delete_template_usecase()
        )

        template = await usecase.execute(
            template_uuid=template_uuid,
            organization_id=request.state.organization_id,
            actor_id=request.state.user_id,
        )

        payload = {
            "template_uuid": template.uuid,
        }

    return cr.success(
        data=payload,
        message="Email template deleted successfully",
        status_code=HTTP_200_OK,
    )


## ------------------------------------------------ Asset Endpoints ------------------------------------------------ ##


@private_router.post(
    "/templates/{template_uuid:str}/assets",
    response_model=CustomSuccessResponseSchema,
)
async def create_template_asset(
    request: Request,
    template_uuid: str,
    session: AsyncSessionDep,
    usage: Annotated[
        TemplateAssetUsageEnum,
        Form(),
    ],
    file: Annotated[
        UploadFile,
        File(),
    ],
):
    """
    Endpoint for uploading an inline image or attachment.
    """
    content = await file.read()

    try:
        async with EmailTemplateUOW(session):
            organization_container = get_organization_container(
                session
            )
            email_template_container = (
                get_email_template_container(session)
            )

            await _load_current_organization_context(
                request=request,
                organization_container=organization_container,
            )

            usecase: CreateTemplateAssetUseCase = (
                email_template_container
                .create_template_asset_usecase()
            )

            asset_request = CreateTemplateAssetRequestSchema(
                usage=usage,
            )

            asset = await usecase.execute(
                template_uuid=template_uuid,
                payload=asset_request,
                filename=file.filename or "unnamed-file",
                content=content,
                content_type=file.content_type,
                organization_id=request.state.organization_id,
                actor_id=request.state.user_id,
            )

            payload = {
                "asset": (
                    TemplateAssetResponseSchema
                    .model_validate(asset)
                    .model_dump(mode="json")
                )
            }

    finally:
        await file.close()

    return cr.success(
        data=payload,
        message="Template asset uploaded successfully",
        status_code=HTTP_201_CREATED,
    )


@private_router.get(
    "/templates/{template_uuid:str}/assets",
    response_model=CustomSuccessResponseSchema,
)
async def list_template_assets(
    request: Request,
    template_uuid: str,
    session: AsyncSessionDep,
    asset_usage: Annotated[
        TemplateAssetUsageEnum | None,
        Query(alias="usage"),
    ] = None,
    asset_type: Annotated[
        TemplateAssetTypeEnum | None,
        Query(),
    ] = None,
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
):
    """
    Endpoint for listing template inline images and attachments.
    """
    async with EmailTemplateUOW(session):
        organization_container = get_organization_container(
            session
        )
        email_template_container = get_email_template_container(
            session
        )

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: ListTemplateAssetsUseCase = (
            email_template_container
            .list_template_assets_usecase()
        )

        assets, total = await usecase.execute(
            template_uuid=template_uuid,
            organization_id=request.state.organization_id,
            usage=(
                asset_usage.value
                if asset_usage
                else None
            ),
            asset_type=(
                asset_type.value
                if asset_type
                else None
            ),
            limit=limit,
            offset=offset,
        )

        items = [
            TemplateAssetResponseSchema.model_validate(asset)
            for asset in assets
        ]

        payload = TemplateAssetListResponseSchema(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        ).model_dump(mode="json")

    return cr.success(
        data=payload,
        message="Template assets listed successfully",
    )


@private_router.delete(
    "/templates/{template_uuid:str}/assets/{asset_uuid:str}",
    response_model=CustomSuccessResponseSchema,
)
async def delete_template_asset(
    request: Request,
    template_uuid: str,
    asset_uuid: str,
    session: AsyncSessionDep,
):
    """
    Endpoint for deleting template asset metadata and stored file.
    """
    async with EmailTemplateUOW(session):
        organization_container = get_organization_container(
            session
        )
        email_template_container = get_email_template_container(
            session
        )

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: DeleteTemplateAssetUseCase = (
            email_template_container
            .delete_template_asset_usecase()
        )

        asset = await usecase.execute(
            template_uuid=template_uuid,
            asset_uuid=asset_uuid,
            organization_id=request.state.organization_id,
            actor_id=request.state.user_id,
        )

        payload = {
            "asset_uuid": asset.uuid,
        }

    return cr.success(
        data=payload,
        message="Template asset deleted successfully",
        status_code=HTTP_200_OK,
    )


## ------------------------------------------------ System Template Copy Endpoint ------------------------------------------------ ##


@private_router.post(
    "/template-gallery/templates/{template_uuid:str}/copy",
    response_model=CustomSuccessResponseSchema,
)
async def copy_system_template(
    request: Request,
    template_uuid: str,
    session: AsyncSessionDep,
):
    """
    Endpoint for copying a system template into the active organization.

    The copied template becomes an organization-owned custom draft.
    """
    async with EmailTemplateUOW(session):
        organization_container = get_organization_container(
            session
        )
        email_template_container = get_email_template_container(
            session
        )

        await _load_current_organization_context(
            request=request,
            organization_container=organization_container,
        )

        usecase: CopySystemTemplateUseCase = (
            email_template_container
            .copy_system_template_usecase()
        )

        template = await usecase.execute(
            template_uuid=template_uuid,
            organization_id=request.state.organization_id,
            actor_id=request.state.user_id,
        )

        payload = {
            "template": (
                TemplateResponseSchema
                .model_validate(template)
                .model_dump(mode="json")
            )
        }

    return cr.success(
        data=payload,
        message="System template copied successfully",
        status_code=HTTP_201_CREATED,
    )


## ------------------------------------------------ Include Routers ------------------------------------------------ ##

router.include_router(protected_router)
router.include_router(private_router)
