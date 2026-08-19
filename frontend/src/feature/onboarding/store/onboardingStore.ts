import { create } from "zustand";
import { persist } from "zustand/middleware";
import type {
  OnboardingState,
  OrganizationData,
  ThemeOption,
} from "../types/onboarding.types";

interface OnboardingStore extends OnboardingState {
  setStep: (step: number) => void;
  nextStep: () => void;
  prevStep: () => void;
  updateOrganization: (data: Partial<OrganizationData>) => void;
  setMonthlyEmailVolume: (volume: string) => void;
  setIndustrySector: (sector: string) => void;
  setSource: (source: string) => void;
  setTheme: (theme: ThemeOption) => void;
  completeOnboarding: () => void;
  setSkipped: (skipped: boolean) => void;
  resetOnboarding: () => void;
}

const initialOrganization: OrganizationData = {
  organizationName: "",
  websiteUrl: "",
  organizationSize: "",
  companyEmailDomain: "",
  description: "",
};

const initialState: OnboardingState = {
  currentStep: 1,
  organization: initialOrganization,
  monthlyEmailVolume: "",
  industrySector: "",
  source: "",
  theme: "light",
  isCompleted: false,
  isSkipped: false,
};

export const useOnboardingStore = create<OnboardingStore>()(
  persist(
    (set) => ({
      ...initialState,
      setStep: (step) => set({ currentStep: Math.min(Math.max(step, 1), 7) }),
      nextStep: () => set((state) => ({ currentStep: Math.min(state.currentStep + 1, 7) })),
      prevStep: () => set((state) => ({ currentStep: Math.max(state.currentStep - 1, 1) })),
      updateOrganization: (data) => set((state) => ({ organization: { ...state.organization, ...data } })),
      setMonthlyEmailVolume: (volume) => set({ monthlyEmailVolume: volume }),
      setIndustrySector: (sector) => set({ industrySector: sector }),
      setSource: (source) => set({ source }),
      setTheme: (theme) => set({ theme }),
      completeOnboarding: () => set({ isCompleted: true }),
      setSkipped: (skipped) => set({ isSkipped: skipped }),
      resetOnboarding: () => set({ ...initialState }),
    }),
    {
      name: "mailtracko-onboarding-storage",
      version: 2,
      migrate: (persisted) => {
        const state = (persisted ?? {}) as Omit<Partial<OnboardingState>, "theme"> & { theme?: string };
        return {
          ...initialState,
          ...state,
          organization: { ...initialOrganization, ...(state.organization ?? {}) },
          theme: state.theme === "dark" || state.theme === "midnight-focus" ? "dark" : "light",
        };
      },
    },
  ),
);
