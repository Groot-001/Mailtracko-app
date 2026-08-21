import { useMemo, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { AlertCircle, ArrowLeft, CheckCircle2, Loader2, Send, Users } from "lucide-react";

import { useInviteMember } from "../../../../feature/organization/hooks/useInvitations";
import type { RoleCode } from "../../../../feature/organization/types/organization.types";
import { AppSelect } from "../../../../shared/components/AppSelect";
import { PageContainer, PageHeader, PageSection } from "../../../../shared/components/layout";
import { getApiErrorMessage } from "../../../../shared/utils/apiError";

export const Route = createFileRoute("/_protected/organization/team/invite")({
  component: InviteWizardPage,
});

type InviteRole = Extract<RoleCode, "admin" | "member">;
type Step = "details" | "review" | "complete";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MAX_INVITES_PER_BATCH = 20;

function parseEmails(value: string) {
  const candidates = value
    .split(/[\n,;]+/)
    .map((email) => email.trim().toLowerCase())
    .filter(Boolean);
  return [...new Set(candidates)];
}

function InviteWizardPage() {
  const inviteMutation = useInviteMember();
  const [step, setStep] = useState<Step>("details");
  const [emailsText, setEmailsText] = useState("");
  const [roleCode, setRoleCode] = useState<InviteRole>("member");
  const [formError, setFormError] = useState<string | null>(null);
  const [sendResults, setSendResults] = useState<Array<{ email: string; ok: boolean; error?: string }>>([]);
  const [isSendingBatch, setIsSendingBatch] = useState(false);

  const emails = useMemo(() => parseEmails(emailsText), [emailsText]);
  const invalidEmails = emails.filter((email) => !EMAIL_PATTERN.test(email));

  const validateDetails = () => {
    if (!emails.length) return "Enter at least one email address.";
    if (emails.length > MAX_INVITES_PER_BATCH) {
      return `You can invite a maximum of ${MAX_INVITES_PER_BATCH} people at once.`;
    }
    if (invalidEmails.length) return `Invalid email address: ${invalidEmails[0]}`;
    return null;
  };

  const continueToReview = () => {
    const error = validateDetails();
    setFormError(error);
    if (!error) setStep("review");
  };

  const sendInvitations = async () => {
    const error = validateDetails();
    if (error) {
      setFormError(error);
      setStep("details");
      return;
    }

    setFormError(null);
    setIsSendingBatch(true);
    const results: Array<{ email: string; ok: boolean; error?: string }> = [];
    for (const email of emails) {
      try {
        await inviteMutation.mutateAsync({ email, role_code: roleCode });
        results.push({ email, ok: true });
      } catch (inviteError) {
        results.push({
          email,
          ok: false,
          error: getApiErrorMessage(inviteError, "Invitation could not be sent."),
        });
      }
    }
    setSendResults(results);
    setIsSendingBatch(false);
    setStep("complete");
  };

  const startAnother = () => {
    setEmailsText("");
    setRoleCode("member");
    setFormError(null);
    setSendResults([]);
    setStep("details");
  };

  const succeeded = sendResults.filter((result) => result.ok).length;
  const failed = sendResults.length - succeeded;

  return (
    <PageContainer nested>
      <PageHeader
        title="Invite team members"
        description="Invite people using the roles enforced by the MailTracko backend."
        breadcrumbs={
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[#8F740D]">
            Organization Team
          </p>
        }
        actions={
          <Link
            to="/organization/team"
            className="inline-flex items-center gap-2 rounded-xl border border-[#CEC6B0]/60 bg-white px-4 py-2 text-xs font-bold text-[#4C4736] hover:bg-[#F8F7F2]"
          >
            <ArrowLeft className="h-4 w-4" /> Back to team
          </Link>
        }
      />
      <PageSection>

      <div className="grid grid-cols-3 gap-2" aria-label="Invitation progress">
        {(["details", "review", "complete"] as const).map((item, index) => {
          const activeIndex = step === "details" ? 0 : step === "review" ? 1 : 2;
          const isActive = index <= activeIndex;
          return <div key={item} className={`h-1.5 rounded-full ${isActive ? "bg-[#8F740D]" : "bg-[#E8E1D0]"}`} />;
        })}
      </div>

      {step === "details" && (
        <section className="rounded-2xl border border-[#CEC6B0]/50 bg-white p-6 sm:p-7">
          <div className="flex items-start gap-3">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#F7F2E2]"><Users className="h-5 w-5 text-[#8F740D]" /></div>
            <div><h2 className="font-bold text-[#1A1C1C]">Invitation details</h2><p className="mt-1 text-xs text-[#756F60]">The email field starts blank. Add up to {MAX_INVITES_PER_BATCH} addresses, separated by commas or new lines.</p></div>
          </div>

          <div className="mt-6 space-y-5">
            <label className="block">
              <span className="text-xs font-bold text-[#4C4736]">Email addresses</span>
              <textarea
                rows={6}
                value={emailsText}
                onChange={(event) => { setEmailsText(event.target.value); setFormError(null); }}
                autoComplete="off"
                placeholder="name@company.com"
                className="mt-1.5 w-full resize-y rounded-xl border border-[#CEC6B0]/60 px-3 py-2.5 text-sm outline-none focus:border-[#8F740D] focus:ring-2 focus:ring-[#F1D442]/40"
              />
              <span className="mt-1 block text-[11px] text-[#756F60]">{emails.length} unique address{emails.length === 1 ? "" : "es"}</span>
            </label>

            <label className="block">
              <span className="text-xs font-bold text-[#4C4736]">Role</span>
              <AppSelect className="mt-1.5" value={roleCode} onValueChange={(value) => setRoleCode(value as InviteRole)} ariaLabel="Invitation role" options={[{ value: "member", label: "Member" }, { value: "admin", label: "Admin" }]} />
              <span className="mt-1 block text-[11px] text-[#756F60]">Owner access cannot be granted through an invitation.</span>
            </label>
          </div>

          {formError && <p className="mt-5 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-xs font-semibold text-red-700"><AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />{formError}</p>}

          <div className="mt-6 flex justify-end"><button type="button" onClick={continueToReview} className="rounded-xl bg-[#8F740D] px-5 py-2.5 text-sm font-bold text-white hover:bg-[#6A5B00]">Review invitations</button></div>
        </section>
      )}

      {step === "review" && (
        <section className="rounded-2xl border border-[#CEC6B0]/50 bg-white p-6 sm:p-7">
          <h2 className="font-bold text-[#1A1C1C]">Review before sending</h2>
          <p className="mt-1 text-xs text-[#756F60]">Each person will receive a real invitation email through the configured transactional email service.</p>
          <div className="mt-5 overflow-hidden rounded-xl border border-[#E8E1D0]">
            {emails.map((email) => <div key={email} className="flex items-center justify-between gap-4 border-b border-[#F1EDE3] px-4 py-3 last:border-0"><span className="min-w-0 truncate text-sm font-medium text-[#1A1C1C]">{email}</span><span className="rounded-full bg-[#F7F2E2] px-2.5 py-1 text-[11px] font-bold capitalize text-[#6A5B00]">{roleCode}</span></div>)}
          </div>
          <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            <button type="button" disabled={isSendingBatch} onClick={() => setStep("details")} className="rounded-xl border border-[#CEC6B0]/60 px-5 py-2.5 text-sm font-semibold disabled:opacity-50">Back</button>
            <button type="button" disabled={isSendingBatch} onClick={() => void sendInvitations()} className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#8F740D] px-5 py-2.5 text-sm font-bold text-white disabled:opacity-60">
              {isSendingBatch ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />} {isSendingBatch ? "Sending..." : "Send invitations"}
            </button>
          </div>
        </section>
      )}

      {step === "complete" && (
        <section className="rounded-2xl border border-[#CEC6B0]/50 bg-white p-6 sm:p-7">
          <div className="flex items-start gap-3"><div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-emerald-50"><CheckCircle2 className="h-5 w-5 text-emerald-700" /></div><div><h2 className="font-bold text-[#1A1C1C]">Invitation run complete</h2><p className="mt-1 text-xs text-[#756F60]">{succeeded} sent successfully{failed ? ` · ${failed} failed` : ""}.</p></div></div>
          <div className="mt-5 overflow-hidden rounded-xl border border-[#E8E1D0]">{sendResults.map((result) => <div key={result.email} className="border-b border-[#F1EDE3] px-4 py-3 last:border-0"><div className="flex items-center gap-2 text-sm font-medium"><span className={result.ok ? "text-emerald-700" : "text-red-700"}>{result.ok ? "✓" : "!"}</span><span>{result.email}</span></div>{result.error && <p className="mt-1 pl-5 text-xs text-red-700">{result.error}</p>}</div>)}</div>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-end"><button type="button" onClick={startAnother} className="rounded-xl border border-[#CEC6B0]/60 px-5 py-2.5 text-sm font-semibold">Invite more people</button><Link to="/organization/team" className="rounded-xl bg-[#8F740D] px-5 py-2.5 text-center text-sm font-bold text-white">Return to team</Link></div>
        </section>
      )}
      </PageSection>
    </PageContainer>
  );
}
