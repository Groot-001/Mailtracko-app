import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { createAccount } from "../api/registerApi";
import { useToast } from "../../../shared/hooks/useToast";
import { logoutAccount } from "../../../shared/api/authApi";
import { useAuthStore } from "../../../shared/store/AuthStore";
import { forceNextLoginScreen } from "../../../shared/auth/forceLogin";

export function useCreateAccount() {
  const navigate = useNavigate();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: createAccount,

    onSuccess: async (_response, variables) => {
      if (variables.invite_token) {
        // An invitation may have been opened while a different account was
        // authenticated in this browser. Explicitly end that old session and
        // force the login screen so the newly registered invitee must sign in.
        forceNextLoginScreen();
        try {
          await logoutAccount();
        } catch {
          // The cookie may already be absent/expired; clearing client auth is
          // still safe and the one-shot login guard prevents a redirect loop.
        }
        useAuthStore.getState().logout();
      }

      showToast("Account created successfully. Please sign in to continue.", "success");
      navigate({ to: "/login" });
    },
  });
}
