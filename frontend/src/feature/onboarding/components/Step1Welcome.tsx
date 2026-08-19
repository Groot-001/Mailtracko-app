import {
  Eye,
  Users,
  Shield,
  ArrowRight,
  Lock,
  CheckCircle2,
} from "lucide-react";
import { ONBOARDING_STEPS } from "../store/onboardingsteps";

interface Step1WelcomeProps {
  onGetStarted: () => void;
  onSkip?: () => void;
}

export function Step1Welcome({ onGetStarted, onSkip }: Step1WelcomeProps) {
  return (
    <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
      {/* Left Main Card */}
      <div className="lg:col-span-8 bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 sm:p-10 shadow-lg flex flex-col justify-between min-h-[580px]">
        <div className="space-y-6">
          {/* Step Pill */}
          <div className="inline-block bg-[#F5E29F]/50 text-[#8F740D] border border-[#F2DF9C] px-3 py-1 rounded-full text-xs font-semibold">
            Step 1 of 7
          </div>

          {/* Heading */}
          <div className="space-y-3">
            <h1 className="text-3xl sm:text-4xl font-extrabold text-[#1A1C1C] tracking-tight">
              Welcome to <span className="text-[#8F740D]">MailTracko</span>
            </h1>
            <p className="text-[#4C4736] text-base leading-relaxed max-w-xl">
              Let's set up your workspace. In just a few quick steps, you'll be
              ready to track emails, gain insights, and drive meaningful
              conversations.
            </p>
          </div>

          {/* Content Split: Value Props + Preview Graphic */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2 items-center">
            {/* Feature Points */}
            <div className="space-y-5">
              <div className="flex gap-4 items-start">
                <div className="w-10 h-10 rounded-xl bg-[#F2DF9C]/40 flex items-center justify-center shrink-0">
                  <Eye className="w-5 h-5 text-[#8F740D]" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#1A1C1C]">
                    Real-time Email Tracking
                  </h3>
                  <p className="text-xs text-[#4C4736] leading-relaxed">
                    Know when your emails are opened.
                  </p>
                </div>
              </div>

              <div className="flex gap-4 items-start">
                <div className="w-10 h-10 rounded-xl bg-[#F2DF9C]/40 flex items-center justify-center shrink-0">
                  <Users className="w-5 h-5 text-[#8F740D]" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#1A1C1C]">
                    Team Collaboration
                  </h3>
                  <p className="text-xs text-[#4C4736] leading-relaxed">
                    Invite your team and track together.
                  </p>
                </div>
              </div>

              <div className="flex gap-4 items-start">
                <div className="w-10 h-10 rounded-xl bg-[#F2DF9C]/40 flex items-center justify-center shrink-0">
                  <Shield className="w-5 h-5 text-[#8F740D]" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#1A1C1C]">
                    Privacy-First by Design
                  </h3>
                  <p className="text-xs text-[#4C4736] leading-relaxed">
                    Your data is encrypted and never shared.
                  </p>
                </div>
              </div>
            </div>

            {/* Visual Graphic Mockup */}
            <div className="bg-[#F9F9F9] border border-[#EEEEEE] rounded-xl p-5 relative overflow-hidden flex flex-col items-center justify-center min-h-[200px]">
              {/* Decorative Card 1 */}
              <div className="w-full max-w-[220px] bg-white rounded-lg shadow-md border border-[#EEEEEE] p-3 text-left space-y-1 transform -rotate-2 hover:rotate-0 transition-transform">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-[11px] font-bold text-emerald-700">
                    Email opened
                  </span>
                </div>
                <p className="text-[10px] text-gray-500">
                  2:30 PM - New York, US
                </p>
              </div>

              {/* Decorative Card 2 */}
              <div className="w-full max-w-[200px] bg-white rounded-lg shadow-md border border-[#EEEEEE] p-3 mt-3 text-left space-y-1.5 transform rotate-2 hover:rotate-0 transition-transform">
                <span className="text-[10px] font-semibold text-gray-400">
                  Engagement Rate
                </span>
                <div className="flex items-end gap-1.5 h-8">
                  <div className="w-3 bg-[#F2DF9C] rounded-xs h-[40%]" />
                  <div className="w-3 bg-[#F2DF9C] rounded-xs h-[70%]" />
                  <div className="w-3 bg-[#8F740D] rounded-xs h-[100%]" />
                  <div className="w-3 bg-[#F2DF9C] rounded-xs h-[60%]" />
                </div>
              </div>

              {/* Floating check badge */}
              <div className="absolute bottom-3 right-3 w-8 h-8 rounded-full bg-[#8F740D] text-white flex items-center justify-center shadow-md">
                <CheckCircle2 className="w-5 h-5 stroke-[2.5]" />
              </div>
            </div>
          </div>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row items-center gap-4 pt-4 border-t border-[#EEEEEE]">
            <button
              type="button"
              onClick={onGetStarted}
              className="w-full sm:w-auto bg-[#8F740D] hover:bg-[#6E5E00] text-white font-bold text-sm px-8 py-3.5 rounded-xl flex items-center justify-center gap-2.5 transition-all shadow-md hover:shadow-lg cursor-pointer"
            >
              <span>Get Started</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            {onSkip && (
              <button
                type="button"
                onClick={onSkip}
                className="w-full sm:w-auto border border-[#CEC6B0] hover:bg-[#EEEEEE] text-[#4C4736] font-semibold text-sm px-8 py-3.5 rounded-xl transition-all cursor-pointer"
              >
                Skip for now
              </button>
            )}
          </div>
        </div>

        {/* Security badge at bottom */}
        <div className="flex items-center gap-2 text-xs text-[#4C4736]/80 pt-6 mt-4">
          <Lock className="w-3.5 h-3.5 text-[#8F740D]" />
          <span>
            <strong>Your security is our priority.</strong> We use
            enterprise-grade encryption and follow best practices to keep your
            data safe.
          </span>
        </div>
      </div>

      {/* Right Checklist Sidebar */}
      <div className="lg:col-span-4 bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 shadow-sm space-y-5">
        <h3 className="text-base font-bold text-[#1A1C1C]">
          What you'll set up
        </h3>

        <ol className="space-y-3.5">
          {ONBOARDING_STEPS.map((step) => {
            const isFirst = step.id === 1;
            return (
              <li
                key={step.id}
                className={`p-3 rounded-xl flex items-start gap-3 transition-all ${
                  isFirst
                    ? "bg-[#F5E29F]/20 border border-[#F2DF9C]"
                    : "bg-[#F9F9F9]"
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                    isFirst
                      ? "bg-[#8F740D] text-white"
                      : "bg-[#EEEEEE] text-[#4C4736]"
                  }`}
                >
                  {step.id}
                </div>
                <div className="space-y-0.5">
                  <h4
                    className={`text-xs font-bold ${
                      isFirst ? "text-[#8F740D]" : "text-[#1A1C1C]"
                    }`}
                  >
                    {step.label}
                  </h4>
                  <p className="text-[11px] text-[#4C4736] leading-tight">
                    {step.shortDescription}
                  </p>
                </div>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
