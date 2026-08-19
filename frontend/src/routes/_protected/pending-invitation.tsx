import { useEffect, useState } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { CheckCircle2, Loader2, MailWarning } from "lucide-react";
import {
  completePendingInvitation,
  getPendingInvitationToken,
} from "../../shared/auth/pendingInvitation";
import { getApiErrorMessage } from "../../shared/utils/apiError";

export const Route = createFileRoute("/_protected/pending-invitation")({
  component: PendingInvitationPage,
});

function PendingInvitationPage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<"checking" | "missing" | "failed">(() => {
    return getPendingInvitationToken() ? "checking" : "missing";
  });
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getPendingInvitationToken();
    if (!token) {
      return;
    }

    completePendingInvitation()
      .then((accepted) => {
        if (accepted) {
          navigate({ to: "/dashboard", replace: true });
          return;
        }
        setStatus("missing");
      })
      .catch((reason) => {
        setError(getApiErrorMessage(reason, "The invitation could not be accepted."));
        setStatus("failed");
      });
  }, [navigate]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-surface px-4 py-10">
      <section className="w-full max-w-lg rounded-2xl border border-[#CEC6B0]/40 bg-white p-8 text-center shadow-lg">
        {status === "checking" ? (
          <>
            <Loader2 className="mx-auto h-9 w-9 animate-spin text-[#8F740D]" />
            <h1 className="mt-5 text-xl font-bold text-[#1A1C1C]">Accepting invitation</h1>
            <p className="mt-2 text-sm text-[#6F6857]">Please wait while MailTracko connects your account to the organization.</p>
          </>
        ) : (
          <>
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#F8F0D7]">
              {status === "failed" ? (
                <MailWarning className="h-7 w-7 text-[#8F740D]" />
              ) : (
                <CheckCircle2 className="h-7 w-7 text-[#8F740D]" />
              )}
            </div>
            <h1 className="mt-5 text-xl font-bold text-[#1A1C1C]">Pending organization invitation</h1>
            <p className="mt-2 text-sm leading-6 text-[#6F6857]">
              {status === "failed"
                ? error
                : "Open the original invitation email and use its Accept Invitation link. The secure token is required to join the organization."}
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-6 rounded-xl bg-[#8F740D] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#735D0B]"
            >
              Retry
            </button>
          </>
        )}
      </section>
    </main>
  );
}
