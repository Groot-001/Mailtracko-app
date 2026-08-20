import { useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  industrySectorStepSchema,
  type IndustrySectorStepFormData,
  type IndustrySectorStepFormInput,
} from "../schema/onboardingSchema";
import {
  Search,
  Check,
  Laptop,
  Landmark,
  HeartPulse,
  GraduationCap,
  ShoppingCart,
  Home,
  Briefcase,
  Factory,
  FileText,
  Lightbulb,
  BarChart,
  PieChart,
  ArrowRight,
  Headphones,
} from "lucide-react";
import { ONBOARDING_STEPS } from "../store/onboardingsteps";

interface Step4IndustrySectorProps {
  initialValue: string;
  onNext: (sector: string) => void;
  onBack: () => void;
  currentStep?: number;
}

interface SectorCard {
  id: string;
  title: string;
  description: string;
  badge?: string;
  icon: React.ReactNode;
}

const SECTOR_OPTIONS: SectorCard[] = [
  {
    id: "technology",
    title: "Technology",
    description: "Software, SaaS, IT services, and tech companies.",
    badge: "Best match",
    icon: <Laptop className="w-6 h-6 text-[#8F740D]" />,
  },
  {
    id: "finance",
    title: "Finance",
    description: "Banking, fintech, insurance, and financial services.",
    badge: "Popular",
    icon: <Landmark className="w-6 h-6 text-[#8F740D]" />,
  },
  {
    id: "healthcare",
    title: "Healthcare",
    description: "Health services, medical devices, and wellness.",
    badge: "Popular",
    icon: <HeartPulse className="w-6 h-6 text-[#8F740D]" />,
  },
  {
    id: "education",
    title: "Education",
    description: "Schools, universities, online learning, and edtech.",
    icon: <GraduationCap className="w-6 h-6 text-[#8F740D]" />,
  },
  {
    id: "ecommerce",
    title: "E-commerce",
    description: "Online stores, marketplaces, and retail brands.",
    badge: "Popular",
    icon: <ShoppingCart className="w-6 h-6 text-[#8F740D]" />,
  },
  {
    id: "real_estate",
    title: "Real Estate",
    description: "Property, real estate services, and investment firms.",
    icon: <Home className="w-6 h-6 text-[#8F740D]" />,
  },
  {
    id: "consulting",
    title: "Consulting",
    description: "Management, strategy, and professional services.",
    icon: <Briefcase className="w-6 h-6 text-[#8F740D]" />,
  },
  {
    id: "manufacturing",
    title: "Manufacturing",
    description: "Production, industrial goods, and engineering.",
    icon: <Factory className="w-6 h-6 text-[#8F740D]" />,
  },
];

export function Step4IndustrySector({
  initialValue,
  onNext,
  onBack,
  currentStep = 4,
}: Step4IndustrySectorProps) {
  const [searchQuery, setSearchQuery] = useState<string>("");

  const {
    handleSubmit,
    control,
    setValue,
    formState: { errors },
  } = useForm<IndustrySectorStepFormInput, unknown, IndustrySectorStepFormData>({
    resolver: zodResolver(industrySectorStepSchema),
    defaultValues: {
      industrySector: initialValue as IndustrySectorStepFormInput["industrySector"],
    },
  });

  const selected = useWatch({ control, name: "industrySector" });

  const onSubmit = (data: IndustrySectorStepFormData) => {
    onNext(data.industrySector);
  };

  const filteredSectors = SECTOR_OPTIONS.filter(
    (sector) =>
      sector.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sector.description.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      {/* Left Stepper Navigation Column */}
      <div className="hidden lg:block lg:col-span-2 bg-white border border-[#CEC6B0]/40 rounded-2xl p-4 space-y-4 shadow-sm">
        <ol className="space-y-3">
          {ONBOARDING_STEPS.map((step) => {
            const isCompleted = step.id < currentStep;
            const isCurrent = step.id === currentStep;

            return (
              <li
                key={step.id}
                className={`p-2.5 rounded-xl flex items-center gap-2.5 transition-all ${
                  isCurrent
                    ? "bg-[#F5E29F]/30 border border-[#F2DF9C] font-bold text-[#8F740D]"
                    : isCompleted
                      ? "text-[#1A1C1C]"
                      : "text-[#4C4736]/60 opacity-70"
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                    isCompleted
                      ? "bg-[#8F740D] text-white"
                      : isCurrent
                        ? "bg-[#8F740D] text-white"
                        : "bg-[#EEEEEE] text-[#4C4736]"
                  }`}
                >
                  {isCompleted ? (
                    <Check className="w-3.5 h-3.5 stroke-[3]" />
                  ) : (
                    step.id
                  )}
                </div>
                <span className="text-xs">{step.label}</span>
              </li>
            );
          })}
        </ol>

        {/* Need Help Box */}
        <div className="pt-4 border-t border-[#EEEEEE] space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-[#1A1C1C]">
            <Headphones className="w-4 h-4 text-[#8F740D]" />
            <span>Need help?</span>
          </div>
          <p className="text-[11px] text-[#4C4736]">
            Our team is here to help you get started.
          </p>
          <button
            type="button"
            className="w-full border border-[#CEC6B0] hover:bg-[#EEEEEE] text-xs font-semibold py-1.5 rounded-lg text-[#4C4736] transition-all cursor-pointer"
          >
            Contact support
          </button>
        </div>
      </div>

      {/* Center Main Content Area */}
      <form onSubmit={handleSubmit(onSubmit)} className="lg:col-span-7 bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 sm:p-8 shadow-lg space-y-6">
        <div className="space-y-2">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#1A1C1C] tracking-tight">
            Choose your industry sector
          </h1>
          <p className="text-[#4C4736] text-xs sm:text-sm">
            This helps us personalize your templates, insights, and tracking
            recommendations.
          </p>
        </div>

        {/* Search Input Filter */}
        <div className="relative flex items-center">
          <Search className="w-4 h-4 text-[#4C4736]/60 absolute left-3.5 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            maxLength={100}
            placeholder="Search industries (e.g., Technology, Healthcare, Finance)"
            className="w-full bg-[#F9F9F9] border border-[#CEC6B0]/60 focus:border-[#8F740D] focus:bg-white rounded-xl py-2.5 pl-10 pr-4 text-xs sm:text-sm text-[#1A1C1C] outline-none transition-all"
          />
        </div>

        {/* Industry Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {filteredSectors.map((sector) => {
            const isSelected = selected === sector.id;
            return (
              <button
                key={sector.id}
                type="button"
                onClick={() => setValue("industrySector", sector.id as IndustrySectorStepFormInput["industrySector"], { shouldValidate: true })}
                className={`relative border-2 rounded-2xl p-5 flex flex-col items-center justify-center text-center gap-3 transition-all cursor-pointer ${
                  isSelected
                    ? "bg-[#F5E29F]/15 border-[#8F740D] shadow-md ring-2 ring-[#8F740D]/20"
                    : "bg-[#F9F9F9] border-[#CEC6B0]/30 hover:border-[#8F740D]/60 hover:bg-white"
                }`}
              >
                {/* Badge if present */}
                {sector.badge && (
                  <span
                    className={`absolute top-2.5 ${
                      isSelected ? "right-10" : "right-3"
                    } text-[9px] font-bold px-2 py-0.5 rounded-full ${
                      sector.badge === "Best match"
                        ? "bg-[#F5E29F] text-[#8F740D]"
                        : "bg-[#EEEEEE] text-[#4C4736]"
                    }`}
                  >
                    {sector.badge}
                  </span>
                )}

                {/* Selected Checkmark Badge */}
                {isSelected && (
                  <div className="absolute top-2.5 right-3 w-5 h-5 rounded-full bg-[#8F740D] text-white flex items-center justify-center shadow-xs">
                    <Check className="w-3 h-3 stroke-[3]" />
                  </div>
                )}

                <div className="w-12 h-12 rounded-full bg-[#F5E29F]/30 flex items-center justify-center shrink-0">
                  {sector.icon}
                </div>

                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-[#1A1C1C]">
                    {sector.title}
                  </h4>
                  <p className="text-[11px] text-[#4C4736] leading-tight">
                    {sector.description}
                  </p>
                </div>
              </button>
            );
          })}
        </div>

        {/* Helpful Tip */}
        <p className="text-[11px] text-[#4C4736]/80 italic text-center pt-2">
          Can't find your industry? Choose the closest match. You can update
          this anytime in settings.
        </p>

        {errors.industrySector && (
          <p role="alert" className="text-center text-sm font-medium text-red-600">{errors.industrySector.message}</p>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-4 border-t border-[#EEEEEE]">
          <button
            type="button"
            onClick={onBack}
            className="border border-[#CEC6B0] hover:bg-[#EEEEEE] text-[#4C4736] font-semibold text-xs sm:text-sm px-6 py-2.5 rounded-xl transition-all cursor-pointer"
          >
            Back
          </button>

          <button
            type="submit"
            className="bg-[#8F740D] hover:bg-[#6E5E00] text-white font-bold text-xs sm:text-sm px-8 py-2.5 rounded-xl flex items-center gap-2 transition-all shadow-md cursor-pointer"
          >
            <span>Continue</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>

      {/* Right Information Panel */}
      <div className="lg:col-span-3 bg-white border border-[#CEC6B0]/40 rounded-2xl p-5 space-y-5 shadow-sm">
        <h3 className="text-xs font-bold text-[#1A1C1C]">
          Why your industry matters
        </h3>

        <div className="space-y-4">
          <div className="flex gap-3 items-start">
            <div className="w-7 h-7 rounded-lg bg-[#F5E29F]/40 flex items-center justify-center shrink-0">
              <FileText className="w-3.5 h-3.5 text-[#8F740D]" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-[#1A1C1C]">
                Relevant Templates
              </h4>
              <p className="text-[10px] text-[#4C4736] leading-tight">
                Get email templates proven to work in your industry.
              </p>
            </div>
          </div>

          <div className="flex gap-3 items-start">
            <div className="w-7 h-7 rounded-lg bg-[#F5E29F]/40 flex items-center justify-center shrink-0">
              <Lightbulb className="w-3.5 h-3.5 text-[#8F740D]" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-[#1A1C1C]">
                Smart Tracking Suggestions
              </h4>
              <p className="text-[10px] text-[#4C4736] leading-tight">
                We'll recommend what to track based on your industry.
              </p>
            </div>
          </div>

          <div className="flex gap-3 items-start">
            <div className="w-7 h-7 rounded-lg bg-[#F5E29F]/40 flex items-center justify-center shrink-0">
              <BarChart className="w-3.5 h-3.5 text-[#8F740D]" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-[#1A1C1C]">
                Better Benchmarks
              </h4>
              <p className="text-[10px] text-[#4C4736] leading-tight">
                Compare your performance with similar businesses.
              </p>
            </div>
          </div>
        </div>

        {/* Dashboard preview graphic */}
        <div className="bg-[#F9F9F9] border border-[#EEEEEE] rounded-xl p-3 text-center space-y-2">
          <div className="flex items-center justify-between text-[10px] text-gray-500">
            <span>Industry Analytics</span>
            <PieChart className="w-3.5 h-3.5 text-[#8F740D]" />
          </div>
          <div className="h-16 bg-white rounded-lg border border-[#EEEEEE] flex items-center justify-center p-2">
            <div className="w-10 h-10 rounded-full border-4 border-[#8F740D] border-t-[#F5E29F] animate-spin-slow" />
          </div>
        </div>
      </div>
    </div>
  );
}
