import { useState, useMemo, useEffect } from "react";
import { useSearch, useNavigate } from "@tanstack/react-router";
import {
  useEmailAccountsList,
  useTestConnection,
  useDeleteEmailAccount,
} from "../hooks/useEmailAccounts";
import { Mail, ShieldCheck, Plus, Loader2, Trash2, RefreshCw, Flame, AlertTriangle } from "lucide-react";
import { GoogleIcon } from "./shared/ProviderIcons";
import { ConnectWizardModal } from "./ConnectWizardModal";
import { getApiErrorMessage } from "../../../shared/utils/apiError";
import { SMTPFormModal } from "./SMTPFormModal";
import { VerifyCodeModal } from "./VerifyCodeModal";
import { GmailModal } from "./GmailModal";
import { useToast } from "../../../shared/hooks/useToast";
import { ConfirmDialog } from "../../../shared/components/ConfirmDialog";

export const EmailAccountsDashboard = () => {
  const navigate = useNavigate();
  const search: { success?: string; error?: string } = useSearch({
    from: "/_protected/organization/account-settings/email-accounts",
  });

  // Queries
  const { data: accountsData, isLoading: accountsLoading, refetch } = useEmailAccountsList();
  const testMutation = useTestConnection();
  const deleteMutation = useDeleteEmailAccount();
  const { showToast } = useToast();

  // Local tab state
  const [activeTab, setActiveTab] = useState<"connected" | "failed">("connected");

  // Wizard coordination states
  const [wizardOpen, setWizardOpen] = useState(false);
  const [smtpFormOpen, setSmtpFormOpen] = useState(false);
  const [gmailOpen, setGmailOpen] = useState(false);

  // Verification code modal states
  const [verifyCodeOpen, setVerifyCodeOpen] = useState(false);
  const [verifyUuid, setVerifyUuid] = useState("");
  const [verifyEmail, setVerifyEmail] = useState("");

  // Testing health indicators
  const [testingUuid, setTestingUuid] = useState<string | null>(null);
  const [disconnectUuid, setDisconnectUuid] = useState<string | null>(null);

  // Catch OAuth callback redirect state
  useEffect(() => {
    if (search.success === "email_connected") {
      refetch();
      if (window.opener) {
        // Notify the opener window (main page) and close this popup
        window.opener.postMessage({ type: "email_connected_oauth" }, window.location.origin);
        window.close();
      } else {
        // Clear query params
        navigate({
          to: "/organization/account-settings/email-accounts",
          search: {},
        });
      }
    } else if (search.error) {
      const message =
        search.error === "oauth_denied"
          ? "Google authorization was cancelled or denied."
          : search.error === "oauth_invalid_callback"
            ? "Google returned an incomplete authorization response. Please try again."
            : search.error === "oauth_account_already_connected"
              ? "This account is already connected to your organization."
              : search.error === "oauth_conflict"
                ? "This Google account conflicts with an existing sender account."
                : "Failed to connect the Google account. Please try again.";
      showToast(message, "error");
      if (window.opener) {
        window.opener.postMessage(
          { type: "email_connected_oauth_error", error: search.error },
          window.location.origin,
        );
        window.close();
      } else {
        navigate({
          to: "/organization/account-settings/email-accounts",
          search: {},
        });
      }
    }
  }, [search, refetch, navigate, showToast]);

  // Listen for the OAuth popup reporting a completed connection
  useEffect(() => {
    const handleOAuthMessage = (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return;
      if (event.data?.type === "email_connected_oauth") {
        refetch();
      } else if (event.data?.type === "email_connected_oauth_error") {
        const message = event.data?.error === "oauth_account_already_connected"
          ? "This account is already connected to your organization."
          : "Failed to connect the Google account. Please try again.";
        showToast(message, "error");
      }
    };
    window.addEventListener("message", handleOAuthMessage);
    return () => window.removeEventListener("message", handleOAuthMessage);
  }, [refetch, showToast]);

  // Statistics computation
  const stats = useMemo(() => {
    const items = accountsData?.items ?? [];
    const scores = items
      .map((item) => item.health_score)
      .filter((score) => Number.isFinite(score));
    const avgScore = scores.length > 0
      ? Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length)
      : null;

    const healthyCount = items.filter((item) => item.health_status === "healthy").length;
    const attentionCount = items.filter(
      (item) => item.health_status === "unhealthy" || item.status === "reconnect_required",
    ).length;

    return {
      score: avgScore,
      healthyCount,
      attentionCount,
      total: items.length,
    };
  }, [accountsData]);

  // Filter accounts based on tab selection
  const filteredAccounts = useMemo(() => {
    if (!accountsData?.items) return [];
    const items = accountsData.items;
    if (activeTab === "connected") {
      return items.filter((i) => i.status === "active" || i.status === "pending_verification");
    } else {
      return items.filter((i) => i.status === "reconnect_required" || i.status === "disconnected");
    }
  }, [accountsData, activeTab]);

  const handleProviderSelect = (provider: "gmail" | "smtp") => {
    setWizardOpen(false);
    if (provider === "smtp") {
      setSmtpFormOpen(true);
    } else if (provider === "gmail") {
      setGmailOpen(true);
    }
  };

  const handleTestConnection = async (uuid: string) => {
    setTestingUuid(uuid);
    try {
      const res = await testMutation.mutateAsync(uuid);
      showToast(`Test Connection Completed. Deliverability Health Score: ${res.health_score}/100`, "success");
    } catch (err: unknown) {
      showToast(getApiErrorMessage(err, "Failed to verify connection parameters."), "error");
    } finally {
      setTestingUuid(null);
    }
  };

  const handleDeleteAccount = async () => {
    if (!disconnectUuid) return;
    try {
      await deleteMutation.mutateAsync(disconnectUuid);
      setDisconnectUuid(null);
      showToast("Email account disconnected successfully.", "success");
    } catch (err: unknown) {
      showToast(getApiErrorMessage(err, "Failed to disconnect email account."), "error");
    }
  };

  const handleOAuthSuccess = (authUrl: string) => {
    setGmailOpen(false);
    // Open OAuth consent in a popup window
    const width = 550;
    const height = 650;
    const left = window.screen.width / 2 - width / 2;
    const top = window.screen.height / 2 - height / 2;
    const popup = window.open(
      authUrl,
      "Connect Email Redirection",
      `width=${width},height=${height},top=${top},left=${left}`
    );
    if (!popup) {
      showToast("Your browser blocked the Google sign-in popup. Allow popups for MailTracko and try again.", "error");
      return;
    }

    // Poll only while the OAuth popup is alive, with a hard timeout so a tab
    // left open on Google cannot leave an interval running indefinitely.
    const deadline = Date.now() + 10 * 60 * 1000;
    const poll = window.setInterval(() => {
      if (popup.closed) {
        window.clearInterval(poll);
        return;
      }
      if (Date.now() >= deadline) {
        window.clearInterval(poll);
        popup.close();
        showToast("Google authorization timed out. Please try connecting the account again.", "error");
        return;
      }
      let href: string;
      try {
        href = popup.location.href;
      } catch {
        // Popup is still on the provider's cross-origin domain — keep polling
        return;
      }
      const url = new URL(href);
      if (url.origin === window.location.origin) {
        window.clearInterval(poll);
        popup.close();
        if (url.searchParams.get("error")) {
          showToast("Failed to connect account via OAuth. Please try again.", "error");
        }
        refetch();
      }
    }, 500);
  };

  return (
    <div className="space-y-6">
      <ConfirmDialog
        open={Boolean(disconnectUuid)}
        onOpenChange={(open) => { if (!open) setDisconnectUuid(null); }}
        title="Disconnect sender account?"
        description="Disconnect and remove this email account from MailTracko? This action cannot be undone."
        confirmLabel="Disconnect account"
        isLoading={deleteMutation.isPending}
        onConfirm={handleDeleteAccount}
      />
      {/* Metrics Strip */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Global Inbox Health */}
        <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-5 flex items-center justify-between shadow-sm md:col-span-2">
          <div className="space-y-3 flex-1">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-[#8F740D]" />
              <h3 className="text-sm font-bold text-[#1A1C1C]">Global Inbox Health</h3>
            </div>
            <p className="text-xs text-[#4C4736] max-w-sm">
              Aggregate deliverability score computed across all active sender domains.
            </p>
            <div className="flex gap-4 pt-1">
              <div className="bg-[#F9F9F9] rounded-xl px-3 py-1.5 border border-[#EEEEEE]">
                <p className="text-[10px] text-[#4C4736] font-semibold">Excellent</p>
                <p className="text-sm font-bold text-emerald-600">{stats.healthyCount} accounts</p>
              </div>
              <div className="bg-[#F9F9F9] rounded-xl px-3 py-1.5 border border-[#EEEEEE]">
                <p className="text-[10px] text-[#4C4736] font-semibold">Needs Attention</p>
                <p className="text-sm font-bold text-amber-600">{stats.attentionCount} account</p>
              </div>
            </div>
          </div>

          <div className="flex flex-col items-center gap-1 shrink-0 px-4">
            <div className="w-20 h-20 rounded-full border-4 border-[#F1D442]/30 border-t-[#8F740D] flex items-center justify-center">
              <span className="text-lg font-black text-[#1A1C1C]">{stats.score ?? "—"}</span>
              {stats.score !== null && <span className="text-[10px] text-[#4C4736] ml-0.5">/100</span>}
            </div>
          </div>
        </div>

        {/* Warmup Status */}
        <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-5 flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Flame className="w-5 h-5 text-[#8F740D]" />
              <h3 className="text-sm font-bold text-[#1A1C1C]">Warmup Status</h3>
            </div>
          </div>
          <div className="space-y-1 my-3 text-center sm:text-left">
            <div className="inline-flex items-center gap-1.5 bg-slate-100 text-slate-700 text-[10px] font-bold px-2 py-0.5 rounded-full">
              <AlertTriangle className="w-3.5 h-3.5" /> Not enabled
            </div>
            <p className="text-xs text-[#4C4736] pt-1">
              Automated inbox warmup is not enabled in this build. MailTracko will not claim or simulate warmup traffic.
            </p>
          </div>
          <button disabled className="w-full cursor-not-allowed py-2 border border-[#CEC6B0]/60 bg-[#F4F3F3] text-[#756F60] text-xs font-semibold rounded-xl">
            Warmup unavailable
          </button>
        </div>
      </div>

      {/* Tabs list bar */}
      <div className="flex justify-between items-center border-b border-[#EEEEEE] flex-wrap gap-2">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab("connected")}
            className={`pb-2 text-xs font-bold border-b-2 transition-all ${
              activeTab === "connected"
                ? "border-[#8F740D] text-[#8F740D]"
                : "border-transparent text-[#4C4736] hover:text-[#1A1C1C]"
            }`}
          >
            Connected Accounts
          </button>
          <button
            onClick={() => setActiveTab("failed")}
            className={`pb-2 text-xs font-bold border-b-2 transition-all ${
              activeTab === "failed"
                ? "border-[#8F740D] text-[#8F740D]"
                : "border-transparent text-[#4C4736] hover:text-[#1A1C1C]"
            }`}
          >
            Disconnected / Failed
          </button>
        </div>
        <button
          onClick={() => setWizardOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[#8F740D] hover:bg-[#6A5B00] text-white text-xs font-semibold rounded-xl transition-colors mb-2"
        >
          <Plus className="w-3.5 h-3.5" /> Connect Account
        </button>
      </div>

      {/* Grid of connected accounts */}
      {accountsLoading ? (
        <div className="flex justify-center items-center py-20">
          <Loader2 className="w-8 h-8 text-[#8F740D] animate-spin" />
        </div>
      ) : filteredAccounts.length === 0 ? (
        <div className="text-center py-16 bg-white border border-[#CEC6B0]/40 rounded-2xl">
          <Mail className="w-12 h-12 text-[#CEC6B0] mx-auto mb-3" />
          <p className="font-semibold text-sm text-[#1A1C1C]">No accounts found</p>
          <p className="text-xs text-[#4C4736] mt-1 mb-4">
            Connect Google Workspace/Gmail or a custom SMTP mailbox.
          </p>
          <button
            onClick={() => setWizardOpen(true)}
            className="px-4 py-2 bg-[#8F740D] text-white text-xs font-bold rounded-xl"
          >
            Connect Account
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {filteredAccounts.map((account) => (
            <div
              key={account.uuid}
              className={`bg-white border rounded-2xl p-5 flex flex-col justify-between hover:shadow-md transition-shadow relative ${
                account.status === "pending_verification"
                  ? "border-amber-300 bg-amber-50/10"
                  : "border-[#CEC6B0]/40"
              }`}
            >
              <div className="space-y-4">
                {/* Header: Avatar, Provider name, and Actions */}
                <div className="flex justify-between items-start gap-2">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-slate-50 border border-[#CEC6B0]/40 flex items-center justify-center shrink-0">
                      {account.provider === "gmail" ? (
                        <GoogleIcon className="w-5 h-5" />
                      ) : (
                        <Mail className="w-5 h-5 text-[#8F740D]" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-[#1A1C1C] truncate" title={account.email}>
                        {account.email}
                      </p>
                      <p className="text-[10px] text-[#4C4736] truncate capitalize">
                        {account.provider === "smtp" ? "Custom SMTP" : account.provider}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    {/* Test Connection Button */}
                    <button
                      onClick={() => handleTestConnection(account.uuid)}
                      disabled={testingUuid === account.uuid}
                      className="p-1.5 text-[#4C4736] hover:bg-slate-100 rounded-lg transition-colors"
                      title="Test Connection"
                    >
                      {testingUuid === account.uuid ? (
                        <Loader2 className="w-3.5 h-3.5 text-[#8F740D] animate-spin" />
                      ) : (
                        <RefreshCw className="w-3.5 h-3.5" />
                      )}
                    </button>
                    {/* Delete/Disconnect Button */}
                    <button
                      onClick={() => setDisconnectUuid(account.uuid)}
                      className="p-1.5 text-[#CEC6B0] hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                      title="Disconnect Account"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Verification Warning for SMTP */}
                {account.status === "pending_verification" && (
                  <div
                    onClick={() => {
                      setVerifyUuid(account.uuid);
                      setVerifyEmail(account.email);
                      setVerifyCodeOpen(true);
                    }}
                    className="flex gap-2 items-center bg-amber-50 border border-amber-200 text-[#8F740D] p-2.5 rounded-xl text-[10px] cursor-pointer hover:bg-amber-100 transition-colors font-medium"
                  >
                    <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
                    <span>Pending Verification. Enter Code →</span>
                  </div>
                )}

                {/* Score & Health details */}
                {account.status !== "pending_verification" && (
                  <div className="space-y-3">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-[#4C4736]">Health Score</span>
                      <span className="font-bold text-[#1A1C1C]">{Number.isFinite(account.health_score) ? `${account.health_score}/100` : "Not checked"}</span>
                    </div>

                    {/* Progress Bar Sent limits */}
                    <div className="space-y-1">
                      <div className="flex justify-between items-center text-[10px]">
                        <span className="text-[#4C4736]">Daily Sent limit</span>
                        <span className="font-semibold">
                          {account.daily_sent_count} / {account.sending_limit}
                        </span>
                      </div>
                      <div className="w-full bg-[#EEEEEE] h-1.5 rounded-full overflow-hidden">
                        <div
                          className="bg-[#8F740D] h-full transition-all"
                          style={{
                            width: `${account.sending_limit > 0
                              ? Math.min((account.daily_sent_count / account.sending_limit) * 100, 100)
                              : 0}%`,
                          }}
                        />
                      </div>
                      {account.daily_sent_count >= account.sending_limit * 0.9 && (
                        <p className="text-[9px] text-amber-600 font-semibold">Approaching limit</p>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Warmup is intentionally not presented as an active control until
                  a persisted backend warmup service exists. */}
              {account.status !== "pending_verification" && (
                <div className="mt-4 pt-3 border-t border-[#F4F3F3] flex justify-between items-center text-xs">
                  <span className="text-[#756F60] flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" /> Warmup unavailable
                  </span>
                </div>
              )}
            </div>
          ))}

          {/* Dotted add card */}
          <div
            onClick={() => setWizardOpen(true)}
            className="border-2 border-dashed border-[#CEC6B0]/60 hover:border-[#8F740D] rounded-2xl p-5 flex flex-col items-center justify-center text-center space-y-3 cursor-pointer hover:bg-slate-50 transition-colors min-h-[180px] group"
          >
            <div className="w-10 h-10 bg-slate-50 group-hover:bg-[#F1D442]/20 border border-[#CEC6B0]/40 group-hover:border-[#F1D442]/50 rounded-full flex items-center justify-center transition-colors">
              <Plus className="w-5 h-5 text-[#8F740D]" />
            </div>
            <div>
              <p className="text-xs font-bold text-[#1A1C1C]">Add Another Account</p>
              <p className="text-[10px] text-[#4C4736] mt-0.5">
                Connect Gmail or a custom SMTP/IMAP mailbox.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Render Steps Wizards */}
      {wizardOpen && (
        <ConnectWizardModal
          onClose={() => setWizardOpen(false)}
          onSelect={handleProviderSelect}
        />
      )}

      {smtpFormOpen && (
        <SMTPFormModal
          onClose={() => setSmtpFormOpen(false)}
          onBack={() => {
            setSmtpFormOpen(false);
            setWizardOpen(true);
          }}
          onSuccess={(uuid, email) => {
            setSmtpFormOpen(false);
            setVerifyUuid(uuid);
            setVerifyEmail(email);
            setVerifyCodeOpen(true);
            refetch();
          }}
        />
      )}

      {gmailOpen && (
        <GmailModal
          onClose={() => setGmailOpen(false)}
          onBack={() => {
            setGmailOpen(false);
            setWizardOpen(true);
          }}
          onSuccess={handleOAuthSuccess}
        />
      )}


      {verifyCodeOpen && (
        <VerifyCodeModal
          uuid={verifyUuid}
          email={verifyEmail}
          onClose={() => {
            setVerifyCodeOpen(false);
            setVerifyUuid("");
            setVerifyEmail("");
          }}
          onSuccess={() => {
            setVerifyCodeOpen(false);
            setVerifyUuid("");
            setVerifyEmail("");
            refetch();
          }}
        />
      )}
      
    </div>
  );
};
