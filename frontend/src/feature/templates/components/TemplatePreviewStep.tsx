import { useEffect, useState } from "react";
import { Monitor, Send, Smartphone } from "lucide-react";
import { useEmailAccounts } from "../../../shared/api/useWorkspaceData";
import { EmailPreviewFrame } from "../../../shared/components/EmailPreviewFrame";
import { AppSelect } from "../../../shared/components/AppSelect";
import { InlineNotice } from "../../../shared/components/InlineNotice";
import { getApiErrorMessage } from "../../../shared/utils/apiError";
import { usePreviewTemplate, useSendTemplateTestEmail } from "../hooks/useTemplates";
import type { TemplatePreviewResult } from "../types/template.types";
import type { TemplateDraft } from "./TemplateWizard";

interface TemplatePreviewStepProps {
  draft: TemplateDraft;
}

const previewVariables = {
  first_name: "Alex",
  last_name: "Morgan",
  email: "alex.morgan@example.com",
  company: "MailTracko",
  unsubscribe_link: "#unsubscribe-preview",
};

export const TemplatePreviewStep = ({ draft }: TemplatePreviewStepProps) => {
  const [device, setDevice] = useState<"desktop" | "mobile">("desktop");
  const [preview, setPreview] = useState<TemplatePreviewResult | null>(null);
  const [recipient, setRecipient] = useState("");
  const [accountUuid, setAccountUuid] = useState("");
  const [feedback, setFeedback] = useState<{ tone: "success" | "error"; text: string } | null>(null);
  const previewMutation = usePreviewTemplate();
  const testMutation = useSendTemplateTestEmail();
  const accountsQuery = useEmailAccounts();
  const defaultAccountUuid = accountsQuery.data?.items[0]?.uuid ?? "";
  const selectedAccountUuid = accountUuid || defaultAccountUuid;

  useEffect(() => {
    let active = true;
    previewMutation
      .mutateAsync({
        subject: draft.subject,
        body_html: draft.body_html,
        preheader: draft.preheader || null,
        variables: previewVariables,
      })
      .then((result) => {
        if (active) setPreview(result);
      })
      .catch((error: unknown) => {
        if (active) {
          setFeedback({ tone: "error", text: getApiErrorMessage(error, "Template preview could not be generated.") });
        }
      });
    return () => {
      active = false;
    };
    // The preview is intentionally refreshed only when this step is opened.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const sendTest = async () => {
    setFeedback(null);
    if (!selectedAccountUuid || !recipient.trim()) {
      setFeedback({ tone: "error", text: "Select a sender account and enter a test recipient email." });
      return;
    }
    try {
      await testMutation.mutateAsync({
        email_account_uuid: selectedAccountUuid,
        recipient_email: recipient.trim(),
        subject: draft.subject,
        body_html: draft.body_html,
        preheader: draft.preheader || null,
        from_name: draft.from_name || null,
        variables: { ...previewVariables, email: recipient.trim() },
      });
      setFeedback({ tone: "success", text: `Test email sent to ${recipient.trim()}.` });
    } catch (error) {
      setFeedback({ tone: "error", text: getApiErrorMessage(error, "The test email could not be sent.") });
    }
  };

  const renderedBody = preview?.body_html || draft.body_html;

  return (
    <div className="grid min-w-0 gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(280px,360px)]">
      <section className="min-w-0 overflow-hidden rounded-2xl border border-[#E8E1D0] bg-white p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#EEE8DA] pb-4">
          <div className="flex rounded-xl border border-[#E0D8C7] bg-[#FCFBF7] p-1">
            <button
              type="button"
              onClick={() => setDevice("desktop")}
              className={`flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-semibold ${
                device === "desktop" ? "bg-white text-[#7A6208] shadow-sm" : "text-[#6C6658]"
              }`}
            >
              <Monitor className="h-4 w-4" /> Desktop
            </button>
            <button
              type="button"
              onClick={() => setDevice("mobile")}
              className={`flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-semibold ${
                device === "mobile" ? "bg-white text-[#7A6208] shadow-sm" : "text-[#6C6658]"
              }`}
            >
              <Smartphone className="h-4 w-4" /> Mobile
            </button>
          </div>
          <p className="min-w-0 max-w-full break-words text-xs text-[#88806D]">Subject: {preview?.subject || draft.subject}</p>
        </div>

        <div className="flex min-h-[570px] min-w-0 justify-center overflow-x-auto bg-[#F7F4ED] p-4 sm:p-8">
          <article
            className={`overflow-hidden rounded-xl border border-[#E8E1D0] bg-white shadow-lg transition-all ${
              device === "mobile" ? "w-full max-w-[360px]" : "w-full max-w-[760px]"
            }`}
          >
            <div className="border-b border-[#EEE8DA] px-6 py-5">
              <p className="text-lg font-bold text-[#171A22]">MailTracko</p>
              {draft.preheader && <p className="mt-1 text-xs text-[#8B8371]">{draft.preheader}</p>}
            </div>
            <EmailPreviewFrame
              html={renderedBody}
              title="Template email preview"
              className="min-h-[430px]"
            />
          </article>
        </div>
      </section>

      <aside className="min-w-0 space-y-5">
        {feedback && <InlineNotice tone={feedback.tone}>{feedback.text}</InlineNotice>}
        <section className="min-w-0 overflow-hidden rounded-2xl border border-[#E8E1D0] bg-white p-5">
          <h3 className="font-semibold text-[#171A22]">Send Test Email</h3>
          <p className="mt-1 text-xs leading-5 text-[#817966]">Uses a connected organization sender account.</p>
          <label className="mt-5 block space-y-2">
            <span className="text-xs font-semibold text-[#403A2E]">Sender Account</span>
            <AppSelect value={selectedAccountUuid} onValueChange={setAccountUuid} ariaLabel="Sender account" searchable options={[{ value: "", label: "Select sender" }, ...(accountsQuery.data?.items.map((account) => ({ value: account.uuid, label: `${account.email} (${account.provider})` })) ?? [])]} />
          </label>
          <label className="mt-4 block space-y-2">
            <span className="text-xs font-semibold text-[#403A2E]">Recipient Email</span>
            <input
              type="email"
              value={recipient}
              onChange={(event) => setRecipient(event.target.value)}
              placeholder="recipient@your-domain.tld"
              className="h-11 w-full min-w-0 rounded-xl border border-[#DED7C7] px-3.5 text-sm outline-none focus:border-[#A88916] focus:ring-1 focus:ring-[#E9DFAE]/60"
            />
          </label>
          <button
            type="button"
            onClick={sendTest}
            disabled={testMutation.isPending}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-[#8F740D] px-4 py-3 text-sm font-semibold text-white disabled:opacity-55"
          >
            <Send className="h-4 w-4" /> {testMutation.isPending ? "Sending..." : "Send Test"}
          </button>
        </section>

        <section className="min-w-0 overflow-hidden rounded-2xl border border-[#E8E1D0] bg-white p-5">
          <h3 className="font-semibold text-[#171A22]">Variable Check</h3>
          <div className="mt-4 space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-[#756E5C]">Variables found</span>
              <strong>{preview?.variables.length ?? 0}</strong>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[#756E5C]">Unresolved</span>
              <strong className={preview?.unresolved_variables.length ? "text-[#B42318]" : "text-[#26733D]"}>
                {preview?.unresolved_variables.length ?? 0}
              </strong>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[#756E5C]">Fallbacks used</span>
              <strong>{preview?.fallback_variables.length ?? 0}</strong>
            </div>
          </div>
        </section>
      </aside>
    </div>
  );
};
