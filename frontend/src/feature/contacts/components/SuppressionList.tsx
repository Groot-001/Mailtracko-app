import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Ban, Loader2, Plus, Search, ShieldCheck, Trash2 } from "lucide-react";

import { AppSelect } from "../../../shared/components/AppSelect";
import { ConfirmDialog } from "../../../shared/components/ConfirmDialog";
import { PaginationControls } from "../../../shared/components/PaginationControls";
import { useToast } from "../../../shared/hooks/useToast";
import { getApiErrorMessage } from "../../../shared/utils/apiError";
import { PageContainer, PageHeader, PageSection } from "../../../shared/components/layout";
import {
  addSuppression,
  getSuppressions,
  removeSuppression,
} from "../../platform/api/platformApi";

const formatDate = (value: string) =>
  new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );

export const SuppressionList = () => {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [email, setEmail] = useState("");
  const [reason, setReason] = useState("manual");
  const [pendingRemove, setPendingRemove] = useState<{ uuid: string; email: string } | null>(null);

  const suppressions = useQuery({
    queryKey: ["suppressions", search, page, pageSize],
    queryFn: () => getSuppressions(search, pageSize, (page - 1) * pageSize),
    placeholderData: (previous) => previous,
  });

  const total = suppressions.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  const add = useMutation({
    mutationFn: addSuppression,
    onSuccess: () => {
      setEmail("");
      setPage(1);
      showToast("Email added to the workspace suppression list.", "success");
      queryClient.invalidateQueries({ queryKey: ["suppressions"] });
    },
    onError: (error) => {
      showToast(getApiErrorMessage(error, "The address could not be suppressed."), "error");
    },
  });
  const remove = useMutation({
    mutationFn: removeSuppression,
    onSuccess: () => {
      setPendingRemove(null);
      showToast("Suppression removed successfully.", "success");
      queryClient.invalidateQueries({ queryKey: ["suppressions"] });
    },
    onError: (error) => {
      showToast(getApiErrorMessage(error, "The suppression could not be removed."), "error");
    },
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    add.mutate({ email: email.trim(), reason });
  };

  return (
    <PageContainer>
      <ConfirmDialog
        open={pendingRemove !== null}
        onOpenChange={(open) => {
          if (!open && !remove.isPending) setPendingRemove(null);
        }}
        title="Remove suppression?"
        description={`${pendingRemove?.email ?? "This address"} will be eligible for future campaigns unless another suppression rule applies.`}
        confirmLabel="Remove suppression"
        isLoading={remove.isPending}
        onConfirm={async () => {
          if (pendingRemove) await remove.mutateAsync(pendingRemove.uuid);
        }}
      />

      <PageHeader
        title="Global suppression list"
        description="Unsubscribed, bounced, complained, and manually blocked recipients are enforced across every campaign."
        breadcrumbs={<p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[#8F740D]">Deliverability</p>}
        actions={
          <div className="inline-flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-800">
            <ShieldCheck className="h-4 w-4" /> Campaign suppression is active
          </div>
        }
      />

      <PageSection>
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="overflow-hidden rounded-2xl border border-[#CEC6B0]/50 bg-white">
          <div className="flex flex-col gap-3 border-b border-[#EEE9DC] p-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="font-bold text-[#1A1C1C]">Suppressed recipients</h2>
              <p className="text-xs text-[#756F60]">{total} active entries</p>
            </div>
            <label className="relative block sm:w-72">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#9A9487]" />
              <span className="sr-only">Search suppressed email addresses</span>
              <input
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setPage(1);
                }}
                placeholder="Search email address"
                className="w-full rounded-xl border border-[#CEC6B0]/60 py-2 pl-9 pr-3 text-sm outline-none focus:border-[#8F740D]"
              />
            </label>
          </div>

          {suppressions.isLoading ? (
            <div className="grid min-h-52 place-items-center"><Loader2 className="h-5 w-5 animate-spin text-[#8F740D]" /></div>
          ) : suppressions.isError ? (
            <p className="m-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">The suppression list could not be loaded.</p>
          ) : suppressions.data?.items.length ? (
            <>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[620px] text-left text-sm">
                  <thead><tr className="bg-[#FBFAF6] text-[10px] uppercase tracking-wider text-[#756F60]"><th className="px-5 py-3">Email address</th><th className="px-5 py-3">Reason</th><th className="px-5 py-3">Added</th><th className="px-5 py-3 text-right">Action</th></tr></thead>
                  <tbody className="divide-y divide-[#F4F1E8]">
                    {suppressions.data.items.map((item) => (
                      <tr key={item.uuid} className="hover:bg-[#FBFAF6]">
                        <td className="max-w-[260px] truncate px-5 py-3.5 font-mono text-xs font-semibold text-[#1A1C1C]" title={item.email}>{item.email}</td>
                        <td className="px-5 py-3.5"><span className="rounded-full bg-red-50 px-2 py-1 text-[10px] font-bold uppercase text-red-700">{item.reason.replaceAll("_", " ")}</span></td>
                        <td className="px-5 py-3.5 text-xs text-[#625D4F]">{formatDate(item.suppressed_at)}</td>
                        <td className="px-5 py-3.5 text-right">
                          <button
                            type="button"
                            disabled={remove.isPending}
                            onClick={() => setPendingRemove({ uuid: item.uuid, email: item.email })}
                            className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50 disabled:opacity-50"
                          >
                            <Trash2 className="h-3.5 w-3.5" /> Remove
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <PaginationControls
                page={page}
                pageSize={pageSize}
                total={total}
                itemLabel="entries"
                onPageChange={setPage}
                onPageSizeChange={(size) => {
                  setPageSize(size);
                  setPage(1);
                }}
              />
            </>
          ) : (
            <div className="grid min-h-52 place-items-center p-8 text-center"><div><Ban className="mx-auto h-8 w-8 text-[#C4BDAA]" /><p className="mt-3 font-semibold text-[#1A1C1C]">No matching suppression entries</p><p className="mt-1 text-xs text-[#756F60]">Entries created by recipients and delivery events will appear here.</p></div></div>
          )}
        </div>

        <aside className="h-fit rounded-2xl border border-[#CEC6B0]/50 bg-white p-5">
          <div className="flex items-center gap-2"><Plus className="h-4 w-4 text-[#8F740D]" /><h2 className="font-bold text-[#1A1C1C]">Add an email</h2></div>
          <p className="mt-2 text-xs leading-relaxed text-[#756F60]">Use this for legal requests, complaints, known traps, or recipients who contacted your team directly.</p>
          <form onSubmit={submit} className="mt-5 space-y-4">
            <label className="block"><span className="text-xs font-bold text-[#4C4736]">Email address</span><input type="email" required value={email} onChange={(event) => setEmail(event.target.value)} className="mt-1.5 w-full rounded-xl border border-[#CEC6B0]/60 px-3 py-2.5 text-sm outline-none focus:border-[#8F740D]" /></label>
            <label className="block"><span className="text-xs font-bold text-[#4C4736]">Reason</span><AppSelect value={reason} onValueChange={setReason} ariaLabel="Suppression reason" className="mt-1.5" options={[{ value: "manual", label: "Manual block" }, { value: "complaint", label: "Complaint" }, { value: "legal_request", label: "Legal request" }, { value: "invalid_address", label: "Invalid address" }]} /></label>
            <button type="submit" disabled={add.isPending} className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#8F740D] px-4 py-2.5 text-xs font-bold text-white disabled:opacity-50">{add.isPending && <Loader2 className="h-4 w-4 animate-spin" />} {add.isPending ? "Adding…" : "Add to suppression list"}</button>
          </form>
        </aside>
        </div>
      </PageSection>
    </PageContainer>
  );
};
