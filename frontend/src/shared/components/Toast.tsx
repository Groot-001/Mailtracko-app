import { AlertTriangle, CheckCircle2, Info } from "lucide-react";

export type ToastType = "success" | "error" | "info";

export interface ToastData {
  text: string;
  type: ToastType;
}

interface ToastProps {
  toast: ToastData;
  onClose: () => void;
}

export const Toast = ({ toast, onClose }: ToastProps) => (
  <div
    role="status"
    aria-live={toast.type === "error" ? "assertive" : "polite"}
    className={`w-[min(24rem,calc(100vw-2rem))] rounded-xl border px-4 py-3 text-white shadow-xl flex items-center gap-2.5 ${
      toast.type === "error"
        ? "border-red-900 bg-red-950"
        : toast.type === "info"
          ? "border-[#CEC6B0]/20 bg-[#1A1C1C]"
          : "border-emerald-950/30 bg-[#1A1C1C]"
    }`}
  >
    <div className="sr-only">{toast.type} notification</div>
    {toast.type === "error" ? (
      <AlertTriangle className="h-4 w-4 shrink-0 text-red-400" />
    ) : toast.type === "info" ? (
      <Info className="h-4 w-4 shrink-0 text-[#F1D442]" />
    ) : (
      <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
    )}
    <span className="min-w-0 flex-1 text-xs font-semibold leading-5">{toast.text}</span>
    <button
      type="button"
      onClick={onClose}
      aria-label="Dismiss notification"
      className="ml-1 shrink-0 text-sm leading-none text-white/70 transition hover:text-white"
    >
      ✕
    </button>
  </div>
);
