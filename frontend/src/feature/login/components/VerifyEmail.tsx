import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Route as VerifyEmailRoute } from "../../../routes/verify-email";
import { Link, useNavigate } from "@tanstack/react-router";
import { useVerifyEmail } from "../hooks/useverifyEmail";
import {
  verifyEmailSchema,
  type VerifyEmailFormData,
} from "../schema/VerifyEmailSchema";
import { ShieldCheck, ArrowLeft, Loader2 } from "lucide-react";
import { resendVerificationEmail } from "../api/verifyEmailApi";
import { getApiErrorMessage } from "../../../shared/utils/apiError";
import { useToast } from "../../../shared/hooks/useToast";

export default function VerifyEmail() {
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [serverError, setServerError] = useState<string | null>(null);
  const [verified, setVerified] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);

  const { email } = VerifyEmailRoute.useSearch();
  const navigate = useNavigate();
  const { mutate, isPending } = useVerifyEmail();
  const { showToast } = useToast();

  const {
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<VerifyEmailFormData>({
    resolver: zodResolver(verifyEmailSchema),
    defaultValues: {
      token: "",
    },
  });

  useEffect(() => {
    if (resendCooldown <= 0) return;
    const timer = setInterval(() => {
      setResendCooldown((value) => Math.max(0, value - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [resendCooldown]);

  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d?$/.test(value)) return;

    const updatedOtp = [...otp];
    updatedOtp[index] = value;

    setOtp(updatedOtp);
    setValue("token", updatedOtp.join(""));
    setServerError(null);

    if (value && index < 5) {
      document.getElementById(`otp-${index + 1}`)?.focus();
    }
  };

  const handleKeyDown = (
    index: number,
    e: React.KeyboardEvent<HTMLInputElement>,
  ) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      document.getElementById(`otp-${index - 1}`)?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    const pasteData = e.clipboardData.getData("text");
    if (/^\d{6}$/.test(pasteData)) {
      const digits = pasteData.split("");
      setOtp(digits);
      setValue("token", pasteData);
      setServerError(null);
      document.getElementById("otp-5")?.focus();
    }
    e.preventDefault();
  };

  const onSubmit = (data: VerifyEmailFormData) => {
    mutate(data, {
      onSuccess: () => {
        setServerError(null);
        setVerified(true);
      },
      onError: (err: unknown) => {
        setVerified(false);
        setServerError(
          getApiErrorMessage(err, "Invalid or expired code. Please try again."),
        );
        setOtp(["", "", "", "", "", ""]);
        setValue("token", "");
        document.getElementById("otp-0")?.focus();
      },
    });
  };

  const handleResend = async () => {
    if (resendCooldown > 0) return;
    setIsResending(true);
    setServerError(null);
    try {
      await resendVerificationEmail(email);
      showToast("Verification code resent successfully", "success");
      setResendCooldown(60);
    } catch (err: unknown) {
      setServerError(
        getApiErrorMessage(err, "Failed to resend verification code. Please try again later."),
      );
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-margin-mobile py-stack-lg">
      {/* Notifications are rendered by the global top-right toast host. */}

      <div className="w-full max-w-115 rounded-xl border border-[#CEC6B0]/40 bg-white shadow-lg overflow-hidden">
        
        {/* Top Border Accent */}
        <div className="h-1 w-full bg-[#8F740D]" />

        <div className="p-6 sm:p-8 space-y-6">
          <div className="text-center space-y-2">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-xl bg-surface-container-low border border-outline-variant/30 shadow-inner">
              <ShieldCheck className="w-6 h-6 text-primary" />
            </div>
            <h1 className="text-3xl font-extrabold text-on-surface tracking-tight">
              MailTracko
            </h1>
          </div>

          {verified ? (
            <div className="text-center space-y-6">
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-5 text-xs sm:text-sm text-emerald-800 space-y-1">
                <p className="text-sm font-bold">
                  Email verified successfully!
                </p>
                <p className="opacity-90">
                  Your email <span className="font-bold break-all">{email}</span> has
                  been confirmed.
                </p>
              </div>

              <button
                type="button"
                onClick={() => navigate({ to: "/login" })}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary hover:bg-[#6E5E00] py-3 text-sm font-bold text-on-primary shadow-md hover:shadow-lg transition-all cursor-pointer"
              >
                Continue to Login
                <span>→</span>
              </button>
            </div>
          ) : (
            <>
              <div className="text-center space-y-2">
                <h2 className="text-lg font-bold text-on-surface">Verify your email</h2>
                <p className="text-xs text-on-surface-variant leading-relaxed max-w-xs mx-auto">
                  We've sent a 6-digit verification code to your email address. Please enter it below.
                </p>
              </div>

              {/* Centered raw email view, without edit button */}
              <div className="rounded-lg border border-outline-variant/50 bg-[#F9F9F9] px-4 py-3 text-xs sm:text-sm text-center">
                <span className="font-bold text-on-surface break-all">{email}</span>
              </div>

              {serverError && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs font-semibold text-red-600">
                  {serverError}
                </div>
              )}
              
              {errors.token && !serverError && (
                <p className="text-xs text-red-600 font-semibold text-center">
                  {errors.token.message}
                </p>
              )}

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                {/* OTP input boxes */}
                <div className="flex justify-between gap-1.5 sm:gap-3">
                  {otp.map((digit, index) => (
                    <input
                      key={index}
                      id={`otp-${index}`}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      disabled={isPending}
                      onChange={(e) => handleOtpChange(index, e.target.value)}
                      onKeyDown={(e) => handleKeyDown(index, e)}
                      onPaste={handlePaste}
                      className={`h-11 w-11 sm:h-14 sm:w-14 rounded-lg border text-center text-lg sm:text-xl font-bold outline-none bg-surface-container-low transition-all focus:bg-white focus:border-primary ${
                        serverError ? "border-red-400" : "border-[#CEC6B0]"
                      }`}
                    />
                  ))}
                </div>

                <button
                  type="submit"
                  disabled={isPending}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary hover:bg-[#6E5E00] py-3 text-sm font-bold text-on-primary shadow-md hover:shadow-lg transition-all cursor-pointer disabled:opacity-75"
                >
                  {isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin text-white" />
                      <span>Verifying...</span>
                    </>
                  ) : (
                    <>
                      <span>Verify & Continue</span>
                      <span>→</span>
                    </>
                  )}
                </button>
              </form>

              {/* Resend actions block without available-seconds label */}
              <div className="text-center space-y-2 text-xs">
                <p className="text-on-surface-variant">
                  Didn't receive the code?
                </p>
                <div className="flex justify-center items-center">
                  <button
                    type="button"
                    onClick={handleResend}
                    disabled={isResending || resendCooldown > 0}
                    className="font-bold text-primary hover:text-[#6E5E00] cursor-pointer hover:underline disabled:opacity-50"
                  >
                    {isResending
                      ? "Resending..."
                      : resendCooldown > 0
                        ? `Resend code (${resendCooldown}s)`
                        : "Resend code"}
                  </button>
                </div>
              </div>

              <hr className="border-outline-variant/60" />

              <Link
                to="/login"
                className="flex w-full items-center justify-center gap-1.5 text-xs font-bold text-on-surface-variant hover:text-primary transition-colors cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back to login</span>
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
