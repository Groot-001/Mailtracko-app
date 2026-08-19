import { Crown, ShieldCheck, User } from "lucide-react";
import type { RoleCode, RoleDefinition } from "../../types/organization.types";
import { DefaultBadge } from "../shared/StatusBadge";

// ─── Role Definitions ─────────────────────────────────────────────────────────

export const ROLE_DEFINITIONS: RoleDefinition[] = [
  {
    code: "owner",
    label: "Owner",
    description: "Full access to all organization settings, billing, and team management.",
    isDefault: true,
    permissions: [
      "Manage organization settings",
      "Manage billing",
      "Invite / remove members",
      "Create campaigns",
      "View reports",
      "Manage integrations",
      "Export data",
    ],
  },
  {
    code: "admin",
    label: "Admin",
    description: "Manage teams, campaigns, and settings. No access to billing or ownership transfer.",
    permissions: [
      "Manage organization settings",
      "Invite / remove members",
      "Create campaigns",
      "View reports",
      "Manage integrations",
      "Export data",
    ],
  },
  {
    code: "member",
    label: "Member",
    description: "Access assigned features to collaborate and contribute to campaigns.",
    permissions: [
      "Create campaigns",
      "View reports",
    ],
  },
];

// ─── Icon map ─────────────────────────────────────────────────────────────────

const roleIcons: Record<RoleCode, React.ElementType> = {
  owner: Crown,
  admin: ShieldCheck,
  member: User,
};

// ─── Component ────────────────────────────────────────────────────────────────

interface RoleCardProps {
  role: RoleDefinition;
  memberCount: number;
  isSelected: boolean;
  onClick: () => void;
}

export const RoleCard = ({ role, memberCount, isSelected, onClick }: RoleCardProps) => {
  const Icon = roleIcons[role.code];

  return (
    <button
      id={`role-card-${role.code}`}
      onClick={onClick}
      className={`w-full text-left bg-white border rounded-2xl p-5 transition-all duration-200 hover:shadow-md group ${
        isSelected
          ? "border-[#8F740D] ring-2 ring-[#F1D442]/40 shadow-md"
          : "border-[#CEC6B0]/40 hover:border-[#CEC6B0]"
      }`}
    >
      <div className="flex items-start gap-3">
        <div
          className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-colors ${
            isSelected ? "bg-[#F1D442]/30" : "bg-[#F4F3F3] group-hover:bg-[#F1D442]/20"
          }`}
        >
          <Icon className="w-5 h-5 text-[#8F740D]" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-bold text-[#1A1C1C]">{role.label}</span>
            {role.isDefault && <DefaultBadge />}
          </div>
          <p className="text-xs text-[#4C4736] leading-relaxed line-clamp-2">
            {role.description}
          </p>
        </div>
      </div>
      <p className="text-xs font-semibold text-[#8F740D] mt-3">
        {memberCount} member{memberCount !== 1 ? "s" : ""}
      </p>
    </button>
  );
};
