import { createFileRoute, redirect } from "@tanstack/react-router";
import OnboardingLayout from "../../feature/onboarding/components/OnboardingLayout";
import { checkAuth } from "../../feature/login/checkAuth";
import { getOnboardingStatus } from "../../feature/organization/api/organizationApi";
import { getPlatformAccess } from "../../feature/platform/api/platformApi";

export const Route = createFileRoute("/onboarding")({
  beforeLoad: async () => {
    const user = await checkAuth();
    if (!user) {
      throw redirect({ to: "/login" });
    }

    // Dedicated platform administrators do not need a customer workspace.
    try {
      const access = await getPlatformAccess();
      if (access.is_platform_admin && !access.organization_uuid) {
        throw redirect({ to: "/admin", replace: true });
      }
    } catch (error: unknown) {
      if (typeof error === "object" && error !== null && "to" in error) throw error;
    }

    // Completed onboarding is authoritative server state. Browser history must
    // never trap an existing workspace on the setup wizard.
    try {
      const status = await getOnboardingStatus();
      if (status.has_completed_onboarding && status.organization_uuid) {
        throw redirect({ to: "/dashboard", replace: true });
      }
    } catch (error: unknown) {
      if (typeof error === "object" && error !== null && "to" in error) {
        throw error;
      }
      // New users can continue onboarding if the status endpoint is temporarily
      // unavailable; the launch handler performs another authoritative check.
    }
  },
  component: OnboardingLayout,
});
