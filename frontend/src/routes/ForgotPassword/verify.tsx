import { useEffect, useState } from "react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { z } from "zod";
import { ArrowLeft, Eye, EyeOff, Loader2, Lock, ShieldCheck } from "lucide-react";
import {
  forgotPassword,
  resetForgotPassword,
  verifyForgotPasswordCode,
} from "../../feature/login/api/forgotPasswordApi";
import { getApiErrorMessage, getApiFieldErrors } from "../../shared/utils/apiError";
import { useToast } from "../../shared/hooks/useToast";

const RESET_CHALLENGE_KEY = "mailtracko_password_reset_challenge";
const verifySearchSchema = z.object({
  email: z.string().email().catch(""),
  step: z.enum(["verify", "password"]).optional().catch("verify"),
});

export const Route = createFileRoute("/ForgotPassword/verify")({
  validateSearch: verifySearchSchema,
  component: VerifyForgotPasswordPage,
});

const PASSWORD_MIN_LENGTH = 12;
const PASSWORD_MAX_LENGTH = 128;
const validatePasswordStrength = (password: string): string | null => {
  if (password.length < PASSWORD_MIN_LENGTH) return "Password must be at least 12 characters";
  if (password.length > PASSWORD_MAX_LENGTH) return "Password cannot exceed 128 characters";
  if (!/[A-Z]/.test(password)) return "Password must contain at least one uppercase letter";
  if (!/[a-z]/.test(password)) return "Password must contain at least one lowercase letter";
  if (!/\d/.test(password)) return "Password must contain at least one number";
  if (!/[!@#$%^&*()_+\-=[\]{}|;':",./<>?`~]/.test(password)) return "Password must contain at least one special character";
  return null;
};

function VerifyForgotPasswordPage() {
  const { email, step = "verify" } = Route.useSearch();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [serverError, setServerError] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [confirmError, setConfirmError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  const reset_challenge =
    typeof window !== "undefined" ? window.sessionStorage.getItem(RESET_CHALLENGE_KEY) : null;

  useEffect(() => {
    if (resendCooldown <= 0) return;
    const timer = window.setInterval(
      () => setResendCooldown((value) => Math.max(0, value - 1)),
      1000,
    );
    return () => window.clearInterval(timer);
  }, [resendCooldown]);

  useEffect(() => {
    // Do not render the password form from a direct URL without a server-issued challenge.
    if (step === "password" && !reset_challenge) {
      setServerError("Your password reset session has expired. Verify a new security code.");
      void navigate({
        to: "/ForgotPassword/verify",
        search: { email, step: "verify" },
        replace: true,
      });
    }
  }, [email, navigate, reset_challenge, step]);

  const updateOtp = (index: number, value: string) => {
    if (!/^\d?$/.test(value)) return;
    const next = [...otp];
    next[index] = value;
    setOtp(next);
    setServerError(null);
    if (value && index < 5) document.getElementById(`reset-otp-${index + 1}`)?.focus();
  };

  const handleOtpKeyDown = (index: number, event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Backspace" && !otp[index] && index > 0) {
      document.getElementById(`reset-otp-${index - 1}`)?.focus();
    }
  };

  const handlePaste = (event: React.ClipboardEvent<HTMLInputElement>) => {
    const value = event.clipboardData.getData("text").trim();
    if (/^\d{6}$/.test(value)) {
      setOtp(value.split(""));
      setServerError(null);
      document.getElementById("reset-otp-5")?.focus();
    }
    event.preventDefault();
  };

  const verifyCode = async (event: React.FormEvent) => {
    event.preventDefault();
    const token = otp.join("");
    if (!/^\d{6}$/.test(token)) {
      setServerError("Enter the complete 6-digit security code.");
      return;
    }
    setIsVerifying(true);
    setServerError(null);
    try {
      const result = await verifyForgotPasswordCode({ token });
      window.sessionStorage.setItem(RESET_CHALLENGE_KEY, result.reset_challenge);
      showToast("Security code verified. Create your new password.", "success");
      await navigate({
        to: "/ForgotPassword/verify",
        search: { email, step: "password" },
        replace: true,
      });
    } catch (error) {
      setServerError(getApiErrorMessage(error, "Invalid or expired security code."));
      setOtp(["", "", "", "", "", ""]);
      document.getElementById("reset-otp-0")?.focus();
    } finally {
      setIsVerifying(false);
    }
  };

  const resendCode = async () => {
    if (!email || resendCooldown > 0 || isResending) return;
    setIsResending(true);
    setServerError(null);
    try {
      await forgotPassword({ email });
      setResendCooldown(60);
      showToast("A new security code has been sent.", "success");
    } catch (error) {
      setServerError(getApiErrorMessage(error, "Could not resend the security code."));
    } finally {
      setIsResending(false);
    }
  };

  const resetPassword = async (event: React.FormEvent) => {
    event.preventDefault();
    const challenge = window.sessionStorage.getItem(RESET_CHALLENGE_KEY);
    if (!challenge) {
      setServerError("Your password reset session has expired. Verify a new security code.");
      return;
    }

    const strengthError = validatePasswordStrength(newPassword);
    setPasswordError(strengthError);
    const matchError = newPassword !== confirmPassword ? "Passwords do not match." : null;
    setConfirmError(matchError);
    if (strengthError || matchError) {
      setServerError(null);
      return;
    }

    setIsResetting(true);
    setServerError(null);
    try {
      await resetForgotPassword({ reset_challenge: challenge, new_password: newPassword });
      window.sessionStorage.removeItem(RESET_CHALLENGE_KEY);
      showToast("Password reset successfully. Please sign in.", "success");
      await navigate({ to: "/login" });
    } catch (error) {
      const fieldErrors = getApiFieldErrors(error);
      const newPasswordError = fieldErrors.new_password;
      if (newPasswordError) {
        setPasswordError(newPasswordError);
      } else {
        setServerError(getApiErrorMessage(error, "Password could not be reset."));
      }
    } finally {
      setIsResetting(false);
    }
  };

  const shell = (content: React.ReactNode) => (
    <div className="min-h-screen bg-surface flex items-center justify-center px-margin-mobile py-stack-lg">
      <div className="w-full max-w-115 overflow-hidden rounded-xl border border-[#CEC6B0]/40 bg-white shadow-lg">
        <div className="h-1 w-full bg-[#8F740D]" />
        <div className="space-y-6 p-6 sm:p-8">
          <div className="space-y-2 text-center">
            <h1 className="text-3xl font-extrabold tracking-tight text-on-surface">MailTracko</h1>
            <p className="text-xs font-medium text-on-surface-variant">Secure account recovery</p>
          </div>
          {content}
        </div>
      </div>
    </div>
  );

  if (step === "password" && reset_challenge) {
    return shell(
      <>
        <div className="space-y-2 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-emerald-200 bg-emerald-50">
            <ShieldCheck className="h-6 w-6 text-emerald-700" />
          </div>
          <h2 className="text-lg font-bold text-on-surface">Create New Password</h2>
          <p className="text-xs leading-relaxed text-on-surface-variant">
            Your security code is verified. Choose a strong new password for your account.
          </p>
        </div>
        {serverError ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs font-semibold text-red-700">{serverError}</p> : null}
        <form onSubmit={resetPassword} className="space-y-4">
          <PasswordField
            label="New Password"
            value={newPassword}
            onChange={(value) => {
              setNewPassword(value);
              setPasswordError(null);
            }}
            visible={showPassword}
            onToggle={() => setShowPassword((value) => !value)}
            error={passwordError}
          />
          <PasswordField
            label="Confirm Password"
            value={confirmPassword}
            onChange={(value) => {
              setConfirmPassword(value);
              setConfirmError(null);
            }}
            visible={showPassword}
            onToggle={() => setShowPassword((value) => !value)}
            error={confirmError}
          />
          <p className="text-[11px] leading-5 text-on-surface-variant">At least 12 characters with uppercase, lowercase, number, and special character.</p>
          <button type="submit" disabled={isResetting} className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-3 text-sm font-bold text-on-primary shadow-md transition hover:bg-[#6E5E00] disabled:opacity-60">
            {isResetting ? <><Loader2 className="h-4 w-4 animate-spin" /> Resetting...</> : "Reset Password"}
          </button>
        </form>
      </>,
    );
  }

  return shell(
    <>
      <div className="space-y-2 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-outline-variant/40 bg-surface-container-low">
          <ShieldCheck className="h-6 w-6 text-primary" />
        </div>
        <h2 className="text-lg font-bold text-on-surface">Verify Security Code</h2>
        <p className="text-xs leading-relaxed text-on-surface-variant">
          Enter the 6-digit code sent to <strong>{email || "your email"}</strong>.
        </p>
      </div>
      {serverError ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs font-semibold text-red-700">{serverError}</p> : null}
      <form onSubmit={verifyCode} className="space-y-5">
        <div className="flex justify-between gap-1.5 sm:gap-3">
          {otp.map((digit, index) => (
            <input
              key={index}
              id={`reset-otp-${index}`}
              type="text"
              inputMode="numeric"
              autoComplete={index === 0 ? "one-time-code" : "off"}
              maxLength={1}
              value={digit}
              disabled={isVerifying}
              onChange={(event) => updateOtp(index, event.target.value)}
              onKeyDown={(event) => handleOtpKeyDown(index, event)}
              onPaste={handlePaste}
              className="h-11 w-11 rounded-lg border border-[#CEC6B0] bg-surface-container-low text-center text-lg font-bold outline-none transition focus:border-primary focus:bg-white sm:h-14 sm:w-14 sm:text-xl"
            />
          ))}
        </div>
        <button type="submit" disabled={isVerifying} className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-3 text-sm font-bold text-on-primary shadow-md transition hover:bg-[#6E5E00] disabled:opacity-60">
          {isVerifying ? <><Loader2 className="h-4 w-4 animate-spin" /> Verifying...</> : "Verify Code"}
        </button>
      </form>
      <div className="text-center text-xs">
        <button type="button" onClick={() => void resendCode()} disabled={isResending || resendCooldown > 0} className="font-bold text-primary hover:underline disabled:opacity-50">
          {isResending ? "Sending..." : resendCooldown > 0 ? `Resend Code (${resendCooldown}s)` : "Resend Code"}
        </button>
      </div>
      <hr className="border-outline-variant/60" />
      <Link to="/login" className="flex items-center justify-center gap-1.5 text-xs font-bold text-on-surface-variant transition hover:text-primary">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Login
      </Link>
    </>,
  );
}

function PasswordField({
  label,
  value,
  onChange,
  visible,
  onToggle,
  error,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  visible: boolean;
  onToggle: () => void;
  error?: string | null;
}) {
  return (
    <label className="block space-y-1.5">
      <span className="block text-xs font-bold text-on-surface-variant">{label}</span>
      <div className="relative flex items-center">
        <Lock className="pointer-events-none absolute left-3 h-4 w-4 text-on-surface-variant" />
        <input
          type={visible ? "text" : "password"}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          autoComplete="new-password"
          maxLength={128}
          className="w-full rounded-lg border border-outline-variant/60 bg-surface-container-low py-2.5 pl-9 pr-10 text-sm text-on-surface outline-none transition focus:border-primary focus:bg-white"
        />
        <button type="button" onClick={onToggle} aria-label={visible ? "Hide password" : "Show password"} className="absolute right-3 text-on-surface-variant hover:text-primary">
          {visible ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
        </button>
      </div>
      {error && (
        <p className="text-xs text-red-600 font-medium">{error}</p>
      )}
    </label>
  );
}
