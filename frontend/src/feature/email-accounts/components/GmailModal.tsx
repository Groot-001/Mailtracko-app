import { useConnectOAuth } from "../hooks/useEmailAccounts";
import { GoogleIcon } from "./shared/ProviderIcons";
import { CheckCircle2, Info, Loader2 } from "lucide-react";
import { getApiErrorMessage } from "../../../shared/utils/apiError";
import { useToast } from "../../../shared/hooks/useToast";
import { useQuery } from "@tanstack/react-query";
import { getPlatformAccess } from "../../platform/api/platformApi";

interface GmailModalProps {
  onClose: () => void;
  onBack: () => void;
  onSuccess: (url: string) => void;
}

export const GmailModal = ({ onClose, onBack, onSuccess }: GmailModalProps) => {
  const connectMutation = useConnectOAuth();
  const { showToast } = useToast();
  const access = useQuery({
    queryKey: ["platform", "access"],
    queryFn: getPlatformAccess,
    staleTime: 5 * 60 * 1000,
  });
  const gmailConfigured = access.data?.integrations?.gmail_sender_configured !== false;

  const handleSignIn = async () => {
    if (!gmailConfigured) {
      showToast(
        "Google sender connection is not configured for this MailTracko environment. Contact your administrator.",
        "error",
      );
      return;
    }
    try {
      const res = await connectMutation.mutateAsync({ provider: "gmail" });
      onSuccess(res.authorization_url);
    } catch (err: unknown) {
      showToast(getApiErrorMessage(err, "Failed to initiate Google sign-in."), "error");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl shadow-xl max-w-md w-full p-6 space-y-6 relative animate-in zoom-in-95 duration-200">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-[#4C4736] hover:text-[#1A1C1C] text-sm"
        >
          ✕
        </button>

        {/* Title & Icon */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 bg-slate-50 border border-[#CEC6B0]/40 rounded-xl flex items-center justify-center mx-auto">
            <GoogleIcon className="w-7 h-7" />
          </div>
          <h3 className="text-base font-bold text-[#1A1C1C]">Connect Google Workspace</h3>
          <p className="text-xs text-[#4C4736] leading-relaxed max-w-xs mx-auto">
            Authenticate securely with Google to enable MailTracko to manage campaigns directly from your inbox.
          </p>
        </div>

        {/* Sign In Button */}
        <div className="flex flex-col items-center justify-center pt-2">
          <button
            onClick={handleSignIn}
            disabled={connectMutation.isPending || !gmailConfigured}
            className="flex items-center justify-center gap-2.5 px-6 py-2.5 bg-white border border-[#CEC6B0]/80 hover:bg-slate-50 text-[#1A1C1C] font-semibold text-xs rounded-xl shadow-sm transition-all disabled:opacity-50"
          >
            {connectMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin text-[#8F740D]" />
            ) : (
              <GoogleIcon className="w-4 h-4" />
            )}
            Sign in with Google
          </button>
          {!gmailConfigured ? (
            <p className="mt-2 max-w-xs text-center text-[11px] font-medium text-amber-700">
              Google sender connection is unavailable until an administrator configures Google OAuth.
            </p>
          ) : null}
        </div>

        {/* Requirements Details Card */}
        <div className="bg-[#F9F9F9] border border-[#EEEEEE] rounded-xl p-4 space-y-3.5 text-xs text-[#4C4736]">
          <p className="font-bold text-[10px] text-[#1A1C1C] uppercase tracking-wider">
            MailTracko requires access to:
          </p>
          <div className="flex gap-2.5 items-start">
            <CheckCircle2 className="w-4.5 h-4.5 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-[#1A1C1C]">Send emails on your behalf</p>
              <p className="text-[10px] mt-0.5">Required to execute automated email campaigns.</p>
            </div>
          </div>
          <div className="flex gap-2.5 items-start">
            <CheckCircle2 className="w-4.5 h-4.5 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-[#1A1C1C]">Basic Google profile</p>
              <p className="text-[10px] mt-0.5">Used to identify the connected sender account. MailTracko does not request inbox-reading access.</p>
            </div>
          </div>
          <div className="flex gap-2 items-start border-t border-[#EEEEEE] pt-3 text-[10px]">
            <Info className="w-4 h-4 text-[#8F740D] shrink-0 mt-0.5" />
            <p>We never read your personal emails or delete messages.</p>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex gap-3 justify-between pt-2 border-t border-[#F4F3F3]">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-[#4C4736] hover:underline"
          >
            Cancel
          </button>
          <button
            onClick={onBack}
            className="px-4 py-2 border border-[#CEC6B0]/60 rounded-xl text-xs font-semibold hover:bg-[#F4F3F3]"
          >
            ← Back
          </button>
        </div>
      </div>
      
    </div>
  );
};
