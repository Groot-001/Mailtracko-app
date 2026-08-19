import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";

import { loginUser } from "../api/loginApi";
import { bootstrapApp } from "../../../shared/app/bootstrap";
import { resolveInitialRoute } from "../../../shared/app/resolveInitialRoute";
import { completePendingInvitation } from "../../../shared/auth/pendingInvitation";
import { clearForcedLoginScreen } from "../../../shared/auth/forceLogin";

export function useLogin() {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: loginUser,

    onSuccess: async (envelope) => {
      if (
        envelope?.data?.requires_email_verification &&
        envelope?.data?.user?.email
      ) {
        navigate({
          to: "/verify-email",
          search: {
            email: envelope.data.user.email,
          },
        });

        return;
      }

      if (envelope?.data?.requires_2fa) {
        return;
      }

      // The backend has already set the HttpOnly session cookie. A fresh
      // successful authentication can now release the invitation login guard.
      clearForcedLoginScreen();

      // An existing user who opened an invitation link can
      // authenticate first and then accept that exact token in the same flow.
      try {
        await completePendingInvitation();
      } catch {
        // Keep the token in sessionStorage so the protected fallback page can retry.
      }

      const app = await bootstrapApp();

      if (!app) {
        return;
      }

      const initialRoute = resolveInitialRoute(app);

      navigate({
        to: initialRoute,
      });
    },
  });
}
