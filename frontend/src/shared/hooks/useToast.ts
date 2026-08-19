import { useCallback } from "react";
import { create } from "zustand";
import type { ToastData, ToastType } from "../components/Toast";

export interface ToastItem extends ToastData {
  id: string;
}

interface ToastStore {
  toasts: ToastItem[];
  show: (text: string, type?: ToastType) => void;
  dismiss: (id: string) => void;
}

const toastTimers = new Map<string, ReturnType<typeof setTimeout>>();
let toastSequence = 0;

const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  show: (text, type = "success") => {
    const id = `toast-${Date.now()}-${toastSequence++}`;
    const prefersReduced =
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    const timeout = prefersReduced ? 6000 : 4000;

    set((state) => ({
      // Keep the newest four notifications so rapid actions remain readable
      // without covering the product UI on laptop/mobile screens.
      toasts: [...state.toasts, { id, text, type }].slice(-4),
    }));

    const timer = setTimeout(() => {
      toastTimers.delete(id);
      set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) }));
    }, timeout);
    toastTimers.set(id, timer);
  },
  dismiss: (id) => {
    const timer = toastTimers.get(id);
    if (timer) clearTimeout(timer);
    toastTimers.delete(id);
    set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) }));
  },
}));

/** Shared product-wide notification API. The visual host is mounted once in __root. */
export const useToast = () => {
  const toasts = useToastStore((state) => state.toasts);
  const show = useToastStore((state) => state.show);
  const dismiss = useToastStore((state) => state.dismiss);

  const showToast = useCallback(
    (text: string, type: ToastType = "success") => show(text, type),
    [show],
  );

  return { toasts, showToast, dismissToast: dismiss };
};
