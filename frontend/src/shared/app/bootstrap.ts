import { checkAuth } from "../../feature/login/checkAuth";
import type { User } from "../../feature/login/types/user";
import { getOnboardingStatus } from "../../feature/organization/api/organizationApi";
import type { OnboardingStatus } from "../../feature/organization/api/organizationApi";

export interface ApplicationState {
  user: User;
  onboarding: OnboardingStatus;
}

export async function bootstrapApp(): Promise<ApplicationState | null> {
  const user = await checkAuth();

  if (!user) {
    return null;
  }

  const onboarding = await getOnboardingStatus();

  return {
    user,
    onboarding,
  };
}
