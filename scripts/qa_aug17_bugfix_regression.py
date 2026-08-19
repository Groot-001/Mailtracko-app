"""Static regression checks for the August 17 MailTracko bug-fix pass."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    contact_router = read("backend/src/modules/contacts/presentation/routers/contact_list_routers.py")
    contact_ui = read("frontend/src/feature/contacts/components/ContactsDashboard.tsx")
    require("CONTACT_LIST_IN_USE" in contact_router and "force: bool = Query(default=False)" in contact_router,
            "contact collections must be protected when unfinished campaigns depend on them")
    require("Delete Anyway" in contact_ui and "getContactListCampaignUsage" in contact_ui,
            "contact deletion UI must show the explicit campaign dependency warning")
    require("confirmDeleteCollection" in contact_ui and "pendingDeleteCampaignWarning" in contact_ui
            and contact_ui.index('title="Delete Collection?"') < contact_ui.index('title="This collection is being used by a campaign"'),
            "contact deletion must use normal confirmation first, then a second campaign warning when needed")
    require("delete_contacts" in contact_router and "CONTACT_DELETE_PERMISSION_REQUIRED" in contact_router,
            "contact deletion must be permission-protected without removing normal member contact workflows")

    template_repo = read("backend/src/modules/email_template/infrastructure/repositories/template_repository_impl.py")
    template_ui = read("frontend/src/feature/templates/components/TemplateDashboard.tsx")
    require("CampaignStatus.COMPLETED.value" in template_repo and "CampaignStatus.ARCHIVED.value" in template_repo,
            "completed/terminal campaigns must stop blocking template lifecycle actions")
    require("Archived Templates" in template_ui and "Unarchive" in template_ui,
            "templates need a dedicated archive management section")
    require("archiveTarget" in template_ui and "restoreTarget" in template_ui,
            "archive and unarchive actions must require confirmation")
    require("getTemplateCampaignUsage" in template_ui and "blockedLifecycle" in template_ui
            and "Template is being used by a campaign" in template_ui,
            "template archive/delete must show a blocking campaign-in-use popup before destructive confirmation")
    template_gallery_router = read("backend/src/modules/email_template/presentation/routers/email_template_routers.py")
    gallery_usecase = read("backend/src/modules/email_template/application/usecases/gallery/list_system_templates_usecase.py")
    gallery_block = template_gallery_router.split('async def list_system_templates(', 1)[1].split('@protected_router.get', 1)[0]
    require("include_archived=include_archived" not in gallery_block and "include_archived" not in gallery_usecase,
            "system template gallery must not pass unsupported include_archived arguments")

    campaign_service = read("backend/src/modules/campaign/application/services/campaign_service.py")
    campaign_repo = read("backend/src/modules/campaign/infrastructure/repositories/campaign_repository_impl.py")
    campaign_ui = read("frontend/src/feature/campaigns/components/CampaignDashboard.tsx")
    wizard = read("frontend/src/feature/campaigns/components/CampaignWizard.tsx")
    require("restore_campaign" in campaign_service and "Restore Campaign" in campaign_ui,
            "archived campaigns must be restorable")
    require("CampaignModel.status != CampaignStatus.ARCHIVED.value" in campaign_repo,
            "active campaign list must exclude archived campaigns")
    require("Save as Draft" in wizard and "useBlocker" in wizard,
            "leaving a dirty campaign wizard must ask whether to save a draft")

    logo_router = read("backend/src/modules/organization/presentation/routers/organization_routers.py")
    logo_ui = read("frontend/src/feature/organization/components/settings/OrganizationSettings.tsx")
    require("Save changes to apply it" in logo_router,
            "logo upload must not immediately persist organization settings")
    require("markDirty" in logo_ui,
            "uploaded logo must remain local dirty form state until Save Changes")

    force_login = read("frontend/src/shared/auth/forceLogin.ts")
    registration = read("frontend/src/feature/login/hooks/useregister.ts")
    login_route = read("frontend/src/routes/login.tsx")
    require("mailtracko_force_login_until_authenticated" in force_login and "forceNextLoginScreen" in registration,
            "invitation registration must explicitly force the login screen")
    require("shouldForceLoginScreen" in login_route,
            "existing browser sessions must not bypass forced post-invitation login")

    perms = read("backend/src/modules/platform/application/workspace_permissions.py")
    workspace = read("backend/src/modules/platform/presentation/workspace_routers.py")
    migration = read("backend/migrations/versions/d1e2f3a4b5c6_member_permission_overrides.py")
    require("manage_member_permissions" in perms and "update_member_permissions" in workspace,
            "fine-grained owner/admin/member permission delegation must exist")
    require("permissions" in migration and "op.add_column" in migration,
            "member permission overrides require a database migration")
    require('"manage_campaigns": True' in perms and '"manage_contacts": True' in perms and '"manage_templates": True' in perms and '"delete_contacts": False' in perms,
            "member defaults must preserve normal product workflows while restricting destructive contact deletion")

    oauth_backend = read("backend/src/modules/email_account/presentation/routers/email_account_routers.py")
    oauth_ui = read("frontend/src/feature/email-accounts/components/EmailAccountsDashboard.tsx")
    require("oauth_account_already_connected" in oauth_backend and "already connected to your organization" in oauth_ui,
            "already-connected OAuth account errors must survive callback handling")

    onboarding = read("frontend/src/feature/onboarding/components/Step6ThemeSelection.tsx")
    onboarding_layout = read("frontend/src/feature/onboarding/components/OnboardingLayout.tsx")
    require('id: "light"' in onboarding and 'id: "dark"' in onboarding and "Executive Light" not in onboarding and "Midnight Focus" not in onboarding,
            "onboarding must expose only the backend-supported Light and Dark themes")
    require("validationSteps" in onboarding_layout and "onboarding.setStep(invalid.step)" in onboarding_layout and "Step ${invalid.step}" in onboarding_layout,
            "onboarding launch validation must identify and navigate to the failing setup step")
    appearance_store = read("frontend/src/shared/store/UiPreferencesStore.ts")
    appearance_page = read("frontend/src/routes/_protected/organization/account-settings/preferences.tsx")
    require("compactDensity" not in appearance_store and "reduceMotion" not in appearance_store and "showSidebarIcons" not in appearance_store,
            "unused display preferences must be removed from shared state")
    require('id: "light"' in appearance_page and 'id: "dark"' in appearance_page and "Save appearance" in appearance_page,
            "Light/Dark appearance choices must remain editable after onboarding")

    notifications = read("frontend/src/feature/organization/components/notifications/NotificationsPage.tsx")
    workspace = read("backend/src/modules/platform/presentation/workspace_routers.py")
    require('Personal' in notifications and 'Organization' in notifications and 'System' in notifications,
            "notifications must separate personal, organization, and system activity")
    require("member_role_changed" in workspace and "OrganizationActivityModel" in workspace,
            "member role changes must be written to organization activity")


    security = read("frontend/src/feature/organization/components/account-settings/SecuritySettings.tsx")
    require("Sign out other devices?" in security and "postPasswordSignOutPromptOpen" in security,
            "password change must offer to sign out other active sessions")

    editor = read("frontend/src/feature/templates/components/RichTextEditor.tsx")
    require("uploadTemplateImage" in editor and "insertImage" in editor,
            "template editor must support image/logo insertion")

    require("Import Contacts" in contact_ui and "Google Sheets" in contact_ui and "Manual" in contact_ui,
            "contacts must have a unified import entry point")
    require("silentRefresh" in contact_ui and "setInterval" in contact_ui,
            "non-editing contact data must refresh safely in the background without a loading flash")

    sheets_client = read("backend/src/modules/contacts/infrastructure/oauth/google_sheets_oauth_client.py")
    sheets_callback = read("backend/src/modules/contacts/application/usecases/core/sheets_oauth_callback_usecase.py")
    require('quote(range_, safe="")' in sheets_client and "Google Sheet cannot be accessed" in sheets_client,
            "Google Sheets URLs/tabs must be safely encoded with actionable access errors")
    require('get_by_context(' in sheets_callback and 'purpose="google_sheets"' in sheets_callback and "sheets_token_org" not in sheets_callback,
            "Google Sheets connection ownership must be persisted in the database rather than Redis")

    contact_router = read("backend/src/modules/contacts/presentation/routers/contact_list_routers.py")
    require("from src.modules.platform.application.workspace_permissions import effective_workspace_permissions" in contact_router,
            "contacts router must import the workspace permission helper it executes")

    onboarding_hook = read("frontend/src/feature/onboarding/hooks/useOnboarding.ts")
    onboarding_store = read("frontend/src/feature/onboarding/store/onboardingStore.ts")
    member_repo = read("backend/src/modules/organization/infrastructure/repositories/organization_member_repository_impl.py")
    require("skipOnboarding" in onboarding_hook and "store.setSkipped(true)" in onboarding_hook and "store.setStep(7)" in onboarding_hook,
            "Skip onboarding must skip data entry and go to Step 7 without creating the workspace")
    require('organizationName: store.organization.organizationName.trim() || "My Workspace"' in onboarding_hook,
            "skipped onboarding must apply a safe internal workspace name only when Launch Workspace is confirmed")
    require("isSkipped" in onboarding_store and "if (!onboarding.isSkipped)" in onboarding_layout,
            "skipped onboarding must not validate optional skipped steps")
    skip_handler = onboarding_layout.split("const handleSkipOnboarding", 1)[1].split("const handleLaunchWorkspace", 1)[0]
    require('navigate({ to: "/dashboard"' not in skip_handler and "onboarding.skipOnboarding()" in skip_handler,
            "Skip must never navigate directly to Dashboard; Step 7 Launch Workspace remains mandatory")
    require("onSkip={handleSkipOnboarding}" in onboarding_layout and "Launch Workspace" in read("frontend/src/feature/onboarding/components/Step7ReviewFinish.tsx"),
            "Skip must finish at the Review & Finish / Launch Workspace screen")
    require("json.dumps(entity.permissions or {})" in member_repo and "_decode_permissions" in member_repo,
            "raw organization-member SQL must serialize JSON permission values for asyncpg")
    onboarding_root = ROOT / "frontend/src/feature/onboarding"
    require(not any(any(ord(ch) > 127 for ch in path.read_text(encoding="utf-8"))
                    for path in onboarding_root.rglob("*.tsx")),
            "onboarding user-facing TSX copy must remain ASCII English to avoid mojibake")

    print("ALL AUGUST 17 BUG-FIX REGRESSION CHECKS PASSED")


if __name__ == "__main__":
    main()
