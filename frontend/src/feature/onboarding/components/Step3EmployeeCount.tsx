import { useState } from "react";
import { emailVolumeStepSchema } from "../schema/onboardingSchema";
import { Mail, Check, TrendingUp, Star, RefreshCw, ArrowRight, ShieldCheck } from "lucide-react";

interface Step3EmployeeCountProps {
  initialValue: string;
  onNext: (volume: string) => void;
  onBack: () => void;
}

interface VolumeCard {
  id: string;
  label: string;
  sublabel: string;
}

const VOLUME_OPTIONS: VolumeCard[] = [
  { id: "< 5,000", label: "Under 5,000", sublabel: "Starter / Personal use" },
  { id: "5,000 - 25,000", label: "5,000 - 25,000", sublabel: "Growing team" },
  { id: "25,000 - 100,000", label: "25,000 - 100,000", sublabel: "Scaling sender" },
  { id: "100,000 - 500,000", label: "100,000 - 500,000", sublabel: "High volume" },
  { id: "500,000+", label: "500,000+", sublabel: "Enterprise scale" },
];

export function Step3EmployeeCount({
  initialValue,
  onNext,
  onBack,
}: Step3EmployeeCountProps) {
  const [selected, setSelected] = useState<string>(initialValue || "");
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleContinue = () => {
    const result = emailVolumeStepSchema.safeParse({ emailVolume: selected });
    if (!result.success) {
      setValidationError(result.error.issues[0]?.message ?? "Please select an email volume");
      return;
    }
    setValidationError(null);
    onNext(result.data.emailVolume);
  };

  return (
    <div className="w-full bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 sm:p-10 shadow-lg space-y-8">
      {/* Top Header */}
      <div className="text-center space-y-3 max-w-2xl mx-auto">
        <div className="inline-block bg-[#F5E29F]/50 text-[#8F740D] border border-[#F2DF9C] px-3 py-1 rounded-full text-xs font-semibold">
          Step 3 of 7
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-[#1A1C1C] tracking-tight">
          What is your expected monthly email volume?
        </h1>
        <p className="text-[#4C4736] text-sm leading-relaxed">
          This helps us optimize your email tracking infrastructure and recommend the right plan tier for your needs.
        </p>
      </div>

      {/* Grid of Email Volume Option Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {VOLUME_OPTIONS.map((item) => {
          const isSelected = selected === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => { setSelected(item.id); setValidationError(null); }}
              className={`relative border-2 rounded-2xl p-6 flex flex-col items-center justify-center gap-3 transition-all cursor-pointer text-center ${
                isSelected
                  ? "bg-[#F5E29F]/20 border-[#8F740D] shadow-md ring-2 ring-[#8F740D]/20"
                  : "bg-[#F9F9F9] border-[#CEC6B0]/40 hover:border-[#8F740D]/60 hover:bg-white"
              }`}
            >
              {/* Selected Checkmark Badge */}
              {isSelected && (
                <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-[#8F740D] text-white flex items-center justify-center shadow-xs">
                  <Check className="w-3.5 h-3.5 stroke-[3]" />
                </div>
              )}

              <div className="w-12 h-12 rounded-full bg-[#F5E29F]/40 flex items-center justify-center">
                <Mail className="w-6 h-6 text-[#8F740D]" />
              </div>

              <div>
                <span className="text-lg font-extrabold text-[#1A1C1C] block">
                  {item.label}
                </span>
                <span className="text-xs text-[#4C4736] font-medium">
                  {item.sublabel}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Usage notice */}
      <div className="flex items-center justify-center gap-2 text-xs text-[#4C4736] pt-2">
        <ShieldCheck className="w-4 h-4 text-[#8F740D]" />
        <span>
          Your information is secure. We use this data only to configure your tracking nodes.
        </span>
      </div>

      {/* Bottom Information Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 pt-4 border-t border-[#EEEEEE]">
        {/* Card 1 */}
        <div className="bg-[#F9F9F9] border border-[#EEEEEE] rounded-xl p-4 flex gap-3.5 items-start">
          <div className="w-9 h-9 rounded-lg bg-[#F5E29F]/50 flex items-center justify-center shrink-0">
            <TrendingUp className="w-4 h-4 text-[#8F740D]" />
          </div>
          <div className="space-y-0.5">
            <h4 className="text-xs font-bold text-[#1A1C1C]">Dedicated delivery</h4>
            <p className="text-[11px] text-[#4C4736] leading-snug">
              High-performance tracking nodes with 99.99% uptime, tailored for any volume.
            </p>
          </div>
        </div>

        {/* Card 2 */}
        <div className="bg-[#F9F9F9] border border-[#EEEEEE] rounded-xl p-4 flex gap-3.5 items-start">
          <div className="w-9 h-9 rounded-lg bg-[#F5E29F]/50 flex items-center justify-center shrink-0">
            <Star className="w-4 h-4 text-[#8F740D]" />
          </div>
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <h4 className="text-xs font-bold text-[#1A1C1C]">Optimal plan</h4>
              <span className="text-[9px] font-bold bg-[#F5E29F] text-[#8F740D] px-1.5 py-0.2 rounded-xs">
                Matched
              </span>
            </div>
            <p className="text-[11px] text-[#4C4736] leading-snug">
              Ensures you remain on a plan with zero limits or hidden tracking caps.
            </p>
          </div>
        </div>

        {/* Card 3 */}
        <div className="bg-[#F9F9F9] border border-[#EEEEEE] rounded-xl p-4 flex gap-3.5 items-start">
          <div className="w-9 h-9 rounded-lg bg-[#F5E29F]/50 flex items-center justify-center shrink-0">
            <RefreshCw className="w-4 h-4 text-[#8F740D]" />
          </div>
          <div className="space-y-0.5">
            <h4 className="text-xs font-bold text-[#1A1C1C]">Change volume anytime</h4>
            <p className="text-[11px] text-[#4C4736] leading-snug">
              Scale your workspace up or down directly in your Billing preferences.
            </p>
          </div>
        </div>
      </div>

      {validationError && (
        <p role="alert" className="text-center text-sm font-medium text-red-600">{validationError}</p>
      )}

      {/* Action Bar */}
      <div className="flex items-center justify-between pt-6 border-t border-[#EEEEEE]">
        <button
          type="button"
          onClick={onBack}
          className="border border-[#CEC6B0] hover:bg-[#EEEEEE] text-[#4C4736] font-semibold text-sm px-8 py-3 rounded-xl transition-all cursor-pointer"
        >
          Back
        </button>

        <button
          type="button"
          onClick={handleContinue}
          className="bg-[#8F740D] hover:bg-[#6E5E00] text-white font-bold text-sm px-10 py-3 rounded-xl flex items-center gap-2 transition-all shadow-md cursor-pointer"
        >
          <span>Continue</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
