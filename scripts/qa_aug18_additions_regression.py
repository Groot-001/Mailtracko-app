"""Regression checks for the two 2026-08-18 additions fixed after the v2 package.

Bug #1: Create Collection typing must not be disrupted by Modal autofocus lifecycle.
Bug #2: Organization updates must synchronize through the shared query cache and
         the Save Changes button must remain dimensionally stable while pending.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    modal = read("frontend/src/shared/components/Modal.tsx")
    contacts = read("frontend/src/feature/contacts/components/ContactsDashboard.tsx")
    org_hook = read("frontend/src/feature/organization/hooks/useOrganization.ts")
    org_settings = read("frontend/src/feature/organization/components/settings/OrganizationSettings.tsx")
    org_api = read("frontend/src/feature/organization/api/organizationApi.ts")
    org_router = read("backend/src/modules/organization/presentation/routers/organization_routers.py")

    # Bug #1: inline onClose callbacks from parent renders must not restart the
    # modal lifecycle/autofocus effect on every controlled-input keystroke.
    require("const onCloseRef = useRef(onClose)" in modal, "Modal must keep a stable onClose ref")
    require("onCloseRef.current = onClose" in modal, "Modal must keep the close callback fresh")
    require("}, [open]);" in modal, "Modal lifecycle/autofocus effect must depend only on open")
    require("[onClose, open]" not in modal, "Modal must not refocus on every inline onClose identity change")
    require('data-autofocus="true"' in contacts, "Create Collection name remains the intended initial focus")
    require("value={newListName}" in contacts and "setNewListName(event.target.value)" in contacts,
            "Create Collection name must stay a normal controlled input")

    # Bug #2: PATCH response is authoritative and must be pushed into the shared
    # organization cache used by both Settings and Organization Overview.
    require("queryClient.setQueryData(ORGANIZATION_QUERY_KEY, updatedOrganization)" in org_hook,
            "Saved organization must update the shared organization cache immediately")
    edit_block = org_hook[org_hook.index("export const useEditOrganization"):org_hook.index("export const useRequestOrganizationDeletion")]
    require("invalidateQueries({ queryKey: ORGANIZATION_QUERY_KEY" not in edit_block,
            "Edit success must not race the canonical PATCH response with an immediate current-org refetch")
    require('["organization", "activities"]' in edit_block,
            "Organization update activity should refresh independently")
    require("reset(defaultsFromOrganization(updated))" in org_settings,
            "Settings form must reset to the canonical saved server response")
    require('aria-busy={editMutation.isPending}' in org_settings and 'min-w-[152px]' in org_settings,
            "Save Changes button must expose pending state without resizing/flickering")
    require("current_organization" in org_api and "current_organization" in org_router,
            "Frontend/backend must agree on the updated organization response contract")

    print("PASS: Aug 18 additions regression checks (collection typing + organization sync/save UX)")


if __name__ == "__main__":
    main()
