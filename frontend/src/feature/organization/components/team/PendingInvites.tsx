import { useState } from "react";
import { ChevronRight, Clock, Loader2, RotateCcw, X } from "lucide-react";
import type { OrganizationInvitation } from "../../types/organization.types";
import { useResendInvitation, useRevokeInvitation } from "../../hooks/useInvitations";
import { ConfirmDialog } from "../../../../shared/components/ConfirmDialog";
import { useToast } from "../../../../shared/hooks/useToast";
import { getApiErrorMessage } from "../../../../shared/utils/apiError";

const formatRelativeInviteTime = (isoDate?: string | null): string => {
  if (!isoDate) return "recently";
  const timestamp = new Date(isoDate).getTime();
  if (!Number.isFinite(timestamp)) return "recently";

  // Clamp small server/client clock differences so users never see negative time.
  const diffMs = Math.max(0, Date.now() - timestamp);
  const minutes = Math.floor(diffMs / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  const days = Math.floor(hours / 24);
  if (days === 1) return "yesterday";
  return `${days} days ago`;
};

interface PendingInviteRowProps {
  invitation: OrganizationInvitation;
}

const PendingInviteRow = ({ invitation }: PendingInviteRowProps) => {
  const resendMutation = useResendInvitation();
  const revokeMutation = useRevokeInvitation();
  const { showToast } = useToast();
  const [confirmOpen, setConfirmOpen] = useState(false);

  const handleResend = async () => {
    try {
      await resendMutation.mutateAsync(invitation.uuid);
      showToast(`Invitation resent to ${invitation.email}.`, "success");
    } catch (error) {
      showToast(getApiErrorMessage(error, "Invitation could not be resent."), "error");
    }
  };

  const handleRevoke = async () => {
    try {
      await revokeMutation.mutateAsync(invitation.uuid);
      setConfirmOpen(false);
      showToast("Invitation cancelled successfully.", "success");
    } catch (error) {
      showToast(getApiErrorMessage(error, "Invitation could not be cancelled."), "error");
    }
  };

  const sentAt = invitation.updated_at ?? invitation.created_at;

  return (
    <div className="border-b border-[#EEEEEE] py-3 last:border-0">
      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={(open) => {
          if (!revokeMutation.isPending) setConfirmOpen(open);
        }}
        title="Cancel invitation?"
        description={`Cancel the pending invitation for ${invitation.email}? The existing invite link will stop working.`}
        confirmLabel="Cancel invitation"
        isLoading={revokeMutation.isPending}
        onConfirm={handleRevoke}
      />

      <div className="mb-1.5 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-xs font-semibold text-[#1A1C1C]" title={invitation.email}>{invitation.email}</p>
          <p className="text-[11px] capitalize text-[#4C4736]">{invitation.role_code}</p>
        </div>
        <span className="flex-shrink-0 whitespace-nowrap text-[11px] text-[#4C4736]">
          Invited {formatRelativeInviteTime(sentAt)}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={handleResend}
          disabled={resendMutation.isPending || revokeMutation.isPending}
          className="flex items-center gap-1 text-[11px] font-semibold text-[#8F740D] hover:underline disabled:cursor-not-allowed disabled:opacity-50"
          aria-label={`Resend invitation to ${invitation.email}`}
        >
          {resendMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <RotateCcw className="h-3 w-3" />}
          {resendMutation.isPending ? "Resending…" : "Resend"}
        </button>
        <button
          type="button"
          onClick={() => setConfirmOpen(true)}
          disabled={revokeMutation.isPending || resendMutation.isPending}
          className="flex items-center gap-1 text-[11px] font-semibold text-red-500 hover:underline disabled:opacity-50"
          aria-label={`Cancel invitation to ${invitation.email}`}
        >
          <X className="h-3 w-3" />
          Cancel
        </button>
      </div>
    </div>
  );
};

interface PendingInvitesProps {
  invitations: OrganizationInvitation[];
}

export const PendingInvites = ({ invitations }: PendingInvitesProps) => {
  const pending = invitations.filter((inv) => inv.status === "pending");

  return (
    <div className="mt-4 space-y-4 rounded-2xl border border-[#CEC6B0]/40 bg-white p-5">
      <div className="flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#F4F3F3]">
          <Clock className="h-4 w-4 text-[#8F740D]" />
        </div>
        <span className="text-sm font-semibold text-[#1A1C1C]">Pending invites</span>
      </div>

      {pending.length === 0 ? (
        <p className="py-4 text-center text-xs text-[#4C4736]">No pending invitations.</p>
      ) : (
        <>
          {pending.slice(0, 3).map((inv) => (
            <PendingInviteRow key={inv.uuid} invitation={inv} />
          ))}

          {pending.length > 3 && (
            <button type="button" className="flex w-full items-center justify-between pt-1 text-xs font-semibold text-[#8F740D] hover:underline">
              View all pending invites
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          )}
        </>
      )}
    </div>
  );
};
