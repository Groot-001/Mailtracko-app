import { useState } from "react";
import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { z } from "zod";
import { Loader2, AlertCircle, ShieldAlert } from "lucide-react";
import { declineInvite } from "../../feature/login/api/registerApi";
import { useInviteValidation } from "../../feature/login/hooks/useInviteValidation";
import { getApiErrorMessage } from "../../shared/utils/apiError";
import { forceNextLoginScreen } from "../../shared/auth/forceLogin";
import { clearPendingInvitationToken } from "../../shared/auth/pendingInvitation";

const declineSearchSchema = z.object({
  token: z.string().catch(""),
});

export const Route = createFileRoute("/invite/decline")({
  validateSearch: declineSearchSchema,
  component: InviteDeclinePage,
});

function InviteDeclinePage() {
  const { token } = Route.useSearch();
  const navigate = useNavigate();
  const { data, error: validationError, isValidating } = useInviteValidation(token)
  const orgName = data?.organization_name ?? null
  const invitedEmail = data?.email ?? null
  const validationErrorMessage = validationError ? getApiErrorMessage(validationError, 'Link expired or invalid. Please check the link or ask the organization owner for a new invite.') : null
  const [isDeclining, setIsDeclining] = useState(false);
  const [declineSuccess, setDeclineSuccess] = useState(false);
  const [declineError, setDeclineError] = useState<string | null>(null);

  // Validation is handled by `useInviteValidation`. When no token exists we render
  // a missing-token message directly during render.

  const handleConfirmDecline = async () => {
    if (!token) return;
    try {
      setIsDeclining(true);
      setDeclineError(null);
      await declineInvite(token);
      clearPendingInvitationToken();
      forceNextLoginScreen();
      setDeclineSuccess(true);
      navigate({ to: "/login", replace: true });
    } catch (error: unknown) {
      setDeclineError(getApiErrorMessage(error, 'Failed to decline the invitation.'))
    } finally {
      setIsDeclining(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center px-margin-mobile py-stack-lg">
        <div className="w-full max-w-120 bg-surface-container-lowest border border-red-200 rounded-xl shadow-lg p-8 flex flex-col items-center justify-center text-center space-y-4">
          <div className="text-red-600 bg-red-50 p-3 rounded-full border border-red-200">
            <AlertCircle className="w-8 h-8" />
          </div>
          <h2 className="text-lg font-bold text-on-surface">Invalid Invitation</h2>
          <p className="text-xs text-on-surface-variant max-w-sm leading-relaxed">
            No invitation token found in the URL. Please verify your invitation link.
          </p>
          <Link
            to="/login"
            className="mt-2 text-xs font-bold text-primary hover:underline"
          >
            Go to login
          </Link>
        </div>
      </div>
    )
  }

  if (isValidating) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center px-margin-mobile py-stack-lg">
        <div className="w-full max-w-120 bg-surface-container-lowest border border-[#CEC6B0]/40 rounded-xl shadow-lg p-8 flex flex-col items-center justify-center space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-sm font-semibold text-on-surface font-sans">Validating invitation details...</p>
        </div>
      </div>
    );
  }

  if (isDeclining) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center px-margin-mobile py-stack-lg">
        <div className="w-full max-w-120 bg-surface-container-lowest border border-[#CEC6B0]/40 rounded-xl shadow-lg p-8 flex flex-col items-center justify-center space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-sm font-semibold text-on-surface font-sans">Declining invitation...</p>
        </div>
      </div>
    );
  }

  if (validationErrorMessage) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center px-margin-mobile py-stack-lg">
        <div className="w-full max-w-120 bg-surface-container-lowest border border-red-200 rounded-xl shadow-lg p-8 flex flex-col items-center justify-center text-center space-y-4">
          <div className="text-red-600 bg-red-50 p-3 rounded-full border border-red-200">
            <AlertCircle className="w-8 h-8" />
          </div>
          <h2 className="text-lg font-bold text-on-surface">Invalid Invitation</h2>
          <p className="text-xs text-on-surface-variant max-w-sm leading-relaxed">
            {validationErrorMessage}
          </p>
          <Link
            to="/login"
            className="mt-2 text-xs font-bold text-primary hover:underline"
          >
            Go to login
          </Link>
        </div>
      </div>
    );
  }

  if (declineSuccess) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center px-margin-mobile py-stack-lg">
        <div className="w-full max-w-120 bg-surface-container-lowest border border-[#CEC6B0]/40 rounded-xl shadow-lg p-8 flex flex-col items-center justify-center text-center space-y-5">
          <div className="text-emerald-600 bg-emerald-50 p-3 rounded-full border border-emerald-200">
            <AlertCircle className="w-8 h-8 text-emerald-600" />
          </div>
          <h2 className="text-lg font-bold text-on-surface">Invitation Declined</h2>
          <p className="text-xs text-on-surface-variant max-w-sm leading-relaxed font-medium">
            You have declined the invitation to join <strong>{orgName}</strong>. If you want to continue, please sign in.
          </p>
          
          <button
            type="button"
            onClick={() => navigate({ to: "/login" })}
            className="w-full bg-primary hover:bg-[#6E5E00] text-on-primary rounded-lg py-2.5 text-sm font-bold shadow-md hover:shadow-lg transition-all cursor-pointer"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-margin-mobile py-stack-lg">
      <div className="w-full max-w-120 bg-surface-container-lowest border border-[#CEC6B0]/40 rounded-xl shadow-lg overflow-hidden">
        
        {/* Top Border Accent */}
        <div className="h-1 w-full bg-red-600" />

        <div className="p-8 space-y-6">
          <div className="text-center space-y-2">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-xl bg-red-50 border border-red-200/50 shadow-inner">
              <ShieldAlert className="w-6 h-6 text-red-600" />
            </div>
            <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">
              Decline Invitation
            </h1>
            <p className="text-xs text-on-surface-variant leading-relaxed max-w-xs mx-auto">
              Are you sure you want to decline the invitation to join <strong>{orgName}</strong> as <strong>{invitedEmail}</strong>?
            </p>
          </div>

          <div className="flex flex-col gap-2 pt-2">
            {declineError && <p role="alert" className="rounded-lg bg-red-50 p-3 text-xs text-red-700">{declineError}</p>}
            <button
              type="button"
              onClick={handleConfirmDecline}
              disabled={isDeclining}
              className="w-full bg-red-600 hover:bg-red-700 text-white rounded-lg py-2.5 text-sm font-bold shadow-md hover:shadow-lg transition-all cursor-pointer disabled:opacity-75"
            >
              {isDeclining ? "Declining..." : "Decline Invitation"}
            </button>
            
            <Link
              to="/invite"
              search={{ token }}
              disabled={isDeclining}
              className="w-full text-center text-xs font-bold text-on-surface-variant hover:text-on-surface py-2 transition-colors cursor-pointer"
            >
              Cancel
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
