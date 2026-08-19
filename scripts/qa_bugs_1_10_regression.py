"""Regression checks for QA Bug Report bugs 1-10.

These checks are intentionally dependency-free so they can run in release CI.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "src"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def check_upload_limits() -> None:
    files = [
        "frontend/src/feature/organization/components/settings/OrganizationSettings.tsx",
        "frontend/src/feature/onboarding/components/Step2Organization.tsx",
        "frontend/src/routes/_protected/organization/account-settings/index.tsx",
        "backend/src/modules/organization/presentation/routers/organization_routers.py",
        "backend/src/modules/auth/presentation/routers/auth_core_routers.py",
    ]
    for rel in files:
        text = read(rel)
        require("2 * 1024 * 1024" not in text, f"{rel}: still enforces 2 MB")
        require("2 MB" not in text, f"{rel}: still tells users 2 MB")
        require("5 * 1024 * 1024" in text or "5 MB" in text, f"{rel}: has no 5 MB evidence")


def check_shared_ui() -> None:
    require((ROOT / "frontend/src/shared/components/ConfirmDialog.tsx").exists(), "shared ConfirmDialog missing")
    require((ROOT / "frontend/src/shared/components/AppSelect.tsx").exists(), "shared AppSelect missing")
    require((ROOT / "frontend/src/shared/components/TextPromptDialog.tsx").exists(), "shared TextPromptDialog missing")


def check_no_native_dialogs_or_selects() -> None:
    offenders: list[str] = []
    select_offenders: list[str] = []
    for path in FRONTEND.rglob("*.tsx"):
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in ("window.confirm(", "window.alert(", "window.prompt(", "confirm(`", "confirm(\"", "confirm('")):
            offenders.append(str(path.relative_to(ROOT)))
        if "<select" in text:
            select_offenders.append(str(path.relative_to(ROOT)))
    require(not offenders, "browser-native dialogs remain: " + ", ".join(offenders))
    require(not select_offenders, "native <select> controls remain: " + ", ".join(select_offenders))


def check_team_pagination() -> None:
    team = read("frontend/src/feature/organization/components/team/TeamManagement.tsx")
    api = read("frontend/src/feature/organization/api/organizationApi.ts")
    repo = read("backend/src/modules/organization/infrastructure/repositories/organization_member_repository_impl.py")
    require("setLimit" in team, "Team Management does not maintain server page size state")
    require("offset:" in team or "offset" in team, "Team Management is not using offset pagination")
    require("search?: string" in api and "role?:" in api, "member API lacks server-side search/role filters")
    require("user_is_active" in repo or "effective_status" in repo, "member projection does not derive status from auth-user activity")




def check_shared_pagination_component() -> None:
    require((ROOT / "frontend/src/shared/components/PaginationControls.tsx").exists(), "shared PaginationControls missing")
    for rel in [
        "frontend/src/feature/organization/components/team/MembersTable.tsx",
        "frontend/src/feature/contacts/components/ContactsDashboard.tsx",
        "frontend/src/feature/campaigns/components/CampaignDashboard.tsx",
        "frontend/src/feature/templates/components/TemplateDashboard.tsx",
    ]:
        text = read(rel)
        require("PaginationControls" in text, f"{rel}: does not use shared pagination")
    for rel in [
        "frontend/src/feature/campaigns/components/CampaignDashboard.tsx",
        "frontend/src/feature/templates/components/TemplateDashboard.tsx",
    ]:
        text = read(rel)
        require("useState(10)" in text, f"{rel}: must default to 10 rows per page")
        require("pageSize" in text, f"{rel}: page size is not configurable")


def check_member_api_does_not_leak_filters_to_invitations() -> None:
    api = read("frontend/src/feature/organization/api/organizationApi.ts")
    start = api.index("export interface ListInvitationsParams")
    end = api.index("export const inviteMember", start)
    invitations_block = api[start:end]
    require("params?.role" not in invitations_block, "member role filter leaked into invitation API params")
    require("params?.search" not in invitations_block, "member search filter leaked into invitation API params")


def check_onboarding_transition() -> None:
    layout = read("frontend/src/feature/onboarding/components/OnboardingLayout.tsx")
    require("Preparing your workspace" in layout, "onboarding has no intentional workspace transition UI")


def check_csv_and_limits() -> None:
    contacts = read("frontend/src/feature/contacts/components/ContactsDashboard.tsx")
    require("Download CSV Template" in contacts, "contacts CSV action label is ambiguous")
    require("Download Template" not in contacts and "Download template" not in contacts, "old Download Template copy remains")
    require("maxLength={50}" in contacts, "collection/name form does not enforce 50 characters")


def check_save_draft_routing() -> None:
    wizard = read("frontend/src/feature/templates/components/TemplateWizard.tsx")
    require("Save Draft" in wizard, "Save Draft action missing")
    require('to: "/templates"' in wizard or 'navigate({ to: "/templates"' in wizard, "Save Draft does not route to Templates list")


def check_dark_mode_scrollbars() -> None:
    css = read("frontend/src/index.css")
    require("scrollbar-color" in css and "::-webkit-scrollbar" in css, "dark-mode scrollbar treatment missing")



def check_remaining_project_wide_patterns() -> None:
    asset_usecase = read("backend/src/modules/email_template/application/usecases/assets/create_template_asset_usecase.py")
    require("5 * 1024 * 1024" in asset_usecase, "template asset uploads are not capped at 5 MB")

    for rel in [
        "frontend/src/feature/contacts/components/SuppressionList.tsx",
        "frontend/src/feature/organization/components/team/PendingInvites.tsx",
        "frontend/src/routes/_protected/organization/account-settings/api-integrations.tsx",
    ]:
        require("ConfirmDialog" in read(rel), f"{rel}: destructive action does not use the shared confirmation dialog")

    for rel in [
        "frontend/src/feature/contacts/components/SuppressionList.tsx",
        "frontend/src/routes/_protected/organization/account-settings/activity.tsx",
        "frontend/src/routes/_protected/admin/index.tsx",
    ]:
        require("PaginationControls" in read(rel), f"{rel}: high-volume list does not use shared pagination")

    platform_api = read("frontend/src/feature/platform/api/platformApi.ts")
    require("getSuppressions = async (search?: string, limit = 10, offset = 0)" in platform_api, "suppression API is not paginated by the frontend")
    require("getAuditLogs = async (search?: string, limit = 10, offset = 0)" in platform_api, "audit-log API is not paginated by the frontend")
    require("getAdminOrganizations = async (limit = 10, offset = 0)" in platform_api, "admin organizations API is not paginated by the frontend")
    require("getAdminUsers = async (search?: string, limit = 10, offset = 0)" in platform_api, "admin users API is not paginated by the frontend")

    register = read("frontend/src/feature/login/components/Register.tsx")
    invite = read("frontend/src/routes/invite/index.tsx")
    smtp = read("frontend/src/feature/email-accounts/components/SMTPFormModal.tsx")
    integrations = read("frontend/src/routes/_protected/organization/account-settings/api-integrations.tsx")
    require('maxLength={50}' in register, "registration full name lacks a 50-character frontend guard")
    require('maxLength={50}' in invite, "invitation full name lacks a 50-character frontend guard")
    require('maxLength={50}' in smtp, "sender display name lacks a 50-character frontend guard")
    require(integrations.count('maxLength={50}') >= 2, "integration key/webhook names lack 50-character frontend guards")

    email_account_schema = read("backend/src/modules/email_account/presentation/schemas/email_account_schemas.py")
    require("NameString" in email_account_schema and "sender_name: NameString" in email_account_schema, "sender_name backend limit is not aligned to 50 characters")

    overview = read("frontend/src/feature/organization/components/overview/OrganizationOverview.tsx")
    require('org?.created_at' in overview, "organization overview still hides the real creation date")
    require('label: "Created", value: "—"' not in overview, "organization creation date remains hard-coded")

def main() -> None:
    check_upload_limits()
    check_shared_ui()
    check_no_native_dialogs_or_selects()
    check_team_pagination()
    check_shared_pagination_component()
    check_member_api_does_not_leak_filters_to_invitations()
    check_onboarding_transition()
    check_csv_and_limits()
    check_save_draft_routing()
    check_dark_mode_scrollbars()
    check_remaining_project_wide_patterns()
    print("ALL QA BUGS 1-10 REGRESSION CHECKS PASSED")


if __name__ == "__main__":
    main()
