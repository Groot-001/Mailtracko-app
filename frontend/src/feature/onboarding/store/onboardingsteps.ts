import type { StepMeta } from "../types/onboarding.types";

export const ONBOARDING_STEPS: StepMeta[] = [
  { id: 1, label: "Welcome", shortDescription: "Get started" },
  { id: 2, label: "Workspace", shortDescription: "Workspace details" },
  {
    id: 3,
    label: "Email Volume",
    shortDescription: "Expected sending volume",
  },
  { id: 4, label: "Industry Sector", shortDescription: "Choose your industry" },
  { id: 5, label: "Source", shortDescription: "Help us understand you" },
  {
    id: 6,
    label: "Theme Selection",
    shortDescription: "Personalize your experience",
  },
  { id: 7, label: "Review & Finish", shortDescription: "Confirm and launch" },
];
