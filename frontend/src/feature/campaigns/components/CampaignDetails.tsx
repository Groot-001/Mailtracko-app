import { useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";

// FIX: Type the icon entries so TypeScript knows Icon is a React component.
import type { LucideIcon } from "lucide-react";

import {
  Archive,
  ArrowLeft,
  BarChart3,
  CalendarClock,
  CheckCircle2,
  Copy,
  Edit3,
  Mail,
  PauseCircle,
  PlayCircle,
  Send,
  StopCircle,
  Users,
} from "lucide-react";

import { InlineNotice } from "../../../shared/components/InlineNotice";
import { Modal } from "../../../shared/components/Modal";
import { getApiErrorMessage } from "../../../shared/utils/apiError";
import { PageContainer, PageHeader, PageSection } from "../../../shared/components/layout";

import {
  useABTest,
  useArchiveCampaign,
  useCampaign,
  useCampaignAnalytics,
  useCampaignRecipients,
  useCancelCampaign,
  useDuplicateCampaign,
  usePauseCampaign,
  useResumeCampaign,
  useSelectABWinner,
  useSequence,
} from "../hooks/useCampaigns";

interface CampaignDetailsProps {
  campaignUuid: string;
}

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

const label = (value: string) =>
  value.charAt(0).toUpperCase() +
  value.slice(1).replaceAll("_", " ");

const statusClass = (status: string) => {
  if (["running", "ready"].includes(status)) {
    return "border-[#CDE8D4] bg-[#EAF7ED] text-[#26733D]";
  }

  if (status === "scheduled") {
    return "border-[#F0D9A6] bg-[#FFF4DB] text-[#976312]";
  }

  if (["failed", "cancelled"].includes(status)) {
    return "border-[#F4C6C2] bg-[#FFF0EF] text-[#B42318]";
  }

  if (status === "completed") {
    return "border-[#C8D7F5] bg-[#EDF3FF] text-[#315EA8]";
  }

  return "border-[#DEDEDE] bg-[#F3F3F3] text-[#5F6470]";
};

export const CampaignDetails = ({
  campaignUuid,
}: CampaignDetailsProps) => {
  const navigate = useNavigate();

  const campaignQuery = useCampaign(campaignUuid);
  const recipientsQuery = useCampaignRecipients(campaignUuid);
  const analyticsQuery = useCampaignAnalytics(campaignUuid);

  const sequenceQuery = useSequence(
    campaignUuid,
    campaignQuery.data?.campaign_type === "sequence",
  );

  const abTestQuery = useABTest(
    campaignUuid,
    campaignQuery.data?.campaign_type === "ab_test",
  );

  const pauseMutation = usePauseCampaign();
  const resumeMutation = useResumeCampaign();
  const cancelMutation = useCancelCampaign();
  const archiveMutation = useArchiveCampaign();
  const duplicateMutation = useDuplicateCampaign();
  const selectWinnerMutation = useSelectABWinner();

  const [confirmAction, setConfirmAction] = useState<
    "cancel" | "archive" | null
  >(null);

  const [feedback, setFeedback] = useState<{
    tone: "success" | "error";
    text: string;
  } | null>(null);

  if (campaignQuery.isLoading) {
    return (
      <PageContainer>
        <div className="h-[720px] animate-pulse rounded-2xl bg-[#F0ECE2]" />
      </PageContainer>
    );
  }

  if (campaignQuery.isError || !campaignQuery.data) {
    return (
      <PageContainer>
        <InlineNotice tone="error">
          {getApiErrorMessage(
            campaignQuery.error,
            "Campaign could not be loaded.",
          )}
        </InlineNotice>
      </PageContainer>
    );
  }

  const campaign = campaignQuery.data;
  const analytics = analyticsQuery.data;

  const remaining = Math.max(
    0,
    campaign.total_recipients -
      campaign.sent_count -
      campaign.failed_count -
      campaign.skipped_count,
  );

  const runAction = async (
    action: () => Promise<unknown>,
    success: string,
  ) => {
    setFeedback(null);

    try {
      await action();

      setFeedback({
        tone: "success",
        text: success,
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        text: getApiErrorMessage(
          error,
          "Campaign action could not be completed.",
        ),
      });
    }
  };

  const confirmDestructiveAction = async () => {
    if (!confirmAction) return;

    const action = confirmAction;

    setConfirmAction(null);

    if (action === "cancel") {
      await runAction(
        () => cancelMutation.mutateAsync(campaignUuid),
        "Campaign cancelled.",
      );
    } else {
      await runAction(
        () => archiveMutation.mutateAsync(campaignUuid),
        "Campaign archived.",
      );
    }
  };

  return (
    <PageContainer>
      <PageHeader
        title={campaign.name}
        description={campaign.description || "Organization email campaign."}
        breadcrumbs={
          <Link
            to="/campaigns"
            className="inline-flex items-center gap-2 text-sm font-medium text-[#7A6208] hover:underline"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Campaigns
          </Link>
        }
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`rounded-full border px-3 py-1 text-xs font-semibold ${statusClass(
                campaign.status,
              )}`}
            >
              {label(campaign.status)}
            </span>

            <span className="rounded-full border border-[#D8C990] bg-[#F8F0D7] px-3 py-1 text-xs font-semibold text-[#735E10]">
              {label(campaign.campaign_type)}
            </span>

            {campaign.status === "draft" && (
              <Link
                to="/campaigns/$campaignUuid/edit"
                params={{ campaignUuid }}
                className="inline-flex items-center gap-2 rounded-xl bg-[#8F740D] px-4 py-2.5 text-sm font-semibold text-white"
              >
                <Edit3 className="h-4 w-4" />
                Edit Campaign
              </Link>
            )}

            {campaign.status === "running" && (
              <button
                type="button"
                onClick={() =>
                  runAction(
                    () => pauseMutation.mutateAsync(campaignUuid),
                    "Campaign paused.",
                  )
                }
                className="inline-flex items-center gap-2 rounded-xl border border-[#D9CFB8] bg-white px-4 py-2.5 text-sm font-semibold text-[#5E5230]"
              >
                <PauseCircle className="h-4 w-4" />
                Pause
              </button>
            )}

            {campaign.status === "paused" && (
              <button
                type="button"
                onClick={() =>
                  runAction(
                    () => resumeMutation.mutateAsync(campaignUuid),
                    "Campaign resumed.",
                  )
                }
                className="inline-flex items-center gap-2 rounded-xl border border-[#D9CFB8] bg-white px-4 py-2.5 text-sm font-semibold text-[#5E5230]"
              >
                <PlayCircle className="h-4 w-4" />
                Resume
              </button>
            )}

            <button
              type="button"
              onClick={async () => {
                try {
                  const duplicated =
                    await duplicateMutation.mutateAsync(campaignUuid);

                  navigate({
                    to: "/campaigns/$campaignUuid/edit",
                    params: {
                      campaignUuid: (
                        duplicated as {
                          uuid: string;
                        }
                      ).uuid,
                    },
                  });
                } catch (error) {
                  setFeedback({
                    tone: "error",
                    text: getApiErrorMessage(
                      error,
                      "Campaign could not be duplicated.",
                    ),
                  });
                }
              }}
              className="inline-flex items-center gap-2 rounded-xl border border-[#D9CFB8] bg-white px-4 py-2.5 text-sm font-semibold text-[#5E5230]"
            >
              <Copy className="h-4 w-4" />
              Duplicate
            </button>
          </div>
        }
      />

      {feedback && (
        <div className="mt-5">
          <InlineNotice tone={feedback.tone}>
            {feedback.text}
          </InlineNotice>
        </div>
      )}

      <PageSection>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {(
          [
            [
              "Recipients",
              campaign.total_recipients,
              Users,
            ],
            [
              "Sent",
              campaign.sent_count,
              Send,
            ],
            [
              "Failed",
              campaign.failed_count,
              StopCircle,
            ],
            [
              "Skipped",
              campaign.skipped_count,
              CheckCircle2,
            ],
            [
              "Remaining",
              remaining,
              BarChart3,
            ],
          ] satisfies ReadonlyArray<
            readonly [string, number, LucideIcon]
          >
        ).map(([title, value, Icon]) => (
          <div
            key={title}
            className="rounded-2xl border border-[#E8E1D0] bg-white p-5 shadow-[0_8px_24px_rgba(66,54,16,0.04)]"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[#696253]">
                  {title}
                </p>

                <p className="mt-1 text-2xl font-bold text-[#111827]">
                  {value.toLocaleString()}
                </p>
              </div>

              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#F8F0D7] text-[#8F740D]">
                <Icon className="h-5 w-5" />
              </div>
            </div>
          </div>
        ))}
        </div>
      </PageSection>

      <PageSection>
        <div className="grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
        <section className="rounded-2xl border border-[#E8E1D0] bg-white p-6 shadow-[0_8px_24px_rgba(66,54,16,0.04)]">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-[#111827]">Campaign performance</h2>
              <p className="mt-1 text-sm text-[#756E5C]">Latest delivery and engagement totals.</p>
            </div>
            <BarChart3 className="h-5 w-5 text-[#8F740D]" />
          </div>

          {analyticsQuery.isLoading ? (
            <div className="mt-5 h-36 animate-pulse rounded-xl bg-[#F3EFE5]" />
          ) : analyticsQuery.isError || !analytics ? (
            <div className="mt-5">
              <InlineNotice tone="error">Campaign analytics could not be loaded.</InlineNotice>
            </div>
          ) : (
            <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {[
                ["Delivered", analytics.delivered, `${analytics.delivery_rate.toFixed(1)}%`],
                ["Opened", analytics.opened, `${analytics.open_rate.toFixed(1)}%`],
                ["Clicked", analytics.clicked, `${analytics.click_rate.toFixed(1)}%`],
                ["Replied", analytics.replied, `${analytics.reply_rate.toFixed(1)}%`],
              ].map(([title, value, rate]) => (
                <div key={String(title)} className="rounded-xl border border-[#EEE7D7] bg-[#FFFCF5] p-4">
                  <p className="text-xs font-medium uppercase tracking-wide text-[#7B7462]">{title}</p>
                  <p className="mt-2 text-2xl font-bold text-[#111827]">{Number(value).toLocaleString()}</p>
                  <p className="mt-1 text-sm font-semibold text-[#8F740D]">{rate}</p>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="rounded-2xl border border-[#E8E1D0] bg-white p-6 shadow-[0_8px_24px_rgba(66,54,16,0.04)]">
          <h2 className="text-lg font-semibold text-[#111827]">Campaign details</h2>
          <dl className="mt-5 space-y-4 text-sm">
            {[
              ["Sender", campaign.email_account_email || "Not selected"],
              ["Template", campaign.template_name || "Not selected"],
              ["Audience", campaign.contact_list_name || "Not selected"],
              ["Scheduled", formatDate(campaign.scheduled_at)],
              ["Timezone", campaign.timezone || "—"],
              ["Created", formatDate(campaign.created_at)],
            ].map(([term, value]) => (
              <div key={term} className="flex items-start justify-between gap-4 border-b border-[#F0EBDF] pb-3 last:border-0 last:pb-0">
                <dt className="text-[#756E5C]">{term}</dt>
                <dd className="text-right font-medium text-[#2F2A1F]">{value}</dd>
              </div>
            ))}
          </dl>
        </section>
      </div>

      {campaign.campaign_type === "sequence" && (
        <section className="mt-6 rounded-2xl border border-[#E8E1D0] bg-white p-6">
          <div className="flex items-center gap-2">
            <CalendarClock className="h-5 w-5 text-[#8F740D]" />
            <h2 className="text-lg font-semibold text-[#111827]">Sequence</h2>
          </div>
          {sequenceQuery.isLoading ? (
            <div className="mt-4 h-24 animate-pulse rounded-xl bg-[#F3EFE5]" />
          ) : sequenceQuery.isError || !sequenceQuery.data ? (
            <div className="mt-4"><InlineNotice tone="error">Sequence configuration could not be loaded.</InlineNotice></div>
          ) : (
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-xl bg-[#FFFCF5] p-4"><p className="text-sm text-[#756E5C]">Status</p><p className="mt-1 font-semibold text-[#111827]">{label(sequenceQuery.data.status)}</p></div>
              <div className="rounded-xl bg-[#FFFCF5] p-4"><p className="text-sm text-[#756E5C]">Steps</p><p className="mt-1 font-semibold text-[#111827]">{sequenceQuery.data.total_steps}</p></div>
              <div className="rounded-xl bg-[#FFFCF5] p-4"><p className="text-sm text-[#756E5C]">Stop on reply</p><p className="mt-1 font-semibold text-[#111827]">{sequenceQuery.data.stop_on_reply ? "Yes" : "No"}</p></div>
              <div className="rounded-xl bg-[#FFFCF5] p-4"><p className="text-sm text-[#756E5C]">Stop on click</p><p className="mt-1 font-semibold text-[#111827]">{sequenceQuery.data.stop_on_click ? "Yes" : "No"}</p></div>
            </div>
          )}
        </section>
      )}

      {campaign.campaign_type === "ab_test" && (
        <section className="mt-6 rounded-2xl border border-[#E8E1D0] bg-white p-6">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2"><Mail className="h-5 w-5 text-[#8F740D]" /><h2 className="text-lg font-semibold text-[#111827]">A/B test</h2></div>
            {abTestQuery.data && !abTestQuery.data.winner_variant_uuid && (
              <button type="button" onClick={() => runAction(() => selectWinnerMutation.mutateAsync({ uuid: campaignUuid }), "A/B winner selected." )} className="rounded-xl bg-[#8F740D] px-4 py-2 text-sm font-semibold text-white">Select winner</button>
            )}
          </div>
          {abTestQuery.isLoading ? (
            <div className="mt-4 h-24 animate-pulse rounded-xl bg-[#F3EFE5]" />
          ) : abTestQuery.isError || !abTestQuery.data ? (
            <div className="mt-4"><InlineNotice tone="error">A/B test configuration could not be loaded.</InlineNotice></div>
          ) : (
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {abTestQuery.data.variants.map((variant) => (
                <div key={variant.uuid} className="rounded-xl border border-[#EEE7D7] bg-[#FFFCF5] p-4">
                  <p className="font-semibold text-[#111827]">Variant {variant.variant_type.toUpperCase()}: {variant.name}</p>
                  <p className="mt-2 text-sm text-[#756E5C]">Allocation {variant.allocation_percentage}% · Sent {variant.sent_count} · Opened {variant.opened_count} · Clicked {variant.clicked_count}</p>
                </div>
              ))}
            </div>
          )}
        </section>
      )}
      </PageSection>

      <PageSection>
        <section className="rounded-2xl border border-[#E8E1D0] bg-white p-6">
        <div className="flex items-center justify-between gap-3">
          <div><h2 className="text-lg font-semibold text-[#111827]">Recipients</h2><p className="mt-1 text-sm text-[#756E5C]">Most recent campaign recipients and delivery state.</p></div>
          <Users className="h-5 w-5 text-[#8F740D]" />
        </div>
        {recipientsQuery.isLoading ? (
          <div className="mt-4 h-32 animate-pulse rounded-xl bg-[#F3EFE5]" />
        ) : recipientsQuery.isError ? (
          <div className="mt-4"><InlineNotice tone="error">Recipients could not be loaded.</InlineNotice></div>
        ) : recipientsQuery.data?.items.length ? (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead><tr className="border-b border-[#E8E1D0] text-[#756E5C]"><th className="px-3 py-3 font-medium">Email</th><th className="px-3 py-3 font-medium">Status</th><th className="px-3 py-3 font-medium">Attempt</th><th className="px-3 py-3 font-medium">Sent</th></tr></thead>
              <tbody>{recipientsQuery.data.items.slice(0, 10).map((recipient) => (
                <tr key={recipient.uuid} className="border-b border-[#F1ECE1] last:border-0"><td className="px-3 py-3 font-medium text-[#2F2A1F]">{recipient.email}</td><td className="px-3 py-3 text-[#756E5C]">{label(recipient.status)}</td><td className="px-3 py-3 text-[#756E5C]">{recipient.attempt_count}</td><td className="px-3 py-3 text-[#756E5C]">{formatDate(recipient.sent_at)}</td></tr>
              ))}</tbody>
            </table>
          </div>
        ) : (
          <p className="mt-4 rounded-xl bg-[#FFFCF5] p-4 text-sm text-[#756E5C]">No recipients have been generated for this campaign yet.</p>
        )}
        </section>
      </PageSection>

      <PageSection>
        <div className="flex flex-wrap justify-end gap-2">
        {!['cancelled', 'completed', 'archived'].includes(campaign.status) && (
          <button type="button" onClick={() => setConfirmAction('cancel')} className="inline-flex items-center gap-2 rounded-xl border border-[#E7BDB9] bg-white px-4 py-2.5 text-sm font-semibold text-[#A63830]"><StopCircle className="h-4 w-4" />Cancel campaign</button>
        )}
        {!['archived', 'running', 'launching'].includes(campaign.status) && (
          <button type="button" onClick={() => setConfirmAction('archive')} className="inline-flex items-center gap-2 rounded-xl border border-[#D9CFB8] bg-white px-4 py-2.5 text-sm font-semibold text-[#5E5230]"><Archive className="h-4 w-4" />Archive</button>
        )}
        </div>
      </PageSection>

      <Modal open={confirmAction !== null} title={confirmAction === 'cancel' ? 'Cancel campaign?' : 'Archive campaign?'} description={confirmAction === 'cancel' ? 'Pending sends will be stopped. This action cannot be undone.' : 'The campaign will be kept with Archived status so its history and analytics remain available.'} onClose={() => setConfirmAction(null)}>
        <div className="flex justify-end gap-2">
          <button type="button" onClick={() => setConfirmAction(null)} className="rounded-xl border border-[#D9CFB8] px-4 py-2 text-sm font-semibold text-[#5E5230]">Keep campaign</button>
          <button type="button" onClick={confirmDestructiveAction} className="rounded-xl bg-[#A63830] px-4 py-2 text-sm font-semibold text-white">Confirm</button>
        </div>
      </Modal>
    </PageContainer>
  );
};
