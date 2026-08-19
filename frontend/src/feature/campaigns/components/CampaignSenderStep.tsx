import { CheckCircle2, Mail, ShieldCheck } from "lucide-react";
import { useEmailAccounts } from "../../../shared/api/useWorkspaceData";
import { InlineNotice } from "../../../shared/components/InlineNotice";
import { getApiErrorMessage } from "../../../shared/utils/apiError";
import type { CampaignDraft } from "./CampaignWizard";

interface CampaignSenderStepProps {
  draft: CampaignDraft;
  updateDraft: (updates: Partial<CampaignDraft>) => void;
}

const statusTone = (status: string) =>
  status === "connected" || status === "active" || status === "verified"
    ? "bg-[#EAF7ED] text-[#26733D]"
    : "bg-[#FFF4DB] text-[#976312]";

export const CampaignSenderStep = ({ draft, updateDraft }: CampaignSenderStepProps) => {
  const accountsQuery = useEmailAccounts();
  const selectedAccount = accountsQuery.data?.items.find(
    (account) => account.uuid === draft.email_account_uuid,
  );

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
      <section className="rounded-2xl border border-[#E8E1D0] bg-white p-5 sm:p-6">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#F8F0D7] text-[#8F740D]">
            <Mail className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-[#171A22]">Select Sender</h2>
            <p className="mt-1 text-sm text-[#756E5C]">
              Phase 1 uses one connected email account for the campaign.
            </p>
          </div>
        </div>

        {accountsQuery.isError ? (
          <div className="mt-6">
            <InlineNotice tone="error">
              {getApiErrorMessage(accountsQuery.error, "Sender accounts could not be loaded.")}
            </InlineNotice>
          </div>
        ) : accountsQuery.isLoading ? (
          <div className="mt-6 space-y-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <div key={index} className="h-24 animate-pulse rounded-xl bg-[#F3F0E8]" />
            ))}
          </div>
        ) : accountsQuery.data?.items.length ? (
          <div className="mt-6 space-y-3">
            {accountsQuery.data.items.map((account) => {
              const selected = account.uuid === draft.email_account_uuid;
              const remaining = Math.max(0, account.sending_limit - account.daily_sent_count);
              return (
                <button
                  key={account.uuid}
                  type="button"
                  onClick={() => updateDraft({ email_account_uuid: account.uuid })}
                  className={`w-full rounded-xl border p-4 text-left transition ${
                    selected
                      ? "border-[#B99A22] bg-[#FFFCF3] ring-2 ring-[#EDE2B5]"
                      : "border-[#E5DDCA] bg-white hover:border-[#CDBF8E] hover:bg-[#FFFDF8]"
                  }`}
                >
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex min-w-0 items-center gap-3">
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#F8F0D7] text-[#8F740D]">
                        <Mail className="h-5 w-5" />
                      </div>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-[#222731]">
                          {account.sender_name || account.email}
                        </p>
                        <p className="mt-1 truncate text-xs text-[#77705E]">{account.email}</p>
                        <div className="mt-2 flex flex-wrap items-center gap-2">
                          <span className={`rounded-full px-2 py-1 text-[10px] font-semibold ${statusTone(account.status)}`}>
                            {account.status}
                          </span>
                          <span className="text-[10px] uppercase tracking-wide text-[#8B8371]">
                            {account.provider}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between gap-5 sm:block sm:text-right">
                      <div>
                        <p className="text-xs text-[#817966]">Available today</p>
                        <p className="mt-1 text-sm font-semibold text-[#292D36]">
                          {remaining.toLocaleString()} / {account.sending_limit.toLocaleString()}
                        </p>
                      </div>
                      {selected && <CheckCircle2 className="h-5 w-5 text-[#8F740D] sm:ml-auto sm:mt-2" />}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="mt-6 rounded-xl border border-dashed border-[#D9CFB8] bg-[#FCFAF4] px-5 py-10 text-center">
            <Mail className="mx-auto h-7 w-7 text-[#8F740D]" />
            <p className="mt-3 text-sm font-semibold text-[#292D36]">No sender account connected</p>
            <p className="mt-1 text-xs text-[#817966]">
              Connect and verify an email account before launching a campaign.
            </p>
          </div>
        )}
      </section>

      <aside className="space-y-5">
        <section className="rounded-2xl border border-[#E8E1D0] bg-[#FFFCF3] p-5">
          <h3 className="font-semibold text-[#171A22]">Selected Sender</h3>
          {selectedAccount ? (
            <div className="mt-4 rounded-xl border border-[#E5DDCA] bg-white p-4">
              <p className="text-sm font-semibold text-[#292D36]">
                {selectedAccount.sender_name || selectedAccount.email}
              </p>
              <p className="mt-1 text-xs text-[#817966]">{selectedAccount.email}</p>
              <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                <div className="rounded-lg bg-[#F8F5EC] p-3">
                  <p className="text-[#817966]">Daily limit</p>
                  <p className="mt-1 font-semibold text-[#292D36]">
                    {selectedAccount.sending_limit.toLocaleString()}
                  </p>
                </div>
                <div className="rounded-lg bg-[#F8F5EC] p-3">
                  <p className="text-[#817966]">Health</p>
                  <p className="mt-1 font-semibold text-[#292D36]">
                    {selectedAccount.health_status || "Unknown"}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <p className="mt-4 text-sm text-[#817966]">Choose an account to continue.</p>
          )}
        </section>

        <div className="flex gap-3 rounded-2xl border border-[#D4E8D9] bg-[#F3FBF5] p-4 text-sm text-[#356345]">
          <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0" />
          <p className="leading-6">
            Sender verification and provider health are controlled by the Email Account module.
          </p>
        </div>
      </aside>
    </div>
  );
};
