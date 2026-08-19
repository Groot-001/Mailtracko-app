import { createRootRoute, Outlet } from "@tanstack/react-router";
import { Toast } from "../shared/components/Toast";
import { useToast } from "../shared/hooks/useToast";

const RootLayout = () => {
  const { toasts, dismissToast } = useToast();

  return (
    <>
      <Outlet />
      <div className="pointer-events-none fixed right-4 top-4 z-[200] flex max-w-[calc(100vw-2rem)] flex-col items-end gap-2 sm:right-5 sm:top-5">
        {toasts.map((toast) => (
          <div key={toast.id} className="pointer-events-auto">
            <Toast toast={toast} onClose={() => dismissToast(toast.id)} />
          </div>
        ))}
      </div>
    </>
  );
};

export const Route = createRootRoute({
  component: RootLayout,
});
