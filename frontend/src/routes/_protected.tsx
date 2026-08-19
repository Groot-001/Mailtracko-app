import { Outlet, createFileRoute, redirect } from "@tanstack/react-router";
import { checkAuth } from "../feature/login/checkAuth";
import { getOnboardingStatus } from "../feature/organization/api/organizationApi";
import { ProductShell } from "../shared/components/ProductShell";
import { getPlatformAccess } from "../feature/platform/api/platformApi";

export const Route = createFileRoute("/_protected")({
  beforeLoad: async ({ location }) => {
    // 1. Check authentication
    const user = await checkAuth();

    if (!user) {
      throw redirect({
        to: "/login",
      });
    }

    // Platform administrators may be dedicated operator accounts with no
    // customer workspace. They must still be able to reach /admin directly.
    try {
      const access = await getPlatformAccess();
      if (access.is_platform_admin) {
        if (location.pathname.startsWith("/admin")) return;
        if (!access.organization_uuid) {
          throw redirect({ to: "/admin", replace: true });
        }
      }
    } catch (error: unknown) {
      if (typeof error === "object" && error !== null && "to" in error) {
        throw error;
      }
      // Normal users without a workspace can legitimately receive a 403 here;
      // onboarding status below remains the source of truth for them.
    }

    // 2. Check onboarding status — skip if user is already heading to onboarding
    if (location.pathname.startsWith("/onboarding")) {
      return;
    }

    try {
      const status = await getOnboardingStatus();

      if (status.needs_onboarding) {
        throw redirect({
          to: "/onboarding",
        });
      }
    } catch (error: unknown) {
      // If it's a redirect, re-throw it
      if (error instanceof Error && "to" in error) {
        throw error;
      }
      // If the onboarding-status API fails (e.g. user has no org yet),
      // redirect to onboarding as a safe default
      if (
        typeof error === "object" &&
        error !== null &&
        "statusCode" in error
      ) {
        throw error; // re-throw TanStack redirect objects
      }
      throw redirect({
        to: "/onboarding",
      });
    }
  },

  component: ProtectedLayout,
});

function ProtectedLayout() {
  return (
    <ProductShell>
      <Outlet />
    </ProductShell>
  );
}
