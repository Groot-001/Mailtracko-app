import { createFileRoute } from "@tanstack/react-router";
import { SecuritySettings } from "../../../../feature/organization/components/account-settings/SecuritySettings";
import { getCurrentUser } from "../../../../shared/api/authApi";
import { useAuthStore } from "../../../../shared/store/AuthStore";

export const Route = createFileRoute("/_protected/organization/account-settings/security")({
  loader: async () => {
    try {
      const user = await getCurrentUser();
      useAuthStore.getState().setUser(user);
      return user;
    } catch (err) {
      console.error("Loader failed to fetch current user for security:", err);
      return null;
    }
  },
  component: SecuritySettings,
});
