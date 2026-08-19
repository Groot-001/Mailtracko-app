import { useState, useEffect } from "react";
import { useVerifySMTP, useResendCode } from "../hooks/useEmailAccounts";
import { Loader2, Mail } from "lucide-react";
import { getApiErrorMessage } from "../../../shared/utils/apiError";

interface VerifyCodeModalProps {
  uuid: string;
  email: string;
  onClose: () => void;
  onSuccess: () => void;
}

export const VerifyCodeModal = ({ uuid, email, onClose, onSuccess }: VerifyCodeModalProps) => {
  const verifyMutation = useVerifySMTP();
  const resendMutation = useResendCode();

  const [code, setCode] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Timer state for resend cooldown (60 seconds)
  const [cooldown, setCooldown] = useState(0);
  const [resendAttempts, setResendAttempts] = useState(0);

  useEffect(() => {
    if (cooldown > 0) {
      const timer = setInterval(() => setCooldown((c) => c - 1), 1000);
      return () => clearInterval(timer);
    }
  }, [cooldown]);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (code.trim().length !== 6) {
      setErrorMessage("Verification code must be exactly 6 characters.");
      return;
    }

    setErrorMessage(null);
    try {
      await verifyMutation.mutateAsync({
        uuid,
        payload: { code: code.toUpperCase().trim() },
      });
      onSuccess();
    } catch (err: unknown) {
      setErrorMessage(getApiErrorMessage(err, "Invalid verification code."));
    }
  };

  const handleResend = async () => {
    if (cooldown > 0) return;
    if (resendAttempts >= 3) {
      setErrorMessage("Maximum resend attempts reached.");
      return;
    }

    setErrorMessage(null);
    try {
      await resendMutation.mutateAsync(uuid);
      setCooldown(60);
      setResendAttempts((a) => a + 1);
    } catch (err: unknown) {
      setErrorMessage(getApiErrorMessage(err, "Failed to resend code."));
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl shadow-xl max-w-sm w-full p-6 space-y-5 relative animate-in zoom-in-95 duration-200">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-[#4C4736] hover:text-[#1A1C1C] text-sm"
        >
          ✕
        </button>

        {/* Title */}
        <div className="text-center space-y-1">
          <div className="w-10 h-10 bg-[#F1D442]/20 border border-[#F1D442]/50 text-[#8F740D] rounded-full flex items-center justify-center mx-auto mb-2">
            <Mail className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-[#1A1C1C]">Verify SMTP Account</h3>
          <p className="text-xs text-[#4C4736] leading-relaxed">
            We sent a 6-character code to <strong>{email}</strong>. Enter it below to activate this sender domain.
          </p>
        </div>

        <form onSubmit={handleVerify} className="space-y-4">
          <div className="space-y-1.5">
            <input
              type="text"
              required
              maxLength={6}
              placeholder="A1B2C3"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              className="w-full text-center tracking-widest text-lg font-mono font-extrabold px-3 py-2.5 rounded-xl border border-[#CEC6B0]/60 focus:outline-none focus:ring-1 focus:ring-[#F1D442]/30 focus:border-[#8F740D]"
            />
          </div>

          {errorMessage && (
            <p className="text-xs text-red-500 text-center font-medium leading-relaxed">
              {errorMessage}
            </p>
          )}

          {/* Resend Action */}
          <div className="text-center text-xs">
            {cooldown > 0 ? (
              <span className="text-[#4C4736]">
                Resend code in <strong className="text-[#1A1C1C]">{cooldown}s</strong>
              </span>
            ) : (
              <button
                type="button"
                onClick={handleResend}
                disabled={resendAttempts >= 3 || resendMutation.isPending}
                className="text-[#8F740D] hover:underline font-bold disabled:opacity-50 disabled:no-underline"
              >
                {resendMutation.isPending ? "Resending..." : "Resend verification code"}
              </button>
            )}
            {resendAttempts > 0 && resendAttempts < 3 && (
              <p className="text-[10px] text-[#4C4736] mt-0.5">Attempt {resendAttempts} of 3</p>
            )}
          </div>

          {/* Buttons */}
          <div className="flex gap-2.5 pt-2 border-t border-[#F4F3F3]">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 border border-[#CEC6B0]/60 rounded-xl text-xs font-bold text-[#1A1C1C] hover:bg-[#F4F3F3]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={verifyMutation.isPending}
              className="flex-1 py-2 bg-[#8F740D] hover:bg-[#6A5B00] text-white text-xs font-bold rounded-xl flex items-center justify-center gap-1.5"
            >
              {verifyMutation.isPending ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" /> Verifying...
                </>
              ) : (
                "Verify Code"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
