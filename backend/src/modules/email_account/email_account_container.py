from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.email_account.application.usecases.crud_usecases import (
    DisconnectAccountUseCase,
    GetAccountUseCase,
    ListAccountsUseCase,
    UpdateAccountUseCase,
)
from src.modules.email_account.application.usecases.oauth_callback_usecase import OAuthCallbackUseCase
from src.modules.email_account.application.usecases.oauth_connect_usecase import OAuthConnectUseCase
from src.modules.email_account.application.usecases.resend_verification_usecase import ResendVerificationUseCase
from src.modules.email_account.application.usecases.smtp_connect_usecase import SmtpConnectUseCase
from src.modules.email_account.application.usecases.smtp_verify_usecase import SmtpVerifyUseCase
from src.modules.email_account.application.usecases.test_connection_usecase import TestConnectionUseCase
from src.modules.email_account.domain.services.email_account_domain_service import EmailAccountDomainService
from src.modules.email_account.infrastructure.oauth.google_mail_oauth_client import GoogleMailOAuthClient
from src.modules.email_account.infrastructure.repositories.email_account_repository_impl import EmailAccountRepositoryImpl
from src.modules.email_account.infrastructure.repositories.oauth_config_repository_impl import OauthConfigRepositoryImpl
from src.modules.email_account.infrastructure.repositories.smtp_config_repository_impl import SmtpConfigRepositoryImpl
from src.modules.organization.domain.services.organization_domain_service import OrganizationDomainService
from src.modules.organization.domain.services.organization_member_domain_service import OrganizationMemberDomainService
from src.modules.organization.infrastructure.repositories.organization_member_repository_impl import OrganizationMemberRepositoryImpl
from src.modules.organization.infrastructure.repositories.organization_repository_impl import OrganizationRepositoryImpl
from src.shared.infrastructure.hasher.hasher import HasherService


class EmailAccountContainer(containers.DeclarativeContainer):
    session = providers.Dependency(instance_of=AsyncSession)

    # Repositories
    email_account_repo = providers.Factory(EmailAccountRepositoryImpl, session=session)
    smtp_config_repo = providers.Factory(SmtpConfigRepositoryImpl, session=session)
    oauth_config_repo = providers.Factory(OauthConfigRepositoryImpl, session=session)
    organization_repo = providers.Factory(OrganizationRepositoryImpl, session=session)
    organization_member_repo = providers.Factory(OrganizationMemberRepositoryImpl, session=session)

    # Services
    hasher_service = providers.Factory(HasherService)
    google_mail_oauth_client = providers.Singleton(GoogleMailOAuthClient)

    # Domain services
    email_account_domain_service = providers.Factory(
        EmailAccountDomainService,
        account_repository=email_account_repo,
        smtp_config_repository=smtp_config_repo,
        oauth_config_repository=oauth_config_repo,
    )
    organization_domain_service = providers.Factory(
        OrganizationDomainService,
        repository=organization_repo,
    )
    organization_member_domain_service = providers.Factory(
        OrganizationMemberDomainService,
        repository=organization_member_repo,
    )

    # Use cases
    oauth_connect_usecase = providers.Factory(
        OAuthConnectUseCase,
        email_account_domain_service=email_account_domain_service,
        google_mail_oauth_client=google_mail_oauth_client,
    )
    test_connection_usecase = providers.Factory(
        TestConnectionUseCase,
        email_account_domain_service=email_account_domain_service,
        google_mail_oauth_client=google_mail_oauth_client,
    )
    oauth_callback_usecase = providers.Factory(
        OAuthCallbackUseCase,
        email_account_domain_service=email_account_domain_service,
        google_mail_oauth_client=google_mail_oauth_client,
        test_connection_usecase=test_connection_usecase,
    )
    smtp_connect_usecase = providers.Factory(
        SmtpConnectUseCase,
        email_account_domain_service=email_account_domain_service,
        hasher_service=hasher_service,
    )
    smtp_verify_usecase = providers.Factory(
        SmtpVerifyUseCase,
        email_account_domain_service=email_account_domain_service,
        hasher_service=hasher_service,
    )
    resend_verification_usecase = providers.Factory(
        ResendVerificationUseCase,
        email_account_domain_service=email_account_domain_service,
        hasher_service=hasher_service,
    )
    list_accounts_usecase = providers.Factory(
        ListAccountsUseCase,
        email_account_domain_service=email_account_domain_service,
    )
    get_account_usecase = providers.Factory(
        GetAccountUseCase,
        email_account_domain_service=email_account_domain_service,
    )
    update_account_usecase = providers.Factory(
        UpdateAccountUseCase,
        email_account_domain_service=email_account_domain_service,
    )
    disconnect_account_usecase = providers.Factory(
        DisconnectAccountUseCase,
        email_account_domain_service=email_account_domain_service,
    )


def get_email_account_container(session: AsyncSession) -> EmailAccountContainer:
    container = EmailAccountContainer()
    container.session.override(session)
    return container