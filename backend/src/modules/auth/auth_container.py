from dependency_injector import containers, providers as p
from sqlalchemy.ext.asyncio import AsyncSession


from src.modules.auth.application.usecases.password.forgot_password_usecase import (
    ForgotPasswordUseCase,
)
from src.modules.auth.application.usecases.password.verify_forgot_password_usecase import (
    VerifyForgotPasswordUseCase,
)
from src.modules.auth.application.usecases.session.list_sessions_usecase import (
    GetCurrentSessionUseCase,
    ListSessionsUseCase,
)
from src.modules.auth.application.usecases.core.login_user_usecase import (
    LoginUserUseCase,
)
from src.modules.auth.application.usecases.core.logout_user_usecase import (
    LogoutUserUseCase,
)
from src.modules.auth.application.usecases.oauth.oauth_usecase import (
    OAuthCallbackUseCase,
    OAuthLoginUseCase,
)
from src.modules.auth.infrastructure.oauth.google_oauth_client import GoogleOAuthClient
from src.modules.auth.application.usecases.core.get_current_user_usecase import (
    GetCurrentUserUseCase,
)
from src.modules.auth.application.usecases.core.register_user_usecase import (
    RegisterUserUseCase,
)

from src.modules.auth.application.usecases.session.revoke_session_usecase import (
    RevokeAllSessionsUseCase,
    RevokeSessionUseCase,
)
from src.modules.auth.application.usecases.session.revoke_other_sessions_usecase import (
    RevokeOtherSessionsUseCase,
)
from src.modules.auth.application.usecases.core.list_user_activities_usecase import (
    ListUserActivitiesUseCase,
)
from src.modules.auth.application.usecases.core.change_password_usecase import (
    ChangePasswordUseCase,
)
from src.modules.auth.application.usecases.core.disable_totp_usecase import (
    DisableTotpUseCase,
)
from src.modules.auth.application.usecases.core.setup_totp_usecase import (
    SetupTotpUseCase,
)
from src.modules.auth.application.usecases.core.update_profile_usecase import (
    UpdateProfileUseCase,
)
from src.modules.auth.application.usecases.core.verify_2fa_login_usecase import (
    Verify2FALoginUseCase,
)
from src.modules.auth.application.usecases.core.verify_and_enable_totp_usecase import (
    VerifyAndEnableTotpUseCase,
)
from src.modules.auth.application.usecases.core.delete_account_usecase import (
    DeleteAccountUseCase,
)
from src.modules.auth.application.usecases.email.verify_email_usecase import (
    ResendVerificationUseCase,
    VerifyEmailUseCase,
)
from src.modules.auth.domain.services.user_account_domain_service import (
    UserAccountDomainService,
)
from src.modules.auth.domain.services.user_domain_service import UserDomainService
from src.modules.auth.domain.services.user_session_domain_service import (
    UserSessionDomainService,
)
from src.modules.auth.domain.services.user_token_domain_service import (
    UserTokenDomainService,
)
from src.modules.auth.infrastructure.repositories.user_account_repository_impl import (
    UserAccountRepository,
)
from src.modules.auth.infrastructure.repositories.user_activity_repository_impl import (
    UserActivityRepositoryImpl,
)
from src.modules.auth.infrastructure.repositories.user_repository_impl import (
    UserRepository,
)
from src.shared.infrastructure.hasher.hasher import HasherService
from src.modules.auth.infrastructure.repositories.user_session_repository_impl import (
    UserSessionRepository,
)
from src.modules.auth.infrastructure.repositories.user_token_repository_impl import (
    UserTokenRepository,
)
from src.modules.auth.infrastructure.repositories.user_totp_recovery_code_repository_impl import (
    UserTotpRecoveryCodeRepositoryImpl,
)
from src.modules.auth.infrastructure.repositories.user_totp_secret_repository_impl import (
    UserTotpSecretRepositoryImpl,
)
from src.modules.organization.domain.services.organization_domain_service import (
    OrganizationDomainService,
)
from src.modules.organization.domain.services.organization_member_domain_service import (
    OrganizationMemberDomainService,
)
from src.modules.organization.infrastructure.repositories.organization_member_repository_impl import (
    OrganizationMemberRepositoryImpl,
)
from src.modules.organization.infrastructure.repositories.organization_repository_impl import (
    OrganizationRepositoryImpl,
)


class AuthContainer(containers.DeclarativeContainer):
    """DI container for authentication module dependencies."""

    config = p.Configuration()
    session = p.Dependency(instance_of=AsyncSession)

    # Repositories
    user_repository = p.Factory(UserRepository, session=session)
    user_account_repository = p.Factory(UserAccountRepository, session=session)
    user_session_repository = p.Factory(UserSessionRepository, session=session)
    user_token_repository = p.Factory(UserTokenRepository, session=session)
    user_activity_repository = p.Factory(UserActivityRepositoryImpl, session=session)
    user_totp_secret_repository = p.Factory(UserTotpSecretRepositoryImpl, session=session)
    user_totp_recovery_code_repository = p.Factory(UserTotpRecoveryCodeRepositoryImpl, session=session)
    organization_repository = p.Factory(OrganizationRepositoryImpl, session=session)
    organization_member_repository = p.Factory(OrganizationMemberRepositoryImpl, session=session)

    # Services
    hasher_service = p.Factory(HasherService)
    google_oauth_client = p.Singleton(GoogleOAuthClient)

    # Domain services
    user_domain_service = p.Factory(
        UserDomainService, repository=user_repository, hasher_service=hasher_service
    )
    organization_domain_service = p.Factory(
        OrganizationDomainService, repository=organization_repository
    )
    organization_member_domain_service = p.Factory(
        OrganizationMemberDomainService, repository=organization_member_repository
    )
    user_account_domain_service = p.Factory(
        UserAccountDomainService, repository=user_account_repository
    )
    user_session_domain_service = p.Factory(
        UserSessionDomainService, repository=user_session_repository
    )
    user_token_domain_service = p.Factory(
        UserTokenDomainService, repository=user_token_repository, hasher_service=hasher_service
    )

    # Use cases
    register_user_usecase = p.Factory(
        RegisterUserUseCase,
        user_domain_service=user_domain_service,
        user_account_domain_service=user_account_domain_service,
        user_session_domain_service=user_session_domain_service,
        user_token_domain_service=user_token_domain_service,
    )
    get_current_user_usecase = p.Factory(
        GetCurrentUserUseCase,
        user_domain_service=user_domain_service,
        organization_member_domain_service=organization_member_domain_service,
        organization_domain_service=organization_domain_service,
        totp_repo=user_totp_secret_repository,
    )
    login_user_usecase = p.Factory(
        LoginUserUseCase,
        user_domain_service=user_domain_service,
        user_account_domain_service=user_account_domain_service,
        user_session_domain_service=user_session_domain_service,
        user_activity_repo=user_activity_repository,
        totp_repo=user_totp_secret_repository,
    )
    logout_user_usecase = p.Factory(
        LogoutUserUseCase,
        user_session_domain_service=user_session_domain_service,
    )
    update_profile_usecase = p.Factory(
        UpdateProfileUseCase,
        user_domain_service=user_domain_service,
        user_activity_repo=user_activity_repository,
    )
    list_user_activities_usecase = p.Factory(
        ListUserActivitiesUseCase,
        user_activity_repo=user_activity_repository,
    )
    change_password_usecase = p.Factory(
        ChangePasswordUseCase,
        user_domain_service=user_domain_service,
        user_account_domain_service=user_account_domain_service,
        user_session_domain_service=user_session_domain_service,
        hasher_service=hasher_service,
        user_activity_repo=user_activity_repository,
    )
    setup_totp_usecase = p.Factory(
        SetupTotpUseCase,
        totp_repo=user_totp_secret_repository,
        recovery_code_repo=user_totp_recovery_code_repository,
        hasher_service=hasher_service,
    )
    verify_and_enable_totp_usecase = p.Factory(
        VerifyAndEnableTotpUseCase,
        totp_repo=user_totp_secret_repository,
        user_activity_repo=user_activity_repository,
    )
    disable_totp_usecase = p.Factory(
        DisableTotpUseCase,
        totp_repo=user_totp_secret_repository,
        user_activity_repo=user_activity_repository,
        recovery_code_repo=user_totp_recovery_code_repository,
    )
    verify_2fa_login_usecase = p.Factory(
        Verify2FALoginUseCase,
        user_domain_service=user_domain_service,
        user_session_domain_service=user_session_domain_service,
        totp_repo=user_totp_secret_repository,
        recovery_code_repo=user_totp_recovery_code_repository,
        hasher_service=hasher_service,
    )
    forgot_password_usecase = p.Factory(
        ForgotPasswordUseCase,
        user_domain_service=user_domain_service,
        user_token_domain_service=user_token_domain_service,
    )
    verify_forgot_password_usecase = p.Factory(
        VerifyForgotPasswordUseCase,
        user_domain_service=user_domain_service,
        user_account_domain_service=user_account_domain_service,
        user_session_domain_service=user_session_domain_service,
        user_token_domain_service=user_token_domain_service,
    )
    verify_email_usecase = p.Factory(
        VerifyEmailUseCase,
        user_domain_service=user_domain_service,
        user_token_domain_service=user_token_domain_service,
    )
    resend_verification_usecase = p.Factory(
        ResendVerificationUseCase,
        user_domain_service=user_domain_service,
        user_token_domain_service=user_token_domain_service,
    )
    oauth_login_usecase = p.Factory(
        OAuthLoginUseCase,
        google_oauth_client=google_oauth_client,
    )
    oauth_callback_usecase = p.Factory(
        OAuthCallbackUseCase,
        user_domain_service=user_domain_service,
        user_account_domain_service=user_account_domain_service,
        google_oauth_client=google_oauth_client,
    )
    delete_account_usecase = p.Factory(
        DeleteAccountUseCase,
        user_domain_service=user_domain_service,
        user_session_domain_service=user_session_domain_service,
        organization_member_domain_service=organization_member_domain_service,
    )
    list_sessions_usecase = p.Factory(
        ListSessionsUseCase,
        user_session_domain_service=user_session_domain_service,
    )
    get_current_session_usecase = p.Factory(
        GetCurrentSessionUseCase,
        user_session_domain_service=user_session_domain_service,
    )
    revoke_session_usecase = p.Factory(
        RevokeSessionUseCase,
        user_session_domain_service=user_session_domain_service,
    )
    revoke_all_sessions_usecase = p.Factory(
        RevokeAllSessionsUseCase,
        user_session_domain_service=user_session_domain_service,
    )
    revoke_other_sessions_usecase = p.Factory(
        RevokeOtherSessionsUseCase,
        user_session_domain_service=user_session_domain_service,
    )


def get_auth_container(session: AsyncSession) -> AuthContainer:
    """Create and return a configured AuthContainer instance."""
    container = AuthContainer()
    container.session.override(session)
    return container
