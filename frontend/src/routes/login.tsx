import { createFileRoute, redirect } from "@tanstack/react-router";
import LoginForm from "../feature/login/components/LoginForm";
import { bootstrapApp } from "../shared/app/bootstrap";
import { resolveInitialRoute } from "../shared/app/resolveInitialRoute";
import { shouldForceLoginScreen } from "../shared/auth/forceLogin";

export const Route = createFileRoute("/login")({
  beforeLoad: async () => {
    // Invitation registration/sign-in must show the login form even if this
    // browser still has another user's session cookie.
    if (shouldForceLoginScreen()) {
      return;
    }

    const app = await bootstrapApp();

    if (!app) {
      return;
    }

    const route = resolveInitialRoute(app);

    throw redirect({
      to: route,
    });
  },

  component: LoginForm,
});
