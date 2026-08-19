import { CheckCircle2, FileText, Tag, UserRound } from "lucide-react";
import { EmailPreviewFrame } from "../../../shared/components/EmailPreviewFrame";
import type { TemplateDraft } from "./TemplateWizard";

interface TemplateReviewStepProps {
  draft: TemplateDraft;
  categoryName?: string;
}

export const TemplateReviewStep = ({ draft, categoryName }: TemplateReviewStepProps) => (
  <div className="grid min-w-0 gap-6 xl:grid-cols-[minmax(280px,420px)_minmax(0,1fr)]">
    <div className="min-w-0 space-y-5">
      <section className="min-w-0 overflow-hidden rounded-2xl border border-[#E8E1D0] bg-white p-5">
        <h2 className="text-lg font-semibold text-[#171A22]">Template Details</h2>
        <dl className="mt-5 divide-y divide-[#EEE8DA] text-sm">
          {[
            ["Template Name", draft.name, FileText],
            ["Category", categoryName || "Uncategorized", Tag],
            ["From", draft.from_name || draft.from_email || "Campaign sender", UserRound],
          ].map(([label, value, Icon]) => (
            <div key={String(label)} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#F8F0D7] text-[#8F740D]">
                <Icon className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <dt className="text-xs text-[#817966]">{label as string}</dt>
                <dd className="mt-1 break-words font-medium text-[#292D36]">{value as string}</dd>
              </div>
            </div>
          ))}
        </dl>
      </section>

      <section className="min-w-0 overflow-hidden rounded-2xl border border-[#D4E8D9] bg-[#F3FBF5] p-5">
        <div className="flex gap-3">
          <CheckCircle2 className="mt-0.5 h-5 w-5 text-[#2D8A4A]" />
          <div>
            <p className="font-semibold text-[#25643A]">Ready to save</p>
            <p className="mt-1 text-sm leading-5 text-[#487456]">
              The required name, subject, and email body are complete. Publish only when the template is ready for campaigns.
            </p>
          </div>
        </div>
      </section>
    </div>

    <section className="min-w-0 overflow-hidden rounded-2xl border border-[#E8E1D0] bg-white p-5">
      <div className="flex items-center justify-between border-b border-[#EEE8DA] pb-4">
        <h3 className="font-semibold text-[#171A22]">Email Preview</h3>
        <span className="rounded-lg bg-[#F7F0DA] px-2.5 py-1 text-xs text-[#735E10]">Desktop</span>
      </div>
      <div className="mt-5 min-w-0 overflow-hidden rounded-xl border border-[#E8E1D0] bg-[#FCFBF7] p-5">
        <p className="text-lg font-bold text-[#171A22]">MailTracko</p>
        <p className="mt-4 break-words text-base font-semibold text-[#252A34]">{draft.subject}</p>
        <EmailPreviewFrame
          html={draft.body_html}
          title="Final template preview"
          className="mt-4 min-h-[420px] rounded-lg"
        />
      </div>
    </section>
  </div>
);
