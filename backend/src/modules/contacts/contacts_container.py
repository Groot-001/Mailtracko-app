from dependency_injector import containers, providers as p
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contacts.application.usecases.core.create_contact_list_usecase import (
    CreateContactListUseCase,
)
from src.modules.contacts.application.usecases.core.delete_contact_list_usecase import (
    DeleteContactListUseCase,
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
from src.modules.contacts.application.usecases.core.import_sheet_usecase import (
    ImportSheetUseCase,
)
from src.modules.contacts.application.usecases.core.initiate_sheets_oauth_usecase import (
    InitiateSheetsOAuthUseCase,
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
from src.modules.contacts.application.usecases.core.list_sheet_tabs_usecase import (
    ListSheetTabsUseCase,
)
from src.modules.contacts.application.usecases.core.sheets_oauth_callback_usecase import (
    SheetsOAuthCallbackUseCase,
)
from src.modules.contacts.application.usecases.core.create_contact_usecase import (
    CreateContactUseCase,
)
from src.modules.contacts.application.usecases.core.update_contact_list_usecase import (
    UpdateContactListUseCase,
)
from src.modules.contacts.application.usecases.core.delete_contact_usecase import (
    DeleteContactUseCase,
)
from src.modules.contacts.domain.services.contact_domain_service import (
    ContactDomainService,
)
from src.modules.contacts.domain.services.contact_list_domain_service import (
    ContactListDomainService,
)
from src.modules.contacts.infrastructure.oauth.google_sheets_oauth_client import (
    GoogleSheetsOAuthClient,
)
from src.modules.contacts.infrastructure.repositories.contact_activity_repository_impl import (
    ContactActivityRepositoryImpl,
)
from src.modules.contacts.infrastructure.repositories.contact_import_log_repository_impl import (
    ContactImportLogRepositoryImpl,
)
from src.modules.contacts.infrastructure.repositories.contact_list_repository_impl import (
    ContactListRepositoryImpl,
)
from src.modules.contacts.infrastructure.repositories.contact_repository_impl import (
    ContactRepositoryImpl,
)
from src.modules.email_account.infrastructure.repositories.oauth_config_repository_impl import (
    OauthConfigRepositoryImpl,
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


class ContactContainer(containers.DeclarativeContainer):
    """DI container for contacts module dependencies."""

    session = p.Dependency(instance_of=AsyncSession)

    # Repositories
    contact_list_repo = p.Factory(ContactListRepositoryImpl, session=session)
    contact_repo = p.Factory(ContactRepositoryImpl, session=session)
    contact_activity_repo = p.Factory(ContactActivityRepositoryImpl, session=session)
    contact_import_log_repo = p.Factory(ContactImportLogRepositoryImpl, session=session)
    oauth_config_repo = p.Factory(OauthConfigRepositoryImpl, session=session)
    organization_repo = p.Factory(OrganizationRepositoryImpl, session=session)
    organization_member_repo = p.Factory(
        OrganizationMemberRepositoryImpl, session=session
    )

    # Domain services
    contact_domain_service = p.Factory(
        ContactDomainService,
        repository=contact_repo,
    )
    contact_list_domain_service = p.Factory(
        ContactListDomainService,
        repository=contact_list_repo,
    )
    organization_domain_service = p.Factory(
        OrganizationDomainService,
        repository=organization_repo,
    )
    organization_member_domain_service = p.Factory(
        OrganizationMemberDomainService,
        repository=organization_member_repo,
    )

    # OAuth clients
    google_sheets_oauth_client = p.Singleton(GoogleSheetsOAuthClient)

    # Use cases
    create_contact_list_usecase = p.Factory(
        CreateContactListUseCase,
        contact_list_domain_service=contact_list_domain_service,
    )
    get_contact_list_usecase = p.Factory(
        GetContactListUseCase,
        contact_list_domain_service=contact_list_domain_service,
    )
    update_contact_list_usecase = p.Factory(
        UpdateContactListUseCase,
        contact_list_domain_service=contact_list_domain_service,
    )
    delete_contact_list_usecase = p.Factory(
        DeleteContactListUseCase,
        contact_list_domain_service=contact_list_domain_service,
    )
    list_contact_lists_usecase = p.Factory(
        ListContactListsUseCase,
        contact_list_domain_service=contact_list_domain_service,
    )
    list_contacts_usecase = p.Factory(
        ListContactsUseCase,
        contact_list_domain_service=contact_list_domain_service,
        contact_repo=contact_repo,
    )
    create_contact_usecase = p.Factory(
        CreateContactUseCase,
        contact_list_domain_service=contact_list_domain_service,
        contact_domain_service=contact_domain_service,
    )
    export_contacts_usecase = p.Factory(
        ExportContactsUseCase,
        contact_list_domain_service=contact_list_domain_service,
        contact_repo=contact_repo,
    )
    import_contacts_usecase = p.Factory(
        ImportContactsUseCase,
        contact_list_domain_service=contact_list_domain_service,
        contact_domain_service=contact_domain_service,
        import_log_repo=contact_import_log_repo,
        contact_activity_repo=contact_activity_repo,
    )
    list_contact_timeline_usecase = p.Factory(
        ListContactTimelineUseCase,
        contact_list_domain_service=contact_list_domain_service,
        contact_repo=contact_repo,
        contact_activity_repo=contact_activity_repo,
    )
    initiate_sheets_oauth_usecase = p.Factory(
        InitiateSheetsOAuthUseCase,
        google_sheets_oauth_client=google_sheets_oauth_client,
    )
    sheets_oauth_callback_usecase = p.Factory(
        SheetsOAuthCallbackUseCase,
        google_sheets_oauth_client=google_sheets_oauth_client,
        oauth_config_repo=oauth_config_repo,
    )
    list_sheet_tabs_usecase = p.Factory(
        ListSheetTabsUseCase,
        google_sheets_oauth_client=google_sheets_oauth_client,
        oauth_config_repo=oauth_config_repo,
    )
    import_sheet_usecase = p.Factory(
        ImportSheetUseCase,
        contact_list_domain_service=contact_list_domain_service,
        contact_domain_service=contact_domain_service,
        import_log_repo=contact_import_log_repo,
        google_sheets_oauth_client=google_sheets_oauth_client,
        oauth_config_repo=oauth_config_repo,
        contact_activity_repo=contact_activity_repo,
    )
    delete_contact_usecase = p.Factory(
        DeleteContactUseCase,
        contact_repo=contact_repo,
        contact_list_domain_service=contact_list_domain_service,
    )


def get_contact_container(session: AsyncSession) -> ContactContainer:
    """Create and return a configured ContactContainer instance."""
    container = ContactContainer()
    container.session.override(session)
    return container
