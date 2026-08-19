from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.organization.application.usecases.core.accept_organization_invitation_usecase import (
    AcceptOrganizationInvitationUseCase,
)
from src.modules.organization.application.usecases.core.create_organization_usecase import (
    CreateOrganizationUseCase,
)
from src.modules.organization.application.usecases.core.decline_organization_invitation_usecase import (
    DeclineOrganizationInvitationUseCase,
)
from src.modules.organization.application.usecases.core.edit_organization_details_usecase import (
    EditOrganizationDetailsUseCase,
)

from src.modules.organization.application.usecases.core.get_organization_details_usecase import (
    GetOrganizationDetailsUseCase,
)
from src.modules.organization.application.usecases.core.get_organization_onboarding_status_usecase import (
    GetOrganizationOnboardingStatusUseCase,
)
from src.modules.organization.application.usecases.core.invite_organization_member_usecase import (
    InviteOrganizationMemberUseCase,
)
from src.modules.organization.application.usecases.core.list_organization_invitations_usecase import (
    ListOrganizationInvitationsUseCase,
)
from src.modules.organization.application.usecases.core.list_organization_members_usecase import (
    ListOrganizationMembersUseCase,
)
from src.modules.organization.application.usecases.core.remove_organization_member_usecase import (
    RemoveOrganizationMemberUseCase,
)
from src.modules.organization.application.usecases.core.request_organization_deletion_usecase import (
    RequestOrganizationDeletionUseCase,
)
from src.modules.organization.application.usecases.core.revoke_organization_invitation_usecase import (
    RevokeOrganizationInvitationUseCase,
)
from src.modules.organization.application.usecases.core.resend_organization_invitation_usecase import (
    ResendOrganizationInvitationUseCase,
)
from src.modules.organization.domain.services.organization_domain_service import (
    OrganizationDomainService,
)
from src.modules.organization.domain.services.organization_invitation_domain_service import (
    OrganizationInvitationDomainService,
)
from src.modules.organization.domain.services.organization_member_domain_service import (
    OrganizationMemberDomainService,
)
from src.modules.organization.infrastructure.repositories.organization_invitation_repository_impl import (
    OrganizationInvitationRepositoryImpl,
)
from src.modules.organization.infrastructure.repositories.organization_member_repository_impl import (
    OrganizationMemberRepositoryImpl,
)
from src.modules.organization.infrastructure.repositories.organization_repository_impl import (
    OrganizationRepositoryImpl,
)
from src.modules.organization.application.usecases.core.list_recent_organization_activities_usecase import (
    ListRecentOrganizationActivitiesUseCase,
)
from src.modules.organization.domain.services.organization_activity_domain_service import (
    OrganizationActivityDomainService,
)
from src.modules.organization.infrastructure.repositories.organization_activity_repository_impl import (
    OrganizationActivityRepositoryImpl,
)
from src.modules.organization.application.usecases.core.get_organization_deletion_summary_usecase import (
    GetOrganizationDeletionSummaryUseCase,
)

class OrganizationContainer(containers.DeclarativeContainer):
    """
    Container for organization-related dependencies.
    """

    session = providers.Dependency(instance_of=AsyncSession)

    ## ------------------------ Repositories ------------------------ ##

    organization_repository = providers.Factory(
        OrganizationRepositoryImpl,
        session=session,
    )

    organization_member_repository = providers.Factory(
        OrganizationMemberRepositoryImpl,
        session=session,
    )

    organization_invitation_repository = providers.Factory(
        OrganizationInvitationRepositoryImpl,
        session=session,
    )
    organization_activity_repository = providers.Factory(
    OrganizationActivityRepositoryImpl,
    session=session,
)

    ## ------------------------ Domain Services ------------------------ ##

    organization_domain_service = providers.Factory(
        OrganizationDomainService,
        repository=organization_repository,
    )

    organization_member_domain_service = providers.Factory(
        OrganizationMemberDomainService,
        repository=organization_member_repository,
    )

    organization_invitation_domain_service = providers.Factory(
        OrganizationInvitationDomainService,
        repository=organization_invitation_repository,
    )
    organization_activity_domain_service = providers.Factory(
    OrganizationActivityDomainService,
    repository=organization_activity_repository,
)

    ## ------------------------ Use Cases ------------------------ ##

    create_organization_usecase = providers.Factory(
        CreateOrganizationUseCase,
        organization_domain_service=organization_domain_service,
        organization_member_domain_service=organization_member_domain_service,
    )

    get_organization_details_usecase = providers.Factory(
        GetOrganizationDetailsUseCase,
        organization_domain_service=organization_domain_service,
    )

    edit_organization_usecase = providers.Factory(
        EditOrganizationDetailsUseCase,
        organization_domain_service=organization_domain_service,
        organization_member_domain_service=organization_member_domain_service,
    )

    get_organization_deletion_summary_usecase = providers.Factory(
        GetOrganizationDeletionSummaryUseCase,
        organization_domain_service=organization_domain_service,
        organization_member_domain_service=organization_member_domain_service,
        organization_invitation_domain_service=organization_invitation_domain_service,
    )
    request_organization_deletion_usecase = providers.Factory(
        RequestOrganizationDeletionUseCase,
        organization_domain_service=organization_domain_service,
    )

    list_organization_members_usecase = providers.Factory(
        ListOrganizationMembersUseCase,
        organization_member_domain_service=organization_member_domain_service,
    )

    remove_organization_member_usecase = providers.Factory(
        RemoveOrganizationMemberUseCase,
        organization_member_domain_service=organization_member_domain_service,
    )

    invite_organization_member_usecase = providers.Factory(
        InviteOrganizationMemberUseCase,
        organization_domain_service=organization_domain_service,
        organization_invitation_domain_service=organization_invitation_domain_service,
        organization_member_domain_service=organization_member_domain_service,
    )

    accept_organization_invitation_usecase = providers.Factory(
        AcceptOrganizationInvitationUseCase,
        organization_invitation_domain_service=organization_invitation_domain_service,
        organization_member_domain_service=organization_member_domain_service,
    )

    decline_organization_invitation_usecase = providers.Factory(
        DeclineOrganizationInvitationUseCase,
        organization_invitation_domain_service=organization_invitation_domain_service,
    )

    revoke_organization_invitation_usecase = providers.Factory(
        RevokeOrganizationInvitationUseCase,
        organization_invitation_domain_service=organization_invitation_domain_service,
        organization_member_domain_service=organization_member_domain_service,
    )

    resend_organization_invitation_usecase = providers.Factory(
        ResendOrganizationInvitationUseCase,
        organization_domain_service=organization_domain_service,
        organization_invitation_domain_service=organization_invitation_domain_service,
        organization_member_domain_service=organization_member_domain_service,
    )

    list_organization_invitations_usecase = providers.Factory(
        ListOrganizationInvitationsUseCase,
        organization_invitation_domain_service=organization_invitation_domain_service,
    )

    get_organization_onboarding_status_usecase = providers.Factory(
        GetOrganizationOnboardingStatusUseCase,
        organization_domain_service=organization_domain_service,
        organization_member_domain_service=organization_member_domain_service,
        organization_invitation_domain_service=organization_invitation_domain_service,
    )
    
    list_recent_organization_activities_usecase = providers.Factory(
    ListRecentOrganizationActivitiesUseCase,
    organization_activity_domain_service=organization_activity_domain_service,
)


def get_organization_container(session: AsyncSession) -> OrganizationContainer:
    """
    Dependency injector for Organization Container.
    """
    organization_container = OrganizationContainer()
    organization_container.session.override(session)
    return organization_container
