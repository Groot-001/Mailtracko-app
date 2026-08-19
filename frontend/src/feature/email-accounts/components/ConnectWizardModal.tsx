import { useState } from "react";
import { GoogleIcon } from "./shared/ProviderIcons";
import { Mail } from "lucide-react";

interface ConnectWizardModalProps {
  onClose: () => void;
  onSelect: (provider: "gmail" | "smtp") => void;
}

export const ConnectWizardModal = ({ onClose, onSelect }: ConnectWizardModalProps) => {
  const [selected, setSelected] = useState<"gmail" | "smtp" | null>(null);

  const handleNext = () => {
    if (selected) {
      onSelect(selected);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl shadow-xl max-w-md w-full p-6 space-y-6 relative animate-in zoom-in-95 duration-200">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-[#4C4736] hover:text-[#1A1C1C] text-sm"
        >
          ✕
        </button>

        {/* Title */}
        <div className="text-center">
          <h3 className="text-base font-bold text-[#1A1C1C]">Connect Email Account</h3>
          <p className="text-xs text-[#4C4736] mt-1">
            Choose your email client provider platform.
          </p>
        </div>

        {/* Provider Chooser Grid */}
        <div className="grid grid-cols-2 gap-3">
          {[
            {
              id: "gmail" as const,
              label: "Gmail",
              sub: "(Google Workspace)",
              icon: GoogleIcon,
            },
            {
              id: "smtp" as const,
              label: "Custom",
              sub: "SMTP/IMAP",
              icon: Mail,
            },
          ].map((prov) => {
            const isSelected = selected === prov.id;
            return (
              <button
                key={prov.id}
                onClick={() => setSelected(prov.id)}
                className={`p-4 border rounded-xl flex flex-col items-center text-center justify-between min-h-[110px] transition-all hover:bg-slate-50 ${
                  isSelected
                    ? "border-[#8F740D] bg-[#F1D442]/10"
                    : "border-[#CEC6B0]/40 bg-white"
                }`}
              >
                {prov.id === "smtp" ? (
                  <prov.icon className="w-7 h-7 text-[#8F740D]" />
                ) : (
                  <prov.icon className="w-7 h-7" />
                )}
                <div className="space-y-0.5">
                  <p className="text-xs font-bold text-[#1A1C1C]">{prov.label}</p>
                  <p className="text-[9px] text-[#4C4736] leading-none">{prov.sub}</p>
                </div>
              </button>
            );
          })}
        </div>

        {/* Buttons */}
        <div className="flex gap-3 justify-end pt-2 border-t border-[#F4F3F3]">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-[#CEC6B0]/60 rounded-xl text-xs font-semibold hover:bg-[#F4F3F3]"
          >
            Cancel
          </button>
          <button
            onClick={handleNext}
            disabled={!selected}
            className="px-5 py-2 bg-[#8F740D] hover:bg-[#6A5B00] text-white text-xs font-semibold rounded-xl disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};
