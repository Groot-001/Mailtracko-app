import {
  Settings,
  CreditCard,
  UserPlus,
  Megaphone,
  BarChart2,
  Plug,
  Download,
  CheckCircle2,
  Ban,
} from "lucide-react";
import type { RoleCode } from "../../types/organization.types";

// ─── Permission rows data ─────────────────────────────────────────────────────

interface PermissionDef {
  label: string;
  icon: React.ElementType;
  owner: boolean;
  admin: boolean;
  member: boolean;
}

const PERMISSIONS: PermissionDef[] = [
  { label: "Manage organization settings", icon: Settings, owner: true, admin: true, member: false },
  { label: "Manage billing", icon: CreditCard, owner: true, admin: false, member: false },
  { label: "Invite / remove members", icon: UserPlus, owner: true, admin: true, member: false },
  { label: "Create campaigns", icon: Megaphone, owner: true, admin: true, member: true },
  { label: "View reports", icon: BarChart2, owner: true, admin: true, member: true },
  { label: "Manage integrations", icon: Plug, owner: true, admin: true, member: false },
  { label: "Export data", icon: Download, owner: true, admin: true, member: false },
];

// ─── Component ────────────────────────────────────────────────────────────────

interface PermissionsMatrixProps {
  selectedRole: RoleCode;
}

export const PermissionsMatrix = ({ selectedRole }: PermissionsMatrixProps) => {
  const roles: { code: RoleCode; label: string; icon: React.ElementType }[] = [
    { code: "owner", label: "Owner", icon: Settings },
    { code: "admin", label: "Admin", icon: Settings },
    { code: "member", label: "Member", icon: Settings },
  ];

  return (
    <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 space-y-5">
      <div>
        <h2 className="text-base font-semibold text-[#1A1C1C]">Permissions matrix</h2>
        <p className="text-xs text-[#4C4736] mt-0.5">Compare permissions across roles.</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[500px]">
          <thead>
            <tr className="border-b border-[#EEEEEE]">
              <th className="pb-3 text-left text-xs font-semibold text-[#4C4736] w-[45%]">
                Permission
              </th>
              {roles.map((r) => (
                <th
                  key={r.code}
                  className={`pb-3 text-center text-xs font-semibold w-[18%] ${
                    r.code === selectedRole ? "text-[#8F740D]" : "text-[#4C4736]"
                  }`}
                >
                  <div className="flex items-center justify-center gap-1">
                    {r.code === "owner" && <span className="text-[#8F740D]">👑</span>}
                    {r.label}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#F4F3F3]">
            {PERMISSIONS.map((perm) => (
              <tr key={perm.label} className="group hover:bg-[#F9F9F9] transition-colors">
                <td className="py-3.5">
                  <div className="flex items-center gap-2.5">
                    <perm.icon className="w-4 h-4 text-[#CEC6B0] flex-shrink-0" />
                    <span className="text-sm text-[#1A1C1C]">{perm.label}</span>
                  </div>
                </td>
                {(["owner", "admin", "member"] as const).map((role) => {
                  const allowed = perm[role];
                  return (
                    <td key={role} className="py-3.5 text-center">
                      {allowed ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-500 mx-auto" />
                      ) : (
                        <Ban className="w-5 h-5 text-[#CEC6B0] mx-auto" />
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 text-xs text-[#4C4736] pt-2 border-t border-[#EEEEEE]">
        <span className="flex items-center gap-1.5">
          <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Allowed
        </span>
        <span className="flex items-center gap-1.5">
          <Ban className="w-4 h-4 text-[#CEC6B0]" /> Restricted
        </span>
      </div>
    </div>
  );
};
