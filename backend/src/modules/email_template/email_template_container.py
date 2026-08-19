from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

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
from src.modules.email_template.domain.services.template_asset_domain_service import (
    TemplateAssetDomainService,
)
from src.modules.email_template.domain.services.template_category_domain_service import (
    TemplateCategoryDomainService,
)
from src.modules.email_template.domain.services.template_domain_service import (
    TemplateDomainService,
)
from src.modules.email_template.domain.services.template_rendering_service import (
    TemplateRenderingService,
)
from src.modules.email_template.infrastructure.repositories.template_asset_repository_impl import (
    TemplateAssetRepositoryImpl,
)
from src.modules.email_template.infrastructure.repositories.template_category_repository_impl import (
    TemplateCategoryRepositoryImpl,
)
from src.modules.email_template.infrastructure.repositories.template_repository_impl import (
    TemplateRepositoryImpl,
)
from src.shared.infrastructure.storage.cloudinary_uploader import CloudinaryUploader

from src.modules.email_template.application.usecases.core.get_template_dashboard_summary_usecase import (
    GetTemplateDashboardSummaryUseCase,
)

from src.modules.email_account.email_account_container import (
    EmailAccountContainer,
)
from src.modules.email_template.application.usecases.test_email.send_template_test_email_usecase import (
    SendTemplateTestEmailUseCase,
)
from src.modules.email_template.infrastructure.email_sender.adapter.connected_email_account_test_sender import (
    ConnectedEmailAccountTestSender,
)

class EmailTemplateContainer(containers.DeclarativeContainer):
    """
    Container for email-template-related dependencies.
    """

    session = providers.Dependency(instance_of=AsyncSession)

    ## ------------------------ Repositories ------------------------ ##

    template_repository = providers.Factory(
        TemplateRepositoryImpl,
        session=session,
    )

    template_category_repository = providers.Factory(
        TemplateCategoryRepositoryImpl,
        session=session,
    )

    template_asset_repository = providers.Factory(
        TemplateAssetRepositoryImpl,
        session=session,
    )

    email_account_container = providers.Container(
        EmailAccountContainer,
        session=session,
    )

    ## ------------------------ Infrastructure Services ------------------------ ##

    uploader = providers.Factory(
        CloudinaryUploader,
    )

    test_email_sender = providers.Factory(
        ConnectedEmailAccountTestSender,
        email_account_domain_service=(
            email_account_container
            .email_account_domain_service
        ),
        google_mail_oauth_client=(
            email_account_container
            .google_mail_oauth_client
        ),
    )

    ## ------------------------ Domain Services ------------------------ ##

    template_domain_service = providers.Factory(
        TemplateDomainService,
        repository=template_repository,
    )

    template_category_domain_service = providers.Factory(
        TemplateCategoryDomainService,
        repository=template_category_repository,
    )

    template_asset_domain_service = providers.Factory(
        TemplateAssetDomainService,
        repository=template_asset_repository,
    )

    template_rendering_service = providers.Factory(
        TemplateRenderingService,
    )

    ## ------------------------ Custom Template Use Cases ------------------------ ##

    create_template_usecase = providers.Factory(
        CreateTemplateUseCase,
        template_domain_service=template_domain_service,
        template_category_domain_service=template_category_domain_service,
    )

    get_template_details_usecase = providers.Factory(
        GetTemplateDetailsUseCase,
        template_domain_service=template_domain_service,
    )

    list_templates_usecase = providers.Factory(
        ListTemplatesUseCase,
        template_domain_service=template_domain_service,
    )

    get_template_dashboard_summary_usecase = providers.Factory(
        GetTemplateDashboardSummaryUseCase,
        template_domain_service=template_domain_service,
        template_category_domain_service=(
            template_category_domain_service
        ),
    )

    edit_template_details_usecase = providers.Factory(
        EditTemplateDetailsUseCase,
        template_domain_service=template_domain_service,
        template_category_domain_service=template_category_domain_service,
    )

    publish_template_usecase = providers.Factory(
        PublishTemplateUseCase,
        template_domain_service=template_domain_service,
    )

    archive_template_usecase = providers.Factory(
        ArchiveTemplateUseCase,
        template_domain_service=template_domain_service,
    )

    restore_template_usecase = providers.Factory(
        RestoreTemplateUseCase,
        template_domain_service=template_domain_service,
    )

    duplicate_template_usecase = providers.Factory(
        DuplicateTemplateUseCase,
        template_domain_service=template_domain_service,
    )

    delete_template_usecase = providers.Factory(
        DeleteTemplateUseCase,
        template_domain_service=template_domain_service,
    )

    ## ------------------------ System Template Use Cases ------------------------ ##

    get_system_template_details_usecase = providers.Factory(
        GetSystemTemplateDetailsUseCase,
        template_domain_service=template_domain_service,
    )

    list_system_templates_usecase = providers.Factory(
        ListSystemTemplatesUseCase,
        template_domain_service=template_domain_service,
    )

    copy_system_template_usecase = providers.Factory(
        CopySystemTemplateUseCase,
        template_domain_service=template_domain_service,
    )

    ## ------------------------ Preview Use Case ------------------------ ##

    preview_template_usecase = providers.Factory(
        PreviewTemplateUseCase,
        template_rendering_service=(
            template_rendering_service
        ),
    )

    send_template_test_email_usecase = providers.Factory(
        SendTemplateTestEmailUseCase,
        preview_template_usecase=(
            preview_template_usecase
        ),
        test_email_sender=test_email_sender,
        template_rendering_service=(
            template_rendering_service
        ),
    )

    ## ------------------------ Category Use Cases ------------------------ ##

    list_template_categories_usecase = providers.Factory(
        ListTemplateCategoriesUseCase,
        template_category_domain_service=template_category_domain_service,
    )

    list_organization_template_categories_usecase = providers.Factory(
        ListOrganizationTemplateCategoriesUseCase,
        template_category_domain_service=template_category_domain_service,
    )

    create_template_category_usecase = providers.Factory(
        CreateTemplateCategoryUseCase,
        template_category_domain_service=template_category_domain_service,
    )

    ## ------------------------ Asset Use Cases ------------------------ ##

    create_template_asset_usecase = providers.Factory(
        CreateTemplateAssetUseCase,
        template_domain_service=template_domain_service,
        template_asset_domain_service=template_asset_domain_service,
        uploader=uploader,
    )

    list_template_assets_usecase = providers.Factory(
        ListTemplateAssetsUseCase,
        template_domain_service=template_domain_service,
        template_asset_domain_service=template_asset_domain_service,
    )

    delete_template_asset_usecase = providers.Factory(
        DeleteTemplateAssetUseCase,
        template_domain_service=template_domain_service,
        template_asset_domain_service=template_asset_domain_service,
        uploader=uploader,
    )


def get_email_template_container(
    session: AsyncSession,
) -> EmailTemplateContainer:
    """
    Dependency injector for Email Template Container.
    """
    email_template_container = EmailTemplateContainer()
    email_template_container.session.override(session)

    return email_template_container