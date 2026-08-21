import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import {
  AlertTriangle,
  Building2,
  CreditCard,
  Database,
  Loader2,
  Megaphone,
  Search,
  Server,
  Shield,
  TicketCheck,
  Trash2,
  Users,
} from "lucide-react";

import { PageContainer, PageHeader, PageSection } from "../../../shared/components/layout";

import {
  deleteAdminOrganization,
  deleteAdminUser,
  getAdminDashboard,
  getAdminOrganizations,
  getAdminUsers,
  getPlatformAccess,
  updateAdminOrganizationStatus,
  updateAdminUserStatus,
} from "../../../feature/platform/api/platformApi";
import { StripeAdminPanel } from "../../../feature/platform/components/StripeAdminPanel";
import { ConfirmDialog } from "../../../shared/components/ConfirmDialog";
import { PaginationControls } from "../../../shared/components/PaginationControls";
import { useToast } from "../../../shared/hooks/useToast";
import { getApiErrorMessage } from "../../../shared/utils/apiError";

export const Route = createFileRoute("/_protected/admin/")({ component: AdminConsole });

const money = (cents: number) =>
  new Intl.NumberFormat(undefined, { style: "currency", currency: "USD" }).format(cents / 100);

function AdminConsole() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [userSearchInput, setUserSearchInput] = useState("");
  const [userSearch, setUserSearch] = useState("");
  const [organizationPage, setOrganizationPage] = useState(1);
  const [organizationPageSize, setOrganizationPageSize] = useState(10);
  const [userPage, setUserPage] = useState(1);
  const [userPageSize, setUserPageSize] = useState(10);
  const [pendingDelete, setPendingDelete] = useState<{
    kind: "organization" | "user";
    uuid: string;
    label: string;
  } | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setUserSearch(userSearchInput.trim());
      setUserPage(1);
    }, 350);
    return () => window.clearTimeout(timer);
  }, [userSearchInput]);

  const access = useQuery({ queryKey: ["platform", "access"], queryFn: getPlatformAccess });
  const isAdmin = access.data?.is_platform_admin === true;
  const dashboard = useQuery({
    queryKey: ["admin", "dashboard"],
    queryFn: getAdminDashboard,
    enabled: isAdmin,
  });
  const organizations = useQuery({
    queryKey: ["admin", "organizations", organizationPage, organizationPageSize],
    queryFn: () => getAdminOrganizations(organizationPageSize, (organizationPage - 1) * organizationPageSize),
    enabled: isAdmin,
    placeholderData: (previous) => previous,
  });
  const users = useQuery({
    queryKey: ["admin", "users", userSearch, userPage, userPageSize],
    queryFn: () => getAdminUsers(userSearch, userPageSize, (userPage - 1) * userPageSize),
    enabled: isAdmin,
    placeholderData: (previous) => previous,
  });

  const organizationTotal = organizations.data?.total ?? 0;
  const userTotal = users.data?.total ?? 0;
  const organizationTotalPages = Math.max(1, Math.ceil(organizationTotal / organizationPageSize));
  const userTotalPages = Math.max(1, Math.ceil(userTotal / userPageSize));

  useEffect(() => {
    if (organizationPage > organizationTotalPages) setOrganizationPage(organizationTotalPages);
  }, [organizationPage, organizationTotalPages]);
  useEffect(() => {
    if (userPage > userTotalPages) setUserPage(userTotalPages);
  }, [userPage, userTotalPages]);

  const status = useMutation({
    mutationFn: updateAdminOrganizationStatus,
    onSuccess: (_, payload) => {
      showToast(`Organization ${payload.status === "active" ? "reactivated" : "suspended"} successfully.`, "success");
      queryClient.invalidateQueries({ queryKey: ["admin", "organizations"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "dashboard"] });
    },
    onError: (error) => showToast(getApiErrorMessage(error, "Organization status could not be updated."), "error"),
  });
  const userStatus = useMutation({
    mutationFn: updateAdminUserStatus,
    onSuccess: (_, payload) => {
      showToast(`User ${payload.is_active ? "reactivated" : "suspended"} successfully.`, "success");
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "dashboard"] });
    },
    onError: (error) => showToast(getApiErrorMessage(error, "User status could not be updated."), "error"),
  });
  const removeUser = useMutation({
    mutationFn: deleteAdminUser,
    onSuccess: () => {
      setPendingDelete(null);
      showToast("User deleted successfully.", "success");
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "dashboard"] });
    },
    onError: (error) => showToast(getApiErrorMessage(error, "User could not be deleted."), "error"),
  });
  const removeOrganization = useMutation({
    mutationFn: deleteAdminOrganization,
    onSuccess: () => {
      setPendingDelete(null);
      showToast("Organization deleted successfully.", "success");
      queryClient.invalidateQueries({ queryKey: ["admin", "organizations"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "dashboard"] });
    },
    onError: (error) => showToast(getApiErrorMessage(error, "Organization could not be deleted."), "error"),
  });

  if (access.isLoading) {
    return <div className="grid min-h-[60vh] place-items-center"><Loader2 className="h-6 w-6 animate-spin text-[#8F740D]" /></div>;
  }
  if (access.isError) {
    return <AdminError title="Could not verify administrator access" message={getApiErrorMessage(access.error, "Refresh the page or sign in again.")} />;
  }
  if (!isAdmin) {
    return (
      <div className="mx-auto mt-16 max-w-xl rounded-2xl border border-red-200 bg-red-50 p-8 text-center">
        <Shield className="mx-auto h-8 w-8 text-red-700" />
        <h1 className="mt-3 text-lg font-bold text-red-950">Platform administrator access required</h1>
        <p className="mt-2 text-sm text-red-800">This console is separate from workspace owner and admin roles.</p>
      </div>
    );
  }
  if (dashboard.isLoading) {
    return <div className="grid min-h-[60vh] place-items-center"><Loader2 className="h-6 w-6 animate-spin text-[#8F740D]" /></div>;
  }
  if (dashboard.isError || !dashboard.data) {
    return <AdminError title="Administration dashboard unavailable" message={getApiErrorMessage(dashboard.error, "The dashboard could not be loaded. Try again.")} />;
  }

  const data = dashboard.data;
  const deleting = removeUser.isPending || removeOrganization.isPending;
  const handleConfirmDelete = async () => {
    if (!pendingDelete) return;
    if (pendingDelete.kind === "organization") await removeOrganization.mutateAsync(pendingDelete.uuid);
    else await removeUser.mutateAsync(pendingDelete.uuid);
  };
  const cards = [
    ["Users", `${data.users.active} active`, `${data.users.total} total`, Users],
    ["Organizations", data.organizations, "customer workspaces", Building2],
    ["Campaigns", data.campaigns, "all tenants", Megaphone],
    ["Net revenue", money(data.billing.net_revenue_cents), "provider-settled", CreditCard],
    ["Support queue", data.support.open_tickets, "open tickets", TicketCheck],
    ["Risk events", data.risk.open_abuse_events, "open investigations", AlertTriangle],
  ] as const;

  return (
    <PageContainer>
      <PageHeader
        title="MailTracko administration"
        description="Tenant operations, revenue, support, risk, plans, providers, and feature controls use audited APIs."
        breadcrumbs={
          <div className="flex items-center gap-2 text-[#8F740D]">
            <Shield className="h-4 w-4" />
            <p className="text-[11px] font-bold uppercase tracking-[0.18em]">Platform control plane</p>
          </div>
        }
      />

      <PageSection>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
        {cards.map(([label, value, detail, Icon]) => (
          <article key={label} className="rounded-2xl border border-[#CEC6B0]/50 bg-white p-4">
            <Icon className="h-5 w-5 text-[#8F740D]" />
            <p className="mt-4 text-[10px] font-bold uppercase tracking-wider text-[#756F60]">{label}</p>
            <p className="mt-1 text-xl font-black text-[#1A1C1C]">{value}</p>
            <p className="mt-1 text-[11px] text-[#756F60]">{detail}</p>
          </article>
        ))}
        </div>
      </PageSection>

      <PageSection>
        <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex items-center gap-3 rounded-2xl border border-[#CEC6B0]/50 bg-white p-4">
          <Database className={`h-5 w-5 ${data.infrastructure.database === "healthy" ? "text-emerald-600" : "text-red-600"}`} />
          <div><p className="text-xs font-bold">PostgreSQL</p><p className="text-[11px] capitalize text-[#756F60]">{data.infrastructure.database}</p></div>
        </div>
        <div className="flex items-center gap-3 rounded-2xl border border-[#CEC6B0]/50 bg-white p-4">
          <Server className={`h-5 w-5 ${data.infrastructure.redis === "healthy" ? "text-emerald-600" : "text-red-600"}`} />
          <div><p className="text-xs font-bold">Redis</p><p className="text-[11px] capitalize text-[#756F60]">{data.infrastructure.redis}</p></div>
        </div>
        </div>
      </PageSection>

      <PageSection>
        <StripeAdminPanel />
      </PageSection>

      <PageSection>
        <section className="overflow-hidden rounded-2xl border border-[#CEC6B0]/50 bg-white">
        <header className="border-b border-[#EEE9DC] p-5">
          <h2 className="font-bold">Customer organizations</h2>
          <p className="text-xs text-[#756F60]">Subscription and operational status across all tenants.</p>
        </header>
        {organizations.isLoading ? (
          <Loader2 className="m-6 h-5 w-5 animate-spin" />
        ) : organizations.isError ? (
          <p className="m-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{getApiErrorMessage(organizations.error, "Could not load organizations.")}</p>
        ) : organizations.data?.items.length ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[900px] text-left text-sm">
                <thead><tr className="bg-[#FBFAF6] text-[10px] uppercase tracking-wider text-[#756F60]"><th className="px-5 py-3">Organization</th><th className="px-5 py-3">Owner</th><th className="px-5 py-3">Plan</th><th className="px-5 py-3">Subscription</th><th className="px-5 py-3">Workspace</th><th className="px-5 py-3 text-right">Action</th></tr></thead>
                <tbody className="divide-y divide-[#F4F1E8]">
                  {organizations.data.items.map((org) => (
                    <tr key={org.uuid}>
                      <td className="px-5 py-3.5"><p className="max-w-[240px] truncate font-semibold" title={org.name}>{org.name}</p><p className="max-w-[240px] truncate text-xs text-[#756F60]">{org.domain_email || org.uuid}</p></td>
                      <td className="px-5 py-3.5 text-xs">{org.owner_email}</td>
                      <td className="px-5 py-3.5">{org.plan_name || "Unassigned"}</td>
                      <td className="px-5 py-3.5 capitalize">{org.subscription_status || "none"}</td>
                      <td className="px-5 py-3.5"><span className={`rounded-full px-2 py-1 text-[10px] font-bold uppercase ${org.status === "active" ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>{org.status}</span></td>
                      <td className="px-5 py-3.5"><div className="flex justify-end gap-2"><button disabled={status.isPending} onClick={() => status.mutate({ uuid: org.uuid, status: org.status === "active" ? "suspended" : "active" })} className={`rounded-lg border px-3 py-1.5 text-xs font-semibold ${org.status === "active" ? "border-red-200 text-red-700 hover:bg-red-50" : "border-emerald-200 text-emerald-700 hover:bg-emerald-50"}`}>{org.status === "active" ? "Suspend" : "Reactivate"}</button><button disabled={deleting} onClick={() => setPendingDelete({ kind: "organization", uuid: org.uuid, label: org.name })} className="rounded-lg border border-red-200 p-2 text-red-700 hover:bg-red-50 disabled:opacity-50" aria-label={`Delete ${org.name}`}><Trash2 className="h-3.5 w-3.5" /></button></div></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <PaginationControls page={organizationPage} pageSize={organizationPageSize} total={organizationTotal} itemLabel="organizations" onPageChange={setOrganizationPage} onPageSizeChange={(size) => { setOrganizationPageSize(size); setOrganizationPage(1); }} />
          </>
        ) : (
          <p className="p-10 text-center text-sm text-[#756F60]">No customer organizations found.</p>
        )}
      </section>
      </PageSection>

      <PageSection>
        <section className="overflow-hidden rounded-2xl border border-[#CEC6B0]/50 bg-white">
        <header className="flex flex-col justify-between gap-4 border-b border-[#EEE9DC] p-5 sm:flex-row sm:items-end">
          <div><h2 className="font-bold">User management</h2><p className="text-xs text-[#756F60]">Search, suspend, reactivate, or soft-delete user accounts.</p></div>
          <label className="flex items-center gap-2 rounded-xl border border-[#CEC6B0]/60 bg-[#FBFAF6] px-3 py-2"><Search className="h-4 w-4 text-[#756F60]" /><span className="sr-only">Search users</span><input value={userSearchInput} onChange={(event) => setUserSearchInput(event.target.value)} placeholder="Search users" className="bg-transparent text-sm outline-none" /></label>
        </header>
        {users.isLoading ? (
          <Loader2 className="m-6 h-5 w-5 animate-spin" />
        ) : users.isError ? (
          <p className="m-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{getApiErrorMessage(users.error, "Could not load users.")}</p>
        ) : users.data?.items.length ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead><tr className="bg-[#FBFAF6] text-[10px] uppercase tracking-wider text-[#756F60]"><th className="px-5 py-3">User</th><th className="px-5 py-3">Verified</th><th className="px-5 py-3">Last login</th><th className="px-5 py-3">Status</th><th className="px-5 py-3 text-right">Actions</th></tr></thead>
                <tbody className="divide-y divide-[#F4F1E8]">
                  {users.data.items.map((user) => (
                    <tr key={user.uuid}>
                      <td className="px-5 py-3.5"><p className="max-w-[260px] truncate font-semibold" title={user.full_name || user.email}>{user.full_name || "Unnamed user"}</p><p className="max-w-[260px] truncate text-xs text-[#756F60]" title={user.email}>{user.email}</p></td>
                      <td className="px-5 py-3.5 text-xs">{user.email_verified_at ? "Yes" : "No"}</td>
                      <td className="px-5 py-3.5 text-xs">{user.last_login_at ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(user.last_login_at)) : "Never"}</td>
                      <td className="px-5 py-3.5"><span className={`rounded-full px-2 py-1 text-[10px] font-bold uppercase ${user.is_active ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>{user.is_active ? "Active" : "Suspended"}</span></td>
                      <td className="px-5 py-3.5"><div className="flex justify-end gap-2"><button disabled={userStatus.isPending} onClick={() => userStatus.mutate({ uuid: user.uuid, is_active: !user.is_active })} className="rounded-lg border border-[#CEC6B0] px-3 py-1.5 text-xs font-semibold disabled:opacity-50">{user.is_active ? "Suspend" : "Reactivate"}</button><button disabled={deleting} onClick={() => setPendingDelete({ kind: "user", uuid: user.uuid, label: user.email })} className="rounded-lg border border-red-200 p-2 text-red-700 hover:bg-red-50 disabled:opacity-50" aria-label={`Delete ${user.email}`}><Trash2 className="h-3.5 w-3.5" /></button></div></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <PaginationControls page={userPage} pageSize={userPageSize} total={userTotal} itemLabel="users" onPageChange={setUserPage} onPageSizeChange={(size) => { setUserPageSize(size); setUserPage(1); }} />
          </>
        ) : (
          <p className="p-10 text-center text-sm text-[#756F60]">No users match the current search.</p>
        )}
        </section>
      </PageSection>

      <ConfirmDialog
        open={pendingDelete !== null}
        onOpenChange={(open) => {
          if (!open && !deleting) setPendingDelete(null);
        }}
        title={pendingDelete?.kind === "organization" ? "Delete organization?" : "Delete user?"}
        description={pendingDelete?.kind === "organization"
          ? `Delete ${pendingDelete.label}? This hides the tenant and stops access.`
          : `Delete ${pendingDelete?.label ?? "this user"}? Existing sessions will be revoked.`}
        confirmLabel="Delete"
        isLoading={deleting}
        onConfirm={handleConfirmDelete}
      />
    </PageContainer>
  );
}

function AdminError({ title, message }: { title: string; message: string }) {
  return (
    <div className="mx-auto mt-16 max-w-xl rounded-2xl border border-red-200 bg-red-50 p-8 text-center">
      <AlertTriangle className="mx-auto h-8 w-8 text-red-700" />
      <h1 className="mt-3 text-lg font-bold text-red-950">{title}</h1>
      <p className="mt-2 text-sm text-red-800">{message}</p>
    </div>
  );
}
