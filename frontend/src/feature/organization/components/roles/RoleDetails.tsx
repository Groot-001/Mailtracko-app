import { Crown, ShieldCheck, User, CheckCircle2, UserCog } from "lucide-react";
import { Link } from "@tanstack/react-router";
import type { RoleCode, RoleDefinition } from "../../types/organization.types";
import { DefaultBadge } from "../shared/StatusBadge";

// ─── Icon map ─────────────────────────────────────────────────────────────────

const roleIcons: Record<RoleCode, React.ElementType> = {
  owner: Crown,
  admin: ShieldCheck,
  member: User,
};

// ─── Component ────────────────────────────────────────────────────────────────

interface RoleDetailsProps {
  role: RoleDefinition;
}

export const RoleDetails = ({ role }: RoleDetailsProps) => {
  const Icon = roleIcons[role.code];

  return (
    <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 space-y-5">
      <h2 className="text-base font-semibold text-[#1A1C1C]">Role details</h2>

      {/* Role header */}
      <div className="flex items-start gap-3">
        <div className="w-12 h-12 rounded-xl bg-[#F1D442]/30 flex items-center justify-center flex-shrink-0">
          <Icon className="w-6 h-6 text-[#8F740D]" />
        </div>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg font-bold text-[#1A1C1C]">{role.label}</span>
            {role.isDefault && <DefaultBadge />}
          </div>
          <p className="text-xs text-[#4C4736] leading-relaxed">{role.description}</p>
        </div>
      </div>

      {/* Key permissions */}
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-[#1A1C1C]">Key permissions</h3>
        <ul className="space-y-2">
          {role.permissions.map((perm) => (
            <li key={perm} className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
              <span className="text-sm text-[#4C4736]">{perm}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Built-in permission definitions are fixed; member role assignments are editable. */}
      <Link
        id="manage-member-roles-btn"
        to="/organization/team"
        className="w-full flex items-center justify-center gap-2 py-2.5 bg-[#8F740D] hover:bg-[#6A5B00] text-white text-sm font-semibold rounded-xl transition-colors"
      >
        <UserCog className="w-4 h-4" />
        Manage member roles
      </Link>
      <p className="text-xs text-[#4C4736] text-center leading-relaxed">
        Change an individual member between Admin and Member from Team Management.
      </p>

      {/* Owner note */}
      {role.code === "owner" && (
        <p className="text-xs text-[#4C4736] text-center leading-relaxed">
          Owners can't be deleted. Transfer ownership to another member before leaving.
        </p>
      )}
    </div>
  );
};
