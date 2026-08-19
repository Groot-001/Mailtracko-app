import type { ReactNode } from "react";
import { AlertCircle, CheckCircle2, Info } from "lucide-react";

interface InlineNoticeProps {
  tone?: "info" | "success" | "error";
  children: ReactNode;
}

export const InlineNotice = ({ tone = "info", children }: InlineNoticeProps) => {
  const styles = {
    info: "border-[#E3D8B5] bg-[#FFFBEE] text-[#685817]",
    success: "border-[#CDE7D4] bg-[#F1FBF4] text-[#25643A]",
    error: "border-[#F0C8C5] bg-[#FFF3F2] text-[#9B2C2C]",
  }[tone];
  const Icon = tone === "success" ? CheckCircle2 : tone === "error" ? AlertCircle : Info;

  const role = tone === "error" ? "alert" : "status";
  const ariaLive = tone === "error" ? "assertive" : "polite";

  return (
    <div role={role} aria-live={ariaLive} className={`flex items-start gap-2.5 rounded-xl border px-3.5 py-3 text-sm ${styles}`}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <div>{children}</div>
    </div>
  );
};
