import { useEffect, useRef } from "react";
import { AlertTriangle, Loader2, X } from "lucide-react";

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  isLoading?: boolean;
  variant?: "destructive" | "warning";
  secondaryLabel?: string;
  onSecondary?: () => void | Promise<void>;
  onConfirm: () => void | Promise<void>;
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  isLoading = false,
  variant = "destructive",
  secondaryLabel,
  onSecondary,
  onConfirm,
}: ConfirmDialogProps) {
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement as HTMLElement | null;
    const timer = window.setTimeout(() => cancelRef.current?.focus(), 0);
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !isLoading) onOpenChange(false);
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      window.clearTimeout(timer);
      document.removeEventListener("keydown", onKeyDown);
      previous?.focus?.();
    };
  }, [open, isLoading, onOpenChange]);

  if (!open) return null;

  const iconClass = variant === "destructive" ? "bg-red-50 text-red-600" : "bg-amber-50 text-amber-700";
  const actionClass = variant === "destructive"
    ? "bg-red-600 hover:bg-red-700 focus-visible:ring-red-500"
    : "bg-[#8F740D] hover:bg-[#6A5B00] focus-visible:ring-[#8F740D]";

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/55 p-4 backdrop-blur-[2px]"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !isLoading) onOpenChange(false);
      }}
    >
      <section
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        aria-describedby="confirm-dialog-description"
        className="w-full max-w-md overflow-hidden rounded-2xl border border-[#CEC6B0]/50 bg-white shadow-2xl"
      >
        <div className="flex items-start gap-4 p-6">
          <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${iconClass}`}>
            <AlertTriangle className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-3">
              <h2 id="confirm-dialog-title" className="text-base font-bold text-[#1A1C1C]">
                {title}
              </h2>
              <button
                type="button"
                aria-label="Close confirmation"
                disabled={isLoading}
                onClick={() => onOpenChange(false)}
                className="rounded-lg p-1.5 text-[#756F60] transition hover:bg-[#F4F3F3] disabled:opacity-40"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <p id="confirm-dialog-description" className="mt-2 text-sm leading-6 text-[#4C4736]">
              {description}
            </p>
          </div>
        </div>
        <div className="flex flex-col-reverse gap-2 border-t border-[#EEE9DC] bg-[#FBFAF6] px-6 py-4 sm:flex-row sm:justify-end">
          <button
            ref={cancelRef}
            type="button"
            disabled={isLoading}
            onClick={() => onOpenChange(false)}
            className="inline-flex min-h-10 items-center justify-center rounded-xl border border-[#CEC6B0]/60 bg-white px-4 text-sm font-semibold text-[#1A1C1C] transition hover:bg-[#F4F3F3] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {cancelLabel}
          </button>
          {secondaryLabel && onSecondary ? (
            <button
              type="button"
              disabled={isLoading}
              onClick={() => void onSecondary()}
              className="inline-flex min-h-10 items-center justify-center rounded-xl border border-[#CEC6B0]/60 bg-white px-4 text-sm font-semibold text-[#5A5241] transition hover:bg-[#F4F3F3] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {secondaryLabel}
            </button>
          ) : null}
          <button
            type="button"
            disabled={isLoading}
            onClick={() => void onConfirm()}
            className={`inline-flex min-h-10 items-center justify-center gap-2 rounded-xl px-4 text-sm font-bold text-white shadow-sm transition focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 ${actionClass}`}
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {isLoading ? `${confirmLabel.replace(/…|\.\.\.$/, "")}…` : confirmLabel}
          </button>
        </div>
      </section>
    </div>
  );
}
