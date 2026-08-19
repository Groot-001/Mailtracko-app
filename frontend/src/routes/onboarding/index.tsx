import { createFileRoute } from "@tanstack/react-router";
import OnboardingLayout from "../../feature/onboarding/components/OnboardingLayout";

export const Route = createFileRoute("/onboarding/")({
  component: OnboardingLayout,
});
