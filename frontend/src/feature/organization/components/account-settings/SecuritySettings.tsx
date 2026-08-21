import { useCallback, useEffect, useRef, useState } from "react";
import { getApiErrorMessage } from "../../../../shared/utils/apiError";
import {
  Lock,
  Eye,
  EyeOff,
  ShieldCheck,
  Laptop,
  CheckCircle,
  Loader2,
  Copy,
  Download,
  AlertTriangle,
  Trash2,
} from "lucide-react";
import { useAuthStore } from "../../../../shared/store/AuthStore";
import {
  changePassword,
  deleteCurrentAccount,
  disable2FA,
  getCurrentAuthSession,
  getCurrentUser,
  listAuthSessions,
  revokeOtherAuthSessions,
  revokeAuthSession,
  setup2FA,
  verify2FA,
} from "../../../../shared/api/authApi";
import type { AuthSession } from "../../../../shared/api/authApi";
import { ConfirmDialog } from "../../../../shared/components/ConfirmDialog";
import { useToast } from "../../../../shared/hooks/useToast";

const PASSWORD_MIN_LENGTH = 12;
const PASSWORD_MAX_LENGTH = 128;
const PASSWORD_SPECIAL_CHARACTERS = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~";

export const SecuritySettings = () => {
  const store = useAuthStore();
  const user = store.user;
  const { setUser } = store;

  const [is2faOverride, setIs2faOverride] = useState<{ userUuid: string | null; value: boolean } | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const user2faSource = !!(user?.is_2fa_enabled || user?.two_factor_enabled);
  const is2faEnabled = is2faOverride && is2faOverride.userUuid === user?.uuid
    ? is2faOverride.value
    : user2faSource;

  // Modal Password States
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [isSaving, setIsSaving] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState("");
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);

  // 2FA Setup Flow States
  const [isSetupLoading, setIsSetupLoading] = useState(false);
  const [setupData, setSetupData] = useState<{
    secret: string;
    provisioning_uri: string;
    qr_code: string;
    recovery_codes: string[];
  } | null>(null);

  const [verificationCode, setVerificationCode] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [isDisabling, setIsDisabling] = useState(false);
  const [disable2FADialogOpen, setDisable2FADialogOpen] = useState(false);
  const [hasCopiedOrDownloaded, setHasCopiedOrDownloaded] = useState(false);
  const [showCopyWarning, setShowCopyWarning] = useState(false);
  const [sessions, setSessions] = useState<AuthSession[]>([]);
  const [currentSessionUuid, setCurrentSessionUuid] = useState<string | null>(null);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [, setSessionsError] = useState(false);
  const [revokingSessionUuid, setRevokingSessionUuid] = useState<string | null>(null);
  const [postPasswordSignOutPromptOpen, setPostPasswordSignOutPromptOpen] = useState(false);
  const mountedRef = useRef(true);

  const { showToast } = useToast();

  // Sync 2FA state from DB on mount / reload
  useEffect(() => {
    const fetchLatestUser = async () => {
      try {
        const latestUser = await getCurrentUser();
        if (latestUser) {
          setUser(latestUser);
        }
      } catch (err) {
        console.error("Failed to load user details on mount:", err);
      }
    };
    fetchLatestUser();
  }, [setUser]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const requestSessions = useCallback(async (): Promise<{
    sessions: AuthSession[];
    currentSessionUuid: string | null;
  }> => {
    const [items, current] = await Promise.all([
      listAuthSessions(),
      getCurrentAuthSession(),
    ]);

    return {
      sessions: items,
      currentSessionUuid: current?.uuid || null,
    };
  }, []);

  useEffect(() => {
    let isActive = true;

    void requestSessions()
      .then(({ sessions: nextSessions, currentSessionUuid: nextCurrentSessionUuid }) => {
        if (!isActive || !mountedRef.current) return;
        setSessions(nextSessions);
        setCurrentSessionUuid(nextCurrentSessionUuid);
        setSessionsError(false);
      })
      .catch(() => {
        if (!isActive || !mountedRef.current) return;
        setSessionsError(true);
        showToast("Active sessions could not be loaded", "error");
      })
      .finally(() => {
        if (isActive && mountedRef.current) {
          setSessionsLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [requestSessions]);

  const reloadSessions = useCallback(async () => {
    setSessionsLoading(true);
    setSessionsError(false);
    try {
      const { sessions: nextSessions, currentSessionUuid: nextCurrentSessionUuid } = await requestSessions();
      if (!mountedRef.current) return;
      setSessions(nextSessions);
      setCurrentSessionUuid(nextCurrentSessionUuid);
      setSessionsError(false);
    } catch {
      if (!mountedRef.current) return;
      setSessionsError(true);
      showToast("Active sessions could not be loaded", "error");
    } finally {
      if (mountedRef.current) {
        setSessionsLoading(false);
      }
    }
  }, [requestSessions]);

  const handleRevokeSession = async (sessionUuid: string) => {
    setRevokingSessionUuid(sessionUuid);
    try {
      await revokeAuthSession(sessionUuid);
      setSessions((current) => current.filter((item) => item.uuid !== sessionUuid));
      showToast("Session signed out", "success");
    } catch {
      showToast("Session could not be revoked", "error");
    } finally {
      setRevokingSessionUuid(null);
    }
  };

  const handleSignOutOtherSessions = async () => {
    const otherSessions = sessions.filter((item) => item.uuid !== currentSessionUuid);
    if (otherSessions.length === 0) return;
    setRevokingSessionUuid("all");
    try {
      await revokeOtherAuthSessions();
      setSessions((current) => current.filter((item) => item.uuid === currentSessionUuid));
      showToast("Other sessions signed out", "success");
    } catch {
      showToast("Other sessions could not be signed out", "error");
      await reloadSessions();
    } finally {
      setRevokingSessionUuid(null);
    }
  };

  const handlePostPasswordSignOut = async () => {
    setRevokingSessionUuid("all");
    try {
      await revokeOtherAuthSessions();
      setSessions((current) => current.filter((item) => item.uuid === currentSessionUuid));
      setPostPasswordSignOutPromptOpen(false);
      showToast("Other sessions signed out", "success");
    } catch {
      showToast("Other sessions could not be signed out", "error");
      await reloadSessions();
    } finally {
      setRevokingSessionUuid(null);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmation !== "DELETE") {
      showToast('Type "DELETE" to confirm account deletion.', "info");
      return;
    }
    setIsDeletingAccount(true);
    try {
      await deleteCurrentAccount();
      store.logout();
      window.location.assign("/login");
    } catch (error) {
      showToast(
        getApiErrorMessage(error, "Account deletion could not be scheduled."),
        "error",
      );
    } finally {
      setIsDeletingAccount(false);
    }
  };

  const handleModalClose = () => {
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setShowCurrentPassword(false);
    setShowNewPassword(false);
    setShowConfirmPassword(false);
    setIsModalOpen(false);
  };

  const getPasswordValidationError = (value: string) => {
    if (value.length < PASSWORD_MIN_LENGTH) {
      return "Password must be at least 12 characters";
    }
    if (value.length > PASSWORD_MAX_LENGTH) {
      return "Password must be at most 128 characters";
    }
    if (!/[A-Z]/.test(value)) {
      return "Password must contain at least one uppercase letter";
    }
    if (!/[a-z]/.test(value)) {
      return "Password must contain at least one lowercase letter";
    }
    if (!/\d/.test(value)) {
      return "Password must contain at least one number";
    }
    if (![...value].some((character) => PASSWORD_SPECIAL_CHARACTERS.includes(character))) {
      return "Password must contain at least one special character";
    }
    return null;
  };

  const handlePasswordChangeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPassword || !newPassword || !confirmPassword) {
      showToast("Please fill in all fields.", "error");
      return;
    }

    const passwordValidationError = getPasswordValidationError(newPassword);
    if (passwordValidationError) {
      showToast(passwordValidationError, "error");
      return;
    }
    if (newPassword !== confirmPassword) {
      showToast("New password and confirm password do not match.", "error");
      return;
    }

    setIsSaving(true);
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      showToast("Password changed successfully", "success");
      handleModalClose();
      setPostPasswordSignOutPromptOpen(true);
      void reloadSessions();
    } catch (err: unknown) {
      showToast(getApiErrorMessage(err, "Failed to change password. Please verify your current password."), "error");
    } finally {
      setIsSaving(false);
    }
  };

  // 2FA Enable Handlers
  const handleStart2FA = async () => {
    setIsSetupLoading(true);
    setHasCopiedOrDownloaded(false);
    setShowCopyWarning(false);
    try {
      const response = await setup2FA();
      if (response && response.data) {
        setSetupData(response.data);
      }
    } catch (err: unknown) {
      const msg = getApiErrorMessage(err, "");
      if (msg.toLowerCase().includes("already enabled") || msg.toLowerCase().includes("already active")) {
        if (user) {
          store.setUser({
            ...user,
            is_2fa_enabled: true,
            two_factor_enabled: true,
          });
        }
        setIs2faOverride({ userUuid: user?.uuid ?? null, value: true });
        showToast("2FA is already enabled", "success");
      } else {
        showToast(msg || "Failed to initialize 2FA setup.", "error");
      }
    } finally {
      setIsSetupLoading(false);
    }
  };

  const handleCopyRecoveryCodes = () => {
    if (setupData) {
      navigator.clipboard.writeText(setupData.recovery_codes.join("\n"));
      setHasCopiedOrDownloaded(true);
      setShowCopyWarning(false);
      showToast("Recovery codes copied to clipboard.", "success");
    }
  };

  const handleDownloadRecoveryCodes = () => {
    if (setupData) {
      const blob = new Blob([setupData.recovery_codes.join("\n")], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "mailtracko-recovery-codes.txt";
      a.click();
      URL.revokeObjectURL(url);
      setHasCopiedOrDownloaded(true);
      setShowCopyWarning(false);
      showToast("Recovery codes downloaded.", "success");
    }
  };

  const handleVerify2FA = async () => {
    if (!verificationCode) {
      showToast("Please enter the 6-digit authentication code.", "error");
      return;
    }
    if (!hasCopiedOrDownloaded) {
      setShowCopyWarning(true);
      showToast("Please copy or download your recovery codes before proceeding.", "info");
      return;
    }

    setIsVerifying(true);
    try {
      await verify2FA(verificationCode);
      if (user) {
        store.setUser({
          ...user,
          is_2fa_enabled: true,
          two_factor_enabled: true,
        });
      }
      setIs2faOverride({ userUuid: user?.uuid ?? null, value: true });
      setSetupData(null);
      setVerificationCode("");
      showToast("2FA enabled successfully", "success");
    } catch (err: unknown) {
      showToast(getApiErrorMessage(err, "Invalid 6-digit code. Please try again."), "error");
    } finally {
      setIsVerifying(false);
    }
  };

  const handleDisable2FA = async () => {
    setIsDisabling(true);
    try {
      await disable2FA();
      if (user) {
        store.setUser({
          ...user,
          is_2fa_enabled: false,
          two_factor_enabled: false,
        });
      }
      setIs2faOverride({ userUuid: user?.uuid ?? null, value: false });
      setDisable2FADialogOpen(false);
      showToast("2FA disabled successfully", "success");
    } catch (err: unknown) {
      showToast(getApiErrorMessage(err, "Failed to disable 2FA."), "error");
    } finally {
      setIsDisabling(false);
    }
  };

  return (
    <div className="space-y-6">
      <ConfirmDialog
        open={postPasswordSignOutPromptOpen}
        onOpenChange={setPostPasswordSignOutPromptOpen}
        title="Sign out other devices?"
        description="Your password was changed successfully. For extra security, you can sign out every other active MailTracko session and keep this device signed in."
        confirmLabel="Sign out other devices"
        cancelLabel="Keep other sessions"
        variant="warning"
        isLoading={revokingSessionUuid === "all"}
        onConfirm={handlePostPasswordSignOut}
      />
      <ConfirmDialog
        open={disable2FADialogOpen}
        onOpenChange={setDisable2FADialogOpen}
        title="Disable two-factor authentication?"
        description="Your account will no longer require an authenticator code at sign-in, which reduces account security."
        confirmLabel="Disable 2FA"
        isLoading={isDisabling}
        onConfirm={handleDisable2FA}
      />
      {/* Notifications are rendered by the global top-right toast host. */}

      {/* Security Settings Section */}
      <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 space-y-6">
        <div>
          <h2 className="text-base font-semibold text-[#1A1C1C]">
            Security Settings
          </h2>
          <p className="text-xs text-[#4C4736] mt-0.5">
            Manage your password, authentication methods, and account security.
          </p>
        </div>

        {/* Change Password Trigger */}
        {user?.has_password === false ? (
          <div className="space-y-4 pt-2 border-t border-[#F4F3F3]">
            <div className="flex items-center gap-2 text-sm font-semibold text-[#1A1C1C]">
              <Lock className="w-4 h-4 text-[#8F740D]" />
              <h3>Password</h3>
            </div>
            <p className="text-xs text-[#4C4736] -mt-2">
              This account was created with Google sign-in and does not use a password.
            </p>
          </div>
        ) : (
          <div className="space-y-4 pt-2 border-t border-[#F4F3F3]">
            <div className="flex items-center gap-2 text-sm font-semibold text-[#1A1C1C]">
              <Lock className="w-4 h-4 text-[#8F740D]" />
              <h3>Change Password</h3>
            </div>
            <p className="text-xs text-[#4C4736] -mt-2">
              Update your password regularly to keep your account secure.
            </p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="px-4 py-2 border border-[#CEC6B0]/60 rounded-xl text-xs font-semibold text-[#1A1C1C] hover:bg-[#F4F3F3] transition-colors cursor-pointer bg-white"
            >
              Change Password
            </button>
          </div>
        )}

        {/* Two-Factor Authentication */}
        <div className="space-y-4 pt-4 border-t border-[#F4F3F3]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-semibold text-[#1A1C1C]">
              <ShieldCheck className="w-4 h-4 text-[#8F740D]" />
              <h3>Authenticator app (TOTP)</h3>
            </div>
            <span className={`inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
              is2faEnabled
                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                : "bg-red-50 text-red-700 border-red-200"
            }`}>
              <CheckCircle className="w-3 h-3" /> {is2faEnabled ? "Enabled" : "Disabled"}
            </span>
          </div>
          <p className="text-xs text-[#4C4736] -mt-2">
            Use Google Authenticator, Authy, or another compatible authenticator app.
          </p>

          {/* Setup / Status Layout Block */}
          <div className="pt-2">
            {is2faEnabled ? (
              <div className="space-y-3">
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-xs text-emerald-800 leading-relaxed">
                  <p className="font-bold text-sm mb-1 flex items-center gap-1.5">
                    <CheckCircle className="w-4 h-4 text-emerald-600" />
                    Two-Factor Authentication is active
                  </p>
                  <p>Your account is protected with a secondary authentication code. Ensure you keep your recovery codes stored safely.</p>
                </div>
                <button
                  type="button"
                  onClick={() => setDisable2FADialogOpen(true)}
                  disabled={isDisabling}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-xl transition-colors disabled:opacity-50 cursor-pointer"
                >
                  {isDisabling ? "Disabling..." : "Disable 2FA"}
                </button>
              </div>
            ) : setupData ? (
              /* Setup In-Progress Block */
              <div className="border border-[#CEC6B0]/40 rounded-xl p-5 bg-[#F9F9F9] space-y-5 animate-in fade-in duration-200">
                <div className="flex flex-col md:flex-row gap-6">
                  {/* QR code scanning */}
                  <div className="space-y-2 flex flex-col items-center md:items-start">
                    <span className="text-xs font-bold text-[#4C4736] uppercase tracking-wide">1. Scan QR Code in your authenticator app</span>
                    <img
                      src={setupData.qr_code}
                      alt="Authenticator QR Code"
                      className="w-40 h-40 border border-[#CEC6B0]/40 rounded-xl bg-white p-2 shadow-sm"
                    />
                    <span className="text-[10px] text-[#4C4736] text-center md:text-left">
                      Secret: <code className="bg-[#F4F3F3] px-1 py-0.5 rounded font-mono text-[10px]">{setupData.secret}</code>
                    </span>
                  </div>

                  {/* Recovery Codes Block */}
                  <div className="flex-1 space-y-3">
                    <span className="text-xs font-bold text-[#4C4736] uppercase tracking-wide block">2. Save Recovery Codes</span>
                    <p className="text-[11px] text-[#4C4736] leading-relaxed">
                      Recovery codes are used to access your account if you lose your authenticator device. Write them down or download them.
                    </p>

                    <div className="grid grid-cols-2 gap-2 bg-white border border-[#CEC6B0]/40 rounded-xl p-3 font-mono text-xs text-[#1A1C1C]">
                      {setupData.recovery_codes.map((code) => (
                        <div key={code} className="text-center bg-[#F9F9F9] py-1 rounded border border-[#EEEEEE]">
                          {code}
                        </div>
                      ))}
                    </div>

                    <div className="flex gap-2.5">
                      <button
                        type="button"
                        onClick={handleCopyRecoveryCodes}
                        className="flex items-center gap-1.5 px-3 py-1.5 border border-[#CEC6B0]/60 rounded-xl text-xs font-semibold text-[#1A1C1C] hover:bg-[#F4F3F3] transition-colors cursor-pointer bg-white"
                      >
                        <Copy className="w-3.5 h-3.5" />
                        Copy All
                      </button>
                      <button
                        type="button"
                        onClick={handleDownloadRecoveryCodes}
                        className="flex items-center gap-1.5 px-3 py-1.5 border border-[#CEC6B0]/60 rounded-xl text-xs font-semibold text-[#1A1C1C] hover:bg-[#F4F3F3] transition-colors cursor-pointer bg-white"
                      >
                        <Download className="w-3.5 h-3.5" />
                        Download (.txt)
                      </button>
                    </div>
                  </div>
                </div>

                {/* Warning Alert if they haven't saved */}
                {showCopyWarning && (
                  <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs font-medium text-amber-800 flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <span>Please copy or download your recovery codes. If you lose your device, you will need these codes to log in.</span>
                  </div>
                )}

                {/* Code verification input */}
                <div className="pt-3 border-t border-[#F4F3F3] space-y-2">
                  <label htmlFor="totp-verify-input" className="block text-xs font-bold text-[#4C4736] uppercase tracking-wide">
                    3. Enter Authentication Code
                  </label>
                  <p className="text-[11px] text-[#4C4736]">
                    Enter the 6-digit code shown in your authenticator app (Google Authenticator, Authy, or compatible app).
                  </p>
                  <div className="flex gap-3 max-w-sm">
                    <input
                      id="totp-verify-input"
                      type="text"
                      maxLength={6}
                      placeholder="000000"
                      value={verificationCode}
                      inputMode="numeric"
                      autoComplete="one-time-code"
                      onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                      className="w-full px-3 py-2 rounded-xl border border-[#CEC6B0]/60 text-sm text-[#1A1C1C] bg-white focus:outline-none focus:ring-2 focus:ring-[#F1D442]/50 focus:border-[#8F740D] transition-all text-center tracking-widest font-bold placeholder-[#CEC6B0]"
                    />
                    <button
                      type="button"
                      onClick={handleVerify2FA}
                      disabled={isVerifying}
                      className="flex items-center gap-1 px-5 py-2 bg-[#8F740D] hover:bg-[#6A5B00] text-white text-xs font-semibold rounded-xl transition-colors disabled:opacity-50 cursor-pointer shrink-0"
                    >
                      {isVerifying ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Verifying...</span>
                        </>
                      ) : (
                        <span>Verify & Enable</span>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              /* Enable Button */
              <div className="space-y-3">
                <button
                  type="button"
                  onClick={handleStart2FA}
                  disabled={isSetupLoading}
                  className="flex items-center gap-1.5 px-4 py-2 bg-[#8F740D] hover:bg-[#6A5B00] text-white text-xs font-semibold rounded-xl transition-colors disabled:opacity-50 cursor-pointer"
                >
                  {isSetupLoading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Loading setup...</span>
                    </>
                  ) : (
                    <span>Enable Authenticator App (TOTP)</span>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-3 pt-4 border-t border-[#F4F3F3]">
          <h3 className="text-sm font-semibold text-[#1A1C1C]">Account identity</h3>
          <div className="flex items-center justify-between rounded-xl border border-[#CEC6B0]/40 bg-[#F9F9F9] px-4 py-3">
            <div>
              <p className="text-sm font-semibold text-[#1A1C1C]">{user?.email || "Account email unavailable"}</p>
              <p className="mt-0.5 text-[11px] text-[#4C4736]">Authentication providers are linked through their verified sign-in flows.</p>
            </div>
            <ShieldCheck className="h-5 w-5 text-[#8F740D]" />
          </div>
        </div>

        <div className="space-y-4 pt-4 border-t border-[#F4F3F3]">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[#1A1C1C]">Active Sessions</h3>
            <button type="button" onClick={() => void reloadSessions()} disabled={sessionsLoading} className="text-xs font-bold text-[#8F740D] hover:underline cursor-pointer disabled:opacity-50">
              Refresh
            </button>
          </div>
          <p className="text-xs text-[#4C4736] -mt-2">
            These are the devices currently signed in to your account.
          </p>

          <div className="space-y-3">
            {sessionsLoading ? (
              <div className="grid min-h-24 place-items-center"><Loader2 className="h-5 w-5 animate-spin text-[#8F740D]" /></div>
            ) : sessions.length === 0 ? (
              <p className="rounded-xl border border-dashed border-[#CEC6B0] bg-[#F9F9F9] p-5 text-center text-xs text-[#4C4736]">No active sessions were returned.</p>
            ) : sessions.map((session) => {
              const isCurrent = session.uuid === currentSessionUuid;
              return <div key={session.uuid} className="flex items-center justify-between gap-4 rounded-xl border border-[#CEC6B0]/40 bg-[#F9F9F9] p-4">
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-[#CEC6B0]/30 bg-white"><Laptop className="h-5 w-5 text-[#8F740D]" /></div>
                  <div className="min-w-0"><h4 className="text-sm font-semibold text-[#1A1C1C]">{isCurrent ? "Current browser" : "Web session"}</h4><p className="mt-0.5 truncate text-[11px] text-[#4C4736]" title={session.user_agent || undefined}>{session.ip_address || "IP unavailable"} · {session.created_at ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(session.created_at)) : "Start time unavailable"}</p></div>
                </div>
                {isCurrent ? <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-0.5 text-xs font-bold text-emerald-700">Current</span> : <button type="button" disabled={revokingSessionUuid === session.uuid || revokingSessionUuid === "all"} onClick={() => void handleRevokeSession(session.uuid)} className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-bold text-red-700 hover:bg-red-50 disabled:opacity-50">Sign out</button>}
              </div>;
            })}
          </div>

          <div className="pt-2">
            {sessions.some((item) => item.uuid !== currentSessionUuid) ? (
              <button type="button" onClick={() => void handleSignOutOtherSessions()} disabled={revokingSessionUuid !== null} className="px-4 py-2 border border-red-200 text-red-600 rounded-xl text-xs font-bold hover:bg-red-50 transition-colors cursor-pointer disabled:cursor-not-allowed disabled:opacity-50">
                {revokingSessionUuid === "all" ? "Signing out..." : "Sign out other sessions"}
              </button>
            ) : (
              <p className="text-xs text-[#4C4736]">No other active sessions.</p>
            )}
          </div>
        </div>
        <div className="space-y-4 border-t border-red-100 pt-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-sm font-semibold text-red-700">
                <Trash2 className="h-4 w-4" />
                Delete user account
              </div>
              <p className="mt-1 max-w-2xl text-xs leading-5 text-[#4C4736]">
                Schedules deletion of your personal MailTracko account and signs out every session.
                Workspace owners must transfer ownership or schedule organization deletion first.
              </p>
            </div>
            <button
              type="button"
              onClick={() => {
                setDeleteConfirmation("");
                setIsDeleteModalOpen(true);
              }}
              className="shrink-0 rounded-xl border border-red-200 bg-white px-4 py-2 text-xs font-bold text-red-700 hover:bg-red-50"
            >
              Delete account
            </button>
          </div>
        </div>
      </div>

      {isDeleteModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1A1C1C]/45 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-red-100 bg-white p-6 shadow-xl">
            <div className="flex items-start gap-3">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-red-50">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <h3 className="font-semibold text-[#1A1C1C]">Schedule account deletion?</h3>
                <p className="mt-1 text-xs leading-5 text-[#4C4736]">
                  This revokes all sessions immediately. Type <strong>DELETE</strong> to confirm.
                </p>
              </div>
            </div>
            <input
              value={deleteConfirmation}
              onChange={(event) => setDeleteConfirmation(event.target.value)}
              placeholder="DELETE"
              autoComplete="off"
              className="mt-5 h-11 w-full rounded-xl border border-[#CEC6B0]/60 px-3 text-sm outline-none focus:border-red-400 focus:ring-2 focus:ring-red-100"
            />
            <div className="mt-5 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setIsDeleteModalOpen(false)}
                disabled={isDeletingAccount}
                className="rounded-xl border border-[#CEC6B0]/60 bg-white px-4 py-2 text-xs font-semibold text-[#1A1C1C] hover:bg-[#F4F3F3]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => void handleDeleteAccount()}
                disabled={deleteConfirmation !== "DELETE" || isDeletingAccount}
                className="rounded-xl bg-red-600 px-4 py-2 text-xs font-bold text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isDeletingAccount ? "Scheduling…" : "Delete account"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Change Password Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-[#1A1C1C]/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form
            noValidate
            onSubmit={handlePasswordChangeSubmit}
            className="bg-white rounded-2xl border border-[#CEC6B0]/40 w-full max-w-md p-6 space-y-5 shadow-xl relative animate-in fade-in zoom-in-95 duration-200"
          >
            <div>
              <h3 className="text-base font-semibold text-[#1A1C1C]">Change Password</h3>
              <p className="text-xs text-[#4C4736] mt-0.5">
                Set a new password for your account.
              </p>
            </div>

            <div className="space-y-4">
              {/* Current Password */}
              <div className="space-y-1.5">
                <label htmlFor="modal-current-pw" className="block text-xs font-bold text-[#4C4736] tracking-wide uppercase">
                  Current Password
                </label>
                <div className="relative flex items-center">
                  <input
                    id="modal-current-pw"
                    type={showCurrentPassword ? "text" : "password"}
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="Enter current password"
                    className="w-full px-3 py-2.5 pr-10 rounded-xl border border-[#CEC6B0]/60 text-sm text-[#1A1C1C] bg-white focus:outline-none focus:ring-2 focus:ring-[#F1D442]/50 focus:border-[#8F740D] transition-all placeholder-[#CEC6B0]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowCurrentPassword((v) => !v)}
                    className="absolute right-3 text-[#4C4736] hover:text-[#1A1C1C]"
                  >
                    {showCurrentPassword ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* New Password */}
              <div className="space-y-1.5">
                <label htmlFor="modal-new-pw" className="block text-xs font-bold text-[#4C4736] tracking-wide uppercase">
                  New Password
                </label>
                <div className="relative flex items-center">
                  <input
                    id="modal-new-pw"
                    type={showNewPassword ? "text" : "password"}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter new password"
                    minLength={PASSWORD_MIN_LENGTH}
                    maxLength={PASSWORD_MAX_LENGTH}
                    aria-describedby="modal-new-pw-requirements modal-new-pw-count"
                    className="w-full px-3 py-2.5 pr-10 rounded-xl border border-[#CEC6B0]/60 text-sm text-[#1A1C1C] bg-white focus:outline-none focus:ring-2 focus:ring-[#F1D442]/50 focus:border-[#8F740D] transition-all placeholder-[#CEC6B0]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPassword((v) => !v)}
                    className="absolute right-3 text-[#4C4736] hover:text-[#1A1C1C]"
                  >
                    {showNewPassword ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                  </button>
                </div>
                <div className="flex items-center justify-between gap-2 text-[11px] text-[#4C4736]">
                  <span id="modal-new-pw-requirements">12–128 characters with uppercase, lowercase, number, and symbol.</span>
                  <span id="modal-new-pw-count" className="font-semibold" aria-live="polite">{newPassword.length}/{PASSWORD_MAX_LENGTH}</span>
                </div>
              </div>

              {/* Confirm New Password */}
              <div className="space-y-1.5">
                <label htmlFor="modal-confirm-pw" className="block text-xs font-bold text-[#4C4736] tracking-wide uppercase">
                  Confirm New Password
                </label>
                <div className="relative flex items-center">
                  <input
                    id="modal-confirm-pw"
                    type={showConfirmPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm new password"
                    maxLength={PASSWORD_MAX_LENGTH}
                    className="w-full px-3 py-2.5 pr-10 rounded-xl border border-[#CEC6B0]/60 text-sm text-[#1A1C1C] bg-white focus:outline-none focus:ring-2 focus:ring-[#F1D442]/50 focus:border-[#8F740D] transition-all placeholder-[#CEC6B0]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword((v) => !v)}
                    className="absolute right-3 text-[#4C4736] hover:text-[#1A1C1C]"
                  >
                    {showConfirmPassword ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2 border-t border-[#F4F3F3]">
              <button
                type="button"
                onClick={handleModalClose}
                className="px-4 py-2 border border-[#CEC6B0]/60 rounded-xl text-xs font-semibold text-[#1A1C1C] hover:bg-[#F4F3F3] transition-colors cursor-pointer bg-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSaving}
                className="flex items-center gap-1.5 px-4 py-2 bg-[#8F740D] hover:bg-[#6A5B00] text-white text-xs font-semibold rounded-xl transition-colors disabled:opacity-50 cursor-pointer"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <span>Save Changes</span>
                )}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
