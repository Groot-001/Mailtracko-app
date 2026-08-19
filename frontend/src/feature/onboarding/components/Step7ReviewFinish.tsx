import {
  CheckCircle2,
  Building2,
  Users,
  Briefcase,
  Globe,
  Palette,
  Edit3,
  Lock,
  PartyPopper,
  Check,
  ArrowRight,
  Loader2,
} from "lucide-react";
import type { OnboardingState } from "../types/onboarding.types";

interface Step7ReviewFinishProps {
  onboardingState: OnboardingState;
  onEditStep: (step: number) => void;
  onLaunchWorkspace: () => void;
  isSubmitting?: boolean;
  errorMessage?: string | null;
}

export function Step7ReviewFinish({
  onboardingState,
  onEditStep,
  onLaunchWorkspace,
  isSubmitting = false,
  errorMessage = null,
}: Step7ReviewFinishProps) {
  const { organization, monthlyEmailVolume, industrySector, source, theme, isSkipped } =
    onboardingState;

  return (
    <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
      {/* Left Main Review List Container */}
      <div className="lg:col-span-8 bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 sm:p-10 shadow-lg space-y-6">
        <div className="inline-block bg-[#F5E29F]/50 text-[#8F740D] border border-[#F2DF9C] px-3 py-1 rounded-full text-xs font-semibold">
          Step 7 of 7
        </div>

        {/* Heading */}
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold text-[#1A1C1C] tracking-tight flex items-center gap-2">
            <span>Review & finish setup</span>
            
          </h1>

          <div className="flex items-center gap-2 text-emerald-700 bg-emerald-50 border border-emerald-200 p-3 rounded-xl text-xs font-bold">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>
              {isSkipped ? "Setup details were skipped. Review the defaults and launch your workspace." : "You're all set! Review your settings and launch your workspace."}
            </span>
          </div>

          <p className="text-[#4C4736] text-sm leading-relaxed pt-1">
            {isSkipped
              ? "You chose to skip the optional setup questions. Nothing else is required; you can edit any section if you want, or launch with safe defaults."
              : "Everything looks great. Take a moment to review your setup details. You can edit any section before launching your MailTracko workspace."}
          </p>
        </div>

        {/* Configured Summary Cards List */}
        <div className="space-y-3 pt-2">
          {/* Card 1: Organization Details */}
          <div className="bg-[#F9F9F9] border border-[#CEC6B0]/30 rounded-xl p-4 flex items-center justify-between hover:bg-white hover:border-[#8F740D]/50 transition-all">
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-[#F5E29F]/40 flex items-center justify-center shrink-0">
                <Building2 className="w-5 h-5 text-[#8F740D]" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#1A1C1C]">
                  Organization Details
                </h4>
                <p className="text-xs text-[#4C4736]">
                  {organization.organizationName || "Organization not provided"} -{" "}
                  {organization.companyEmailDomain || "Domain not provided"}
                  {/* {organization.headquartersLocation ||
                    "New York, United States"} */}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onEditStep(2)}
              className="flex items-center gap-1 text-xs font-bold text-[#8F740D] hover:underline cursor-pointer px-3 py-1.5 rounded-lg hover:bg-[#F5E29F]/20"
            >
              <span>Edit</span>
              <Edit3 className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Card 2: Expected Email Volume */}
          <div className="bg-[#F9F9F9] border border-[#CEC6B0]/30 rounded-xl p-4 flex items-center justify-between hover:bg-white hover:border-[#8F740D]/50 transition-all">
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-[#F5E29F]/40 flex items-center justify-center shrink-0">
                <Users className="w-5 h-5 text-[#8F740D]" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#1A1C1C]">
                  Expected Email Volume
                </h4>
                <p className="text-xs text-[#4C4736]">
                  {monthlyEmailVolume || "Not selected"} {monthlyEmailVolume ? "emails / month" : ""}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onEditStep(3)}
              className="flex items-center gap-1 text-xs font-bold text-[#8F740D] hover:underline cursor-pointer px-3 py-1.5 rounded-lg hover:bg-[#F5E29F]/20"
            >
              <span>Edit</span>
              <Edit3 className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Card 3: Industry Sector */}
          <div className="bg-[#F9F9F9] border border-[#CEC6B0]/30 rounded-xl p-4 flex items-center justify-between hover:bg-white hover:border-[#8F740D]/50 transition-all">
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-[#F5E29F]/40 flex items-center justify-center shrink-0">
                <Briefcase className="w-5 h-5 text-[#8F740D]" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#1A1C1C]">
                  Industry Sector
                </h4>
                <p className="text-xs text-[#4C4736] capitalize">
                  {industrySector.replace("_", " ") || "Not selected"}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onEditStep(4)}
              className="flex items-center gap-1 text-xs font-bold text-[#8F740D] hover:underline cursor-pointer px-3 py-1.5 rounded-lg hover:bg-[#F5E29F]/20"
            >
              <span>Edit</span>
              <Edit3 className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Card 4: Source */}
          <div className="bg-[#F9F9F9] border border-[#CEC6B0]/30 rounded-xl p-4 flex items-center justify-between hover:bg-white hover:border-[#8F740D]/50 transition-all">
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-[#F5E29F]/40 flex items-center justify-center shrink-0">
                <Globe className="w-5 h-5 text-[#8F740D]" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#1A1C1C]">Source</h4>
                <p className="text-xs text-[#4C4736] capitalize">
                  {source.replace("_", " ") || "Not selected"}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onEditStep(5)}
              className="flex items-center gap-1 text-xs font-bold text-[#8F740D] hover:underline cursor-pointer px-3 py-1.5 rounded-lg hover:bg-[#F5E29F]/20"
            >
              <span>Edit</span>
              <Edit3 className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Card 5: Theme Selection */}
          <div className="bg-[#F9F9F9] border border-[#CEC6B0]/30 rounded-xl p-4 flex items-center justify-between hover:bg-white hover:border-[#8F740D]/50 transition-all">
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-[#F5E29F]/40 flex items-center justify-center shrink-0">
                <Palette className="w-5 h-5 text-[#8F740D]" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#1A1C1C]">
                  Theme Selection
                </h4>
                <p className="text-xs text-[#4C4736] capitalize">
                  {theme === "dark" ? "Dark" : "Light"}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onEditStep(6)}
              className="flex items-center gap-1 text-xs font-bold text-[#8F740D] hover:underline cursor-pointer px-3 py-1.5 rounded-lg hover:bg-[#F5E29F]/20"
            >
              <span>Edit</span>
              <Edit3 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Bottom Banner Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-[#EEEEEE]">
          <div className="bg-[#F9F9F9] border border-[#EEEEEE] rounded-xl p-4 flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-[#F5E29F]/40 flex items-center justify-center shrink-0">
              <Lock className="w-4 h-4 text-[#8F740D]" />
            </div>
            <div className="space-y-0.5 text-xs">
              <h4 className="font-bold text-[#1A1C1C]">
                Enterprise-grade security
              </h4>
              <p className="text-[#4C4736] text-[11px]">
                Your data is encrypted and never shared.
              </p>
            </div>
          </div>

          <div className="bg-[#F9F9F9] border border-[#EEEEEE] rounded-xl p-4 flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-[#F5E29F]/40 flex items-center justify-center shrink-0">
              <PartyPopper className="w-4 h-4 text-[#8F740D]" />
            </div>
            <div className="space-y-0.5 text-xs">
              <h4 className="font-bold text-[#1A1C1C]">Congratulations!</h4>
              <p className="text-[#4C4736] text-[11px]">
                You're ready to track, analyze, and grow.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Sidebar Setup Complete & Launch Card */}
      <div className="lg:col-span-4 bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 shadow-sm space-y-6 text-center">
        {/* Celebration Trophy Icon */}
        <div className="space-y-3 flex flex-col items-center">
          <div className="w-16 h-16 rounded-full bg-[#8F740D] text-white flex items-center justify-center shadow-lg ring-8 ring-[#F5E29F]/40">
            <Check className="w-8 h-8 stroke-[3]" />
          </div>
          <div>
            <h3 className="text-xl font-extrabold text-[#1A1C1C]">
              Setup Complete
            </h3>
            <p className="text-xs text-[#4C4736]">
              {isSkipped ? "Your workspace will be created with safe defaults when you launch it." : "Your MailTracko workspace is ready."}
            </p>
          </div>
        </div>

        {/* Setup Checklist */}
        <div className="text-left space-y-3 border-t border-b border-[#EEEEEE] py-4">
          <h4 className="text-xs font-bold text-[#1A1C1C]">Setup Checklist</h4>
          <ol className="space-y-2 text-xs">
            <li className="flex items-center gap-2 text-emerald-700 font-semibold">
              <Check className="w-4 h-4 stroke-[3] text-emerald-600" />
              <span>1. Workspace set up</span>
            </li>
            <li className="flex items-center gap-2 text-emerald-700 font-semibold">
              <Check className="w-4 h-4 stroke-[3] text-emerald-600" />
              <span>{isSkipped ? "2. Organization profile skipped (optional)" : "2. Organization profile configured"}</span>
            </li>
            <li className="flex items-center gap-2 text-emerald-700 font-semibold">
              <Check className="w-4 h-4 stroke-[3] text-emerald-600" />
              <span>{isSkipped ? "3. Email volume skipped (optional)" : "3. Team size registered"}</span>
            </li>
            <li className="flex items-center gap-2 text-emerald-700 font-semibold">
              <Check className="w-4 h-4 stroke-[3] text-emerald-600" />
              <span>{isSkipped ? "4. Industry sector skipped (optional)" : "4. Industry sector selected"}</span>
            </li>
            <li className="flex items-center gap-2 text-emerald-700 font-semibold">
              <Check className="w-4 h-4 stroke-[3] text-emerald-600" />
              <span>{isSkipped ? "5. Discovery source skipped (optional)" : "5. Referral source noted"}</span>
            </li>
            <li className="flex items-center gap-2 text-emerald-700 font-semibold">
              <Check className="w-4 h-4 stroke-[3] text-emerald-600" />
              <span>6. Theme personalized</span>
            </li>
            <li className="flex items-center gap-2 text-emerald-700 font-semibold">
              <Check className="w-4 h-4 stroke-[3] text-emerald-600" />
              <span>7. Setup confirmed</span>
            </li>
          </ol>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3">
          {errorMessage ? (
            <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-medium text-red-700">
              {errorMessage}
            </div>
          ) : null}
          <button
            type="button"
            disabled={isSubmitting}
            onClick={onLaunchWorkspace}
            className="w-full bg-[#8F740D] hover:bg-[#6E5E00] text-white font-bold text-sm py-3.5 px-6 rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-xl cursor-pointer disabled:opacity-70"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Launching Workspace...</span>
              </>
            ) : (
              <>
                <span>Launch Workspace</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>

          <button
            type="button"
            onClick={() => onEditStep(1)}
            className="w-full border border-[#CEC6B0] hover:bg-[#EEEEEE] text-[#4C4736] font-semibold text-xs py-2.5 rounded-xl transition-all cursor-pointer"
          >
            Review again
          </button>
        </div>
      </div>
    </div>
  );
}
