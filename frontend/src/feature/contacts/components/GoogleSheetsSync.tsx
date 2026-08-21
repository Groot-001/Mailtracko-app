import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useSearch } from "@tanstack/react-router";
import {
  ExternalLink,
  FileSpreadsheet,
  Loader2,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";

import { AppSelect } from "../../../shared/components/AppSelect";
import { PageContainer, PageHeader, PageSection } from "../../../shared/components/layout";
import { DataPreviewTable } from "../../../shared/components/DataPreviewTable";
import { getApiErrorMessage } from "../../../shared/utils/apiError";
import {
  importFromGoogleSheet,
  initGoogleSheetsOauth,
  listContactLists,
  listGoogleSheetsTabs,
} from "../api/contactsApi";
import type { ImportSuccessData } from "../types/contacts.types";

const SHEET_URL_RE = /^https:\/\/docs\.google\.com\/spreadsheets\/d\/[A-Za-z0-9_-]+/;

const sheetImportSchema = z.object({
  sheetUrl: z
    .string()
    .trim()
    .min(1, "Paste a valid Google Sheets URL, for example https://docs.google.com/spreadsheets/d/...")
    .regex(
      SHEET_URL_RE,
      "Paste a valid Google Sheets URL, for example https://docs.google.com/spreadsheets/d/...",
    ),
  tab: z.string(),
  listUuid: z.string(),
});

type SheetImportFormValues = z.infer<typeof sheetImportSchema>;

export const GoogleSheetsSync = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const search: { success?: string; error?: string; message?: string } = useSearch({
    from: "/_protected/contacts/google-sheets",
  });
  const [oauthNotice, setOauthNotice] = useState<{
    kind: "success" | "error";
    message: string;
  } | null>(null);
  const lists = useQuery({
    queryKey: ["contact-lists", "sheet-import"],
    queryFn: () => listContactLists(200),
  });
  const [result, setResult] = useState<ImportSuccessData | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<SheetImportFormValues>({
    resolver: zodResolver(sheetImportSchema),
    defaultValues: {
      sheetUrl: "",
      tab: "",
      listUuid: "",
    },
  });

  const sheetUrl = watch("sheetUrl");
  const tab = watch("tab");
  const listUuid = watch("listUuid");

  const oauth = useMutation({
    mutationFn: initGoogleSheetsOauth,
    onSuccess: ({ auth_url }) => window.location.assign(auth_url),
  });
  const tabs = useMutation({
    mutationFn: listGoogleSheetsTabs,
    onSuccess: (data) => {
      setValue("tab", data.tabs[0]?.title || "", { shouldDirty: true, shouldValidate: true });
    },
  });
  const importMutation = useMutation({
    mutationFn: () => importFromGoogleSheet(listUuid, sheetUrl.trim(), tab),
    onSuccess: (data) => {
      setResult(data);
      reset();
      queryClient.invalidateQueries({ queryKey: ["contacts"] });
      queryClient.invalidateQueries({ queryKey: ["contacts", "import-history"] });
      queryClient.invalidateQueries({ queryKey: ["contact-lists"] });
    },
  });

  const loadTabs = handleSubmit((values) => {
    setResult(null);
    setValue("tab", "", { shouldDirty: true, shouldValidate: true });
    setOauthNotice(null);
    tabs.mutate(values.sheetUrl.trim());
  });

  const requestError = tabs.error || oauth.error || importMutation.error || lists.error;

  useEffect(() => {
    if (search.success === "sheets_connected") {
      setOauthNotice({
        kind: "success",
        message: "Google Sheets connected successfully. You can now load worksheet tabs.",
      });
    } else if (search.error) {
      setOauthNotice({
        kind: "error",
        message:
          search.message?.trim() ||
          (search.error === "oauth_denied"
            ? "Google Sheets authorization was cancelled or denied."
            : search.error === "oauth_invalid_callback"
              ? "Google returned an incomplete authorization response. Please try again."
              : "Google Sheets authorization failed. Please try connecting again."),
      });
    } else {
      return;
    }

    void navigate({ to: "/contacts/google-sheets", search: {}, replace: true });
  }, [navigate, search.error, search.message, search.success]);

  return (
    <PageContainer>
      <PageHeader
        title="Import from Google Sheets"
        description="Authorize Google, inspect live worksheet tabs, and import into a selected MailTracko collection."
        breadcrumbs={
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[#8F740D]">
            Contacts
          </p>
        }
        actions={
          <button
            type="button"
            disabled={oauth.isPending}
            onClick={() => oauth.mutate()}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-[#8F740D] bg-white px-4 py-2.5 text-xs font-bold text-[#6A5B00] disabled:opacity-50"
          >
            {oauth.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <ExternalLink className="h-4 w-4" />
            )}
            Connect Google account
          </button>
        }
      />
      <PageSection>

      {oauthNotice && (
        <div
          role="status"
          className={`rounded-xl border p-4 text-sm ${
            oauthNotice.kind === "success"
              ? "border-emerald-200 bg-emerald-50 text-emerald-900"
              : "border-red-200 bg-red-50 text-red-800"
          }`}
        >
          {oauthNotice.message}
        </div>
      )}

      <div className="flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
        <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0" />
        <p>
          MailTracko requests read-only spreadsheet access. Google credentials are
          stored encrypted and imports are recorded in the workspace audit trail.
        </p>
      </div>

      <section className="rounded-2xl border border-[#CEC6B0]/50 bg-white p-6">
        <div className="flex gap-3">
          <FileSpreadsheet className="h-5 w-5 text-[#8F740D]" />
          <div>
            <h2 className="font-bold">Import source</h2>
            <p className="text-xs text-[#756F60]">
              Paste the complete Google Sheets URL after authorizing your account. The
              sheet header must contain all columns of the CSV import template:
              email, first_name, last_name, company, phone, city, state, country.
            </p>
          </div>
        </div>

        <form onSubmit={loadTabs} noValidate className="mt-6 space-y-5">
          <label className="block">
            <span className="text-xs font-bold text-[#4C4736]">Google Sheets URL</span>
            <div className="mt-1.5 flex flex-col gap-2 sm:flex-row">
              <input
                type="url"
                maxLength={2048}
                autoComplete="url"
                {...register("sheetUrl", {
                  onChange: () => {
                    setResult(null);
                  },
                })}
                placeholder="https://docs.google.com/spreadsheets/d/..."
                className="min-w-0 flex-1 rounded-xl border border-[#CEC6B0]/60 bg-white px-3 py-2.5 text-sm text-[#1A1C1C] placeholder:text-[#9A9385] focus:border-[#8F740D] focus:outline-none focus:ring-1 focus:ring-[#F1D442]/30"
              />
              <button
                disabled={tabs.isPending || !sheetUrl.trim()}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#1A1C1C] px-4 py-2.5 text-xs font-bold text-white disabled:opacity-50"
              >
                {tabs.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                Load worksheets
              </button>
            </div>
            {errors.sheetUrl && (
              <span role="alert" className="mt-1.5 block text-xs font-semibold text-red-600">
                {errors.sheetUrl.message}
              </span>
            )}
          </label>

          {requestError && (
            <div role="alert" className="flex flex-col gap-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800 sm:flex-row sm:items-center sm:justify-between">
              <p className="min-w-0">
                {getApiErrorMessage(
                  requestError,
                  "The Google Sheets request could not be completed.",
                )}
              </p>
              <button
                type="button"
                disabled={oauth.isPending}
                onClick={() => oauth.mutate()}
                className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg border border-red-200 bg-white px-3 py-2 text-xs font-bold text-red-700 hover:bg-red-50 disabled:opacity-50"
              >
                {oauth.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
                Reconnect Google
              </button>
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <label>
              <span className="text-xs font-bold text-[#4C4736]">Worksheet</span>
              <AppSelect
                value={tab}
                onValueChange={(value) => setValue("tab", value, { shouldDirty: true, shouldValidate: true })}
                disabled={!tabs.data?.tabs.length}
                ariaLabel="Worksheet"
                searchable
                className="mt-1.5"
                options={[
                  { value: "", label: "Load worksheets first", disabled: Boolean(tabs.data?.tabs.length) },
                  ...(tabs.data?.tabs.map((item) => ({ value: item.title, label: `${item.title} · ${item.row_count} rows` })) ?? []),
                ]}
              />
            </label>

            <label>
              <span className="text-xs font-bold text-[#4C4736]">Target collection</span>
              <AppSelect
                value={listUuid}
                onValueChange={(value) => setValue("listUuid", value, { shouldDirty: true, shouldValidate: true })}
                disabled={lists.isPending || lists.isError}
                ariaLabel="Target collection"
                searchable
                className="mt-1.5"
                options={[
                  { value: "", label: "Select a collection" },
                  ...(lists.data?.items.map((item) => ({ value: item.uuid, label: item.name })) ?? []),
                ]}
              />
            </label>
          </div>

          <div className="flex justify-end">
            <button
              type="button"
              disabled={!tab || !listUuid || importMutation.isPending}
              onClick={() => importMutation.mutate()}
              className="inline-flex items-center gap-2 rounded-xl bg-[#8F740D] px-5 py-2.5 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {importMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Import worksheet
            </button>
          </div>
        </form>
      </section>

      {result && (
        <section className="rounded-2xl border border-[#CEC6B0]/50 bg-white p-6">
          <h2 className="font-bold">Import completed</h2>
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {[
              ["Rows", result.total],
              ["Imported", result.imported],
              ["Updated", result.updated],
              ["Duplicates", result.duplicates ?? 0],
              ["Skipped", result.skipped ?? result.errors.length],
              ["Errors", result.errors.length],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl bg-[#FBFAF6] p-4 text-center">
                <p className="text-xl font-black">{value}</p>
                <p className="text-[10px] uppercase text-[#756F60]">{label}</p>
              </div>
            ))}
          </div>

          {result.preview && result.preview.headers.length > 0 && (
            <div className="mt-5">
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#756F60]">
                Imported data preview
              </p>
              <DataPreviewTable
                headers={result.preview.headers}
                rows={result.preview.rows}
              />
            </div>
          )}

          {result.errors.length > 0 && (
            <div className="mt-5 divide-y divide-red-100 rounded-xl border border-red-200 bg-red-50">
              {result.errors.slice(0, 20).map((error, index) => (
                <p key={`${error.row}-${index}`} className="p-3 text-xs text-red-800">
                  Row {error.row}: {error.error}
                </p>
              ))}
              {result.errors.length > 20 && (
                <p className="p-3 text-xs font-semibold text-red-800">
                  {result.errors.length - 20} additional row errors were omitted from this
                  preview.
                </p>
              )}
            </div>
          )}
        </section>
      )}
      </PageSection>
    </PageContainer>
  );
};