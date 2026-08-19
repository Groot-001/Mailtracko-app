"""Regression checks for the remaining low-risk QA fixes.

Run from repository root:
    python scripts/qa_remaining_simple_bugs.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def check_password_visibility_icons() -> None:
    files = [
        "frontend/src/feature/login/components/LoginForm.tsx",
        "frontend/src/feature/login/components/Register.tsx",
        "frontend/src/routes/ForgotPassword/verify.tsx",
        "frontend/src/routes/invite/index.tsx",
        "frontend/src/feature/organization/components/account-settings/SecuritySettings.tsx",
    ]
    for rel in files:
        text = compact(read(rel))
        # QA convention: the icon reflects the CURRENT state: Eye while visible,
        # EyeOff while masked. aria-label still describes the button action.
        inverted = re.findall(
            r"show(?:Current|New|Confirm)?Password\s*\?\s*<EyeOff\b[^>]*>.*?</EyeOff>|"
            r"show(?:Current|New|Confirm)?Password\s*\?\s*<EyeOff\b[^>]*/>",
            text,
        )
        require(not inverted, f"{rel}: visible password still renders EyeOff")

    print("PASS: password visibility icons reflect current visibility state")


def check_organization_dark_surface() -> None:
    css = read("frontend/src/index.css")
    require(
        '[class~="bg-[#FAFAF8]"]' in css,
        "dark theme does not override OrganizationLayout bg-[#FAFAF8]",
    )
    print("PASS: organization main surface is covered by dark theme")


def check_template_category_dropdowns() -> None:
    dashboard = read("frontend/src/feature/templates/components/TemplateDashboard.tsx")
    gallery = read("frontend/src/feature/templates/components/TemplateGalleryStep.tsx")
    for rel, text in [
        ("TemplateDashboard.tsx", dashboard),
        ("TemplateGalleryStep.tsx", gallery),
    ]:
        require("AppSelect" in text, f"{rel}: category filter does not use the shared AppSelect")
        require('ariaLabel="Filter templates by category"' in text, f"{rel}: category filter lacks an accessible label")
        require("<select" not in text, f"{rel}: raw browser select remains")
    print("PASS: template category dropdowns use the shared professional select control")


def check_contact_server_search_sync() -> None:
    text = compact(read("frontend/src/feature/contacts/components/ContactsDashboard.tsx"))
    require("const [contactsLimit, setContactsLimit] = useState(10)" in text, "contacts dashboard must default to 10 rows per page")
    require("limit: contactsLimit" in text, "contacts dashboard does not send the selected page size to the backend")
    require("offset: (contactsPage - 1) * contactsLimit" in text, "contacts dashboard does not send the current page offset")
    require("search: search.trim() || undefined" in text, "contact search is not sent to the backend")
    require(
        "status: statusFilter === 'all' ? undefined : statusFilter" in text,
        "contact status filter is not sent to the backend",
    )
    require(
        "verification_status: verificationFilter === 'all' ? undefined : verificationFilter" in text,
        "contact verification filter is not sent to the backend",
    )
    dependency_prefix = "[activeListUuid, contactsLimit, contactsPage, search, statusFilter, verificationFilter"
    require(
        dependency_prefix in text,
        "contacts are not refreshed when pagination/search/filter values change",
    )
    require(
        "silentRefresh" in text and "setInterval" in text and "setContactsLoading" not in text.split("const silentRefresh", 1)[1].split("const openCsvFilePicker", 1)[0],
        "contacts dashboard does not silently refresh background list data without flashing",
    )
    require("PaginationControls" in text, "contacts dashboard does not use the shared pagination control")
    pagination = read("frontend/src/shared/components/PaginationControls.tsx")
    require("[10, 25, 50, 100]" in pagination, "shared rows-per-page options are incomplete")
    print("PASS: contact search/filter/pagination uses backend data")


def main() -> None:
    check_password_visibility_icons()
    check_organization_dark_surface()
    check_template_category_dropdowns()
    check_contact_server_search_sync()
    print("ALL REMAINING SIMPLE QA REGRESSION CHECKS PASSED")


if __name__ == "__main__":
    main()
