import { HelpCircle } from "lucide-react";
import mailtrackoicon from "../../../assets/Icon.svg";

interface OnboardingHeaderProps {
  onNeedHelp?: () => void;
}

export function OnboardingHeader({ onNeedHelp }: OnboardingHeaderProps) {
  return (
    <header className="w-full bg-white border-b border-[#EEEEEE] py-3.5 px-6 sm:px-12 flex items-center justify-between sticky top-0 z-30 shadow-xs">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-[#8F740D] flex items-center justify-center shadow-xs">
          <img src={mailtrackoicon} alt="MailTracko" className="w-5 h-5 text-white filter brightness-0 invert" />
        </div>
        <span className="text-xl font-bold tracking-tight text-[#1A1C1C]">
          MailTracko
        </span>
      </div>

      <button
        type="button"
        onClick={onNeedHelp}
        className="flex items-center gap-1.5 text-sm font-medium text-[#4C4736] hover:text-[#8F740D] transition-colors cursor-pointer"
      >
        <HelpCircle className="w-4 h-4 text-[#8F740D]" />
        <span>Need help?</span>
      </button>
    </header>
  );
}
