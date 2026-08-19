import { useEffect, useId, useRef } from "react";
import { X } from "lucide-react";

interface TextPromptDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  label: string;
  value: string;
  onValueChange: (value: string) => void;
  onSubmit: () => void;
  submitLabel?: string;
  placeholder?: string;
  inputType?: "text" | "url";
  error?: string | null;
  maxLength?: number;
}

export function TextPromptDialog({
  open,
  onOpenChange,
  title,
  description,
  label,
  value,
  onValueChange,
  onSubmit,
  submitLabel = "Insert",
  placeholder,
  inputType = "text",
  error,
  maxLength,
}: TextPromptDialogProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const titleId = useId();
  const errorId = useId();

  useEffect(() => {
    if (!open) return;
    const timer = window.setTimeout(() => inputRef.current?.focus({ preventScroll: true }), 0);
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onOpenChange(false);
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      window.clearTimeout(timer);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onOpenChange]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/55 p-4 backdrop-blur-[2px]">
      <section role="dialog" aria-modal="true" aria-labelledby={titleId} className="w-full max-w-md rounded-2xl border border-[#CEC6B0]/50 bg-white p-6 shadow-2xl focus:outline-none">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 id={titleId} className="text-base font-bold text-[#1A1C1C]">{title}</h2>
            {description ? <p className="mt-1 text-sm text-[#4C4736]">{description}</p> : null}
          </div>
          <button type="button" onClick={() => onOpenChange(false)} className="rounded-lg p-1.5 text-[#756F60] hover:bg-[#F4F3F3]" aria-label="Close dialog">
            <X className="h-4 w-4" />
          </button>
        </div>
        <form
          className="mt-5 space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            if (!value.trim()) return;
            onSubmit();
          }}
        >
          <label className="block space-y-1.5">
            <span className="text-xs font-bold text-[#4C4736]">{label}</span>
            <input
              ref={inputRef}
              type={inputType}
              value={value}
              onChange={(event) => onValueChange(event.target.value)}
              placeholder={placeholder}
              maxLength={maxLength}
              aria-invalid={Boolean(error)}
              aria-describedby={error ? errorId : undefined}
              className={`w-full rounded-xl border bg-white px-3 py-2.5 text-sm text-[#1A1C1C] outline-none transition focus:ring-1 ${error ? "border-red-400 focus:border-red-500 focus:ring-red-300/30" : "border-[#CEC6B0]/60 focus:border-[#8F740D] focus:ring-[#F1D442]/30"}`}
            />
            {error ? <p id={errorId} role="alert" className="text-xs font-medium text-red-600">{error}</p> : null}
          </label>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => onOpenChange(false)} className="rounded-xl border border-[#CEC6B0]/60 bg-white px-4 py-2.5 text-sm font-semibold text-[#1A1C1C] hover:bg-[#F4F3F3]">Cancel</button>
            <button type="submit" disabled={!value.trim()} className="rounded-xl bg-[#8F740D] px-4 py-2.5 text-sm font-bold text-white hover:bg-[#6A5B00] disabled:opacity-50">{submitLabel}</button>
          </div>
        </form>
      </section>
    </div>
  );
}
