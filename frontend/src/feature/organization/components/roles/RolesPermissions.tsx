import { useMembers } from "../../hooks/useMembers";
import { useOrganizationStore } from "../../store/organizationStore";
import { RoleCard, ROLE_DEFINITIONS } from "./RoleCard";
import { PermissionsMatrix } from "./PermissionsMatrix";
import { RoleDetails } from "./RoleDetails";
import type { RoleCode } from "../../types/organization.types";
import { TeamTabs } from "../team/TeamTabs";

export const RolesPermissions = () => {
  const { selectedRole, setSelectedRole } = useOrganizationStore();
  const { data: membersData } = useMembers({ limit: 200 });

  const allMembers = membersData?.items ?? [];

  const getMemberCount = (role: RoleCode): number =>
    allMembers.filter((m) => m.role_code === role).length;

  const selectedRoleDef =
    ROLE_DEFINITIONS.find((r) => r.code === selectedRole) ??
    ROLE_DEFINITIONS[0];

  return (
    <div className="mx-auto max-w-[1480px] space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold text-[#1A1C1C] tracking-tight">
          Roles & Permissions
        </h1>
        <p className="text-sm text-[#4C4736] mt-1">
          Manage roles and control what team members can see and do.
        </p>
      </div>

      <TeamTabs />

      {/* Role cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {ROLE_DEFINITIONS.map((role) => (
          <RoleCard
            key={role.code}
            role={role}
            memberCount={getMemberCount(role.code)}
            isSelected={selectedRole === role.code}
            onClick={() => setSelectedRole(role.code)}
          />
        ))}
      </div>

      {/* Matrix + Details */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
        <PermissionsMatrix selectedRole={selectedRole} />
        <RoleDetails role={selectedRoleDef} />
      </div>
    </div>
  );
};
