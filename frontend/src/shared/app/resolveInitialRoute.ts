import type { ApplicationState } from "./bootstrap";

export function resolveInitialRoute({ onboarding }: ApplicationState): string {
  if (onboarding.has_pending_invitation) {
    // Route authenticated users through the canonical protected entry point.
    // This protected route can retry a token retained from the invitation link.
    return "/pending-invitation";
  }

  if (onboarding.has_completed_onboarding) {
    return "/dashboard";
  }

  return "/onboarding";
}
