import { useMutation } from "@tanstack/react-query";
import { useOnboardingStore } from "../store/onboardingStore";
import { createOrganization } from "../api/onboardingApi";
import type { OnboardingState } from "../types/onboarding.types";
import { updateProfile } from "../../../shared/api/authApi";
import { useAuthStore } from "../../../shared/store/AuthStore";

export const useOnboarding = () => {
  const store = useOnboardingStore();

  const completeMutation = useMutation({
    mutationFn: async (finalState: OnboardingState) => {
      // Create the workspace first. A failed organization request must not leave
      // the user's personal theme partially changed while onboarding is still
      // incomplete.
      const created = await createOrganization(finalState);

      // Onboarding and backend now share one theme contract: light or dark.
      const theme = finalState.theme;
      try {
        const updatedUser = await updateProfile({ theme });
        useAuthStore.getState().setUser(updatedUser);
      } catch {
        // Workspace creation is authoritative. A profile-theme failure should not
        // create a duplicate organization if the user retries the final step.
      }
      return created;
    },
    onSuccess: () => {
      store.completeOnboarding();
      store.resetOnboarding(); // Clear store upon successful organization creation
    },
  });

  return {
    ...store,
    isSubmitting: completeMutation.isPending,
    finishOnboarding: () => {
      const finalState: OnboardingState = store.isSkipped
        ? {
            ...store,
            currentStep: 7,
            organization: {
              ...store.organization,
              organizationName: store.organization.organizationName.trim() || "My Workspace",
            },
            isCompleted: false,
          }
        : store;
      return completeMutation.mutateAsync(finalState);
    },
    // Skip only skips data entry. It never creates the workspace or enters the
    // dashboard by itself; the user must still reach Step 7 and explicitly
    // click Launch Workspace. Missing optional values are resolved only then.
    skipOnboarding: () => {
      store.setSkipped(true);
      store.setStep(7);
    },
  };
};
