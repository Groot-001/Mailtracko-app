import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Loader2, Search, ScrollText } from "lucide-react";

import { getAuditLogs } from "../../../../feature/platform/api/platformApi";
import { PaginationControls } from "../../../../shared/components/PaginationControls";

export const Route = createFileRoute("/_protected/organization/account-settings/activity")({
  component: ActivityLog,
});

function ActivityLog() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const query = useQuery({
    queryKey: ["audit-logs", search, page, pageSize],
    queryFn: () => getAuditLogs(search, pageSize, (page - 1) * pageSize),
    placeholderData: (previous) => previous,
  });

  const total = query.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  return (
    <section className="overflow-hidden rounded-2xl border border-[#CEC6B0]/50 bg-white">
      <header className="flex flex-col gap-4 border-b border-[#EEE9DC] p-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-3">
          <ScrollText className="h-5 w-5 text-[#8F740D]" />
          <div>
            <h2 className="font-bold text-[#1A1C1C]">Workspace activity</h2>
            <p className="text-xs text-[#756F60]">Security-sensitive and administrative actions.</p>
          </div>
        </div>
        <label className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#9A9487]" />
          <span className="sr-only">Search activity</span>
          <input
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
            placeholder="Search actions"
            className="rounded-xl border border-[#CEC6B0]/60 py-2 pl-9 pr-3 text-sm"
          />
        </label>
      </header>

      {query.isLoading ? (
        <div className="grid min-h-60 place-items-center"><Loader2 className="h-5 w-5 animate-spin text-[#8F740D]" /></div>
      ) : query.isError ? (
        <p className="m-6 rounded-xl bg-red-50 p-4 text-sm text-red-800">Activity could not be loaded. Owner or admin access may be required.</p>
      ) : query.data?.items.length ? (
        <>
          <div className="divide-y divide-[#F4F1E8]">
            {query.data.items.map((item) => (
              <article key={item.uuid} className="flex flex-col gap-2 p-5 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-[#1A1C1C]" title={item.action}>{item.action.replaceAll(".", " · ").replaceAll("_", " ")}</p>
                  <p className="mt-1 truncate text-xs text-[#756F60]" title={item.resource_uuid || undefined}>{item.resource_type.replaceAll("_", " ")}{item.resource_uuid ? ` · ${item.resource_uuid}` : ""}</p>
                  <p className="mt-1 truncate text-xs text-[#756F60]">{item.actor?.email || "System"}{item.ip_address ? ` · ${item.ip_address}` : ""}</p>
                </div>
                <time className="shrink-0 text-xs text-[#756F60]">{new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(item.created_at))}</time>
              </article>
            ))}
          </div>
          <PaginationControls
            page={page}
            pageSize={pageSize}
            total={total}
            itemLabel="events"
            onPageChange={setPage}
            onPageSizeChange={(size) => {
              setPageSize(size);
              setPage(1);
            }}
          />
        </>
      ) : (
        <p className="p-12 text-center text-sm text-[#756F60]">No activity has been recorded for this workspace yet.</p>
      )}
    </section>
  );
}
