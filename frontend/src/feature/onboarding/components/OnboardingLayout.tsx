import { useState } from "react";
import { Loader2 } from "lucide-react";
import { useNavigate } from "@tanstack/react-router";
import { OnboardingHeader } from "./OnboardingHeader";
import { OnboardingStepper } from "./OnboardingStepper";
import { Step1Welcome } from "./Step1Welcome";
import { Step2Organization } from "./Step2Organization";
import { Step3EmployeeCount } from "./Step3EmployeeCount";
import { Step4IndustrySector } from "./Step4IndustrySector";
import { Step5SourceDiscovery } from "./Step5SourceDiscovery";
import { Step6ThemeSelection } from "./Step6ThemeSelection";
import { Step7ReviewFinish } from "./Step7ReviewFinish";
import { useOnboarding } from "../hooks/useOnboarding";
import { getOnboardingStatus } from "../../organization/api/organizationApi";
import { getApiErrorMessage } from "../../../shared/utils/apiError";
import {
  organizationStepSchema,
  emailVolumeStepSchema,
  industrySectorStepSchema,
  sourceStepSchema,
  themeStepSchema,
} from "../schema/onboardingSchema";
import type {
  OrganizationData,
  ThemeOption,
} from "../types/onboarding.types";

export default function OnboardingLayout() {
  const navigate = useNavigate();
  const onboarding = useOnboarding();
  const [launchError, setLaunchError] = useState<string | null>(null);
  const [isLaunching, setIsLaunching] = useState(false);

  const handleStepClick = (step: number) => {
    // Clear any stale launch validation message as soon as the user leaves the
    // review step so an old error cannot linger over later edits.
    setLaunchError(null);
    if (step <= onboarding.currentStep) onboarding.setStep(step);
  };

  const handleSkipOnboarding = () => {
    setLaunchError(null);
    onboarding.skipOnboarding();
  };

  const handleLaunchWorkspace = async () => {
    setLaunchError(null);

    const validationSteps = [
      { step: 2, label: "Organization", result: organizationStepSchema.safeParse(onboarding.organization) },
      { step: 3, label: "Email volume", result: emailVolumeStepSchema.safeParse({ emailVolume: onboarding.monthlyEmailVolume }) },
      { step: 4, label: "Industry", result: industrySectorStepSchema.safeParse({ industrySector: onboarding.industrySector }) },
      { step: 5, label: "Discovery source", result: sourceStepSchema.safeParse({ source: onboarding.source }) },
      {
        step: 6,
        label: "Appearance",
        result: themeStepSchema.safeParse({ theme: onboarding.theme }),
      },
    ];

    if (!onboarding.isSkipped) {
      const invalid = validationSteps.find((item) => !item.result.success);
      if (invalid && !invalid.result.success) {
        const issue = invalid.result.error.issues[0];
        setLaunchError(`Step ${invalid.step} (${invalid.label}): ${issue?.message ?? "Please review this step."}`);
        onboarding.setStep(invalid.step);
        return;
      }
    }

    setIsLaunching(true);

    // Relaunch is intentionally idempotent. A completed user may arrive here
    // through browser Back/history or a stale onboarding tab; never try to
    // create a second organization in that case.
    try {
      const status = await getOnboardingStatus();
      if (status.has_completed_onboarding && status.organization_uuid) {
        await navigate({ to: "/dashboard", replace: true });
        return;
      }
    } catch {
      // A transient status failure should not prevent first-time onboarding.
    }

    try {
      await onboarding.finishOnboarding();
      await navigate({ to: "/dashboard", replace: true });
    } catch (error: unknown) {
      // If the create request actually completed but the client lost the
      // response, re-check authoritative server state before showing an error.
      try {
        const status = await getOnboardingStatus();
        if (status.has_completed_onboarding && status.organization_uuid) {
          await navigate({ to: "/dashboard", replace: true });
          return;
        }
      } catch {
        // Fall through to the actionable error message below.
      }
      const message = getApiErrorMessage(error, "Workspace launch failed. Please try again.");
      const normalized = message.toLowerCase();
      const inferredStep = normalized.includes("organization") || normalized.includes("domain") || normalized.includes("website")
        ? 2
        : normalized.includes("volume")
          ? 3
          : normalized.includes("industry") || normalized.includes("sector")
            ? 4
            : normalized.includes("source")
              ? 5
              : normalized.includes("theme") || normalized.includes("appearance")
                ? 6
                : 7;
      setLaunchError(`Step ${inferredStep}: ${message}`);
      if (inferredStep !== 7) onboarding.setStep(inferredStep);
      setIsLaunching(false);
    }
  };

  if (isLaunching) {
    return (
      <div className="flex min-h-screen w-full items-center justify-center bg-[#F9F9F9] px-6">
        <div role="status" aria-live="polite" className="w-full max-w-md rounded-2xl border border-[#CEC6B0]/50 bg-white p-8 text-center shadow-xl">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#F5E29F]/40">
            <Loader2 className="h-7 w-7 animate-spin text-[#8F740D]" />
          </div>
          <h1 className="mt-5 text-xl font-bold text-[#1A1C1C]">Preparing your workspace...</h1>
          <p className="mt-2 text-sm leading-6 text-[#4C4736]">We're applying your setup and loading your dashboard. This usually takes only a moment.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-[#F9F9F9] flex flex-col justify-between selection:bg-[#F5E29F] selection:text-[#8F740D]">
      {/* Top Header */}
      <OnboardingHeader
        onNeedHelp={() => {
          window.location.href = "mailto:support@mailtracko.com";
        }}
      />

      {/* Stepper Progress Bar */}
      <div className="bg-white border-b border-[#EEEEEE]">
        <OnboardingStepper
          currentStep={onboarding.currentStep}
          onStepClick={handleStepClick}
        />
      </div>

      {/* Main Content Area */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {onboarding.currentStep === 1 && (
          <Step1Welcome
            onGetStarted={() => { onboarding.setSkipped(false); onboarding.setStep(2); }}
            onSkip={handleSkipOnboarding}
          />
        )}

        {onboarding.currentStep === 2 && (
          <Step2Organization
            initialValues={onboarding.organization}
            onNext={(orgData: OrganizationData) => {
              onboarding.updateOrganization(orgData);
              onboarding.setStep(3);
            }}
            onBack={() => onboarding.setStep(1)}
          />
        )}

        {onboarding.currentStep === 3 && (
          <Step3EmployeeCount
            initialValue={onboarding.monthlyEmailVolume}
            onNext={(volume: string) => {
              onboarding.setMonthlyEmailVolume(volume);
              onboarding.setStep(4);
            }}
            onBack={() => onboarding.setStep(2)}
          />
        )}

        {onboarding.currentStep === 4 && (
          <Step4IndustrySector
            initialValue={onboarding.industrySector}
            currentStep={4}
            onNext={(sector: string) => {
              onboarding.setIndustrySector(sector);
              onboarding.setStep(5);
            }}
            onBack={() => onboarding.setStep(3)}
          />
        )}

        {onboarding.currentStep === 5 && (
          <Step5SourceDiscovery
            initialSource={onboarding.source}
            onNext={(source: string) => {
              onboarding.setSource(source);
              onboarding.setStep(6);
            }}
            onBack={() => onboarding.setStep(4)}
          />
        )}

        {onboarding.currentStep === 6 && (
          <Step6ThemeSelection
            initialTheme={onboarding.theme}
            onNext={(theme: ThemeOption) => {
              onboarding.setTheme(theme);
              onboarding.setStep(7);
            }}
            onBack={() => onboarding.setStep(5)}
          />
        )}

        {onboarding.currentStep === 7 && (
          <Step7ReviewFinish
            onboardingState={onboarding}
            onEditStep={(step: number) => {
              setLaunchError(null);
              onboarding.setStep(step);
            }}
            onLaunchWorkspace={handleLaunchWorkspace}
            isSubmitting={isLaunching || onboarding.isSubmitting}
            errorMessage={launchError}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="w-full bg-white border-t border-[#EEEEEE] py-4 px-6 sm:px-12 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#4C4736]/70">
        <div>
          &copy; {new Date().getFullYear()} MailTracko. All rights reserved.
        </div>
        <div className="flex items-center gap-4">
          <a href="https://mailtracko.com/privacy" className="hover:underline hover:text-[#8F740D]">
            Privacy Policy
          </a>
          <span>-</span>
          <a href="https://mailtracko.com/terms" className="hover:underline hover:text-[#8F740D]">
            Terms of Service
          </a>
        </div>
      </footer>
    </div>
  );
}
