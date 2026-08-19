import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { z } from "zod";
import { useEffect, useState } from "react";
import { ShieldCheck, ArrowLeft, Loader2 } from "lucide-react";
import { verify2FALogin } from "../shared/api/authApi";
import { getApiErrorMessage } from "../shared/utils/apiError";
import { bootstrapApp } from "../shared/app/bootstrap";
import { resolveInitialRoute } from "../shared/app/resolveInitialRoute";
import { useAuthStore } from "../shared/store/AuthStore";
import mailicon from "../assets/Background.svg";
import { completePendingInvitation } from "../shared/auth/pendingInvitation";
import { clearForcedLoginScreen } from "../shared/auth/forceLogin";
import {
  clearPending2FAToken,
  getPending2FAToken,
  storePending2FAToken,
} from "../shared/auth/pending2FA";

const verify2faSearchSchema = z.object({
  // Backward-compatible only. New logins keep the temporary token out of the URL.
  temp_token: z.string().optional(),
});

export const Route = createFileRoute("/verify-2fa")({
  validateSearch: verify2faSearchSchema,
  component: Verify2FAPage,
});

function Verify2FAPage() {
  const { temp_token: legacyTempToken } = Route.useSearch();
  const [totpCode, setTotpCode] = useState("");
  const [useRecoveryCode, setUseRecoveryCode] = useState(false);
  const [is2faVerifying, setIs2faVerifying] = useState(false);
  const [login2faError, setLogin2faError] = useState<string | null>(null);

  const navigate = useNavigate();
  const store = useAuthStore();
  const tempToken = legacyTempToken || getPending2FAToken();
  const hasServerChallenge = !tempToken; // Google OAuth stores the temporary MFA challenge in HttpOnly cookie.

  useEffect(() => {
    if (!legacyTempToken) return;
    storePending2FAToken(legacyTempToken);
    void navigate({ to: "/verify-2fa", search: {}, replace: true });
  }, [legacyTempToken, navigate]);

  const handle2faLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Password login supplies a sessionStorage token. Google OAuth uses an
    // HttpOnly mfa_challenge cookie, which deliberately cannot be read here.
    if (!totpCode.trim()) {
      setLogin2faError("Please enter your authentication code.");
      return;
    }

    setIs2faVerifying(true);
    setLogin2faError(null);
    try {
      const response = await verify2FALogin({
        ...(tempToken ? { temp_token: tempToken } : {}),
        code: totpCode.trim(),
      });

      if (response && response.data) {
        clearPending2FAToken();
        clearForcedLoginScreen();
        // The backend has already set the HttpOnly session cookie; only update
        // the in-memory user store here.
        // Set user in store
        store.setUser(response.data.user);

        // Complete a pending invitation after 2FA establishes
        // the authenticated session, using the token retained from the invite page.
        try {
          await completePendingInvitation();
        } catch {
          // The protected pending-invitation page will provide a safe retry state.
        }

        // Bootstrap and redirect
        const app = await bootstrapApp();
        if (app) {
          const initialRoute = resolveInitialRoute(app);
          navigate({ to: initialRoute });
        } else {
          navigate({ to: "/dashboard" });
        }
      }
    } catch (err: unknown) {
      setLogin2faError(getApiErrorMessage(err, "Invalid authentication code. Please try again."));
    } finally {
      setIs2faVerifying(false);
    }
  };

  return (
    <div className="w-full relative min-h-screen overflow-hidden bg-surface px-margin-mobile flex items-center justify-center">
      {/* Ambient background blur */}
      <div className="absolute -top-20 -left-32 rounded-xl w-96 h-96 bg-[#E5C52B33] blur-[120px]"></div>
      <div className="absolute -bottom-1.5 left-2/5 rounded-xl w-80 h-80 bg-[#D7C6851A] blur-[100px]"></div>
      <div className="absolute bottom-10 -right-28 rounded-xl w-125 h-125 bg-[#A8C9F726] blur-[150px]"></div>

      <div className="w-full max-w-115 rounded-xl border border-[#CEC6B0]/40 bg-white shadow-lg overflow-hidden relative z-10">
        {/* Top Border Accent */}
        <div className="h-1 w-full bg-[#8F740D]" />

        <div className="p-6 sm:p-8 space-y-6">
          <div className="text-center pb-2 mx-auto">
            <img
              src={mailicon}
              alt="MailTracko Logo"
              className="w-16 mx-auto"
            />
            <span className="text-on-surface font-sans text-center tracking-[-0.6px] text-headline-md font-bold mt-2 block">
              MailTracko
            </span>
          </div>

          <form onSubmit={handle2faLoginSubmit} className="space-y-6">
            <div className="flex flex-col gap-1 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-surface-container-low border border-outline-variant/30 mb-2">
                <ShieldCheck className="w-6 h-6 text-[#8F740D]" />
              </div>
              <span className="text-title-sm text-on-surface font-semibold">
                Two-Factor Authentication
              </span>
              <span className="text-xs text-[#4B4738] max-w-xs mx-auto">
                {useRecoveryCode
                  ? "Enter one unused MailTracko recovery code to complete sign in."
                  : "Enter the 6-digit verification code from your authenticator app."}
                {hasServerChallenge ? " Your Google sign-in is waiting for this step." : ""}
              </span>
            </div>

            {login2faError && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs font-semibold text-red-600 text-center">
                {login2faError}
              </div>
            )}

            <div className="space-y-1.5">
              <label htmlFor="totp-code" className="text-[#4B4738] text-xs font-bold text-label-caps block">
                Authentication code
              </label>
              <input
                id="totp-code"
                type="text"
                inputMode={useRecoveryCode ? "text" : "numeric"}
                autoComplete="one-time-code"
                maxLength={useRecoveryCode ? 32 : 6}
                placeholder={useRecoveryCode ? "e.g. A1B2-C3D4-E5F6" : "123456"}
                value={totpCode}
                onChange={(e) => {
                  const next = useRecoveryCode
                    ? e.target.value.toUpperCase().replace(/[^A-Z0-9-]/g, "")
                    : e.target.value.replace(/\D/g, "").slice(0, 6);
                  setTotpCode(next);
                  setLogin2faError(null);
                }}
                className="w-full px-3 py-3 rounded-lg border border-[#CEC6B0] text-sm text-on-surface bg-surface-container-low focus:bg-white focus:outline-none focus:border-[#8F740D] transition-all text-center tracking-wider font-semibold placeholder-[#CEC6B0]"
              />
            </div>

            <button
              type="button"
              onClick={() => {
                setUseRecoveryCode((current) => !current);
                setTotpCode("");
                setLogin2faError(null);
              }}
              className="w-full text-center text-xs font-bold text-[#8F740D] underline underline-offset-4 hover:text-[#6E5E00]"
            >
              {useRecoveryCode ? "Use authenticator code" : "Use recovery code"}
            </button>

            <button
              type="submit"
              disabled={is2faVerifying}
              className="w-full flex justify-center items-center gap-2 rounded-lg bg-[#8F740D] hover:bg-[#6E5E00] py-3.5 text-white text-sm font-bold shadow-md hover:shadow-lg transition-all cursor-pointer disabled:opacity-75"
            >
              {is2faVerifying ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                  <span>Verifying...</span>
                </>
              ) : (
                <>
                  <span>Verify & Sign In</span>
                  <span>→</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={() => {
                clearPending2FAToken();
                navigate({ to: "/login" });
              }}
              className="flex items-center justify-center gap-1.5 text-xs font-bold text-on-surface-variant hover:text-primary transition-colors cursor-pointer w-full"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to credentials login</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
