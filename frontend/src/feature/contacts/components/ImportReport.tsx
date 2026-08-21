import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, CheckCircle2, FileSpreadsheet, Loader2 } from "lucide-react";
import { PageContainer, PageHeader, PageSection } from "../../../shared/components/layout";

import { getContactImportHistory } from "../api/contactsApi";

const formatDate = (value: string) =>
  new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );

export const ImportReport = () => {
  const history = useQuery({ queryKey: ["contacts", "import-history"], queryFn: getContactImportHistory });
  const [selectedUuid, setSelectedUuid] = useState<string | null>(null);
  const selected = history.data?.items.find((item) => item.uuid === selectedUuid) || history.data?.items[0];

  return (
    <PageContainer>
      <PageHeader
        title="Import history"
        description="Every CSV and Google Sheets import is recorded with its real row-level outcome."
        breadcrumbs={
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[#8F740D]">
            Contacts
          </p>
        }
      />
      <PageSection>
        {history.isLoading ? (
          <div className="grid min-h-72 place-items-center">
            <Loader2 className="h-6 w-6 animate-spin text-[#8F740D]" />
          </div>
        ) : history.isError ? (
          <p className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            Import history could not be loaded.
          </p>
        ) : !history.data?.items.length ? (
          <div className="rounded-2xl border border-[#CEC6B0]/50 bg-white p-12 text-center">
            <FileSpreadsheet className="mx-auto h-9 w-9 text-[#C4BDAA]" />
            <h2 className="mt-3 font-bold">No imports yet</h2>
            <p className="mt-1 text-sm text-[#756F60]">
              Import a CSV or Google Sheet from Contacts to create the first report.
            </p>
          </div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-[340px_minmax(0,1fr)]">
            <aside className="overflow-hidden rounded-2xl border border-[#CEC6B0]/50 bg-white">
              <div className="border-b border-[#EEE9DC] p-5">
                <h2 className="font-bold">Import runs</h2>
                <p className="text-xs text-[#756F60]">{history.data.total} recorded</p>
              </div>
              <div className="max-h-[620px] divide-y divide-[#F4F1E8] overflow-y-auto">
                {history.data.items.map((item) => (
                  <button
                    type="button"
                    key={item.uuid}
                    onClick={() => setSelectedUuid(item.uuid)}
                    className={`w-full p-4 text-left ${
                      selected?.uuid === item.uuid ? "bg-[#F7F4E8]" : "hover:bg-[#FBFAF6]"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {item.error_count ? (
                        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                      ) : (
                        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                      )}
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold">{item.filename}</p>
                        <p className="mt-1 text-xs text-[#756F60]">{formatDate(item.created_at)}</p>
                        <p className="mt-1 text-[11px] text-[#756F60]">
                          {item.success_count} imported · {item.error_count} errors
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </aside>
            {selected && (
              <section className="space-y-5">
                <div className="rounded-2xl border border-[#CEC6B0]/50 bg-white p-6">
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="text-xs font-bold uppercase text-[#756F60]">
                        {selected.status}
                      </p>
                      <h2 className="mt-1 text-lg font-bold">{selected.filename}</h2>
                      <p className="mt-1 text-xs text-[#756F60]">
                        Started {formatDate(selected.created_at)}
                      </p>
                    </div>
                    <div className="grid grid-cols-3 gap-3 text-center">
                      <div className="rounded-xl bg-[#FBFAF6] p-3">
                        <p className="text-xl font-black">{selected.total_rows}</p>
                        <p className="text-[10px] uppercase text-[#756F60]">Rows</p>
                      </div>
                      <div className="rounded-xl bg-emerald-50 p-3">
                        <p className="text-xl font-black text-emerald-700">
                          {selected.success_count}
                        </p>
                        <p className="text-[10px] uppercase text-emerald-700">Imported</p>
                      </div>
                      <div className="rounded-xl bg-red-50 p-3">
                        <p className="text-xl font-black text-red-700">{selected.error_count}</p>
                        <p className="text-[10px] uppercase text-red-700">Errors</p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="overflow-hidden rounded-2xl border border-[#CEC6B0]/50 bg-white">
                  <div className="border-b border-[#EEE9DC] p-5">
                    <h3 className="font-bold">Row feedback</h3>
                    <p className="text-xs text-[#756F60]">
                      Only errors returned by the import parser are listed.
                    </p>
                  </div>
                  {selected.errors.length ? (
                    <div className="divide-y divide-[#F4F1E8]">
                      {selected.errors.map((issue, index) => (
                        <div key={`${issue.row || index}-${index}`} className="flex gap-4 p-4">
                          <span className="min-w-14 font-mono text-xs text-[#756F60]">
                            Row {issue.row ?? "—"}
                          </span>
                          <p className="text-sm text-red-800">
                            {issue.error || issue.message || "The row could not be imported."}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-10 text-center">
                      <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-600" />
                      <p className="mt-3 text-sm font-semibold">No row errors were reported.</p>
                    </div>
                  )}
                </div>
              </section>
            )}
          </div>
        )}
      </PageSection>
    </PageContainer>
  );
};
