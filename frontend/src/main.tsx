import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import { QueryClientProvider } from "@tanstack/react-query";

import { routeTree } from "./routeTree.gen";
import { queryClient } from "./shared/api/queryClient";
import { installGlobalInputPolicy } from "./shared/utils/inputPolicy";

import "./index.css";

const router = createRouter({ routeTree });


// Apply the saved theme before React paints to prevent light/dark flashes on
// refresh and during the first authenticated render.
try {
  const persisted = JSON.parse(localStorage.getItem("auth-storage") || "null") as {
    state?: { user?: { theme?: string } | null };
  } | null;
  document.documentElement.dataset.theme = persisted?.state?.user?.theme === "dark" ? "dark" : "light";
} catch {
  document.documentElement.dataset.theme = "light";
}

installGlobalInputPolicy();

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
);
