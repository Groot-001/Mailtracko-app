"""Regression checks for the user-reported MailTracko bugs collected on 2026-08-18.

These are intentionally lightweight source-contract checks so they can run in CI even
when the browser stack is unavailable. Runtime/API suites provide the complementary
behavioral coverage.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    contacts = read("frontend/src/feature/contacts/components/ContactsDashboard.tsx")
    login = read("frontend/src/feature/login/components/LoginForm.tsx")
    login_schema = read("frontend/src/feature/login/schema/LoginSchema.ts")
    index_css = read("frontend/src/index.css")
    main_tsx = read("frontend/src/main.tsx")
    input_policy = read("frontend/src/shared/utils/inputPolicy.ts")
    api_error = read("frontend/src/shared/utils/apiError.ts")

    # Bugs 1 / 8 / 16: whole compound-field focus + limits + login validation.
    require("focus-within" in login, "Login inputs must style the whole compound field on focus")
    require("maxLength={254}" in login and "maxLength={128}" in login, "Login limits must be explicit")
    require("Email is required" in login_schema and "Password is required" in login_schema, "Login schema must have field-specific messages")
    require("installGlobalInputPolicy" in main_tsx, "Global input policy must be installed")
    require("MutationObserver" in input_policy and "maxLength" in input_policy, "Dynamic text fields must receive safe limits")
    require(":has(> input:focus" in index_css, "Compound input wrapper focus styling must be global")

    # Bugs 2 / 3 / 5 / 7 / 11 / 12 / 13.
    require("mt-csv-preview" in contacts, "CSV preview must use explicit themed styles")
    require("importMenuRef" in contacts and "event.key === 'Escape'" in contacts, "Import menu must close on outside/Escape")
    require(">Add selected<" not in contacts and ">Add selected\n" not in contacts, "Redundant Add selected button must be removed")
    require("handleAddSelectedToCollection(value)" in contacts, "Collection selection must perform the add action directly")
    require("min-h-[680px]" in contacts and "h-[88px]" in contacts, "Paginated contact layout must stay dimensionally stable")
    require("createPortal" in contacts and "collectionMenuPosition" in contacts, "Collection action menu must be portal-positioned")
    require("Create collection" in contacts and "showCreateListForm" in contacts, "Create Collection must use modal state")
    require(contacts.count("csvFileInputRef.current?.click()") >= 1 and "csvFileInputRef" in contacts, "CSV entry points must share the same file input")

    # Bugs 4 / 6: silent background synchronization with no blocking loading flash.
    require("silentRefresh" in contacts and "setInterval" in contacts, "Contacts must silently refresh in the background")
    silent_block = contacts[contacts.index("const silentRefresh"):contacts.index("const intervalId")]
    require("setContactsLoading(true)" not in silent_block and "setListsLoading(true)" not in silent_block, "Background sync must not flash blocking loaders")
    require("syncContactsWorkspace" in contacts and "refreshCollections" in contacts, "Contact mutations must synchronize lists and counts")

    # Bug 9: standardized protected-page shell width.
    protected_files = [
        "frontend/src/feature/contacts/components/ContactsDashboard.tsx",
        "frontend/src/feature/campaigns/components/CampaignDashboard.tsx",
        "frontend/src/feature/templates/components/TemplateDashboard.tsx",
        "frontend/src/feature/organization/components/overview/OrganizationOverview.tsx",
        "frontend/src/routes/_protected/support/index.tsx",
    ]
    for path in protected_files:
        require("max-w-[1480px]" in read(path), f"{path} must use the standard application page width")

    # Bug 10: real structured API errors, not generic Validation Error.
    require("validation error" in api_error, "Error helper should explicitly recognize the generic validation label")
    require("errors" in api_error and "detail" in api_error, "Error helper must inspect structured validation details")
    backend_errors = read("backend/src/shared/exceptions/exception_handler.py")
    require("RequestValidationError" in backend_errors and "first_message" in backend_errors, "Backend must expose the first specific validation message")

    # Bugs 14 / 15 / 17: normalized Sheet headers + persistent connection + signed OAuth state.
    csv_utils = read("backend/src/modules/contacts/application/usecases/core/csv_utils.py")
    sheet_import = read("backend/src/modules/contacts/application/usecases/core/import_sheet_usecase.py")
    sheet_tabs = read("backend/src/modules/contacts/application/usecases/core/list_sheet_tabs_usecase.py")
    oauth_state = read("backend/src/shared/security/oauth_state.py")
    sheet_callback = read("backend/src/modules/contacts/application/usecases/core/sheets_oauth_callback_usecase.py")
    require('"companyname": "company"' in csv_utils and '"emailaddress": "email"' in csv_utils, "Google/CSV headers must normalize common formats")
    require("normalize_import_header" in sheet_import, "Google Sheets import must normalize headers")
    require("get_by_context" in sheet_import and "get_by_context" in sheet_tabs, "Sheets connection must be loaded from persistent DB context")
    require("sheets_token_org" not in sheet_import + sheet_tabs + sheet_callback, "Sheets connection must not depend on ephemeral Redis mapping")
    require("URLSafeTimedSerializer" in oauth_state and "SignatureExpired" in oauth_state, "OAuth state must be signed and expiring")
    auth_oauth = read("backend/src/modules/auth/application/usecases/oauth/oauth_usecase.py")
    signed_login_state = (
        'create_oauth_state("auth-login"' in auth_oauth
        and 'parse_oauth_state(state, "auth-login")' in auth_oauth
    )
    redis_login_state = (
        'secrets.token_urlsafe(32)' in auth_oauth
        and 'setex(f"oauth_state:{state}", 300' in auth_oauth
        and 'delete(f"oauth_state:{state}")' in auth_oauth
    )
    require(signed_login_state or redis_login_state, "Login OAuth must use expiring, CSRF-safe one-time state")

    # Bugs 18 / 19: only Light/Dark and professional step/backend schemas.
    onboarding_schema = read("frontend/src/feature/onboarding/schema/onboardingSchema.ts")
    onboarding_types = read("frontend/src/feature/onboarding/types/onboarding.types.ts")
    onboarding_layout = read("frontend/src/feature/onboarding/components/OnboardingLayout.tsx")
    org_schema = read("backend/src/modules/organization/presentation/schemas/organization_schemas.py")
    org_enum = read("backend/src/modules/organization/domain/enums/organization_enums.py")
    onboarding_tree = "\n".join(
        p.read_text(encoding="utf-8")
        for p in (ROOT / "frontend/src/feature/onboarding").rglob("*.ts*")
    )
    require('z.enum(["light", "dark"]' in onboarding_schema, "Onboarding theme schema must only allow Light/Dark")
    require('ThemeOption = "light" | "dark"' in onboarding_types, "Onboarding theme type must only allow Light/Dark")
    require("compactDensity" not in onboarding_tree and "reduceMotion" not in onboarding_tree and "showSidebarIcons" not in onboarding_tree, "Nonfunctional display preferences must be removed")
    require("safeParse" in onboarding_layout and "validationSteps.find" in onboarding_layout, "Final onboarding launch must revalidate all steps")
    require("OrganizationThemeEnum" in org_schema and "Literal" in org_schema, "Backend onboarding must validate enums/ranges server-side")
    require("onboarding_skipped" in org_schema and "validate_required_onboarding_steps" in org_schema, "Backend must reject incomplete non-skipped onboarding payloads")
    require("DARK = \"dark\"" in org_enum and "LIGHT = \"light\"" in org_enum, "Backend theme enum must be Dark/Light")
    require("MIDNIGHT" not in org_enum and "EXECUTIVE" not in org_enum, "Legacy four-theme values must not remain in backend enum")

    # Migration required for persistent Sheets ownership + theme normalization.
    migration = read("backend/migrations/versions/d2e3f4a5b6c7_oauth_theme_hardening.py")
    require("organization_id" in migration and "purpose" in migration, "Migration must persist Sheets OAuth ownership")
    require("midnight-focus" in migration and "dark" in migration, "Migration must normalize legacy theme values")

    print("PASS: 2026-08-18 user-reported bug regression checks")


if __name__ == "__main__":
    main()
