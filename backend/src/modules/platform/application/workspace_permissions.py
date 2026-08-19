"""Workspace permission defaults and safe per-member overrides.

Roles remain the compatibility baseline.  A member's ``permissions`` JSON only
contains explicit overrides so existing organizations keep their current
behaviour after the migration.
"""

from collections.abc import Mapping
import json
from typing import Any

WORKSPACE_PERMISSION_KEYS = (
    "manage_organization",
    "manage_members",
    "manage_member_permissions",
    "manage_campaigns",
    "manage_contacts",
    "delete_contacts",
    "manage_templates",
    "manage_integrations",
    "view_reports",
    "export_data",
)

ROLE_PERMISSION_DEFAULTS: dict[str, dict[str, bool]] = {
    "owner": {key: True for key in WORKSPACE_PERMISSION_KEYS},
    "admin": {
        "manage_organization": True,
        "manage_members": True,
        "manage_member_permissions": False,
        "manage_campaigns": True,
        "manage_contacts": True,
        "delete_contacts": True,
        "manage_templates": True,
        "manage_integrations": True,
        "view_reports": True,
        "export_data": True,
    },
    "member": {
        "manage_organization": False,
        "manage_members": False,
        "manage_member_permissions": False,
        "manage_campaigns": True,
        "manage_contacts": True,
        "delete_contacts": False,
        "manage_templates": True,
        "manage_integrations": False,
        "view_reports": True,
        "export_data": False,
    },
}


def effective_workspace_permissions(member: Any) -> dict[str, bool]:
    role_code = str(getattr(member, "role_code", "member") or "member")
    effective = dict(ROLE_PERMISSION_DEFAULTS.get(role_code, ROLE_PERMISSION_DEFAULTS["member"]))
    if role_code == "owner":
        return effective

    overrides = getattr(member, "permissions", None)
    # Some repository paths use textual SQL. PostgreSQL JSON values can then
    # arrive as strings instead of already-decoded dictionaries. Normalize both
    # forms so permission overrides are enforced consistently.
    if isinstance(overrides, str):
        try:
            decoded = json.loads(overrides)
            overrides = decoded if isinstance(decoded, Mapping) else {}
        except (TypeError, ValueError, json.JSONDecodeError):
            overrides = {}
    if isinstance(overrides, Mapping):
        for key in WORKSPACE_PERMISSION_KEYS:
            if key in overrides and isinstance(overrides[key], bool):
                effective[key] = overrides[key]

    # Delegation authority is never meaningful for an ordinary member.
    if role_code == "member":
        effective["manage_member_permissions"] = False
    return effective


def member_has_permission(member: Any, permission: str) -> bool:
    return bool(effective_workspace_permissions(member).get(permission, False))
