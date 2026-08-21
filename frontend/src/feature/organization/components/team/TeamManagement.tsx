import { useEffect, useMemo, useState } from "react";
import { Search, UserPlus } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { useMembers } from "../../hooks/useMembers";
import { usePendingInvitations } from "../../hooks/useInvitations";
import { useOrganizationStore } from "../../store/organizationStore";
import { MembersTable } from "./MembersTable";
import { InvitePanel } from "./InvitePanel";
import { PendingInvites } from "./PendingInvites";
import type { RoleCode } from "../../types/organization.types";
import { TeamTabs } from "./TeamTabs";
import { AppSelect } from "../../../../shared/components/AppSelect";
import { PageContainer } from "../../../../shared/components/layout";

export const TeamManagement = () => {
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const store = useOrganizationStore();

  const memberParams = useMemo(
    () => ({
      limit,
      offset: (page - 1) * limit,
      search: store.memberSearchQuery.trim() || undefined,
      role: store.memberRoleFilter === "all" ? undefined : store.memberRoleFilter,
      status: store.memberStatusFilter === "all" ? undefined : store.memberStatusFilter,
    }),
    [limit, page, store.memberRoleFilter, store.memberSearchQuery, store.memberStatusFilter],
  );

  const { data: membersData, isLoading, isFetching } = useMembers(memberParams);
  const { data: invitationsData } = usePendingInvitations();
  const members = membersData?.items ?? [];
  const total = membersData?.total ?? 0;
  const invitations = invitationsData?.items ?? [];
  const totalPages = Math.max(1, Math.ceil(total / limit));

  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  const resetToFirstPage = () => setPage(1);

  return (
    <PageContainer nested>
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#1A1C1C]">Team Management</h1>
          <p className="mt-1 text-sm text-[#4C4736]">Manage your team members, roles, and access permissions.</p>
        </div>
        <Link
          to="/organization/team/invite"
          className="flex cursor-pointer items-center gap-1.5 rounded-xl bg-[#8F740D] px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[#6A5B00]"
        >
          <UserPlus className="h-4 w-4" />
          Invite members
        </Link>
      </div>

      <TeamTabs />

      <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
        <div className="relative w-full flex-1 xl:max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#CEC6B0]" />
          <input
            id="member-search"
            type="search"
            placeholder="Search members by name or email..."
            value={store.memberSearchQuery}
            onChange={(event) => {
              store.setMemberSearchQuery(event.target.value);
              resetToFirstPage();
            }}
            className="w-full rounded-xl border border-[#CEC6B0]/60 bg-white py-2.5 pl-9 pr-3 text-sm text-[#1A1C1C] placeholder:text-[#CEC6B0] focus:border-[#8F740D] focus:outline-none focus:ring-2 focus:ring-[#F1D442]/50"
          />
        </div>

        <div className="grid w-full grid-cols-1 gap-2 sm:grid-cols-2 xl:w-auto">
          <AppSelect
            value={store.memberRoleFilter}
            onValueChange={(value) => {
              store.setMemberRoleFilter(value as RoleCode | "all");
              resetToFirstPage();
            }}
            ariaLabel="Filter members by role"
            options={[
              { value: "all", label: "All roles" },
              { value: "owner", label: "Owner" },
              { value: "admin", label: "Admin" },
              { value: "member", label: "Member" },
            ]}
            className="min-w-[150px]"
          />
          <AppSelect
            value={store.memberStatusFilter}
            onValueChange={(value) => {
              store.setMemberStatusFilter(value);
              resetToFirstPage();
            }}
            ariaLabel="Filter members by status"
            options={[
              { value: "all", label: "All statuses" },
              { value: "active", label: "Active" },
              { value: "inactive", label: "Inactive" },
            ]}
            className="min-w-[160px]"
          />
        </div>
      </div>

      <div className="grid min-w-0 grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="min-w-0 rounded-2xl border border-[#CEC6B0]/40 bg-white p-5">
          {isLoading ? (
            <div className="flex h-48 items-center justify-center" role="status" aria-label="Loading members">
              <div className="h-7 w-7 animate-spin rounded-full border-2 border-[#8F740D] border-t-transparent" />
            </div>
          ) : (
            <div className={isFetching ? "opacity-70 transition-opacity" : "transition-opacity"}>
              <MembersTable members={members} total={total} page={page} limit={limit} onPageChange={setPage} onPageSizeChange={(value) => { setLimit(value); setPage(1); }} />
            </div>
          )}
        </div>

        <div className="hidden space-y-0 lg:block">
          <InvitePanel />
          <PendingInvites invitations={invitations} />
        </div>
      </div>

      {store.invitePanelOpen && (
        <div className="space-y-4 lg:hidden">
          <InvitePanel onSuccess={() => store.setInvitePanelOpen(false)} />
          <PendingInvites invitations={invitations} />
        </div>
      )}
    </PageContainer>
  );
};
