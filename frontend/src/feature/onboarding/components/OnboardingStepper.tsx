import { Check } from "lucide-react";
import { ONBOARDING_STEPS } from "../store/onboardingsteps";

interface OnboardingStepperProps {
  currentStep: number;
  onStepClick?: (step: number) => void;
}

export function OnboardingStepper({
  currentStep,
  onStepClick,
}: OnboardingStepperProps) {
  return (
    <nav
      aria-label="Onboarding Progress"
      className="w-full py-4 px-4 overflow-x-auto scrollbar-none"
    >
      <ol className="flex items-center justify-between min-w-[760px] max-w-5xl mx-auto px-4">
        {ONBOARDING_STEPS.map((step, idx) => {
          const isCompleted = step.id < currentStep;
          const isCurrent = step.id === currentStep;
          const isLast = idx === ONBOARDING_STEPS.length - 1;

          return (
            <li key={step.id} className="flex-1 flex items-center relative">
              <button
                type="button"
                disabled={!isCompleted && !isCurrent}
                onClick={() => onStepClick?.(step.id)}
                className={`flex items-center gap-2.5 group cursor-pointer transition-all ${
                  !isCompleted && !isCurrent
                    ? "cursor-not-allowed opacity-60"
                    : ""
                }`}
              >
                {/* Step Badge */}
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all shrink-0 ${
                    isCompleted
                      ? "bg-[#8F740D] text-white shadow-xs"
                      : isCurrent
                        ? "bg-[#8F740D] text-white ring-4 ring-[#8F740D]/20 shadow-xs"
                        : "bg-[#EEEEEE] text-[#4C4736] border border-[#CEC6B0]/40"
                  }`}
                >
                  {isCompleted ? (
                    <Check className="w-4 h-4 stroke-[3]" />
                  ) : (
                    step.id
                  )}
                </div>

                {/* Step Text Labels */}
                <div className="flex flex-col text-left">
                  <span
                    className={`text-xs font-bold leading-tight ${
                      isCurrent
                        ? "text-[#8F740D]"
                        : isCompleted
                          ? "text-[#1A1C1C]"
                          : "text-[#4C4736]"
                    }`}
                  >
                    {step.label}
                  </span>
                  <span className="text-[10px] text-[#4C4736]/70 leading-tight hidden lg:inline">
                    {step.shortDescription}
                  </span>
                </div>
              </button>

              {/* Connecting line */}
              {!isLast && (
                <div className="flex-1 mx-3 h-[2px] bg-[#EEEEEE] relative">
                  <div
                    className="h-[2px] bg-[#8F740D] transition-all duration-300"
                    style={{
                      width: isCompleted ? "100%" : "0%",
                    }}
                  />
                </div>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
