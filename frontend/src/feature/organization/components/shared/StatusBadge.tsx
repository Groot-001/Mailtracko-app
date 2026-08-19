import type { RoleCode, MemberStatus, InvitationStatus } from "../../types/organization.types";

// ─── Role Badge ───────────────────────────────────────────────────────────────

interface RoleBadgeProps {
  role: RoleCode;
}

const roleStyles: Record<RoleCode, string> = {
  owner: "bg-[#F1D442]/30 text-[#6A5B00] border border-[#F1D442]/60",
  admin: "bg-purple-50 text-purple-700 border border-purple-200",
  member: "bg-blue-50 text-blue-700 border border-blue-200",
};

const roleLabels: Record<RoleCode, string> = {
  owner: "Owner",
  admin: "Admin",
  member: "Member",
};

export const RoleBadge = ({ role }: RoleBadgeProps) => (
  <span
    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${roleStyles[role]}`}
  >
    {roleLabels[role]}
  </span>
);

// ─── Member Status Badge ──────────────────────────────────────────────────────

interface MemberStatusBadgeProps {
  status: MemberStatus | "invited";
}

const memberStatusStyles: Record<string, string> = {
  active: "text-emerald-700",
  inactive: "text-[#4C4736]",
  removed: "text-red-600",
  invited: "text-amber-600",
};

const memberStatusDotStyles: Record<string, string> = {
  active: "bg-emerald-500",
  inactive: "bg-[#4C4736]/40",
  removed: "bg-red-500",
  invited: "bg-amber-400",
};

const memberStatusLabels: Record<string, string> = {
  active: "Active",
  inactive: "Inactive",
  removed: "Removed",
  invited: "Invited",
};

export const MemberStatusBadge = ({ status }: MemberStatusBadgeProps) => (
  <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${memberStatusStyles[status] ?? "text-gray-600"}`}>
    <span className={`w-2 h-2 rounded-full ${memberStatusDotStyles[status] ?? "bg-gray-400"}`} />
    {memberStatusLabels[status] ?? status}
  </span>
);

// ─── Invitation Status Badge ──────────────────────────────────────────────────

interface InvitationStatusBadgeProps {
  status: InvitationStatus;
}

const invitationStatusStyles: Record<InvitationStatus, string> = {
  pending: "bg-amber-50 text-amber-700 border border-amber-200",
  accepted: "bg-emerald-50 text-emerald-700 border border-emerald-200",
  declined: "bg-red-50 text-red-700 border border-red-200",
  revoked: "bg-gray-100 text-gray-600 border border-gray-200",
  expired: "bg-gray-100 text-gray-500 border border-gray-200",
};

const invitationStatusLabels: Record<InvitationStatus, string> = {
  pending: "Pending",
  accepted: "Accepted",
  declined: "Declined",
  revoked: "Revoked",
  expired: "Expired",
};

export const InvitationStatusBadge = ({ status }: InvitationStatusBadgeProps) => (
  <span
    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${invitationStatusStyles[status]}`}
  >
    {invitationStatusLabels[status]}
  </span>
);

// ─── Default Badge ─────────────────────────────────────────────────────────────

interface DefaultBadgeProps {
  label?: string;
}

export const DefaultBadge = ({ label = "Default" }: DefaultBadgeProps) => (
  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-[#F1D442]/30 text-[#6A5B00] border border-[#F1D442]/60">
    {label}
  </span>
);
