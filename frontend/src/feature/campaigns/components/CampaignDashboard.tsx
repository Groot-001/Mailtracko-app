import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import {
  AlertTriangle,
  Archive,
  CheckCircle2,
  Clock3,
  Copy,
  Edit3,
  MoreVertical,
  PauseCircle,
  PlayCircle,
  Plus,
  Search,
  Send,
  Trash2,
} from "lucide-react";
import { useEmailAccounts } from "../../../shared/api/useWorkspaceData";
import { AppSelect } from "../../../shared/components/AppSelect";
import { PaginationControls } from "../../../shared/components/PaginationControls";
import { InlineNotice } from "../../../shared/components/InlineNotice";
import { getApiErrorMessage } from "../../../shared/utils/apiError";
import { PageContainer, PageHeader, PageSection } from "../../../shared/components/layout";
import {
  useArchiveCampaign,
  useCampaignSummary,
  useDeleteCampaign,
  useCampaigns,
  useDuplicateCampaign,
  usePauseCampaign,
  useResumeCampaign,
  useRestoreCampaign,
} from "../hooks/useCampaigns";
import type { Campaign, CampaignStatus } from "../types/campaign.types";


const formatDate = (value: string | null) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
};

const statusStyles: Record<string, string> = {
  draft: "border-[#D8D8D8] bg-[#F3F3F3] text-[#5F6470]",
  ready: "border-[#CDE8D4] bg-[#EAF7ED] text-[#26733D]",
  scheduled: "border-[#F0D9A6] bg-[#FFF4DB] text-[#976312]",
  launching: "border-[#F0D9A6] bg-[#FFF4DB] text-[#976312]",
  running: "border-[#CDE8D4] bg-[#EAF7ED] text-[#26733D]",
  paused: "border-[#F4C6C2] bg-[#FFF0EF] text-[#B42318]",
  completed: "border-[#C8D7F5] bg-[#EDF3FF] text-[#315EA8]",
  cancelled: "border-[#E0E0E0] bg-[#F4F4F4] text-[#686D78]",
  failed: "border-[#F4C6C2] bg-[#FFF0EF] text-[#B42318]",
  archived: "border-[#E0E0E0] bg-[#F4F4F4] text-[#686D78]",
};

const statusLabel = (status: string) =>
  status.charAt(0).toUpperCase() + status.slice(1).replaceAll("_", " ");

const SummaryCard = ({
  icon: Icon,
  label,
  value,
  description,
}: {
  icon: typeof Send;
  label: string;
  value: number;
  description: string;
}) => (
  <div className="rounded-2xl border border-[#E8E1D0] bg-white p-5 shadow-[0_8px_24px_rgba(66,54,16,0.04)]">
    <div className="flex items-center gap-4">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#F8F0D7] text-[#8F740D]">
        <Icon className="h-6 w-6" />
      </div>
      <div>
        <p className="text-sm text-[#696253]">{label}</p>
        <p className="mt-0.5 text-2xl font-bold text-[#111827]">{value}</p>
        <p className="mt-1 text-xs text-[#99917D]">{description}</p>
      </div>
    </div>
  </div>
);

export const CampaignDashboard = () => {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<CampaignStatus | "">("");
  const [section, setSection] = useState<"active" | "archived">("active");
  const [accountUuid, setAccountUuid] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const [menuPosition, setMenuPosition] = useState<{ top?: number; bottom?: number; right: number } | null>(null);
  const actionMenuRef = useRef<HTMLDivElement | null>(null);
  const [feedback, setFeedback] = useState<{ tone: "success" | "error"; text: string } | null>(null);
  const [campaignPendingDelete, setCampaignPendingDelete] = useState<Campaign | null>(null);
  const activeCampaignDefaults = { include_archived: false } as const;
  const params = useMemo(
    () => ({
      search,
      status: section === "archived" ? "archived" : status,
      email_account_uuid: accountUuid || undefined,
      include_archived: activeCampaignDefaults.include_archived,
      limit: pageSize,
      offset: (page - 1) * pageSize,
    }),
    [accountUuid, page, pageSize, search, section, status],
  );
  const campaignsQuery = useCampaigns(params);
  const summaryQuery = useCampaignSummary();
  const accountsQuery = useEmailAccounts();
  const duplicateMutation = useDuplicateCampaign();
  const pauseMutation = usePauseCampaign();
  const resumeMutation = useResumeCampaign();
  const archiveMutation = useArchiveCampaign();
  const restoreMutation = useRestoreCampaign();
  const deleteMutation = useDeleteCampaign();

  const totalPages = Math.max(1, Math.ceil((campaignsQuery.data?.total ?? 0) / pageSize));
  const summary = summaryQuery.data;

  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  useEffect(() => {
    if (!openMenu) return;

    const closeOnOutsideClick = (event: MouseEvent) => {
      const target = event.target as Element | null;
      if (target?.closest("[data-action-menu-trigger='true']")) return;
      if (!actionMenuRef.current?.contains(target as Node)) {
        setOpenMenu(null);
      }
    };

    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpenMenu(null);
      }
    };

    const closeOnViewportChange = () => setOpenMenu(null);
    document.addEventListener("mousedown", closeOnOutsideClick);
    document.addEventListener("keydown", closeOnEscape);
    window.addEventListener("resize", closeOnViewportChange);
    window.addEventListener("scroll", closeOnViewportChange, true);
    return () => {
      document.removeEventListener("mousedown", closeOnOutsideClick);
      document.removeEventListener("keydown", closeOnEscape);
      window.removeEventListener("resize", closeOnViewportChange);
      window.removeEventListener("scroll", closeOnViewportChange, true);
    };
  }, [openMenu]);

  const runAction = async (action: () => Promise<unknown>, success: string) => {
    setOpenMenu(null);
    setFeedback(null);
    try {
      await action();
      setFeedback({ tone: "success", text: success });
    } catch (error) {
      setFeedback({ tone: "error", text: getApiErrorMessage(error, "The campaign action could not be completed.") });
    }
  };

  const actionMenu = (campaign: Campaign) => (
    <div
      ref={actionMenuRef}
      style={menuPosition ?? undefined}
      className="fixed z-50 w-52 rounded-xl border border-[#E4DDCD] bg-white p-1.5 text-left shadow-xl"
    >
      <Link
        to="/campaigns/$campaignUuid"
        params={{ campaignUuid: campaign.uuid }}
        onClick={() => setOpenMenu(null)}
        className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-[#3E4350] hover:bg-[#F8F4E9]"
      >
        <Send className="h-4 w-4" /> View Campaign
      </Link>
      {campaign.status === "draft" && (
        <Link
          to="/campaigns/$campaignUuid/edit"
          params={{ campaignUuid: campaign.uuid }}
          onClick={() => setOpenMenu(null)}
          className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-[#3E4350] hover:bg-[#F8F4E9]"
        >
          <Edit3 className="h-4 w-4" /> Edit Campaign
        </Link>
      )}
      <button
        type="button"
        onClick={async () => {
          setOpenMenu(null);
          setFeedback(null);
          try {
            const duplicated = await duplicateMutation.mutateAsync(campaign.uuid);
            setFeedback({ tone: "success", text: "Campaign duplicated as a draft." });
            navigate({ to: "/campaigns/$campaignUuid/edit", params: { campaignUuid: duplicated.uuid } });
          } catch (error) {
            setFeedback({ tone: "error", text: getApiErrorMessage(error, "The campaign action could not be completed.") });
          }
        }}
        className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-[#3E4350] hover:bg-[#F8F4E9]"
      >
        <Copy className="h-4 w-4" /> Duplicate Campaign
      </button>
      {campaign.status === "running" && (
        <button
          type="button"
          onClick={() => runAction(() => pauseMutation.mutateAsync(campaign.uuid), "Campaign paused.")}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-[#3E4350] hover:bg-[#F8F4E9]"
        >
          <PauseCircle className="h-4 w-4" /> Pause Campaign
        </button>
      )}
      {campaign.status === "paused" && (
        <button
          type="button"
          onClick={() => runAction(() => resumeMutation.mutateAsync(campaign.uuid), "Campaign resumed.")}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-[#3E4350] hover:bg-[#F8F4E9]"
        >
          <PlayCircle className="h-4 w-4" /> Resume Campaign
        </button>
      )}
      {!(["archived", "running", "launching"].includes(campaign.status)) && (
        <button
          type="button"
          onClick={() => runAction(() => archiveMutation.mutateAsync(campaign.uuid), "Campaign archived.")}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-[#3E4350] hover:bg-[#F8F4E9]"
        >
          <Archive className="h-4 w-4" /> Archive Campaign
        </button>
      )}
      {campaign.status === "archived" && (
        <button
          type="button"
          onClick={() => runAction(() => restoreMutation.mutateAsync(campaign.uuid), "Campaign restored from archive.")}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-[#3E4350] hover:bg-[#F8F4E9]"
        >
          <CheckCircle2 className="h-4 w-4" /> Restore Campaign
        </button>
      )}
      {!(["running", "launching"].includes(campaign.status)) && (
        <button
          type="button"
          onClick={() => {
            setOpenMenu(null);
            setCampaignPendingDelete(campaign);
          }}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-[#B42318] hover:bg-[#FFF1EF]"
        >
          <Trash2 className="h-4 w-4" /> Delete Campaign
        </button>
      )}
    </div>
  );

  return (
    <PageContainer>
      <PageHeader
        title="Campaigns"
        description="Create, launch, and monitor organization email campaigns."
        actions={
          <Link
            to="/campaigns/new"
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#8F740D] px-5 py-3 text-sm font-semibold text-white shadow-button hover:bg-[#735D0B]"
          >
            <Plus className="h-4 w-4" /> Create Campaign
          </Link>
        }
      />

      {feedback && <div className="mt-5"><InlineNotice tone={feedback.tone}>{feedback.text}</InlineNotice></div>}

      <PageSection>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          <SummaryCard icon={Send} label="Total Campaigns" value={summary?.total_campaigns ?? 0} description="All campaigns" />
          <SummaryCard icon={PlayCircle} label="Active" value={summary?.active ?? 0} description="Currently sending" />
          <SummaryCard icon={Clock3} label="Scheduled" value={summary?.scheduled ?? 0} description="Waiting to start" />
          <SummaryCard icon={PauseCircle} label="Paused" value={summary?.paused ?? 0} description="Temporarily stopped" />
          <SummaryCard icon={CheckCircle2} label="Drafts" value={summary?.drafts ?? 0} description="Still being configured" />
        </div>
      </PageSection>

      <PageSection>
        <div className="inline-flex rounded-xl border border-[#DED7C7] bg-white p-1">
        <button type="button" onClick={() => { setSection("active"); setStatus(""); setPage(1); }} className={`rounded-lg px-4 py-2 text-sm font-semibold ${section === "active" ? "bg-[#8F740D] text-white" : "text-[#625A47] hover:bg-[#F8F5EC]"}`}>Active Campaigns</button>
        <button type="button" onClick={() => { setSection("archived"); setStatus(""); setPage(1); }} className={`rounded-lg px-4 py-2 text-sm font-semibold ${section === "archived" ? "bg-[#8F740D] text-white" : "text-[#625A47] hover:bg-[#F8F5EC]"}`}>Archived Campaigns</button>
      </div>

      <section className="mt-4 overflow-visible rounded-2xl border border-[#E8E1D0] bg-white shadow-[0_8px_28px_rgba(66,54,16,0.04)]">
        <div className="grid gap-3 border-b border-[#EEE8DA] p-4 md:grid-cols-[minmax(240px,1fr)_200px_240px_auto]">
          <label className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8D8572]" />
            <input
              value={search}
              onChange={(event) => { setSearch(event.target.value); setPage(1); }}
              placeholder="Search campaigns..."
              className="h-11 w-full rounded-xl border border-[#DED7C7] pl-10 pr-3 text-sm outline-none focus:border-[#A88916] focus:ring-2 focus:ring-[#E9DFAE]"
            />
          </label>
          {section === "active" ? (
            <AppSelect value={status} onValueChange={(value) => { setStatus(value as CampaignStatus | ""); setPage(1); }} ariaLabel="Campaign status" options={[{ value: "", label: "All Active Statuses" }, ...Object.keys(statusStyles).filter((value) => value !== "archived").map((value) => ({ value, label: statusLabel(value) }))]} />
          ) : (
            <div className="flex h-11 items-center rounded-xl border border-[#DED7C7] bg-[#F8F5EC] px-3 text-sm font-medium text-[#625A47]">Archived only</div>
          )}
          <AppSelect value={accountUuid} onValueChange={(value) => { setAccountUuid(value); setPage(1); }} ariaLabel="Sender account" searchable options={[{ value: "", label: "All Sender Accounts" }, ...(accountsQuery.data?.items.map((account) => ({ value: account.uuid, label: account.email })) ?? [])]} />
          <button
            type="button"
            onClick={() => { setSearch(""); setStatus(""); setAccountUuid(""); setPage(1); }}
            className="h-11 rounded-xl border border-[#DED7C7] px-4 text-sm font-medium text-[#625A47] hover:bg-[#F8F5EC]"
          >
            Reset
          </button>
        </div>

        {campaignsQuery.isError ? (
          <div className="p-6"><InlineNotice tone="error">{getApiErrorMessage(campaignsQuery.error, "Campaigns could not be loaded.")}</InlineNotice></div>
        ) : campaignsQuery.isLoading ? (
          <div className="space-y-3 p-5">{Array.from({ length: 6 }).map((_, index) => <div key={index} className="h-16 animate-pulse rounded-xl bg-[#F5F2EA]" />)}</div>
        ) : campaignsQuery.data?.items.length ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[1040px] border-collapse">
                <thead>
                  <tr className="border-b border-[#EEE8DA] bg-[#FCFBF7] text-left text-xs font-semibold text-[#6E6757]">
                    <th className="px-5 py-3.5">Campaign</th><th className="px-4 py-3.5">Status</th><th className="px-4 py-3.5">Audience</th><th className="px-4 py-3.5">Sender</th><th className="px-4 py-3.5">Schedule</th><th className="px-4 py-3.5">Progress</th><th className="px-4 py-3.5">Last Updated</th><th className="w-24 px-4 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {campaignsQuery.data.items.map((campaign) => (
                    <tr key={campaign.uuid} className="border-b border-[#F0ECE2] last:border-0 hover:bg-[#FFFDF8]">
                      <td className="px-5 py-4">
                        <Link to="/campaigns/$campaignUuid" params={{ campaignUuid: campaign.uuid }} className="text-sm font-semibold text-[#171A22] hover:text-[#8F740D]">{campaign.name}</Link>
                        <p className="mt-1 max-w-64 truncate text-xs text-[#8A826F]">{campaign.description || campaign.campaign_type.replaceAll("_", " ")}</p>
                      </td>
                      <td className="px-4 py-4"><span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${statusStyles[campaign.status] || statusStyles.draft}`}>{statusLabel(campaign.status)}</span></td>
                      <td className="px-4 py-4 text-sm text-[#4D5360]">{campaign.total_recipients.toLocaleString()}<p className="text-[11px] text-[#938B78]">recipients</p></td>
                      <td className="px-4 py-4 text-sm text-[#4D5360]">{campaign.email_account_email || "Not selected"}</td>
                      <td className="px-4 py-4 text-xs leading-5 text-[#5E6471]">{campaign.scheduled_at ? formatDate(campaign.scheduled_at) : campaign.launched_at ? `Started ${formatDate(campaign.launched_at)}` : "—"}</td>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-3"><span className="w-10 text-xs font-semibold text-[#4D5360]">{Math.round(campaign.progress_percentage)}%</span><div className="h-1.5 w-24 overflow-hidden rounded-full bg-[#ECE8DE]"><div className="h-full rounded-full bg-[#8F740D]" style={{ width: `${Math.min(100, campaign.progress_percentage)}%` }} /></div></div>
                      </td>
                      <td className="px-4 py-4 text-xs leading-5 text-[#5E6471]">{formatDate(campaign.updated_at || campaign.created_at)}</td>
                      <td className="w-24 px-4 py-4 text-right">
                        <div className="relative inline-flex items-center justify-end">
                          <button
                            type="button"
                            onClick={(event) => {
                              if (openMenu === campaign.uuid) {
                                setOpenMenu(null);
                                return;
                              }
                              const rect = event.currentTarget.getBoundingClientRect();
                              const estimatedMenuHeight = 280;
                              const openUpward =
                                window.innerHeight - rect.bottom < estimatedMenuHeight &&
                                rect.top > estimatedMenuHeight;
                              setMenuPosition({
                                ...(openUpward
                                  ? { bottom: Math.max(8, window.innerHeight - rect.top + 6) }
                                  : { top: rect.bottom + 6 }),
                                right: Math.max(8, window.innerWidth - rect.right),
                              });
                              setOpenMenu(campaign.uuid);
                            }}
                            data-action-menu-trigger="true"
                            className="rounded-lg p-2 text-[#5F6470] hover:bg-[#F2EEE4]"
                            aria-label={`Actions for ${campaign.name}`}
                          ><MoreVertical className="h-4 w-4" /></button>
                          {openMenu === campaign.uuid && actionMenu(campaign)}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <PaginationControls
              page={page}
              pageSize={pageSize}
              total={campaignsQuery.data.total}
              itemLabel="campaigns"
              onPageChange={setPage}
              onPageSizeChange={(value) => { setPageSize(value); setPage(1); }}
              isLoading={campaignsQuery.isFetching}
              className="border-t border-[#EEE8DA] px-5 py-4"
            />
          </>
        ) : (
          <div className="px-6 py-16 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#F8F0D7] text-[#8F740D]"><Send className="h-7 w-7" /></div>
            <h2 className="mt-4 text-lg font-semibold text-[#111827]">{section === "archived" ? "No archived campaigns" : "No campaigns found"}</h2>
            <p className="mt-1 text-sm text-[#756E5C]">{section === "archived" ? "Archived campaigns will appear here and can be restored." : "Create your first campaign or reset the current filters."}</p>
            {section === "active" && <Link to="/campaigns/new" className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#8F740D] px-4 py-2.5 text-sm font-semibold text-white"><Plus className="h-4 w-4" /> Create Campaign</Link>}
          </div>
        )}
      </section>
    </PageSection>

      {campaignPendingDelete && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/30 px-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-campaign-title"
        >
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-red-50">
                <AlertTriangle className="h-5 w-5 text-red-500" />
              </div>
              <div>
                <h2 id="delete-campaign-title" className="text-base font-semibold text-[#1A1C1C]">Delete campaign?</h2>
                <p className="mt-1 text-sm text-[#4C4736]">
                  <strong>{campaignPendingDelete.name}</strong> will be removed from campaign history. This cannot be undone from the UI.
                </p>
              </div>
            </div>
            <div className="mt-5 flex gap-3">
              <button
                type="button"
                onClick={() => setCampaignPendingDelete(null)}
                disabled={deleteMutation.isPending}
                className="flex-1 rounded-lg border border-[#CEC6B0]/60 py-2 text-sm font-medium text-[#1A1C1C] hover:bg-[#F4F3F3] disabled:opacity-60"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={async () => {
                  const campaign = campaignPendingDelete;
                  setFeedback(null);
                  try {
                    await deleteMutation.mutateAsync(campaign.uuid);
                    setCampaignPendingDelete(null);
                    setFeedback({ tone: "success", text: "Campaign deleted." });
                  } catch (error) {
                    setFeedback({ tone: "error", text: getApiErrorMessage(error, "The campaign action could not be completed.") });
                  }
                }}
                disabled={deleteMutation.isPending}
                className="flex-1 rounded-lg bg-red-600 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60"
              >
                {deleteMutation.isPending ? "Deleting…" : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </PageContainer>
  );
};
