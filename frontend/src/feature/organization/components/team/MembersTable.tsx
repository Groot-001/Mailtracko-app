import { useState } from "react";
import { MoreHorizontal, ShieldCheck, Trash2, UserCog } from "lucide-react";
import type { OrganizationMember } from "../../types/organization.types";
import { AvatarInitials } from "../shared/AvatarInitials";
import { RoleBadge, MemberStatusBadge } from "../shared/StatusBadge";
import { EmptyState } from "../shared/EmptyState";
import { useRemoveMember, useUpdateMemberPermissions, useUpdateMemberRole } from "../../hooks/useMembers";
import { useToast } from "../../../../shared/hooks/useToast";
import { getApiErrorMessage } from "../../../../shared/utils/apiError";
import { ConfirmDialog } from "../../../../shared/components/ConfirmDialog";
import { PaginationControls } from "../../../../shared/components/PaginationControls";
import { Modal } from "../../../../shared/components/Modal";
import { useQuery } from "@tanstack/react-query";
import { getPlatformAccess } from "../../../platform/api/platformApi";

const formatLastActive = (lastActiveAt: string | null): string => {
  if (!lastActiveAt) return "Never";
  const diff = Date.now() - new Date(lastActiveAt).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
};

const PERMISSION_OPTIONS = [
  ["manage_organization", "Manage organization settings"],
  ["manage_members", "Invite and remove members"],
  ["manage_member_permissions", "Manage member permissions"],
  ["manage_campaigns", "Manage campaigns"],
  ["manage_contacts", "Create and update contacts"],
  ["delete_contacts", "Delete contacts and collections"],
  ["manage_templates", "Manage templates"],
  ["manage_integrations", "Manage integrations"],
  ["view_reports", "View reports"],
  ["export_data", "Export data"],
] as const;

const ROLE_PERMISSION_DEFAULTS: Record<"admin" | "member", Record<string, boolean>> = {
  admin: {
    manage_organization: true, manage_members: true, manage_member_permissions: false,
    manage_campaigns: true, manage_contacts: true, delete_contacts: true, manage_templates: true,
    manage_integrations: true, view_reports: true, export_data: true,
  },
  member: {
    manage_organization: false, manage_members: false, manage_member_permissions: false,
    manage_campaigns: true, manage_contacts: true, delete_contacts: false, manage_templates: true,
    manage_integrations: false, view_reports: true, export_data: false,
  },
};

const effectiveMemberPermissions = (member: OrganizationMember) => {
  if (member.role_code === "owner") {
    return Object.fromEntries(PERMISSION_OPTIONS.map(([key]) => [key, true]));
  }
  return { ...ROLE_PERMISSION_DEFAULTS[member.role_code], ...(member.permissions ?? {}) };
};

interface ActionMenuProps {
  member: OrganizationMember;
  onRemove: () => void;
  onRoleChange: (role: "admin" | "member") => void;
  onPermissions: () => void;
  canManagePermissions: boolean;
}

const ActionMenu = ({ member, onRemove, onRoleChange, onPermissions, canManagePermissions }: ActionMenuProps) => {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button
        id={`member-actions-${member.uuid}`}
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="rounded-lg p-1.5 text-[#4C4736] transition-colors hover:bg-[#F4F3F3]"
        aria-label="Member actions"
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <MoreHorizontal className="h-4 w-4" />
      </button>
      {open ? (
        <>
          <button type="button" aria-label="Close member actions" className="fixed inset-0 z-10 cursor-default" onClick={() => setOpen(false)} />
          <div role="menu" className="absolute right-0 top-full z-20 mt-1 w-48 overflow-hidden rounded-xl border border-[#CEC6B0]/40 bg-white py-1 shadow-xl">
            <button
              type="button"
              role="menuitem"
              onClick={() => {
                onRoleChange(member.role_code === "admin" ? "member" : "admin");
                setOpen(false);
              }}
              className="flex w-full items-center gap-2 px-3 py-2 text-xs text-[#1A1C1C] transition-colors hover:bg-[#F4F3F3]"
            >
              <UserCog className="h-3.5 w-3.5 text-[#4C4736]" />
              Make {member.role_code === "admin" ? "member" : "admin"}
            </button>
            {canManagePermissions ? (
              <button
                type="button"
                role="menuitem"
                onClick={() => { onPermissions(); setOpen(false); }}
                className="flex w-full items-center gap-2 px-3 py-2 text-xs text-[#1A1C1C] transition-colors hover:bg-[#F4F3F3]"
              >
                <ShieldCheck className="h-3.5 w-3.5 text-[#4C4736]" />
                Manage permissions
              </button>
            ) : null}
            <hr className="my-1 border-[#EEEEEE]" />
            <button
              type="button"
              role="menuitem"
              onClick={() => {
                onRemove();
                setOpen(false);
              }}
              className="flex w-full items-center gap-2 px-3 py-2 text-xs text-red-600 transition-colors hover:bg-red-50"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Remove member
            </button>
          </div>
        </>
      ) : null}
    </div>
  );
};

interface MembersTableProps {
  members: OrganizationMember[];
  total: number;
  page: number;
  limit: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
}

export const MembersTable = ({ members, total, page, limit, onPageChange, onPageSizeChange }: MembersTableProps) => {
  const [pendingRemoveId, setPendingRemoveId] = useState<number | null>(null);
  const [permissionMember, setPermissionMember] = useState<OrganizationMember | null>(null);
  const [permissionDraft, setPermissionDraft] = useState<Record<string, boolean>>({});
  const removeMutation = useRemoveMember();
  const roleMutation = useUpdateMemberRole();
  const permissionsMutation = useUpdateMemberPermissions();
  const accessQuery = useQuery({ queryKey: ["platform", "access"], queryFn: getPlatformAccess, staleTime: 30_000 });
  const { showToast } = useToast();

  const pendingMember = members.find((member) => member.id === pendingRemoveId) ?? null;

  const handleConfirmRemove = async () => {
    if (!pendingRemoveId) return;
    try {
      await removeMutation.mutateAsync(pendingRemoveId);
      setPendingRemoveId(null);
      showToast("Member removed successfully.", "success");
    } catch (error) {
      showToast(getApiErrorMessage(error, "Failed to remove member."), "error");
    }
  };

  const handleRoleChange = async (memberUuid: string, roleCode: "admin" | "member") => {
    try {
      await roleMutation.mutateAsync({ memberUuid, roleCode });
      showToast(`Member role updated to ${roleCode}.`, "success");
    } catch (error) {
      showToast(getApiErrorMessage(error, "Failed to update member role."), "error");
    }
  };

  const openPermissions = (member: OrganizationMember) => {
    setPermissionMember(member);
    setPermissionDraft(effectiveMemberPermissions(member));
  };

  const savePermissions = async () => {
    if (!permissionMember) return;
    try {
      await permissionsMutation.mutateAsync({ memberUuid: permissionMember.uuid, permissions: permissionDraft });
      showToast("Member permissions updated successfully.", "success");
      setPermissionMember(null);
    } catch (error) {
      showToast(getApiErrorMessage(error, "Failed to update member permissions."), "error");
    }
  };

  const actorRole = accessQuery.data?.workspace_role;
  const actorCanDelegate = actorRole === "owner" || (actorRole === "admin" && Boolean(accessQuery.data?.workspace_permissions?.manage_member_permissions));
  const canManageTargetPermissions = (member: OrganizationMember) =>
    actorCanDelegate && member.role_code !== "owner" && (actorRole === "owner" || member.role_code === "member");

  if (members.length === 0) {
    return <EmptyState icon={UserCog} title="No members found" description="Try adjusting your search or filters." />;
  }

  return (
    <>
      
      <Modal
        open={Boolean(permissionMember)}
        onClose={() => setPermissionMember(null)}
        title="Member permissions"
        description={permissionMember ? `Choose what ${permissionMember.user?.full_name ?? permissionMember.user?.email ?? "this member"} can do in this organization.` : undefined}
      >
        <div className="space-y-3">
          {PERMISSION_OPTIONS.map(([key, label]) => {
            const memberRole = permissionMember?.role_code;
            const disabled = memberRole === "member" && key === "manage_member_permissions";
            const actorPermission = accessQuery.data?.workspace_permissions?.[key] ?? false;
            const adminCannotGrant = actorRole === "admin" && !actorPermission;
            return (
              <label key={key} className={`flex items-center justify-between gap-4 rounded-xl border border-[#EEE9DB] px-3 py-2.5 ${disabled || adminCannotGrant ? "opacity-55" : ""}`}>
                <span className="text-sm text-[#302C24]">{label}</span>
                <input
                  type="checkbox"
                  checked={Boolean(permissionDraft[key])}
                  disabled={disabled || adminCannotGrant}
                  onChange={(event) => setPermissionDraft((current) => ({ ...current, [key]: event.target.checked }))}
                  className="h-4 w-4 accent-[#8F740D]"
                />
              </label>
            );
          })}
          <p className="text-xs leading-5 text-[#756F60]">
            Owners always retain full access. Delegated admins can manage members only, and can never grant a permission they do not have themselves.
          </p>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => setPermissionMember(null)} className="rounded-xl border border-[#CEC6B0]/60 px-4 py-2 text-sm font-semibold">Cancel</button>
            <button type="button" disabled={permissionsMutation.isPending} onClick={() => void savePermissions()} className="rounded-xl bg-[#8F740D] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60">
              {permissionsMutation.isPending ? "Saving…" : "Save permissions"}
            </button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        open={Boolean(pendingMember)}
        onOpenChange={(open) => { if (!open) setPendingRemoveId(null); }}
        title="Remove member?"
        description={`${pendingMember?.user?.full_name ?? pendingMember?.user?.email ?? "This member"} will lose access to this organization immediately.`}
        confirmLabel="Remove member"
        isLoading={removeMutation.isPending}
        onConfirm={handleConfirmRemove}
      />

      <div className="max-w-full overflow-x-auto overscroll-x-contain lg:overflow-x-visible">
        <table className="w-full min-w-[720px] lg:min-w-0">
          <thead>
            <tr className="border-b border-[#EEEEEE]">
              {[
                "Member",
                "Email",
                "Role",
                "Status",
                "Last active",
                "Actions",
              ].map((column) => (
                <th key={column} className="pb-3 text-left text-xs font-semibold text-[#4C4736] first:pl-1">{column}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#F4F3F3]">
            {members.map((member) => (
              <tr key={member.uuid} className="group transition-colors hover:bg-[#F9F9F9]">
                <td className="py-3.5 pl-1">
                  <div className="flex items-center gap-2.5">
                    <AvatarInitials name={member.user?.full_name} email={member.user?.email} avatarUrl={member.user?.avatar} bgColor={member.user?.avatar_bg} size="md" />
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="max-w-[220px] truncate text-sm font-medium text-[#1A1C1C]" title={member.user?.full_name ?? undefined}>{member.user?.full_name ?? "—"}</span>
                        {member.role_code === "owner" ? <span className="rounded-full bg-[#F1D442]/20 px-1.5 py-0.5 text-[10px] font-semibold text-[#8F740D]">Owner</span> : null}
                      </div>
                      {member.user?.email ? <p className="mt-0.5 max-w-[240px] truncate text-xs text-[#4C4736]" title={member.user.email}>{member.user.email}</p> : null}
                    </div>
                  </div>
                </td>
                <td className="py-3.5"><span className="block max-w-[240px] truncate text-sm text-[#4C4736]" title={member.user?.email ?? undefined}>{member.user?.email ?? "—"}</span></td>
                <td className="py-3.5"><RoleBadge role={member.role_code} /></td>
                <td className="py-3.5">
                  <div className="space-y-1">
                    <MemberStatusBadge status={member.status} />
                    <span className={`inline-flex items-center gap-1 text-[11px] font-semibold ${member.presence === "online" ? "text-emerald-700" : "text-[#756F60]"}`}>
                      <span className={`h-1.5 w-1.5 rounded-full ${member.presence === "online" ? "bg-emerald-500" : "bg-[#B8B09D]"}`} />
                      {member.presence === "online" ? "Online" : "Offline"}
                    </span>
                  </div>
                </td>
                <td className="py-3.5"><span className="text-sm text-[#4C4736]">{member.presence === "online" ? "Active now" : formatLastActive(member.last_active_at)}</span></td>
                <td className="py-3.5">
                  {member.role_code !== "owner" ? (
                    <ActionMenu
                      member={member}
                      onRemove={() => setPendingRemoveId(member.id)}
                      onRoleChange={(roleCode) => void handleRoleChange(member.uuid, roleCode)}
                      onPermissions={() => openPermissions(member)}
                      canManagePermissions={canManageTargetPermissions(member)}
                    />
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <PaginationControls
        page={page}
        pageSize={limit}
        total={total}
        itemLabel="members"
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
        isLoading={removeMutation.isPending || roleMutation.isPending}
        className="mt-4 border-t border-[#EEEEEE] pt-5"
      />
    </>
  );
};
