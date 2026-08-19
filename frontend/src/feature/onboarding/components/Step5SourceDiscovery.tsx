import { useState } from "react";
import {
  Users,
  Share2,
  Video,
  ShoppingBag,
  Mail,
  Calendar,
  MoreHorizontal,
  Lock,
  ArrowRight,
  Quote,
} from "lucide-react";
import type { SourceDiscoveryOption } from "../types/onboarding.types";
import { sourceStepSchema } from "../schema/onboardingSchema";

interface Step5SourceDiscoveryProps {
  initialSource: string;
  onNext: (source: string) => void;
  onBack: () => void;
}

interface SourceOption {
  id: SourceDiscoveryOption;
  label: string;
  icon: React.ReactNode;
}

const SOURCE_OPTIONS: SourceOption[] = [
  {
    id: "social_media",
    label: "Social Media",
    icon: <Share2 className="w-4 h-4 text-blue-600" />,
  },
  {
    id: "referral",
    label: "Referral",
    icon: <Users className="w-4 h-4 text-[#8F740D]" />,
  },
  {
    id: "linkedin",
    label: "LinkedIn",
    icon: <Share2 className="w-4 h-4 text-blue-700" />,
  },
  {
    id: "youtube",
    label: "YouTube",
    icon: <Video className="w-4 h-4 text-red-600" />,
  },
  {
    id: "marketplace",
    label: "Marketplace",
    icon: <ShoppingBag className="w-4 h-4 text-amber-600" />,
  },
  {
    id: "newsletter",
    label: "Newsletter",
    icon: <Mail className="w-4 h-4 text-emerald-600" />,
  },
  {
    id: "events_webinar",
    label: "Event / Webinar",
    icon: <Calendar className="w-4 h-4 text-purple-600" />,
  },
  {
    id: "others",
    label: "Other",
    icon: <MoreHorizontal className="w-4 h-4 text-gray-500" />,
  },
];

export function Step5SourceDiscovery({
  initialSource,
  onNext,
  onBack,
}: Step5SourceDiscoveryProps) {
  const [selected, setSelected] = useState<string>(initialSource || "");
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleContinue = () => {
    const result = sourceStepSchema.safeParse({ source: selected });
    if (!result.success) {
      setValidationError(result.error.issues[0]?.message ?? "Please review this step");
      return;
    }
    setValidationError(null);
    onNext(result.data.source);
  };

  return (
    <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
      {/* Left Main Options Container */}
      <div className="lg:col-span-8 bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 sm:p-10 shadow-lg space-y-6">
        <div className="inline-block bg-[#F5E29F]/50 text-[#8F740D] border border-[#F2DF9C] px-3 py-1 rounded-full text-xs font-semibold">
          Step 5 of 7
        </div>

        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold text-[#1A1C1C] tracking-tight">
            How did you hear about MailTracko?
          </h1>
          <p className="text-[#4C4736] text-sm leading-relaxed">
            Your response helps us personalize your experience and recommend the right tips and features.
          </p>
        </div>

        {/* Radio Option Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          {SOURCE_OPTIONS.map((item) => {
            const isSelected = selected === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => { setSelected(item.id); setValidationError(null); }}
                className={`border-2 rounded-xl p-4 flex items-center justify-between transition-all cursor-pointer ${
                  isSelected
                    ? "bg-[#F5E29F]/20 border-[#8F740D] shadow-xs"
                    : "bg-[#F9F9F9] border-[#CEC6B0]/40 hover:border-[#8F740D]/60 hover:bg-white"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-white shadow-xs border border-[#EEEEEE] flex items-center justify-center">
                    {item.icon}
                  </div>
                  <span className="text-sm font-bold text-[#1A1C1C]">
                    {item.label}
                  </span>
                </div>

                {/* Radio Circle */}
                <div
                  className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                    isSelected
                      ? "border-[#8F740D] bg-[#8F740D]"
                      : "border-[#CEC6B0]"
                  }`}
                >
                  {isSelected && (
                    <div className="w-2 h-2 rounded-full bg-white" />
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {validationError && (
          <p role="alert" className="text-sm font-medium text-red-600">{validationError}</p>
        )}

        {/* Action Bar */}
        <div className="flex items-center justify-between pt-6 border-t border-[#EEEEEE]">
          <button
            type="button"
            onClick={onBack}
            className="border border-[#CEC6B0] hover:bg-[#EEEEEE] text-[#4C4736] font-semibold text-sm px-6 py-3 rounded-xl transition-all cursor-pointer"
          >
            Back
          </button>

          <button
            type="button"
            onClick={handleContinue}
            className="bg-[#8F740D] hover:bg-[#6E5E00] text-white font-bold text-sm px-8 py-3 rounded-xl flex items-center gap-2 transition-all shadow-md cursor-pointer"
          >
            <span>Continue</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* Privacy Note */}
        <div className="flex items-center gap-2 text-xs text-[#4C4736]/80 pt-2">
          <Lock className="w-3.5 h-3.5 text-[#8F740D]" />
          <span>Your responses are anonymous and help us improve our onboarding.</span>
        </div>
      </div>

      {/* Right Side Info & Pie Chart Graphic */}
      <div className="lg:col-span-4 space-y-6">
        <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 shadow-sm space-y-5">
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-[#1A1C1C]">
              We reach customers everywhere
            </h3>
            <p className="text-[11px] text-[#4C4736]">
              Here are the most common ways people discover MailTracko.
            </p>
          </div>

          {/* Donut Pie Chart Graphic */}
          <div className="flex items-center justify-center py-4 relative">
            <div className="w-36 h-36 rounded-full border-8 border-[#8F740D] border-r-[#F5E29F] border-b-[#E2C635] border-l-slate-400 relative flex items-center justify-center shadow-inner">
              <div className="w-12 h-12 rounded-xl bg-[#8F740D] text-white flex items-center justify-center shadow-md">
                <Mail className="w-6 h-6" />
              </div>
            </div>
          </div>

          {/* Legend */}
          <div className="space-y-2 text-xs font-semibold text-[#1A1C1C]">
            <div className="flex justify-between items-center">
              <span className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#8F740D]" /> Google Search
              </span>
              <span className="text-[#8F740D]">36%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#F5E29F]" /> Referral
              </span>
              <span>22%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-600" /> LinkedIn
              </span>
              <span>16%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-red-600" /> YouTube
              </span>
              <span>10%</span>
            </div>
          </div>
        </div>

        {/* Customer Testimonial Card */}
        <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 shadow-sm space-y-3">
          <Quote className="w-6 h-6 text-[#8F740D]/40 fill-[#8F740D]/20" />
          <p className="text-xs text-[#4C4736] italic leading-relaxed">
            "We found MailTracko while searching for email tracking that actually respects privacy. It's been a game-changer for our team."
          </p>
          <div className="pt-2 border-t border-[#EEEEEE]">
            <h4 className="text-xs font-bold text-[#1A1C1C]">Sarah Mitchell</h4>
            <p className="text-[10px] text-[#4C4736]">Growth Lead, Elevate Labs</p>
          </div>
        </div>
      </div>
    </div>
  );
}
