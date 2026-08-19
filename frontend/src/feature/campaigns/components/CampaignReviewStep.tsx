import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  FileText,
  Mail,
  Users,
} from "lucide-react";
import { useContactLists, useEmailAccounts } from "../../../shared/api/useWorkspaceData";
import { useTemplates } from "../../templates/hooks/useTemplates";
import type { CampaignReview, SequencePreview } from "../types/campaign.types";
import type { CampaignDraft } from "./CampaignWizard";

interface CampaignReviewStepProps {
  draft: CampaignDraft;
  review: CampaignReview | null;
  sequencePreview: SequencePreview | null;
  reviewing: boolean;
}

export const CampaignReviewStep = ({ draft, review, sequencePreview, reviewing }: CampaignReviewStepProps) => {
  const listsQuery = useContactLists();
  const accountsQuery = useEmailAccounts();
  const templatesQuery = useTemplates({ limit: 100, offset: 0 });
  const contactList = listsQuery.data?.items.find((item) => item.uuid === draft.contact_list_uuid);
  const account = accountsQuery.data?.items.find((item) => item.uuid === draft.email_account_uuid);
  const template = templatesQuery.data?.items.find((item) => item.uuid === draft.template_uuid);

  const rows = [
    ["Campaign", draft.name, FileText],
    ["Audience", contactList?.name || "Not selected", Users],
    ["Sender", account?.email || "Not selected", Mail],
    [
      "Content",
      draft.campaign_type === "sequence"
        ? `${draft.sequence_steps.length} sequence step(s)`
        : draft.campaign_type === "ab_test"
          ? "A/B variants A and B"
          : template?.name || "Not selected",
      FileText,
    ],
    [
      "Schedule",
      draft.delivery_mode === "immediate"
        ? "Send immediately"
        : draft.scheduled_at_local || "Not selected",
      Clock3,
    ],
  ] as const;

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
      <section className="rounded-2xl border border-[#E8E1D0] bg-white p-5 sm:p-6">
        <h2 className="text-lg font-semibold text-[#171A22]">Final Review</h2>
        <p className="mt-1 text-sm text-[#756E5C]">
          Confirm the Phase 1 campaign configuration before launching or scheduling.
        </p>

        <div className="mt-6 divide-y divide-[#EEE8DA] rounded-2xl border border-[#E8E1D0]">
          {rows.map(([label, value, Icon]) => (
            <div key={label} className="flex items-start gap-4 p-4 sm:p-5">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#F8F0D7] text-[#8F740D]">
                <Icon className="h-4 w-4" />
              </div>
              <div>
                <p className="text-xs text-[#817966]">{label}</p>
                <p className="mt-1 text-sm font-semibold text-[#292D36]">{value}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <aside className="space-y-5">
        <section className="rounded-2xl border border-[#E8E1D0] bg-[#FFFCF3] p-5">
          <h3 className="font-semibold text-[#171A22]">Backend Readiness Check</h3>
          {reviewing ? (
            <div className="mt-5 space-y-3">
              {Array.from({ length: 3 }).map((_, index) => (
                <div key={index} className="h-10 animate-pulse rounded-xl bg-[#F0EADC]" />
              ))}
            </div>
          ) : review ? (
            <div className="mt-5 space-y-4">
              <div
                className={`flex gap-3 rounded-xl border p-4 ${
                  review.ready
                    ? "border-[#CDE7D4] bg-[#F1FBF4] text-[#25643A]"
                    : "border-[#F0C8C5] bg-[#FFF3F2] text-[#9B2C2C]"
                }`}
              >
                {review.ready ? (
                  <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0" />
                ) : (
                  <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
                )}
                <div>
                  <p className="text-sm font-semibold">
                    {review.ready ? "Campaign is ready" : "Campaign needs attention"}
                  </p>
                  <p className="mt-1 text-xs leading-5">
                    {review.ready
                      ? "The backend review passed."
                      : "Resolve the errors below before launch."}
                  </p>
                </div>
              </div>

              {review.errors.length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-[#9B2C2C]">Errors</p>
                  <ul className="mt-2 space-y-2 text-xs leading-5 text-[#7E3030]">
                    {review.errors.map((error) => (
                      <li key={error} className="rounded-lg bg-[#FFF3F2] px-3 py-2">{error}</li>
                    ))}
                  </ul>
                </div>
              )}

              {review.warnings.length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-[#8A6912]">Warnings</p>
                  <ul className="mt-2 space-y-2 text-xs leading-5 text-[#705B22]">
                    {review.warnings.map((warning) => (
                      <li key={warning} className="rounded-lg bg-[#FFF7E3] px-3 py-2">{warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              {Object.keys(review.audience).length > 0 && (
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(review.audience).map(([label, value]) => (
                    <div key={label} className="rounded-xl border border-[#E5DDCA] bg-white p-3">
                      <p className="text-[10px] uppercase tracking-wide text-[#817966]">{label.replaceAll("_", " ")}</p>
                      <p className="mt-1 text-lg font-bold text-[#292D36]">{value.toLocaleString()}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-[#817966]">
              The readiness check runs automatically when this step opens.
            </p>
          )}
        </section>

        {draft.campaign_type === "sequence" && sequencePreview && (
          <section className="rounded-2xl border border-[#E8E1D0] bg-white p-5">
            <h3 className="font-semibold text-[#171A22]">Sequence Timeline</h3>
            <p className="mt-1 text-xs text-[#817966]">
              Estimated completion: {new Date(sequencePreview.completes_at).toLocaleString()}
            </p>
            <div className="mt-4 space-y-2">
              {sequencePreview.steps.map((step) => (
                <div key={`${step.step_order}-${step.due_at}`} className="rounded-xl border border-[#EEE8DA] bg-[#FFFCF3] p-3">
                  <p className="text-xs font-semibold text-[#292D36]">
                    Step {step.step_order}: {step.step_type.replaceAll("_", " ")}
                  </p>
                  <p className="mt-1 text-[11px] text-[#817966]">{new Date(step.due_at).toLocaleString()}</p>
                </div>
              ))}
            </div>
          </section>
        )}
      </aside>
    </div>
  );
};
