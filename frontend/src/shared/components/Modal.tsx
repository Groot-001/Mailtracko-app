import { useEffect, useRef } from "react";
import type { ReactNode } from "react";
import { X } from "lucide-react";

interface ModalProps {
  open: boolean;
  title: string;
  description?: string;
  children: ReactNode;
  onClose: () => void;
}

export const Modal = ({ open, title, description, children, onClose }: ModalProps) => {
  const dialogRef = useRef<HTMLElement | null>(null);
  const onCloseRef = useRef(onClose);

  // Parents commonly pass an inline onClose callback. Keep the latest callback
  // without making the modal-open lifecycle effect depend on its identity. If
  // the lifecycle effect re-runs on every parent render, it re-applies autofocus
  // on every keystroke and moves the caret while a user is typing.
  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement as HTMLElement | null;

    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onCloseRef.current();
      if (event.key === "Tab" && dialogRef.current) {
        // simple focus trap
        const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        }
      }
    };

    document.addEventListener("keydown", handleKey);

    // Move focus to the intended control instead of the dialog shell. Focusing
    // the shell made the global focus-visible outline look like a glowing modal.
    const focusTimer = window.setTimeout(() => {
      const target = dialogRef.current?.querySelector<HTMLElement>(
        '[data-autofocus="true"], input:not([disabled]), textarea:not([disabled]), select:not([disabled]), button:not([disabled])',
      );
      target?.focus({ preventScroll: true });
    }, 0);

    return () => {
      document.removeEventListener("keydown", handleKey);
      window.clearTimeout(focusTimer);
      // restore focus
      previous?.focus();
    };
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Close dialog"
        className="absolute inset-0 bg-[#111827]/35 backdrop-blur-[1px]"
        onClick={onClose}
      />
      <section
        role="dialog"
        aria-modal="true"
        aria-label={title}
        aria-describedby={description ? "modal-desc" : undefined}
        ref={dialogRef}
        tabIndex={-1}
        className="relative z-10 w-full max-w-lg rounded-2xl border border-[#E8E1D0] bg-white p-6 shadow-2xl focus:outline-none"
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1.5 text-[#7B7462] hover:bg-[#F6F2E7]"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>
        <h2 className="pr-8 text-lg font-semibold text-[#111827]">{title}</h2>
        {description && (
          <p id="modal-desc" className="mt-1 text-sm text-[#756E5C]">
            {description}
          </p>
        )}
        <div className="mt-5">{children}</div>
      </section>
    </div>
  );
};
