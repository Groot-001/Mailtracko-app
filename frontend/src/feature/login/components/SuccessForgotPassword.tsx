import { Check, ArrowLeft } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { useForgotPassword } from "../hooks/useForgotPassword";

export default function SuccessForgotPassword({ email }: { email?: string }) {
  const { mutate, isPending } = useForgotPassword();

  const handleResend = () => {
    if (!email) return;
    mutate({ email });
  };

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-margin-mobile py-stack-lg">
      <div className="w-full max-w-md relative">
        {/* Top accent bar */}
        <div className="h-1 rounded-t-xl bg-linear-to-r from-primary via-primary-fixed-dim to-primary" />

        <div className="bg-surface-container-lowest rounded-b-xl shadow-lg border border-[#CEC6B0]/40 px-gutter py-stack-lg text-center space-y-5">
          <div className="space-y-1">
            <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">MailTracko</h1>
            <p className="text-xs text-on-surface-variant font-medium">
              Recover your enterprise account access.
            </p>
          </div>

          <div className="w-14 h-14 mx-auto rounded-xl bg-surface-container-low flex items-center justify-center border border-outline-variant/30 shadow-inner">
            <Check className="w-6 h-6 text-primary" strokeWidth={3} />
          </div>

          <div className="space-y-2">
            <h2 className="text-lg font-bold text-on-surface">
              Check your email
            </h2>
            <p className="text-xs text-on-surface-variant leading-relaxed px-2">
              We've sent a password reset link to{" "}
              {email ? (
                <span className="font-bold text-on-surface block sm:inline break-all">{email}</span>
              ) : (
                "the address you provided"
              )}. Please
              check your inbox and follow the instructions.
            </p>
          </div>

          <p className="text-xs text-on-surface-variant">
            Didn't receive the email?{" "}
            <button
              type="button"
              onClick={handleResend}
              disabled={isPending || !email}
              className="font-bold text-primary hover:text-[#6E5E00] underline cursor-pointer"
            >
              {isPending ? "Sending..." : "Click to resend"}
            </button>
          </p>

          <hr className="border-outline-variant/60" />

          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 text-xs font-bold text-on-surface-variant hover:text-primary transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Login</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
